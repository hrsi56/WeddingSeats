# WeddingSeats.py
import re
import streamlit as st
import pandas as pd
from sqlalchemy import false
from sqlalchemy.sql.sqltypes import NullType

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
st.set_page_config(page_title="טובת וירדן - החתונה", layout="wide")

st.markdown("""
<style>
/* עימוד כללי לעברית */
html, body, [class*="css"] {
    direction: rtl;
    text-align: right;
    font-family: "Segoe UI", "Helvetica Neue", sans-serif;
    background-color: #f7f7f7;
    color: #222;
}

/* כותרות */
h1, h2, h3 {
    text-align: center;
    direction: rtl;
    font-weight: 600;
    margin-top: 1rem;
    margin-bottom: 0.75rem;
    color: #2c3e50;
}
h1 { font-size: 28px !important; }
h2 { font-size: 24px !important; }
h3 { font-size: 20px !important; }

/* קלטים */
input, textarea, select {
    direction: rtl;
    text-align: right;
    background-color: white;
    border: 1px solid #ccc;
    border-radius: 6px;
    padding: 10px;
    width: 100%;
    font-size: 16px;
}

/* תוויות */
label {
    display: block;
    margin-bottom: 6px;
    font-weight: 500;
    color: #444;
}

/* כפתורים */
button[kind="primary"] {
    background-color: #4CAF50 !important;
    color: white !important;
    border: none;
    padding: 10px 24px;
    border-radius: 8px;
    font-size: 16px;
    font-weight: bold;
    transition: background-color 0.3s ease;
}
button[kind="primary"]:hover {
    background-color: #45a049 !important;
}

/* טבלאות */
table {
    width: 100%;
    border-collapse: collapse;
    direction: rtl;
    font-size: 15px;
}
thead {
    background-color: #e0e0e0;
    color: #000;
}
th, td {
    padding: 10px;
    border-bottom: 1px solid #ddd;
}
tbody tr:nth-child(even) {
    background-color: #f9f9f9;
}

/* הודעות */
div[data-testid="stAlert"] {
    border-radius: 10px;
    padding: 16px;
    font-size: 16px;
    direction: rtl;
}

/* קונטיינרים */
div[data-testid="stVerticalBlock"] {
    margin-bottom: 1rem;
}

/* קישורים */
a {
    color: #1f77b4;
    text-decoration: none;
}
a:hover {
    text-decoration: underline;
}

/* תיבות סימון ו-radio */
.stCheckbox > div, .stRadio > div {
    direction: rtl;
}
</style>
""", unsafe_allow_html=True)

weddate = "16.10.25"  # תאריך החתונה, ניתן לשנות לפי הצורך


from datetime import datetime,timedelta

today = datetime.today().date()
event_date = datetime.strptime(weddate, "%d.%m.%y").date()


if "logscreen" not in st.session_state:
    st.session_state.logscreen = False
    if today < event_date - timedelta(days=7):
        st.session_state.logscreen = True

if "serscreen" not in st.session_state:
    st.session_state.serscreen = False
    if today >= event_date - timedelta(days=7):
        st.session_state.serscreen = True



# אתחול
create_tables()
area_map, ROWS, COLS = prepare_area_map()

st.title("טובת רייטר וירדן ויקטור דג׳ורנו - 💍 החתונה 💍")

if st.session_state.get("finished") == "תודה":
    st.session_state.logscreen = False
    st.session_state.serscreen = False

    st.markdown(
        """
        <div style='text-align:center; margin-top:100px;'>
            <h1>תודה רבה! המקומות נשמרו בהצלחה 
              </h1>
        </div>
        """,
        unsafe_allow_html=True
    )

elif st.session_state.get("finished") == "מצטערים":
    st.session_state.logscreen = False
    st.session_state.serscreen = False

    st.markdown(
        """
        <div style='text-align:center; margin-top:100px;'>
            <h1>מצטערים שלא תוכלו להגיע. תודה על העדכון  </h1>
        </div>
        """,
        unsafe_allow_html=True
    )

