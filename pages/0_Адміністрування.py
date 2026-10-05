import streamlit as st
from navigation import show_nav
from queries.admin_queries import (
    get_pending_requests, 
    get_request_history, 
    get_all_users, 
    process_edit_request, 
    reset_user_password
)

show_nav()

# === 1. ЗАХИСТ СТОРІНКИ ===
if not st.session_state.get('logged_in') or st.session_state.get('user_role') != 'Admin':
    st.error("🚫 Доступ заборонено.")
    st.stop()

# === 2. ІНТЕРФЕЙС ===
st.title("⚙️ Панель Адміністратора")

tab_req, tab_hist, tab_users = st.tabs(["🔔 Нові запити", "🗄️ Реєстр запитів", "👥 Користувачі"])

# --- ВКЛАДКА 1: НОВІ ЗАПИТИ ---
with tab_req:
    st.subheader("Очікують рішення")
    df_req = get_pending_requests()
    
    if df_req.empty:
        st.success("🎉 Немає нових запитів на розблокування.")
    else:
        for _, row in df_req.iterrows():
            with st.container(border=True):
                st.markdown(f"**Фахівець:** :blue[{row['ManagerName']}] | **Пайовик:** {row['CounterpartyName']} | **Договір:** {row['ContractNumber']}")
                st.info(f"**Причина запиту:** {row['RequestReason']}")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✅ Схвалити (Дозволити редагування)", key=f"app_{row['RequestID']}", type="primary", use_container_width=True):
                        process_edit_request(row['RequestID'], row['ResultID'], st.session_state['user_id'], 'Approved')
                        st.toast("✅ Запит схвалено!")
                        st.rerun()
                
                with col2:
                    # Кнопка відхилення відкриває поле для вводу причини
                    if st.button("❌ Відхилити", key=f"rej_btn_{row['RequestID']}", use_container_width=True):
                        st.session_state[f'rejecting_{row["RequestID"]}'] = True
                
                if st.session_state.get(f'rejecting_{row["RequestID"]}'):
                    admin_reason = st.text_input("Вкажіть причину відмови (обов'язково):", key=f"rej_reason_{row['RequestID']}")
                    if st.button("Підтвердити відхилення", key=f"confirm_rej_{row['RequestID']}", type="primary"):
                        if not admin_reason:
                            st.error("Причина відмови обов'язкова!")
                        else:
                            process_edit_request(row['RequestID'], row['ResultID'], st.session_state['user_id'], 'Rejected', admin_reason)
                            st.toast("✅ Запит відхилено!")
                            del st.session_state[f'rejecting_{row["RequestID"]}']
                            st.rerun()

# --- ВКЛАДКА 2: ІСТОРІЯ ---
with tab_hist:
    st.subheader("Реєстр оброблених запитів")
    df_hist = get_request_history()
    if not df_hist.empty:
        st.dataframe(df_hist, hide_index=True, use_container_width=True)
    else:
        st.info("Історія порожня.")

# --- ВКЛАДКА 3: КОРИСТУВАЧІ ---
with tab_users:
    st.subheader("Керування користувачами")
    df_users = get_all_users()
    if not df_users.empty:
        user_options = {f"{row['FullName']} ({row['Username']}) - Роль: {row['Role']}": row['UserID'] for _, row in df_users.iterrows()}
        selected_user_label = st.selectbox("Скидання пароля користувачу:", [""] + list(user_options.keys()))
        
        if selected_user_label:
            temp_password = st.text_input("Тимчасовий пароль", value="123456")
            if st.button("🔄 Скинути пароль", type="primary"):
                reset_user_password(user_options[selected_user_label], temp_password)
                st.success(f"✅ Пароль змінено на: **{temp_password}**")
        st.write("---")
        st.dataframe(df_users, hide_index=True, use_container_width=True)