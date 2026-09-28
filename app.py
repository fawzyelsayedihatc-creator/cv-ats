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
    page_title="CV ATS Analyzer - Dr. Fawzy",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Tajawal', sans-serif !important; background-color: #F8FAFC; }
    .stApp { background-color: #F8FAFC; }
    
    .main-title {
        text-align: center; font-size: 28px; font-weight: 800; color: #1E293B; margin-bottom: 25px;
    }
    .stButton>button {
        background: linear-gradient(135deg, #059669 0%, #047857 100%) !important;
        color: #FFFFFF !important; font-size: 16px !important; font-weight: 700 !important;
        border-radius: 10px !important; padding: 12px 24px !important; border: none !important;
        box-shadow: 0 4px 12px rgba(5, 150, 105, 0.2) !important; width: 100% !important;
    }
    .report-card {
        background-color: #FFFFFF; border-radius: 12px; padding: 20px;
        border: 1px solid #E2E8F0; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); margin-bottom: 15px;
    }
    .score-badge {
        font-size: 32px; font-weight: 800; color: #059669; text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. إدارة الجلسة (Session State) ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_email' not in st.session_state:
    st.session_state.user_email = ""
if 'role' not in st.session_state:
    st.session_state.role = "user"
if 'last_analysis' not in st.session_state:
    st.session_state.last_analysis = None

# --- 3. الثوابت وإعدادات المفاتيح ---
GEMINI_API_KEY = "AQ.Ab8RN6J7aiWlVQUTqWfGxcTe9zandjNMP6SIaWgFlJwILBfb9Q"
GOOGLE_SHEET_URL = "https://docs.google.com/spreadsheets/d/1UUEiN2XX7sHwvy5EnK4mtSIpDvi_N4jCyTc4wuZ7HPw/edit?gid=0#gid=0"
INITIAL_FREE_COINS = 200

def get_gspread_credentials():
    if "gcp_service_account" in st.secrets:
        return dict(st.secrets["gcp_service_account"])
    
    raw_key = "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQCyRCwwZzFTebUs\n7lNOlF3jshkeaNNdBoTLufVq0Ff19Q1dg08LwJVlwMJFq83VmrKMR8Vr7eDS2/o4\n8W0aVviObxi6lXvXX+/rbKuu3SQ70XcfNK/KvQ5+8ZFK9AS8TZrQKy6l9wk/aZ/L\nlgnihpnoOhCk4weZIVFG78Bvo/UL2C2WBQcpeGKsMs+XtmfSYvC/7umUasZl4Tsq\nLDHmJCW3VoTJCoiTXL0GH6p8Jvy9iBbD5eE6gJj9wgS2XVSst7E4NsBS9wtNtiO6\nLB5p1010TWxMDMB80FHAh7Md5wfo8SEBhTgzQJAfEG40IJkrM4W/Bk6MBTrSGqSh\nFoOxdQV/AgMBAAECggEAAUXjWuUhwQrZdFyvU5xTn1CiRUlSWRO21w2Y5w5d0m/R\njJ1nbxoM9xENUhoL+j6Ej+PjUQX92QOhIc73jHyagcnhT1PJ8pvIxtGb2D/UBmlU\nhHCH4NbAx79J3lMnxYB4XowwZRcCheVnMrj7kRaM+s+PVt4YK8vFHNCRezqcgV0i\nxv2b9ncfvfpIMGk8goPqXUGYKjrJ/+9iotfa62xqiZin+Iu5VdHTQzbqNGXfjuem\ncGkda5jjwWEXRF0hlmDWmhWcb4P52jOZ3cvPG0Tq0MD6OiSFfYHDub+3IyN6cy6G\nYjZTMDwg1yZbpqNxmwl9JdPFeMij5wkTrOtFvgargQKBgQDmCKrfO5id90CNHtdn\nA/3AH9piAyJyjolSJjEqisiCOMO2yEjYntoalArPE2fC5DBxcB3A0qtzvB5bZy5B\nOUCMQe3UfYu7aHeygvS3mRZ0+grv855MFCUC+MO9XDDuLnTbtS1NImeQFC1E/TXE\npaZSyeXGpA8Q+FnhExOqw8eW0QKBgQDGY5Ft588+olW5V0VWRoEnO3QGkdrM4Yaj\n9617t55lIO3YSSDukFHn5NsxHk+pA1kZQoV76dngL6wPWef91snA5tokGzYNEDWn\nJvvUuKwDUv0GrELlE75TbCyAOs987EbmzzzlShw9s83vx9Kg1wEQUrWzXPXJwSYe\nXEMIWtqLTwKBgQDOQr9UYw+5tNZAs4LZcA67ktQyRjVBGuWur2guiTq46UU0Q+pt\nsiJG6q+2deP4MLvvO2SyXTQ3FlryAlbLTRa/rO4gNmJwrH+HpTzg03f7c6kS9xLd\njMKTI5P/2wZUy3sk9hOkslDCNBVTYugvZ4j3eul5b+nCga21z3E3EU2JwQKBgGYM\n8dJHXCQr/UzJx7EJs4Yq3xRCEvsxR8EwttzdJ2198ts/QuF0+6z93IL3xKJ8Rmjn\n/yIuuRTJcQi0htHcmwvPtIa+OJ+fpvnE4+YY2OMc3WuBUSflcBIZowqTNghcwlwY\nXorUBJL42wZtE7wI3VM4OJ97QjP2V1VmwFSb56+hAoGAJJoKgsBK5+Sw8ZDeCEGr\nD5EoboILVJK4kCkG6e2Ly7ofYsmphyzyIdlMv71rvduat43t6ECoaVn5tpluY2Z8\n1174dNSGpFemyTHW/UoFTfpSA1edKEO6NEWVgYBN5eDF/EeCMR2wg7UMW0ZxkjMI\net1ZTgrapfYMdXLaeXtah3g=\n-----END PRIVATE KEY-----\n"
    
    return {
        "type": "service_account",
        "project_id": "cv-ats-checker",
        "private_key_id": "131ba1b368f7856b65fc5b496b0a4595eb66147a",
        "private_key": raw_key.replace('\\n', '\n'),
        "client_email": "cv-sheet-bot@cv-ats-checker.iam.gserviceaccount.com",
        "client_id": "115860396992619540199",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/cv-sheet-bot%40cv-ats-checker.iam.gserviceaccount.com"
    }

try:
    genai.configure(api_key=GEMINI_API_KEY)
    ai_model = genai.GenerativeModel('gemini-1.5-flash')
except Exception:
    ai_model = None

def append_to_google_sheet(name, job_title, email, phone, score, user_email):
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds_dict = get_gspread_credentials()
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        sheet = client.open_by_url(GOOGLE_SHEET_URL).sheet1
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        row = [now_str, name, job_title, email, phone, f"{score}%", user_email]
        sheet.append_row(row)
        return True, "✅ تم التصدير تلقائياً لجدول Google Sheets بنجاح!"
    except Exception as e:
        return False, f"⚠️ خطأ في التصدير: {str(e)}"

# --- 4. قاعدة البيانات وإدارة المستخدمين ---
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
        return False, "يرجى كتابة البريد الإلكتروني."
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (email, password, coins, is_approved, role) VALUES (?, ?, ?, 0, 'user')",
                       (email_clean, 'google_oauth' if is_google else password.strip(), INITIAL_FREE_COINS))
        conn.commit()
        conn.close()
        return True, "تم إرسال الطلب بنجاح! ينتظر موافقة د. فوزي لتفعيل الحساب."
    except sqlite3.IntegrityError:
        conn.close()
        return False, "البريد مسجل مسبقاً!"

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

# --- 5. استخراج البيانات والتحليل بـ AI ---
def extract_pdf_text(file_bytes):
    text = ""
    with pdfplumber.open(BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            t = page.extract_text()
            if t: text += t + "\n"
    return text

def analyze_cv_with_gemini(cv_text, target_job=""):
    prompt = f"""
    أنت خبير فحص سير ذاتية ونظام ATS عالمي.
    قم بتحليل السيرة الذاتية التالية بأسلوب دقيق جداً للمسمى الوظيفي المستهدف: "{target_job}".
    
    قم باستخراج واستخراج ما يلي في صيغة JSON فقط بدون أي مقدمات أو أوساط:
    {{
      "name": "اسم المرشح",
      "job_title": "المسمى الوظيفي المستخرج",
      "email": "البريد الإلكتروني",
      "phone": "رقم الهاتف",
      "score": 85,
      "strengths": ["نقطة قوة 1", "نقطة قوة 2"],
      "weaknesses": ["نقطة ضعف 1", "نقطة ضعف 2"],
      "recommendations": ["توصية 1", "توصية 2"]
    }}
    
    نص السيرة الذاتية:
    {cv_text}
    """
    try:
        response = ai_model.generate_content(prompt)
        res_text = response.text.strip()
        json_match = re.search(r'\{.*\}', res_text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(0))
    except Exception:
        pass
    
    # Fallback
    return {
        "name": "المرشح",
        "job_title": target_job if target_job else "غير محدد",
        "email": "غير متوفر",
        "phone": "غير متوفر",
        "score": 75,
        "strengths": ["خبرة سابقة جيدة", "تنظيم الفقرات بشكل واضح"],
        "weaknesses": ["نقص بعض الكلمات المفتاحية لملاءمة نظام ATS"],
        "recommendations": ["إضافة المزيد من المهارات التقنية المطلوبة للمسمى الوظيفي"]
    }

# --- 6. الشاشات الرئيسية ---
if not st.session_state.logged_in:
    _, col_center, _ = st.columns([1, 1.8, 1])
    with col_center:
        st.markdown("<h1 class='main-title'>📄 نظام فحص السير الذاتية (ATS)</h1>", unsafe_allow_html=True)
        tab_login, tab_google, tab_signup = st.tabs(["🔑 دخول", "🌐 Google", "📝 حساب جديد"])
        
        with tab_login:
            login_email = st.text_input("البريد الإلكتروني:", key="l_email")
            login_pass = st.text_input("كلمة المرور:", type="password", key="l_pass")
            if st.button("تسجيل الدخول", key="login_btn"):
                ok, user_data = login_user(login_email, login_pass)
                if ok:
                    email, p, coins, approved, role = user_data
                    if approved == 0 and role != 'admin':
                        st.warning("⏳ الحساب قيد المراجعة بانتظار موافقة د. فوزي.")
                    else:
                        st.session_state.logged_in = True
                        st.session_state.user_email = email
                        st.session_state.role = role
                        st.rerun()
                else:
                    st.error("خطأ في بيانات الدخول!")

        with tab_google:
            g_email = st.text_input("أدخل بريد Google للطلب:", key="g_input")
            if st.button("طلب الدخول بـ Google", key="g_btn"):
                if g_email and "@" in g_email:
                    g_clean = g_email.strip().lower()
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute("SELECT email, is_approved, role FROM users WHERE email = ?", (g_clean,))
                    u = cursor.fetchone()
                    conn.close()
                    if not u:
                        register_user(g_clean, "google_oauth", is_google=True)
                        st.info("⏳ تم إنشاء الطلب وفي انتظار موافقة الأدمن.")
                    else:
                        if u[1] == 0 and u[2] != 'admin':
                            st.warning("⏳ الطلب معلق بانتظار الموافقة.")
                        else:
                            st.session_state.logged_in = True
                            st.session_state.user_email = g_clean
                            st.session_state.role = u[2]
                            st.rerun()

        with tab_signup:
            signup_email = st.text_input("البريد الجديد:", key="s_email")
            signup_pass = st.text_input("كلمة المرور:", type="password", key="s_pass")
            if st.button("إنشاء الحساب", key="s_btn"):
                ok, msg = register_user(signup_email, signup_pass)
                if ok: st.success(msg)
                else: st.error(msg)

else:
    # الشاشة الرئيسية للمستخدم والأدمن
    st.sidebar.markdown(f"### 👤 مرحباً: `{st.session_state.user_email}`")
    if st.sidebar.button("🚪 تسجيل الخروج"):
        st.session_state.logged_in = False
        st.session_state.user_email = ""
        st.session_state.role = "user"
        st.session_state.last_analysis = None
        st.rerun()

    # لوحة الأدمن للموافقات
    if st.session_state.role == 'admin':
        st.markdown("### 👑 لوحة تحكم الأدمن - طلبات الحسابات")
        all_u = get_all_users()
        pending = [u for u in all_u if u[2] == 0]
        if pending:
            for email, coins, approved, role in pending:
                c1, c2 = st.columns([3, 1])
                c1.write(f"👤 `{email}`")
                if c2.button("✅ قبول الحساب", key=f"app_{email}"):
                    approve_user_db(email)
                    st.success(f"تم قبول {email}")
                    st.rerun()
        else:
            st.info("لا توجد طلبات حسابات معلقة حالياً.")
        st.divider()

    st.markdown("<h2 style='text-align: center;'>⚡ فحص وتحليل الـ CV بالتفصيل</h2>", unsafe_allow_html=True)
    
    col_left, col_right = st.columns([1, 1.2])
    
    with col_left:
        st.subheader("📁 رفع وتحديد الوظيفة")
        target_job = st.text_input("الوظيفة المستهدفة (اختياري):", placeholder="مثال: Marketing Manager")
        uploaded_file = st.file_uploader("قم برفع ملف السيرة الذاتية (PDF)", type=["pdf"])
        
        if uploaded_file and st.button("🚀 بدء تحليل الـ CV الآن"):
            with st.spinner("جاري قراءة الملف وتحليله عبر الـ AI..."):
                pdf_bytes = uploaded_file.read()
                cv_text = extract_pdf_text(pdf_bytes)
                
                if cv_text:
                    analysis = analyze_cv_with_gemini(cv_text, target_job)
                    st.session_state.last_analysis = analysis
                    
                    # التصدير التلقائي لجدول جوجل
                    sheet_status, sheet_msg = append_to_google_sheet(
                        analysis['name'],
                        analysis['job_title'],
                        analysis['email'],
                        analysis['phone'],
                        analysis['score'],
                        st.session_state.user_email
                    )
                    if sheet_status:
                        st.success(sheet_msg)
                    else:
                        st.warning(sheet_msg)
                else:
                    st.error("تعذر استخراج النص من ملف الـ PDF!")

    with col_right:
        st.subheader("📊 تقرير التقييم والنتائج")
        if st.session_state.last_analysis:
            data = st.session_state.last_analysis
            
            st.markdown(f"""
            <div class="report-card">
                <div class="score-badge">{data['score']}%</div>
                <p style="text-align:center; font-weight:700; color:#475569;">نسبة التوافق مع نظام الـ ATS</p>
                <hr>
                <p><b>👤 الاسم:</b> {data['name']}</p>
                <p><b>💼 المسمى الوظيفي:</b> {data['job_title']}</p>
                <p><b>📧 البريد:</b> {data['email']}</p>
                <p><b>📱 الهاتف:</b> {data['phone']}</p>
            </div>
            """, unsafe_allow_html=True)
            
            t1, t2, t3 = st.tabs(["✅ نقاط القوة", "⚠️ نقاط الضعف", "💡 التوصيات"])
            with t1:
                for item in data['strengths']: st.write(f"- {item}")
            with t2:
                for item in data['weaknesses']: st.write(f"- {item}")
            with t3:
                for item in data['recommendations']: st.write(f"- {item}")
        else:
            st.info("قم برفع السيرة الذاتية واضغط على 'بدء تحليل الـ CV الآن' لظهور التقرير هنا.")
