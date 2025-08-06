from passlib.hash import bcrypt
from sqlalchemy.orm import Session
from db import User, SessionLocal

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_user(db: Session, username: str, email: str, password: str, role="user"):
    hashed_pw = bcrypt.hash(password)
    user = User(username=username, email=email, hashed_password=hashed_pw, role=role, is_admin=(role == "admin"))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def authenticate_user(db: Session, email: str, password: str):
    user = db.query(User).filter(User.email == email).first()
    if not user or not bcrypt.verify(password, user.hashed_password):
        return None
    return user

def get_logged_in_user(request, db: Session):
    email = request.session.get("user_email")
    if not email:
        return None
    return db.query(User).filter(User.email == email).first()
