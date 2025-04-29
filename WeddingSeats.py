# WeddingSeats.py

import streamlit as st
st.set_page_config(layout="wide")
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
    reset_all_seats,
    populate_seats,
    prepare_area_map,
    update_user_num_guests,
    Seat
)
from utils import generate_seating_html, tables_config

# אתחול בסיסי
create_tables()
area_map, ROWS, COLS = prepare_area_map()

# מילוי מושבים אם צריך
with SessionLocal() as db:
    if not get_all_seats(db):
        populate_seats(db, area_map)
        st.success("✔️ הוזנו כיסאות לאולם. מרענן...")
        st.rerun()

# --- התחברות ---

st.title("💍 מערכת ניהול מושבים - החתונה")
st.header("התחברות / רישום")

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
    else:
        with SessionLocal() as db:
            user = get_user_by_name_phone(db, name.strip(), phone.strip())
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
                        user = create_user(db2, name.strip(), phone.strip(), "guest", reserve_count=guest_reserves)
                        st.success("נרשמת כאורח בהצלחה!")
                        st.session_state['user'] = user

# --- מסך אדמין ---
if 'admin' in st.session_state and st.session_state['admin']:
    st.header("🎩 מסך אדמין - ניהול האולם")

    with SessionLocal() as db:
        seats_data = get_all_seats(db)
        users_data = get_all_users(db)

    seats_status = {(seat.row, seat.col): seat for seat in seats_data}

    st.subheader("מפת מושבים")

    cols = st.columns(6)
    i = 0
    for table_id, num_seats in tables_config.items():
        col = cols[i % 6]
        import streamlit.components.v1 as components
        html_code = generate_seating_html(table_id, num_seats)
        components.html(html_code, height=200)
        i += 1

    st.subheader("📋 רשימת משתמשים")
    df_users = pd.DataFrame([{
        "שם": u.name,
        "טלפון": u.phone,
        "סוג": u.user_type,
        "אורחים": u.num_guests,
        "רזרבות": u.reserve_count
    } for u in users_data])
    st.dataframe(df_users)

    st.subheader("🛠 פעולות ניהול")

    if st.button("איפוס אולם"):
        with SessionLocal() as db:
            reset_all_seats(db)
        st.success("האולם אופס בהצלחה!")
        st.rerun()

    if st.button("📥 הורד רשימת משתמשים ל-CSV"):
        st.download_button(
            label="הורד קובץ",
            data=df_users.to_csv(index=False).encode('utf-8'),
            file_name="users_list.csv",
            mime="text/csv"
        )

    st.stop()

# --- מסך משתמש רגיל ---
elif 'user' in st.session_state:
    user = st.session_state['user']

    if user.user_type == 'user':
        st.header("בחירת כיסאות")

        with SessionLocal() as db:
            db_user = get_user_by_name_phone(db, user.name, user.phone)
            num_guests = db_user.num_guests if db_user else 1

        if 'num_guests' not in st.session_state:
            with st.form("guests_form"):
                guests = st.number_input("כמה אורחים מגיעים?", min_value=1, step=1, value=num_guests)
                submit_guests = st.form_submit_button("המשך")

            if submit_guests:
                with SessionLocal() as db:
                    update_user_num_guests(db, user.id, guests)
                st.session_state['num_guests'] = guests
                st.success("✔️ מספר האורחים נשמר!")
                st.rerun()
            else:
                st.stop()

        if 'selected_seats' not in st.session_state:
            with SessionLocal() as db:
                seats_data = get_all_seats(db)
                st.session_state['selected_seats'] = set(
                    (seat.row, seat.col) for seat in seats_data if seat.owner_id == user.id
                )

        selected = st.session_state['selected_seats']

        st.subheader(f"בחר {st.session_state['num_guests']} כיסאות:")

        seats_data = get_all_seats(SessionLocal())
        users_data = get_all_users(SessionLocal())

        seats_status = {(seat.row, seat.col): seat for seat in seats_data}
        seat_numbers = {}
        area_counters = {}

        for seat in seats_data:
            row, col = seat.row, seat.col
            area = seat.area
            if area:
                if area not in area_counters:
                    area_counters[area] = 1
                seat_numbers[(row, col)] = f"{area}{area_counters[area]}"
                area_counters[area] += 1

        cols = st.columns(6)
        i = 0
        for table_id, num_seats in tables_config.items():
            col = cols[i % 6]
            import streamlit.components.v1 as components
            html_code = generate_seating_html(table_id, num_seats)
            components.html(html_code, height=200)
            i += 1

        if st.button("אשר בחירה ושלח"):
            with SessionLocal() as db:
                old_seats = db.query(Seat).filter_by(owner_id=user.id).all()
                for seat in old_seats:
                    seat.status = 'free'
                    seat.owner_id = None
                db.commit()

                if check_seats_availability(db, list(selected)):
                    for row, col in list(selected):
                        assign_seat(db, row, col, area_map[row][col], user.id)

                    chosen = len(selected)
                    reserves = st.session_state['num_guests'] - chosen
                    if reserves > 0:
                        user.reserve_count += reserves
                        db.commit()

                    st.success(
                        f"✔️ {chosen} כיסאות נשמרו עבורך. {reserves if reserves > 0 else 0} נרשמו ברזרבה."
                    )
                    st.session_state['selected_seats'].clear()
                    del st.session_state['num_guests']
                    st.rerun()
                else:
                    st.error("❗ חלק מהמושבים כבר נתפסו. אנא בחר מחדש.")
                    st.session_state['selected_seats'].clear()
                    st.rerun()

    elif user.user_type == 'guest':
        st.info("כאורח, הכיסאות שלך נרשמו כבר ברזרבה בלבד.")