else:


    if not st.session_state.serscreen:
        with st.form("Ser?"):
            serscreen = st.form_submit_button("חיפוש מקומות קיימים")
            if serscreen:
                st.session_state.serscreen = True
                st.session_state.logscreen = False
                st.rerun()

    if st.session_state.serscreen and not st.session_state.logscreen :

        st.title("🎟️ חיפוש מקומות ")
        query = st.text_input("🔍 חפש לפי שם או טלפון")
        st.button("חפש")  # לא עושה כלום, רק נותן תחושת שליטה למשתמש
        if query:
            with SessionLocal() as db:
                results = db.query(User).filter(
                    (User.name.ilike(f"%{query}%")) |
                    (User.phone.ilike(f"%{query}%"))
                ).all()

                if results:
                    data = []
                    for user in results:
                        seats = db.query(Seat).filter(Seat.owner_id == user.id).all()
                        for seat in seats:
                            data.append({
                                "כיסא": seat.row,
                                "שולחן": seat.col,
                                "איזור": seat.area,
                                "שם": user.name
                            })
                    df = pd.DataFrame(data)
                    st.dataframe(df)
                else:
                    st.info("לא נמצאו תוצאות מתאימות.")


        if not st.session_state.logscreen:
            with st.form("logyou?"):
                logscreen = st.form_submit_button("אני רוצה להתחבר / להרשם ")
                if logscreen:
                    st.session_state.logscreen = True
                    st.session_state.serscreen = False
                    st.rerun()


    if st.session_state.logscreen and not st.session_state.serscreen:

        # אם המשתמש סיים את ההזמנה

        # התחברות
        st.header("התחברות / רישום")

        with st.form("login_form"):
            name = st.text_input("שם מלא")
            phone = st.text_input("טלפון")
            phone = phone.strip()
            name = re.sub(' +', ' ', name.strip())
            submitted = st.form_submit_button("המשך")

        if submitted:
            if not phone.strip():
                st.warning("יש להזין מספר טלפון נייד.")
            elif not (len(phone.strip()) == 10) :
                st.warning("יש להזין מספר טלפון נייד בן 10 ספרות.")
            elif not (phone.strip().isdigit()):
                st.warning("יש להזין מספר טלפון נייד בספרות בלבד.")
            elif name.strip() == "ירדן" and phone.strip() == "0547957141":
                st.success("ברוך הבא אדמין!")
                st.session_state['admin'] = True
            elif not re.fullmatch(r'^[א-ת]{2,}( [א-ת]{2,})+$', name.strip())     :
                st.warning("יש להזין שם ושם משפחה, ובאותיות עבריות בלבד. (לדוגמא: ׳דגורנו׳ בלי צ׳ופצ׳יק)")
            else:
                with SessionLocal() as db:
                    user = get_user_by_name_phone(db, name.strip(), phone.strip())
                    if user:

                        st.success(f"שלום {user.name}! רישום קיים.")
                        st.session_state['מוזמן'] = user
                    else:
                        # יצירת משתמש חדש עם סוג מוזמן
                        user = create_user(db, name.strip(), phone.strip(), user_type='אורח לא רשום', reserve_count=0)
                        st.success("נרשמת בהצלחה!")
                        st.session_state['מוזמן'] = user



        # --- מסך אדמין ---
        if 'admin' in st.session_state:
            st.header("🎩 מסך אדמין - ניהול האולם")

            st.subheader("🔎 חיפוש ובחירת משתמש")

            search_query = st.text_input("הקלד שם או טלפון לחיפוש")
            selected_user = None  # <<< הגדרה ברירת מחדל חשובה

            if search_query:
                with SessionLocal() as db:
                    search_results = db.query(User).filter(
                        (User.name.ilike(f"%{search_query}%")) |
                        (User.phone.ilike(f"%{search_query}%"))
                    ).all()

                if search_results:
                    names = [f"{u.name} ({u.phone})" for u in search_results]
                    choice = st.selectbox("בחר משתמש מהתוצאות:", options=names)

                    # שליפת המשתמש לפי הבחירה
                    selected_user = next((u for u in search_results if f"{u.name} ({u.phone})" == choice), None)

            st.header("רישום חדש")

            with st.form("login_form2"):
                name = st.text_input("שם מלא")
                phone = st.text_input("טלפון")
                phone = phone.strip()
                name = re.sub(' +', ' ', name.strip())
                submitted = st.form_submit_button("המשך")

            if submitted:
                if not phone.strip():
                    st.warning("יש להזין מספר טלפון נייד.")
                elif not (len(phone.strip()) == 10):
                    st.warning("יש להזין מספר טלפון נייד בן 10 ספרות.")
                elif not (phone.strip().isdigit()):
                    st.warning("יש להזין מספר טלפון נייד בספרות בלבד.")
                elif name.strip() == "ירדן" and phone.strip() == "0547957141":
                    st.success("ברוך הבא אדמין!")
                    st.session_state['admin'] = True
                elif not re.fullmatch(r'^[א-ת]{2,}( [א-ת]{2,})+$', name.strip()):
                    st.warning("יש להזין שם ושם משפחה, ובאותיות עבריות בלבד. (לדוגמא: ׳דגורנו׳ בלי צ׳ופצ׳יק)")
                else:
                    with SessionLocal() as db:
                        userrrrr = get_user_by_name_phone(db, name.strip(), phone.strip())
                        if userrrrr:
                            st.success(f"שלום {user.name}! רישום קיים.")
                            selected_user = userrrrr
                        else:
                            # יצירת משתמש חדש עם סוג מוזמן
                            selected_user = create_user(db, name.strip(), phone.strip(), user_type='אורח לא רשום',
                                               reserve_count=0)

            if selected_user:
                st.success(f"נבחר: {selected_user.name} ({selected_user.phone})")
                st.markdown("#### פרטי המשתמש:")
                st.write({
                    "סוג": selected_user.user_type,
                    "אורחים": selected_user.num_guests,
                    "מגיע": selected_user.is_coming,
                })

                st.session_state[selected_user] = selected_user

                if st.session_state[selected_user]:
                    user = st.session_state[selected_user]
                    coming_choice = "כן"

                    if coming_choice == "כן" :
                        with SessionLocal() as db:
                            db_user = get_user_by_name_phone(db, user.name, user.phone)
                            db_user.is_coming = coming_choice
                            db.commit()

                        with SessionLocal() as db:
                            db_user = get_user_by_name_phone(db, user.name, user.phone)
                            num_guests = db_user.num_guests if db_user else 1

                        submit_guests = False

                        if 'num_guests' not in st.session_state:
                            with st.form("guests_form"):
                                guests = st.number_input("כמה אורחים הגיעו?", min_value=1, step=1, value=num_guests)
                                submit_guests = st.form_submit_button("המשך")

                        if submit_guests:
                            st.session_state['num_guests'] = guests

                        if st.session_state['num_guests']:
                            with SessionLocal() as db:
                                update_user_num_guests(db, user.id, guests)
                            st.success("✔️ מספר האורחים נשמר!")

                            old_seats = db.query(Seat).filter_by(owner_id=user.id).all()
                            for seat in old_seats:
                                seat.status = 'free'
                                seat.owner_id = None
                            db.commit()

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
                            # שליפה והכנה

                            with SessionLocal() as db:
                                area_options = [row[0] for row in db.query(Seat.area).distinct().all()]

                            with st.form("area_form"):
                                area_choice = st.selectbox("בחר אזור:", options=area_options,
                                                           index=area_options.index(user.area) if user.area else 0)
                                if st.form_submit_button("שלח בחירה"):
                                    st.session_state["area_chosen"] = True
                                    st.session_state["area_choice"] = area_choice
                                    with SessionLocal() as db:
                                        db_user = get_user_by_name_phone(db, user.name, user.phone)
                                        db_user.area = area_choice
                                        db.commit()

                            if st.session_state.get("area_chosen"):
                                area_choice = st.session_state["area_choice"]

                                areas = sorted({seat.area for seat in seats_data if seat.area == user.area})


                                st.subheader(f"בחר {st.session_state['num_guests']} כיסאות:")


                                if 'selected_seats' not in st.session_state:
                                    st.session_state['selected_seats'] = set(
                                        seat.id for seat in seats_data if seat.owner_id == user.id
                                    )

                                selected = st.session_state['selected_seats']

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

                                if st.session_state['stopstate']:
                                    st.warning(f"בחר רק {st.session_state['num_guests']} כיסאות.")
                                else:
                                    with st.form("confirm_seats"):
                                        confirm_seats_b = st.form_submit_button("אשר בחירה")
                                    if confirm_seats_b:
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


                seats_list = db.query(Seat).filter_by(owner_id=user.id).all()
                seat_info = [
                    {
                        "שולחן": seat.col ,
                        "שורה": seat.row ,
                        "איזור": seat.area
                    }
                    for seat in seats_list
                ]

                st.write({
                    "שם": selected_user.name,
                    "אורחים": selected_user.num_guests,
                    "רזרבות": db_user.reserve_count,
                    "איזור": selected_user.area,
                    "כיסאות": seat_info
                })



            with SessionLocal() as db:
                users = get_all_users(db)
                seats = get_all_seats(db)


            st.subheader("📋 טבלת משתמשים ברזרבה")
            df_users = pd.DataFrame([{
                "רזרבות": u.reserve_count,
                "אורחים": u.num_guests,
                "סוג": u.user_type,
                "טלפון": int(u.phone),
                "שם": u.name
            } for u in users if u.reserve_count > 0])
            st.dataframe(df_users)


            st.subheader("📋 טבלת משתמשים")
            df_users = pd.DataFrame([{
                "מגיע": u.is_coming,
                "רזרבות": u.reserve_count,
                "אורחים": u.num_guests,
                "סוג": u.user_type,
                "טלפון": int(u.phone),
                "שם": u.name
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



        # ---- מסך משתמש רגיל ----
        elif 'מוזמן' in st.session_state:
            user = st.session_state['מוזמן']

            if user.user_type == 'מוזמן' or user.user_type == 'נרשם מאוחר':

                coming_choice = st.radio("האם אתה מתכוון להגיע?", options=["כן", "לא"], index=None)

                if coming_choice == "כן" :
                    with SessionLocal() as db:
                        db_user = get_user_by_name_phone(db, user.name, user.phone)
                        db_user.is_coming = coming_choice
                        db.commit()
                    st.success("✔️ מצב ההגעה נשמר!")

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
                        else:
                            st.stop()

                        if user.area is None:
                            with SessionLocal() as db:
                                area_options = [row[0] for row in db.query(Seat.area).distinct().all()]

                            area_choice = st.selectbox("בחר איזור ישיבה:", options=area_options,
                                                       index=area_options.index(user.area) if user.area else 0)
                            send = st.button("שלח בחירה")
                            if send:
                                with SessionLocal() as db:
                                    db_user = get_user_by_name_phone(db, user.name, user.phone)
                                    db_user.area = area_choice
                                    db.commit()
                            else:
                                st.stop()

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
                        except:
                            pass
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

import qrcode
from PIL import Image, ImageDraw, ImageFont
import streamlit as st
from io import BytesIO
import base64

def create_qr_with_text(url, text):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=15,  # מגדיל את גודל התמונה
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white").convert('RGB')
    draw = ImageDraw.Draw(img)

    font_size = 200
    try:
        # פונט עבה אם זמין
        font = ImageFont.truetype("arialbd.ttf", font_size)
    except:
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except:
            font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    img_width, img_height = img.size
    x = (img_width - text_width) // 2
    y = (img_height - text_height) // 2

    padding = 20  # יותר רווח סביב הטקסט
    draw.rectangle(
        [(x - padding, y - padding), (x + text_width + padding, y + text_height + padding)],
        fill="white"
    )
    draw.text((x, y), text, font=font, fill="black")

    return img

def image_to_base64(img):
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()

def display_clickable_qr(img, link, caption):
    img_base64 = image_to_base64(img)
    html = f"""
    <div style="text-align: center">
        <a href="{link}" target="_blank">
            <p style="font-weight: bold; font-size: 20px;">{caption}</p>        
            <img src="data:image/png;base64,{img_base64}" style="width: 70%; max-width: 300px;" />
        </a>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


import random

# הגרלת מספר שלם בין 1 ל-100
number = random.randint(1, 1000)

# בדיקת זוגיות
if number % 2 == 0:
    bit_link = "https://www.bitpay.co.il/app/me/E9049ECA-8141-BA0B-2447-B065756C7CE27979"
    paybox_link = "https://link.payboxapp.com/MezqeVWwZKLExEqe9"

else:
    bit_link = "https://www.bitpay.co.il/app/me/CCB63470-71B9-3957-154F-F3E20BEBF8F452AD"
    paybox_link = "https://link.payboxapp.com/4bxjYRXxUs5ZNbGT8"

    

# יצירת QR עם טקסט מודגש באמצע
bit_img = create_qr_with_text(bit_link, "bit")
paybox_img = create_qr_with_text(paybox_link, "PayBox")

import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json

# קבלת הסודות מתוך st.secrets
service_account_info = st.secrets["gcp_service_account"]

# יצירת credentials מהסודות
creds = ServiceAccountCredentials.from_json_keyfile_dict(
    dict(service_account_info),
    scopes=[
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
)

client = gspread.authorize(creds)
sheet = client.open("wedding").sheet1


st.header("")
st.header("")

# UI

st.header("כתיבת ברכה לזוג המאושר")


with st.form("blessing_form"):
    name = st.text_input("שם")
    blessing = st.text_area("ברכה")
    submit = st.form_submit_button("שליחה")

    if submit:
        if name.strip() and blessing.strip():
            sheet.append_row([name, blessing])
            st.success("✅ הברכה נשלחה בהצלחה!")
        else:
            st.error("🛑 אנא מלאו את כל השדות.")

            st.title(" ")


# תצוגה זה לצד זה
col1, col2 = st.columns(2)

with col1:
    display_clickable_qr(bit_img, bit_link, "Bit")

with col2:
    display_clickable_qr(paybox_img, paybox_link, "PayBox")
