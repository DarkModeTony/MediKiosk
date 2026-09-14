import os
import uuid
import shutil
from abc import ABC, abstractmethod
from typing import IO

class DocumentStorage(ABC):
    @abstractmethod
    def save_document(self, file_stream: IO, filename: str, patient_id: str) -> str:
        pass

    @abstractmethod
    def get_document_path(self, storage_id: str) -> str:
        pass

class LocalStorageProvider(DocumentStorage):
    def __init__(self, base_dir: str = "uploads"):
        self.base_dir = os.path.join(os.getcwd(), base_dir)
        os.makedirs(self.base_dir, exist_ok=True)

    def save_document(self, file_stream: IO, filename: str, patient_id: str) -> str:
        ext = filename.split('.')[-1] if '.' in filename else ''
        storage_id = f"{patient_id}_{uuid.uuid4().hex}.{ext}"
        filepath = os.path.join(self.base_dir, storage_id)
        
        with open(filepath, "wb") as f:
            shutil.copyfileobj(file_stream, f)
            
        return storage_id

    def get_document_path(self, storage_id: str) -> str:
        return os.path.join(self.base_dir, storage_id)

def get_document_storage() -> DocumentStorage:
    # MVP uses LocalStorageProvider
    # Can be replaced with ObjectStorageProvider (S3) based on env vars
    return LocalStorageProvider(os.environ.get("DOCUMENT_STORAGE_PATH", "uploads"))
