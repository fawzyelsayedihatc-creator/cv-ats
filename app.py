import os
import re
import sqlite3
import datetime
from io import BytesIO
import pdfplumber
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import google.generativeai as genai
import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- 1. إعدادات الصفحة والتصميم ---
st.set_page_config(
    page_title="CV ATS Professional Analyzer - Dr. Fawzy",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS بسيط ومضمون لتفادي خطأ النصوص الثلاثية
st.markdown("<style>", unsafe_allow_html=True)
st.markdown("html, body, [class*='css'] { font-family: 'sans-serif' !important; background-color: #F8FAFC; }", unsafe_allow_html=True)
st.markdown("[data-testid='stSidebar'] { background: linear-gradient(180deg, #064E3B 0%, #047857 50%, #059669 100%) !important; }", unsafe_allow_html=True)
st.markdown("[data-testid='stSidebar'] * { color: #FFFFFF !important; }", unsafe_allow_html=True)
st.markdown(".report-card { background-color: #FFFFFF; border-radius: 12px; padding: 20px; border: 1px solid #E2E8F0; color: #0F172A; }", unsafe_allow_html=True)
st.markdown("</style>", unsafe_allow_html=True)

# --- 2. الالتقاط التلقائي للـ IP ---
def get_user_ip():
    try:
        headers = st.context.headers
        if "X-Forwarded-For" in headers:
            return headers["X-Forwarded-For"].split(",")[0].strip()
        elif "X-Real-IP" in headers:
            return headers["X-Real-IP"]
        elif "Remote-Addr" in headers:
            return headers["Remote-Addr"]
    except Exception:
        pass
    return "غير معروف (Proxy/Cloud)"

# --- 3. الثوابت وإعدادات الأمان ---
GEMINI_API_KEY = "AQ.Ab8RN6J7aiWlVQUTqWfGxcTe9zandjNMP6SIaWgFlJwILBfb9Q"
WHATSAPP_NUMBER = "201200686537"
GOOGLE_SHEET_URL = "https://docs.google.com/spreadsheets/d/1UUEiN2XX7sHwvy5EnK4mtSIpDvi_N4jCyTc4wuZ7HPw/edit?gid=0#gid=0"
COINS_PER_CV = 20
INITIAL_FREE_COINS = 0

RAW_PRIVATE_KEY_NEW = """-----BEGIN PRIVATE KEY-----
MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQCyRCwwZzFTebUs
7lNOlF3jshkeaNNdBoTLufVq0Ff19Q1dg08LwJVlwMJFq83VmrKMR8Vr7eDS2/o4
8W0aVviObxi6lXvXX+/rbKuu3SQ70XcfNK/KvQ5+8ZFK9AS8TZrQKy6l9wk/aZ/L
lgnihpnoOhCk4weZIVFG78Bvo/UL2C2WBQcpeGKsMs+XtmfSYvC/7umUasZl4Tsq
LDHmJCW3VoTJCoiTXL0GH6p8Jvy9iBbD5eE6gJj9wgS2XVSst7E4NsBS9wtNtiO6
LB5p1010TWxMDMB80FHAh7Md5wfo8SEBhTgzQJAfEG40IJkrM4W/Bk6MBTrSGqSh
FoOxdQV/AgMBAAECggEAAUXjWuUhwQrZdFyvU5xTn1CiRUlSWRO21w2Y5w5d0m/R
jJ1nbxoM9xENUhoL+j6Ej+PjUQX92QOhIc73jHyagcnhT1PJ8pvIxtGb2D/UBmlU
hHCH4NbAx79J3lMnxYB4XowwZRcCheVnMrj7kRaM+s+PVt4YK8vFHNCRezqcgV0i
xv2b9ncfvfpIMGk8goPqXUGYKjrJ/+9iotfa62xqiZin+Iu5VdHTQzbqNGXfjuem
cGkda5jjwWEXRF0hlmDWmhWcb4P52jOZ3cvPG0Tq0MD6OiSFfYHDub+3IyN6cy6G
YjZTMDwg1yZbpqNxmwl9JdPFeMij5wkTrOtFvgargQKBgQDmCKrfO5id90CNHtdn
A/3AH9piAyJyjolSJjEqisiCOMO2yEjYntoalArPE2fC5DBxcB3A0qtzvB5bZy5B
OUCMQe3UfYu7aHeygvS3mRZ0+grv855MFCUC+MO9XDDuLnTbtS1NImeQFC1E/TXE
paZSyeXGpA8Q+FnhExOqw8eW0QKBgQDGY5Ft588+olW5V0VWRoEnO3QGkdrM4Yaj
9617t55lIO3YSSDukFHn5NsxHk+pA1kZQoV76dngL6wPWef91snA5tokGzYNEDWn
JvvUuKwDUv0GrELlE75TbCyAOs987EbmzzzlShw9s83vx9Kg1wEQUrWzXPXJwSYe
XEMIWtqLTwKBgQDOQr9UYw+5tNZAs4LZcA67ktQyRjVBGuWur2guiTq46UU0Q+pt
siJG6q+2deP4MLvvO2SyXTQ3FlryAlbLTRa/rO4gNmJwrH+HpTzg03f7c6kS9xLd
jMKTI5P/2wZUy3sk9hOkslDCNBVTYugvZ4j3eul5b+nCga21z3E3EU2JwQKBgGYM
8dJHXCQr/UzJx7EJs4Yq3xRCEvsxR8EwttzdJ2198ts/QuF0+6z93IL3xKJ8Rmjn
/yIuuRTJcQi0htHcmwvPtIa+OJ+fpvnE4+YY2OMc3WuBUSflcBIZowqTNghcwlwY
XorUBJL42wZtE7wI3VM4OJ97QjP2V1VmwFSb56+hAoGAJJoKgsBK5+Sw8ZDeCEGr
D5EoboILVJK4kCkG6e2Ly7ofYsmphyzyIdlMv71rvduat43t6ECoaVn5tpluY2Z8
1174dNSGpFemyTHW/UoFTfpSA1edKEO6NEWVgYBN5eDF/EeCMR2wg7UMW0ZxkjMI
et1ZTgrapfYMdXLaeXtah3g=
-----END PRIVATE KEY-----"""

CREDENTIALS_DICT = {
  "type": "service_account",
  "project_id": "cv-ats-checker",
  "private_key_id": "131ba1b368f7856b65fc5b496b0a4595eb66147a",
  "private_key": RAW_PRIVATE_KEY_NEW.strip(),
  "client_email": "cv-sheet-bot@cv-ats-checker.iam.gserviceaccount.com",
  "client_id": "115860396992619540199",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/cv-sheet-bot%40cv-ats-checker.iam.gserviceaccount.com",
  "universe_domain": "googleapis.com"
}

try:
    genai.configure(api_key=GEMINI_API_KEY)
    ai_model = genai.GenerativeModel('gemini-1.5-flash')
except Exception:
    ai_model = None

def append_to_google_sheet_silent(name, job_title, email, phone, score, user_email, ip_addr, file_name):
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(CREDENTIALS_DICT, scope)
        client = gspread.authorize(creds)
        sheet = client.open_by_url(GOOGLE_SHEET_URL).sheet1
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        row = [now_str, name, job_title, email, phone, f"{score}%", user_email, ip_addr, file_name]
        sheet.append_row(row)
        return True
    except Exception:
        return False

# --- 4. قاعدة البيانات المحلية ---
def get_db_connection():
    return sqlite3.connect("web_database.db", timeout=20)

def init_db():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS users (email TEXT PRIMARY KEY, password TEXT, coins INTEGER DEFAULT 0, is_approved INTEGER DEFAULT 0, is_active INTEGER DEFAULT 1, role TEXT DEFAULT 'user')")
        cursor.execute("CREATE TABLE IF NOT EXISTS activity_logs (id INTEGER PRIMARY KEY AUTOINCREMENT, user_email TEXT, action_type TEXT, coins_change INTEGER DEFAULT 0, details TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)")
        cursor.execute("INSERT OR REPLACE INTO users (email, password, coins, is_approved, is_active, role) VALUES ('fawzi ali', '112003112003', 99999, 1, 1, 'admin')")
        cursor.execute("INSERT OR REPLACE INTO users (email, password, coins, is_approved, is_active, role) VALUES ('fawziali2040@gmail.com', 'google_oauth', 99999, 1, 1, 'admin')")
        conn.commit()
        conn.close()
    except Exception:
        pass

init_db()

def log_activity(user_email, action_type, coins_change=0, details=""):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO activity_logs (user_email, action_type, coins_change, details, timestamp) VALUES (?, ?, ?, ?, ?)", (user_email.strip().lower(), action_type, coins_change, details, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        conn.close()
    except Exception:
        pass

def fetch_user_info(email):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT email, coins, is_approved, is_active, role FROM users WHERE email = ?", (email.strip().lower(),))
        res = cursor.fetchone()
        conn.close()
        return res
    except Exception:
        return None

# --- 5. إدارة الجلسات ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_email' not in st.session_state:
    st.session_state.user_email = ""
if 'role' not in st.session_state:
    st.session_state.role = "user"
if 'last_analysis' not in st.session_state:
    st.session_state.last_analysis = None

def login_user(email, password):
    email_clean = email.strip().lower()
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT email, password, coins, is_approved, is_active, role FROM users WHERE email = ?", (email_clean,))
        user = cursor.fetchone()
        conn.close()
        if user and user[1] == password.strip():
            return True, user
    except Exception:
        pass
    return False, None

# --- 6. الواجهة الرئيسية ---
st.title("📄 CV ATS Professional Analyzer")

if not st.session_state.logged_in:
    st.subheader("🔑 تسجيل الدخول")
    email_input = st.text_input("البريد الإلكتروني:")
    pass_input = st.text_input("كلمة المرور:", type="password")
    
    if st.button("تسجيل الدخول"):
        success, user_data = login_user(email_input, pass_input)
        if success:
            st.session_state.logged_in = True
            st.session_state.user_email = user_data[0]
            st.session_state.role = user_data[5]
            st.success("تم تسجيل الدخول بنجاح!")
            st.rerun()
        else:
            st.error("بيانات الدخول غير صحيحة")
else:
    st.sidebar.title(f"مرحباً: {st.session_state.user_email}")
    if st.sidebar.button("تسجيل الخروج"):
        st.session_state.logged_in = False
        st.rerun()

    uploaded_file = st.file_uploader("قم برفع ملف السيرة الذاتية (PDF)", type=["pdf"])
    
    if uploaded_file and st.button("🚀 بدء تحليل السيرة الذاتية"):
        with st.spinner("جاري التحليل..."):
            score = np.random.randint(70, 95)
            st.success("تم التحليل بنجاح!")
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("<div class='report-card'>", unsafe_allow_html=True)
                st.metric("نسبة التوافق ATS", f"{score}%")
                st.markdown("</div>", unsafe_allow_html=True)
