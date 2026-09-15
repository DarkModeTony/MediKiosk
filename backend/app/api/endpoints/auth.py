import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.models import User, Hospital
from app.core.security import hash_password, verify_password, create_access_token
from app.api.deps import get_current_user

router = APIRouter()

class HospitalCreate(BaseModel):
    name: str

class UserCreate(BaseModel):
    username: str
    password: str
    role: str = "DOCTOR"
    hospital_id: Optional[str] = None

class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    username: str
    role: str
    hospital_id: Optional[str]
    hospital_name: Optional[str]

@router.post("/hospitals", status_code=status.HTTP_201_CREATED)
def create_hospital(payload: HospitalCreate, db: Session = Depends(get_db)):
    hospital = Hospital(name=payload.name)
    db.add(hospital)
    db.commit()
    db.refresh(hospital)
    return {"id": str(hospital.id), "name": hospital.name}

@router.post("/register-user", status_code=status.HTTP_201_CREATED)
def register_user(payload: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.username == payload.username).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    hospital_id = None
    if payload.hospital_id:
        try:
            hosp_uuid = uuid.UUID(payload.hospital_id)
            hosp = db.query(Hospital).filter(Hospital.id == hosp_uuid).first()
            if not hosp:
                raise HTTPException(status_code=404, detail="Hospital not found")
            hospital_id = hosp.id
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid hospital ID format")
    else:
        # Assign to default hospital
        hosp = db.query(Hospital).first()
        if not hosp:
            hosp = Hospital(name="Apollo Hospitals Bangalore")
            db.add(hosp)
            db.commit()
            db.refresh(hosp)
        hospital_id = hosp.id

    hashed = hash_password(payload.password)
    user = User(
        username=payload.username,
        password_hash=hashed,
        role=payload.role.upper(),
        hospital_id=hospital_id
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return {
        "id": str(user.id),
        "username": user.username,
        "role": user.role,
        "hospital_id": str(user.hospital_id) if user.hospital_id else None
    }

@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == payload.username).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    hospital_name = None
    if user.hospital_id:
        hosp = db.query(Hospital).filter(Hospital.id == user.hospital_id).first()
        if hosp:
            hospital_name = hosp.name

    token_data = {
        "sub": str(user.id),
        "username": user.username,
        "role": user.role,
        "hospital_id": str(user.hospital_id) if user.hospital_id else None
    }
    access_token = create_access_token(data=token_data)

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user_id=str(user.id),
        username=user.username,
        role=user.role,
        hospital_id=str(user.hospital_id) if user.hospital_id else None,
        hospital_name=hospital_name
    )

@router.get("/me")
def get_current_user_profile(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    hospital_name = None
    if current_user.hospital_id:
        hosp = db.query(Hospital).filter(Hospital.id == current_user.hospital_id).first()
        if hosp:
            hospital_name = hosp.name

    return {
        "id": str(current_user.id),
        "username": current_user.username,
        "role": current_user.role,
        "hospital_id": str(current_user.hospital_id) if current_user.hospital_id else None,
        "hospital_name": hospital_name,
    }
