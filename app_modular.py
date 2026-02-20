"""
מערכת שיבוץ מבצעית 2026 - גרסה Standalone
כל הקוד בקובץ אחד - ללא תלות בקבצים חיצוניים
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
REQUIRED_SHIFT_COLUMNS = ['תחנה', 'משמרת', 'סוג תקן']
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
@import url('https://fonts.googleapis.com/css2?family=Heebo:wght@300;400;500;600;700;800&family=Rubik:wght@400;500;600;700&display=swap');

:root {
    --primary: #1a4d7a;
    --accent: #e67e22;
    --success: #27ae60;
    --danger: #e74c3c;
}

html, body, [class*="css"] { 
    font-family: 'Heebo', sans-serif; 
}

[data-testid="stAppViewContainer"],
[data-testid="stSidebar"],
[data-testid="stMain"] {
    direction: rtl !important; 
    text-align: right !important;
}

[data-testid="stAppViewContainer"] { 
    background: linear-gradient(135deg, #faf8f5 0%, #f4f1ed 100%); 
}

h1 { 
    font-family: 'Rubik', sans-serif !important; 
    font-weight: 800 !important;
    background: linear-gradient(135deg, var(--primary) 0%, #2e6ba8 100%);
    -webkit-background-clip: text !important; 
    -webkit-text-fill-color: transparent !important; 
}

.stButton > button {
    border-radius: 8px !important;
    font-weight: 600 !important;
    transition: all 0.3s ease !important;
}

.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, var(--primary) 0%, #2e6ba8 100%) !important;
    box-shadow: 0 4px 12px rgba(26, 77, 122, 0.3) !important;
}

.stButton > button[kind="primary"]:hover {
    transform: translateY(-2px) !important;
}

.day-header { 
    background: linear-gradient(135deg, var(--primary) 0%, #2e6ba8 100%);
    color: white; 
    padding: 1.5rem 1rem; 
    border-radius: 12px 12px 0 0;
    text-align: center; 
    margin-bottom: 0.5rem;
    box-shadow: 0 4px 12px rgba(26, 77, 122, 0.3);
}

.day-name { 
    font-size: 1.3rem; 
    font-weight: 700; 
    display: block; 
    margin-bottom: 0.25rem;
    font-family: 'Rubik', sans-serif;
}

.day-date { 
    font-size: 0.9rem; 
    opacity: 0.9; 
}

.shift-mini { 
    background: linear-gradient(135deg, #fff 0%, #f9f9f9 100%);
    padding: 1rem; 
    border-radius: 8px; 
    border-right: 5px solid var(--primary);
    margin-bottom: 1rem; 
    transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
    box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    position: relative;
}

.shift-mini::before {
    content: '';
    position: absolute;
    top: 0;
    right: 0;
    width: 100%;
    height: 100%;
    background: linear-gradient(135deg, transparent 0%, rgba(26, 77, 122, 0.03) 100%);
    opacity: 0;
    transition: opacity 0.3s ease;
}

.shift-mini:hover { 
    transform: translateX(-8px) translateY(-2px);
    box-shadow: 0 8px 24px rgba(0,0,0,0.1);
}

.shift-mini:hover::before {
    opacity: 1;
}

.shift-mini.atan { 
    border-right-color: var(--accent);
    background: linear-gradient(135deg, #fff9f0 0%, #fef5e7 100%);
}

.shift-top { 
    display: flex; 
    justify-content: space-between; 
    margin-bottom: 0.75rem;
    position: relative;
    z-index: 1;
}

.shift-title { 
    font-weight: 700; 
    font-size: 1.1rem;
    color: var(--primary);
    font-family: 'Rubik', sans-serif;
}

.shift-mini.atan .shift-title { 
    color: var(--accent);
}

.shift-badge { 
    padding: 0.25rem 0.75rem; 
    border-radius: 20px; 
    font-size: 0.75rem; 
    font-weight: 600;
    background: rgba(26, 77, 122, 0.1); 
    color: var(--primary);
}

.shift-mini.atan .shift-badge { 
    background: rgba(230, 126, 34, 0.1); 
    color: var(--accent);
}

.shift-station { 
    color: #7f8c8d; 
    font-size: 0.9rem; 
    margin-bottom: 0.75rem;
    font-weight: 500;
}

.shift-status { 
    padding: 0.75rem; 
    border-radius: 8px; 
    font-weight: 600; 
    font-size: 0.9rem;
    display: flex; 
    align-items: center; 
    gap: 0.5rem; 
    margin-bottom: 0.75rem;
    border: 1px solid;
}

.status-assigned { 
    background: linear-gradient(135deg, rgba(39, 174, 96, 0.1) 0%, rgba(39, 174, 96, 0.05) 100%);
    color: var(--success);
    border-color: rgba(39, 174, 96, 0.2);
}

.status-empty { 
    background: linear-gradient(135deg, rgba(231, 76, 60, 0.1) 0%, rgba(231, 76, 60, 0.05) 100%);
    color: var(--danger);
    border-color: rgba(231, 76, 60, 0.2);
}

.status-cancelled { 
    background: linear-gradient(135deg, rgba(127, 140, 141, 0.1) 0%, rgba(127, 140, 141, 0.05) 100%);
    color: #7f8c8d;
    border-color: rgba(127, 140, 141, 0.2);
}

[data-testid="stMetricValue"] {
    font-family: 'Rubik', sans-serif !important;
    font-size: 2rem !important;
    font-weight: 800 !important;
    color: var(--primary) !important;
}

.stSuccess {
    background: linear-gradient(135deg, rgba(39, 174, 96, 0.1) 0%, rgba(39, 174, 96, 0.05) 100%) !important;
    border-right: 4px solid var(--success) !important;
    border-radius: 8px !important;
}

.stError {
    background: linear-gradient(135deg, rgba(231, 76, 60, 0.1) 0%, rgba(231, 76, 60, 0.05) 100%) !important;
    border-right: 4px solid var(--danger) !important;
    border-radius: 8px !important;
}

@keyframes slideIn {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
}

[data-testid="column"] {
    animation: slideIn 0.5s ease-out;
}
</style>
""", unsafe_allow_html=True)

