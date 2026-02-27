from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
import datetime
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String, default="user") # admin, premium, user
    is_active = Column(Boolean, default=True)

    face_embedding = relationship("FaceEmbedding", back_populates="owner", uselist=False)
    bookings = relationship("Booking", back_populates="owner")
    entry_logs = relationship("EntryLog", back_populates="user")

class FaceEmbedding(Base):
    __tablename__ = "face_embeddings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    embedding = Column(JSON) # Normalized vector

    owner = relationship("User", back_populates="face_embedding")

class Lounge(Base):
    __tablename__ = "lounges"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    airport = Column(String)
    total_seats = Column(Integer)
    occupancy = Column(Integer, default=0)

    bookings = relationship("Booking", back_populates="lounge")
    menu_items = relationship("MenuItem", back_populates="lounge")

class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    lounge_id = Column(Integer, ForeignKey("lounges.id"))
    date = Column(DateTime, default=datetime.datetime.utcnow)
    slot = Column(String) # e.g., "10:00-12:00"
    status = Column(String, default="confirmed")
    is_paid = Column(Boolean, default=False)
    flight_number = Column(String, nullable=True)
    qr_code = Column(String, nullable=True) # Base64 or string
    check_in_time = Column(DateTime, nullable=True)
    check_out_time = Column(DateTime, nullable=True)

    owner = relationship("User", back_populates="bookings")
    lounge = relationship("Lounge", back_populates="bookings")
    orders = relationship("Order", back_populates="booking")

class EntryLog(Base):
    __tablename__ = "entry_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    lounge_id = Column(Integer, ForeignKey("lounges.id"))
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    status = Column(String) # Access Granted, Access Denied
    reason = Column(String)
    check_out_time = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="entry_logs")

class MenuItem(Base):
    __tablename__ = "menu_items"

    id = Column(Integer, primary_key=True, index=True)
    lounge_id = Column(Integer, ForeignKey("lounges.id"))
    name = Column(String)
    description = Column(String)
    price = Column(Float)
    is_veg = Column(Boolean, default=True)
    is_available = Column(Boolean, default=True)
    image_url = Column(String, nullable=True)

    lounge = relationship("Lounge", back_populates="menu_items")
    order_items = relationship("OrderItem", back_populates="menu_item")

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    booking_id = Column(Integer, ForeignKey("bookings.id"))
    status = Column(String, default="pending") # pending, served
    total_price = Column(Float)

    booking = relationship("Booking", back_populates="orders")
    items = relationship("OrderItem", back_populates="order")

class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    menu_item_id = Column(Integer, ForeignKey("menu_items.id"))
    quantity = Column(Integer, default=1)

    order = relationship("Order", back_populates="items")
    menu_item = relationship("MenuItem", back_populates="order_items")
