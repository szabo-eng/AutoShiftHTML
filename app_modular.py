"""
מערכת שיבוץ מבצעית 2026
גרסה מלאה עם כל התכונות
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import logging

# הגדרות לוגים
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# קבועים
REQUIRED_REQUEST_COLUMNS = ['שם', 'תאריך מבוקש', 'משמרת', 'תחנה']
REQUIRED_SHIFT_COLUMNS = ['משמרת', 'תחנה', 'סוג תקן']  # סדר מדויק כמו בקובץ
OPTIONAL_SHIFT_COLUMNS = ['שעות', 'תפקיד']  # עמודות אופציונליות
DAYS_HEB = {
    'Sunday': 'ראשון', 'Monday': 'שני', 'Tuesday': 'שלישי',
    'Wednesday': 'רביעי', 'Thursday': 'חמישי', 'Friday': 'שישי', 'Saturday': 'שבת'
}
DATE_FORMATS = ['%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y']

# Firebase - אופציונלי
try:
    import firebase_admin
    from firebase_admin import credentials, firestore
    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False
    logger.warning("Firebase not installed - running without database")

# הגדרות דף
st.set_page_config(
    page_title="מערכת שיבוץ מבצעית 2026", 
    page_icon="📅", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS מוטמע
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Heebo:wght@300;400;500;600;700;800&display=swap');

:root {
    --primary: #1a4d7a;
    --accent: #e67e22;
    --success: #27ae60;
    --danger: #e74c3c;
    --warning: #f39c12;
    --gray: #95a5a6;
}

/* RTL for entire app */
* {
    font-family: 'Heebo', sans-serif;
}

html, body, [class*="css"] {
    direction: rtl !important;
    text-align: right !important;
}

/* Fix Streamlit elements */
.stTextInput > div > div > input,
.stNumberInput > div > div > input,
.stSelectbox > div > div > div,
.stMultiSelect > div > div > div,
.stTextArea > div > div > textarea {
    direction: rtl !important;
    text-align: right !important;
}

/* Fix dataframes */
.dataframe {
    direction: rtl !important;
}

.dataframe th {
    text-align: right !important;
}

.dataframe td {
    text-align: right !important;
}

/* Fix buttons */
.stButton > button {
    width: 100%;
    border-radius: 8px;
    font-weight: 600;
    transition: all 0.3s;
    direction: rtl !important;
}

.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}

/* Fix file uploader */
.stFileUploader {
    direction: rtl !important;
}

/* Fix sidebar */
.css-1d391kg, [data-testid="stSidebar"] {
    direction: rtl !important;
}

.main {
    direction: rtl !important;
    background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
}

.day-header {
    background: linear-gradient(135deg, var(--primary) 0%, #2e6ba8 100%);
    color: white;
    padding: 1rem;
    border-radius: 8px;
    text-align: center;
    margin-bottom: 1rem;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.day-name {
    font-size: 1.1rem;
    font-weight: 700;
    display: block;
}

.day-date {
    font-size: 0.9rem;
    opacity: 0.9;
    display: block;
}

.shift-card {
    background: white;
    border-radius: 8px;
    padding: 1rem;
    margin-bottom: 0.75rem;
    border-right: 4px solid var(--primary);
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    transition: all 0.3s;
    direction: rtl;
    text-align: right;
}

.shift-card:hover {
    transform: translateX(-4px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}

.shift-card.assigned {
    border-right-color: var(--success);
    background: linear-gradient(to left, #ffffff, #d5f4e6);
}

.shift-card.empty {
    border-right-color: var(--warning);
    background: linear-gradient(to left, #ffffff, #fff4e6);
}

.shift-card.cancelled {
    border-right-color: var(--gray);
    background: linear-gradient(to left, #ffffff, #f0f0f0);
    opacity: 0.7;
}

/* צבעים לפי סוג משמרת */
.shift-card.morning {
    background: linear-gradient(to left, #ffffff, #ffe5cc) !important;
    border-right-color: #ff8c00 !important;
}

.shift-card.evening {
    background: linear-gradient(to left, #ffffff, #d4edda) !important;
    border-right-color: #28a745 !important;
}

.shift-card.night {
    background: linear-gradient(to left, #ffffff, #d1e7ff) !important;
    border-right-color: #0066cc !important;
}

.shift-card.morning.assigned {
    background: linear-gradient(to left, #fff5e6, #ffcc99) !important;
}

.shift-card.evening.assigned {
    background: linear-gradient(to left, #e8f5e9, #a5d6a7) !important;
}

.shift-card.night.assigned {
    background: linear-gradient(to left, #e6f2ff, #99c2ff) !important;
}

.shift-card.morning.empty {
    background: linear-gradient(to left, #fff8f0, #ffd9b3) !important;
}

.shift-card.evening.empty {
    background: linear-gradient(to left, #f1f8f4, #b8e0c0) !important;
}

.shift-card.night.empty {
    background: linear-gradient(to left, #f0f7ff, #b3d9ff) !important;
}

.shift-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.5rem;
}

.shift-title {
    font-weight: 700;
    font-size: 1rem;
    color: var(--primary);
}

.shift-employee {
    font-size: 0.95rem;
    color: #2c3e50;
    font-weight: 600;
}

.shift-station {
    font-size: 0.85rem;
    color: #7f8c8d;
    margin-top: 0.25rem;
}

.shift-station strong {
    color: #5a6c7d;
    font-weight: 600;
}

/* סימון מיוחד לאט"ן */
.shift-type-atan {
    font-weight: 600;
    color: #d32f2f !important;
    display: inline-flex;
    align-items: center;
    gap: 0.25rem;
}

.shift-type-atan::before {
    content: "🔒";
    font-size: 0.9em;
}

.status-badge {
    display: inline-block;
    padding: 0.25rem 0.75rem;
    border-radius: 12px;
    font-size: 0.75rem;
    font-weight: 600;
}

.status-assigned {
    background: var(--success);
    color: white;
}

.status-empty {
    background: var(--warning);
    color: white;
}

.status-cancelled {
    background: var(--gray);
    color: white;
}

/* Fix radio buttons */
.stRadio > div {
    direction: rtl !important;
}

/* Fix checkboxes */
.stCheckbox {
    direction: rtl !important;
}

/* Fix metrics */
[data-testid="stMetricValue"] {
    direction: ltr !important;
}
</style>
""", unsafe_allow_html=True)

