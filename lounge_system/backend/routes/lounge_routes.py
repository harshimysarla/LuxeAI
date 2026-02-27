from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from .. import models, auth
from pydantic import BaseModel
from datetime import datetime, timedelta

router = APIRouter(prefix="/lounges", tags=["lounges"])

class BookingCreate(BaseModel):
    lounge_id: int
    slot: str
    card_number: str # Mock payment
    expiry: str
    cvv: str

class OrderItemCreate(BaseModel):
    menu_item_id: int
    quantity: int

class OrderCreate(BaseModel):
    booking_id: int
    items: list[OrderItemCreate]

@router.get("/")
def get_lounges(db: Session = Depends(get_db)):
    return db.query(models.Lounge).all()

@router.get("/menu/{lounge_id}")
def get_menu(lounge_id: int, db: Session = Depends(get_db)):
    return db.query(models.MenuItem).filter(models.MenuItem.lounge_id == lounge_id).all()

@router.post("/order")
def place_order(order: OrderCreate, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_active_user)):
    booking = db.query(models.Booking).filter(models.Booking.id == order.booking_id, models.Booking.user_id == current_user.id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    total_price = 0
    new_order = models.Order(booking_id=order.booking_id, total_price=0)
    db.add(new_order)
    db.flush()
    
    for item in order.items:
        menu_item = db.query(models.MenuItem).filter(models.MenuItem.id == item.menu_item_id).first()
        if menu_item:
            total_price += menu_item.price * item.quantity
            db.add(models.OrderItem(order_id=new_order.id, menu_item_id=item.menu_item_id, quantity=item.quantity))
    
    new_order.total_price = total_price
    db.commit()
    return {"message": "Order placed successfully", "order_id": new_order.id, "total": total_price}

@router.get("/flight/{flight_number}")
def get_flight_info(flight_number: str):
    # Mock Flight API
    # Logic: return random data for hackathon demo
    return {
        "flight_number": flight_number,
        "destination": "London (LHR)",
        "gate": "B12",
        "status": "On Time",
        "departure_time": (datetime.now() + timedelta(hours=3)).strftime("%Y-%m-%dT%H:%M:%S")
    }

@router.get("/")
def get_lounges(db: Session = Depends(get_db)):
    return db.query(models.Lounge).all()

@router.get("/{lounge_id}")
def get_lounge(lounge_id: int, db: Session = Depends(get_db)):
    lounge = db.query(models.Lounge).filter(models.Lounge.id == lounge_id).first()
    if not lounge:
        raise HTTPException(status_code=404, detail="Lounge not found")
    return {
        "id": lounge.id,
        "name": lounge.name,
        "airport": lounge.airport,
        "total_seats": lounge.total_seats,
        "occupancy": lounge.occupancy,
        "occupancy_percent": (lounge.occupancy / lounge.total_seats * 100) if lounge.total_seats > 0 else 0,
        "menu": lounge.menu_items
    }

@router.post("/book")
def create_booking(booking: BookingCreate, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_active_user)):
    # Simulating Seat Availability Check
    lounge = db.query(models.Lounge).filter(models.Lounge.id == booking.lounge_id).first()
    if not lounge or lounge.occupancy >= lounge.total_seats:
         raise HTTPException(status_code=400, detail="Lounge is full or not found")

    # Simulate Payment Success
    is_paid = True if booking.card_number else False
    
    # Generate mock QR code string
    import uuid
    qr_data = f"LOUNGE-{booking.lounge_id}-{uuid.uuid4().hex[:8]}"

    new_booking = models.Booking(
        user_id=current_user.id,
        lounge_id=booking.lounge_id,
        slot=booking.slot,
        is_paid=is_paid,
        status="confirmed",
        qr_code=qr_data
    )
    db.add(new_booking)
    
    # Simulate Real-time Seat Occupancy Increment
    lounge.occupancy += 1
    
    db.commit()
    db.refresh(new_booking)
    return {"message": "Booking successful", "booking_id": new_booking.id, "is_paid": new_booking.is_paid, "qr_code": qr_data}
