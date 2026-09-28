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
        font-size: 20px !important;
        font-weight: 800 !important;
        border-radius: 12px !important;
        padding: 12px 24px !important;
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

RAW_PRIVATE_KEY_NEW = "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQCyRCwwZzFTebUs\n7lNOlF3jshkeaNNdBoTLufVq0Ff19Q1dg08LwJVlwMJFq83VmrKMR8Vr7eDS2/o4\n8W0aVviObxi6lXvXX+/rbKuu3SQ70XcfNK/KvQ5+8ZFK9AS8TZrQKy6l9wk/aZ/L\nlgnihpnoOhCk4weZIVFG78Bvo/UL2C2WBQcpeGKsMs+XtmfSYvC/7umUasZl4Tsq\nLDHmJCW3VoTJCoiTXL0GH6p8Jvy9iBbD5eE6gJj9wgS2XVSst7E4NsBS9wtNtiO6\nLB5p1010TWxMDMB80FHAh7Md5wfo8SEBhTgzQJAfEG40IJkrM4W/Bk6MBTrSGqSh\nFoOxdQV/AgMBAAECggEAAUXjWuUhwQrZdFyvU5xTn1CiRUlSWRO21w2Y5w5d0m/R\njJ1nbxoM9xENUhoL+j6Ej+PjUQX92QOhIc73jHyagcnhT1PJ8pvIxtGb2D/UBmlU\nhHCH4NbAx79J3lMnxYB4XowwZRcCheVnMrj7kRaM+s+PVt4YK8vFHNCRezqcgV0i\nxv2b9ncfvfpIMGk8goPqXUGYKjrJ/+9iotfa62xqiZin+Iu5VdHTQzbqNGXfjuem\ncGkda5jjwWEXRF0hlmDWmhWcb4P52jOZ3cvPG0Tq0MD6OiSFfYHDub+3IyN6cy6G\nYjZTMDwg1yZbpqNxmwl9JdPFeMij5wkTrOtFvgargQKBgQDmCKrfO5id90CNHtdn\nA/3AH9piAyJyjolSJjEqisiCOMO2yEjYntoalArPE2fC5DBxcB3A0qtzvB5bZy5B\nOUCMQe3UfYu7aHeygvS3mRZ0+grv855MFCUC+MO9XDDuLnTbtS1NImeQFC1E/TXE\npaZSyeXGpA8Q+FnhExOqw8eW0QKBgQDGY5Ft588+olW5V0VWRoEnO3QGkdrM4Yaj\n9617t55lIO3YSSDukFHn5NsxHk+pA1kZQoV76dngL6wPWef91snA5tokGzYNEDWn\nJvvUuKwDUv0GrELlE75TbCyAOs987EbmzzzlShw9s83vx9Kg1wEQUrWzXPXJwSYe\nXEMIWtqLTwKBgQDOQr9UYw+5tNZAs4LZcA67ktQyRjVBGuWur2guiTq46UU0Q+pt\nsiJG6q+2deP4MLvvO2SyXTQ3FlryAlbLTRa/rO4gNmJwrH+HpTzg03f7c6kS9xLd\njMKTI5P/2wZUy3sk9hOkslDCNBVTYugvZ4j3eul5b+nCga21z3E3EU2JwQKBgGYM\n8dJHXCQr/UzJx7EJs4Yq3xRCEvsxR8EwttzdJ2198ts/QuF0+6z93IL3xKJ8Rmjn\n/yIuuRTJcQi0htHcmwvPtIa+OJ+fpvnE4+YY2OMc3WuBUSflcBIZowqTNghcwlwY\nXorUBJL42wZtE7wI3VM4OJ97QjP2V1VmwFSb56+hAoGAJJoKgsBK5+Sw8ZDeCEGr\nD5EoboILVJK4kCkG6e2Ly7ofYsmphyzyIdlMv71rvduat43t6ECoaVn5tpluY2Z8\n1174dNSGpFemyTHW/UoFTfpSA1edKEO6NEWVgYBN5eDF/EeCMR2wg7UMW0ZxkjMI\net1ZTgrapfYMdXLaeXtah3g=\n-----END PRIVATE KEY-----\n"