# Firebase אתחול
db = None
if FIREBASE_AVAILABLE:
    try:
        if 'firebase' in st.secrets:
            if not firebase_admin._apps:
                cred = credentials.Certificate(dict(st.secrets['firebase']))
                firebase_admin.initialize_app(cred)
            db = firestore.client()
            logger.info("Firebase connected successfully")
    except Exception as e:
        logger.error(f"Firebase initialization failed: {e}")

# Helper Functions
def parse_date_safe(date_str):
    """המרת תאריך מחוזקת"""
    for fmt in DATE_FORMATS:
        try:
            return pd.to_datetime(date_str, format=fmt)
        except:
            continue
    try:
        return pd.to_datetime(date_str)
    except:
        return None

def get_day_name(date_str):
    """קבלת שם יום בעברית"""
    try:
        return DAYS_HEB.get(parse_date_safe(date_str).strftime('%A'), "")
    except:
        return ""

def get_week_start(date_str):
    """מחזיר תאריך ראשון של השבוע"""
    try:
        dt = parse_date_safe(date_str)
        if dt:
            days_since_sunday = (dt.weekday() + 1) % 7
            sunday = dt - pd.Timedelta(days=days_since_sunday)
            return sunday.strftime('%Y-%m-%d')
    except:
        pass
    return date_str

def validate_dataframes(req_df, shi_df):
    """בדיקת תקינות קבצים - רק בדיקת קיום עמודות, לא סדר"""
    errors = []
    
    # בדיקת קובץ בקשות - רק שהעמודות קיימות
    missing_req = set(REQUIRED_REQUEST_COLUMNS) - set(req_df.columns)
    if missing_req:
        errors.append(f"❌ עמודות חסרות בקובץ בקשות: {', '.join(missing_req)}")
    
    # בדיקת קובץ משמרות - רק שהעמודות קיימות
    missing_shi = set(REQUIRED_SHIFT_COLUMNS) - set(shi_df.columns)
    if missing_shi:
        errors.append(f"❌ עמודות חסרות בתבנית משמרות: {', '.join(missing_shi)}")
    
    return errors

def get_atan_column(df):
    """מציאת עמודת אט"ן - תומך בשמות שונים"""
    # רשימת שמות אפשריים
    possible_names = ['אטן', 'אט"ן', 'אט״ן', 'אטען', 'atan', 'מורשה']
    
    for col in df.columns:
        col_lower = col.lower().strip()
        # בדוק אם יש התאמה חלקית
        if any(name in col_lower for name in possible_names):
            return col
        # בדוק אם יש אט בעמודה
        if 'אט' in col:
            return col
    
    return None

def get_balance():
    """חישוב מאזן משמרות"""
    balance = {}
    for emp in st.session_state.final_schedule.values():
        balance[emp] = balance.get(emp, 0) + 1
    return balance

def auto_assign(dates, shi_df, req_df, balance):
    """שיבוץ אוטומטי עם כללים מתקדמים"""
    temp_schedule, temp_assigned = {}, {d: set() for d in dates}
    running_balance = balance.copy()
    atan_col = get_atan_column(req_df)
    
    # עקוב אחר שיבוצים שבועיים
    weekly_assignments = {}
    
    def get_week_key(date_str):
        """מחזיר מפתח שבוע"""
        try:
            date_obj = parse_date_safe(date_str)
            if date_obj:
                days_since_sunday = (date_obj.weekday() + 1) % 7
                sunday = date_obj - pd.Timedelta(days=days_since_sunday)
                return sunday.strftime('%Y-%m-%d')
        except:
            pass
        return date_str
    
    def get_hours_from_request(row):
        """מחלץ שעות מבקשה"""
        time_cols = [c for c in req_df.columns if 'שע' in c or 'זמן' in c or 'hour' in c.lower() or 'time' in c.lower()]
        if time_cols:
            hours_val = row[time_cols[0]] if time_cols[0] in row.index else None
            if pd.notna(hours_val):
                hours_str = str(hours_val).strip().replace(' ', '')
                return hours_str
        return None
    
    def get_hours_from_shift(shift_row):
        """מחלץ שעות ממשמרת"""
        time_cols = [c for c in shi_df.columns if 'שע' in c or 'זמן' in c or 'hour' in c.lower() or 'time' in c.lower()]
        if time_cols:
            hours_val = shift_row[time_cols[0]] if time_cols[0] in shift_row.index else None
            if pd.notna(hours_val):
                hours_str = str(hours_val).strip().replace(' ', '')
                return hours_str
        return None
    
    # מכסה שבועית
    WEEKLY_LIMIT = st.session_state.get('weekly_shift_limit', 5)
    
    for date_str in dates:
        week_key = get_week_key(date_str)
        
        for idx, shift_row in shi_df.iterrows():
            shift_key = f"{date_str}_{shift_row['תחנה']}_{shift_row['משמרת']}_{idx}"
            if shift_key in st.session_state.cancelled_shifts:
                continue
            
            # סינון מועמדים
            potential = req_df[
                (req_df['תאריך מבוקש'] == date_str) &
                (req_df['משמרת'] == shift_row['משמרת']) &
                (req_df['תחנה'] == shift_row['תחנה']) &
                (~req_df['שם'].isin(temp_assigned[date_str]))
            ].copy()
            
            # בדיקת שעות (אם מופעל)
            strict_hours = st.session_state.get('strict_hours_matching', True)
            shift_hours = get_hours_from_shift(shift_row)
            
            if strict_hours and shift_hours and not potential.empty:
                matching_hours = []
                for _, emp_row in potential.iterrows():
                    emp_hours = get_hours_from_request(emp_row)
                    if emp_hours and emp_hours == shift_hours:
                        matching_hours.append(emp_row['שם'])
                
                if matching_hours:
                    potential = potential[potential['שם'].isin(matching_hours)]
                else:
                    potential = potential.iloc[0:0]
            
            # בדיקת מכסה שבועית
            if not potential.empty and week_key:
                available_employees = []
                for emp_name in potential['שם'].unique():
                    emp_week_count = weekly_assignments.get(emp_name, {}).get(week_key, 0)
                    if emp_week_count < WEEKLY_LIMIT:
                        available_employees.append(emp_name)
                
                if available_employees:
                    potential = potential[potential['שם'].isin(available_employees)]
            
            # בדיקת אט"ן
            if "אט" in str(shift_row['סוג תקן']) and atan_col:
                potential = potential[potential[atan_col] == 'כן']
            
            # שיבוץ
            if not potential.empty:
                potential['score'] = potential['שם'].map(lambda x: running_balance.get(x, 0))
                best = potential.sort_values('score').iloc[0]['שם']
                temp_schedule[shift_key] = best
                temp_assigned[date_str].add(best)
                running_balance[best] = running_balance.get(best, 0) + 1
                
                # עדכן ספירה שבועית
                if week_key:
                    if best not in weekly_assignments:
                        weekly_assignments[best] = {}
                    weekly_assignments[best][week_key] = weekly_assignments[best].get(week_key, 0) + 1
    
    return temp_schedule, temp_assigned

