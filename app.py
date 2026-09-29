import os
import re
import json
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
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import urllib.request
import arabic_reshaper
from bidi.algorithm import get_display

# --- دالة لمعالجة النصوص العربية لتظهر سليمة وليست مقلوبة ---
def fix_arabic(text):
    if not text:
        return ""
    try:
        if any('\u0600' <= c <= '\u06ff' for c in str(text)):
            reshaped_text = arabic_reshaper.reshape(str(text))
            return get_display(reshaped_text)
        return str(text)
    except Exception:
        return text

# --- 1. إعدادات الصفحة والتصميم ---
st.set_page_config(
    page_title="CV ATS Professional Analyzer - Dr. Fawzy",
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
        font-size: 18px !important;
        font-weight: 800 !important;
        border-radius: 12px !important;
        padding: 10px 20px !important;
        border: none !important;
        box-shadow: 0 4px 14px rgba(5, 150, 105, 0.3) !important;
        width: 100% !important;
    }
    
    .report-card {
        background-color: #FFFFFF;
        border-radius: 12px;
        padding: 20px;
        border: 1px solid #E2E8F0;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
        font-size: 18px !important;
        font-weight: 700 !important;
        line-height: 1.8 !important;
        color: #0F172A !important;
    }
</style>
""", unsafe_allow_html=True)

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
8dJHXCQr/UzJx7EJs4Yq3xRCEvsxR8EwttzdJ2198ts/QuF0+6z93IL3xKJ8Rmjn/yIuuRTJcQi0htHcmwvPtIa+OJ+fpvnE4+YY2OMc3WuBUSflcBIZowqTNghcwlwY
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
        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive"
        ]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(CREDENTIALS_DICT, scope)
        client = gspread.authorize(creds)
        sheet = client.open_by_url(GOOGLE_SHEET_URL).sheet1
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        row = [now_str, name, job_title, email, phone, f"{score}%", user_email, ip_addr, file_name]
        sheet.append_row(row)
        return True
    except Exception as e:
        return False

# --- 4. قاعدة البيانات المحلية وسجلات النشاط لكل أكونت ---
def get_db_connection():
    return sqlite3.connect("web_database.db", timeout=20)

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            email TEXT PRIMARY KEY,
            password TEXT,
            coins INTEGER DEFAULT 0,
            is_approved INTEGER DEFAULT 0,
            role TEXT DEFAULT 'user'
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_activity_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT,
            action_type TEXT,
            coins_change INTEGER,
            details TEXT,
            timestamp TEXT
        )
    """)
    cursor.execute("INSERT OR REPLACE INTO users (email, password, coins, is_approved, role) VALUES ('fawzi ali', '112003112003', 99999, 1, 'admin')")
    cursor.execute("INSERT OR REPLACE INTO users (email, password, coins, is_approved, role) VALUES ('fawziali2040@gmail.com', 'google_oauth', 99999, 1, 'admin')")
    conn.commit()
    conn.close()

init_db()

def log_user_activity(email, action_type, coins_change, details):
    conn = get_db_connection()
    cursor = conn.cursor()
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("INSERT INTO user_activity_logs (email, action_type, coins_change, details, timestamp) VALUES (?, ?, ?, ?, ?)",
                   (email.strip().lower(), action_type, coins_change, details, now_str))
    conn.commit()
    conn.close()

def fetch_user_coins(email):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT coins FROM users WHERE email = ?", (email.strip().lower(),))
    res = cursor.fetchone()
    conn.close()
    return res[0] if res else 0

def get_user_logs(email):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT action_type, coins_change, details, timestamp FROM user_activity_logs WHERE email = ? ORDER BY timestamp DESC", (email.strip().lower(),))
    logs = cursor.fetchall()
    conn.close()
    return logs

# --- 5. حماية الجلسات وتثبيتها ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_email' not in st.session_state:
    st.session_state.user_email = ""
if 'role' not in st.session_state:
    st.session_state.role = "user"
if 'last_analysis' not in st.session_state:
    st.session_state.last_analysis = None
if 'bulk_results' not in st.session_state:
    st.session_state.bulk_results = None
