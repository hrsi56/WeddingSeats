# WeddingSeats.py

import streamlit as st
import pandas as pd
from database import (
    create_tables,
    SessionLocal,
    get_user_by_name_phone,
    create_user,
    get_all_users,
    get_all_seats,
    assign_seat,
    check_seats_availability,
)
from areas import prepare_area_map

# יצירת טבלאות במסד הנתונים
create_tables()

# הכנת המפה והאולם
area_map, ROWS, COLS = prepare_area_map()

st.title("💍 מערכת ניהול מושבים - החתונה")

# טופס התחברות משתמש
st.header("התחברות / רישום")

with st.form("login_form"):
    name = st.text_input("שם מלא")
    phone = st.text_input("טלפון")
    submitted = st.form_submit_button("המשך")

if submitted:
    if not name or not phone:
        st.warning("יש להזין שם וטלפון.")
    else:
        with SessionLocal() as db:
            user = get_user_by_name_phone(db, name, phone)
            if user:
                st.success(f"שלום {user.name}! רישום קיים.")
                st.session_state['user'] = user
            else:
                st.warning("משתמש לא נמצא. תוכל להירשם כאורח.")

                with st.form("guest_register"):
                    guest_reserves = st.number_input("כמה מקומות ברזרבה תרצה?", min_value=1, step=1)
                    submit_guest = st.form_submit_button("רשום אותי כאורח")

                if submit_guest:
                    with SessionLocal() as db2:
                        user = create_user(db2, name, phone, "guest", reserve_count=guest_reserves)
                        st.success("נרשמת כאורח בהצלחה!")
                        st.session_state['user'] = user

# בדיקה אם יש משתמש מחובר
if 'user' in st.session_state:
    user = st.session_state['user']

    if user.user_type == 'user':
        st.header("בחירת כיסאות")

        with SessionLocal() as db:
            seats_data = get_all_seats(db)
            users_data = get_all_users(db)

        seats_status = {}
        seat_numbers = {}
        area_counters = {}

        for seat in seats_data:
            row, col = seat.row, seat.col
            area = seat.area
            seats_status[(row, col)] = seat

            if area:
                if area not in area_counters:
                    area_counters[area] = 1
                seat_numbers[(row, col)] = f"{area}{area_counters[area]}"
                area_counters[area] += 1

        # ניהול בחירה
        if 'selected_seats' not in st.session_state:
            st.session_state['selected_seats'] = set()

        selected = st.session_state['selected_seats']

        st.write("בחר את הכיסאות שלך:")

        for r in range(ROWS):
            cols = st.columns(COLS)
            for c in range(COLS):
                seat = seats_status.get((r, c), None)
                area = area_map[r][c]
                if not area:
                    cols[c].empty()
                    continue

                label = seat_numbers.get((r, c), "")

                if seat and seat.status == 'taken':
                    owner = next((u for u in users_data if u.id == seat.owner_id), None)
                    display_text = owner.name if owner else "תפוס"
                    cols[c].button(display_text, disabled=True)

                elif seat and seat.status == 'free':
                    key = f"seat_{r}_{c}"
                    is_selected = (r, c) in selected
                    button_text = f"{label} {'✅' if is_selected else ''}"
                    if cols[c].button(button_text, key=key):
                        if is_selected:
                            selected.remove((r, c))
                        else:
                            selected.add((r, c))

        if selected:
            if st.button("אשר בחירה ושלח"):
                selected_coords = list(st.session_state['selected_seats'])

                if not selected_coords:
                    st.warning("לא נבחרו כיסאות.")
                else:
                    with SessionLocal() as db:
                        if check_seats_availability(db, selected_coords):
                            for row, col in selected_coords:
                                assign_seat(db, row, col, area_map[row][col], user.id)
                            st.success("✔️ הכיסאות נשמרו עבורך!")
                            st.session_state['selected_seats'].clear()
                        else:
                            st.error("❗ חלק מהמושבים כבר נתפסו. אנא בחר מחדש.")
                            st.session_state['selected_seats'].clear()
                            st.experimental_rerun()

    elif user.user_type == 'guest':
        st.info("כאורח, הכיסאות שלך נרשמו ברזרבה בלבד.")

# קו מפריד
st.markdown("---")

# הצגת סיכום נתונים
st.header("📊 טבלת סיכום כללית")

with SessionLocal() as db:
    users_data = get_all_users(db)

if users_data:
    df = pd.DataFrame([{
        "שם": u.name,
        "טלפון": u.phone,
        "סוג משתמש": u.user_type,
        "רזרבות": u.reserve_count
    } for u in users_data])
    st.dataframe(df)
else:
    st.info("אין רישומים קיימים כרגע.")