@st.dialog("שיבוץ עובד", width="large")
def show_assignment_dialog(shift_key, date_str, station, shift_type, req_df, balance, shi_df):
    """דיאלוג שיבוץ ידני"""
    # פרטי משמרת
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"**📅 תאריך:** {date_str}")
    with col2:
        st.markdown(f"**🏢 תחנה:** {station}")
    with col3:
        st.markdown(f"**⏰ משמרת:** {shift_type}")
    
    st.markdown("---")
    
    if not isinstance(st.session_state.assigned_today, dict):
        st.session_state.assigned_today = {}
    
    already_working = st.session_state.assigned_today.get(date_str, set())
    
    # מועמדים
    all_candidates = req_df[
        (req_df['תאריך מבוקש'] == date_str) &
        (req_df['משמרת'] == shift_type) &
        (~req_df['שם'].isin(already_working))
    ].copy()
    
    all_candidates = all_candidates.drop_duplicates(subset=['שם'], keep='first')
    
    # בדיקת אט"ן
    shift_row = None
    for idx, s in shi_df.iterrows():
        test_key = f"{date_str}_{s['תחנה']}_{s['משמרת']}_{idx}"
        if test_key == shift_key:
            shift_row = s
            break
    
    is_atan_shift = False
    if shift_row is not None and "אט" in str(shift_row['סוג תקן']):
        is_atan_shift = True
        atan_col = get_atan_column(req_df)
        if atan_col:
            all_candidates['מורשה אטן'] = all_candidates[atan_col].apply(
                lambda x: '✅' if str(x).strip() == 'כן' else '❌'
            )
    
    if all_candidates.empty:
        st.warning(f"😕 אין עובדים שביקשו {shift_type} ב-{date_str}")
        if st.button("סגור", use_container_width=True):
            st.rerun()
    else:
        # הכנת נתונים
        all_candidates['מאזן משמרות'] = all_candidates['שם'].map(lambda x: balance.get(x, 0))
        all_candidates['תחנה מבוקשת'] = all_candidates['תחנה']
        all_candidates['התאמה'] = all_candidates['תחנה'].apply(
            lambda x: '🎯 תחנה מתאימה' if x == station else '⚪ תחנה אחרת'
        )
        
        # מיון
        all_candidates['sort_match'] = all_candidates['תחנה'].apply(lambda x: 0 if x == station else 1)
        all_candidates = all_candidates.sort_values(['sort_match', 'מאזן משמרות'])
        
        # עמודות להצגה
        columns_to_show = ['שם', 'תחנה מבוקשת', 'מאזן משמרות', 'התאמה']
        
        time_cols = [c for c in all_candidates.columns if 'שע' in c or 'זמן' in c]
        if time_cols:
            columns_to_show.insert(2, time_cols[0])
        
        if is_atan_shift and 'מורשה אטן' in all_candidates.columns:
            columns_to_show.insert(2, 'מורשה אטן')
        
        columns_to_show = [c for c in columns_to_show if c in all_candidates.columns]
        
        if is_atan_shift:
            st.info("ℹ️ משמרת אט\"ן - רק עובדים מורשים יכולים להישבץ")
        
        # טבלה
        st.dataframe(
            all_candidates[columns_to_show],
            use_container_width=True,
            hide_index=True,
            height=min(len(all_candidates) * 35 + 38, 300)
        )
        
        # סטטיסטיקה
        matching_station = len(all_candidates[all_candidates['תחנה מבוקשת'] == station])
        other_station = len(all_candidates) - matching_station
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("סה\"כ זמינים", len(all_candidates))
        with col2:
            st.metric("🎯 תחנה מתאימה", matching_station)
        with col3:
            st.metric("⚪ תחנה אחרת", other_station)
        
        st.markdown("---")
        
        # בחירה
        selectable_candidates = all_candidates.copy()
        if is_atan_shift and 'מורשה אטן' in all_candidates.columns:
            authorized = selectable_candidates[selectable_candidates['מורשה אטן'] == '✅']
            unauthorized = selectable_candidates[selectable_candidates['מורשה אטן'] == '❌']
            
            if not authorized.empty:
                st.markdown("### ✅ עובדים מורשים לאט\"ן:")
                selected = st.radio(
                    "בחר עובד מורשה:",
                    options=authorized['שם'].tolist(),
                    format_func=lambda x: f"👤 {x} • תחנה: {all_candidates[all_candidates['שם']==x]['תחנה מבוקשת'].values[0]} • מאזן: {balance.get(x, 0)}",
                    label_visibility="collapsed"
                )
                
                if not unauthorized.empty:
                    with st.expander(f"⚠️ {len(unauthorized)} עובדים ללא הרשאה"):
                        for name in unauthorized['שם'].tolist():
                            st.write(f"• {name}")
            else:
                st.warning("⚠️ אין עובדים מורשים זמינים")
                selected = st.radio(
                    "בחר עובד:",
                    options=selectable_candidates['שם'].tolist(),
                    format_func=lambda x: f"👤 {x} • מאזן: {balance.get(x, 0)}",
                    label_visibility="collapsed"
                )
        else:
            selected = st.radio(
                "בחר עובד לשיבוץ:",
                options=selectable_candidates['שם'].tolist(),
                format_func=lambda x: f"👤 {x} • תחנה: {all_candidates[all_candidates['שם']==x]['תחנה מבוקשת'].values[0]} • מאזן: {balance.get(x, 0)}",
                label_visibility="visible"
            )
        
        # כפתורים
        col1, col2 = st.columns([3, 1])
        with col1:
            if st.button("✅ שבץ עובד", type="primary", use_container_width=True):
                st.session_state.final_schedule[shift_key] = selected
                if date_str not in st.session_state.assigned_today:
                    st.session_state.assigned_today[date_str] = set()
                st.session_state.assigned_today[date_str].add(selected)
                
                selected_station = all_candidates[all_candidates['שם'] == selected]['תחנה מבוקשת'].values[0]
                if selected_station != station:
                    st.info(f"ℹ️ {selected} ביקש/ה תחנה {selected_station} אך שובץ/ה לתחנה {station}")
                
                st.success(f"✅ {selected} שובץ/ה!")
                st.rerun()
        with col2:
            if st.button("❌ ביטול", use_container_width=True):
                st.rerun()

