from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
import os
import shutil
import uuid
from ..database import get_db
from .. import models, auth, face_logic, express_entry

router = APIRouter(prefix="/face", tags=["face"])

UPLOAD_DIR = "temp_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/register")
async def register_face(
    file: UploadFile = File(...), 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(auth.get_current_active_user)
):
    # Save file temporarily
    file_ext = file.filename.split(".")[-1]
    file_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}.{file_ext}")
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Get embedding
    embedding = face_logic.get_embedding(file_path)
    
    # Cleanup
    if os.path.exists(file_path):
        os.remove(file_path)
        
    if embedding is None:
        raise HTTPException(status_code=400, detail="No face detected or AI error. Please try another photo.")
    
    # Store embedding
    db_embedding = db.query(models.FaceEmbedding).filter(models.FaceEmbedding.user_id == current_user.id).first()
    if db_embedding:
        db_embedding.embedding = embedding
    else:
        new_embedding = models.FaceEmbedding(user_id=current_user.id, embedding=embedding)
        db.add(new_embedding)
    
    db.commit()
    return {"message": "Face registered successfully"}

@router.post("/verify-entry/{lounge_id}")
async def verify_entry(
    lounge_id: int,
    file: UploadFile = File(...), 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(auth.get_current_active_user)
):
    # Save file temporarily
    file_ext = file.filename.split(".")[-1]
    file_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}.{file_ext}")
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Check entry eligibility
    is_allowed, reason = express_entry.check_entry_eligibility(db, current_user, lounge_id, file_path)
    
    # Log entry attempt
    log = models.EntryLog(
        user_id=current_user.id, 
        lounge_id=lounge_id, 
        status="Access Granted" if is_allowed else "Access Denied",
        reason=reason
    )
    db.add(log)
    db.commit()

    # Cleanup
    if os.path.exists(file_path):
        os.remove(file_path)
        
    return {
        "access_granted": is_allowed,
        "reason": reason,
        "user": current_user.username
    }
