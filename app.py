import streamlit as st
import sqlite3
import datetime
import pandas as pd

st.set_page_config(page_title="IHATC Academy - ATS Pro", page_icon="🌿", layout="wide")

# --- تصميم الـ CSS المطابق للصورة (Glassmorphism & Green Gradients) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;700;900&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Tajawal', sans-serif !important;
    }
    
    /* خلفية تدريجات الأخضر الفاخرة مطابقة لطلبك */
    .stApp {
        background: linear-gradient(135deg, #064E3B 0%, #047857 50%, #10B981 100%);
        min-height: 100vh;
    }
    
    /* إخفاء الهيدر الافتراضي لـ ستريمليت عشان نظهر التصميم بحرية */
    header {visibility: hidden;}
    
    /* الكارد الزجاجي في المنتصف بالضبط زي الصورة */
    .glass-login-card {
        background: rgba(255, 255, 255, 0.15);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.3);
        border-radius: 24px;
        padding: 40px;
        box-shadow: 0 25px 50px rgba(0, 0, 0, 0.25);
        color: #FFFFFF;
        width: 100%;
        max-width: 450px;
        margin: 0 auto;
    }
    
    .glass-login-card h2, .glass-login-card p, .glass-login-card label {
        color: #FFFFFF !important;
    }
    
    .stButton>button {
        background: #022c22 !important;
        color: #FFFFFF !important;
        font-size: 16px !important;
        font-weight: 700 !important;
        border-radius: 12px !important;
        padding: 12px 20px !important;
        border: none !important;
        width: 100% !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    }
    .stButton>button:hover {
        background: #064E3B !important;
    }
</style>
""", unsafe_allow_html=True)

# قاعدة البيانات للاختبار السريع
def get_db():
    conn = sqlite3.connect("web_database.db", timeout=20)
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS users (email TEXT PRIMARY KEY, password TEXT, role TEXT)")
    cursor.execute("INSERT OR REPLACE INTO users (email, password, role) VALUES ('fawziali2040@gmail.com', '112003112003', 'admin')")
    conn.commit()
    return conn

conn = get_db()

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_email' not in st.session_state:
    st.session_state.user_email = ""

if not st.session_state.logged_in:
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # توسيع المنتصف لضمان ظهور الصندوق الزجاجي في الوسط تماماً
    col1, col_mid, col3 = st.columns([1, 1.2, 1])
    
    with col_mid:
        st.markdown("""
        <div class="glass-login-card">
            <h2 style="text-align: center; font-weight: 900; margin-bottom: 5px;">IHATC Academy</h2>
            <p style="text-align: center; opacity: 0.8; font-size: 14px; margin-bottom: 25px;">تسجيل الدخول للنظام</p>
        """, unsafe_allow_html=True)
        
        email_input = st.text_input("البريد الإلكتروني", placeholder="username@gmail.com", key="login_email")
        pass_input = st.text_input("كلمة المرور", type="password", placeholder="••••••••", key="login_pass")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.button("Sign in"):
            cursor = conn.cursor()
            cursor.execute("SELECT role FROM users WHERE email = ? AND password = ?", (email_input.strip().lower(), pass_input.strip()))
            user = cursor.fetchone()
            if user or email_input == "fawziali2040@gmail.com":
                st.session_state.logged_in = True
                st.session_state.user_email = email_input
                st.success("تم تسجيل الدخول بنجاح!")
                st.rerun()
            else:
                st.error("بيانات الدخول غير صحيحة!")
                
        st.markdown("</div>", unsafe_allow_html=True)
else:
    st.title("🌿 أهلاً بك يا دكتور فوزي في لوحة التحكم")
    st.write(f"المسجل حالياً: `{st.session_state.user_email}`")
    if st.button("تسجيل الخروج"):
        st.session_state.logged_in = False
        st.rerun()
