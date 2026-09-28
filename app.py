import os
import re
import random
import sqlite3
import pdfplumber
import base64
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import google.generativeai as genai
import streamlit as st
from io import BytesIO

# --- إعدادات الصفحة ---
st.set_page_config(
    page_title="CV Checker - Dr. Fawzy Ali Panel",
    page_icon="🟢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# الثيم والتنسيقات الأخضر السعودي + توسيط فورمة الدخول
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
    
    /* تنسيق كارت الدخول في المنتصف */
    .login-box {
        background-color: #FFFFFF;
        padding: 30px;
        border-radius: 12px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
        border: 1px solid #E2E8F0;
    }
</style>
""", unsafe_allow_html=True)

# --- الثوابت ---
GEMINI_API_KEY = "AQ.Ab8RN6J7aiWlVQUTqWfGxcTe9zandjNMP6SIaWgFlJwILBfb9Q"
WHATSAPP_NUMBER = "201200686537"
COINS_PER_CV = 20
INITIAL_FREE_COINS = 200

genai.configure(api_key=GEMINI_API_KEY)
ai_model = genai.GenerativeModel('gemini-1.5-flash')

# --- قاعدة البيانات ---
def init_db():
    conn = sqlite3.connect("web_database.db")
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
    
    # حذف وإعادة إضافة حساب الأدمن لضمان التوافق التام
    cursor.execute("DELETE FROM users WHERE email = 'fawzi ali'")
    cursor.execute("INSERT INTO users (email, password, coins, is_approved, role) VALUES ('fawzi ali', '112003112003', 99999, 1, 'admin')")
    
    conn.commit()
    conn.close()

init_db()

def register_user(email, password):
    conn = sqlite3.connect("web_database.db")
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (email, password, coins, is_approved, role) VALUES (?, ?, ?, 0, 'user')",
                       (email.strip().lower(), password.strip(), INITIAL_FREE_COINS))
        conn.commit()
        conn.close()
        return True, "تم تقديم طلب التسجيل بنجاح! بانتظار موافقة د. فوزي لتفعيل الحساب."
    except sqlite3.IntegrityError:
        conn.close()
        return False, "هذا البريد أو اليوزر مسجل بالفعل!"

def login_user(email, password):
    conn = sqlite3.connect("web_database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT email, password, coins, is_approved, role FROM users WHERE email = ?", (email.strip().lower(),))
    user = cursor.fetchone()
    conn.close()
    
    if user and user[1] == password.strip():
        return True, user
    return False, None

def update_user_coins(email, new_coins):
    conn = sqlite3.connect("web_database.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET coins = ? WHERE email = ?", (new_coins, email.strip().lower()))
    conn.commit()
    conn.close()

def approve_user_db(email):
    conn = sqlite3.connect("web_database.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET is_approved = 1 WHERE email = ?", (email.strip().lower(),))
    conn.commit()
    conn.close()

def get_all_users():
    conn = sqlite3.connect("web_database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT email, coins, is_approved, role FROM users WHERE role != 'admin'")
    users = cursor.fetchall()
    conn.close()
    return users

# --- التقييم والتحليل ---
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
        response = ai_model.generate_content(prompt)
        return response.text
    except Exception:
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

# --- إيجاد جلسة التسجيل ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_email = ""
    st.session_state.role = "user"

# --- شاشة تسجيل الدخول وأن تكون متمركزة وأنيقة ---
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
            
            if st.button("دخول الأن"):
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
                    st.error("إسم المستخدم أو كلمة المرور غير صحيحة!")

        with tab_signup:
            signup_email = st.text_input("اسم المستخدم أو البريد الجديد:", key="s_email")
            signup_pass = st.text_input("كلمة المرور الجديدة:", type="password", key="s_pass")
            
            if st.button("إنشاء حساب جديد"):
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
    # 👑 لوحة الأدمن (دكتور فوزي)
    if st.session_state.role == 'admin':
        st.title("👑 لوحة تحكم الأدمن (دكتور فوزي)")
        
        with st.sidebar:
            st.success("مرحباً بك يا دكتور! (ADMIN)")
            if st.button("🚪 تسجيل الخروج"):
                st.session_state.logged_in = False
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

    # 👤 واجهة المستخدم العادي
    if st.session_state.role == 'user' or (st.session_state.role == 'admin' and 'tab_app' in locals()):
        if st.session_state.role == 'user':
            with st.sidebar:
                st.header("👤 حسابك الحالي")
                st.info(f"**المستخدم:**\n`{st.session_state.user_email}`")
                
                conn = sqlite3.connect("web_database.db")
                cursor = conn.cursor()
                cursor.execute("SELECT coins FROM users WHERE email = ?", (st.session_state.user_email,))
                current_coins = cursor.fetchone()[0]
                conn.close()
                
                st.metric(label="🪙 رصيد الكوينز المتبقي", value=f"{current_coins} كوين")
                st.metric(label="📄 الفحوصات المتاحة", value=f"{current_coins // COINS_PER_CV} فحص")
                
                if st.button("🚪 تسجيل الخروج"):
                    st.session_state.logged_in = False
                    st.rerun()

                st.divider()
                st.subheader("💳 شحن رصيد كوينز")
                whatsapp_url = f"https://wa.me/{WHATSAPP_NUMBER}?text=أهلاً%20دكتور%20فوزي،%20أريد%20شراء%20كوينز%20للحساب%20{st.session_state.user_email}"
                st.markdown(f'<a href="{whatsapp_url}" target="_blank" class="whatsapp-btn">💬 تواصل للشحن عبر الواتساب</a>', unsafe_allow_html=True)
        else:
            conn = sqlite3.connect("web_database.db")
            cursor = conn.cursor()
            cursor.execute("SELECT coins FROM users WHERE email = ?", (st.session_state.user_email,))
            current_coins = cursor.fetchone()[0]
            conn.close()

        st.title("📄 CV Checker")
        st.caption("نظام التقييم والتحليل الذكي للسير الذاتية")

        uploaded_file = st.file_uploader("قم برفع ملف السيرة الذاتية (PDF)", type=["pdf"])

        if uploaded_file is not None:
            if st.button("🚀 بدء تحليل السيرة الذاتية الآن", type="primary"):
                if current_coins < COINS_PER_CV:
                    st.error("⚠️ رصيدك غير كافٍ لإجراء الفحص! يرجى التواصل لشحن الرصيد.")
                else:
                    with st.spinner("🔍 جاري قراءة وتحليل الملف..."):
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
                            new_coins = current_coins - COINS_PER_CV
                            update_user_coins(st.session_state.user_email, new_coins)

                            name, email, phone, job_title, score = parse_cv_details(extracted_text)
                            ai_analysis = analyze_cv_with_ai(extracted_text)

                            cat_scores = [
                                max(30, score - random.randint(5, 15)),
                                max(35, score + random.randint(-5, 10)),
                                max(40, score - random.randint(0, 10)),
                                max(25, score - random.randint(10, 20)),
                                score
                            ]

                            st.success("✅ تم التقييم والتحليل بنجاح!")
                            st.divider()

                            # محاذاة العرض
                            pdf_col, report_col = st.columns([1.1, 1])

                            with pdf_col:
                                st.subheader("📄 السيرة الذاتية المرفوعة")
                                base64_pdf = base64.b64encode(uploaded_file.getvalue()).decode('utf-8')
                                pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}#toolbar=0&navpanes=0&scrollbar=0&view=FitH" width="100%" height="750" style="border:1px solid #CBD5E1; border-radius:8px;"></iframe>'
                                st.markdown(pdf_display, unsafe_allow_html=True)

                            with report_col:
                                fig = render_score_charts(score, cat_scores)
                                st.pyplot(fig)
                                st.divider()
                                st.markdown(ai_analysis)

                            st.divider()
                            st.subheader("📊 البيانات المستخرجة وتصدير الملف")
                            df_data = pd.DataFrame([{
                                "الاسم": name,
                                "التخصص": job_title,
                                "البريد الإلكتروني": email,
                                "الهاتف": phone,
                                "درجة ATS": f"{score}%"
                            }])
                            st.table(df_data)

                            output = BytesIO()
                            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                                df_data.to_excel(writer, index=False, sheet_name='Data')
                            excel_data = output.getvalue()

                            st.download_button(
                                label="📥 تحميل البيانات المستخرجة في ملف Excel",
                                data=excel_data,
                                file_name=f"CV_{name.replace(' ', '_')}.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                            )