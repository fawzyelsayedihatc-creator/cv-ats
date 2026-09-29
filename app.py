import streamlit as st
import google.generativeai as genai
import os
import json
from pypdf import PdfReader
import pandas as pd

# إعداد صفحة Streamlit
st.set_page_config(page_title="نظام تقييم السير الذاتية الاحترافي ATS", layout="wide")

st.title("🎯 نظام تقييم السير الذاتية واكتشاف المطابقة (ATS CV)")
st.write("قم برفع السير الذاتية وإدخال الوصف الوظيفي لتحليلها بدقة واحترافية عالية.")

# إدخال المفتاح أو سحبه من الـ Secrets
api_key = st.text_input("أدخل مفتاح Gemini API:", type="password")

if not api_key and "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]

job_description = st.text_area("أدخل الوصف الوظيفي هنا (Job Description):")

# خيار نوع الفحص
analysis_mode = st.radio("اختر نوع الفحص:", ["فحص جماعي لملفات متعددة", "فحص منفرد لملف واحد"])
uploaded_files = st.file_uploader("اختر ملفات السيرة الذاتية (PDF):", type=["pdf"], accept_multiple_files=True)

def extract_text_from_pdf(uploaded_file):
    try:
        reader = PdfReader(uploaded_file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        return text
    except Exception as e:
        return ""

def extract_cv_info_with_ai(cv_text, job_desc):
    prompt = """
    أنت محلل خبير في أنظمة تتبع المتقدمين (ATS CV) ومسؤول موارد بشرية.
    قم بتحليل نص السيرة الذاتية التالي بناءً على الوصف الوظيفي، واستخرج البيانات بدقة:
    
    الوصف الوظيفي:
    {job_desc}
    
    نص السيرة الذاتية:
    {cv_text}
    
    أعطني النتيجة حصرياً بصيغة JSON صحيحة وبالهيكل التالي دون أي إضافات نصية خارجية:
    {{
      "Candidate Name": "اسم المرشح المستخرج باللغة الموجودة في السيرة الذاتية (إذا كان عربي يكتب بشكل صحيح ومنمق)",
      "Job Title": "المسمى الوظيفي أو التخصص المناسب للمرشح بناءً على خبراته",
      "Email": "البريد الإلكتروني إن وجد أو 'غير مذكور'",
      "Phone": "رقم الهاتف إن وجد أو 'غير مذكور'",
      "JD Match": "نسبة المطابقة كنسبة مئوية مثل 85%",
      "MissingKeywords": ["الكلمات", "المفتاحية", "الناقصة"],
      "Profile Summary": "ملخص تقييمي موجز لأداء المرشح ومدى ملاءمته للوظيفة كـ ATS CV"
    }}
    """
    
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt.format(job_desc=job_desc, cv_text=cv_text))
        clean_res = response.text.strip().replace("```json", "").replace("```", "").strip()
        return json.loads(clean_res)
    except Exception as e:
        return None

if st.button("بدء تحليل و تقييم الـ ATS CV"):
    if not api_key:
        st.warning("يرجى إدخال مفتاح Gemini API أولاً.")
    elif not job_description:
        st.warning("يرجى إدخال الوصف الوظيفي.")
    elif not uploaded_files:
        st.warning("يرجى رفع ملف سيرة ذاتية واحد على الأقل.")
    else:
        genai.configure(api_key=api_key)
        
        if analysis_mode == "فحص جماعي لملفات متعددة":
            st.subheader("📊 نتائج الفحص الجماعي الشامل (ATS CV)")
            table_data = []
            
            with st.spinner("جاري معالجة وفحص جميع السير الذاتية..."):
                for uploaded_file in uploaded_files:
                    cv_text = extract_text_from_pdf(uploaded_file)
                    if cv_text.strip():
                        res_json = extract_cv_info_with_ai(cv_text, job_description)
                        if res_json:
                            table_data.append({
                                "اسم الملف": uploaded_file.name,
                                "الاسم المستخرج": res_json.get("Candidate Name", "غير محدد"),
                                "المسمى الوظيفي": res_json.get("Job Title", "غير محدد"),
                                "البريد الإلكتروني": res_json.get("Email", "غير مذكور"),
                                "الهاتف": res_json.get("Phone", "غير مذكور"),
                                "ATS درجة": res_json.get("JD Match", "0%")
                            })
            
            if table_data:
                df = pd.DataFrame(table_data)
                st.dataframe(df, use_container_width=True)
            else:
                st.error("تعذر استخراج بيانات من الملفات المرفوعة.")
                
        else:
            st.subheader("🔍 تقرير الفحص المنفرد للـ ATS CV")
            for uploaded_file in uploaded_files:
                st.markdown(f"---")
                st.markdown(f"### ملف المرشح: {uploaded_file.name}")
                with st.spinner(f"جاري فحص وتحليل {uploaded_file.name}..."):
                    cv_text = extract_text_from_pdf(uploaded_file)
                    if cv_text.strip():
                        res_json = extract_cv_info_with_ai(cv_text, job_description)
                        if res_json:
                            col1, col2 = st.columns(2)
                            with col1:
                                st.metric(label="نسبة مطابقة الـ ATS CV", value=res_json.get("JD Match", "غير متوفرة"))
                                st.write(f"**الاسم المستخرج:** {res_json.get('Candidate Name', 'غير محدد')}")
                                st.write(f"**المسمى الوظيفي / التخصص:** {res_json.get('Job Title', 'غير محدد')}")
                            with col2:
                                st.write(f"**البريد الإلكتروني:** {res_json.get('Email', 'غير مذكور')}")
                                st.write(f"**الهاتف:** {res_json.get('Phone', 'غير مذكور')}")
                            
                            st.write("**الكلمات المفتاحية الناقصة:**")
                            st.info(", ".join(res_json.get("MissingKeywords", [])))
                            
                            st.write("**الملخص المهني للـ ATS:**")
                            st.success(res_json.get("Profile Summary", "لا يوجد ملخص."))
                    else:
                        st.error(f"تعذر استخراج النص من الملف {uploaded_file.name}")
