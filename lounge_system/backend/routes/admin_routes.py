from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..database import get_db
from .. import models, auth

router = APIRouter(prefix="/admin", tags=["admin"])

@router.get("/stats")
def get_stats(db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_admin_user)):
    total_users = db.query(models.User).count()
    total_bookings = db.query(models.Booking).count()
    total_entries = db.query(models.EntryLog).filter(models.EntryLog.status == "Access Granted").count()
    
    # Mock Revenue Calculation
    revenue = db.query(models.Booking).filter(models.Booking.is_paid == True).count() * 50 # Let's say $50 per entry
    
    return {
        "total_users": total_users,
        "total_bookings": total_bookings,
        "total_entries": total_entries,
        "revenue": revenue
    }

@router.get("/logs")
def get_logs(db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_admin_user)):
    logs = db.query(models.EntryLog).order_by(models.EntryLog.timestamp.desc()).limit(100).all()
    result = []
    for log in logs:
        user = db.query(models.User).filter(models.User.id == log.user_id).first()
        lounge = db.query(models.Lounge).filter(models.Lounge.id == log.lounge_id).first()
        result.append({
            "id": log.id,
            "username": user.username if user else "Unknown",
            "lounge": lounge.name if lounge else "Unknown",
            "status": log.status,
            "reason": log.reason,
            "timestamp": log.timestamp
        })
    return result

@router.get("/users")
def get_users(db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_admin_user)):
    return db.query(models.User).all()
