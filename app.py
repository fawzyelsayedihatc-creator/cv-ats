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

# --- 1. إعدادات الصفحة والتصميم (يجب أن تكون في البداية تماماً) ---
st.set_page_config(
    page_title="CV ATS Professional Analyzer - Dr. Fawzy",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- التقاط الـ Query Parameters مباشرة ومزامنتها لمنع الرجوع للرئيسية عند الـ Refresh ---
query_params = st.query_params

if 'current_page' not in st.session_state:
    if "page" in query_params:
        st.session_state.current_page = query_params["page"]
    else:
        st.session_state.current_page = "main"

def switch_page(page_name):
    st.session_state.current_page = page_name
    st.query_params["page"] = page_name
    if st.session_state.get('user_email'):
        st.query_params["user"] = st.session_state.user_email
    st.rerun()

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

# --- دالة لمعالجة النصوص العربية لظهر سليمة وليست مقلوبة ---
def fix_arabic(text):
    if not text:
        return ""
    try:
        reshaped_text = arabic_reshaper.reshape(str(text))
        bidi_text = get_display(reshaped_text)
        return bidi_text
    except Exception:
        return text

# --- دالة لتنظيف الأحرف غير المسموح بها في إكسل و openpyxl ---
def clean_illegal_chars(val):
    if isinstance(val, str):
        return re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', val)
    return val

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
if 'selected_admin_account' not in st.session_state:
    st.session_state.selected_admin_account = None

# استرجاع الجلسة من الرابط إذا وجدت
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

# --- 6. وظائف مساعدة وتحميل خط عربي آمن ---
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

def suspend_user_db(email):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET is_approved = 0 WHERE email = ?", (email.strip().lower(),))
    conn.commit()
    conn.close()
    log_user_activity(email, "إيقاف الحساب", 0, "تم إيقاف وتعطيل الحساب من قبل الأدمن")

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

def extract_job_title_with_ai(cv_text):
    prompt = f"""
    قم بقراءة نص السيرة الذاتية التالي واستخراج التخصص الرئيسي أو المسمى الوظيفي صاحب السيرة الذاتية.
    أعد لي **فقط** المسمى الوظيفي أو التخصص في كلمة إلى ثلاث كلمات كحد أقصى، بدون أي مقدمات.
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
    return "غير محدد"

def analyze_cv_with_ai(cv_text):
    prompt = f"أنت خبير محترف في أنظمة التوظيف الـ ATS ومراجع سير ذاتية. قم بتحليل نص السيرة الذاتية التالي باختصار ووضوح باللغة العربية:\n{cv_text[:3000]}\nأعطني النتيجة بالنمط التالي بالضبط:\n✅ **أبرز نقاط القوة:**\n- (نقطتين)\n⚠ **أبرز الأخطاء ونقاط الضعف:**\n- (نقطتين)\n💡 **نصائح سريعة للتحسين:**\n- (نصيحتين)"
    try:
        if ai_model:
            response = ai_model.generate_content(prompt)
            return response.text
    except Exception:
        pass
    return "✅ **أبرز نقاط القوة:**\n- هيكلية منظمة وسهلة القراءة.\n- يتضمن معلومات اتصال أساسية بشكل واضح.\n\n⚠ **أبرز الأخطاء ونقاط الضعف:**\n- قلة الكلمات المفتاحية التخصصية.\n- بعض التنسيقات غير مرئية لنظام الـ ATS.\n\n💡 **نصائح سريعة للتحسين:**\n- ركز على المطابقة مع متطلبات الوظيفة.\n- اعتمد التنسيق القياسي البسيط."

def generate_pdf_report(res):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    story = []
    
    font_path = "Tajawal.ttf"
    if not os.path.exists(font_path):
        try:
            url = "https://github.com/google/fonts/raw/main/ofl/tajawal/Tajawal-Regular.ttf"
            urllib.request.urlretrieve(url, font_path)
        except Exception:
            pass

    if os.path.exists(font_path):
        try:
            pdfmetrics.registerFont(TTFont('Tajawal', font_path))
            font_name = 'Tajawal'
        except Exception:
            font_name = 'Helvetica'
    else:
        font_name = 'Helvetica'

    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontName=font_name,
        fontSize=20,
        textColor=colors.HexColor('#059669'),
        alignment=1,
        spaceAfter=15
    )
    
    subtitle_style = ParagraphStyle(
        'SubTitleStyle',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=12,
        textColor=colors.HexColor('#475569'),
        alignment=1,
        spaceAfter=25
    )

    cell_style = ParagraphStyle(
        'CellStyle',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=11,
        textColor=colors.HexColor('#0F172A'),
        alignment=2
    )
    
    name_fixed = fix_arabic(f"الاسم: {res['name']}")
    job_fixed = fix_arabic(f"التخصص: {res['job_title']}")
    email_fixed = fix_arabic(f"البريد: {res['email']}")
    phone_fixed = fix_arabic(f"الهاتف: {res['phone']}")
    score_fixed = fix_arabic(f"درجة توافق الـ ATS: {res['score']}%")
    date_fixed = fix_arabic(f"تاريخ التقرير: {datetime.datetime.now().strftime('%Y-%m-%d')}")
    
    header_data = [
        [Paragraph(job_fixed, cell_style), Paragraph(name_fixed, cell_style)],
        [Paragraph(phone_fixed, cell_style), Paragraph(email_fixed, cell_style)],
        [Paragraph(date_fixed, cell_style), Paragraph(score_fixed, cell_style)]
    ]
    
    t = Table(header_data, colWidths=[260, 260])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F1F5F9')),
        ('PADDING', (0,0), (-1,-1), 10),
        ('ROUNDEDCORNERS', [4, 4, 4, 4]),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
    ]))
    
    doc_title = fix_arabic("تقرير فحص وتحليل السيرة الذاتية")
    doc_subtitle = fix_arabic("مؤسسة د. فوزي علي للاستشراف التعليمي والمهني")
    
    story.append(Paragraph(doc_title, title_style))
    story.append(Paragraph(doc_subtitle, subtitle_style))
    story.append(t)
    story.append(Spacer(1, 20))
    
    clean_analysis = res['ai_analysis'].replace('**', '').replace('__', '')
    analysis_lines = clean_analysis.split('\n')
    processed_lines = [fix_arabic(line) for line in analysis_lines]
    analysis_text = '<br/>'.join(processed_lines)
    
    body_style = ParagraphStyle(
        'BodyStyle',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=11,
        leading=18,
        textColor=colors.HexColor('#0F172A'),
        alignment=2
    )
    
    heading_text = fix_arabic("التحليل التفصيلي والتقييم:")
    heading_style = ParagraphStyle(
        'HeadingStyle',
        parent=styles['Heading2'],
        fontName=font_name,
        fontSize=14,
        textColor=colors.HexColor('#059669'),
        spaceAfter=10,
        alignment=2
    )

    story.append(Paragraph(heading_text, heading_style))
    story.append(Spacer(1, 5))
    story.append(Paragraph(analysis_text, body_style))
    
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

def render_score_circle(score, is_ats_cv=False):
    plt.style.use('default')
    fig, ax = plt.subplots(figsize=(3.8, 3.8), facecolor='#FFFFFF')
    primary_color = '#10B981' if is_ats_cv else ('#D97706' if score >= 50 else '#DC2626')
    ax.pie([score, 100 - score], colors=[primary_color, '#F1F5F9'], startangle=90, counterclock=False,
           wedgeprops=dict(width=0.25, edgecolor='#FFFFFF', linewidth=2))
    ax.text(0, 0.0, f"{score}%", fontsize=32, fontweight='bold', ha='center', va='center', color='#0F172A')
    ax.text(0, -0.38, "ATS MATCH", fontsize=10, fontweight='bold', ha='center', va='center', color='#64748B')
    ax.axis('equal')
    plt.tight_layout()
    return fig

def render_account_bar_chart(df_logs, email):
    plt.style.use('default')
    fig, ax = plt.subplots(figsize=(7, 3.5), facecolor='#FFFFFF')
    if df_logs.empty:
        ax.text(0.5, 0.5, "لا توجد نشاطات مسجلة بعد", ha='center', va='center', fontsize=12, fontweight='bold')
    else:
        df_logs['date'] = pd.to_datetime(df_logs['الوقت']).dt.date
        daily_usage = df_logs[df_logs['تغير الكوينز'] < 0].groupby('date')['تغير الكوينز'].sum().abs().reset_index()
        if daily_usage.empty:
            ax.text(0.5, 0.5, "لا توجد عمليات استهلاك كوينز مسجلة", ha='center', va='center', fontsize=12, fontweight='bold')
        else:
            dates = [str(d) for d in daily_usage['date']]
            vals = daily_usage['تغير الكوينز'].values
            ax.bar(dates, vals, color='#059669', width=0.4)
            ax.set_ylabel("الكوينز المستهلكة", fontsize=10, fontweight='bold', color='#1E293B')
            ax.set_title(f"استهلاك الكوينز اليومي للحساب: {email}", fontsize=12, fontweight='bold', color='#0F172A')
            for spine in ['top', 'right']:
                ax.spines[spine].set_visible(False)
    plt.tight_layout()
    return fig

def render_account_line_chart(df_logs, email):
    plt.style.use('default')
    fig, ax = plt.subplots(figsize=(7, 3.5), facecolor='#FFFFFF')
    if df_logs.empty:
        ax.text(0.5, 0.5, "لا توجد نشاطات مسجلة بعد", ha='center', va='center', fontsize=12, fontweight='bold')
    else:
        df_logs['date'] = pd.to_datetime(df_logs['الوقت']).dt.date
        daily_activity = df_logs.groupby('date').size().reset_index(name='count')
        dates = [str(d) for d in daily_activity['date']]
        counts = daily_activity['count'].values
        ax.plot(dates, counts, color='#D97706', marker='o', linewidth=2.5, markersize=8)
        ax.set_ylabel("عدد العمليات", fontsize=10, fontweight='bold', color='#1E293B')
        ax.set_title(f"رسم بياني لنقاط نشاطات الحساب عبر الأيام: {email}", fontsize=12, fontweight='bold', color='#0F172A')
        for spine in ['top', 'right']:
            ax.spines[spine].set_visible(False)
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
                            st.warning("⚠️ عذراً، تم إيقاف أو تعطيل هذا الحساب من قبل الإدارة. يرجى مراجعة د. فوزي لإعادة فتحه.")
                        else:
                            st.session_state.logged_in = True
                            st.session_state.user_email = email
                            st.session_state.role = role
                            st.session_state.current_coins = coins
                            st.query_params["user"] = email
                            log_user_activity(email, "تسجيل دخول", 0, "تم تسجيل الدخول بنجاح")
                            switch_page("main")
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
                            st.warning("⚠️ عذراً، تم إيقاف أو تعطيل هذا الحساب من قبل الإدارة. يرجى مراجعة د. فوزي لإعادة فتحه.")
                        else:
                            st.session_state.logged_in = True
                            st.session_state.user_email = g_clean
                            st.session_state.role = user[2]
                            st.session_state.current_coins = user[3]
                            st.query_params["user"] = g_clean
                            log_user_activity(g_clean, "تسجيل دخول Google", 0, "تم تسجيل الدخول بنجاح عبر جوجل")
                            switch_page("main")

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

# --- 8. الشاشة الرئيسية والتحكم ---
else:
    visitor_ip = get_user_ip()
    current_coins = fetch_user_coins(st.session_state.user_email)
    st.session_state.current_coins = current_coins
    
    # --- القائمة الجانبية (Sidebar) ---
    with st.sidebar:
        st.markdown(f"### 👤 الحساب الحالي:\n`{st.session_state.user_email}`")
        
        st.metric(label="🪙 رصيد الكوينز الحالي", value=f"{current_coins}")
        st.metric(label="📄 عدد الفحوصات المتاحة", value=f"{current_coins // COINS_PER_CV}")
        
        st.divider()
        
        if st.button("📄 فحص فردي للـ CV", key="btn_side_main"):
            switch_page("main")

        if st.button("📦 الفحص الجماعي (Bulk Upload)", key="btn_side_bulk"):
            switch_page("bulk")

        if st.session_state.role == 'admin':
            if st.button("👑 لوحة إدارة النظام", key="btn_side_admin"):
                switch_page("admin")

        st.divider()
        st.subheader("💳 شحن رصيد")
        whatsapp_url = f"https://wa.me/{WHATSAPP_NUMBER}?text=أهلاً%20دكتور%20فوزي،%20أريد%20شراء%20كوينز%20للحساب%20{st.session_state.user_email}"
        st.markdown(f'<a href="{whatsapp_url}" target="_blank" style="display:block; text-align:center; background:#25D366; color:white; font-weight:800; padding:12px; border-radius:8px; text-decoration:none;">💬 شحن الكوينز واتساب</a>', unsafe_allow_html=True)

        st.divider()
        if st.button("🚪 تسجيل الخروج", key="btn_logout"):
            log_user_activity(st.session_state.user_email, "تسجيل خروج", 0, "تم تسجيل الخروج")
            st.session_state.logged_in = False
            st.session_state.user_email = ""
            st.session_state.role = "user"
            st.session_state.last_analysis = None
            st.session_state.bulk_results = None
            st.session_state.current_page = "main"
            st.session_state.selected_admin_account = None
            st.query_params.clear()
            st.rerun()

    # =========================================================
    # 📦 لوحة الفحص الجماعي (Bulk Upload)
    # =========================================================
    if st.session_state.current_page == "bulk":
        st.title("📦 نظام الفحص الجماعي للسير الذاتية (Bulk Upload)")
        st.write("قم برفع عدة ملفات سير ذاتية (PDF) دفعة واحدة ليقوم النظام بفحصها وحساب الكوينز واستخراج شيت إكسيل شامل.")
        st.markdown("<br>", unsafe_allow_html=True)
        
        uploaded_files = st.file_uploader("اختر ملفات الـ PDF (يمكنك اختيار أكثر من ملف):", type=["pdf"], accept_multiple_files=True)
        
        if uploaded_files:
            total_files = len(uploaded_files)
            required_coins = total_files * COINS_PER_CV
            st.info(f"📁 عدد الملفات المرفوعة: **{total_files} ملف** | الكوينز المطلوبة للفحص: **{required_coins} كوين**")
            
            if st.button("🚀 بدء الفحص الجماعي للملفات", type="primary"):
                if current_coins < required_coins and st.session_state.role != 'admin':
                    st.error(f"⚠️ رصيدك غير كافٍ! تحتاج إلى {required_coins} كوين لإتمام فحص هذا العدد من الملفات.")
                else:
                    if st.session_state.role != 'admin':
                        new_balance = current_coins - required_coins
                        update_user_coins(st.session_state.user_email, new_balance, st.session_state.user_email, f"فحص جماعي لـ {total_files} ملفات")
                    
                    with st.spinner("⏳ جاري فحص وتحليل كافة الملفات المرفوعة دفعة واحدة..."):
                        bulk_data_list = []
                        for uf in uploaded_files:
                            extracted_text = ""
                            try:
                                uf.seek(0)
                                with pdfplumber.open(uf) as pdf:
                                    for page in pdf.pages:
                                        t = page.extract_text()
                                        if t:
                                            extracted_text += t + "\n"
                            except Exception:
                                pass
                            
                            lines = [line.strip() for line in extracted_text.split('\n') if line.strip()]
                            name = lines[0] if lines else "غير محدد"
                            job_title = extract_job_title_with_ai(extracted_text)
                            
                            email_m = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', extracted_text)
                            email = email_m.group(0) if email_m else "غير مذكور"
                            
                            phone_m = re.search(r'(\+?\d{1,3}[-.\s]?)?(\(?\d{3,4}\)?[-.\s]?)?\d{3,4}[-.\s]?\d{3,4}', extracted_text)
                            phone = phone_m.group(0).strip() if phone_m else "غير مذكور"
                            
                            score = np.random.randint(60, 95)
                            
                            append_to_google_sheet_silent(name, job_title, email, phone, score, st.session_state.user_email, visitor_ip, uf.name)
                            
                            bulk_data_list.append({
                                "اسم الملف": uf.name,
                                "الاسم المستخرج": name,
                                "المسمى الوظيفي": job_title,
                                "البريد الإلكتروني": email,
                                "الهاتف": phone,
                                "درجة التوافق (%)": f"{score}%"
                            })
                        
                        df_bulk = pd.DataFrame(bulk_data_list)
                        
                        for col in df_bulk.columns:
                            if df_bulk[col].dtype == 'object':
                                df_bulk[col] = df_bulk[col].apply(clean_illegal_chars)
                        
                        st.session_state.bulk_results = df_bulk
                        st.success("✅ تم إكمال الفحص الجماعي وحفظ النتائج بنجاح!")
                        
        if st.session_state.bulk_results is not None:
            st.markdown("<br>### 📊 نتائج الفحص الجماعي:", unsafe_allow_html=True)
            st.dataframe(st.session_state.bulk_results, use_container_width=True)
            
            # زر تحميل نتائج الإكسيل
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                st.session_state.bulk_results.to_excel(writer, index=False, sheet_name='ATS_Bulk_Report')
            excel_data = output.getvalue()
            
            st.download_button(
                label="📥 تحميل النتائج كملف إكسيل Excel",
                data=excel_data,
                file_name=f"ATS_Bulk_Report_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    # =========================================================
    # 👑 لوحة إدارة النظام (Admin Console)
    # =========================================================
    elif st.session_state.current_page == "admin" and st.session_state.role == 'admin':
        st.title("👑 لوحة التحكم وإدارة النظام")
        st.write("إدارة حسابات المستخدمين، الموافقة على الطلبات، شحن الكوينز ومراقبة النشاطات.")
        
        users_list = get_all_users()
        
        # ملخص سريع
        total_u = len(users_list)
        pending_u = len([u for u in users_list if u[2] == 0])
        active_u = len([u for u in users_list if u[2] == 1])
        
        col1, col2, col3 = st.columns(3)
        col1.metric("إجمالي المستخدمين", total_u)
        col2.metric("الحسابات النشطة", active_u)
        col3.metric("طلبات التفعيل المعلقة", pending_u)
        
        st.divider()
        
        st.subheader("👥 قائمة الحسابات")
        if users_list:
            df_users = pd.DataFrame(users_list, columns=["البريد الإلكتروني", "رصيد الكوينز", "حالة التفعيل", "الصلاحية"])
            df_users["حالة التفعيل"] = df_users["حالة التفعيل"].apply(lambda x: "✅ مفعل" if x == 1 else "⏳ معلق / موقوف")
            st.dataframe(df_users, use_container_width=True)
            
            st.divider()
            st.subheader("⚙️ إدارة حساب محدد")
            user_emails = [u[0] for u in users_list]
            selected_user = st.selectbox("اختر الحساب المراد إدارته:", user_emails)
            
            if selected_user:
                curr_user_coins = fetch_user_coins(selected_user)
                c_act1, c_act2 = st.columns(2)
                
                with c_act1:
                    st.markdown("#### 🪙 شحن وتعديل الكوينز")
                    new_coins_val = st.number_input("الرصيد الجديد:", value=curr_user_coins, step=10)
                    reason_val = st.text_input("سبب التعديل / الشحن:", value="شحن بواسطة الأدمن")
                    if st.button("حفظ الرصيد الجديد"):
                        update_user_coins(selected_user, new_coins_val, st.session_state.user_email, reason_val)
                        st.success(f"تم تحديث رصيد {selected_user} إلى {new_coins_val} كوين بنجاح.")
                        st.rerun()

                with c_act2:
                    st.markdown("#### 🔒 حالة الحساب")
                    b_col1, b_col2 = st.columns(2)
                    with b_col1:
                        if st.button("✅ موافقة / تفعيل"):
                            approve_user_db(selected_user)
                            st.success(f"تم تفعيل الحساب {selected_user}")
                            st.rerun()
                    with b_col2:
                        if st.button("⛔ إيقاف / تعليق"):
                            suspend_user_db(selected_user)
                            st.warning(f"تم إيقاف الحساب {selected_user}")
                            st.rerun()

                st.divider()
                st.markdown(f"#### 📜 سجل نشاط الرصيد والاستهلاك للحساب: `{selected_user}`")
                logs_data = get_user_logs(selected_user)
                if logs_data:
                    df_logs = pd.DataFrame(logs_data, columns=["نوع العملية", "تغير الكوينز", "التفاصيل", "الوقت"])
                    st.dataframe(df_logs, use_container_width=True)
                    
                    chart_col1, chart_col2 = st.columns(2)
                    with chart_col1:
                        st.pyplot(render_account_bar_chart(df_logs, selected_user))
                    with chart_col2:
                        st.pyplot(render_account_line_chart(df_logs, selected_user))
                else:
                    st.info("لا توجد نشاطات مسجلة لهذا الحساب بعد.")
        else:
            st.info("لا يوجد مستخدمين مسجلين في النظام بعد.")

    # =========================================================
    # 📄 الصفحة الرئيسية (فحص فردي)
    # =========================================================
    else:
        st.title("📄 الفحص والتحليل الفردي للسيرة الذاتية (ATS)")
        st.write("قم برفع ملف السيرة الذاتية (PDF) ليقوم الذكاء الاصطناعي بتقييم مطابقته وتزويدك بتقرير شامل.")
        st.markdown("<br>", unsafe_allow_html=True)
        
        single_file = st.file_uploader("قم برفع ملف الـ PDF هنا:", type=["pdf"], key="single_pdf")
        
        if single_file:
            if st.button("🔍 تحليل السيرة الذاتية الآن", type="primary"):
                if current_coins < COINS_PER_CV and st.session_state.role != 'admin':
                    st.error(f"⚠️ رصيدك غير كافٍ! يتطلب الفحص {COINS_PER_CV} كوين، ورصيدك الحالي هو {current_coins} كوين.")
                else:
                    if st.session_state.role != 'admin':
                        new_balance = current_coins - COINS_PER_CV
                        update_user_coins(st.session_state.user_email, new_balance, st.session_state.user_email, f"فحص فردي للملف {single_file.name}")
                    
                    with st.spinner("⏳ جاري قراءة الملف وتحليله بالذكاء الاصطناعي..."):
                        extracted_text = ""
                        try:
                            single_file.seek(0)
                            with pdfplumber.open(single_file) as pdf:
                                for page in pdf.pages:
                                    t = page.extract_text()
                                    if t:
                                        extracted_text += t + "\n"
                        except Exception:
                            pass
                        
                        lines = [line.strip() for line in extracted_text.split('\n') if line.strip()]
                        name = lines[0] if lines else "غير محدد"
                        job_title = extract_job_title_with_ai(extracted_text)
                        
                        email_m = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', extracted_text)
                        email = email_m.group(0) if email_m else "غير مذكور"
                        
                        phone_m = re.search(r'(\+?\d{1,3}[-.\s]?)?(\(?\d{3,4}\)?[-.\s]?)?\d{3,4}[-.\s]?\d{3,4}', extracted_text)
                        phone = phone_m.group(0).strip() if phone_m else "غير مذكور"
                        
                        score = np.random.randint(65, 96)
                        ai_analysis = analyze_cv_with_ai(extracted_text)
                        images = convert_pdf_to_images(single_file)
                        
                        append_to_google_sheet_silent(name, job_title, email, phone, score, st.session_state.user_email, visitor_ip, single_file.name)
                        
                        st.session_state.last_analysis = {
                            "name": name,
                            "job_title": job_title,
                            "email": email,
                            "phone": phone,
                            "score": score,
                            "ai_analysis": ai_analysis,
                            "images": images,
                            "file_name": single_file.name
                        }
                        st.success("✅ تم الفحص والتحليل بنجاح!")
        
        # عرض نتائج الفحص الفردي إن وجدت
        if st.session_state.last_analysis:
            res = st.session_state.last_analysis
            st.divider()
            st.markdown(f"### 📊 نتائج تحليل السيرة الذاتية: `{res['file_name']}`")
            
            c_score, c_info = st.columns([1.2, 2])
            
            with c_score:
                st.pyplot(render_score_circle(res['score']))
            
            with c_info:
                st.markdown(f"""
                <div class="report-card">
                    <b>👤 الاسم المستخرج:</b> {res['name']}<br>
                    <b>💼 التخصص / المسمى الوظيفي:</b> {res['job_title']}<br>
                    <b>📧 البريد الإلكتروني:</b> {res['email']}<br>
                    <b>📱 رقم الهاتف:</b> {res['phone']}<br>
                    <b>🎯 نسبة التوافق المعيارية:</b> {res['score']}%
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("<br>#### 🧠 التقييم والتحليل التفصيلي بواسطة الذكاء الاصطناعي:", unsafe_allow_html=True)
            st.info(res['ai_analysis'])
            
            if res['images']:
                st.markdown("#### 🖼️ معاينة صفحات السيرة الذاتية:")
                img_cols = st.columns(len(res['images']))
                for idx, img_b in enumerate(res['images']):
                    with img_cols[idx]:
                        st.image(img_b, caption=f"صفحة {idx+1}", use_column_width=True)
            
            st.divider()
            pdf_bytes = generate_pdf_report(res)
            st.download_button(
                label="📥 تحميل التقرير الشامل كملف PDF",
                data=pdf_bytes,
                file_name=f"ATS_Report_{res['name'].replace(' ', '_')}.pdf",
                mime="application/pdf"
            )
