import os
import csv
import re
import sqlite3
from typing import List, Dict, Any, Optional

# Paths relative to repository / backend
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
CSV_CANDIDATE_PATHS = [
    os.path.join(BASE_DIR, "..", "A_Z_medicines_dataset_of_India.csv"),
    os.path.join(BASE_DIR, "A_Z_medicines_dataset_of_India.csv"),
    "D:\\PROJECTSSSSS\\MediKiosk\\A_Z_medicines_dataset_of_India.csv",
]
DB_PATH = os.path.join(BASE_DIR, "data", "medicines.db")

DOSAGE_FORM_PATTERNS = [
    (r"\b(?:tablet|tabs?|tab|dt|pr)\b", "Tablet", ["Oral"], "1 tablet"),
    (r"\b(?:capsule|caps?|cap)\b", "Capsule", ["Oral"], "1 capsule"),
    (r"\b(?:syrup|suspension|liquid|elixir|oral liquid|oral solution)\b", "Syrup", ["Oral"], "5 ml"),
    (r"\b(?:injection|inj|infusion|vial|ampoule)\b", "Injection", ["IV", "IM", "SC"], "1 vial"),
    (r"\b(?:eye drops?|ear drops?|drops?|nasal drops?|nasal spray)\b", "Drops", ["Ophthalmic", "Otic", "Nasal"], "2 drops"),
    (r"\b(?:ointment|gel|cream|lotion|liniment|emulgel)\b", "Topical", ["Topical"], "Apply thin layer"),
    (r"\b(?:inhaler|respules?|rotacaps?|inhalation)\b", "Inhalation", ["Inhalation"], "1 puff"),
    (r"\b(?:lozenge|lozenges)\b", "Lozenge", ["Oral"], "1 lozenge"),
    (r"\b(?:powder|sachet|granules)\b", "Powder/Sachet", ["Oral"], "1 sachet in water"),
]

SPELLING_ALIASES = {
    "amoxicillin": "amoxycillin",
    "paracetamol": "paracetamol",
    "acetaminophen": "paracetamol",
    "dolo": "paracetamol",
    "crocin": "paracetamol",
    "calpol": "paracetamol",
    "augmentin": "amoxycillin",
    "azithromycin": "azithromycin",
    "metformin": "metformin",
    "pantoprazole": "pantoprazole",
}

