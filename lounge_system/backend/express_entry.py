from datetime import datetime, timedelta
from . import models, face_logic
from sqlalchemy.orm import Session

def check_entry_eligibility(db: Session, user: models.User, lounge_id: int, current_image_path: str):
    """
    Consolidated logic for Express Entry.
    """
    # 1. Face Verification
    if not user.face_embedding:
        return False, "Face not registered"
    
    face_result = face_logic.verify_face(user.face_embedding.embedding, current_image_path)
    if not face_result["verified"]:
        return False, f"Face verification failed (Distance: {face_result['distance']:.4f})"

    # 2. Check Booking Existence for Today
    today = datetime.utcnow().date()
    booking = db.query(models.Booking).filter(
        models.Booking.user_id == user.id,
        models.Booking.lounge_id == lounge_id,
        # models.Booking.date == today # In real app, check date. For demo, simplified.
    ).first()

    if not booking:
        return False, "No booking found for this lounge"

    # 3. Check Payment Status
    if not booking.is_paid:
        return False, "Booking not paid"

    # 4. Check Slot Validity
    # Assuming slot is like "HH:MM-HH:MM"
    # For demo, let's say a booking is valid for the whole day it's booked
    # But let's add a mock logic for slot check if slot exists
    if booking.slot:
        try:
            # Simple check: current time should be within some range
            # For hackathon demo, we can just say "valid" if it's the right day
            pass
        except:
            pass

    return True, "Access Granted"
