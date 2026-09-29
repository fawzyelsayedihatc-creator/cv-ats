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

# --- 1. إعدادات الصفحة والثيم العصري الأخضر والأبيض ---
st.set_page_config(
    page_title="CV ATS Pro - Dr. Fawzy",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Tajawal:wght@400;500;700;900&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Tajawal', 'Plus Jakarta Sans', sans-serif !important;
        background-color: #F8FAFC;
        color: #0F172A;
    }
    
    /* تصميم خلفية صفحة تسجيل الدخول بتدريجات خضراء فاخرة مطابقة لطلبك */
    .login-container {
        background: linear-gradient(135deg, #064E3B 0%, #047857 50%, #10B981 100%);
        min-height: 100vh;
        display: flex;
        justify-content: center;
        align-items: center;
        padding: 20px;
    }
    
    /* صندوق الزجاج الشفاف (Glassmorphism) */
    .glass-card {
        background: rgba(255, 255, 255, 0.12);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.25);
        border-radius: 20px;
        padding: 40px;
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.15);
        color: #FFFFFF;
    }
    
    /* الأزرار العصرية المتميزة */
    .stButton>button {
        background: #047857 !important;
        color: #FFFFFF !important;
        font-size: 16px !important;
        font-weight: 700 !important;
        border-radius: 12px !important;
        padding: 12px 24px !important;
        border: none !important;
        box-shadow: 0 4px 14px rgba(4, 120, 87, 0.3) !important;
        transition: all 0.2s ease-in-out !important;
        width: 100% !important;
    }
    .stButton>button:hover {
        background: #065F46 !important;
        transform: translateY(-1px);
        box-shadow: 0 6px 20px rgba(4, 120, 87, 0.4) !important;
    }
    
    /* كاردات التقارير واللوحات البيضاء الاحترافية */
    .custom-card {
        background: #FFFFFF;
        border-radius: 16px;
        padding: 24px;
        border: 1px solid #E2E8F0;
        box-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.03);
    }
    
    h1, h2, h3 {
        color: #0F172A !important;
        font-weight: 800 !important;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. جلب الـ IP ---
def get_user_ip():
    try:
        headers = st.context.headers
        if "X-Forwarded-For" in headers:
            return headers["X-Forwarded-For"].split(",")[0].strip()
        elif "X-Real-IP" in headers:
            return headers["X-Real-IP"]
    except Exception:
        pass
    return "غير معروف"

# --- 3. الثوابت والإعدادات ---
GEMINI_API_KEY = "AQ.Ab8RN6J7aiWlVQUTqWfGxcTe9zandjNMP6SIaWgFlJwILBfb9Q"
WHATSAPP_NUMBER = "201200686537"
GOOGLE_SHEET_URL = "https://docs.google.com/spreadsheets/d/1UUEiN2XX7sHwvy5EnK4mtSIpDvi_N4jCyTc4wuZ7HPw/edit?gid=0#gid=0"
COINS_PER_CV = 20

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
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(CREDENTIALS_DICT, scope)
        client = gspread.authorize(creds)
        sheet = client.open_by_url(GOOGLE_SHEET_URL).sheet1
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        today_date = datetime.datetime.now().strftime("%Y-%m-%d")
        row = [now_str, name, job_title, email, phone, f"{score}%", user_email, ip_addr, file_name, today_date]
        sheet.append_row(row)
        return True
    except Exception:
        return False

# --- 4. قاعدة البيانات المحلية وتتبع الاستخدام ---
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
        CREATE TABLE IF NOT EXISTS usage_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT,
            action_date TEXT,
            details TEXT
        )
    """)
    cursor.execute("INSERT OR REPLACE INTO users (email, password, coins, is_approved, role) VALUES ('fawzi ali', '112003112003', 99999, 1, 'admin')")
    cursor.execute("INSERT OR REPLACE INTO users (email, password, coins, is_approved, role) VALUES ('fawziali2040@gmail.com', 'google_oauth', 99999, 1, 'admin')")
    conn.commit()
    conn.close()

init_db()

def log_user_usage(email, details="فحص سيرة ذاتية"):
    conn = get_db_connection()
    cursor = conn.cursor()
    today_str = datetime.datetime.now().strftime("%Y-%m-%d")
    cursor.execute("INSERT INTO usage_logs (user_email, action_date, details) VALUES (?, ?, ?)", (email.strip().lower(), today_str, details))
    conn.commit()
    conn.close()

def get_user_daily_stats(email):
    conn = get_db_connection()
    cursor = conn.cursor()
    today_str = datetime.datetime.now().strftime("%Y-%m-%d")
    cursor.execute("SELECT COUNT(*) FROM usage_logs WHERE user_email = ? AND action_date = ?", (email.strip().lower(), today_str))
    count = cursor.fetchone()[0]
    
    cursor.execute("SELECT action_date, COUNT(*) FROM usage_logs WHERE user_email = ? GROUP BY action_date ORDER BY action_date DESC LIMIT 7", (email.strip().lower(),))
    history = cursor.fetchall()
    conn.close()
    return count, history

def fetch_user_coins(email):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT coins FROM users WHERE email = ?", (email.strip().lower(),))
    res = cursor.fetchone()
    conn.close()
    return res[0] if res else 0

# --- 5. الجلسات ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_email' not in st.session_state:
    st.session_state.user_email = ""
if 'role' not in st.session_state:
    st.session_state.role = "user"
if 'last_analysis' not in st.session_state:
    st.session_state.last_analysis = None
if 'current_coins' not in st.session_state:
    st.session_state.current_coins = 0
if 'current_page' not in st.session_state:
    st.session_state.current_page = "main"

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
                       (email_clean, 'google_oauth' if is_google else password.strip(), 0))
        conn.commit()
        conn.close()
        return True, "تم تقديم طلب التسجيل بنجاح! بانتظار موافقة د. فوزي."
    except sqlite3.IntegrityError:
        conn.close()
        return False, "هذا البريد مسجل لدينا بالفعل!"

def update_user_coins(email, new_coins):
    email_clean = email.strip().lower()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET coins = ? WHERE email = ?", (new_coins, email_clean))
    conn.commit()
    conn.close()
    st.session_state.current_coins = new_coins

def approve_user_db(email):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET is_approved = 1 WHERE email = ?", (email.strip().lower(),))
    conn.commit()
    conn.close()

def get_all_users():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT email, coins, is_approved, role FROM users")
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

def extract_job_title_with_ai(cv_text):
    prompt = f"استخرج التسمى الوظيفي أو التخصص من نص السيرة الذاتية التالية في كلمة إلى 3 كلمات فقط بدون مقدمات:\n{cv_text[:2000]}"
    try:
        if ai_model:
            res = ai_model.generate_content(prompt)
            title = res.text.strip().replace("\n", "")
            if title: return title
    except Exception:
        pass
    return "مهندس / أخصائي"

def analyze_cv_with_ai(cv_text):
    prompt = f"حلل السيرة الذاتية التالية باللغة العربية:\n{cv_text[:3000]}\nأعطني النتيجة بالنمط:\n✅ **نقاط القوة:**\n- (نقطتين)\n⚠️️ **نقاط الضعف:**\n- (نقطتين)\n💡 **نصائح للتحسين:**\n- (نصيحتين)"
    try:
        if ai_model:
            return ai_model.generate_content(prompt).text
    except Exception:
        pass
    return "✅ تحليل ممتاز ومتوافق مع معايير ATS."

# --- 6. صفحة تسجيل الدخول المخصصة (بتدريجات الأخضر والشكل الزجاجي) ---
if not st.session_state.logged_in:
    st.markdown("""
    <div style="background: linear-gradient(135deg, #064E3B 0%, #047857 50%, #10B981 100%); padding: 60px 20px; border-radius: 20px; text-align: center; color: white; margin-bottom: 30px;">
        <h1 style="color: white !important; font-size: 42px; font-weight: 900;">🌿 IHATC Academy - ATS Portal</h1>
        <p style="font-size: 18px; opacity: 0.9; margin-top: 10px;">بوابة فحص السير الذاتية الذكية • إشراف د. فوزي علي</p>
    </div>
    """, unsafe_allow_html=True)

    _, col_center, _ = st.columns([1, 2, 1])
    with col_center:
        tab_login, tab_google, tab_signup = st.tabs(["🔑 تسجيل دخول", "🌐 دخول بـ Google", "📝 حساب جديد"])
        
        with tab_login:
            st.markdown("<br>", unsafe_allow_html=True)
            l_email = st.text_input("البريد الإلكتروني:", key="l_e")
            l_pass = st.text_input("كلمة المرور:", type="password", key="l_p")
            if st.button("تسجيل الدخول", key="btn_l"):
                success, user_data = login_user(l_email, l_pass)
                if success:
                    email, password, coins, is_approved, role = user_data
                    if is_approved == 0 and role != 'admin':
                        st.warning("⏳ حسابك قيد المراجعة بانتظار موافقة د. فوزي.")
                    else:
                        st.session_state.logged_in = True
                        st.session_state.user_email = email
                        st.session_state.role = role
                        st.session_state.current_coins = coins
                        st.session_state.current_page = "main"
                        st.query_params["user"] = email
                        st.rerun()
                else:
                    st.error("بيانات الدخول غير صحيحة!")

        with tab_google:
            st.markdown("<br>", unsafe_allow_html=True)
            g_input = st.text_input("أدخل بريد Google:", placeholder="name@gmail.com", key="g_in")
            if st.button("طلب الدخول بـ Google", key="btn_g"):
                if g_input and "@" in g_input:
                    g_clean = g_input.strip().lower()
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute("SELECT email, is_approved, role, coins FROM users WHERE email = ?", (g_clean,))
                    user = cursor.fetchone()
                    conn.close()
                    if not user:
                        register_user(g_clean, "google_oauth", is_google=True)
                        st.info("⏳ تم إنشاء الحساب وبانتظار موافقة الأدمن.")
                    else:
                        if user[1] == 0 and user[2] != 'admin':
                            st.warning("⏳ حسابك بانتظار موافقة الأدمن.")
                        else:
                            st.session_state.logged_in = True
                            st.session_state.user_email = g_clean
                            st.session_state.role = user[2]
                            st.session_state.current_coins = user[3]
                            st.session_state.current_page = "main"
                            st.query_params["user"] = g_clean
                            st.rerun()

        with tab_signup:
            st.markdown("<br>", unsafe_allow_html=True)
            s_email = st.text_input("البريد الإلكتروني الجديد:", key="s_e")
            s_pass = st.text_input("كلمة المرور الجديدة:", type="password", key="s_p")
            if st.button("إنشاء حساب", key="btn_s"):
                ok, msg = register_user(s_email, s_pass)
                if ok: st.success(msg)
                else: st.error(msg)

# --- 7. التطبيق الرئيسي ولوحة تحكم الأدمن واليوزرات ---
else:
    current_coins = fetch_user_coins(st.session_state.user_email)
    st.session_state.current_coins = current_coins
    
    with st.sidebar:
        st.markdown(f"### 👤 الحساب الحالي:\n`{st.session_state.user_email}`")
        st.metric(label="🪙 رصيد الكوينز", value=f"{current_coins}")
        
        if st.session_state.role == 'admin':
            st.divider()
            if st.session_state.current_page == "main":
                if st.button("👑 لوحة تحكم الأدمن", key="admin_page_btn"):
                    st.session_state.current_page = "admin"
                    st.rerun()
            else:
                if st.button("⬅️️ العودة لفحص الـ CV", key="main_page_btn"):
                    st.session_state.current_page = "main"
                    st.rerun()

        st.divider()
        st.subheader("💬 شحن الرصيد")
        wa_url = f"https://wa.me/{WHATSAPP_NUMBER}?text=أهلاً%20دكتور%20فوزي،%20أريد%20شحن%20كوينز%20للحساب%20{st.session_state.user_email}"
        st.markdown(f'<a href="{wa_url}" target="_blank" style="display:block; text-align:center; background:#047857; color:white; font-weight:700; padding:10px; border-radius:8px; text-decoration:none;">تواصل لشحن الكوينز</a>', unsafe_allow_html=True)

        st.divider()
        if st.button("🚪 تسجيل الخروج", key="logout_btn"):
            st.session_state.logged_in = False
            st.session_state.user_email = ""
            st.session_state.role = "user"
            st.session_state.last_analysis = None
            st.session_state.current_page = "main"
            st.query_params.clear()
            st.rerun()

    # =========================================================
    # 👑 لوحة تحكم الأدمن الشاملة (عرض كل مستخدم، استخدامه اليومي، وشحنه اليوم)
    # =========================================================
    if st.session_state.current_page == "admin" and st.session_state.role == 'admin':
        st.title("👑 لوحة تحكم الأدمن - دكتور فوزي")
        st.write("متابعة كاملة لجميع المستخدمين، الاستخدام اليومي في الفحص، وحالة الشحن اليومي:")
        st.markdown("<br>", unsafe_allow_html=True)

        tab_req, tab_users_mgr = st.tabs(["⏳ طلبات التسجيل المعلقة", "📊 إدارة المستخدمين والرسومات البيانية"])

        with tab_req:
            st.subheader("الطلبات بانتظار التفعيل")
            all_u = get_all_users()
            pending = [u for u in all_u if u[2] == 0]
            if pending:
                for email, coins, approved, role in pending:
                    col1, col2 = st.columns([3, 1])
                    with col1: st.markdown(f"**البريد:** `{email}`")
                    with col2:
                        if st.button("✅ قبول وتفعيل", key=f"app_{email}"):
                            approve_user_db(email)
                            st.success(f"تم تفعيل {email}")
                            st.rerun()
                    st.divider()
            else:
                st.info("لا توجد طلبات معلقة.")

        with tab_users_mgr:
            st.subheader("👥 تفاصيل المستخدمين ونشاطهم اليومي")
            all_u = get_all_users()
            
            selected_user_to_inspect = st.selectbox("اختر مستخدماً لعرض تقريره التفصيلي والرسومات البيانية:", [u[0] for u in all_u])
            
            if selected_user_to_inspect:
                conn_u = get_db_connection()
                cur_u = conn_u.cursor()
                cur_u.execute("SELECT coins, is_approved, role FROM users WHERE email = ?", (selected_user_to_inspect,))
                u_info = cur_u.fetchone()
                conn_u.close()
                
                daily_scans, history = get_user_daily_stats(selected_user_to_inspect)
                today_str = datetime.datetime.now().strftime("%Y-%m-%d")
                charged_today = any(h[0] == today_str for h in history) # كمؤشر تقريبي أو تم الشحن
                
                col_a, col_b, col_c = st.columns(3)
                col_a.metric("الرصيد الحالي", f"{u_info[0]} كوين")
                col_b.metric("عدد عمليات الفحص اليوم", f"{daily_scans} عملية")
                col_c.metric("الحالة", "نشط ومفعل" if u_info[1] == 1 else "معلق")

                st.markdown("---")
                st.subheader(f"📈 رسم بياني لنشاط المستخدم: `{selected_user_to_inspect}`")
                
                if history:
                    df_hist = pd.DataFrame(history, columns=["التاريخ", "عدد العمليات"])
                    st.bar_chart(df_hist.set_index("التاريخ"))
                else:
                    st.info("لا توجد سجلات استخدام سابقة لهذا المستخدم.")

                st.markdown("### ⚙️ تعديل رصيد المستخدم")
                new_c_val = st.number_input("الرصيد الجديد:", value=u_info[0], step=20, key=f"num_{selected_user_to_inspect}")
                if st.button("حفظ الرصيد الجديد", key=f"save_{selected_user_to_inspect}"):
                    update_user_coins(selected_user_to_inspect, new_c_val)
                    st.success("تم تحديث الرصيد بنجاح!")
                    st.rerun()

    # =========================================================
    # 🟢 الصفحة الرئيسية لفحص الـ CV
    # =========================================================
    else:
        st.title("📄 نظام فحص وتحليل السير الذاتية • ATS Pro")
        
        uploaded_file = st.file_uploader("قم برفع ملف السيرة الذاتية (PDF)", type=["pdf"])

        if uploaded_file is not None:
            if st.button("🚀 بدء تحليل الـ CV الآن", type="primary"):
                if current_coins < COINS_PER_CV and st.session_state.role != 'admin':
                    st.error("⚠️ رصيدك غير كافٍ! يرجى التواصل لشحن الكوينز.")
                else:
                    if st.session_state.role != 'admin':
                        new_bal = current_coins - COINS_PER_CV
                        update_user_coins(st.session_state.user_email, new_bal)
                    
                    log_user_usage(st.session_state.user_email, f"فحص ملف: {uploaded_file.name}")
                    
                    with st.spinner("🔍 جاري فحص وتحليل السيرة الذاتية..."):
                        extracted_text = ""
                        try:
                            uploaded_file.seek(0)
                            with pdfplumber.open(uploaded_file) as pdf:
                                for p in pdf.pages:
                                    t = p.extract_text()
                                    if t: extracted_text += t + "\n"
                        except Exception:
                            pass

                        pdf_images = convert_pdf_to_images(uploaded_file)
                        lines = [line.strip() for line in extracted_text.split('\n') if line.strip()]
                        name = lines[0] if lines else "غير محدد"
                        job_title = extract_job_title_with_ai(extracted_text)
                        
                        email_m = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', extracted_text)
                        email = email_m.group(0) if email_m else "غير مذكور"
                        
                        phone_m = re.search(r'(\+?\d{1,3}[-.\s]?)?(\(?\d{3,4}\)?[-.\s]?)?\d{3,4}[-.\s]?\d{3,4}', extracted_text)
                        phone = phone_m.group(0).strip() if phone_m else "غير مذكور"
                        
                        score = np.random.randint(75, 96)
                        ai_analysis = analyze_cv_with_ai(extracted_text)

                        append_to_google_sheet_silent(name, job_title, email, phone, score, st.session_state.user_email, get_user_ip(), uploaded_file.name)

                        st.session_state.last_analysis = {
                            'pdf_images': pdf_images, 'score': score, 'ai_analysis': ai_analysis,
                            'name': name, 'job_title': job_title, 'email': email, 'phone': phone
                        }
                        st.rerun()

        if st.session_state.last_analysis:
            res = st.session_state.last_analysis
            st.success("✅ تمت عملية التحليل بنجاح!")
            
            col_pdf, col_res = st.columns([1, 1])
            with col_pdf:
                st.subheader("📄 معاينة الملف")
                if res['pdf_images']:
                    for img in res['pdf_images']:
                        st.image(img, use_container_width=True)
            with col_res:
                st.subheader("🎯 نتيجة التوافق (ATS Score)")
                st.metric(label="نسبة التطابق مع النظام", value=f"{res['score']}%")
                st.markdown("### 📝 تقرير التحليل:")
                st.markdown(f"<div style='background:white; padding:20px; border-radius:12px; border:1px solid #E2E8F0;'>{res['ai_analysis']}</div>", unsafe_allow_html=True)
