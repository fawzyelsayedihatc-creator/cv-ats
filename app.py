# --- القائمة الجانبية (Sidebar) ---
    with st.sidebar:
        st.markdown(f"### 👤 الحساب الحالي:\n`{st.session_state.user_email}`")
        
        st.metric(label="🪙 رصيد الكوينز الحالي", value=f"{current_coins}")
        st.metric(label="📄 عدد الفحوصات المتاحة", value=f"{current_coins // COINS_PER_CV}")
        
        # --- زر لوحة الإدارة (يظهر فقط لحساب د. فوزي) ---
        if st.session_state.role == 'admin':
            st.divider()
            if st.session_state.current_page == "main":
                if st.button("👑 لوحة إدارة النظام", key="btn_go_admin"):
                    st.session_state.current_page = "admin"
                    st.rerun()
            else:
                if st.button("⬅️ العودة لفحص الـ CV", key="btn_go_main"):
                    st.session_state.current_page = "main"
                    st.rerun()

        st.divider()
        st.subheader("💳 شحن رصيد")
        whatsapp_url = f"https://wa.me/{WHATSAPP_NUMBER}?text=أهلاً%20دكتور%20فوزي،%20أريد%20شراء%20كوينز%20للحساب%20{st.session_state.user_email}"
        st.markdown(f'<a href="{whatsapp_url}" target="_blank" style="display:block; text-align:center; background:#25D366; color:white; font-weight:800; padding:12px; border-radius:8px; text-decoration:none;">💬 شحن الكوينز واتساب</a>', unsafe_allow_html=True)

        # --- نقل زر تسجيل الخروج لأسفل الصفحة الجانبية ---
        st.divider()
        if st.button("🚪 تسجيل الخروج", key="btn_logout"):
            st.session_state.logged_in = False
            st.session_state.user_email = ""
            st.session_state.role = "user"
            st.session_state.last_analysis = None
            st.session_state.current_page = "main"
            st.query_params.clear()
            st.rerun()
