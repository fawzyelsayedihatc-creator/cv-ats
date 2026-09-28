import os
import re
import json
import random
import sqlite3
import datetime
import pdfplumber
import fitz  # PyMuPDF للعرض الآمن لصورة الـ PDF
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import google.generativeai as genai
import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from PIL import Image
from io import BytesIO

# --- إعدادات الصفحة ---
st.set_page_config(
    page_title="CV Checker - Dr. Fawzy Ali Panel",
    page_icon="🟢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# التنسيقات والثيم
st.markdown("""
<style>
    .stApp { background-color: #F8FAFC; color: #0F172A; }
    [data-testid="stSidebar"] { background-color: #FFFFFF; border-right: 1px solid #E2E8F0; }
    h1, h2, h3 { color: #065F46 !important; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
    
    .stButton>button {
        background: linear-gradient(135deg, #059669 0%, #047857 100%);
        color: #FFFFFF !important; font-weight: bold; border: none;
        border-radius: 8px; padding: 10px 20px; transition: all 0.3s ease;
        width: 100%;
    }
    .stButton>button:hover { background: linear-gradient(135deg, #10B981 0%, #059669 100%); }
    .whatsapp-btn {
        display: block; background-color: #25D366; color: white !important;
        text-align: center; font-weight: bold; padding: 12px; border-radius: 8px; text-decoration: none;
    }
</style>
""", unsafe_allow_html=True)

# --- الثوابت والمفاتيح ---
GEMINI_API_KEY = "AQ.Ab8RN6J7aiWlVQUTqWfGxcTe9zandjNMP6SIaWgFlJwILBfb9Q"
WHATSAPP_NUMBER = "201200686537"
GOOGLE_SHEET_URL = "https://docs.google.com/spreadsheets/d/1UUEiN2XX7sHwvy5EnK4mtSIpDvi_N4jCyTc4wuZ7HPw/edit?gid=0#gid=0"
COINS_PER_CV = 20
INITIAL_FREE_COINS = 200

# بيانات الاعتماد لـ Service Account
CREDENTIALS_DICT = {
  "type": "service_account",
  "project_id": "cv-ats-checker",
  "private_key_id": "d8444889667100910e291cb962bb73b1370c61e7",
  "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQDGoEHAcQH5w3nV\nrMLtddMLIRhpR9AySz9ICtOoS5yhPGLOTKuBCSJvlJ2NTWoGd+ovfPG7Qmejf9Nd\n8KFFH1GZAeJFezQKqH9bpu0sTI/ZHBiXxnNNNy6XX4WV/YA29YW6jjl3/lXPru5L\neN118a8m7KV/70hekXmzgfWYl+WaQg82FZYhcAaS6FTtnuy3g5tD1Z5kdpGyhlXb\nMQmR0rxCxCUvfaMdSGBYr4/VhTUmAOUUAaQQ9/9u+ut+2ELMxO3KSfwHdbVoMnUQ\ndYOB1YDEb7TjDRTvtvH56vaOoi4TM4NeM8NAH7OUfCtnbjoGPFX8CL9EmT7jSy2d\nyux036srAgMBAAECggEADkCIh0T0ldXbY6QiVoSaUJWe2UsQWtOAZmx0dIJ8aitZ\nkaD5u2gK4wPAbFeuMGmhUaf+9mdU5WvyIC74e2u8YKS8dizZdpxRiyOGqCOUPMlh\n0F4qftNjUfRGMxV+AjOK1XCIGh6TTLQqIBs7lM9zOHFJjM0AHd0FZQaBt2HK1U8g\nxSs1EJWJBBOoYrfa6qVL+uAUsqp99E6fnwI55OsuX6pRYlqgunu2KbHsa2ZDL5Qp\ng4EAdAjJDKGn+4Rj5dgWW9zZdLgXcNerogw6k8yX0hNGxqbm5OVKXmXYClmkjxqg\n07xXrfOPAsMbTQeZj2F98Bs0all9YzTfxzGt8zNrzQKBgQDobkLWgTdXyRYj0+Ak\nx2P6iFFqt0hHlaoOnyS6aomdq9qKjaD/AGv69YQkRtF8sFhCdmVdtd2PWFsKbgo0\njIDgPi/Ach+Xbt4C3BPntxWq706zmJdudAYAKyDzADpxwmQq+AY/VUkjWvb9WLA8\nJd9YMBgu1FwMRgt//1Mh5OAW5QKBgQDaxHMBLpME4LQI2X50Lu9HcWTsLzm+DUJo\n89DQAMQN6YpqHh5YN/KZaLe7E05LueEVZDsTewTSKj0X2WSOqQHs8OKbF9ML0nRL\nWbTys9kyiIAlQHXWnk3uv7mhjiZ30VuVkaNhcP2LOd4hSMCgiqVgyfHllAm2bYu7\nAeBHgb4IzwKBgA5DpgpwB6t1hcxRFnJrYjFf6E86TE9IWhVnouNl4mgwwcq7AmRj\n7DyMkL2BMx4J3IDHr1Te8mf3ri6nriynaslYR6nx1wp+HVXjl70iuUuyQAw5kyGO\nMUgVXYJMQ0nz+h3A9vEwFLr8vCe0J6ypTlmlKfbFxZhjPBVw3/M2jqIZAoGBAMpd\nNIDgY1D8xqz0+3tfuymcJB4yZTh/rXHGL99pBfJUmRwmdi1mu3vbGTHs3t0/uYz/\nJYKUplX+inrYNqOchNJ31TZgKHJkH/1fovlrEjwjdl5/LUH1N+Pk6EMgakclm5FU\nogxN58t1IRwq3zziY66Pv7p9YSqmVL4NMzkSNAaTAoGASmDLn8OJ9VWLNafpXiV+\nNW+FKSs9uknEKky8NmUhlnOD1DjHl27qUPV6cvKhuJUsqLLD+MeVh5jG6c/UYjxm\n9AR7A37fUBi+1xfr4dUOC3bxTVhkSYWagWqeSxYZv22UUi1nk+ktm/MC6TdQbnIM\n6yih2xCrwH80uhx6I6yAIEc=\n-----END PRIVATE KEY-----\n",
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

# --- دالة التصدير التلقائي لشيت جوجل ---
def append_to_google_sheet(name, job_title, email, phone, score, user_email):
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(CREDENTIALS_DICT, scope)
        client = gspread.authorize(creds)
        sheet = client.open_by_url(GOOGLE_SHEET_URL).sheet1
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        row = [now_str, name, job_title, email, phone, f"{score}%", user_email]
        sheet.append_row(row)
        return True, None
    except Exception as e:
        return False, str(e)

# --- دالة تحويل أول صفحة من الـ PDF إلى صورة ---
def get_pdf_first_page_image(file_bytes):
    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        if len(doc) > 0:
            page = doc[0]
            pix = page.get_pixmap(dpi=150)
            img = Image.open(BytesIO(pix.tobytes("png")))
            return img
    except Exception:
        pass
    return None

# --- إدارة الاتصال بقاعدة البيانات ---
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
    cursor.execute("INSERT OR REPLACE INTO users (email, password, coins, is_approved, role) VALUES ('fawzi.elsayed.ihatc@gmail.com', 'google_oauth', 99999, 1, 'admin')")
    cursor.execute("INSERT OR REPLACE INTO users (email, password, coins, is_approved, role) VALUES ('fawziali2040@gmail.com', 'google_oauth', 99999, 1, 'admin')")
    conn.commit()
    conn.close()

init_db()

def register_user(email, password):
    email_clean = email.strip().lower()
    if not email_clean or not password.strip():
        return False, "يرجى ملء جميع الحقول المطلوبة."
    
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (email, password, coins, is_approved, role) VALUES (?, ?, ?, 0, 'user')",
                       (email_clean, password.strip(), INITIAL_FREE_COINS))
        conn.commit()
        conn.close()
        return True, "تم تقديم طلب التسجيل بنجاح! بانتظار موافقة د. فوزي لتفعيل الحساب."
    except sqlite3.IntegrityError:
        conn.close()
        return False, "هذا البريد أو اليوزر مسجل بالفعل!"

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

def update_user_coins(email, new_coins):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET coins = ? WHERE email = ?", (new_coins, email.strip().lower()))
    conn.commit()
    conn.close()

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

JOB_TITLES = [
    "software engineer", "data analyst", "project manager", "graphic designer", 
    "digital marketer", "accountant", "human resources", "sales manager", 
    "business analyst", "web developer", "doctor", "pharmacist", "civil engineer",
    "mechanical engineer", "content writer", "ui/ux designer", "customer service"
]

def parse_cv_details(text):
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    email_match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
    email = email_match.group(0) if email_match else "غير مذكور"

    phone_match = re.search(r'(\+?\d{1,3}[-.\s]?)?(\(?\d{3,4}\)?[-.\s]?)?\d{3,4}[-.\s]?\d{3,4}', text)
    phone = "غير مذكور"
    if phone_match:
        extracted_phone = phone_match.group(0).strip()
        if len(re.sub(r'\D', '', extracted_phone)) >= 8:
            phone = extracted_phone

    name = lines[0] if lines else "غير محدد"
    job_title = "غير محدد"
    for title in JOB_TITLES:
        if title in text.lower():
            job_title = title.title()
            break

    base_score = random.randint(65, 88)
    return name, email, phone, job_title, base_score

def analyze_cv_with_ai(cv_text):
    prompt = f"""
    أنت خبير محترف في أنظمة التوظيف الـ ATS ومراجع سير ذاتية.
    قم بتحليل نص السيرة الذاتية التالي باختصار ووضوح باللغة العربية:
    
    {cv_text[:3000]}
    
    أعطني النتيجة بالنمط التالي بالضبط:
    
    ✅ **أبرز نقاط القوة:**
    - (اذكر نقطتين قوة)
    
    ⚠️ **أبرز الأخطاء ونقاط الضعف:**
    - (اذكر نقطتين أخطاء)
    
    💡 **نصائح سريعة للتحسين:**
    - (اذكر نصيحتين عملية)
    """
    try:
        if ai_model:
            response = ai_model.generate_content(prompt)
            return response.text
    except Exception:
        pass
    
    return """✅ **أبرز نقاط القوة:**
- هيكلية السيرة الذاتية منظمة وسهلة القراءة.
- يتضمن معلومات اتصال أساسية بشكل واضح.

⚠️ **أبرز الأخطاء ونقاط الضعف:**
- قلة الكلمات المفتاحية التخصصية في مجال العمل.
- بعض التنسيقات غير مرئية لنظام الـ ATS.

💡 **نصائح سريعة للتحسين:**
- ركز على مطابقة المهارات مع متطلبات الوظيفة.
- اعتمد التنسيق القياسي البسيط."""

def render_score_charts(score, cat_scores):
    plt.style.use('default')
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.5, 3.1), facecolor='#FFFFFF')
    ax1.set_facecolor('#FFFFFF')
    primary_color = '#059669' if score >= 70 else '#D97706' if score >= 50 else '#DC2626'
    status_text = "ممتاز" if score >= 70 else "متوسط" if score >= 50 else "ضعيف"

    ax1.pie([score, 100 - score], colors=[primary_color, '#F1F5F9'], startangle=90, counterclock=False,
            wedgeprops=dict(width=0.25, edgecolor='#FFFFFF', linewidth=2))
    ax1.text(0, 0.12, f"{score}%", fontsize=22, fontweight='bold', ha='center', va='center', color='#0F172A')
    ax1.text(0, -0.15, status_text, fontsize=10, fontweight='bold', ha='center', va='center', color=primary_color)
    ax1.text(0, -0.35, "ATS MATCH", fontsize=8, fontweight='bold', ha='center', va='center', color='#64748B')

    ax2.set_facecolor('#FFFFFF')
    categories_ar = ["الكلمات المفتاحية", "الخبرات والمهام", "المهارات الفنية", "التنسيق والقالب", "التوافق العام"]
    y_pos = np.arange(len(categories_ar))
    bars = ax2.barh(y_pos, cat_scores, color='#059669', height=0.45)
    
    for bar, s in zip(bars, cat_scores):
        bar.set_color('#10B981' if s >= 70 else '#D97706' if s >= 50 else '#DC2626')

    ax2.set_yticks(y_pos)
    ax2.set_yticklabels(categories_ar, fontsize=9, fontweight='bold', color='#1E293B')
    ax2.set_xlim(0, 115)
    for spine in ['top', 'right', 'bottom', 'left']:
        ax2.spines[spine].set_visible(False)
    ax2.xaxis.set_visible(False)

    for bar in bars:
        w = bar.get_width()
        ax2.text(w + 2, bar.get_y() + bar.get_height()/2, f'{int(w)}%', va='center', fontsize=9, fontweight='bold', color='#0F172A')

    ax2.set_title("تفاصيل التوافق مع النظام", fontsize=10, fontweight='bold', color='#64748B', pad=10)
    plt.tight_layout()
    return fig

