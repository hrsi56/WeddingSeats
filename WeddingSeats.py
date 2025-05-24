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
    reset_all_seats,
    prepare_area_map,
    update_user_num_guests,
    Seat  # הוספתי כאן!
)

from database import  User

st.set_page_config(page_title="אישור הגעה לחתונה", layout="wide")

# עיצוב עולמי לדף בעברית
st.markdown("""
    <style>
    html, body, [class*="css"]  {
        direction: rtl;
        text-align: right;
    }

    input, textarea, select {
        direction: rtl;
        text-align: right;
    }

    label {
        display: block;
        text-align: right !important;
    }
    </style>
""", unsafe_allow_html=True)

# אתחול
create_tables()
area_map, ROWS, COLS = prepare_area_map()


st.markdown(
    """
    <h1 style='text-align: center; font-size: 40px;'>
        טובת רייטר וירדן ויקטור דג׳ורנו
        <br>
        💍 החתונה 💍
    </h1>
    """,
    unsafe_allow_html=True
)

# אם המשתמש סיים את ההזמנה

if st.session_state.get("finished") == "תודה":
    st.markdown(
        """
        <div style='text-align:center; margin-top:100px;'>
            <h1 style='font-size:60px;'>תודה רבה! המקומות נשמרו בהצלחה 
              </h1>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.stop()

if st.session_state.get("finished") == "מצטערים":
    st.markdown(
        """
        <div style='text-align:center; margin-top:100px;'>
            <h1 style='font-size:60px;'>מצטערים שלא תוכלו להגיע. תודה על העדכון  </h1>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.stop()


# התחברות
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
                st.session_state['מוזמן'] = user
            else:
                # יצירת משתמש חדש כאורח כברירת מחדל
                user = create_user(db, name.strip(), phone.strip(), user_type='אורח לא רשום', reserve_count=0)
                st.success("נרשמת בהצלחה כאורח!")
                st.session_state['מוזמן'] = user



# --- מסך אדמין ---
if 'admin' in st.session_state:
    st.header("🎩 מסך אדמין - ניהול האולם")

    with SessionLocal() as db:
        users = get_all_users(db)
        seats = get_all_seats(db)

    st.subheader("📋 טבלת משתמשים")
    df_users = pd.DataFrame([{
        "שם": u.name,
        "טלפון": int(u.phone),
        "סוג": u.user_type,
        "אורחים": u.num_guests,
        "רזרבות": u.reserve_count,
        "מגיע": u.is_coming
    } for u in users])
    st.dataframe(df_users)

    st.subheader("🪑 מפת מושבים (לפי אזורים ושולחנות)")
    users_dict = {u.id: u.name for u in users}

    # סידור לפי אזורים מתוך DB
    areas = sorted({seat.area for seat in seats if seat.area})

    for area in areas:
        with st.expander(f"אזור {area}", expanded=True):
            colss = sorted({seat.col for seat in seats if seat.area == area})
            for colll in colss:
                st.markdown(f"שולחן מספר {colll}")
                seats_in_area = [s for s in seats if (s.area == area and s.col == colll)]

                if seats_in_area:
                    seat_cols = st.columns(len(seats_in_area))
                    for i, seat in enumerate(seats_in_area):
                        with seat_cols[i]:
                            key = f"admin_seat_{seat.id}"
                            if seat.status == 'taken':
                                owner_name = users_dict.get(seat.owner_id, "תפוס")
                                st.button(owner_name, disabled=True, key=key)
                            else:
                                label = f"אזור {seat.area}"
                                st.button(label, disabled=True, key=key)

    if st.button("🔄 איפוס אולם"):
        with SessionLocal() as db:
            reset_all_seats(db)
        st.success("האולם אופס!")
        st.rerun()

    st.stop()

# ---- מסך משתמש רגיל ----
elif 'מוזמן' in st.session_state:
    user = st.session_state['מוזמן']

    if user.user_type == 'מוזמן':

        coming_choice = st.radio("האם אתה מתכוון להגיע?", options=["כן", "לא"], index=None)

        if coming_choice == "כן" :
            with SessionLocal() as db:
                db_user = get_user_by_name_phone(db, user.name, user.phone)
                db_user.is_coming = coming_choice
                db.commit()
            st.success("✔️ מצב ההגעה נשמר!")

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
                    old_seats = db.query(Seat).filter_by(owner_id=user.id).all()
                    for seat in old_seats:
                        seat.status = 'free'
                        seat.owner_id = None
                    db.commit()
                else:
                    st.stop()

            with SessionLocal() as db:
                seats_data = get_all_seats(db)
                users_data = get_all_users(db)


            if 'selected_seats' not in st.session_state:
                # טעינה ראשונית - אם יש בחירות ישנות נטען אותן
                st.session_state['selected_seats'] = set(
                    (seat.row, seat.col) for seat in seats_data if seat.owner_id == user.id
                )

            with SessionLocal() as db:
                seats_data = (
                    db.query(Seat)
                    .order_by(Seat.area, Seat.col, Seat.row)
                    .all()
                )
                users_data = db.query(User).all()

            selected = st.session_state['selected_seats']

            if len(selected) > st.session_state['num_guests']:
                st.session_state['stopstate'] = True
            else:
                st.session_state['stopstate'] = False

            # בתוך ה־elif 'מוזמן' in st.session_state:, במקום הקוד הקודם להצגת המפה:
            st.subheader(f"בחר {st.session_state['num_guests']} כיסאות:")
            # שליפה והכנה
            areas = sorted({seat.area for seat in seats_data if seat.area})

            if 'selected_seats' not in st.session_state:
                st.session_state['selected_seats'] = set(
                    seat.id for seat in seats_data if seat.owner_id == user.id
                )

            selected = st.session_state['selected_seats']

            st.subheader(f"בחר {st.session_state['num_guests']} כיסאות:")

            for area in areas:
                with st.expander(f"אזור {area}", expanded=True):
                    colss = sorted({seat.col for seat in seats_data if seat.area == area})
                    for colll in colss:
                        st.markdown(f"שולחן מספר {colll}")
                        seats_in_area = [s for s in seats_data if s.area == area and s.col == colll]

                        if seats_in_area:
                            seat_cols = st.columns(len(seats_in_area))
                            for i, seat in enumerate(seats_in_area):
                                with seat_cols[i]:
                                    key = f"seat_{seat.id}"
                                    if seat.status == 'taken' and seat.owner_id != user.id:
                                        owner = next((u for u in users_data if u.id == seat.owner_id), None)
                                        name_display = owner.name if owner else "תפוס"
                                        st.checkbox(name_display, value=True, disabled=True, key=key)
                                    else:
                                        label = f""
                                        is_sel = seat.id in selected
                                        checked = st.checkbox(label, key=key, value=is_sel)

                                        if checked and not is_sel:
                                            selected.add(seat.id)
                                        elif not checked and is_sel:
                                            selected.discard(seat.id)

            st.session_state['stopstate'] = len(selected) > st.session_state['num_guests']

            if selected:
                if st.session_state['stopstate']:
                    st.warning(f"בחר רק {st.session_state['num_guests']} כיסאות.")
                else:
                    if st.button("אשר בחירה ושלח"):
                        selected_ids = list(st.session_state['selected_seats'])
                        total_guests = st.session_state['num_guests']

                        if not selected_ids:
                            st.warning("לא נבחרו כיסאות.")
                        else:
                            with SessionLocal() as db:
                                # שחרור הכיסאות הקודמים
                                old_seats = db.query(Seat).filter_by(owner_id=user.id).all()
                                for seat in old_seats:
                                    seat.status = 'free'
                                    seat.owner_id = None
                                db.commit()

                                # שמירת הבחירה החדשה
                                for seat_id in selected_ids:
                                    seat = db.query(Seat).filter_by(id=seat_id).first()
                                    if seat:
                                        seat.status = 'taken'
                                        seat.owner_id = user.id
                                db.commit()

                                # חישוב רזרבות
                                chosen = len(selected_ids)
                                reserves = total_guests - chosen
                                db_user = db.query(User).filter(User.id == user.id).first()
                                db_user.reserve_count = reserves
                                db.commit()

                            st.success("✔")
                            st.session_state['selected_seats'].clear()
                            del st.session_state['num_guests']
                            st.session_state['finished'] = "תודה"
                            st.rerun()

        if coming_choice == "לא":
            with SessionLocal() as db:
                db_user = get_user_by_name_phone(db, user.name, user.phone)
                db_user.is_coming = coming_choice
                db.commit()
                try:
                    # שחרור כל הכיסאות הישנים של המשתמש
                    old_seats = db.query(Seat).filter_by(owner_id=user.id).all()
                    for seat in old_seats:
                        seat.status = 'free'
                        seat.owner_id = None
                    db.commit()
                except: pass
            st.session_state['finished'] = "מצטערים"
            st.rerun()  # מנקה את כל האלמנטים הקודמים

    elif user.user_type == 'אורח לא רשום':
        coming_choice = st.radio("האם אתה מתכוון להגיע?", options=["כן", "לא"], index=None)
        if coming_choice == "כן":
            with st.form("guest_register"):
                guest_reserves = st.number_input("כמה מקומות תרצה?", min_value=1, step=1)
                submit_guest = st.form_submit_button("רשום אותי כאורח")

            if submit_guest:
                with SessionLocal() as db:
                    update_user_num_guests(db, user.id, guest_reserves)
                    st.success("נרשמת כאורח בהצלחה!")
                    st.session_state['מוזמן'] = user
                    st.session_state['finished'] = "תודה"
                    st.rerun()  # מנקה את כל האלמנטים הקודמים

        if coming_choice == "לא":
            with SessionLocal() as db:
                db_user = get_user_by_name_phone(db, user.name, user.phone)
                db_user.is_coming = coming_choice
                db.commit()
                try:
                    # שחרור כל הכיסאות הישנים של המשתמש
                    old_seats = db.query(Seat).filter_by(owner_id=user.id).all()
                    for seat in old_seats:
                        seat.status = 'free'
                        seat.owner_id = None
                    db.commit()
                except: pass
            st.session_state['finished'] = "מצטערים"
            st.rerun()  # מנקה את כל האלמנטים הקודמים