# Session State
if 'final_schedule' not in st.session_state:
    st.session_state.final_schedule = {}
if 'assigned_today' not in st.session_state:
    st.session_state.assigned_today = {}
if 'cancelled_shifts' not in st.session_state:
    st.session_state.cancelled_shifts = set()

# Sidebar
with st.sidebar:
    st.markdown("# ⚙️ ניהול מערכת")
    
    # אינדיקטור Firebase
    if db:
        st.success("🟢 Database מחובר")
    else:
        st.warning("🟡 Database לא זמין")
    
    st.divider()
    
    st.markdown("### 📁 קבצים")
    req_file = st.file_uploader("בקשות עובדים", type=['csv'])
    shi_file = st.file_uploader("תבנית משמרות", type=['csv'])
    
    st.divider()
    
    # הגדרות
    st.markdown("### ⚙️ הגדרות שיבוץ")
    
    strict_hours = st.checkbox(
        "בדיקת שעות מדויקת",
        value=st.session_state.get('strict_hours_matching', True),
        help="עובד חייב לבקש את אותן שעות בדיוק"
    )
    st.session_state.strict_hours_matching = strict_hours
    
    if strict_hours:
        st.caption("✅ רק שעות תואמות")
    else:
        st.caption("⚠️ התעלמות משעות")
    
    weekly_limit = st.number_input(
        "מכסה שבועית",
        min_value=1,
        max_value=7,
        value=st.session_state.get('weekly_shift_limit', 5),
        help="מספר מקסימלי למשמרות בשבוע"
    )
    st.session_state.weekly_shift_limit = weekly_limit
    
    st.caption(f"📊 עד {weekly_limit} משמרות/שבוע")
    
    st.divider()
    
    if req_file and shi_file:
        if st.button("🪄 שיבוץ אוטומטי", type="primary", use_container_width=True):
            st.session_state.trigger_auto = True
            st.rerun()
    
    if st.session_state.final_schedule:
        if st.button("💾 שמור ל-Database", type="primary", use_container_width=True):
            if not db:
                st.error("❌ Database לא זמין")
            else:
                try:
                    with st.spinner('שומר...'):
                        batch = db.batch()
                        employees_data = {}
                        
                        for shift_key, employee in st.session_state.final_schedule.items():
                            parts = shift_key.split('_', 3)
                            date_str, station, shift_type = parts[0], parts[1], parts[2]
                            
                            if employee not in employees_data:
                                employees_data[employee] = {'shifts': [], 'total_shifts': 0}
                            
                            employees_data[employee]['shifts'].append({
                                'date': date_str,
                                'station': station,
                                'shift_type': shift_type,
                                'shift_key': shift_key
                            })
                            employees_data[employee]['total_shifts'] += 1
                            
                            doc_ref = db.collection('shifts').document(shift_key)
                            batch.set(doc_ref, {
                                'date': date_str,
                                'station': station,
                                'shift_type': shift_type,
                                'employee': employee,
                                'timestamp': firestore.SERVER_TIMESTAMP,
                                'status': 'assigned'
                            })
                        
                        for shift_key in st.session_state.cancelled_shifts:
                            parts = shift_key.split('_', 3)
                            doc_ref = db.collection('shifts').document(shift_key)
                            batch.set(doc_ref, {
                                'date': parts[0],
                                'station': parts[1],
                                'shift_type': parts[2],
                                'employee': None,
                                'timestamp': firestore.SERVER_TIMESTAMP,
                                'status': 'cancelled'
                            })
                        
                        for employee, data in employees_data.items():
                            doc_ref = db.collection('employee_history').document(employee)
                            existing_doc = doc_ref.get()
                            previous_total = existing_doc.to_dict().get('total_shifts', 0) if existing_doc.exists else 0
                            
                            batch.set(doc_ref, {
                                'name': employee,
                                'shifts': data['shifts'],
                                'current_period_total': data['total_shifts'],
                                'total_shifts': previous_total + data['total_shifts'],
                                'last_updated': firestore.SERVER_TIMESTAMP,
                                'last_shift_date': max([s['date'] for s in data['shifts']]) if data['shifts'] else None
                            }, merge=False)
                        
                        batch.commit()
                        st.success(f"✅ נשמרו {len(st.session_state.final_schedule)} משמרות + {len(employees_data)} עובדים!")
                        
                        with st.expander("📊 פירוט"):
                            for employee, data in employees_data.items():
                                st.write(f"**{employee}**: {data['total_shifts']} משמרות")
                
                except Exception as e:
                    st.error(f"❌ שגיאה: {str(e)}")
    
    # ייצוא מ-Database
    if db:
        st.divider()
        st.markdown("### 📥 ייצוא מ-Database")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📥 ייצא משמרות", use_container_width=True):
                try:
                    with st.spinner('מייצא מ-Database...'):
                        # קרא את כל המשמרות
                        shifts_ref = db.collection('shifts')
                        docs = shifts_ref.stream()
                        
                        shifts_data = []
                        for doc in docs:
                            data = doc.to_dict()
                            shifts_data.append({
                                'shift_key': doc.id,
                                'תאריך': data.get('date', ''),
                                'תחנה': data.get('station', ''),
                                'משמרת': data.get('shift_type', ''),
                                'עובד': data.get('employee', ''),
                                'סטטוס': data.get('status', ''),
                                'זמן שמירה': str(data.get('timestamp', ''))
                            })
                        
                        if shifts_data:
                            shifts_df = pd.DataFrame(shifts_data)
                            shifts_df['תאריך_sort'] = shifts_df['תאריך'].apply(parse_date_safe)
                            shifts_df = shifts_df.sort_values(['תאריך_sort', 'תחנה'])
                            shifts_df = shifts_df.drop(['shift_key', 'תאריך_sort'], axis=1)
                            
                            csv = shifts_df.to_csv(index=False, encoding='utf-8-sig')
                            st.download_button(
                                "⬇️ הורד משמרות",
                                csv,
                                f"db_shifts_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                                mime="text/csv",
                                use_container_width=True
                            )
                            st.info(f"📊 {len(shifts_data)} משמרות ב-Database")
                        else:
                            st.warning("אין משמרות ב-Database")
                
                except Exception as e:
                    st.error(f"❌ שגיאה: {str(e)}")
        
        with col2:
            if st.button("📥 ייצא עובדים", use_container_width=True):
                try:
                    with st.spinner('מייצא מ-Database...'):
                        # קרא את כל העובדים
                        employees_ref = db.collection('employee_history')
                        docs = employees_ref.stream()
                        
                        employees_data = []
                        for doc in docs:
                            data = doc.to_dict()
                            employees_data.append({
                                'שם': data.get('name', ''),
                                'סה"כ משמרות נוכחי': data.get('current_period_total', 0),
                                'סה"כ משמרות מצטבר': data.get('total_shifts', 0),
                                'משמרת אחרונה': data.get('last_shift_date', ''),
                                'עדכון אחרון': str(data.get('last_updated', ''))
                            })
                        
                        if employees_data:
                            employees_df = pd.DataFrame(employees_data)
                            employees_df = employees_df.sort_values('סה"כ משמרות מצטבר', ascending=False)
                            
                            csv = employees_df.to_csv(index=False, encoding='utf-8-sig')
                            st.download_button(
                                "⬇️ הורד עובדים",
                                csv,
                                f"db_employees_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                                mime="text/csv",
                                use_container_width=True
                            )
                            st.info(f"👥 {len(employees_data)} עובדים ב-Database")
                        else:
                            st.warning("אין עובדים ב-Database")
                
                except Exception as e:
                    st.error(f"❌ שגיאה: {str(e)}")
    
    if st.button("🧹 איפוס", use_container_width=True):
        st.session_state.clear()
        st.rerun()
    
    st.divider()
    
    if st.session_state.final_schedule:
        st.markdown("### 📊 סטטיסטיקות")
        c1, c2 = st.columns(2)
        with c1:
            st.metric("משמרות", len(st.session_state.final_schedule))
        with c2:
            st.metric("עובדים", len(set(st.session_state.final_schedule.values())))