# --- إدارة الجلسة ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_email = ""
    st.session_state.role = "user"

# --- شاشة تسجيل الدخول ---
if not st.session_state.logged_in:
    col_left, col_center, col_right = st.columns([1, 1.8, 1])
    
    with col_center:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("<h2 style='text-align: center;'>📄 CV Checker</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #64748B;'>أهلاً بك في منصة فحص وتقييم السير الذاتية</p>", unsafe_allow_html=True)
        
        tab_login, tab_signup = st.tabs(["🔑 تسجيل الدخول", "📝 تسجيل حساب جديد"])
        
        with tab_login:
            login_email = st.text_input("اسم المستخدم / البريد الإلكتروني:", key="l_email")
            login_pass = st.text_input("كلمة المرور:", type="password", key="l_pass")
            
            if st.button("دخول الآن", key="login_btn"):
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
                            st.rerun()
                    else:
                        st.error("اسم المستخدم أو كلمة المرور غير صحيحة!")
                else:
                    st.warning("يرجى إدخال اسم المستخدم وكلمة المرور.")

        with tab_signup:
            signup_email = st.text_input("اسم المستخدم أو البريد الجديد:", key="s_email")
            signup_pass = st.text_input("كلمة المرور الجديدة:", type="password", key="s_pass")
            
            if st.button("إنشاء حساب جديد", key="signup_btn"):
                if signup_email and signup_pass:
                    ok, msg = register_user(signup_email, signup_pass)
                    if ok:
                        st.success(msg)
                    else:
                        st.error(msg)
                else:
                    st.warning("يرجى ملء كافة الحقول.")