# Firebase
def initialize_firebase():
    if not FIREBASE_AVAILABLE:
        return None
    if not firebase_admin._apps:
        try:
            cred = credentials.Certificate(dict(st.secrets["firebase"]))
            firebase_admin.initialize_app(cred)
            logger.info("Firebase initialized")
        except Exception as e:
            logger.warning(f"Firebase not available: {e}")
            return None
    return firestore.client()

db = initialize_firebase()

# פונקציות עזר
def parse_date_safe(date_str):
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(str(date_str).strip(), fmt)
        except ValueError:
            continue
    raise ValueError(f"פורמט תאריך לא תקין: {date_str}")

def get_day_name(date_str):
    try:
        return DAYS_HEB.get(parse_date_safe(date_str).strftime('%A'), "")
    except:
        return ""

def get_week_start(date_str):
    """מחזיר תאריך ראשון של השבוע (ראשון) לתאריך נתון"""
    try:
        dt = parse_date_safe(date_str)
        if dt:
            # חשב כמה ימים עברו מאז ראשון
            days_since_sunday = (dt.weekday() + 1) % 7
            sunday = dt - pd.Timedelta(days=days_since_sunday)
            return sunday.strftime('%Y-%m-%d')
    except:
        pass
    return date_str

def validate_dataframes(req_df, shi_df):
    errors = []
    if set(REQUIRED_REQUEST_COLUMNS) - set(req_df.columns):
        errors.append("❌ עמודות חסרות בקובץ בקשות")
    if set(REQUIRED_SHIFT_COLUMNS) - set(shi_df.columns):
        errors.append("❌ עמודות חסרות בתבנית משמרות")
    return errors

def get_atan_column(df):
    cols = [c for c in df.columns if "אט" in c and "מורשה" in c]
    return cols[0] if cols else None

@st.cache_data(ttl=60)
def get_balance():
    scores = {}
    try:
        if db:
            for doc in db.collection('employee_history').stream():
                scores[doc.id] = doc.to_dict().get('total_shifts', 0)
    except:
        pass
    return scores

def get_employee_counts():
    """ספירת משמרות לכל עובד מהשיבוצים הנוכחיים"""
    counts = {}
    for shift_key, employee in st.session_state.final_schedule.items():
        counts[employee] = counts.get(employee, 0) + 1
    return counts

