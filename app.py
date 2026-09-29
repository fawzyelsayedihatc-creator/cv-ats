import streamlit as st
import google.generativeai as genai
import os
import json
from pypdf import PdfReader

# إعداد صفحة Streamlit
st.set_page_config(page_title="ATS Resume Evaluator", layout="wide")

st.title("نظام تقييم السير الذاتية (ATS)")
st.write("قم برفع السير الذاتية وإدخال الوصف الوظيفي لتقييم مدى مطابقة المرشحين باستخدام الذكاء الاصطناعي.")

# إدخال المفتاح أو سحبه من الـ Secrets
api_key = st.text_input("أدخل مفتاح Gemini API:", type="password")

if not api_key and "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]

job_description = st.text_area("أدخل الوصف الوظيفي هنا:")
uploaded_files = st.file_uploader("اختر ملفات السيرة الذاتية (PDF):", type=["pdf"], accept_multiple_files=True)

def extract_text_from_pdf(uploaded_file):
    try:
        reader = PdfReader(uploaded_file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        return text
    except Exception as e:
        st.error(f"خطأ في قراءة ملف الـ PDF: {e}")
        return ""

if st.button("تقييم السير الذاتية"):
    if not api_key:
        st.warning("يرجى إدخال مفتاح Gemini API أولاً.")
    elif not job_description:
        st.warning("يرجى إدخال الوصف الوظيفي.")
    elif not uploaded_files:
        st.warning("يرجى رفع ملف سيرة ذاتية واحد على الأقل.")
    else:
        genai.configure(api_key=api_key)
        
        prompt = """
        أنت محلل خبير في أنظمة تتبع المتقدمين (ATS) ومسؤول موارد بشرية.
        قم بتقييم نص السيرة الذاتية التالي بناءً على الوصف الوظيفي:
        
        الوصف الوظيفي:
        {job_desc}
        
        نص السيرة الذاتية:
        {resume_text}
        
        أعطني النتيجة حصرياً على هيئة كود JSON بالصيغة التالية ودون أي إضافات نصية خارج الـ JSON:
        {{
          "JD Match": "نسبة المطابقة كنسبة مئوية مثل 85%",
          "MissingKeywords": ["الكلمات المفتاحية الناقصة"],
          "Profile Summary": "ملخص تقييمي موجز لأداء المرشح ومدى ملاءمته للوظيفة"
        }}
        """
        
        for uploaded_file in uploaded_files:
            st.subheader(f"تقرير تقييم الملف: {uploaded_file.name}")
            with st.spinner(f"جاري معالجة وتقييم {uploaded_file.name}..."):
                
                resume_text = extract_text_from_pdf(uploaded_file)
                
                if resume_text.strip():
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    response = model.generate_content(prompt.format(job_desc=job_description, resume_text=resume_text))
                    
                    try:
                        clean_res = response.text.strip().replace("```json", "").replace("```", "").strip()
                        result_json = json.loads(clean_res)
                        
                        st.metric(label="نسبة المطابقة (JD Match)", value=result_json.get("JD Match", "غير متوفرة"))
                        st.write("**الكلمات المفتاحية الناقصة:**")
                        st.write(", ".join(result_json.get("MissingKeywords", [])))
                        st.write("**الملخص المهني:**")
                        st.write(result_json.get("Profile Summary", "لا يوجد ملخص."))
                        
                    except Exception as e:
                        st.error(f"حدث خطأ في تحليل استجابة الذكاء الاصطناعي: {e}")
                        st.text(response.text)
                else:
                    st.error("تعذر استخراج النص من ملف الـ PDF. تأكد أن الملف يحتوي على نصوص واضحة.")
