import streamlit as st
import pandas as pd
from queries.manager_queries import save_manager_result, update_manager_result

def clear_process_session():
    keys = ['process_contract_uid', 'process_contract_num', 'process_owner', 'edit_mode', 'edit_result_id', 'edit_data']
    for k in keys:
        if k in st.session_state:
            del st.session_state[k]

def render_processing_form(on_save_callback=None):
    """Відображає форму опрацювання та зберігає дані в БД"""
    #is_edit = st.session_state.get('edit_mode', False)
    #row_data = st.session_state.get('edit_data', {})
    
    #st.subheader("📝 Редагування результатів" if is_edit else "📝 Внесення результатів")
    #st.markdown(f"Пайовик: **:green[{st.session_state.get('process_owner', '')}]** | Договір: **:green[{st.session_state.get('process_contract_num', '')}]**")
    is_edit = st.session_state.get('edit_mode', False)
    row_data = st.session_state.get('edit_data', {})
    
    # 1. Автоматично вибираємо правильне джерело даних
    row_info = row_data if is_edit else st.session_state.get('process_data', {})
    
    # Маленький помічник, щоб замість 'nan' писати гарний прочерк
    def get_val(val, default="-"):
        return default if pd.isna(val) or str(val).strip().lower() in ['nan', 'none', ''] else str(val)
        
    # Витягуємо наші нові поля
    cadastral = get_val(row_info.get('CadastralNumber'), "В ОФОРМЛЕННІ")
    area = row_info.get('Area')
    area_str = f"{area} га" if pd.notnull(area) else "0.0 га"
    share_num = get_val(row_info.get('ShareNumber'))
    
    # Твій заголовок сторінки
    st.subheader("📝 Редагування результатів" if is_edit else "📝 Внесення результатів")
    
    # 2. Замінюємо твій старий st.markdown на красиву інформаційну плашку st.info
    st.info(
        f"👤 Пайовик: **{st.session_state.get('process_owner', '')}** | 📄 Договір: **{st.session_state.get('process_contract_num', '')}**\n"
        f"📍 Кадастровий: :green[**{cadastral}**] | 📐 Площа: **{area_str}** | 🗺️ № по карті: **{share_num}**"
    )

    def get_idx(options, val): return options.index(val) if pd.notna(val) and val in options else 0
    def get_str(val): return str(val) if pd.notna(val) else ""
    def get_bool(val): return bool(val) if pd.notna(val) else False

    outcomes = ["", "Залишається", "Вилучається", "Резервується"]
    exit_orders = ["Одноосібно на своєму місці", "Одноосібно обмін", "Конкурент"]
    contact_types = ["Дзвінок", "Зустріч", "Месенджер", "Не вдалося зв'язатися"]

    with st.container(border=True):
        col1, col2 = st.columns(2)
        with col1:
            outcome = st.selectbox("Результат *", outcomes, index=get_idx(outcomes, row_data.get('Outcome')) if is_edit else 0)
            exit_order = st.selectbox("Порядок виходу", exit_orders, index=get_idx(exit_orders, row_data.get('ExitOrder')) if is_edit else 0) if outcome == "Вилучається" else ""
            competitor = st.text_input("Назва конкурента", value=get_str(row_data.get('CompetitorName'))) if exit_order == "Конкурент" else ""
            is_conflict = st.checkbox("⚠️ Конфліктний пайовик", value=get_bool(row_data.get('IsConflict')))
            
        with col2:
            contact_type = st.selectbox("Тип контакту", contact_types, index=get_idx(contact_types, row_data.get('ContactType')) if is_edit else 0)
            contact_info = st.text_input("Контакти", value=get_str(row_data.get('ContactInfo')), placeholder="+380...")
            comment = st.text_area("Коментар", value=get_str(row_data.get('Comment')))
        
        col_btn1, col_btn2 = st.columns(2)
        btn_text = "💾 Оновити результати" if is_edit else "💾 Зберегти"
        
        if col_btn1.button(btn_text, type="primary", use_container_width=True):
            if not outcome:
                st.error("Оберіть 'Результат'.")
                return
                
            status_calc = "Reserve" if outcome == "Резервується" else "Submitted"
            
            if is_edit:
                update_manager_result(
                    st.session_state['edit_result_id'], outcome, exit_order, competitor, 
                    contact_type, contact_info, comment, 1 if is_conflict else 0, status_calc
                )
                st.success("✅ Дані успішно оновлено!")
            else:
                save_manager_result(
                    st.session_state['process_contract_uid'], st.session_state['user_id'], outcome, exit_order, 
                    competitor, contact_type, contact_info, comment, 1 if is_conflict else 0, status_calc
                )
                st.success("✅ Збережено!")
                
            clear_process_session()
            if on_save_callback:
               on_save_callback() # Очищаємо кеш
            st.rerun()
                
        if col_btn2.button("❌ Скасувати", use_container_width=True):
            clear_process_session()
            st.rerun()