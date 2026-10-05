import streamlit as st
import pandas as pd
from queries.landman_queries import save_landman_decision

def clean_str(val, default="-"):
    if pd.isna(val) or str(val).strip().lower() in ['nan', 'none', 'nat', '']:
        return default
    return str(val)

def render_landman_card(row, uid, contract_num, owner, tab_type, subrole, user_role, on_process_click):
    """Малює розширену картку договору для Земельника"""
    st.markdown(f"#### 📄 Договір: :green[{contract_num}]")
    
    # --- БЛОК 1: ДАНІ 1С (ЗГОРНУТО) ---
    with st.expander("🏛️ Дані реєстру 1С (Детально)", expanded=False):
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown("**📍 Географія та Поле**")
            st.write(f"Село: {clean_str(row.get('Village'))}")
            st.write(f"Базове поле: **{clean_str(row.get('FieldNumber'))}**")
            st.write(f"Проект культури: :blue[{clean_str(row.get('CropProject'))}]")
        with c2:
            st.markdown("**📜 Юридичні дані**")
            st.write(f"Кадастровий: :green[{clean_str(row.get('CadastralNumber'), 'В ОФОРМЛЕННІ')}]")
            st.write(f"Орендодавець: {clean_str(row.get('LessorType'))}")
            exp = row.get('ExpiryDate')
            st.write(f"Закінчення: {exp.strftime('%d.%m.%Y') if pd.notnull(exp) else '-'}")
        with c3:
            st.markdown("**📐 Характеристики**")
            area = row.get('Area')
            st.write(f"Площа: **{area if pd.notnull(area) else 0} га**")
            st.write(f"№ по карті: {clean_str(row.get('ShareNumber'))}")
        st.markdown("---")
        c_intent1, c_intent2 = st.columns(2)
        with c_intent1:
            st.write(f"🚩 Намір: **{clean_str(row.get('LessorIntent'))}**")
        with c_intent2:
            i_date = row.get('IntentLetterDate')
            st.write(f"📅 Дата листа наміру: {i_date.strftime('%d.%m.%Y') if pd.notnull(i_date) else '-'}")

    # --- БЛОК 2: РІШЕННЯ ФАХІВЦЯ ---
    st.markdown("##### 🗣️ Результат Фахівця")
    st.info(f"**Рішення:** {clean_str(row.get('ManagerOutcome'))} | **Порядок виходу:** {clean_str(row.get('ExitOrder'))} | **Конкурент:** {clean_str(row.get('CompetitorName'))} | **Контакти:** {clean_str(row.get('ContactInfo'))}" )
    if row.get('IsConflict'):
        st.error("⚠️ Увага! Фахівець позначив цього пайовика як КОНФЛІКТНОГО.")
    st.write(f"**Коментар фахівця:** {clean_str(row.get('ManagerComment'))}")
    
    # --- КНОПКА ДІЇ ---
    if tab_type in ['out', 'res'] and (subrole in ['Type1', 'Type2'] or user_role == 'Admin'):
        if st.button("📝 Опрацювати рішення", key=f"btn_land_{uid}"):
            on_process_click(uid, contract_num, owner, row)
    st.markdown("---")

def render_landman_form(on_save_callback=None):
    """Форма внесення даних Земельною службою"""
    uid = st.session_state.get('process_contract_uid')
    contract_num = st.session_state.get('process_contract_num')
    owner = st.session_state.get('process_owner')
    row = st.session_state.get('process_data', {})
    
    st.subheader("🛠️ Опрацювання рішення фахівця")
    st.markdown(f"Пайовик: **:green[{owner}]** | Договір: **:green[{contract_num}]**")
    
    with st.container(border=True):
        col1, col2 = st.columns(2)
        with col1:
            rem_cad = st.text_input("Вилучені кадастрові номери", value=clean_str(row.get('CadastralNumber'), ""))
            rem_vil = st.text_input("Село (вилучення)", value=clean_str(row.get('Village'), ""))
            rem_field = st.text_input("Поле (вилучення)", value=clean_str(row.get('FieldNumber'), ""))
            rem_share = st.text_input("№ Паю (вилучення)", value=clean_str(row.get('ShareNumber'), ""))
            rem_area = st.number_input("Вилучена площа (га)", value=float(row.get('Area') or 0.0))
        
        with col2:
            counterparty = st.text_input("Пайовик (Контрагент)", value=owner)
            comment = st.text_area("Коментар Земельної служби")
            bound_date = st.date_input("Дата винесення меж в натуру", value=None)
            term_date = st.date_input("Дата розірвання в 1С", value=None)
            
        c_btn1, c_btn2 = st.columns(2)
        if c_btn1.button("💾 Зберегти та закрити", type="primary", use_container_width=True):
            save_landman_decision(
                uid, st.session_state['user_id'], rem_cad, rem_vil, rem_field, 
                rem_share, rem_area, counterparty, comment, bound_date, term_date
            )
            st.success("✅ Дані збережено!")
            for k in ['process_contract_uid', 'process_contract_num', 'process_owner', 'process_data']:
                del st.session_state[k]
            if on_save_callback:
               on_save_callback()
            st.rerun()
            
        if c_btn2.button("❌ Скасувати", use_container_width=True):
            for k in ['process_contract_uid', 'process_contract_num', 'process_owner', 'process_data']:
                del st.session_state[k]
            st.rerun()