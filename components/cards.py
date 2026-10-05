import streamlit as st
import pandas as pd
from queries.manager_queries import request_edit

def clean_str(val, default="-"):
    """Надійна очистка від Pandas NaN, None та порожніх рядків"""
    if pd.isna(val) or str(val).strip().lower() in ['nan', 'none', 'nat', '']:
        return default
    return str(val)

def render_contract_card(row, uid, contract_num, owner, tab_type, on_update_callback=None):
    """Малює розширену картку договору та обробляє кнопки дій"""
    st.markdown(f"#### 📄 Договір: :green[{contract_num}]")
    
    if tab_type != "new":
        res = clean_str(row.get('Outcome'))
        outcome_color = "green" if res == "Залишається" else "red" if res == "Вилучається" else "orange"
        st.markdown(f"**Результат:** :{outcome_color}[{res}]")
    
    # --- РОЗШИРЕНА КАРТКА 1С ---
    with st.expander("📂 Повна інформація про ділянку та договір", expanded=(tab_type == "new")):
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown("**📍 Географія та Поле**")
            st.write(f"Село: {clean_str(row.get('Village'))}")
            st.write(f"Хозяйство: {clean_str(row.get('Cluster'))}")
            st.write(f"Базове поле: **{clean_str(row.get('FieldNumber'))}**")
            st.write(f"Поточна культура: {clean_str(row.get('CurrentCrop'))}")
            st.write(f"Проект культури: :blue[{clean_str(row.get('CropProject'))}]")
            
        with c2:
            st.markdown("**📜 Юридичні дані**")
            cad = clean_str(row.get('CadastralNumber'), default="В ОФОРМЛЕННІ")
            st.write(f"Кадастровий: :green[{cad}]")
            st.write(f"Вид договору: {clean_str(row.get('ContractType'))}")
            st.write(f"Орендодавець: {clean_str(row.get('LessorType'))}")
            st.write(f"ІПН: {clean_str(row.get('INN'))}")
            st.write(f"Термін: {clean_str(row.get('TermYears'))} р.")
            exp = row.get('ExpiryDate')
            st.write(f"Закінчення: {exp.strftime('%d.%m.%Y') if pd.notnull(exp) else '-'}")

        with c3:
            st.markdown("**📐 Характеристики**")
            area = row.get('Area')
            st.write(f"Площа: **{area if pd.notnull(area) else 0.0} га**")
            st.write(f"Кількість паїв: {clean_str(row.get('ShareCount'))}")
            st.write(f"№ по карті: {clean_str(row.get('ShareNumber'))}")
            st.write(f"Статус: {clean_str(row.get('PlotStatus'))}")
            
        st.markdown("---")
        c_intent1, c_intent2 = st.columns(2)
        with c_intent1:
            st.write(f"🚩 Намір: **{clean_str(row.get('LessorIntent'))}**")
        with c_intent2:
            i_date = row.get('IntentLetterDate')
            st.write(f"📅 Дата листа наміру: {i_date.strftime('%d.%m.%Y') if pd.notnull(i_date) else '-'}")

    # --- БЛОК ВНЕСЕНИХ РЕЗУЛЬТАТІВ (Тільки для оброблених) ---
    if tab_type != "new":
        with st.expander("📝 Внесені результати обробки", expanded=False):
            st.info(f"**Тип контакту:** {clean_str(row.get('ContactType'))} | **Контакти:** {clean_str(row.get('ContactInfo'))}")
            
            if row.get('Outcome') == "Вилучається":
                st.write(f"**Порядок виходу:** {clean_str(row.get('ExitOrder'))}")
                if clean_str(row.get('CompetitorName')) != "-":
                    st.write(f"**Конкурент:** :red[{clean_str(row.get('CompetitorName'))}]")
            
            if row.get('IsConflict'):
                st.error("⚠️ Пайовик відмічений як конфліктний!")
                
            st.write(f"**Коментар:** {clean_str(row.get('Comment'))}")

    # --- КНОПКИ ДІЙ ---
    if tab_type == "new":
        if st.button("✍️ Опрацювати", key=f"btn_{uid}"):
            st.session_state.update({
                'process_contract_uid': uid, 
                'process_contract_num': contract_num, 
                'process_owner': owner,
                'process_data': row, 
                'edit_mode': False
            })
            st.rerun()
            
    elif tab_type == "done":
        status = row.get('ProcessingStatus')
        if status == 'EditRequest':
            st.warning("⏳ Очікує дозволу на редагування від адміністратора")
        else:
            if row.get('LastRequestStatus') == 'Rejected':
                st.error(f"❌ Запит відхилено. Причина: {clean_str(row.get('AdminComment'), 'Без коментарів')}")
                
            if st.button("🔓 Запросити редагування", key=f"req_{row.get('ResultID', uid)}"):
                st.session_state[f'requesting_for_{row.get("ResultID", uid)}'] = True
                st.rerun()
                
            if st.session_state.get(f'requesting_for_{row.get("ResultID", uid)}'):
                reason = st.text_input("Вкажіть причину редагування:", key=f"reason_{row.get('ResultID', uid)}")
                col1, col2 = st.columns(2)
                if col1.button("Відправити", key=f"send_req_{row.get('ResultID', uid)}", type="primary"):
                    if reason:
                        request_edit(row['ResultID'], st.session_state['user_id'], reason)
                        st.toast("✅ Запит відправлено!")
                        del st.session_state[f'requesting_for_{row.get("ResultID", uid)}']
                        if on_update_callback:
                            on_update_callback()
                        st.rerun()
                    else:
                        st.error("Введіть причину!")
                if col2.button("Скасувати", key=f"cancel_req_{row.get('ResultID', uid)}"):
                    del st.session_state[f'requesting_for_{row.get("ResultID", uid)}']
                    st.rerun()
                    
    elif tab_type == "edit":
        if st.button("📝 Редагувати дані", key=f"edit_btn_{uid}"):
            st.session_state.update({
                'process_contract_uid': uid, 'process_contract_num': contract_num, 
                'process_owner': owner, 'edit_mode': True, 
                'edit_result_id': row['ResultID'], 'edit_data': row 
            })
            st.rerun()
            
    st.markdown("---")