# Main
st.title("📅 לוח שיבוצים")

if req_file and shi_file:
    try:
        # קרא קבצים עם טיפול בגרשיים ו-BOM
        req_df = pd.read_csv(req_file, encoding='utf-8-sig', quotechar='"', doublequote=True)
        shi_df = pd.read_csv(shi_file, encoding='utf-8-sig', quotechar='"', doublequote=True)
        
        # נקה רווחים מיותרים משמות עמודות
        req_df.columns = req_df.columns.str.strip()
        shi_df.columns = shi_df.columns.str.strip()
        
        # רשום תיקונים שבוצעו
        corrections = []
        
        # נקה רווחים מתוכן השעות (אם קיים)
        for df_name, df in [('בקשות', req_df), ('משמרות', shi_df)]:
            time_cols = [c for c in df.columns if 'שע' in c or 'זמן' in c or 'hour' in c.lower()]
            for col in time_cols:
                if col in df.columns:
                    # בדוק אם יש רווחים
                    has_spaces = df[col].astype(str).str.contains(' ').any()
                    df[col] = df[col].astype(str).str.replace(' ', '')
                    if has_spaces:
                        corrections.append(f"נוקו רווחים מעמודת שעות בקובץ {df_name}")
        
        # תקן פורמט שעות הפוך (23:00-15:00 -> 15:00-23:00)
        for df_name, df in [('בקשות', req_df), ('משמרות', shi_df)]:
            time_cols = [c for c in df.columns if 'שע' in c or 'זמן' in c or 'hour' in c.lower()]
            for col in time_cols:
                if col in df.columns:
                    # תקן שעות שמתחילות בשעה גבוהה ומסתיימות בנמוכה
                    def fix_time_format(time_str):
                        if pd.isna(time_str) or str(time_str).strip() == '' or str(time_str) == 'nan':
                            return time_str
                        time_str = str(time_str).strip()
                        if '-' in time_str:
                            parts = time_str.split('-')
                            if len(parts) == 2:
                                start, end = parts[0].strip(), parts[1].strip()
                                # אם השעה מתחילה אחרי שהיא מסתיימת, החלף
                                try:
                                    start_hour = int(start.split(':')[0])
                                    end_hour = int(end.split(':')[0])
                                    if start_hour > end_hour:
                                        return f"{end}-{start}"
                                except:
                                    pass
                        return time_str
                    
                    # החל את התיקון וספור כמה תוקנו
                    original_values = df[col].copy()
                    df[col] = df[col].apply(fix_time_format)
                    fixed_count = (original_values != df[col]).sum()
                    
                    if fixed_count > 0:
                        corrections.append(f"תוקנו {fixed_count} שעות הפוכות בקובץ {df_name}")
        
        # הצג הודעות תיקון
        if corrections:
            with st.expander("🔧 תיקונים אוטומטיים שבוצעו"):
                for correction in corrections:
                    st.info(f"✓ {correction}")
        
        errors = validate_dataframes(req_df, shi_df)
        if errors:
            for e in errors:
                st.error(e)
            st.stop()
        
        # הצג מידע על הקבצים
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.success(f"✅ {len(req_df)} בקשות")
        with col2:
            st.success(f"✅ {len(shi_df)} משמרות")
        with col3:
            st.success(f"✅ {len(req_df['שם'].unique())} עובדים")
        with col4:
            atan_col = get_atan_column(req_df)
            if atan_col:
                atan_count = len(req_df[req_df[atan_col] == 'כן'])
                st.success(f"✅ {atan_count} מורשי אט\"ן")
            else:
                st.info("ℹ️ אין עמודת אט\"ן")
        
        dates = sorted(req_df['תאריך מבוקש'].unique(), key=parse_date_safe)
        balance = get_balance()
        
        # הצג טווח תאריכים
        if dates:
            st.info(f"📅 תאריכים: {dates[0]} עד {dates[-1]} ({len(dates)} ימים)")
        
        # ייצוא
        if st.session_state.final_schedule:
            export_data = []
            
            for shift_key, employee in st.session_state.final_schedule.items():
                parts = shift_key.split('_')
                date_str, station, shift_type = parts[0], parts[1], parts[2]
                shift_idx = int(parts[3]) if len(parts) > 3 else 0
                
                shift_row = None
                if shift_idx < len(shi_df):
                    row = shi_df.iloc[shift_idx]
                    if row['תחנה'] == station and row['משמרת'] == shift_type:
                        shift_row = row
                
                if shift_row is None:
                    matching = shi_df[(shi_df['תחנה'] == station) & (shi_df['משמרת'] == shift_type)]
                    if not matching.empty:
                        shift_row = matching.iloc[0]
                
                hours = ""
                emp_request = req_df[
                    (req_df['שם'] == employee) &
                    (req_df['תאריך מבוקש'] == date_str) &
                    (req_df['משמרת'] == shift_type)
                ]
                
                if not emp_request.empty:
                    time_cols = [c for c in emp_request.columns if 'שע' in c or 'זמן' in c]
                    if time_cols:
                        hours_val = emp_request.iloc[0][time_cols[0]]
                        if pd.notna(hours_val):
                            hours = str(hours_val)
                
                requested_station = station
                if not emp_request.empty and 'תחנה' in emp_request.columns:
                    requested_station = emp_request.iloc[0]['תחנה']
                
                export_data.append({
                    'תאריך': date_str,
                    'יום': get_day_name(date_str),
                    'שעות': hours,
                    'משמרת': shift_type,
                    'תחנה משובצת': station,
                    'תחנה מבוקשת': requested_station,
                    'סוג תקן': shift_row['סוג תקן'] if shift_row is not None else '',
                    'שם עובד': employee,
                    'מאזן משמרות': balance.get(employee, 0),
                    'סטטוס': 'משובץ'
                })
            
            cancelled_data = []
            for shift_key in st.session_state.cancelled_shifts:
                parts = shift_key.split('_')
                date_str, station, shift_type = parts[0], parts[1], parts[2]
                shift_idx = int(parts[3]) if len(parts) > 3 else 0
                
                shift_row = None
                if shift_idx < len(shi_df):
                    row = shi_df.iloc[shift_idx]
                    if row['תחנה'] == station and row['משמרת'] == shift_type:
                        shift_row = row
                
                if shift_row is None:
                    matching = shi_df[(shi_df['תחנה'] == station) & (shi_df['משמרת'] == shift_type)]
                    if not matching.empty:
                        shift_row = matching.iloc[0]
                
                cancelled_data.append({
                    'תאריך': date_str,
                    'יום': get_day_name(date_str),
                    'שעות': '',
                    'משמרת': shift_type,
                    'תחנה משובצת': station,
                    'תחנה מבוקשת': '',
                    'סוג תקן': shift_row['סוג תקן'] if shift_row is not None else '',
                    'שם עובד': '',
                    'מאזן משמרות': '',
                    'סטטוס': 'מבוטל'
                })
            
            all_export_data = export_data + cancelled_data
            
            if all_export_data:
                export_df = pd.DataFrame(all_export_data)
                export_df['תאריך_sort'] = export_df['תאריך'].apply(parse_date_safe)
                export_df = export_df.sort_values(['תאריך_sort', 'תחנה משובצת', 'משמרת'])
                export_df = export_df.drop('תאריך_sort', axis=1)
                
                csv = export_df.to_csv(index=False, encoding='utf-8-sig')
                
                col_export, col_preview = st.columns([1, 3])
                with col_export:
                    st.download_button(
                        label="📥 ייצא CSV מלא",
                        data=csv,
                        file_name=f"shibutz_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                        mime="text/csv",
                        use_container_width=True,
                        type="primary"
                    )
                with col_preview:
                    with st.expander("👁️ תצוגה מקדימה"):
                        st.dataframe(export_df.head(20), use_container_width=True, height=200)
                        st.caption(f"📊 {len(export_data)} משובצות + {len(cancelled_data)} מבוטלות")
        
        st.markdown("---")
        
        # שיבוץ אוטומטי
        if st.session_state.get('trigger_auto'):
            with st.spinner('מבצע שיבוץ...'):
                temp_schedule, temp_assigned = auto_assign(dates, shi_df, req_df, balance)
                st.session_state.final_schedule, st.session_state.assigned_today = temp_schedule, temp_assigned
                st.session_state.trigger_auto = False
            
            total_shifts = len(shi_df) * len(dates)
            assigned_count = len(st.session_state.final_schedule)
            cancelled_count = len(st.session_state.cancelled_shifts)
            missing_count = total_shifts - assigned_count - cancelled_count
            
            st.success(f"✅ שיבוץ הושלם: {assigned_count} משמרות מתוך {total_shifts}")
            if missing_count > 0:
                st.warning(f"⚠️ {missing_count} משמרות חסרות - ראה דוח למטה")
            else:
                st.balloons()
            
            st.rerun()
        
        # מדדים
        if st.session_state.final_schedule:
            total = len(shi_df) * len(dates) - len(st.session_state.cancelled_shifts)
            assigned = len(st.session_state.final_schedule)
            
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("סך משמרות", total)
            c2.metric("משובצות", assigned)
            c3.metric("חסרות", total - assigned)
            c4.metric("השלמה", f"{assigned/total*100:.0f}%" if total > 0 else "0%")
        
        st.markdown("---")
        
        # לוח שיבוץ
        
        # אגדת צבעים
        st.markdown("""
        <div style="display: flex; justify-content: center; gap: 2rem; margin-bottom: 1rem; padding: 0.75rem; background: white; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            <div style="display: flex; align-items: center; gap: 0.5rem;">
                <div style="width: 20px; height: 20px; background: linear-gradient(to left, #ffffff, #ffe5cc); border: 2px solid #ff8c00; border-radius: 4px;"></div>
                <span style="font-weight: 600;">🌅 בוקר</span>
            </div>
            <div style="display: flex; align-items: center; gap: 0.5rem;">
                <div style="width: 20px; height: 20px; background: linear-gradient(to left, #ffffff, #d4edda); border: 2px solid #28a745; border-radius: 4px;"></div>
                <span style="font-weight: 600;">🌆 ערב</span>
            </div>
            <div style="display: flex; align-items: center; gap: 0.5rem;">
                <div style="width: 20px; height: 20px; background: linear-gradient(to left, #ffffff, #d1e7ff); border: 2px solid #0066cc; border-radius: 4px;"></div>
                <span style="font-weight: 600;">🌙 לילה</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        header_cols = st.columns(7)
        for i, d in enumerate(dates[:7]):
            with header_cols[i]:
                st.markdown(f'''
                <div class="day-header">
                    <span class="day-name">{get_day_name(d)}</span>
                    <span class="day-date">{d}</span>
                </div>
                ''', unsafe_allow_html=True)
        
        for idx, shift_row in shi_df.iterrows():
            cols = st.columns(7)
            for i, date_str in enumerate(dates[:7]):
                if i < len(cols):
                    with cols[i]:
                        shift_key = f"{date_str}_{shift_row['תחנה']}_{shift_row['משמרת']}_{idx}"
                        
                        # קבע צבע לפי סוג משמרת
                        shift_type_class = ""
                        shift_name = str(shift_row['משמרת']).lower()
                        if 'בוקר' in shift_name:
                            shift_type_class = "morning"
                        elif 'ערב' in shift_name:
                            shift_type_class = "evening"
                        elif 'לילה' in shift_name:
                            shift_type_class = "night"
                        
                        if shift_key in st.session_state.cancelled_shifts:
                            is_atan = "אט" in str(shift_row['סוג תקן'])
                            atan_badge = " 🔒" if is_atan else ""
                            st.markdown(f'''
                            <div class="shift-card cancelled {shift_type_class}">
                                <div class="shift-header">
                                    <span class="shift-title">{shift_row['משמרת']}{atan_badge}</span>
                                    <span class="status-badge status-cancelled">מבוטל</span>
                                </div>
                                <div class="shift-station" style="font-size: 0.85rem;">{shift_row['תחנה']} • {shift_row['סוג תקן']}</div>
                            </div>
                            ''', unsafe_allow_html=True)
                            
                            if st.button("🔄", key=f"restore_{shift_key}", use_container_width=True):
                                st.session_state.cancelled_shifts.remove(shift_key)
                                st.rerun()
                        
                        elif shift_key in st.session_state.final_schedule:
                            employee = st.session_state.final_schedule[shift_key]
                            is_atan = "אט" in str(shift_row['סוג תקן'])
                            atan_badge = " 🔒" if is_atan else ""
                            st.markdown(f'''
                            <div class="shift-card assigned {shift_type_class}">
                                <div class="shift-header">
                                    <span class="shift-title">{shift_row['משמרת']}{atan_badge}</span>
                                    <span class="status-badge status-assigned">✓</span>
                                </div>
                                <div class="shift-employee">{employee}</div>
                                <div class="shift-station" style="font-size: 0.85rem;">{shift_row['תחנה']} • {shift_row['סוג תקן']}</div>
                            </div>
                            ''', unsafe_allow_html=True)
                            
                            ca, cb = st.columns([3, 1])
                            with ca:
                                if st.button("🗑️", key=f"del_{shift_key}"):
                                    del st.session_state.final_schedule[shift_key]
                                    if date_str in st.session_state.assigned_today:
                                        st.session_state.assigned_today[date_str].discard(employee)
                                    st.rerun()
                            with cb:
                                if st.button("🚫", key=f"cancel_{shift_key}"):
                                    st.session_state.cancelled_shifts.add(shift_key)
                                    st.rerun()
                        
                        else:
                            is_atan = "אט" in str(shift_row['סוג תקן'])
                            atan_badge = " 🔒" if is_atan else ""
                            st.markdown(f'''
                            <div class="shift-card empty {shift_type_class}">
                                <div class="shift-header">
                                    <span class="shift-title">{shift_row['משמרת']}{atan_badge}</span>
                                    <span class="status-badge status-empty">ריק</span>
                                </div>
                                <div class="shift-station" style="font-size: 0.85rem;">{shift_row['תחנה']} • {shift_row['סוג תקן']}</div>
                            </div>
                            ''', unsafe_allow_html=True)
                            
                            ca, cb = st.columns([3, 1])
                            with ca:
                                if st.button("➕ שבץ", key=f"assign_{shift_key}"):
                                    show_assignment_dialog(shift_key, date_str, shift_row['תחנה'], 
                                                         shift_row['משמרת'], req_df, balance, shi_df)
                            with cb:
                                if st.button("🚫", key=f"cancel_{shift_key}"):
                                    st.session_state.cancelled_shifts.add(shift_key)
                                    st.rerun()
        
        # דוח חוסרים
        st.markdown("---")
        st.markdown("---")
        
        total_shifts = len(shi_df) * len(dates)
        assigned_count = len(st.session_state.final_schedule)
        cancelled_count = len(st.session_state.cancelled_shifts)
        missing_count = total_shifts - assigned_count - cancelled_count
        
        if missing_count > 0:
            st.markdown("## 📋 דוח חוסרים")
            st.warning(f"⚠️ {missing_count} משמרות חסרות מתוך {total_shifts}")
            
            with st.expander(f"👁️ הצג דוח - {missing_count} משמרות", expanded=False):
                missing_shifts = []
                
                for date_str in dates:
                    for idx, shift_row in shi_df.iterrows():
                        shift_key = f"{date_str}_{shift_row['תחנה']}_{shift_row['משמרת']}_{idx}"
                        
                        if shift_key not in st.session_state.final_schedule and shift_key not in st.session_state.cancelled_shifts:
                            potential = req_df[
                                (req_df['תאריך מבוקש'] == date_str) &
                                (req_df['משמרת'] == shift_row['משמרת']) &
                                (req_df['תחנה'] == shift_row['תחנה'])
                            ].copy()
                            
                            if potential.empty:
                                reason = "אין בקשות"
                            else:
                                already_working = st.session_state.assigned_today.get(date_str, set())
                                available = potential[~potential['שם'].isin(already_working)]
                                
                                if available.empty:
                                    reason = f"כל המבקשים משובצים ({len(potential)})"
                                else:
                                    reason = "לא ידוע"
                            
                            missing_shifts.append({
                                'תאריך': date_str,
                                'יום': get_day_name(date_str),
                                'תחנה': shift_row['תחנה'],
                                'משמרת': shift_row['משמרת'],
                                'סוג תקן': shift_row['סוג תקן'],
                                'סיבה': reason
                            })
                
                if missing_shifts:
                    missing_df = pd.DataFrame(missing_shifts)
                    
                    st.dataframe(
                        missing_df,
                        use_container_width=True,
                        hide_index=True,
                        height=min(len(missing_df) * 35 + 38, 400)
                    )
                    
                    st.markdown("#### 📊 פירוט לפי סיבה:")
                    reason_counts = missing_df['סיבה'].value_counts()
                    
                    cols = st.columns(min(len(reason_counts), 4))
                    for i, (reason, count) in enumerate(reason_counts.items()):
                        with cols[i % len(cols)]:
                            st.metric(reason, count)
                    
                    st.markdown("---")
                    csv_missing = missing_df.to_csv(index=False, encoding='utf-8-sig')
                    st.download_button(
                        label="📥 ייצא דוח חוסרים",
                        data=csv_missing,
                        file_name=f"missing_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                        mime="text/csv",
                        use_container_width=True,
                        type="primary"
                    )
                    
                    st.info("💡 ניתן לשבץ ידנית משמרות חסרות")
        else:
            if st.session_state.final_schedule:
                st.success("✅ כל המשמרות שובצו!")
    
    except Exception as e:
        st.error(f"❌ שגיאה: {str(e)}")
        logger.error(f"Error: {e}", exc_info=True)
else:
    st.info("📁 העלה קבצי בקשות ומשמרות להתחלה")