def auto_assign(dates, shi_df, req_df, balance):
    temp_schedule, temp_assigned = {}, {d: set() for d in dates}
    running_balance = balance.copy()
    atan_col = get_atan_column(req_df)
    
    # עקוב אחר שיבוצים שבועיים
    weekly_assignments = {}  # {employee: {week_key: count}}
    
    def get_week_key(date_str):
        """מחזיר מפתח שבוע (ראשון-שבת) לתאריך נתון"""
        try:
            date_obj = parse_date_safe(date_str)
            if date_obj:
                # חשב תאריך ראשון השבוע
                days_since_sunday = (date_obj.weekday() + 1) % 7
                sunday = date_obj - pd.Timedelta(days=days_since_sunday)
                return sunday.strftime('%Y-%m-%d')
        except:
            pass
        return date_str
    
    def get_hours_from_request(row):
        """מחלץ שעות מבקשת עובד"""
        time_cols = [c for c in req_df.columns if 'שע' in c or 'זמן' in c or 'hour' in c.lower() or 'time' in c.lower()]
        if time_cols:
            hours_val = row[time_cols[0]] if time_cols[0] in row.index else None
            if pd.notna(hours_val):
                # נקה רווחים ותווים מיוחדים
                hours_str = str(hours_val).strip().replace(' ', '')
                return hours_str
        return None
    
    def get_hours_from_shift(shift_row):
        """מחלץ שעות מתבנית משמרת"""
        time_cols = [c for c in shi_df.columns if 'שע' in c or 'זמן' in c or 'hour' in c.lower() or 'time' in c.lower()]
        if time_cols:
            hours_val = shift_row[time_cols[0]] if time_cols[0] in shift_row.index else None
            if pd.notna(hours_val):
                # נקה רווחים ותווים מיוחדים
                hours_str = str(hours_val).strip().replace(' ', '')
                return hours_str
        return None
    
    # מכסה שבועית (ניתן להגדרה)
    WEEKLY_LIMIT = st.session_state.get('weekly_shift_limit', 5)  # ברירת מחדל: 5 משמרות לשבוע
    
    for date_str in dates:
        week_key = get_week_key(date_str)
        
        for idx, shift_row in shi_df.iterrows():
            shift_key = f"{date_str}_{shift_row['תחנה']}_{shift_row['משמרת']}_{idx}"
            if shift_key in st.session_state.cancelled_shifts:
                continue
            
            # שלב 1: סינון מועמדים - עם כללים חדשים
            potential = req_df[
                (req_df['תאריך מבוקש'] == date_str) &
                (req_df['משמרת'] == shift_row['משמרת']) &
                (req_df['תחנה'] == shift_row['תחנה']) &
                (~req_df['שם'].isin(temp_assigned[date_str]))  # לא עובד היום
            ].copy()
            
            # בדיקת שעות - התאמה מדויקת (רק אם ההגדרה מופעלת)
            strict_hours = st.session_state.get('strict_hours_matching', True)
            shift_hours = get_hours_from_shift(shift_row)
            
            # DEBUG: הדפס מידע על השעות
            if shift_hours and strict_hours:
                logger.info(f"משמרת {shift_key}: שעות במשמרת = '{shift_hours}'")
            
            if strict_hours and shift_hours and not potential.empty:
                # סנן רק עובדים שביקשו את אותן שעות בדיוק
                matching_hours = []
                for _, emp_row in potential.iterrows():
                    emp_hours = get_hours_from_request(emp_row)
                    emp_name = emp_row['שם']
                    
                    # DEBUG: הדפס השוואה
                    logger.info(f"  עובד {emp_name}: שעות בבקשה = '{emp_hours}' | התאמה = {emp_hours == shift_hours}")
                    
                    if emp_hours and emp_hours == shift_hours:
                        matching_hours.append(emp_name)
                
                if matching_hours:
                    potential = potential[potential['שם'].isin(matching_hours)]
                    logger.info(f"  ✅ נמצאו {len(matching_hours)} עובדים עם התאמת שעות")
                else:
                    # אין התאמות - רוקן את potential
                    logger.warning(f"  ⚠️ אין עובדים עם התאמת שעות ל-{shift_hours}")
                    potential = potential.iloc[0:0]  # DataFrame ריק
            
            # בדיקת מכסה שבועית
            if not potential.empty and week_key:
                available_employees = []
                for emp_name in potential['שם'].unique():
                    emp_week_count = weekly_assignments.get(emp_name, {}).get(week_key, 0)
                    if emp_week_count < WEEKLY_LIMIT:
                        available_employees.append(emp_name)
                
                if available_employees:
                    potential = potential[potential['שם'].isin(available_employees)]
            
            # שלב 2: בדיקת אט"ן
            if "אט" in str(shift_row['סוג תקן']) and atan_col:
                potential = potential[potential[atan_col] == 'כן']
            
            # שלב 3 + 4: מיון לפי מאזן ושיבוץ
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
    # פרטי המשמרת - קומפקטי
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
    
    # כל העובדים שביקשו את אותו תאריך ואותה משמרת (ללא קשר לתחנה)
    all_candidates = req_df[
        (req_df['תאריך מבוקש'] == date_str) &
        (req_df['משמרת'] == shift_type) &
        (~req_df['שם'].isin(already_working))  # סנן משובצים
    ].copy()
    
    # הסר כפילויות - עובד שביקש כמה תחנות באותו יום/משמרת
    all_candidates = all_candidates.drop_duplicates(subset=['שם'], keep='first')
    
    # בדיקת אטן
    shift_row = None
    for idx, s in shi_df.iterrows():
        test_key = f"{date_str}_{s['תחנה']}_{s['משמרת']}_{idx}"
        if test_key == shift_key:
            shift_row = s
            break
    
    # סינון אט"ן אם נדרש
    is_atan_shift = False
    if shift_row is not None and "אט" in str(shift_row['סוג תקן']):
        is_atan_shift = True
        atan_col = get_atan_column(req_df)
        if atan_col:
            # שמור את כולם אבל סמן מי מורשה
            all_candidates['מורשה אטן'] = all_candidates[atan_col].apply(
                lambda x: '✅' if str(x).strip() == 'כן' else '❌'
            )
    
    if all_candidates.empty:
        st.warning(f"😕 אין עובדים שביקשו {shift_type} ב-{date_str}")
        st.info(f"💡 {len(already_working)} עובדים כבר משובצים ביום זה")
        if st.button("סגור", use_container_width=True):
            st.rerun()
    else:
        # הכנת נתונים לתצוגה
        all_candidates['מאזן משמרות'] = all_candidates['שם'].map(lambda x: balance.get(x, 0))
        
        # סמן האם התחנה מתאימה
        all_candidates['תחנה מבוקשת'] = all_candidates['תחנה']
        all_candidates['התאמה'] = all_candidates['תחנה'].apply(
            lambda x: '🎯 תחנה מתאימה' if x == station else '⚪ תחנה אחרת'
        )
        
        # מיון: קודם מתאימים, אחר כך לפי מאזן
        all_candidates['sort_match'] = all_candidates['תחנה'].apply(lambda x: 0 if x == station else 1)
        all_candidates = all_candidates.sort_values(['sort_match', 'מאזן משמרות'])
        
        # עמודות להצגה
        columns_to_show = ['שם', 'תחנה מבוקשת', 'מאזן משמרות', 'התאמה']
        
        # הוסף עמודת שעות אם קיימת
        time_cols = [c for c in all_candidates.columns if 'שע' in c or 'זמן' in c or 'hour' in c.lower() or 'time' in c.lower()]
        if time_cols:
            columns_to_show.insert(2, time_cols[0])
        
        # הוסף עמודת אט"ן אם רלוונטי
        if is_atan_shift and 'מורשה אטן' in all_candidates.columns:
            columns_to_show.insert(2, 'מורשה אטן')
        
        # סינון עמודות קיימות
        columns_to_show = [c for c in columns_to_show if c in all_candidates.columns]
        
        # הצג כותרת
        if is_atan_shift:
            st.info("ℹ️ משמרת אט\"ן - רק עובדים מורשים יכולים להישבץ")
        
        # טבלת עובדים
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
        
        st.caption("📊 עובדים ממוינים: קודם תחנה מתאימה, אחר כך לפי מאזן")
        
        st.markdown("---")
        
        # בחירת עובד עם radio buttons
        # סינון לפי אט"ן אם נדרש
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
                    key=f"radio_auth_{shift_key}",
                    label_visibility="collapsed"
                )
                
                if not unauthorized.empty:
                    with st.expander(f"⚠️ {len(unauthorized)} עובדים ללא הרשאת אט\"ן (לא מומלץ)"):
                        st.caption("עובדים אלו ביקשו את המשמרת אך אינם מורשים לאט\"ן")
                        for name in unauthorized['שם'].tolist():
                            st.write(f"• {name} (תחנה: {all_candidates[all_candidates['שם']==name]['תחנה מבוקשת'].values[0]})")
            else:
                st.warning("⚠️ אין עובדים מורשים לאט\"ן זמינים")
                st.markdown("### עובדים ללא הרשאה:")
                selected = st.radio(
                    "בחר עובד (ללא הרשאת אט\"ן):",
                    options=selectable_candidates['שם'].tolist(),
                    format_func=lambda x: f"👤 {x} • תחנה: {all_candidates[all_candidates['שם']==x]['תחנה מבוקשת'].values[0]} • מאזן: {balance.get(x, 0)}",
                    key=f"radio_{shift_key}",
                    label_visibility="collapsed"
                )
        else:
            # משמרת רגילה
            selected = st.radio(
                "בחר עובד לשיבוץ:",
                options=selectable_candidates['שם'].tolist(),
                format_func=lambda x: f"👤 {x} • תחנה: {all_candidates[all_candidates['שם']==x]['תחנה מבוקשת'].values[0]} • מאזן: {balance.get(x, 0)}",
                key=f"radio_{shift_key}",
                label_visibility="visible"
            )
        
        # כפתורי פעולה
        col1, col2 = st.columns([3, 1])
        with col1:
            if st.button("✅ שבץ עובד", type="primary", use_container_width=True):
                st.session_state.final_schedule[shift_key] = selected
                if date_str not in st.session_state.assigned_today:
                    st.session_state.assigned_today[date_str] = set()
                st.session_state.assigned_today[date_str].add(selected)
                
                # בדוק אם שובץ לתחנה אחרת
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
    
    # אינדיקטור חיבור Firebase
    if db:
        st.success("🟢 Database מחובר")
    else:
        st.warning("🟡 Database לא זמין")
    
    st.divider()
    
    st.markdown("### 📁 קבצים")
    req_file = st.file_uploader("בקשות עובדים", type=['csv'])
    shi_file = st.file_uploader("תבנית משמרות", type=['csv'])
    
    st.divider()
    
    # הגדרות שיבוץ
    st.markdown("### ⚙️ הגדרות שיבוץ")
    
    # בדיקת שעות
    strict_hours = st.checkbox(
        "בדיקת שעות מדויקת",
        value=st.session_state.get('strict_hours_matching', True),
        help="אם מסומן: עובד חייב לבקש את אותן שעות בדיוק. אם לא מסומן: התעלם משעות"
    )
    st.session_state.strict_hours_matching = strict_hours
    
    if strict_hours:
        st.caption("✅ רק עובדים ששעותיהם תואמות בדיוק ישובצו")
    else:
        st.caption("⚠️ התעלמות משעות - שיבוץ לפי תאריך/משמרת/תחנה בלבד")
    
    # מכסה שבועית
    weekly_limit = st.number_input(
        "מכסה שבועית (משמרות/שבוע)",
        min_value=1,
        max_value=7,
        value=st.session_state.get('weekly_shift_limit', 5),
        help="מספר מקסימלי של משמרות שעובד יכול לעבוד בשבוע אחד"
    )
    st.session_state.weekly_shift_limit = weekly_limit
    
    st.caption(f"📊 עובד יכול לעבוד עד {weekly_limit} משמרות בשבוע")
    
    st.divider()
    
    if req_file and shi_file:
        if st.button("🪄 שיבוץ אוטומטי", type="primary", use_container_width=True):
            st.session_state.trigger_auto = True
            st.rerun()
    
    if st.session_state.final_schedule:
        if st.button("💾 שמירה ל-Database", type="primary", use_container_width=True):
            if not db:
                st.error("❌ Database לא זמין - ודא שהגדרת Firebase secrets")
            else:
                try:
                    with st.spinner('שומר ל-Database...'):
                        batch = db.batch()
                        saved_count = 0
                        
                        # ארגון נתונים לפי עובד
                        employees_data = {}
                        
                        for shift_key, employee in st.session_state.final_schedule.items():
                            parts = shift_key.split('_', 3)
                            date_str = parts[0]
                            station = parts[1]
                            shift_type = parts[2]
                            
                            # אתחול עובד אם לא קיים
                            if employee not in employees_data:
                                employees_data[employee] = {
                                    'shifts': [],
                                    'total_shifts': 0
                                }
                            
                            # הוסף משמרת לעובד
                            employees_data[employee]['shifts'].append({
                                'date': date_str,
                                'station': station,
                                'shift_type': shift_type,
                                'shift_key': shift_key
                            })
                            employees_data[employee]['total_shifts'] += 1
                            
                            # שמור גם את המשמרת עצמה
                            doc_ref = db.collection('shifts').document(shift_key)
                            batch.set(doc_ref, {
                                'date': date_str,
                                'station': station,
                                'shift_type': shift_type,
                                'employee': employee,
                                'timestamp': firestore.SERVER_TIMESTAMP,
                                'status': 'assigned'
                            })
                            saved_count += 1
                        
                        # שמירת משמרות מבוטלות
                        for shift_key in st.session_state.cancelled_shifts:
                            parts = shift_key.split('_', 3)
                            date_str = parts[0]
                            station = parts[1]
                            shift_type = parts[2]
                            
                            doc_ref = db.collection('shifts').document(shift_key)
                            batch.set(doc_ref, {
                                'date': date_str,
                                'station': station,
                                'shift_type': shift_type,
                                'employee': None,
                                'timestamp': firestore.SERVER_TIMESTAMP,
                                'status': 'cancelled'
                            })
                            saved_count += 1
                        
                        # שמירת נתוני עובדים - עם כל התאריכים
                        for employee, data in employees_data.items():
                            doc_ref = db.collection('employee_history').document(employee)
                            
                            # קרא נתונים קיימים אם יש
                            existing_doc = doc_ref.get()
                            if existing_doc.exists:
                                existing_data = existing_doc.to_dict()
                                previous_total = existing_data.get('total_shifts', 0)
                            else:
                                previous_total = 0
                            
                            # עדכן עם המשמרות החדשות
                            batch.set(doc_ref, {
                                'name': employee,
                                'shifts': data['shifts'],  # רשימת כל המשמרות
                                'current_period_total': data['total_shifts'],  # סה"כ בתקופה הנוכחית
                                'total_shifts': previous_total + data['total_shifts'],  # סה"כ כולל
                                'last_updated': firestore.SERVER_TIMESTAMP,
                                'last_shift_date': max([s['date'] for s in data['shifts']]) if data['shifts'] else None
                            }, merge=False)  # False = החלף את הכל (לא merge)
                        
                        # ביצוע Batch
                        batch.commit()
                        
                        st.success(f"✅ נשמרו {saved_count} משמרות + {len(employees_data)} עובדים ל-Database!")
                        
                        # הצג סיכום
                        with st.expander("📊 פירוט שמירה"):
                            for employee, data in employees_data.items():
                                st.write(f"**{employee}**: {data['total_shifts']} משמרות")
                                dates = [s['date'] for s in data['shifts']]
                                st.caption(f"תאריכים: {', '.join(sorted(set(dates)))}")
                        
                        logger.info(f"Saved {saved_count} shifts and {len(employees_data)} employees to Firebase")
                        
                except Exception as e:
                    st.error(f"❌ שגיאה בשמירה: {str(e)}")
                    logger.error(f"Save error: {e}", exc_info=True)
        
        
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
        req_df = pd.read_csv(req_file, encoding='utf-8-sig')
        shi_df = pd.read_csv(shi_file, encoding='utf-8-sig')
        
        errors = validate_dataframes(req_df, shi_df)
        if errors:
            for e in errors: st.error(e)
            st.stop()
        
        dates = sorted(req_df['תאריך מבוקש'].unique(), key=parse_date_safe)
        balance = get_balance()
        
        # כפתור ייצוא - תמיד זמין אם יש שיבוצים
        if st.session_state.final_schedule:
            export_data = []
            
            # עבור על כל המשמרות המשובצות
            for shift_key, employee in st.session_state.final_schedule.items():
                # פרק את ה-key
                parts = shift_key.split('_')
                date_str = parts[0]
                station = parts[1]
                shift_type = parts[2]
                shift_idx = int(parts[3]) if len(parts) > 3 else 0
                
                # מצא את השורה המקורית בתבנית
                shift_row = None
                if shift_idx < len(shi_df):
                    row = shi_df.iloc[shift_idx]
                    # וודא שזו השורה הנכונה
                    if row['תחנה'] == station and row['משמרת'] == shift_type:
                        shift_row = row
                
                # אם לא נמצא, חפש ידנית
                if shift_row is None:
                    matching = shi_df[(shi_df['תחנה'] == station) & (shi_df['משמרת'] == shift_type)]
                    if not matching.empty:
                        shift_row = matching.iloc[0]
                
                # חפש שעות בקובץ בקשות
                hours = ""
                emp_request = req_df[
                    (req_df['שם'] == employee) &
                    (req_df['תאריך מבוקש'] == date_str) &
                    (req_df['משמרת'] == shift_type)
                ]
                
                if not emp_request.empty:
                    time_cols = [c for c in emp_request.columns if 'שע' in c or 'זמן' in c or 'hour' in c.lower() or 'time' in c.lower()]
                    if time_cols:
                        hours_val = emp_request.iloc[0][time_cols[0]]
                        if pd.notna(hours_val):
                            hours = str(hours_val)
                
                # חפש תחנה מבוקשת
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
            
            # הוסף משמרות מבוטלות
            cancelled_data = []
            for shift_key in st.session_state.cancelled_shifts:
                parts = shift_key.split('_')
                date_str = parts[0]
                station = parts[1]
                shift_type = parts[2]
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
            
            # איחוד הנתונים
            all_export_data = export_data + cancelled_data
            
            # המר לטבלה
            if all_export_data:
                export_df = pd.DataFrame(all_export_data)
                
                # מיון לפי תאריך ואז תחנה
                export_df['תאריך_sort'] = export_df['תאריך'].apply(parse_date_safe)
                export_df = export_df.sort_values(['תאריך_sort', 'תחנה משובצת', 'משמרת'])
                export_df = export_df.drop('תאריך_sort', axis=1)
                
                csv = export_df.to_csv(index=False, encoding='utf-8-sig')
                
                # כפתור הורדה
                col_export, col_preview = st.columns([1, 3])
                with col_export:
                    st.download_button(
                        label="📥 ייצא CSV מלא",
                        data=csv,
                        file_name=f"shibutz_full_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
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
            
            # חישוב סטטיסטיקות ושמירה ל-session state
            total_shifts = len(shi_df) * len(dates)
            assigned_count = len(st.session_state.final_schedule)
            cancelled_count = len(st.session_state.cancelled_shifts)
            missing_count = total_shifts - assigned_count - cancelled_count
            
            st.session_state.last_auto_assign = {
                'total': total_shifts,
                'assigned': assigned_count,
                'missing': missing_count
            }
            
            st.success(f"✅ שיבוץ אוטומטי הושלם: {assigned_count} משמרות שובצו מתוך {total_shifts}")
            if missing_count > 0:
                st.warning(f"⚠️ {missing_count} משמרות ללא שיבוץ - ראה דוח בתחתית הדף")
            else:
                st.balloons()
                st.success("🎉 כל המשמרות שובצו בהצלחה!")
            
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
        
        # לוח שיבוץ - כותרות
        header_cols = st.columns(7)
        for i, d in enumerate(dates[:7]):
            with header_cols[i]:
                st.markdown(f'''
                <div class="day-header">
                    <span class="day-name">{get_day_name(d)}</span>
                    <span class="day-date">{d}</span>
                </div>
                ''', unsafe_allow_html=True)
        
        # משמרות
        for idx in range(len(shi_df)):
            shift_cols = st.columns(7)
            s = shi_df.iloc[idx]
            
            for i, d in enumerate(dates[:7]):
                with shift_cols[i]:
                    key = f"{d}_{s['תחנה']}_{s['משמרת']}_{idx}"
                    assigned = st.session_state.final_schedule.get(key)
                    cancelled = key in st.session_state.cancelled_shifts
                    is_atan = "אט" in str(s['סוג תקן'])
                    atan_class = 'atan' if is_atan else ''
                    
                    # בניית HTML
                    if cancelled:
                        status_html = '<div class="shift-status status-cancelled"><span>🚫</span><span>מבוטל</span></div>'
                    elif assigned:
                        status_html = f'<div class="shift-status status-assigned"><span>👤</span><span>{assigned}</span></div>'
                    else:
                        status_html = '<div class="shift-status status-empty"><span>⚠️</span><span>חסר שיבוץ</span></div>'
                    
                    st.markdown(f'''
                    <div class="shift-mini {atan_class}">
                        <div class="shift-top">
                            <div class="shift-title">{s['משמרת']}</div>
                            <div class="shift-badge">{s['סוג תקן']}</div>
                        </div>
                        <div class="shift-station">{s['תחנה']}</div>
                        {status_html}
                    </div>
                    ''', unsafe_allow_html=True)
                    
                    # כפתורי פעולה
                    if cancelled:
                        if st.button("🔄 שחזר", key=f"restore_{key}", use_container_width=True):
                            st.session_state.cancelled_shifts.remove(key)
                            st.rerun()
                    elif assigned:
                        if st.button("🗑️ הסר", key=f"remove_{key}", use_container_width=True):
                            del st.session_state.final_schedule[key]
                            if d in st.session_state.assigned_today:
                                st.session_state.assigned_today[d].discard(assigned)
                            st.rerun()
                    else:
                        ca, cb = st.columns([3, 1])
                        with ca:
                            if st.button("➕ שבץ", key=f"add_{key}", use_container_width=True):
                                show_assignment_dialog(key, d, s['תחנה'], s['משמרת'], req_df, balance, shi_df)
                        with cb:
                            if st.button("🚫", key=f"cancel_{key}"):
                                st.session_state.cancelled_shifts.add(key)
                                st.rerun()
        
        # דוח חוסרים - בתחתית הדף
        st.markdown("---")
        st.markdown("---")
        
        # חישוב חוסרים
        total_shifts = len(shi_df) * len(dates)
        assigned_count = len(st.session_state.final_schedule)
        cancelled_count = len(st.session_state.cancelled_shifts)
        missing_count = total_shifts - assigned_count - cancelled_count
        
        if missing_count > 0:
            st.markdown("## 📋 דוח חוסרים")
            st.warning(f"⚠️ {missing_count} משמרות ללא שיבוץ מתוך {total_shifts} סה\"כ")
            
            with st.expander(f"👁️ הצג דוח מפורט - {missing_count} משמרות", expanded=False):
                # בניית רשימת חוסרים
                missing_shifts = []
                
                for date_str in dates:
                    for idx, shift_row in shi_df.iterrows():
                        shift_key = f"{date_str}_{shift_row['תחנה']}_{shift_row['משמרת']}_{idx}"
                        
                        # בדוק אם המשמרת לא שובצה ולא מבוטלת
                        if shift_key not in st.session_state.final_schedule and shift_key not in st.session_state.cancelled_shifts:
                            # בדוק למה לא שובצה
                            potential = req_df[
                                (req_df['תאריך מבוקש'] == date_str) &
                                (req_df['משמרת'] == shift_row['משמרת']) &
                                (req_df['תחנה'] == shift_row['תחנה'])
                            ].copy()
                            
                            # סיבה
                            if potential.empty:
                                reason = "אין בקשות"
                            else:
                                already_working = st.session_state.assigned_today.get(date_str, set())
                                available = potential[~potential['שם'].isin(already_working)]
                                
                                if available.empty:
                                    reason = f"כל המבקשים משובצים ({len(potential)})"
                                else:
                                    # בדוק התאמת שעות
                                    time_cols_shift = [c for c in shi_df.columns if 'שע' in c or 'זמן' in c or 'hour' in c.lower()]
                                    time_cols_req = [c for c in req_df.columns if 'שע' in c or 'זמן' in c or 'hour' in c.lower()]
                                    
                                    if time_cols_shift and time_cols_req:
                                        shift_hours = shift_row.get(time_cols_shift[0])
                                        if pd.notna(shift_hours):
                                            shift_hours_str = str(shift_hours).strip()
                                            # בדוק כמה מהזמינים התאימו בשעות
                                            matching_hours = 0
                                            for _, emp_row in available.iterrows():
                                                emp_hours = emp_row.get(time_cols_req[0])
                                                if pd.notna(emp_hours) and str(emp_hours).strip() == shift_hours_str:
                                                    matching_hours += 1
                                            
                                            if matching_hours == 0:
                                                reason = f"אין התאמה לשעות ({len(available)} פנויים)"
                                            else:
                                                # יש התאמה בשעות, בדוק סיבות אחרות
                                                # בדוק מכסה שבועית
                                                WEEKLY_LIMIT = st.session_state.get('weekly_shift_limit', 5)
                                                week_start = get_week_start(date_str)
                                                
                                                employees_under_limit = []
                                                for emp_name in available['שם'].unique():
                                                    # ספור כמה משמרות לעובד השבוע
                                                    week_count = 0
                                                    for assigned_date in st.session_state.assigned_today.keys():
                                                        if get_week_start(assigned_date) == week_start:
                                                            if emp_name in st.session_state.assigned_today[assigned_date]:
                                                                week_count += 1
                                                    
                                                    if week_count < WEEKLY_LIMIT:
                                                        employees_under_limit.append(emp_name)
                                                
                                                if not employees_under_limit:
                                                    reason = f"כולם עברו מכסה שבועית ({len(available)} פנויים)"
                                                else:
                                                    # יש זמינים עם התאמת שעות ומתחת למכסה
                                                    # בדוק אט"ן
                                                    if "אט" in str(shift_row['סוג תקן']):
                                                        atan_col = get_atan_column(req_df)
                                                        if atan_col:
                                                            atan_available = available[
                                                                (available[atan_col] == 'כן') &
                                                                (available['שם'].isin(employees_under_limit))
                                                            ]
                                                            if atan_available.empty:
                                                                reason = f"אין מורשי אט\"ן ({len(employees_under_limit)} פנויים)"
                                                            else:
                                                                reason = "לא ידוע"
                                                        else:
                                                            reason = "אין עמודת אט\"ן"
                                                    else:
                                                        reason = "לא ידוע"
                                        else:
                                            # אין שעות במשמרת, המשך לבדיקות רגילות
                                            if "אט" in str(shift_row['סוג תקן']):
                                                atan_col = get_atan_column(req_df)
                                                if atan_col:
                                                    atan_available = available[available[atan_col] == 'כן']
                                                    if atan_available.empty:
                                                        reason = f"אין מורשי אט\"ן ({len(available)} פנויים)"
                                                    else:
                                                        reason = "לא ידוע"
                                                else:
                                                    reason = "אין עמודת אט\"ן"
                                            else:
                                                reason = "לא ידוע"
                                    else:
                                        # אין עמודת שעות, המשך לבדיקות רגילות
                                        if "אט" in str(shift_row['סוג תקן']):
                                            atan_col = get_atan_column(req_df)
                                            if atan_col:
                                                atan_available = available[available[atan_col] == 'כן']
                                                if atan_available.empty:
                                                    reason = f"אין מורשי אט\"ן ({len(available)} פנויים)"
                                                else:
                                                    reason = "לא ידוע"
                                            else:
                                                reason = "אין עמודת אט\"ן"
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
                    # המר לטבלה
                    missing_df = pd.DataFrame(missing_shifts)
                    
                    # הצג טבלה
                    st.dataframe(
                        missing_df,
                        use_container_width=True,
                        hide_index=True,
                        height=min(len(missing_df) * 35 + 38, 400)
                    )
                    
                    # סטטיסטיקה לפי סיבה
                    st.markdown("#### 📊 פירוט לפי סיבה:")
                    reason_counts = missing_df['סיבה'].value_counts()
                    
                    cols = st.columns(min(len(reason_counts), 4))
                    for i, (reason, count) in enumerate(reason_counts.items()):
                        with cols[i % len(cols)]:
                            st.metric(reason, count)
                    
                    # כפתור ייצוא דוח חוסרים
                    st.markdown("---")
                    csv_missing = missing_df.to_csv(index=False, encoding='utf-8-sig')
                    st.download_button(
                        label="📥 ייצא דוח חוסרים ל-CSV",
                        data=csv_missing,
                        file_name=f"missing_shifts_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                        mime="text/csv",
                        use_container_width=True,
                        type="primary"
                    )
                    
                    st.info("💡 טיפ: ניתן לשבץ ידנית משמרות חסרות על ידי לחיצה על ➕ שבץ בלוח למעלה")
        else:
            if st.session_state.final_schedule:
                st.success("✅ כל המשמרות שובצו בהצלחה!")
    
    except Exception as e:
        st.error(f"❌ {str(e)}")
        logger.error(f"Error: {e}", exc_info=True)

else:
    st.info("👈 העלה קבצים להתחלה")
    
    with st.expander("📖 הוראות"):
        st.markdown("""
        ### 🚀 איך להשתמש?
        
        1. **העלה קבצים** - בקשות עובדים + תבנית משמרות (CSV)
        2. **שיבוץ אוטומטי** - לחץ על הכפתור לשיבוץ חכם
        3. **התאמות ידניות** - שבץ/הסר/בטל משמרות
        4. **שמור/ייצא** - שמור ל-Database או ייצא ל-CSV
        
        ### 📋 פורמט קבצים:
        
        **בקשות עובדים:**
        - שם
        - תאריך מבוקש
        - משמרת
        - תחנה
        
        **תבנית משמרות:**
        - תחנה
        - משמרת
        - סוג תקן
        """)
