import streamlit as st
import google.generativeai as genai
from pdf2image import convert_from_bytes
import io
import os
import json

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

def input_pdf_setup(uploaded_file):
    try:
        # تحويل ملف الـ PDF إلى صور لمعالعتها عبر نموذج الرؤية
        images = convert_from_bytes(uploaded_file.read())
        first_page = images[0]
        
        # تحويل الصورة إلى بايتات
        img_byte_arr = io.BytesIO()
        first_page.save(img_byte_arr, format='JPEG')
        img_byte_arr = img_byte_arr.getvalue()
        
        pdf_parts = [
            {
                "mime_type": "image/jpeg",
                "data": base64.b64encode(img_byte_arr).decode()
            }
        ]
        return pdf_parts
    except Exception as e:
        st.error(f"خطأ في معالجة ملف الـ PDF: {e}")
        return None

import base64

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
        قم بتقييم السيرة الذاتية المرفقة بناءً على الوصف الوظيفي التالي:
        الوصف الوظيفي: {job_desc}
        
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
                
                pdf_content = input_pdf_setup(uploaded_file)
                
                if pdf_content:
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    response = model.generate_content([pdf_content[0], prompt.format(job_desc=job_description)])
                    
                    try:
                        # تنظيف النص المستلم لضمان استخراج JSON صحيح وخالٍ من الأخطاء
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
