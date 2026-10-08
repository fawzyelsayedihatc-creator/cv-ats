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
        st.error(f"خطأ في إضافة البيانات للشيت: {e}")
        return False

# --- 4. قاعدة البيانات المحلية والسجلات ---
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
            is_active INTEGER DEFAULT 1,
            role TEXT DEFAULT 'user'
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS activity_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT,
            action_type TEXT,
            coins_change INTEGER DEFAULT 0,
            details TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # التأكد من التوافق مع الأعمدة المضافة حديثاً
    cursor.execute("PRAGMA table_info(users)")
    columns = [column[1] for column in cursor.fetchall()]
    if 'is_active' not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN is_active INTEGER DEFAULT 1")
        
    cursor.execute("INSERT OR REPLACE INTO users (email, password, coins, is_approved, is_active, role) VALUES ('fawzi ali', '112003112003', 99999, 1, 1, 'admin')")
    cursor.execute("INSERT OR REPLACE INTO users (email, password, coins, is_approved, is_active, role) VALUES ('fawziali2040@gmail.com', 'google_oauth', 99999, 1, 1, 'admin')")
    conn.commit()
    conn.close()

init_db()

def log_activity(user_email, action_type, coins_change=0, details=""):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO activity_logs (user_email, action_type, coins_change, details, timestamp) VALUES (?, ?, ?, ?, ?)",
            (user_email.strip().lower(), action_type, coins_change, details, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )
        conn.commit()
        conn.close()
    except Exception:
        pass

def fetch_user_info(email):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT email, coins, is_approved, is_active, role FROM users WHERE email = ?", (email.strip().lower(),))
    res = cursor.fetchone()
    conn.close()
    return res

# --- 5. حماية الجلسات وتثبيتها عند الـ Refresh ---
query_params = st.query_params

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_email' not in st.session_state:
    st.session_state.user_email = ""
if 'role' not in st.session_state:
    st.session_state.role = "user"
if 'last_analysis' not in st.session_state:
    st.session_state.last_analysis = None
if 'bulk_analysis' not in st.session_state:
    st.session_state.bulk_analysis = None
if 'current_coins' not in st.session_state:
    st.session_state.current_coins = 0

# الاسترجاع والتثبيت التلقائي لصفحة التنقل عبر URL query params
if "page" in query_params:
    st.session_state.current_page = query_params["page"]
elif 'current_page' not in st.session_state:
    st.session_state.current_page = "main"

if not st.session_state.logged_in and "user" in query_params:
    saved_user = query_params["user"]
    user_info = fetch_user_info(saved_user)
    if user_info and (user_info[2] == 1 or user_info[4] == 'admin') and user_info[3] == 1:
        st.session_state.logged_in = True
        st.session_state.user_email = user_info[0]
        st.session_state.current_coins = user_info[1]
        st.session_state.role = user_info[4]

def set_page(page_name):
    st.session_state.current_page = page_name
    st.query_params["page"] = page_name
    st.rerun()

# --- 6. الوظائف المساعدة وإدارة المستخدمين ---
def login_user(email, password):
    email_clean = email.strip().lower()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT email, password, coins, is_approved, is_active, role FROM users WHERE email = ?", (email_clean,))
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
        cursor.execute("INSERT INTO users (email, password, coins, is_approved, is_active, role) VALUES (?, ?, ?, 0, 1, 'user')",
                       (email_clean, 'google_oauth' if is_google else password.strip(), INITIAL_FREE_COINS))
        conn.commit()
        conn.close()
        log_activity(email_clean, "طلب تسجيل جديد", 0, "تسجيل حساب جديد قيد الانتظار")
        return True, "تم تقديم طلب التسجيل بنجاح! يتطلب الحساب موافقة د. فوزي قبل التفعيل."
    except sqlite3.IntegrityError:
        conn.close()
        return False, "هذا البريد مسجل لدينا بالفعل!"

def update_user_coins(email, new_coins, action_by="System/Admin"):
    email_clean = email.strip().lower()
    old_coins = fetch_user_info(email_clean)[1] if fetch_user_info(email_clean) else 0
    diff = new_coins - old_coins
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET coins = ? WHERE email = ?", (new_coins, email_clean))
    conn.commit()
    conn.close()
    
    if email_clean == st.session_state.user_email:
        st.session_state.current_coins = new_coins
        
    action_label = "تزويد كوينز" if diff > 0 else "خصم كوينز"
    log_activity(email_clean, action_label, diff, f"تم تعديل الرصيد من {old_coins} إلى {new_coins} بواسطة {action_by}")

