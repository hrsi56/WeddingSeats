# WeddingSeats.py

import streamlit as st
import pandas as pd
from sqlalchemy.orm import Session
from database import (
    create_tables,
    SessionLocal,
    get_user_by_name_phone,
    create_user,
    get_all_users,
    get_all_seats,
    assign_seat,
    check_seats_availability,
    reset_all_seats,
    populate_seats,
    prepare_area_map,
    update_user_num_guests,
    Seat
)

# הגדרת עמוד
st.set_page_config(layout="wide")

# --- אתחול בסיסי ---
create_tables()
area_map, ROWS, COLS = prepare_area_map()

with SessionLocal() as db:
    if not get_all_seats(db):
        populate_seats(db, area_map)
        st.success("✔️ הוזנו כיסאות לאולם. מרענן...")
        st.rerun()

# --- התחברות ---
st.title("💍 מערכת ניהול מושבים - החתונה")
st.header("התחברות / רישום")

if 'user' not in st.session_state and 'admin' not in st.session_state:
    with st.form("login_form"):
        name = st.text_input("שם מלא")
        phone = st.text_input("טלפון")
        submitted = st.form_submit_button("המשך")

    if submitted:
        if not phone.strip():
            st.warning("יש להזין טלפון.")
        elif name.strip() == "ירדן" and phone.strip() == "0547957141":
            st.success("ברוך הבא אדמין!")
            st.session_state['admin'] = True
            st.experimental_rerun()
        else:
            with SessionLocal() as db:
                user = get_user_by_name_phone(db, name.strip(), phone.strip())
                if user:
                    st.success(f"שלום {user.name}! רישום קיים.")
                    st.session_state['user'] = user
                    st.experimental_rerun()
                else:
                    with st.form("guest_register"):
                        guest_reserves = st.number_input("כמה מקומות ברזרבה תרצה?", min_value=1, step=1)
                        submit_guest = st.form_submit_button("רשום אותי כאורח")

                    if submit_guest:
                        with SessionLocal() as db2:
                            user = create_user(db2, name.strip(), phone.strip(), "guest", reserve_count=guest_reserves)
                            st.success("נרשמת כאורח בהצלחה!")
                            st.session_state['user'] = user
                            st.experimental_rerun()

# --- מסך אדמין ---
if 'admin' in st.session_state:
    st.header("🎩 מסך אדמין - ניהול האולם")

    with SessionLocal() as db:
        users = get_all_users(db)
        seats = get_all_seats(db)

    st.subheader("📋 טבלת משתמשים")
    df_users = pd.DataFrame([{
        "שם": u.name,
        "טלפון": u.phone,
        "סוג": u.user_type,
        "אורחים": u.num_guests,
        "רזרבות": u.reserve_count
    } for u in users])
    st.dataframe(df_users)

    st.subheader("🪑 מפת מושבים")

    seats_status = {(seat.row, seat.col): seat for seat in seats}
    for r in range(ROWS):
        cols = st.columns(COLS)
        for c in range(COLS):
            seat = seats_status.get((r, c))
            if seat:
                text = seat.area if seat.status == 'free' else 'תפוס'
                cols[c].button(text, disabled=True)

    if st.button("🔄 איפוס אולם"):
        with SessionLocal() as db:
            reset_all_seats(db)
        st.success("האולם אופס!")
        st.experimental_rerun()

    st.stop()

# --- מסך משתמש רגיל ---
elif 'user' in st.session_state:
    user = st.session_state['user']

    st.header(f"שלום {user.name} - בחירת כיסאות")

    with SessionLocal() as db:
        db_user = get_user_by_name_phone(db, user.name, user.phone)
        if not db_user:
            st.error("שגיאה בטעינת פרטי המשתמש.")
            st.stop()
        num_guests = db_user.num_guests or 1

    if 'num_guests' not in st.session_state:
        with st.form("guests_form"):
            guests = st.number_input("כמה אורחים מגיעים?", min_value=1, step=1, value=num_guests)
            submit_guests = st.form_submit_button("המשך")

        if submit_guests:
            with SessionLocal() as db:
                update_user_num_guests(db, user.id, guests)
            st.session_state['num_guests'] = guests
            st.success("✔️ מספר האורחים נשמר!")
            st.experimental_rerun()
        else:
            st.stop()

    with SessionLocal() as db:
        seats = get_all_seats(db)
        users = get_all_users(db)

    seats_status = {(seat.row, seat.col): seat for seat in seats}

    if 'selected_seats' not in st.session_state:
        st.session_state['selected_seats'] = set(
            (seat.row, seat.col) for seat in seats if seat.owner_id == user.id
        )

    selected = st.session_state['selected_seats']

    st.subheader(f"בחר {st.session_state['num_guests']} כיסאות:")

    for r in range(ROWS):
        cols = st.columns(COLS)
        for c in range(COLS):
            seat = seats_status.get((r, c))
            if not seat:
                cols[c].empty()
                continue

            key = f"seat_{r}_{c}"
            label = f"{seat.area}"

            if seat.status == 'taken' and seat.owner_id != user.id:
                owner = next((u for u in users if u.id == seat.owner_id), None)
                display_text = owner.name if owner else "תפוס"
                cols[c].checkbox(display_text, key=key, value=True, disabled=True)
            else:
                is_selected = (r, c) in selected
                checked = cols[c].checkbox(label, key=key, value=is_selected)
                if checked and (r, c) not in selected:
                    if len(selected) < st.session_state['num_guests']:
                        selected.add((r, c))
                    else:
                        st.warning(f"לא ניתן לבחור יותר מ-{st.session_state['num_guests']} מושבים.")
                elif not checked and (r, c) in selected:
                    selected.remove((r, c))

    if selected:
        if st.button("אשר בחירה ושלח"):
            selected_coords = list(st.session_state['selected_seats'])
            total_guests = st.session_state['num_guests']

            with SessionLocal() as db:
                # שחרור כיסאות ישנים
                db.query(Seat).filter(Seat.owner_id == user.id).update({"status": "free", "owner_id": None})
                db.commit()

                # בדיקת זמינות
                if check_seats_availability(db, selected_coords):
                    for row, col in selected_coords:
                        assign_seat(db, row, col, area_map[row][col], user.id)

                    chosen = len(selected_coords)
                    reserves = total_guests - chosen
                    if reserves > 0:
                        user.reserve_count += reserves
                        db.commit()

                    st.success(f"✔️ {chosen} כיסאות נבחרו. {reserves if reserves > 0 else 0} ברזרבה.")
                    st.session_state.clear()
                    st.experimental_rerun()
                else:
                    st.error("❗ חלק מהמושבים כבר נתפסו. אנא בחר מחדש.")
                    st.session_state['selected_seats'].clear()
                    st.experimental_rerun()