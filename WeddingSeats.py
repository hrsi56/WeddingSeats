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
    populate_seats,  # נוסיף אותו כאן
    prepare_area_map
)

# ---- בניית בסיס המערכת ----
create_tables()

# בניית מפת האולם
area_map, ROWS, COLS = prepare_area_map()

# בדיקה אם מושבים קיימים, אחרת יצירה
with SessionLocal() as db:
    seats = get_all_seats(db)
    if not seats:
        populate_seats(db, area_map)
        st.success("✔️ הוזנו כיסאות לאולם. ניתן להתחבר כעת.")
        st.rerun()  # רענון כדי שהכיסאות ייטענו

# ---- התחברות / רישום ----
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

# ---- מסך אדמין ----
if 'admin' in st.session_state and st.session_state['admin']:
    st.header("🎩 מסך אדמין - ניהול האולם")

    with SessionLocal() as db:
        seats_data = get_all_seats(db)
        users_data = get_all_users(db)

    st.subheader("מפת מושבים")

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
                owner_name = owner.name if owner else "תפוס"
                cols[c].button(owner_name, disabled=True)
            elif seat and seat.status == 'free':
                cols[c].button(label, disabled=True)

    st.markdown("---")

    st.subheader("📋 רשימת משתמשים")
    df_users = pd.DataFrame([{
        "שם": u.name,
        "טלפון": u.phone,
        "סוג": u.user_type,
        "רזרבות": u.reserve_count
    } for u in users_data])
    st.dataframe(df_users)

    st.subheader("📊 סיכום תפוסה לפי אזורים")
    area_summary = {}
    for seat in seats_data:
        if seat.area:
            area_summary.setdefault(seat.area, {"taken": 0, "total": 0})
            area_summary[seat.area]["total"] += 1
            if seat.status == 'taken':
                area_summary[seat.area]["taken"] += 1

    summary_df = pd.DataFrame([
        {"אזור": k, "תפוסים": v["taken"], "סה\"כ": v["total"]}
        for k, v in area_summary.items()
    ])
    st.dataframe(summary_df)

    st.subheader("🛠 פעולות ניהול")

    if st.button("איפוס אולם"):
        with SessionLocal() as db:
            reset_all_seats(db)
        st.success("האולם אופס בהצלחה!")
        st.experimental_rerun()

    if st.button("📥 הורד רשימת משתמשים ל-CSV"):
        st.download_button(
            label="הורד קובץ",
            data=df_users.to_csv(index=False).encode('utf-8'),
            file_name="users_list.csv",
            mime="text/csv"
        )

# ---- מסך משתמש רגיל ----
elif 'user' in st.session_state:
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