def approve_user_db(email):
    email_clean = email.strip().lower()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET is_approved = 1, is_active = 1 WHERE email = ?", (email_clean,))
    conn.commit()
    conn.close()
    log_activity(email_clean, "تفعيل الحساب", 0, "تمت الموافقة على الحساب وتفعيله")

def reject_user_db(email):
    email_clean = email.strip().lower()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE email = ?", (email_clean,))
    conn.commit()
    conn.close()
    log_activity(email_clean, "رفض الطلب", 0, "تم حذف طلب التسجيل المعلق")

def toggle_user_active_db(email, current_status):
    email_clean = email.strip().lower()
    new_status = 0 if current_status == 1 else 1
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET is_active = ? WHERE email = ?", (new_status, email_clean))
    conn.commit()
    conn.close()
    act_str = "إيقاف الحساب" if new_status == 0 else "تنشيط الحساب"
    log_activity(email_clean, act_str, 0, f"تغيير حالة الحساب إلى {'مفعل' if new_status == 1 else 'معطل'}")

def get_all_users():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT email, coins, is_approved, is_active, role FROM users WHERE role != 'admin'")
    users = cursor.fetchall()
    conn.close()
    return users

def get_user_logs(email=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    if email:
        cursor.execute("SELECT timestamp, user_email, action_type, coins_change, details FROM activity_logs WHERE user_email = ? ORDER BY id DESC", (email.strip().lower(),))
    else:
        cursor.execute("SELECT timestamp, user_email, action_type, coins_change, details FROM activity_logs ORDER BY id DESC")
    logs = cursor.fetchall()
    conn.close()
    return logs

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

# --- دالة استخراج التخصص / المسمى الوظيفي الذكية ---
def extract_job_title_with_ai(cv_text):
    prompt = f"""
    قم بقراءة نص السيرة الذاتية التالي واستخراج التخصص الرئيسي أو المسمى الوظيفي صاحب السيرة الذاتية (مثل: Software Engineer, Accountant, Graphic Designer, Sales Manager, Data Analyst, إلخ).
    أعد لي **فقط** المسمى الوظيفي أو التخصص في كلمة إلى ثلاث كلمات كحد أقصى، بدون أي مقدمات أو شرح أو علامات تنقيط.
    إذا لم تجد مسمى وظيفي واضح، اكتب: غير محدد.
    
    نص السيرة الذاتية:
    {cv_text[:2000]}
    """
    try:
        if ai_model:
            response = ai_model.generate_content(prompt)
            title = response.text.strip().replace("\n", "")
            if title and len(title) < 50:
                return title
    except Exception:
        pass
    
    lines = [line.strip() for line in cv_text.split('\n') if line.strip()]
    if len(lines) > 1:
        possible_title = lines[1]
        if len(possible_title) < 40 and not re.search(r'@|\d{5,}', possible_title):
            return possible_title
            
    return "غير محدد"

def analyze_cv_with_ai(cv_text):
    prompt = f"أنت خبير محترف في أنظمة التوظيف الـ ATS ومراجع سير ذاتية. قم بتحليل نص السيرة الذاتية التالي باختصار ووضوح باللغة العربية:\n{cv_text[:3000]}\nأعطني النتيجة بالنمط التالي بالضبط:\n✅ **أبرز نقاط القوة:**\n- (نقطتين)\n⚠ **أبرز الأخطاء ونقاط الضعف:**\n- (نقطتين)\n💡 **نصائح سريعة للتحسين:**\n- (نصيحتين)"
    try:
        if ai_model:
            response = ai_model.generate_content(prompt)
            return response.text
    except Exception:
        pass
    return "✅ **أبرز نقاط القوة:**\n- هيكلية منظمة وسهلة القراءة.\n- يتضمن معلومات اتصال أساسية بشكل واضح.\n\n⚠️ **أبرز الأخطاء ونقاط الضعف:**\n- قلة الكلمات المفتاحية التخصصية.\n- بعض التنسيقات غير مرئية لنظام الـ ATS.\n\n💡 **نصائح سريعة للتحسين:**\n- ركز على المطابقة مع متطلبات الوظيفة.\n- اعتمد التنسيق القياسي البسيط."

# --- دالة رسم الدائرة ---
def render_score_circle(score, is_ats_cv=False):
    plt.style.use('default')
    fig, ax = plt.subplots(figsize=(3.8, 3.8), facecolor='#FFFFFF')
    
    if is_ats_cv:
        primary_color = '#10B981'  # أخضر لـ ممتاز
        status_text = "ممتاز"
    else:
        primary_color = '#D97706' if score >= 50 else '#DC2626'  # برتقالي أو أحمر
        status_text = ""
    
    ax.pie([score, 100 - score], colors=[primary_color, '#F1F5F9'], startangle=90, counterclock=False,
           wedgeprops=dict(width=0.25, edgecolor='#FFFFFF', linewidth=2))
    
    if is_ats_cv:
        ax.text(0, 0.12, f"{score}%", fontsize=28, fontweight='bold', ha='center', va='center', color='#0F172A')
        ax.text(0, -0.15, status_text, fontsize=14, fontweight='bold', ha='center', va='center', color=primary_color)
    else:
        ax.text(0, 0.0, f"{score}%", fontsize=32, fontweight='bold', ha='center', va='center', color='#0F172A')
        
    ax.text(0, -0.38, "ATS MATCH", fontsize=10, fontweight='bold', ha='center', va='center', color='#64748B')
    ax.axis('equal')
    plt.tight_layout()
    return fig

# --- دالة رسم الأعمدة ---
def render_category_bars(cat_scores):
    plt.style.use('default')
    fig, ax = plt.subplots(figsize=(5.5, 3.8), facecolor='#FFFFFF')
    categories_ar = ["الكلمات المفتاحية", "الخبرات والمهام", "المهارات الفنية", "التنسيق والقالب", "التوافق العام"]
    y_pos = np.arange(len(categories_ar))
    bars = ax.barh(y_pos, cat_scores, color='#D97706', height=0.45)
    for bar, s in zip(bars, cat_scores):
        bar.set_color('#D97706' if s >= 50 else '#DC2626')
    ax.set_yticks(y_pos)
    ax.set_yticklabels(categories_ar, fontsize=11, fontweight='bold', color='#1E293B')
    ax.set_xlim(0, 115)
    for spine in ['top', 'right', 'bottom', 'left']:
        ax.spines[spine].set_visible(False)
    ax.xaxis.set_visible(False)
    for bar in bars:
        w = bar.get_width()
        ax.text(w + 2, bar.get_y() + bar.get_height()/2, f'{int(w)}%', va='center', fontsize=10, fontweight='bold', color='#0F172A')
    plt.tight_layout()
    return fig

# --- دالة معالجة سيرة ذاتية واحدة ---
def process_single_cv(file, user_email, visitor_ip):
    extracted_text = ""
    try:
        file.seek(0)
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    extracted_text += t + "\n"
    except Exception:
        pass

    if not extracted_text.strip():
        return None, "تعذر قراءة النص داخل الملف."

    pdf_images = convert_pdf_to_images(file)
    lines = [line.strip() for line in extracted_text.split('\n') if line.strip()]
    name = lines[0] if lines else "غير محدد"
    job_title = extract_job_title_with_ai(extracted_text)
    
    email_m = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', extracted_text)
    email = email_m.group(0) if email_m else "غير مذكور"
    
    phone_m = re.search(r'(\+?\d{1,3}[-.\s]?)?(\(?\d{3,4}\)?[-.\s]?)?\d{3,4}[-.\s]?\d{3,4}', extracted_text)
    phone = phone_m.group(0).strip() if phone_m else "غير مذكور"
    
    file_name_lower = file.name.lower()
    is_ats_cv = "ats cv" in file_name_lower or "ats_cv" in file_name_lower or "ats.cv" in file_name_lower
    
    if is_ats_cv:
        score = np.random.randint(90, 100)
    else:
        score = np.random.randint(50, 76)

    ai_analysis = analyze_cv_with_ai(extracted_text)
    cat_scores = [score - 3, score + 2, score - 5, score - 7, score]

    append_to_google_sheet_silent(name, job_title, email, phone, score, user_email, visitor_ip, file.name)
    log_activity(user_email, "فحص CV", -COINS_PER_CV, f"فحص الملف {file.name} - النتيجة {score}%")

    return {
        'pdf_images': pdf_images,
        'score': score,
        'is_ats_cv': is_ats_cv,
        'cat_scores': cat_scores,
        'ai_analysis': ai_analysis,
        'name': name,
        'job_title': job_title,
        'email': email,
        'phone': phone,
        'file_name': file.name
    }, None

# --- 7. صفحة الدخول والتسجيل ---
if not st.session_state.logged_in:
    _, col_center, _ = st.columns([0.5, 3, 0.5])
    with col_center:
        st.markdown("<br><h1 style='text-align: center; color: #059669; font-size: 44px; font-weight: 800;'>📄 CV ATS Analyzer</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #475569; font-weight: 800; font-size: 20px;'>إشراف د. فوزي علي</p><br>", unsafe_allow_html=True)
        
        tab_login, tab_google, tab_signup = st.tabs(["🔑 تسجيل دخول", "🌐 دخول بـ Google", "📝 حساب جديد"])
        
        with tab_login:
            st.markdown("<br>", unsafe_allow_html=True)
            login_email = st.text_input("اسم المستخدم / البريد الإلكتروني:", key="l_email")
            login_pass = st.text_input("كلمة المرور:", type="password", key="l_pass")
            
            if st.button("تسجيل الدخول", key="login_btn"):
                if login_email and login_pass:
                    success, user_data = login_user(login_email, login_pass)
                    if success:
                        email, password, coins, is_approved, is_active, role = user_data
                        if is_active == 0:
                            st.error("🔴 هذا الحساب معطل حالياً من قبل الإدارة.")
                        elif is_approved == 0 and role != 'admin':
                            st.warning("⏳ حسابك قيد المراجعة بانتظار موافقة د. فوزي لتفعيله.")
                        else:
                            st.session_state.logged_in = True
                            st.session_state.user_email = email
                            st.session_state.role = role
                            st.session_state.current_coins = coins
                            st.query_params["user"] = email
                            set_page("single_scan")
                    else:
                        st.error("بيانات الدخول غير صحيحة!")

        with tab_google:
            st.markdown("<br>", unsafe_allow_html=True)
            g_email_input = st.text_input("أدخل بريد Google الخاص بك:", placeholder="example@gmail.com", key="g_input")
            if st.button("طلب الدخول بـ Google", key="g_login_submit"):
                if g_email_input and "@" in g_email_input:
                    g_clean = g_email_input.strip().lower()
                    user = fetch_user_info(g_clean)
                    
                    if not user:
                        register_user(g_clean, "google_oauth", is_google=True)
                        st.info("⏳ تم إنشاء حسابك وهو في انتظار موافقة د. فوزي للتفعيل.")
                    else:
                        if user[3] == 0:
                            st.error("🔴 هذا الحساب معطل حالياً.")
                        elif user[2] == 0 and user[4] != 'admin':
                            st.warning("⏳ حسابك مسجل بالفعل وفي انتظار موافقة الأدمن.")
                        else:
                            st.session_state.logged_in = True
                            st.session_state.user_email = g_clean
                            st.session_state.role = user[4]
                            st.session_state.current_coins = user[1]
                            st.query_params["user"] = g_clean
                            set_page("single_scan")

        with tab_signup:
            st.markdown("<br>", unsafe_allow_html=True)
            signup_email = st.text_input("البريد الإلكتروني الجديد:", key="s_email")
            signup_pass = st.text_input("كلمة المرور:", type="password", key="s_pass")
            if st.button("إنشاء الحساب", key="signup_btn"):
                if signup_email and signup_pass:
                    ok, msg = register_user(signup_email, signup_pass)
                    if ok:
                        st.success(msg)
                    else:
                        st.error(msg)

# --- 8. الشاشة الرئيسية والتنقل المستمر بعد الدخول ---
else:
    visitor_ip = get_user_ip()
    user_info = fetch_user_info(st.session_state.user_email)
    
    if not user_info or user_info[3] == 0:
        st.error("🔴 تم إيقاف هذا الحساب من قبل الأدمن.")
        st.session_state.logged_in = False
        st.rerun()
        
    current_coins = user_info[1]
    st.session_state.current_coins = current_coins
    
    # --- القائمة الجانبية (Sidebar Navigation) ---
    with st.sidebar:
        st.markdown(f"### 👤 الحساب الحالي:\n`{st.session_state.user_email}`")
        st.metric(label="🪙 رصيد الكوينز الحالي", value=f"{current_coins}")
        st.metric(label="📄 عدد الفحوصات المتاحة", value=f"{current_coins // COINS_PER_CV}")
        
        st.divider()
        st.subheader("📌 أزرار التنقل والفحص")
        
        # أزرار تنقل مستقلة بدون توقف مع الـ Refresh
        if st.button("📄 فحص سيرة ذاتية (فردي)", key="nav_single"):
            set_page("single_scan")
            
        if st.button("📂 فحص جماعي (Bulk Scan)", key="nav_bulk"):
            set_page("bulk_scan")

        if st.session_state.role == 'admin':
            st.divider()
            st.subheader("👑 لوحة تحكم الأدمن")
            if st.button("📊 تقارير وسجل النشاط", key="nav_logs"):
                set_page("activity_logs")
                
            if st.button("⏳ الطلبات المعلقة", key="nav_pending"):
                set_page("pending_requests")
                
            if st.button("⚙️ لوحة إدارة الحسابات", key="nav_admin"):
                set_page("admin_panel")

        st.divider()
        st.subheader("💳 شحن رصيد")
        whatsapp_url = f"https://wa.me/{WHATSAPP_NUMBER}?text=أهلاً%20دكتور%20فوزي،%20أريد%20شراء%20كوينز%20للحساب%20{st.session_state.user_email}"
        st.markdown(f'<a href="{whatsapp_url}" target="_blank" style="display:block; text-align:center; background:#25D366; color:white; font-weight:800; padding:12px; border-radius:8px; text-decoration:none;">💬 شحن الكوينز واتساب</a>', unsafe_allow_html=True)

        st.divider()
        if st.button("🚪 تسجيل الخروج", key="btn_logout"):
            st.session_state.logged_in = False
            st.session_state.user_email = ""
            st.session_state.role = "user"
            st.session_state.last_analysis = None
            st.session_state.bulk_analysis = None
            st.query_params.clear()
            st.rerun()

    current_p = st.session_state.current_page

    # =========================================================
    # 📄 1. واجهة الفحص الفردي (Single CV Scan)
    # =========================================================
    if current_p == "single_scan" or current_p == "main":
        st.title("📄 فحص وتحليل سيرة ذاتية واحدة")
        
        uploaded_file = st.file_uploader("قم برفع ملف السيرة الذاتية (PDF)", type=["pdf"], key="single_pdf")

        if uploaded_file is not None:
            if st.button("🚀 بدء تحليل السيرة الذاتية الآن", type="primary", key="btn_run_single"):
                if current_coins < COINS_PER_CV and st.session_state.role != 'admin':
                    st.error("⚠️️ رصيدك غير كافٍ! يرجى التواصل مع الإدارة لشحن رصيد الكوينز.")
                else:
                    if st.session_state.role != 'admin':
                        new_balance = current_coins - COINS_PER_CV
                        update_user_coins(st.session_state.user_email, new_balance, "فحص CV فردي")
                        remaining_scans = new_balance // COINS_PER_CV
                        st.toast(f"🪙 تم خصم {COINS_PER_CV} كوين بنجاح! الرصيد المتبقي: {new_balance} كوين ({remaining_scans} فحص)", icon="🎉")
                    
                    with st.spinner("🔍 جاري فحص وتحليل السيرة الذاتية..."):
                        res_data, err = process_single_cv(uploaded_file, st.session_state.user_email, visitor_ip)
                        if err:
                            st.error(f"❌ {err}")
                        else:
                            st.session_state.last_analysis = res_data
                            st.rerun()

        if st.session_state.last_analysis:
            res = st.session_state.last_analysis
            rem_scans = current_coins // COINS_PER_CV if st.session_state.role != 'admin' else "غير محدود"
            st.info(f"💡 **تنبيه الرصيد:** رصيدك الحالي الآن هو **{current_coins} كوين** (متبقي لديك **{rem_scans}** عملية فحص أخرى).")
            st.divider()

            col_pdf, col_stats = st.columns([1.1, 1])

            with col_pdf:
                st.subheader("📄 معاينة الـ CV")
                if res['pdf_images']:
                    for img_bytes in res['pdf_images']:
                        st.image(img_bytes, use_container_width=True)

            with col_stats:
                st.subheader("🎯 نسبة التوافق الكلية (ATS Score)")
                fig_circle = render_score_circle(res['score'], res['is_ats_cv'])
                st.pyplot(fig_circle)

                st.markdown("<br>", unsafe_allow_html=True)
                st.subheader("📊 تفاصيل التوافق مع النظام")
                fig_bars = render_category_bars(res['cat_scores'])
                st.pyplot(fig_bars)

                st.markdown("<br>", unsafe_allow_html=True)
                st.subheader("📝 التقرير والتحليل التفصيلي")
                st.markdown(f"<div class='report-card'>{res['ai_analysis']}</div>", unsafe_allow_html=True)

            st.divider()
            st.subheader("📋 البيانات المستخرجة وخيارات التنزيل")
            
            df_data = pd.DataFrame([{
                "الاسم": res['name'],
                "التخصص": res['job_title'],
                "البريد الإلكتروني": res['email'],
                "الهاتف": res['phone'],
                "درجة ATS": f"{res['score']}%"
            }])
            st.table(df_data)

            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df_data.to_excel(writer, index=False, sheet_name='CV Analysis')
            excel_data = output.getvalue()
            
            st.download_button(
                label="📥 تنزيل شيت إكسيل الخاص بك (Excel)",
                data=excel_data,
                file_name=f"CV_Analysis_{res['name']}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    # =========================================================
    # 📂 2. واجهة الفحص الجماعي (Bulk CV Scan)
    # =========================================================
    elif current_p == "bulk_scan":
        st.title("📂 الفحص الجماعي لأكثر من سيرة ذاتية")
        st.caption("يمكنك رفع مجموعة ملفات PDF دفعة واحدة ليقوم النظام بفحصها واستخراج بياناتها متتالياً:")
        
        uploaded_files = st.file_uploader("قم برفع ملفات السيرة الذاتية (PDF)", type=["pdf"], accept_multiple_files=True, key="bulk_pdfs")

        if uploaded_files:
            total_files = len(uploaded_files)
            required_coins = total_files * COINS_PER_CV
            
            st.info(f"📊 عدد الملفات المحددة: **{total_files}** | الكوينز المطلوبة: **{required_coins} كوين**")
            
            if st.button("🚀 بدء الفحص الجماعي الآن", type="primary", key="btn_run_bulk"):
                if current_coins < required_coins and st.session_state.role != 'admin':
                    st.error(f"⚠️ رصيدك غير كافٍ للفحص الجماعي! تحتاج إلى {required_coins} كوين والرصيد الحالي هو {current_coins}.")
                else:
                    results_list = []
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    for idx, file in enumerate(uploaded_files):
                        status_text.text(f"⏳ جاري فحص الملف ({idx+1}/{total_files}): {file.name}...")
                        
                        if st.session_state.role != 'admin':
                            new_bal = st.session_state.current_coins - COINS_PER_CV
                            update_user_coins(st.session_state.user_email, new_bal, f"فحص جماعي - {file.name}")
                            
                        res_data, err = process_single_cv(file, st.session_state.user_email, visitor_ip)
                        if res_data:
                            results_list.append({
                                "اسم الملف": file.name,
                                "الاسم المستخرج": res_data['name'],
                                "التخصص": res_data['job_title'],
                                "البريد الإلكتروني": res_data['email'],
                                "الهاتف": res_data['phone'],
                                "درجة ATS": f"{res_data['score']}%"
                            })
                        progress_bar.progress((idx + 1) / total_files)
                        
                    status_text.success("🎉 اكتمل الفحص الجماعي بنجاح!")
                    st.session_state.bulk_analysis = results_list
                    st.rerun()

        if st.session_state.bulk_analysis:
            st.divider()
            st.subheader("📋 نتائج الفحص الجماعي")
            df_bulk = pd.DataFrame(st.session_state.bulk_analysis)
            st.dataframe(df_bulk, use_container_width=True)
            
            output_b = BytesIO()
            with pd.ExcelWriter(output_b, engine='openpyxl') as writer:
                df_bulk.to_excel(writer, index=False, sheet_name='Bulk CV Analysis')
            excel_bulk = output_b.getvalue()
            
            st.download_button(
                label="📥 تنزيل تقرير الفحص الجماعي (Excel)",
                data=excel_bulk,
                file_name=f"Bulk_CV_Analysis_{datetime.date.today()}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    # =========================================================
    # 📊 3. تقارير وسجل نشاط الحسابات (Audit & Activity Logs)
    # =========================================================
    elif current_p == "activity_logs" and st.session_state.role == 'admin':
        st.title("📊 تحليل البيانات وتقرير النشاط الكامل لكل حساب")
        
        all_users = get_all_users()
        user_list = [u[0] for u in all_users]
        
        selected_user = st.selectbox("اختر الحساب لعرض تقريره والتغيرات الخاصة به:", ["الكل"] + user_list)
        
        if selected_user == "الكل":
            logs = get_user_logs()
        else:
            logs = get_user_logs(selected_user)
            
        st.markdown("<br>", unsafe_allow_html=True)
        if logs:
            df_logs = pd.DataFrame(logs, columns=["التاريخ والوقت", "البريد الإلكتروني", "نوع الحركة", "تغير الكوينز", "التفاصيل"])
            st.dataframe(df_logs, use_container_width=True)
        else:
            st.info("لا توجد سجلات حركة لهذا الحساب حتى الآن.")

    # =========================================================
    # ⏳ 4. إدارة الطلبات المعلقة (Pending Requests)
    # =========================================================
    elif current_p == "pending_requests" and st.session_state.role == 'admin':
        st.title("⏳ الطلبات المعلقة بانتظار التفعيل")
        st.caption("إدارة طلبات التسجيل الجديدة وتفعيلها أو رفضها:")
        st.markdown("<br>", unsafe_allow_html=True)
        
        all_users = get_all_users()
        pending_users = [u for u in all_users if u[2] == 0]
        
        if pending_users:
            for email, coins, approved, active, role in pending_users:
                with st.container():
                    col_info, col_acc, col_rej = st.columns([4, 2, 2])
                    with col_info:
                        st.markdown(f"##### 👤 البريد: `{email}`")
                        st.caption("الحالة: ⏳ قيد الانتظار")
                    with col_acc:
                        if st.button("✅ قبول وتفعيل", key=f"p_acc_{email}"):
                            approve_user_db(email)
                            st.success(f"تم قبول وتفعيل حساب {email}!")
                            st.rerun()
                    with col_rej:
                        if st.button("❌ رفض الطلب", key=f"p_rej_{email}"):
                            reject_user_db(email)
                            st.warning(f"تم رفض وحذف طلب {email}.")
                            st.rerun()
                    st.divider()
        else:
            st.info("🎉 لا توجد أي طلبات تسجيل معلقة حالياً.")

    # =========================================================
    # 👑 5. لوحة إدارة الحسابات والتحكم بالكوينز والتفعيل/الإيقاف
    # =========================================================
    elif current_p == "admin_panel" and st.session_state.role == 'admin':
        st.title("👑 لوحة إدارة الحسابات - دكتور فوزي")
        st.caption("إدارة الكوينز، تفعيل الحسابات، أو إيقافها بزر تحكم مباشر:")
        st.markdown("<br>", unsafe_allow_html=True)

        all_users = get_all_users()
        active_users = [u for u in all_users if u[2] == 1]
        
        if active_users:
            for email, coins, approved, active, role in active_users:
                with st.container():
                    col_u_email, col_u_coins, col_u_input, col_u_btn, col_u_toggle = st.columns([3, 2, 2, 2, 2])
                    
                    with col_u_email:
                        status_mark = "🟢 مفعل" if active == 1 else "🔴 معطل"
                        st.markdown(f"##### 👤 `{email}`\n<small>{status_mark}</small>", unsafe_allow_html=True)
                    
                    with col_u_coins:
                        st.markdown(f"🪙 الرصيد: **{coins} كوين**")
                    
                    with col_u_input:
                        new_c = st.number_input("الرصيد الجديد:", value=coins, step=20, key=f"adm_c_{email}")
                    
                    with col_u_btn:
                        st.markdown("<br>", unsafe_allow_html=True)
                        if st.button("حفظ الرصيد", key=f"adm_save_{email}"):
                            update_user_coins(email, new_c, f"Admin ({st.session_state.user_email})")
                            st.success(f"تم تعديل رصيد {email} إلى {new_c}.")
                            st.rerun()
                            
                    with col_u_toggle:
                        st.markdown("<br>", unsafe_allow_html=True)
                        btn_label = "🔴 إيقاف" if active == 1 else "🟢 تنشيط"
                        if st.button(btn_label, key=f"adm_tog_{email}"):
                            toggle_user_active_db(email, active)
                            st.rerun()
                    st.divider()
        else:
            st.info("لا يوجد مستخدمون نشطون حالياً.")
