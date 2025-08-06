from sqlalchemy.orm import Session
from db import SessionLocal, engine
from models import Base, User
from auth import get_password_hash

def create_user():
    # Ensure tables are created
    Base.metadata.create_all(bind=engine)

    db: Session = SessionLocal()

    # ✅ Provide a valid email instead of None
    user = User(
        username="testuser2",
        email="test2@example.com",  
        hashed_password=get_password_hash("password123"),
        is_admin=False,
        role="user"
    )

    db.add(user)
    db.commit()
    db.refresh(user)
    db.close()

if __name__ == "__main__":
    create_user()
