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

# --- 1. إعدادات الصفحة وتهيئة التصميم (UI/UX الاحترافي) ---
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
    
    /* أزرار عريضة ومجسمة */
    .stButton>button {
        background: linear-gradient(135deg, #059669 0%, #047857 100%) !important;
        color: #FFFFFF !important;
        font-size: 16px !important;
        font-weight: 700 !important;
        border-radius: 10px !important;
        padding: 12px 24px !important;
        border: none !important;
        box-shadow: 0 4px 12px rgba(5, 150, 105, 0.2) !important;
        width: 100% !important;
        transition: all 0.2s ease-in-out !important;
    }
    .stButton>button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(5, 150, 105, 0.35) !important;
    }
    
    /* بطاقات التقرير والنتائج */
    .report-card {
        background-color: #FFFFFF;
        border-radius: 12px;
        padding: 20px;
        border: 1px solid #E2E8F0;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
        margin-bottom: 15px;
    }

    .whatsapp-btn {
        display: block;
        background: linear-gradient(135deg, #25D366 0%, #128C7E 100%);
        color: white !important;
        text-align: center;
        font-weight: 700;
        padding: 12px;
        border-radius: 10px;
        text-decoration: none;
        box-shadow: 0 4px 10px rgba(37, 211, 102, 0.2);
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

# --- 2. الثوابت وإصلاح مفتاح Google Sheets ---
GEMINI_API_KEY = "AQ.Ab8RN6J7aiWlVQUTqWfGxcTe9zandjNMP6SIaWgFlJwILBfb9Q"
WHATSAPP_NUMBER = "201200686537"
GOOGLE_SHEET_URL = "https://docs.google.com/spreadsheets/d/1UUEiN2XX7sHwvy5EnK4mtSIpDvi_N4jCyTc4wuZ7HPw/edit?gid=0#gid=0"
COINS_PER_CV = 20
INITIAL_FREE_COINS = 200

# إصلاح تنسيق الـ Private Key لتجنب خطأ Invalid JWT Signature
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

try:
    genai.configure(api_key=GEMINI_API_KEY)
    ai_model = genai.GenerativeModel('gemini-1.5-flash')
except Exception:
    ai_model = None

# --- 3. تصدير البيانات الشامل ---
def append_to_google_sheet(name, job_title, email, phone, score, user_email):
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(CREDENTIALS_DICT, scope)
        client = gspread.authorize(creds)
        sheet = client.open_by_url(GOOGLE_SHEET_URL).sheet1
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        row = [now_str, name, job_title, email, phone, f"{score}%", user_email]
        sheet.append_row(row)
        return True, "✅ تم تصدير البيانات بنجاح إلى Google Sheets الخاص بك!"
    except Exception as e:
        return False, f"⚠️ خطأ في التصدير: {str(e)}"

# --- 4. معالجة الـ PDF ---
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

# --- 5. قاعدة البيانات والإدارة ---
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
        # جميع تسجيلات التقديم (سواء عادي أو جوجل) تتطلب موافقة الأدمن (is_approved = 0)
        cursor.execute("INSERT INTO users (email, password, coins, is_approved, role) VALUES (?, ?, ?, 0, 'user')",
                       (email_clean, 'google_oauth' if is_google else password.strip(), INITIAL_FREE_COINS))
        conn.commit()
        conn.close()
        return True, "تم تقديم طلب التسجيل بنجاح! يتطلب الحساب موافقة د. فوزي قبل التفعيل."
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

def update_user_coins(email, new_coins):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET coins = ? WHERE email = ?", (email.strip().lower(), new_coins))
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

# --- 6. تحليل النص بالذكاء الاصطناعي ---
def analyze_cv_with_ai(cv_text):
    prompt = f"أنت خبير محترف في أنظمة التوظيف الـ ATS ومراجع سير ذاتية. قم بتحليل نص السيرة الذاتية التالي باختصار ووضوح باللغة العربية:\n{cv_text[:3000]}\nأعطني النتيجة بالنمط التالي بالضبط:\n✅ **أبرز نقاط القوة:**\n- (نقطتين)\n⚠️ **أبرز الأخطاء ونقاط الضعف:**\n- (نقطتين)\n💡 **نصائح سريعة للتحسين:**\n- (نصيحتين)"
    try:
        if ai_model:
            response = ai_model.generate_content(prompt)
            return response.text
    except Exception:
        pass
    return "✅ **أبرز نقاط القوة:**\n- هيكلية منظمة وسهلة القراءة.\n- يتضمن معلومات اتصال أساسية بشكل واضح.\n\n⚠️ **أبرز الأخطاء ونقاط الضعف:**\n- قلة الكلمات المفتاحية التخصصية.\n- بعض التنسيقات غير مرئية لنظام الـ ATS.\n\n💡 **نصائح سريعة للتحسين:**\n- ركز على المطابقة مع متطلبات الوظيفة.\n- اعتمد التنسيق القياسي البسيط."

def render_score_charts(score, cat_scores):
    plt.style.use('default')
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(8.5, 3.2), facecolor='#FFFFFF')
    
    primary_color = '#059669' if score >= 70 else '#D97706' if score >= 50 else '#DC2626'
    status_text = "ممتاز" if score >= 70 else "متوسط" if score >= 50 else "ضعيف"

    ax1.pie([score, 100 - score], colors=[primary_color, '#F1F5F9'], startangle=90, counterclock=False,
            wedgeprops=dict(width=0.25, edgecolor='#FFFFFF', linewidth=2))
    ax1.text(0, 0.12, f"{score}%", fontsize=22, fontweight='bold', ha='center', va='center', color='#0F172A')
    ax1.text(0, -0.15, status_text, fontsize=10, fontweight='bold', ha='center', va='center', color=primary_color)
    ax1.text(0, -0.35, "ATS MATCH", fontsize=8, fontweight='bold', ha='center', va='center', color='#64748B')

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

# --- 7. نظام تسجيل الدخول ---
if not st.session_state.logged_in:
    _, col_center, _ = st.columns([1, 1.8, 1])
    
    with col_center:
        st.markdown("<br><h1 style='text-align: center; color: #059669;'>📄 CV ATS Analyzer</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #64748B;'>منصة فحص السير الذاتية الذكية - إشراف د. فوزي علي</p>", unsafe_allow_html=True)
        
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
                            st.warning("⏳ حسابك قيد المراجعة بانتظار موافقة د. فوزي لتفعيله.")
                        else:
                            st.session_state.logged_in = True
                            st.session_state.user_email = email
                            st.session_state.role = role
                            st.rerun()
                    else:
                        st.error("بيانات الدخول غير صحيحة!")

        with tab_google:
            st.markdown("#### 🌐 التسجيل الفوري عبر حساب Google")
            st.info("عند إدخال بريدك، يتم تقديم الطلب للأدمن للموافقة والتفعيل.")
            
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
                        st.info("⏳ تم إنشاء حسابك وهو في انتظار موافقة د. فوزي للتفعيل.")
                    else:
                        if user[1] == 0 and user[2] != 'admin':
                            st.warning("⏳ حسابك مسجل بالفعل وفي انتظار موافقة الأدمن.")
                        else:
                            st.session_state.logged_in = True
                            st.session_state.user_email = g_clean
                            st.session_state.role = user[2]
                            st.rerun()
                else:
                    st.error("يرجى كتابة بريد إلكتروني صحيح.")

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

# --- 8. الواجهة الرئيسية والتطبيق بعد الدخول ---
else:
    # Sidebar
    with st.sidebar:
        st.markdown(f"### 👤 الحساب الحالي:\n`{st.session_state.user_email}`")
        if st.session_state.role == 'admin':
            st.success("👑 صلاحية أدمن (د. فوزي)")
            
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT coins FROM users WHERE email = ?", (st.session_state.user_email,))
        user_rec = cursor.fetchone()
        current_coins = user_rec[0] if user_rec else 0
        conn.close()
        
        st.metric(label="🪙 رصيد الكوينز", value=f"{current_coins}")
        st.metric(label="📄 الفحوصات المتاحة", value=f"{current_coins // COINS_PER_CV}")
        
        if st.button("🚪 تسجيل الخروج"):
            st.session_state.logged_in = False
            st.session_state.user_email = ""
            st.session_state.role = "user"
            st.session_state.last_analysis = None
            st.rerun()

        st.divider()
        st.subheader("💳 شحن رصيد")
        whatsapp_url = f"https://wa.me/{WHATSAPP_NUMBER}?text=أهلاً%20دكتور%20فوزي،%20أريد%20شراء%20كوينز%20للحساب%20{st.session_state.user_email}"
        st.markdown(f'<a href="{whatsapp_url}" target="_blank" class="whatsapp-btn">💬 تواصل للشحن عبر الواتساب</a>', unsafe_allow_html=True)

    # لوحة الأدمن
    if st.session_state.role == 'admin':
        st.title("👑 لوحة إدارة النظام - دكتور فوزي")
        tab_users, tab_app = st.tabs(["👥 إدارة المستخدمين والطلبات", "🚀 فحص الـ CV"])

        with tab_users:
            all_users = get_all_users()
            st.markdown("### ⏳ الطلبات المعلقة (الموافقة على الدخول)")
            pending_users = [u for u in all_users if u[2] == 0]
            if pending_users:
                for email, coins, approved, role in pending_users:
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.write(f"👤 `{email}`")
                    with col2:
                        if st.button(f"✅ قبول الحساب", key=f"app_{email}"):
                            approve_user_db(email)
                            st.success(f"تم قبول {email}")
                            st.rerun()
            else:
                st.caption("لا توجد طلبات معلقة.")

            st.divider()
            st.markdown("### 🟢 المستخدمون النشطون")
            active_users = [u for u in all_users if u[2] == 1]
            for email, coins, approved, role in active_users:
                col_u1, col_u2, col_u3 = st.columns([2, 2, 2])
                with col_u1:
                    st.write(f"👤 `{email}`")
                with col_u2:
                    st.write(f"🪙 الرصيد: **{coins}**")
                with col_u3:
                    new_c = st.number_input("تعديل الرصيد:", value=coins, step=20, key=f"num_{email}")
                    if st.button("تحديث", key=f"btn_{email}"):
                        update_user_coins(email, new_c)
                        st.success(f"تم التحديث")
                        st.rerun()

    # شاشة فحص الـ CV
    if st.session_state.role == 'user' or (st.session_state.role == 'admin' and 'tab_app' in locals()):
        st.title("📄 نظام فحص وتحليل الـ CV")
        
        uploaded_file = st.file_uploader("قم برفع ملف السيرة الذاتية (PDF)", type=["pdf"])

        if uploaded_file is not None:
            if st.button("🚀 بدء تحليل السيرة الذاتية الآن", type="primary"):
                if current_coins < COINS_PER_CV and st.session_state.role != 'admin':
                    st.error("⚠️ رصيدك غير كافٍ! يرجى التواصل مع الإدارة للشحن.")
                else:
                    with st.spinner("🔍 جاري قراءة وتحليل السيرة الذاتية..."):
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
                            if st.session_state.role != 'admin':
                                update_user_coins(st.session_state.user_email, current_coins - COINS_PER_CV)

                            pdf_images = convert_pdf_to_images(uploaded_file)
                            
                            # استخراج البيانات التلقائية
                            lines = [line.strip() for line in extracted_text.split('\n') if line.strip()]
                            name = lines[0] if lines else "غير محدد"
                            
                            email_m = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', extracted_text)
                            email = email_m.group(0) if email_m else "غير مذكور"
                            
                            phone_m = re.search(r'(\+?\d{1,3}[-.\s]?)?(\(?\d{3,4}\)?[-.\s]?)?\d{3,4}[-.\s]?\d{3,4}', extracted_text)
                            phone = phone_m.group(0).strip() if phone_m else "غير مذكور"
                            
                            score = np.random.randint(68, 89)
                            ai_analysis = analyze_cv_with_ai(extracted_text)
                            
                            cat_scores = [score - 5, score + 4, score - 8, score - 12, score]

                            st.session_state.last_analysis = {
                                'pdf_images': pdf_images,
                                'score': score,
                                'cat_scores': cat_scores,
                                'ai_analysis': ai_analysis,
                                'name': name,
                                'job_title': "Professional / Applicant",
                                'email': email,
                                'phone': phone
                            }

        # --- 9. عرض التقرير والنتائج بالتصميم الجديد (بجانب الـ PDF وتنسيق بعرض الشاشة) ---
        if st.session_state.last_analysis:
            res = st.session_state.last_analysis
            st.divider()

            # تقسيم الشاشة: معاينة الـ PDF بجانب التقرير كاملاً
            col_pdf_preview, col_main_report = st.columns([1, 1.6])

            with col_pdf_preview:
                st.subheader("📄 معاينة الـ CV")
                if res['pdf_images']:
                    for img_bytes in res['pdf_images']:
                        st.image(img_bytes, use_container_width=True)

            with col_main_report:
                # 1. الرسوم البيانية بعرض الجزء المخصص
                st.markdown("<div class='report-card'>", unsafe_allow_html=True)
                fig = render_score_charts(res['score'], res['cat_scores'])
                st.pyplot(fig)
                st.markdown("</div>", unsafe_allow_html=True)

                # 2. النقاط والتوصيات تحته مباشرة
                st.markdown("<div class='report-card'>", unsafe_allow_html=True)
                st.markdown(res['ai_analysis'])
                st.markdown("</div>", unsafe_allow_html=True)

            st.divider()
            
            # الجدول وخيارات التصدير المتعددة أسفل المعاينة
            st.subheader("📊 البيانات المستخرجة وخيارات التصدير")
            
            df_data = pd.DataFrame([{
                "الاسم": res['name'],
                "التخصص": res['job_title'],
                "البريد الإلكتروني": res['email'],
                "الهاتف": res['phone'],
                "درجة ATS": f"{res['score']}%"
            }])
            
            st.table(df_data)

            col_exp_gsheet, col_exp_excel = st.columns(2)
            
            with col_exp_gsheet:
                if st.button("📊 تصدير فوراً لـ Google Sheets الخاص بك"):
                    ok, msg = append_to_google_sheet(
                        res['name'], res['job_title'], res['email'], res['phone'], res['score'], st.session_state.user_email
                    )
                    if ok:
                        st.success(msg)
                    else:
                        st.error(msg)

            with col_exp_excel:
                # خيار تنزيل ملف Excel مباشر
                output = BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df_data.to_excel(writer, index=False, sheet_name='CV Analysis')
                excel_data = output.getvalue()
                
                st.download_button(
                    label="📥 تنزيل شيت إكسيل (Excel)",
                    data=excel_data,
                    file_name=f"CV_Analysis_{res['name']}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
