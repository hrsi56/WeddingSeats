# WeddingSeats.py
import re
from operator import index

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
    Seat,  # הוספתי כאן!
    User
)






# הגדרות דף (כמו קודם, ללא ארגומנט theme כי הוא ב-config.toml)
st.set_page_config(
    page_title="טובת וירדן - החתונה",
    page_icon="💍",
    layout="wide",
    initial_sidebar_state="expanded",
)




# הסתרת תפריטים/לוגו/פוטר של Streamlit (כמו קודם)
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# CSS מותאם אישית חדש
st.markdown("""
<style>
/* -----------------------------------------------------------
   Streamlit RTL Hebrew Professional Theme
   -----------------------------------------------------------
   Author: <Add-Your-Name>
   Description: A polished, maintainable CSS theme for Streamlit
                dashboards that require right-to-left layout and
                elegant Hebrew typography.
   -----------------------------------------------------------*/

/* === 1. CSS Variables ==================================================== */
:root {
    /* Palette */
    --color-bg:           #faf7f5; /* רקע כללי */
    --color-surface:      #fcfcfc; /* רקע משני */
    --color-primary:      #B08D57; /* זהב מושתק */
    --color-primary-dark: #A07D47; /* hover state */
    --color-primary-dk2:  #806030; /* active state */
    --color-accent:       #84d3fa; /* תכלת עדין למסגרות וקישוטים */
    --color-text:         #4A3B31; /* חום כהה לטקסט */
    --color-table-head:   #B08D57; /* רקע ראש טבלה */

    /* Sizing */
    --radius:        8px;


    /* Effects */
    --shadow-sm:     0 2px 4px rgba(0,0,0,0.10);
    --shadow-md:     0 4px 8px rgba(0,0,0,0.15);
    --transition:    0.3s ease-in-out;
}

/* === 2. Base Layout & Typography ======================================== */
html, body, [class*="st-"] {
    direction: rtl !important;
    font-family: "Candara", "Optima", "Segoe UI", "Arial", sans-serif !important;
    color: var(--color-text);
    background-color: var(--color-bg);
}

/* Headings */
h1, .markdown-text-container h1,
h2, .markdown-text-container h2,
h3, .markdown-text-container h3 {
    text-align: center;

}

h1, .markdown-text-container h1 {
    color: var(--color-text);
    font-weight: 700;
    text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
}

/* h2 & h3 inherit color from root */

/* === 3. Buttons ========================================================= */
div.stButton > button {
    background-color: var(--color-primary) !important;
    color: var(--color-bg) !important;
    border: 1px solid var(--color-accent) !important;
    border-radius: var(--radius) !important;
    font-size: 16px;
    font-weight: 700;
    cursor: pointer;
    box-shadow: var(--shadow-sm);
    transition: all var(--transition);
}

div.stButton > button:hover {
    background-color: var(--color-primary-dark) !important;
    border-color: var(--color-primary-dark) !important;
    box-shadow: var(--shadow-md);
    transform: translateY(-2px);
}

div.stButton > button:active {
    background-color: var(--color-primary-dk2) !important;
    transform: translateY(0);
    box-shadow: var(--shadow-sm);
}

/* === 4. Text & Number Inputs =========================================== */
/* Wrapper */
.stTextInput div[data-baseweb="input"] > div,
.stNumberInput div[data-baseweb="input"] > div {
    display: flex;
    align-items: center;
    background-color: var(--color-surface) !important;
    border: 1px solid var(--color-accent) !important;
    border-radius: var(--radius) !important;
    transition: border-color var(--transition), box-shadow var(--transition);
}
/* Inner input */
.stTextInput input[type="text"],
.stNumberInput input[type="number"] {
    flex: 1;
    background: transparent;
    border: none;
    outline: none;

    font-size: 16px;
    color: var(--color-text) !important;
}
/* Focus state */
.stTextInput div[data-baseweb="input"] > div:focus-within,
.stNumberInput div[data-baseweb="input"] > div:focus-within {
    box-shadow: 0 0 0 0.1rem rgba(176, 141, 87, 0.25) !important;
}

/* === 5. Textarea ======================================================== */
.stTextArea textarea {
    background-color: var(--color-surface) !important;
    border: 1px solid var(--color-accent) !important;
    border-radius: var(--radius) !important;
    font-size: 16px;
    color: var(--color-text);
    min-height: 100px;
    transition: border-color var(--transition), box-shadow var(--transition);
}

.stTextArea textarea:focus {
    border-color: var(--color-primary) !important;
    box-shadow: 0 0 0 0.1rem rgba(176, 141, 87, 0.25) !important;
}

/* Uniform spacing under each input */
.stTextInput, .stNumberInput, .stTextArea {
}

/* === 6. Tables & DataFrames ============================================ */
.stDataFrame, .stTable {
    background-color: var(--color-surface) !important;
    box-shadow: var(--shadow-sm);
    border: none !important;
}

/* Column headers */
.stDataFrame thead th, .stTable thead th {
    background-color: var(--color-table-head) !important;
    color: var(--color-text);
    font-weight: 700;
    border-bottom: 2px solid var(--color-accent) !important;
}

/* Rows */
.stDataFrame tbody tr:nth-child(even),
.stTable tbody tr:nth-child(even),
.stDataFrame tbody tr:nth-child(odd),
.stTable tbody tr:nth-child(odd) {
    background-color: var(--color-surface) !important;
}

.stDataFrame td, .stTable td {
    color: var(--color-text);
    border-bottom: 1px solid var(--color-accent);
}

/* === 7. Checkbox & Radio =============================================== */
.stCheckbox > label, .stRadio > label {
    flex-direction: row-reverse;
    align-items: center;
    text-align: right;
}

.stCheckbox > label span, .stRadio > label span {
}

.stCheckbox svg, .stRadio svg {
    color: var(--color-primary);
    fill: var(--color-primary);
}

/* Checkbox tick */
.stCheckbox svg path {
    fill: var(--color-bg);
}

/* === 8. Containers (Blocks) ============================================ */
div[data-testid="stVerticalBlock"],
div.stBlock {
    background-color: var(--color-bg);
}

/* Remove redundant borders / shadows from nested blocks */
div[data-testid*="stBlock"] > div:not([data-testid="stVerticalBlock"]):not([data-baseweb="card"]) {
    border: none !important;
    box-shadow: none !important;
}

/* ======================================================================= */
/*  סוף קובץ  */


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
if 'admin' not in st.session_state:
    st.header("טובת רייטר וירדן ויקטור דג׳ורנו - 💍 החתונה 💍")


if st.session_state.get("scroll_to_top"):
    st.markdown("""
        <script>
            window.scrollTo({top: 0, behavior: 'smooth'});
        </script>
    """, unsafe_allow_html=True)
    # מחיקת הדגל כדי לא לגלול שוב ברענון הבא
    del st.session_state["scroll_to_top"]

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


    if not st.session_state.serscreen and 'admin' not in st.session_state:
        with st.form("Ser?"):
            serscreen = st.form_submit_button("חיפוש ברשומות")
            if serscreen:
                st.session_state.serscreen = True
                st.session_state.logscreen = False
                st.rerun()

    if st.session_state.serscreen and not st.session_state.logscreen and 'admin' not in st.session_state:

        query = st.text_input("🔍 חפש לפי שם או טלפון")
        st.button("חפש")  # רק תחושת שליטה

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
                        if seats:
                            for seat in seats:
                                data.append({
                                    "טלפון": int(user.phone),
                                    "כיסא": seat.row,
                                    "שולחן": seat.col,
                                    "איזור": user.area,
                                    "אורחים": user.num_guests,
                                    "שם": user.name
                                })
                        else:
                            data.append({
                                "טלפון": int(user.phone),
                                "כיסא": "נא לגשת לכניסה לקבלת מקומות",
                                "שולחן": "—",
                                "איזור": user.area,
                                "אורחים": user.num_guests,
                                "שם": user.name

                            })
                    df = pd.DataFrame(data)
                    st.dataframe(df)
                else:
                    st.info("לא נמצאו תוצאות מתאימות.")


        if not st.session_state.logscreen:
            with st.form("logyou?"):
                logscreen = st.form_submit_button("אישור הגעה")
                if logscreen:
                    st.session_state.logscreen = True
                    st.session_state.serscreen = False
                    st.rerun()


    if st.session_state.logscreen and not st.session_state.serscreen and 'admin' not in st.session_state:

        # אם המשתמש סיים את ההזמנה

        # התחברות

        with st.form("login_form"):
            st.header("אישור הגעה")
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
                st.rerun()
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

        if 'done' not in st.session_state:
            st.session_state['done'] = False
        st.header("🎩 מסך אדמין - ניהול האולם")


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

        if st.button("בחר"):
            st.session_state['done'] = False


        with st.form("logyou? 2"):
            logscreen2 = st.form_submit_button("רישום חדש")
            if logscreen2:
                st.session_state.rishum = True
                st.rerun()
        if 'rishum' in st.session_state and st.session_state['rishum']:
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
                    st.session_state['admin'] = True
                elif not re.fullmatch(r'^[א-ת]{2,}( [א-ת]{2,})+$', name.strip()):
                    st.warning("יש להזין שם ושם משפחה, ובאותיות עבריות בלבד. (לדוגמא: ׳דגורנו׳ בלי צ׳ופצ׳יק)")
                else:
                    selected_user = create_user(db, name.strip(), phone.strip(), user_type='אורח לא רשום',
                                       reserve_count=0)

        if selected_user:
            st.session_state['selected_user'] = selected_user

        if 'selected_user' in st.session_state:
            user = st.session_state['selected_user']

        if 'selected_user' in st.session_state and st.session_state['done'] == False:
            st.session_state.rishum = False
            st.success(f"נבחר: {selected_user.name} ({selected_user.phone})")
            st.markdown("#### פרטי המשתמש:")
            st.write({
                "סוג": selected_user.user_type,
                "מגיע": selected_user.is_coming,
            })

            selected_user = st.session_state['selected_user']

            if selected_user:
                user = st.session_state['selected_user']
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

                    if 'num_guests' in st.session_state:
                        with SessionLocal() as db:
                            update_user_num_guests(db, user.id, st.session_state['num_guests'])
                        st.success("✔️ מספר האורחים נשמר!")



                        with SessionLocal() as db:
                            seats_data = (
                                db.query(Seat)
                                .order_by(Seat.area, Seat.col, Seat.row)
                                .all()
                            )
                            users_data = db.query(User).all()


                        st.session_state["was_area_choice"] = user.area

                        # בתוך ה־elif 'מוזמן' in st.session_state:, במקום הקוד הקודם להצגת המפה:
                        # שליפה והכנה

                        with SessionLocal() as db:
                            area_options = [row[0] for row in db.query(Seat.area).distinct().all()]

                        with st.form("area_form"):
                            area_choice = st.selectbox("בחר אזור:", options=area_options,
                                                       index=area_options.index(user.area) if user.area else 1)
                            if st.form_submit_button("שלח בחירה"):
                                st.session_state["area_chosen"] = True
                                st.session_state["area_choice"] = area_choice
                                with SessionLocal() as db:
                                    db_user = get_user_by_name_phone(db, user.name, user.phone)
                                    db_user.area = area_choice
                                    db.commit()

                                if st.session_state["area_choice"] != st.session_state["was_area_choice"]:
                                    with SessionLocal() as db:
                                        old_seats = db.query(Seat).filter_by(owner_id=user.id).all()
                                        for seat in old_seats:
                                            seat.status = 'free'
                                            seat.owner_id = None
                                        db.commit()
                                    with SessionLocal() as db:
                                        seats_data = (
                                            db.query(Seat)
                                            .order_by(Seat.area, Seat.col, Seat.row)
                                            .all()
                                        )

                                st.rerun()

                        if st.session_state.get("area_chosen"):
                            area_choice = st.session_state["area_choice"]

                            areas = sorted({seat.area for seat in seats_data if seat.area == user.area})

                            st.subheader(f"בחר {st.session_state['num_guests']} כיסאות:")



                            st.session_state['selected_seats'] = set(
                                seat.id for seat in seats_data if seat.owner_id == user.id
                            )

                            selected = st.session_state['selected_seats']

                            if len(selected) > st.session_state['num_guests']:
                                st.session_state['stopstate'] = True
                            else:
                                st.session_state['stopstate'] = False


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
                                                        label = user.name if seat.owner_id == user.id else " "
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

                                    st.session_state['done'] = True
                                    del st.session_state['selected_seats']
                                    del st.session_state['num_guests']
                                    del st.session_state['stopstate']
                                    del st.session_state['selected_user']
                                    del st.session_state["was_area_choice"]
                                    del st.session_state["area_chosen"]
                                    del st.session_state["area_choice"]

                                    st.session_state["scroll_to_top"] = True
                                    st.rerun()


        if st.session_state['done']:
            # שליפת הכיסאות של המשתמש
            seats_list = db.query(Seat).filter_by(owner_id=user.id).all()

            from collections import Counter

            # שלב 1: קיבוץ וספירה לפי מספר שולחן
            table_counts = Counter(seat.col for seat in seats_list)

            # שלב 2: יצירת טקסט ידידותי
            seats_display = [f"{count} מקומות בשולחן {table}" for table, count in sorted(table_counts.items())]

            # שלב 3: הצגה
            st.write(" | ".join(seats_display))

            # בניית טבלה עם פרטי המשתמש וכיסאות מעוצבים
            user_data = {
                "כמות אורחים": selected_user.num_guests,
                "רזרבות": selected_user.reserve_count,
                "מגיע": "כן" if selected_user.is_coming else "לא",
                "איזור נבחר": selected_user.area,
                "מיקומי כיסאות": "\n".join(seats_display) if seats_display else "לא שובצו כיסאות",
                "שם": selected_user.name
            }

            # הצגת הנתונים בטבלה אלגנטית
            st.markdown("### 🪑 מיקומי הישיבה של המשתמש")
            st.dataframe(pd.DataFrame([user_data]))



        with SessionLocal() as db:
            users = get_all_users(db)
            seats = get_all_seats(db)

        st.header("---------------------------------------------------------------------")

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
        users_data = db.query(User).all()

        # סידור לפי אזורים מתוך DB
        areas = sorted({seat.area for seat in seats if seat.area})

        for area in areas:
            with st.expander(f"אזור {area}", expanded=True):
                colss = sorted({seat.col for seat in seats if seat.area == area})
                for colll in colss:
                    seats_in_area = [s for s in seats if (s.area == area and s.col == colll)]
                    free_count = sum(1 for s in seats_in_area if s.status == 'free')

                    st.markdown(f"שולחן מספר {colll} . . . . . . . . {free_count} מקומות פנויים  ")

                    if seats_in_area:
                        seat_cols = st.columns(len(seats_in_area))
                        for i, seat in enumerate(seats_in_area):
                            with seat_cols[i]:
                                key = f"admin_seat_{seat.id}"
                                if seat.status == 'taken':
                                    owner = next((u for u in users_data if u.id == seat.owner_id), None)
                                    name_display = owner.name if owner else "תפוס"
                                    st.checkbox(name_display, value=True, disabled=True, key=key)
                                else:
                                    st.checkbox(" ", value=False, disabled=True, key=key)

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

    padding = 0  # יותר רווח סביב הטקסט
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
            <img src="data:image/png;base64,{img_base64}" style="width: 50%; max-width: 200px;" />
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

# קבלת הסודות מתוך st.secrets
service_account_info = st.secrets["gcp_service_account"]

# יצירת credentials
creds = ServiceAccountCredentials.from_json_keyfile_dict(
    dict(service_account_info),
    scopes=[
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
)

client = gspread.authorize(creds)

# פתיחת הגיליון הראשי פעם אחת בלבד
spreadsheet = client.open("wedding")

# גישה לשוניות רק פעם אחת
blessing_sheet = spreadsheet.worksheet("ברכות")
feedback_sheet = spreadsheet.worksheet("היכרויות")
freeWM = spreadsheet.worksheet("רווקים_רווקות")



# UI

with st.form("blessing_form"):
    st.subheader("📝 כתיבת ברכה לזוג המאושר")
    name = st.text_input("שם")
    blessing = st.text_area("ברכה")
    submit = st.form_submit_button("שליחה")

    if submit:
        if name.strip() and blessing.strip():
            blessing_sheet.append_row([name, blessing])
            st.success("✅ הברכה נשלחה בהצלחה!")
        else:
            st.error("🛑 אנא מלאו את כל השדות.")


# תצוגה זה לצד זה
col1, col2 = st.columns(2)

with col1:
    display_clickable_qr(bit_img, bit_link, "Bit")

with col2:
    display_clickable_qr(paybox_img, paybox_link, "PayBox")



st.header("📸 שתפו אותנו בתמונות מהאירוע 📸")
st.markdown("""
    <div style="text-align: center; margin-top: 20px;">
        <a href="https://photos.app.goo.gl/CXuHxit6c9J6rypy8" target="_blank">
            <img src="https://www.gizchina.com/wp-content/uploads/images/2025/02/Google-photos.png"
                 alt="Google Photos" style="width: 590px; border-radius: 3px; border: 1px solid !important;">
        </a>
    </div>
""", unsafe_allow_html=True)



def load_freewm_data():
    worksheet = spreadsheet.worksheet("רווקים_רווקות")
    data = worksheet.get_all_records()
    return pd.DataFrame(data)
st.header(" ")
st.header("💙 פינת ההיכרויות 💙")





with st.form("feedback_form2"):
    st.subheader("💞 קיר הרווקים והרווקות 💞")
    name_f = st.text_input("שם")
    gender = st.selectbox("מין", options=["בחר", "זכר", "נקבה"])
    onme = st.text_area("קצת עליי")
    submit_f = st.form_submit_button("שלח")

    if submit_f:
        if gender == "בחר":
            st.warning("אנא בחר מין")
        elif name_f.strip() and gender.strip():
            freeWM.append_row([onme, gender, name_f])
            st.success("✅ נשלח בהצלחה!")
            st.rerun()
        else:
            st.error("🛑 אנא מלאו את כל השדות.")


    df = load_freewm_data()

    # פילוח לגברים ולנשים (בהנחה שיש עמודה בשם "מין")
    df_men = df[df.iloc[:, 1] == "זכר"]
    df_women = df[df.iloc[:, 1] == "נקבה"]

    # שתי עמודות זו לצד זו
    col1, col2 = st.columns(2)


    with col1:
        st.markdown("### 👨 רווקים")
        df = df_men.iloc[:,[0,2]].reset_index(drop=True)

        # ── 1) משתמשים ב-Styler כדי להזריק CSS מסודר ──
        styled = (
            df.style
            # הטבלה עצמה: נמתחת ל-100 %, חלוקת רוחב שווה בין העמודות
            .set_table_styles([
                {"selector": "table",
                 "props": [("width", "100%"),
                           ("table-layout", "fixed"),
                           ("direction", "rtl")]},
                # התאים עצמם: עטיפת שורות ויישור לימין
                {"selector": "th, td",
                 "props": [("white-space", "normal"),
                           ("word-wrap", "break-word"),
                           ("text-align", "right")]}
            ])
            # ביטול גבולות דפדפן ישנים (רק אם תרצה עיצוב נקי)
            .set_properties(**{"border": "none"})
        )

        # ── 2) מציגים ב-Streamlit ──
        st.markdown(styled.to_html(), unsafe_allow_html=True)

    with col2:
        st.markdown("### 👩 רווקות")
        df = df_women.iloc[:,[0,2]].reset_index(drop=True)

        # ── 1) משתמשים ב-Styler כדי להזריק CSS מסודר ──
        styled = (
            df.style
            # הטבלה עצמה: נמתחת ל-100 %, חלוקת רוחב שווה בין העמודות
            .set_table_styles([
                {"selector": "table",
                 "props": [("width", "100%"),
                           ("table-layout", "fixed"),
                           ("direction", "rtl")]},
                # התאים עצמם: עטיפת שורות ויישור לימין
                {"selector": "th, td",
                 "props": [("white-space", "normal"),
                           ("word-wrap", "break-word"),
                           ("text-align", "right")]}
            ])
            # ביטול גבולות דפדפן ישנים (רק אם תרצה עיצוב נקי)
            .set_properties(**{"border": "none"})
        )

        # ── 2) מציגים ב-Streamlit ──
        st.markdown(styled.to_html(), unsafe_allow_html=True)

with st.form("feedback_form"):
    st.subheader("מישהו/י מצא/ה חן בעיניך? כתבו לנו ונדאג לברר אם זה הדדי")
    name_f = st.text_input("שם")
    feedback = st.text_area("ההודעה שלך")
    submit_f = st.form_submit_button("שלח")

    if submit_f:
        if name_f.strip() and feedback.strip():
            feedback_sheet.append_row([name_f, feedback])
            st.success("✅ נשלח בהצלחה!")
        else:
            st.error("🛑 אנא מלאו את כל השדות.")
st.stop()
