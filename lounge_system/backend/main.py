from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import engine, Base, SessionLocal
from .routes import auth_routes, face_routes, lounge_routes, admin_routes
from . import models, auth
import logging

# Initialize Database
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Smart AI Lounge Entry System")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(auth_routes.router)
app.include_router(face_routes.router)
app.include_router(lounge_routes.router)
app.include_router(admin_routes.router)

@app.on_event("startup")
async def startup_event():
    # Seed Initial Data if empty
    db = SessionLocal()
    try:
        if db.query(models.Lounge).count() == 0:
            # Create Lounges
            delhi_lounge = models.Lounge(name="Luxe Elite Lounge", airport="IGI Delhi (T3)", total_seats=50)
            mumbai_lounge = models.Lounge(name="Platinum Adani Lounge", airport="CSIA Mumbai (T2)", total_seats=40)
            db.add_all([delhi_lounge, mumbai_lounge])
            db.commit()

            # Create Menu Items with Images
            db.add_all([
                models.MenuItem(
                    lounge_id=delhi_lounge.id, 
                    name="Signature Paneer Tikka", 
                    description="Grilled cottage cheese with exotic spices and mint glaze", 
                    price=18.0, 
                    image_url="assets/paneer_tikka_dish_1772225812362.png"
                ),
                models.MenuItem(
                    lounge_id=delhi_lounge.id, 
                    name="Royal Butter Chicken", 
                    description="Tender chicken in creamy tomato velvet sauce", 
                    price=22.0, 
                    is_veg=False,
                    image_url="assets/butter_chicken_dish_1772225829349.png"
                ),
                models.MenuItem(
                    lounge_id=delhi_lounge.id, 
                    name="Zesty Grilled Salmon", 
                    description="Atlantic salmon with lemon zest and hand-picked asparagus", 
                    price=28.0, 
                    is_veg=False,
                    image_url="assets/grilled_salmon_dish.png"
                ),
                models.MenuItem(
                    lounge_id=delhi_lounge.id, 
                    name="Artisanal Buffet Spread", 
                    description="Unlimited access to our premium juice jars and appetizers", 
                    price=45.0, 
                    image_url="assets/luxury_lounge_buffet.png"
                ),
                models.MenuItem(
                    lounge_id=mumbai_lounge.id, 
                    name="Bombay Special Vada Pav", 
                    description="Authentic spicy potato slider with garlic chutney", 
                    price=8.0, 
                    is_veg=True
                ),
            ])
            
            # Create Admin User
            admin_user = models.User(
                username="admin", 
                hashed_password=auth.get_password_hash("admin123"), 
                role="admin"
            )
            db.add(admin_user)
            db.commit()
    finally:
        db.close()

@app.get("/")
def read_root():
    return {"message": "Welcome to Smart AI Lounge Entry API", "status": "running"}
