# database.py

import streamlit as st
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import pandas as pd

# יצירת בסיס מודלים
Base = declarative_base()

# קונפיגורציה מה-secrets
DB_URL = f"postgresql+psycopg2://{st.secrets['postgres']['user']}:{st.secrets['postgres']['password']}@{st.secrets['postgres']['host']}:{st.secrets['postgres']['port']}/{st.secrets['postgres']['dbname']}"

# יצירת engine ו-session
engine = create_engine(DB_URL, connect_args={"sslmode": "require"})
SessionLocal = sessionmaker(bind=engine)

# מודל משתמש
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(Text, nullable=False)
    phone = Column(Text, nullable=False)
    user_type = Column(Text, nullable=False)  # "user" או "guest"
    reserve_count = Column(Integer, default=0)

    seats = relationship("Seat", back_populates="owner")

# מודל מושב
class Seat(Base):
    __tablename__ = "seats"
    id = Column(Integer, primary_key=True, index=True)
    row = Column(Integer, nullable=False)
    col = Column(Integer, nullable=False)
    area = Column(Text, nullable=True)
    status = Column(Text, default="free")
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    owner = relationship("User", back_populates="seats")

# יצירת טבלאות אם לא קיימות
def create_tables():
    Base.metadata.create_all(bind=engine)

# פונקציות CRUD

def get_user_by_name_phone(db, name, phone):
    return db.query(User).filter(User.name == name, User.phone == phone).first()

def create_user(db, name, phone, user_type, reserve_count=0):
    user = User(name=name, phone=phone, user_type=user_type, reserve_count=reserve_count)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def get_all_users(db):
    return db.query(User).all()

def get_all_seats(db):
    return db.query(Seat).all()

def assign_seat(db, row, col, area, user_id):
    seat = db.query(Seat).filter(Seat.row == row, Seat.col == col).first()
    if seat:
        seat.status = 'taken'
        seat.owner_id = user_id
        db.commit()

def check_seats_availability(db, selected_coords):
    for row, col in selected_coords:
        seat = db.query(Seat).filter(Seat.row == row, Seat.col == col).first()
        if not seat or seat.status != 'free':
            return False
    return True

def reset_all_seats(db):
    seats = db.query(Seat).all()
    for seat in seats:
        seat.status = 'free'
        seat.owner_id = None
    db.commit()