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
    
    for date_str in dates:
        for idx, shift_row in shi_df.iterrows():
            shift_key = f"{date_str}_{shift_row['תחנה']}_{shift_row['משמרת']}_{idx}"
            if shift_key in st.session_state.cancelled_shifts:
                continue
            
            potential = req_df[
                (req_df['תאריך מבוקש'] == date_str) &
                (req_df['משמרת'] == shift_row['משמרת']) &
                (req_df['תחנה'] == shift_row['תחנה']) &
                (~req_df['שם'].isin(temp_assigned[date_str]))
            ].copy()
            
            if "אט" in str(shift_row['סוג תקן']) and atan_col:
                potential = potential[potential[atan_col] == 'כן']
            
            if not potential.empty:
                potential['score'] = potential['שם'].map(lambda x: running_balance.get(x, 0))
                best = potential.sort_values('score').iloc[0]['שם']
                temp_schedule[shift_key] = best
                temp_assigned[date_str].add(best)
                running_balance[best] = running_balance.get(best, 0) + 1
    
    return temp_schedule, temp_assigned

@st.dialog("שיבוץ עובד למשמרת")
def show_assignment_dialog(shift_key, date_str, station, shift_type, req_df, balance, shi_df):
    st.markdown(f"### {get_day_name(date_str)} - {date_str}")
    st.write(f"**{station}** | **{shift_type}**")
    
    if not isinstance(st.session_state.assigned_today, dict):
        st.session_state.assigned_today = {}
    
    already_working = st.session_state.assigned_today.get(date_str, set())
    candidates = req_df[
        (req_df['תאריך מבוקש'] == date_str) &
        (req_df['משמרת'] == shift_type) &
        (req_df['תחנה'] == station) &
        (~req_df['שם'].isin(already_working))
    ].copy()
    
    # בדיקת אטן
    shift_row = None
    for idx, s in shi_df.iterrows():
        test_key = f"{date_str}_{s['תחנה']}_{s['משמרת']}_{idx}"
        if test_key == shift_key:
            shift_row = s
            break
    
    if shift_row is not None and "אט" in str(shift_row['סוג תקן']):
        atan_col = get_atan_column(req_df)
        if atan_col:
            candidates = candidates[candidates[atan_col] == 'כן']
    
    if candidates.empty:
        st.warning("😕 אין מועמדים פנויים")
        if st.button("סגור", type="secondary", use_container_width=True):
            st.rerun()
    else:
        candidates['balance'] = candidates['שם'].map(lambda x: balance.get(x, 0))
        candidates = candidates.sort_values('balance')
        
        selected = st.radio(
            "בחר עובד:",
            options=candidates['שם'].tolist(),
            format_func=lambda x: f"👤 {x} (מאזן: {balance.get(x, 0)})",
            key=f"radio_{shift_key}"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ אישור", type="primary", use_container_width=True):
                st.session_state.final_schedule[shift_key] = selected
                if date_str not in st.session_state.assigned_today:
                    st.session_state.assigned_today[date_str] = set()
                st.session_state.assigned_today[date_str].add(selected)
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
                        # שמירת השיבוצים
                        batch = db.batch()
                        saved_count = 0
                        
                        for shift_key, employee in st.session_state.final_schedule.items():
                            parts = shift_key.split('_', 3)
                            date_str = parts[0]
                            station = parts[1]
                            shift_type = parts[2]
                            
                            # יצירת document
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
                        
                        # עדכון מאזן עובדים
                        for employee, count in get_employee_counts().items():
                            doc_ref = db.collection('employee_history').document(employee)
                            batch.set(doc_ref, {
                                'total_shifts': count,
                                'last_updated': firestore.SERVER_TIMESTAMP
                            }, merge=True)
                        
                        # ביצוע Batch
                        batch.commit()
                        
                        st.success(f"✅ נשמרו {saved_count} משמרות ל-Database!")
                        logger.info(f"Saved {saved_count} shifts to Firebase")
                        
                except Exception as e:
                    st.error(f"❌ שגיאה בשמירה: {str(e)}")
                    logger.error(f"Save error: {e}", exc_info=True)
        
        if st.button("📥 ייצוא", use_container_width=True):
            export_data = []
            for shift_key, employee in st.session_state.final_schedule.items():
                parts = shift_key.split('_')
                export_data.append({'תאריך': parts[0], 'תחנה': parts[1], 'משמרת': parts[2], 'עובד': employee})
            csv = pd.DataFrame(export_data).to_csv(index=False, encoding='utf-8-sig')
            st.download_button("⬇️ הורד", csv, f"shibutz_{datetime.now().strftime('%Y%m%d')}.csv", 
                             mime="text/csv", use_container_width=True)
    
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
        
        # שיבוץ אוטומטי
        if st.session_state.get('trigger_auto'):
            with st.spinner('מבצע שיבוץ...'):
                temp_schedule, temp_assigned = auto_assign(dates, shi_df, req_df, balance)
                st.session_state.final_schedule, st.session_state.assigned_today = temp_schedule, temp_assigned
                st.session_state.trigger_auto = False
            st.success(f"✅ {len(st.session_state.final_schedule)} משמרות שובצו")
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
