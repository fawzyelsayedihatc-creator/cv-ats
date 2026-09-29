import os
import re
import json
import sqlite3
import datetime
import urllib.request
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
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import arabic_reshaper
from bidi.algorithm import get_display

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

def fix_arabic(text):
    try:
        reshaped = arabic_reshaper.reshape(text)
        return get_display(reshaped)
    except Exception:
        return text

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
    except Exception:
        return False

# --- 4. قاعدة البيانات المحلية وسجلات النشاط ---
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
if not st.session_state.logged_in and "user" in st.query_params:
    saved_user = st.query_params["user"]
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

# --- 6. الوظائف المساعدة ---
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
        'TitleStyle', parent=styles['Heading1'], fontName=font_name, fontSize=20,
        textColor=colors.HexColor('#059669'), alignment=1, spaceAfter=15
    )
    subtitle_style = ParagraphStyle(
        'SubTitleStyle', parent=styles['Normal'], fontName=font_name, fontSize=12,
        textColor=colors.HexColor('#475569'), alignment=1, spaceAfter=25
    )
    cell_style = ParagraphStyle(
        'CellStyle', parent=styles['Normal'], fontName=font_name, fontSize=11,
        textColor=colors.HexColor('#0F172A'), alignment=2
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
        'BodyStyle', parent=styles['Normal'], fontName=font_name, fontSize=11,
        leading=18, textColor=colors.HexColor('#0F172A'), alignment=2
    )
    heading_text = fix_arabic("التحليل التفصيلي والتقييم:")
    heading_style = ParagraphStyle(
        'HeadingStyle', parent=styles['Heading2'], fontName=font_name, fontSize=14,
        textColor=colors.HexColor('#059669'), spaceAfter=10, alignment=2
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
    if is_ats_cv:
        primary_color = '#10B981'
        status_text = "ممتاز"
    else:
        primary_color = '#D97706' if score >= 50 else '#DC2626'
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

def render_account_bar_chart(df_logs, email):
    plt.style.use('default')
    fig, ax = plt.subplots(figsize=(7, 3.5), facecolor='#FFFFFF')
    if df_logs.empty:
        ax.text(0.5, 0.5, "لا توجد نشاطات مسجلة بعد", ha='center', va='center', fontsize=12, fontweight='bold')
    else:
        df_logs['date'] = pd.to_datetime(df_logs['timestamp']).dt.date
        daily_usage = df_logs[df_logs['coins_change'] < 0].groupby('date')['coins_change'].sum().abs().reset_index()
        if daily_usage.empty:
            ax.text(0.5, 0.5, "لا توجد عمليات استهلاك كوينز مسجلة", ha='center', va='center', fontsize=12, fontweight='bold')
        else:
            dates = [str(d) for d in daily_usage['date']]
            vals = daily_usage['coins_change'].values
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
        df_logs['date'] = pd.to_datetime(df_logs['timestamp']).dt.date
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
                            st.warning("⏳ حسابك قيد المراجعة بانتظار موافقة د. فوزي لتفعيله.")
                        else:
                            st.session_state.logged_in = True
                            st.session_state.user_email = email
                            st.session_state.role = role
                            st.session_state.current_coins = coins
                            st.session_state.selected_admin_account = None
                            st.query_params["user"] = email
                            log_user_activity(email, "تسجيل دخول", 0, "تم تسجيل الدخول بنجاح")
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
                        st.info("تم تقديم طلب التسجيل بنجاح! بانتظار تفعيل الحساب من د. فوزي.")
                    else:
                        if user[1] == 1 or user[2] == 'admin':
                            st.session_state.logged_in = True
                            st.session_state.user_email = user[0]
                            st.session_state.role = user[2]
                            st.session_state.current_coins = user[3]
                            st.session_state.selected_admin_account = None
                            st.query_params["user"] = user[0]
                            log_user_activity(user[0], "دخول بـ Google", 0, "تسجيل دخول ناجح بـ Google")
                            st.rerun()
                        else:
                            st.warning("⏳ حسابك قيد المراجعة بانتظار موافقة د. فوزي.")

        with tab_signup:
            st.markdown("<br>", unsafe_allow_html=True)
            reg_email = st.text_input("البريد الإلكتروني:", key="r_email")
            reg_pass = st.text_input("كلمة المرور الجديدة:", type="password", key="r_pass")
            if st.button("إنشاء حساب جديد", key="signup_btn"):
                if reg_email and reg_pass:
                    ok, msg = register_user(reg_email, reg_pass)
                    if ok:
                        st.success(msg)
                    else:
                        st.error(msg)

# --- 8. التطبيق الرئيسي ولوحة التحكم (بعد تسجيل الدخول) ---
else:
    st.session_state.current_coins = fetch_user_coins(st.session_state.user_email)
    
    # القائمة الجانبية
    with st.sidebar:
        st.markdown(f"### 👤 مرحبا بك: {st.session_state.user_email}")
        if st.session_state.role != 'admin':
            st.metric(label="🪙 رصيد الكوينز الخاص بك", value=f"{st.session_state.current_coins} كوينز")
        else:
            st.info("👑 حساب مسؤول النظام (الأدمن)")
            
        st.markdown("---")
        
        if st.session_state.role == 'admin':
            nav_choice = st.radio("القائمة:", ["🔍 فحص وحساب السيرة الذاتية", "👑 لوحة تحكم الأدمن"])
        else:
            nav_choice = "🔍 فحص وحساب السيرة الذاتية"
            
        st.markdown("---")
        if st.button("🚪 تسجيل الخروج"):
            st.session_state.logged_in = False
            st.session_state.user_email = ""
            st.session_state.role = "user"
            st.query_params.clear()
            st.rerun()

    # --- لوحة الأدمن ---
    if nav_choice == "👑 لوحة تحكم الأدمن" and st.session_state.role == 'admin':
        st.title("👑 لوحة إدارية - د. فوزي علي")
        st.markdown("إدارة الحسابات، طلبات التفعيل، وتخصيص الكوينز")
        st.markdown("---")
        
        users = get_all_users()
        if not users:
            st.info("لا يوجد مستخدمون حالياً في النظام.")
        else:
            users_df = pd.DataFrame(users, columns=["البريد الإلكتروني", "الكوينز الحالي", "حالة التفعيل", "الرتبة"])
            users_df["حالة التفعيل"] = users_df["حالة التفعيل"].apply(lambda x: "مفعل ✅" if x == 1 else "معطل / قيد الانتظار ⏳")
            st.dataframe(users_df, use_container_width=True)
            
            st.markdown("### ⚙ التحكم بالحسابات")
            selected_user = st.selectbox("اختر الحساب المراد إدارته:", [u[0] for u in users])
            
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT coins, is_approved FROM users WHERE email = ?", (selected_user,))
            u_info = cursor.fetchone()
            conn.close()
            
            if u_info:
                curr_c, is_app = u_info
                col_a, col_b = st.columns(2)
                with col_a:
                    st.write(f"**حالة التفعيل الحالية:** {'مفعل ✅' if is_app == 1 else 'غير مفعل ⏳'}")
                    if is_app == 0:
                        if st.button(f"✅ تفعيل حساب {selected_user}"):
                            approve_user_db(selected_user)
                            st.success(f"تم تفعيل الحساب {selected_user} بنجاح!")
                            st.rerun()
                    else:
                        if st.button(f"🚫 إيقاف حساب {selected_user}"):
                            suspend_user_db(selected_user)
                            st.warning(f"تم إيقاف الحساب {selected_user}.")
                            st.rerun()
                            
                with col_b:
                    st.write(f"**الرصيد الحالي:** {curr_c} كوينز")
                    new_c_val = st.number_input("الرصيد الجديد للكوينز:", value=curr_c, min_value=0, step=10)
                    reason_val = st.text_input("سبب التعديل:", value="شحن رصيد بواسطة الأدمن")
                    if st.button("تحديث رصيد الكوينز"):
                        update_user_coins(selected_user, new_c_val, st.session_state.user_email, reason_val)
                        st.success(f"تم تحديث رصيد {selected_user} إلى {new_c_val} كوينز!")
                        st.rerun()
                        
            st.markdown("---")
            st.markdown("### 📊 سجل نشاط ورسومات الحساب")
            logs = get_user_logs(selected_user)
            if logs:
                df_l = pd.DataFrame(logs, columns=["نوع الإجراء", "تغير الكوينز", "التفاصيل", "الوقت"])
                st.dataframe(df_l, use_container_width=True)
                
                c_chart1, c_chart2 = st.columns(2)
                with c_chart1:
                    fig_bar = render_account_bar_chart(df_l, selected_user)
                    st.pyplot(fig_bar)
                with c_chart2:
                    fig_line = render_account_line_chart(df_l, selected_user)
                    st.pyplot(fig_line)

    # --- صفحة فحص الـ ATS الرئيسي ---
    else:
        st.title("📄 تحليل وفحص السيرة الذاتية (ATS)")
        st.markdown(f"تكلفة الفحص لكل سيرة ذاتية: **{COINS_PER_CV} كوينز**")
        
        uploaded_files = st.file_uploader("قم برفع ملفات السيرة الذاتية (PDF):", type=["pdf"], accept_multiple_files=True)
        
        if uploaded_files:
            if st.button("🚀 بدء الفحص والتحليل"):
                total_cost = len(uploaded_files) * COINS_PER_CV
                
                if st.session_state.role != 'admin' and st.session_state.current_coins < total_cost:
                    st.error(f"رصيدك لا يكفي! تحتاج {total_cost} كوينز لديك فقط {st.session_state.current_coins} كوينز.")
                else:
                    results = []
                    progress_bar = st.progress(0)
                    
                    for idx, file in enumerate(uploaded_files):
                        file_name = file.name
                        text = ""
                        try:
                            file.seek(0)
                            with pdfplumber.open(file) as pdf:
                                for page in pdf.pages:
                                    t = page.extract_text()
                                    if t:
                                        text += t + "\n"
                        except Exception:
                            text = ""
                            
                        # استخراج البيانات الأساسية
                        email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text)
                        phone_match = re.search(r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', text)
                        
                        email = email_match.group(0) if email_match else "غير محدد"
                        phone = phone_match.group(0) if phone_match else "غير محدد"
                        name = file_name.rsplit('.', 1)[0].replace('_', ' ').replace('-', ' ')
                        
                        job_title = extract_job_title_with_ai(text)
                        
                        # حساب نسبة التوافق تقريبية بناءً على محتوى الكلمات
                        score = min(95, max(45, len(text.split()) // 5 if len(text.split()) > 0 else 50))
                        ai_analysis = analyze_cv_with_ai(text)
                        
                        ip_addr = get_user_ip()
                        append_to_google_sheet_silent(name, job_title, email, phone, score, st.session_state.user_email, ip_addr, file_name)
                        
                        res_item = {
                            "name": name,
                            "job_title": job_title,
                            "email": email,
                            "phone": phone,
                            "score": score,
                            "ai_analysis": ai_analysis,
                            "file_name": file_name
                        }
                        results.append(res_item)
                        progress_bar.progress((idx + 1) / len(uploaded_files))
                        
                    # خصم الكوينز للمستخدم العادي
                    if st.session_state.role != 'admin':
                        new_coins = st.session_state.current_coins - total_cost
                        update_user_coins(st.session_state.user_email, new_coins, "System", f"فحص {len(uploaded_files)} سيرة ذاتية")
                        
                    st.session_state.bulk_results = results
                    st.success("تم التقييم بنجاح!")
                    
        # عرض النتائج إذا كانت متوفرة
        if st.session_state.bulk_results:
            st.markdown("---")
            st.subheader("📊 نتائج التقييم:")
            for res in st.session_state.bulk_results:
                with st.expander(f"📌 {res['name']} - {res['job_title']} ({res['score']}%)", expanded=True):
                    c1, c2 = st.columns([1, 2])
                    with c1:
                        fig = render_score_circle(res['score'], is_ats_cv=(res['score'] >= 75))
                        st.pyplot(fig)
                    with c2:
                        st.markdown(f"**المسمى الوظيفي:** {res['job_title']}")
                        st.markdown(f"**البريد:** {res['email']}")
                        st.markdown(f"**الهاتف:** {res['phone']}")
                        st.markdown("---")
                        st.markdown(f"<div class='report-card'>{res['ai_analysis']}</div>", unsafe_allow_html=True)
                        
                        pdf_data = generate_pdf_report(res)
                        st.download_button(
                            label="📥 تحميل تقرير PDF التفصيلي",
                            data=pdf_data,
                            file_name=f"Report_{res['name']}.pdf",
                            mime="application/pdf"
                        )
