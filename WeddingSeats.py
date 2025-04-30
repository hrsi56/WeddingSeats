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
    populate_seats,
    prepare_area_map,
    update_user_num_guests,
    Seat  # הוספתי כאן!
)

from database import  User

# אתחול
create_tables()
area_map, ROWS, COLS = prepare_area_map()

# מילוי מושבים אם אין
with SessionLocal() as db:
    if not get_all_seats(db):
        populate_seats(db, area_map)
        st.success("✔️ הוזנו כיסאות לאולם. מרענן...")
        st.rerun()

# התחברות
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
                # יצירת משתמש חדש כאורח כברירת מחדל
                user = create_user(db, name.strip(), phone.strip(), user_type='guest', reserve_count=0)
                st.success("נרשמת בהצלחה כאורח!")
                st.session_state['user'] = user



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
        "רזרבות": u.reserve_count,
	    "מגיע": u.is_coming

    } for u in users])
    st.dataframe(df_users)
    st.subheader("🪑 מפת מושבים")

    seats_status = {(seat.row, seat.col): seat for seat in seats}
    users_dict = {u.id: u.name for u in users}

    for r in range(ROWS):
        cols = st.columns(COLS)
        for c in range(COLS):
            seat = seats_status.get((r, c))
            if seat:
                if seat.status == 'free':
                    text = seat.area
                else:
                    # שליפת שם בעלים לפי owner_id
                    owner_name = users_dict.get(seat.owner_id, "תפוס")
                    text = owner_name
                key = f"admin_seat_{r}_{c}"
                cols[c].button(text, disabled=True, key=key)
            else:
                cols[c].empty()

    if st.button("🔄 איפוס אולם"):
        with SessionLocal() as db:
            reset_all_seats(db)
        st.success("האולם אופס!")
        st.rerun()

    st.stop()

# ---- מסך משתמש רגיל ----
elif 'user' in st.session_state:
    user = st.session_state['user']

    if user.user_type == 'user':

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
                    st.rerun()
                else:
                    st.stop()

            with SessionLocal() as db:
                seats_data = get_all_seats(db)
                users_data = get_all_users(db)

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

            if 'selected_seats' not in st.session_state:
                # טעינה ראשונית - אם יש בחירות ישנות נטען אותן
                st.session_state['selected_seats'] = set(
                    (seat.row, seat.col) for seat in seats_data if seat.owner_id == user.id
                )

            selected = st.session_state['selected_seats']

            st.subheader(f"בחר {st.session_state['num_guests']} כיסאות:")

            for r in range(ROWS):
                cols = st.columns(COLS)
                for c in range(COLS):
                    seat = seats_status.get((r, c), None)
                    area = area_map[r][c]
                    if not area:
                        cols[c].empty()
                        continue

                    label = seat_numbers.get((r, c), "")

                    key = f"seat_user_{r}_{c}"

                    if seat and seat.status == 'taken' and seat.owner_id != user.id:
                        owner = next((u for u in users_data if u.id == seat.owner_id), None)
                        display_text = owner.name if owner else "תפוס"
                        cols[c].checkbox(display_text, key=key, value=True, disabled=True)
                    else:
                        is_selected = (r, c) in selected
                        checked = cols[c].checkbox(label, key=key, value=is_selected)

                        if checked:
                            if (r, c) not in selected:
                                if len(selected) < st.session_state['num_guests']:
                                    selected.add((r, c))
                                else:
                                    st.warning(f"לא ניתן לבחור יותר מ-{st.session_state['num_guests']} כיסאות.")
                        else:
                            if (r, c) in selected:
                                selected.discard((r, c))

            if selected:
                if len(selected) > st.session_state['num_guests']:
                    st.warning("")
                else:
                    if st.button("אשר בחירה ושלח"):
                        selected_coords = list(st.session_state['selected_seats'])
                        total_guests = st.session_state['num_guests']

                        if not selected_coords:
                            st.warning("לא נבחרו כיסאות.")
                        else:
                            with SessionLocal() as db:
                                # שחרור כל הכיסאות הישנים של המשתמש
                                old_seats = db.query(Seat).filter_by(owner_id=user.id).all()
                                for seat in old_seats:
                                    seat.status = 'free'
                                    seat.owner_id = None
                                db.commit()

                                # בדיקת זמינות ושמירה
                                if check_seats_availability(db, selected_coords):
                                    for row, col in selected_coords:
                                        assign_seat(db, row, col, area_map[row][col], user.id)

                                    chosen = len(selected_coords)
                                    reserves = total_guests - chosen
                                    with SessionLocal() as db:
                                        user = db.query(User).filter(User.id == user.id).first()
                                        user.reserve_count = reserves
                                        db.commit()

                                    st.success(
                                        f"✔")
                                    st.session_state['selected_seats'].clear()
                                    del st.session_state['num_guests']
                                    st.empty()  # מנקה את כל האלמנטים הקודמים
                                    st.markdown(
                                        """
                                        <div style='text-align:center; margin-top:100px;'>
                                            <h1 style='font-size:60px;'>תודה רבה! המקומות נשמרו בהצלחה  </h1>
                                        </div>
                                        """,
                                        unsafe_allow_html=True
                                    )
                                    st.stop()  # עוצר את המשך הריצה
                                else:
                                    st.error("❗ חלק מהמושבים כבר נתפסו. אנא בחר מחדש.")
                                    st.session_state['selected_seats'].clear()
                                    st.rerun()

        if coming_choice == "לא":
            st.empty()  # מנקה את כל האלמנטים הקודמים
            st.markdown(
                """
                <div style='text-align:center; margin-top:100px;'>
                    <h1 style='font-size:60px;'>מצטערים שלא תוכלו להגיע. תודה על העדכון  </h1>
                </div>
                """,
                unsafe_allow_html=True
            )
            st.stop()  # עוצר את המשך הריצה
    elif user.user_type == 'guest':
        coming_choice = st.radio("האם אתה מתכוון להגיע?", options=["כן", "לא"], index=None)
        if coming_choice == "כן":
            with st.form("guest_register"):
                guest_reserves = st.number_input("כמה מקומות תרצה?", min_value=1, step=1)
                submit_guest = st.form_submit_button("רשום אותי כאורח")

            if submit_guest:
                with SessionLocal() as db2:
                    user = create_user(db2, name.strip(), phone.strip(), "guest", reserve_count=guest_reserves)
                    st.success("נרשמת כאורח בהצלחה!")
                    st.session_state['user'] = user
                    st.empty()  # מנקה את כל האלמנטים הקודמים
                    st.markdown(
	                    """
						<div style='text-align:center; margin-top:100px;'>
							<h1 style='font-size:60px;'>תודה רבה! המקומות נשמרו בהצלחה  </h1>
						</div>
						""",
	                    unsafe_allow_html=True
                    )
                    st.stop()  # עוצר את המשך הריצה

        if coming_choice == "לא":
            st.empty()  # מנקה את כל האלמנטים הקודמים
            st.markdown(
                """
                <div style='text-align:center; margin-top:100px;'>
                    <h1 style='font-size:60px;'>מצטערים שלא תוכלו להגיע. תודה על העדכון  </h1>
                </div>
                """,
                unsafe_allow_html=True
            )
            st.stop()  # עוצר את המשך הריצה