class MedicineSearchService:
    _initialized = False

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._ensure_database_ready()

    def _ensure_database_ready(self):
        """Ensures the SQLite database exists and is populated with the medicines dataset."""
        if os.path.exists(self.db_path) and os.path.getsize(self.db_path) > 1024 * 1024:
            return

        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        csv_file = None
        for path in CSV_CANDIDATE_PATHS:
            if os.path.exists(path):
                csv_file = path
                break

        if not csv_file:
            # Create an empty table if CSV is missing so queries don't crash
            conn = sqlite3.connect(self.db_path)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS medicines (
                    id INTEGER PRIMARY KEY,
                    name TEXT,
                    price REAL,
                    is_discontinued INTEGER,
                    manufacturer_name TEXT,
                    type TEXT,
                    pack_size_label TEXT,
                    short_composition1 TEXT,
                    short_composition2 TEXT,
                    name_lower TEXT,
                    composition_lower TEXT
                )
            """)
            conn.commit()
            conn.close()
            return

        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("DROP TABLE IF EXISTS medicines")
        cur.execute("""
            CREATE TABLE medicines (
                id INTEGER PRIMARY KEY,
                name TEXT,
                price REAL,
                is_discontinued INTEGER,
                manufacturer_name TEXT,
                type TEXT,
                pack_size_label TEXT,
                short_composition1 TEXT,
                short_composition2 TEXT,
                name_lower TEXT,
                composition_lower TEXT
            )
        """)

        with open(csv_file, "r", encoding="utf-8", errors="replace") as f:
            reader = csv.reader(f)
            headers = next(reader, None)
            batch = []
            for r in reader:
                if len(r) >= 9:
                    m_id = int(r[0]) if r[0].isdigit() else None
                    name = r[1].strip()
                    try:
                        price = float(r[2]) if r[2] else 0.0
                    except Exception:
                        price = 0.0
                    disc = 1 if r[3].strip().upper() == "TRUE" else 0
                    mfg = r[4].strip()
                    m_type = r[5].strip()
                    pack = r[6].strip()
                    c1 = r[7].strip()
                    c2 = r[8].strip()
                    comp = f"{c1} {c2}".strip()
                    batch.append((
                        m_id, name, price, disc, mfg, m_type, pack, c1, c2,
                        name.lower(), comp.lower()
                    ))
                    if len(batch) >= 10000:
                        cur.executemany("INSERT INTO medicines VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", batch)
                        batch = []
            if batch:
                cur.executemany("INSERT INTO medicines VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", batch)

        cur.execute("CREATE INDEX IF NOT EXISTS idx_medicines_name_lower ON medicines(name_lower)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_medicines_composition_lower ON medicines(composition_lower)")
        conn.commit()
        conn.close()

    @staticmethod
    def extract_form_and_strength(name: str, pack_label: str = "", comp1: str = "", comp2: str = "") -> Dict[str, Any]:
        """Extracts clinically sensible dosage form, strength, suggested routes, and default dose."""
        combined_text = f"{name} {pack_label}".lower()
        form = "Tablet"
        routes = ["Oral"]
        default_dose = "1 tablet"

        for pattern, f_name, f_routes, d_dose in DOSAGE_FORM_PATTERNS:
            if re.search(pattern, combined_text):
                form = f_name
                routes = f_routes
                default_dose = d_dose
                break

        # Extract strength: look for mg, gm, mcg, ml, %, etc.
        strength_match = re.search(r"(\d+(?:\.\d+)?\s*(?:mg|gm|g|mcg|ml|iu|%|w/w|w/v)(?:/\d+(?:\.\d+)?\s*(?:mg|ml))?)", name, re.IGNORECASE)
        if strength_match:
            strength = strength_match.group(1).strip()
        elif comp1:
            comp_match = re.search(r"\(([^)]+)\)", comp1)
            strength = comp_match.group(1).strip() if comp_match else comp1
        else:
            strength = ""

        return {
            "dosage_form": form,
            "strength": strength,
            "suggested_routes": routes,
            "default_dose": default_dose
        }

    def search(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Fast ranked search across 253,000+ medicines:
        1. Exact prefix on name
        2. Substring on name
        3. Prefix / Substring on active ingredient / composition
        """
        if not query or not query.strip():
            return []

        clean_q = query.strip().lower()
        # Check aliases (e.g. amoxicillin -> amoxycillin)
        alias_q = SPELLING_ALIASES.get(clean_q, clean_q)

        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()

        # Prioritized ranking SQL query
        sql = """
            SELECT 
                id, name, price, manufacturer_name, type, pack_size_label, 
                short_composition1, short_composition2,
                CASE 
                    WHEN name_lower LIKE ? THEN 1
                    WHEN name_lower LIKE ? THEN 2
                    WHEN composition_lower LIKE ? THEN 3
                    WHEN composition_lower LIKE ? THEN 4
                    ELSE 5
                END as rank_score
            FROM medicines
            WHERE 
                name_lower LIKE ? 
                OR name_lower LIKE ?
                OR composition_lower LIKE ? 
                OR composition_lower LIKE ?
            ORDER BY rank_score ASC, name_lower ASC
            LIMIT ?
        """

        p_exact = f"{clean_q}%"
        p_sub = f"%{clean_q}%"
        p_alias_exact = f"{alias_q}%"
        p_alias_sub = f"%{alias_q}%"

        cur.execute(sql, (
            p_exact, p_sub, p_alias_exact, p_alias_sub,
            p_exact, p_sub, p_alias_exact, p_alias_sub,
            limit
        ))
        rows = cur.fetchall()
        conn.close()

        results = []
        for r in rows:
            m_id, name, price, mfg, m_type, pack, c1, c2, rank = r
            comp_combined = ", ".join(filter(None, [c1, c2])).strip()
            form_info = self.extract_form_and_strength(name, pack, c1, c2)

            results.append({
                "id": m_id,
                "name": name,
                "generic_name": comp_combined,
                "composition_1": c1,
                "composition_2": c2,
                "manufacturer_name": mfg,
                "type": m_type,
                "pack_size_label": pack,
                "price": price,
                "dosage_form": form_info["dosage_form"],
                "strength": form_info["strength"],
                "suggested_routes": form_info["suggested_routes"],
                "default_dose": form_info["default_dose"],
            })

        return results

    def get_by_id(self, medicine_id: int) -> Optional[Dict[str, Any]]:
        """Retrieves single medicine details by ID."""
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("""
            SELECT id, name, price, manufacturer_name, type, pack_size_label, 
                   short_composition1, short_composition2
            FROM medicines
            WHERE id = ?
        """, (medicine_id,))
        row = cur.fetchone()
        conn.close()

        if not row:
            return None

        m_id, name, price, mfg, m_type, pack, c1, c2 = row
        comp_combined = ", ".join(filter(None, [c1, c2])).strip()
        form_info = self.extract_form_and_strength(name, pack, c1, c2)

        return {
            "id": m_id,
            "name": name,
            "generic_name": comp_combined,
            "composition_1": c1,
            "composition_2": c2,
            "manufacturer_name": mfg,
            "type": m_type,
            "pack_size_label": pack,
            "price": price,
            "dosage_form": form_info["dosage_form"],
            "strength": form_info["strength"],
            "suggested_routes": form_info["suggested_routes"],
            "default_dose": form_info["default_dose"],
        }


# Singleton instance
medicine_search_service = MedicineSearchService()