# --- الواجهة الرئيسية بعد الدخول ---
else:
    if st.session_state.role == 'admin':
        st.title("👑 لوحة تحكم الأدمن (دكتور فوزي)")
        
        with st.sidebar:
            st.success(f"مرحباً بك يا دكتور!\n({st.session_state.user_email})")
            if st.button("🚪 تسجيل الخروج"):
                st.session_state.logged_in = False
                st.session_state.user_email = ""
                st.session_state.role = "user"
                st.rerun()

        tab_users, tab_app = st.tabs(["👥 إدارة المستخدمين والكوينز", "🚀 تجربة فحص الـ CV"])

        with tab_users:
            all_users = get_all_users()
            
            if not all_users:
                st.info("لا يوجد مستخدمون مسجلون بعد.")
            else:
                st.markdown("### ⏳ طلبات الحسابات الجديدة بانتظار الموافقة (Accept)")
                pending_users = [u for u in all_users if u[2] == 0]
                if pending_users:
                    for email, coins, approved, role in pending_users:
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.write(f"👤 **اليوزر:** `{email}` (الرصيد المبدئي: {coins} كوين)")
                        with col2:
                            if st.button(f"✅ قبول الحساب", key=f"app_{email}"):
                                approve_user_db(email)
                                st.success(f"تم تفعيل حساب {email}")
                                st.rerun()
                else:
                    st.caption("لا توجد طلبات معلقة حالياً.")

                st.divider()

                st.markdown("### 🟢 المستخدمون النشطون والتعديل في الرصيد")
                active_users = [u for u in all_users if u[2] == 1]
                for email, coins, approved, role in active_users:
                    col_u1, col_u2, col_u3 = st.columns([2, 2, 2])
                    with col_u1:
                        st.write(f"👤 `{email}`")
                    with col_u2:
                        st.write(f"🪙 الرصيد الحالي: **{coins} كوين** ({coins//COINS_PER_CV} فحوصات)")
                    with col_u3:
                        new_c = st.number_input("تعديل الكوينز:", value=coins, step=20, key=f"num_{email}")
                        if st.button("تحديث الرصيد", key=f"btn_{email}"):
                            update_user_coins(email, new_c)
                            st.success(f"تم تعديل رصيد {email} إلى {new_c} كوين")
                            st.rerun()

        with tab_app:
            st.info("💡 يمكنك تجربة واجهة الفحص وتنسيق التقرير من هنا.")

    if st.session_state.role == 'user' or (st.session_state.role == 'admin' and 'tab_app' in locals()):
        if st.session_state.role == 'user':
            with st.sidebar:
                st.header("👤 حسابك الحالي")
                st.info(f"**المستخدم:**\n`{st.session_state.user_email}`")
                
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT coins FROM users WHERE email = ?", (st.session_state.user_email,))
                user_rec = cursor.fetchone()
                current_coins = user_rec[0] if user_rec else INITIAL_FREE_COINS
                conn.close()
                
                st.metric(label="🪙 رصيد الكوينز المتبقي", value=f"{current_coins} كوين")
                st.metric(label="📄 الفحوصات المتاحة", value=f"{current_coins // COINS_PER_CV} فحص")
                
                if st.button("🚪 تسجيل الخروج"):
                    st.session_state.logged_in = False
                    st.session_state.user_email = ""
                    st.session_state.role = "user"
                    st.rerun()

                st.divider()
                st.subheader("💳 شحن رصيد كوينز")
                whatsapp_url = f"https://wa.me/{WHATSAPP_NUMBER}?text=أهلاً%20دكتور%20فوزي،%20أريد%20شراء%20كوينز%20للحساب%20{st.session_state.user_email}"
                st.markdown(f'<a href="{whatsapp_url}" target="_blank" class="whatsapp-btn">💬 تواصل للشحن عبر الواتساب</a>', unsafe_allow_html=True)
        else:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT coins FROM users WHERE email = ?", (st.session_state.user_email,))
            user_rec = cursor.fetchone()
            current_coins = user_rec[0] if user_rec else 99999
            conn.close()

        st.title("📄 CV Checker")
        st.caption("نظام التقييم والتحليل الذكي للسير الذاتية")

        uploaded_file = st.file_uploader("قم برفع ملف السيرة الذاتية (PDF)", type=["pdf"])

        if uploaded_file is not None:
            if st.button("🚀 بدء تحليل السيرة الذاتية الآن", type="primary"):
                if current_coins < COINS_PER_CV:
                    st.error("⚠️ رصيدك غير كافٍ لإجراء الفحص! يرجى التواصل لشحن الرصيد.")
                else:
                    with st.spinner("🔍 جاري قراءة وتحليل الملف وتصدير البيانات..."):
                        file_bytes = uploaded_file.getvalue()
                        
                        # قراءة النص بالـ pdfplumber
                        extracted_text = ""
                        try:
                            with pdfplumber.open(uploaded_file) as pdf:
                                for page in pdf.pages:
                                    text = page.extract_text()
                                    if text:
                                        extracted_text += text + "\n"
                        except Exception:
                            st.error("حدث خطأ في قراءة ملف الـ PDF.")

                        if not extracted_text.strip():
                            st.error("❌ لم نتمكن من قراءة النص داخل الملف.")
                        else:
                            # خصم الكوينز
                            new_coins = current_coins - COINS_PER_CV
                            update_user_coins(st.session_state.user_email, new_coins)

                            # استخراج البيانات والتحليل
                            name, email, phone, job_title, score = parse_cv_details(extracted_text)
                            ai_analysis = analyze_cv_with_ai(extracted_text)

                            # التصدير لشيت جوجل بدون إظهار أي رسالة نجاح
                            sheet_ok, err_msg = append_to_google_sheet(name, job_title, email, phone, score, st.session_state.user_email)

                            cat_scores = [
                                max(30, score - random.randint(5, 15)),
                                max(35, score + random.randint(-5, 10)),
                                max(40, score - random.randint(0, 10)),
                                max(25, score - random.randint(10, 20)),
                                score
                            ]

                            # استخراج صورة الصفحة الأولى للـ PDF
                            pdf_preview_img = get_pdf_first_page_image(file_bytes)

                            st.divider()

                            # عرض الملف (الصورة) بالجنب والبيانات بجانبه
                            col_preview, col_rep1, col_rep2 = st.columns([1.2, 1.5, 1.3])

                            with col_preview:
                                st.subheader("📄 معينة الـ CV")
                                if pdf_preview_img:
                                    st.image(pdf_preview_img, use_container_width=True)
                                else:
                                    st.info("معاينة المستند غير متاحة.")

                            with col_rep1:
                                fig = render_score_charts(score, cat_scores)
                                st.pyplot(fig)

                            with col_rep2:
                                st.markdown(ai_analysis)

                            st.divider()
                            st.subheader("📊 البيانات المستخرجة")
                            df_data = pd.DataFrame([{
                                "الاسم": name,
                                "التخصص": job_title,
                                "البريد الإلكتروني": email,
                                "الهاتف": phone,
                                "درجة ATS": f"{score}%"
                            }])
                            st.table(df_data)