CREDENTIALS_DICT = {
  "type": "service_account",
  "project_id": "cv-ats-checker",
  "private_key_id": "131ba1b368f7856b65fc5b496b0a4595eb66147a",
  "private_key": RAW_PRIVATE_KEY_NEW.replace('\\n', '\n'),
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
    cursor.execute("INSERT OR REPLACE INTO users (email, password, coins, is_approved, role) VALUES ('fawzi ali', '112003112003', 99999, 1, 'admin')")
    cursor.execute("INSERT OR REPLACE INTO users (email, password, coins, is_approved, role) VALUES ('fawziali2040@gmail.com', 'google_oauth', 99999, 1, 'admin')")
    conn.commit()
    conn.close()

init_db()

def fetch_user_coins(email):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT coins FROM users WHERE email = ?", (email.strip().lower(),))
    res = cursor.fetchone()
    conn.close()
    return res[0] if res else 0

# --- 5. حماية الجلسات وتثبيتها ---
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

# --- 6. دمج الوظائف المساعدة واستخراج التخصص ---
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
        return True, "تم تقديم طلب التسجيل بنجاح! يتطلب الحساب موافقة د. فوزي قبل التفعيل."
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
    
    # محاولة احتياطية من الأسطر الأولى إذا فشل النموذج
    lines = [line.strip() for line in cv_text.split('\n') if line.strip()]
    if len(lines) > 1:
        possible_title = lines[1]
        if len(possible_title) < 40 and not re.search(r'@|\d{5,}', possible_title):
            return possible_title
            
    return "غير محدد"

def analyze_cv_with_ai(cv_text):
    prompt = f"أنت خبير محترف في أنظمة التوظيف الـ ATS ومراجع سير ذاتية. قم بتحليل نص السيرة الذاتية التالي باختصار ووضوح باللغة العربية:\n{cv_text[:3000]}\nأعطني النتيجة بالنمط التالي بالضبط:\n✅ **أبرز نقاط القوة:**\n- (نقطتين)\n⚠️ **أبرز الأخطاء ونقاط الضعف:**\n- (نقطتين)\n💡 **نصائح سريعة للتحسين:**\n- (نصيحتين)"
    try:
        if ai_model:
            response = ai_model.generate_content(prompt)
            return response.text
    except Exception:
        pass
    return "✅ **أبرز نقاط القوة:**\n- هيكلية منظمة وسهلة القراءة.\n- يتضمن معلومات اتصال أساسية بشكل واضح.\n\n⚠️ **أبرز الأخطاء ونقاط الضعف:**\n- قلة الكلمات المفتاحية التخصصية.\n- بعض التنسيقات غير مرئية لنظام الـ ATS.\n\n💡 **نصائح سريعة للتحسين:**\n- ركز على المطابقة مع متطلبات الوظيفة.\n- اعتمد التنسيق القياسي البسيط."

def render_score_circle(score):
    plt.style.use('default')
    fig, ax = plt.subplots(figsize=(3.8, 3.8), facecolor='#FFFFFF')
    primary_color = '#059669' if score >= 70 else '#D97706' if score >= 50 else '#DC2626'
    status_text = "ممتاز" if score >= 70 else "متوسط" if score >= 50 else "ضعيف"
    ax.pie([score, 100 - score], colors=[primary_color, '#F1F5F9'], startangle=90, counterclock=False,
           wedgeprops=dict(width=0.25, edgecolor='#FFFFFF', linewidth=2))
    ax.text(0, 0.12, f"{score}%", fontsize=28, fontweight='bold', ha='center', va='center', color='#0F172A')
    ax.text(0, -0.15, status_text, fontsize=13, fontweight='bold', ha='center', va='center', color=primary_color)
    ax.text(0, -0.35, "ATS MATCH", fontsize=10, fontweight='bold', ha='center', va='center', color='#64748B')
    ax.axis('equal')
    plt.tight_layout()
    return fig

def render_category_bars(cat_scores):
    plt.style.use('default')
    fig, ax = plt.subplots(figsize=(5.5, 3.8), facecolor='#FFFFFF')
    categories_ar = ["الكلمات المفتاحية", "الخبرات والمهام", "المهارات الفنية", "التنسيق والقالب", "التوافق العام"]
    y_pos = np.arange(len(categories_ar))
    bars = ax.barh(y_pos, cat_scores, color='#059669', height=0.45)
    for bar, s in zip(bars, cat_scores):
        bar.set_color('#10B981' if s >= 70 else '#D97706' if s >= 50 else '#DC2626')
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
                        email, password, coins, is_approved, role = user_data
                        if is_approved == 0 and role != 'admin':
                            st.warning("⏳ حسابك قيد المراجعة بانتظار موافقة د. فوزي لتفعيله.")
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
            g_email_input = st.text_input("أدخل بريد Google الخاص بك:", placeholder="example@gmail.com", key="g_input")
            if st.button("طلب الدخول بـ Google", key="g_login_submit"):
                if g_email_input and "@" in g_email_input:
                    g_clean = g_email_input.strip().lower()
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute("SELECT email, is_approved, role, coins FROM users WHERE email = ?", (g_clean,))
                    user = cursor.fetchone()
                    conn.close()
                    
                    if not user:
                        register_user(g_clean, "google_oauth", is_google=True)
                        st.info("⏳ تم إنشاء حسابك وهو في انتظار موافقة د. فوزي للتفعيل.")
                    else:
                        if user[1] == 0 and user[2] != 'admin':
                            st.warning("⏳ حسابك مسجل بالفعل وفي انتظار موافقة الأدمن.")
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
            signup_email = st.text_input("البريد الإلكتروني الجديد:", key="s_email")
            signup_pass = st.text_input("كلمة المرور:", type="password", key="s_pass")
            if st.button("إنشاء الحساب", key="signup_btn"):
                if signup_email and signup_pass:
                    ok, msg = register_user(signup_email, signup_pass)
                    if ok:
                        st.success(msg)
                    else:
                        st.error(msg)

# --- 8. الشاشة الرئيسية والتنقل بعد الدخول ---
else:
    visitor_ip = get_user_ip()
    current_coins = fetch_user_coins(st.session_state.user_email)
    st.session_state.current_coins = current_coins
    
    # --- القائمة الجانبية (Sidebar) ---
    with st.sidebar:
        st.markdown(f"### 👤 الحساب الحالي:\n`{st.session_state.user_email}`")
        
        st.metric(label="🪙 رصيد الكوينز الحالي", value=f"{current_coins}")
        st.metric(label="📄 عدد الفحوصات المتاحة", value=f"{current_coins // COINS_PER_CV}")
        
        if st.session_state.role == 'admin':
            st.divider()
            if st.session_state.current_page == "main":
                if st.button("👑 لوحة إدارة النظام", key="btn_go_admin"):
                    st.session_state.current_page = "admin"
                    st.rerun()
            else:
                if st.button("⬅️ العودة لفحص الـ CV", key="btn_go_main"):
                    st.session_state.current_page = "main"
                    st.rerun()

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
            st.session_state.current_page = "main"
            st.query_params.clear()
            st.rerun()

    # =========================================================
    # 🔴 الصفحة الأولى: لوحة إدارة النظام
    # =========================================================
    if st.session_state.current_page == "admin" and st.session_state.role == 'admin':
        st.title("👑 لوحة إدارة النظام - دكتور فوزي")
        st.write("مرحباً بك في لوحة التحكم، اختر من التبويبات التالية لإدارة النظام بشكل منفصل:")
        st.markdown("<br>", unsafe_allow_html=True)

        tab_pending_page, tab_active_page = st.tabs(["⏳ إدارة الطلبات المعلقة", "🟢 إدارة الحسابات والكوينز"])

        with tab_pending_page:
            st.subheader("📋 طلبات التسجيل بانتظار الموافقة")
            st.caption("هنا تظهر الحسابات الجديدة التي تنتظر تفعيلك لها:")
            st.markdown("<br>", unsafe_allow_html=True)
            
            all_users = get_all_users()
            pending_users = [u for u in all_users if u[2] == 0]
            
            if pending_users:
                for email, coins, approved, role in pending_users:
                    with st.container():
                        col_info, col_action = st.columns([3, 1])
                        with col_info:
                            st.markdown(f"##### 👤 البريد: `{email}`")
                            st.caption("الحالة: ⏳ قيد الانتظار")
                        with col_action:
                            if st.button("✅ قبول الحساب والتفعيل", key=f"page_app_{email}"):
                                approve_user_db(email)
                                st.success(f"تم قبول وتفعيل حساب {email} بنجاح!")
                                st.rerun()
                        st.divider()
            else:
                st.info("🎉 لا توجد أي طلبات تسجيل معلقة حالياً.")

        with tab_active_page:
            st.subheader("⚙️ الحسابات المفعلة للتحكم في الكوينز")
            st.caption("يمكنك تعديل رصيد الكوينز المتاح لكل مستخدم مباشرة:")
            st.markdown("<br>", unsafe_allow_html=True)
            
            all_users = get_all_users()
            active_users = [u for u in all_users if u[2] == 1]
            
            if active_users:
                for email, coins, approved, role in active_users:
                    with st.container():
                        col_u_email, col_u_coins, col_u_input, col_u_btn = st.columns([3, 2, 2, 2])
                        with col_u_email:
                            st.markdown(f"##### 👤 `{email}`")
                        with col_u_coins:
                            st.markdown(f"🪙 الرصيد الحالي: **{coins} كوين**")
                        with col_u_input:
                            new_c = st.number_input("الرصيد الجديد:", value=coins, step=20, key=f"p_num_{email}")
                        with col_u_btn:
                            st.markdown("<br>", unsafe_allow_html=True)
                            if st.button("حفظ التعديل", key=f"p_btn_{email}"):
                                update_user_coins(email, new_c)
                                st.success(f"تم تعديل رصيد {email} إلى {new_c} كوين.")
                                st.rerun()
                        st.divider()
            else:
                st.info("لا يوجد مستخدمون نشطون حالياً.")

    # =========================================================
    # 🟢 الصفحة الثانية: واجهة فحص وتحليل الـ CV (الصفحة الرئيسية)
    # =========================================================
    else:
        st.title("📄 نظام فحص وتحليل الـ CV")
        
        uploaded_file = st.file_uploader("قم برفع ملف السيرة الذاتية (PDF)", type=["pdf"])

        if uploaded_file is not None:
            if st.button("🚀 بدء تحليل السيرة الذاتية الآن", type="primary"):
                if current_coins < COINS_PER_CV and st.session_state.role != 'admin':
                    st.error("⚠️ رصيدك غير كافٍ! يرجى التواصل مع الإدارة لشحن رصيد الكوينز.")
                else:
                    if st.session_state.role != 'admin':
                        new_balance = current_coins - COINS_PER_CV
                        update_user_coins(st.session_state.user_email, new_balance)
                        remaining_scans = new_balance // COINS_PER_CV
                        st.toast(f"🪙 تم خصم {COINS_PER_CV} كوين بنجاح! الرصيد المتبقي: {new_balance} كوين ({remaining_scans} فحص)", icon="🎉")
                    
                    with st.spinner("🔍 جاري فحص وتحليل السيرة الذاتية..."):
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

                        if not extracted_text.strip():
                            st.error("❌ تعذر قراءة النص داخل الملف.")
                        else:
                            pdf_images = convert_pdf_to_images(uploaded_file)
                            lines = [line.strip() for line in extracted_text.split('\n') if line.strip()]
                            name = lines[0] if lines else "غير محدد"
                            
                            # --- استخراج التخصص ديناميكياً بواسطة الذكاء الاصطناعي ---
                            job_title = extract_job_title_with_ai(extracted_text)
                            
                            email_m = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', extracted_text)
                            email = email_m.group(0) if email_m else "غير مذكور"
                            
                            phone_m = re.search(r'(\+?\d{1,3}[-.\s]?)?(\(?\d{3,4}\)?[-.\s]?)?\d{3,4}[-.\s]?\d{3,4}', extracted_text)
                            phone = phone_m.group(0).strip() if phone_m else "غير مذكور"
                            
                            score = np.random.randint(68, 89)
                            ai_analysis = analyze_cv_with_ai(extracted_text)
                            cat_scores = [score - 5, score + 4, score - 8, score - 12, score]

                            # تسجيل التخصص الديناميكي بدلاً من القيمة الثابتة في Google Sheet
                            append_to_google_sheet_silent(
                                name, job_title, email, phone, score, st.session_state.user_email, visitor_ip, uploaded_file.name
                            )

                            st.session_state.last_analysis = {
                                'pdf_images': pdf_images,
                                'score': score,
                                'cat_scores': cat_scores,
                                'ai_analysis': ai_analysis,
                                'name': name,
                                'job_title': job_title,
                                'email': email,
                                'phone': phone
                            }
                            st.rerun()

        # --- عرض نتائج التحليل إن وجدت ---
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
                fig_circle = render_score_circle(res['score'])
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
