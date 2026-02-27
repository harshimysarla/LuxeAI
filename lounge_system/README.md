# Smart AI-Powered Airport Lounge Entry System

This is a hackathon demo project for a seamless, biometric-based lounge access system.

## Core Features
1. **Face Biometrics**: ArcFace-based registration and verification (Threshold: 0.20 distance).
2. **Express Entry**: Automated validation of Face + Booking + Payment.
3. **3D Glass UI**: Modern, cinematic, neo-dark interface.
4. **Admin Dashboard**: Real-time stats, revenue, and entry logs.
5. **Real-time Simulation**: Seat occupancy and crowd levels.

## Tech Stack
- **Backend**: FastAPI, DeepFace, ArcFace, SQLAlchemy, SQLite.
- **Frontend**: Vanilla JS, CSS Glassmorphism, Webcam API.

## Project Structure
```
lounge_system/
├── backend/
│   ├── routes/
│   ├── main.py
│   ├── models.py
│   ├── face_logic.py
│   ├── express_entry.py
│   └── database.py
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── app.js
└── requirements.txt
```

## Setup & Run

### 1. Backend
```bash
# Install dependencies
pip install -r requirements.txt

# Run the server
uvicorn lounge_system.backend.main:app --reload
```

### 2. Frontend
Simply open `lounge_system/frontend/index.html` in a modern web browser.
*(Note: Ensure Backend is running at http://localhost:8000)*

## Demo Credentials
- **Admin**: `admin` / `admin123`
- **User**: Register via the Signup page.