if 'current_coins' not in st.session_state:
    st.session_state.current_coins = 0
if 'current_page' not in st.session_state:
    st.session_state.current_page = "main"
if 'selected_admin_account' not in st.session_state:
    st.session_state.selected_admin_account = None

query_params = st.query_params
if not st.session_state.logged_in and "user" in query_params:
    saved_user = query_params["user"]
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT email, is_approved, role, coins FROM users WHERE email = ?", (saved_user,))
    user = cursor.fetchone()
    conn.close()
    if user and (user[1] == 1 or user[2] == 'admin'):
        st.session_state.logged_in = True
        st.session_state.user_email = user[0]
        st.session_state.role = user[2]
        st.session_state.current_coins = user[3]

# --- 6. وظائف استخراج البيانات بالذكاء الاصطناعي ---
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

def register_user(email, password, is_google=False):
    email_clean = email.strip().lower()
    if not email_clean:
        return False, "يرجى كتابة البريد بشكل صحيح."
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (email, password, coins, is_approved, role) VALUES (?, ?, ?, 0, 'user')",
                       (email_clean, 'google_oauth' if is_google else password.strip(), INITIAL_FREE_COINS))
        conn.commit()
        conn.close()
        log_user_activity(email_clean, "تسجيل حساب", 0, "تم إنشاء الحساب وبانتظار الموافقة")
        return True, "تم تقديم طلب التسجيل بنجاح! يتطلب الحساب موافقة د. فوزي قبل التفعيل."
    except sqlite3.IntegrityError:
        conn.close()
        return False, "هذا البريد مسجل لدينا بالفعل!"

def update_user_coins(email, new_coins, admin_email, reason):
    email_clean = email.strip().lower()
    old_coins = fetch_user_coins(email_clean)
    diff = new_coins - old_coins
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET coins = ? WHERE email = ?", (new_coins, email_clean))
    conn.commit()
    conn.close()
    
    if diff != 0:
        log_user_activity(email_clean, "شحن / تعديل رصيد", diff, f"بواسطة الأدمن {admin_email} - السبب: {reason}")
    
    if email_clean == st.session_state.user_email.lower():
        st.session_state.current_coins = new_coins

def approve_user_db(email):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET is_approved = 1 WHERE email = ?", (email.strip().lower(),))
    conn.commit()
    conn.close()
    log_user_activity(email, "تفعيل الحساب", 0, "تم الموافقة على تفعيل الحساب من قبل الأدمن")

def get_all_users():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT email, coins, is_approved, role FROM users WHERE role != 'admin'")
    users = cursor.fetchall()
    conn.close()
    return users

def convert_pdf_to_images(uploaded_file):
    images_bytes = []
    try:
        uploaded_file.seek(0)
        with pdfplumber.open(uploaded_file) as pdf:
            for page in pdf.pages[:3]:
                pil_image = page.to_image(resolution=150).original
                buf = BytesIO()
                pil_image.save(buf, format="PNG")
                images_bytes.append(buf.getvalue())
    except Exception:
        pass
    return images_bytes

def extract_cv_info_with_ai(cv_text):
    prompt = f"""
    قم بقراءة نص السيرة الذاتية التالي بعناية واستخراج البيانات التالية بدقة:
    1. الاسم الكامل لصاحب السيرة الذاتية (إذا كان باللغة العربية اكتبه مرتباً وصحيحاً من اليمين لليسار، وإذا كان بالإنجليزية اكتبه كما هو).
    2. التخصص الرئيسي أو المسمى الوظيفي المستنتج بناءً على خبراته ودراسته في السيرة الذاتية (في كلمة إلى ثلاث كلمات كحد أقصى).
    
    أعطني النتيجة بصيغة JSON صارمة تحتوي فقط على الحقلين التاليين بدون أي مقدمات أو نص إضافي:
    {{"name": "...", "job_title": "..."}}
    
    نص السيرة الذاتية:
    {cv_text[:3000]}
    """
    try:
        if ai_model:
            response = ai_model.generate_content(prompt)
            clean_res = response.text.strip().replace("```json", "").replace("
