# database.py

import streamlit as st
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.sql.sqltypes import NullType

# ---- חיבור למסד נתונים ----
DB_URL = f"postgresql+psycopg2://{st.secrets['postgres']['user']}:{st.secrets['postgres']['password']}@{st.secrets['postgres']['host']}:{st.secrets['postgres']['port']}/{st.secrets['postgres']['dbname']}"

engine = create_engine(DB_URL, connect_args={"sslmode": "require"})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

from sqlalchemy import Column, Integer, String, ForeignKey, Text, Boolean


# ---- מודלים ----

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(Text, nullable=False)
    phone = Column(Text, nullable=False)
    user_type = Column(Text, nullable=False)
    reserve_count = Column(Integer, default=0)
    num_guests = Column(Integer, default=1)  # ✅ שדה חדש: מספר אורחים
    is_coming = Column(Text, nullable=True)  # ערכים: 'כן', 'לא' או None
    seats = relationship("Seat", back_populates="owner")
    area = Column(Text, nullable=True)


class Seat(Base):
    __tablename__ = "seats"

    id = Column(Integer, primary_key=True, index=True)
    row = Column(Integer, nullable=False)
    col = Column(Integer, nullable=False)
    area = Column(Text, nullable=True)
    status = Column(Text, default="free")
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    owner = relationship("User", back_populates="seats")

# ---- פונקציות עזר ----

def create_tables():
    try:
        Base.metadata.create_all(bind=engine)
    except SQLAlchemyError as e:
        st.error(f"❗ שגיאה ביצירת טבלאות: {e}")

def prepare_area_map():
    areas = {
        'A': {'rows': (0, 2), 'cols': (0, 3)},
        'B': {'rows': (0, 1), 'cols': (4, 7)},
        'C': {'rows': (3, 5), 'cols': (0, 2)},
        'D': {'rows': (3, 5), 'cols': (3, 7)}
    }

    max_row = 0
    max_col = 0
    for bounds in areas.values():
        r_end = bounds['rows'][1]
        c_end = bounds['cols'][1]
        if r_end > max_row:
            max_row = r_end
        if c_end > max_col:
            max_col = c_end

    rows = max_row + 1
    cols = max_col + 1

    area_map = [['' for _ in range(cols)] for _ in range(rows)]
    for area, bounds in areas.items():
        r_start, r_end = bounds['rows']
        c_start, c_end = bounds['cols']
        for r in range(r_start, r_end + 1):
            for c in range(c_start, c_end + 1):
                area_map[r][c] = area

    return area_map, rows, cols


# ---- פונקציות CRUD ----

def get_user_by_name_phone(db, name, phone):
    return db.query(User).filter(User.phone == phone).first()

def create_user(db, name, phone, user_type, reserve_count=0, num_guests=1 , area = NullType):
    user = User(name=name, phone=phone, user_type=user_type, reserve_count=reserve_count, num_guests=num_guests , area = area)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def update_user_num_guests(db, user_id, num_guests):
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        user.num_guests = num_guests
        user.reserve_count = num_guests
        db.commit()

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