import streamlit as st
import pandas as pd
from navigation import show_nav
from queries.manager_queries import get_contracts
from components.cards import render_contract_card
from components.forms import render_processing_form

show_nav()

if not st.session_state.get('logged_in') or st.session_state.get('user_role') not in ['Manager','Brigadier','Admin']:
    st.error("🚫 Доступ заборонено.")
    st.stop()

# Передаємо роль у функцію отримання даних
@st.cache_data(ttl=60)
def load_data(user_id, role):
    return get_contracts(user_id, role)

# КУЛЕНЕПРОБИВНА функція для фільтрів
def get_safe_sorted_list(df, col_name):
    if df.empty or col_name not in df.columns:
        return []
    return sorted(df[col_name].dropna().astype(str).unique().tolist())

st.title("💼 Робоче місце Фахівця")

if 'process_contract_uid' in st.session_state:
    render_processing_form(on_save_callback=load_data.clear)
    st.stop()

# Отримуємо дані з урахуванням ролі
df_all = load_data(st.session_state['user_id'], st.session_state['user_role'])

if not df_all.empty:
    df_all['ExpiryDate'] = pd.to_datetime(df_all['ExpiryDate'], errors='coerce')
    df_all['Рік'] = df_all['ExpiryDate'].dt.year.astype('Int64').astype(str).replace('<NA>', 'Невідомо')
    
    df_new = df_all[df_all['ResultID'].isna()]
    df_edit = df_all[df_all['ResultID'].notna() & (df_all['IsLocked'] == 0)]
    df_done_stay = df_all[df_all['ResultID'].notna() & (df_all['IsLocked'] == 1) & (df_all['Outcome'] == 'Залишається')]
    df_done_out = df_all[df_all['ResultID'].notna() & (df_all['IsLocked'] == 1) & (df_all['Outcome'] == 'Вилучається')]
    df_done_res = df_all[df_all['ResultID'].notna() & (df_all['IsLocked'] == 1) & (df_all['Outcome'] == 'Резервується')]
else:
    df_new = df_edit = df_done_stay = df_done_out = df_done_res = pd.DataFrame()

cols_m = st.columns(5)
cols_m[0].metric("⏳ Нові", len(df_new))
cols_m[1].metric("✅ Залишається", len(df_done_stay))
cols_m[2].metric("❌ Вихід", len(df_done_out))
cols_m[3].metric("⏸️ Резерв", len(df_done_res))
cols_m[4].metric("🔓 Редагування", len(df_edit))

search_q = st.text_input("🔍 Швидкий пошук (ПІБ або Кадастровий)", key="search_q").lower()

st.write("### Фільтри")
c_f1, c_f2, c_f3, c_f4, c_f5 = st.columns(5)

# Використовуємо нову безпечну функцію
v_val = c_f1.selectbox("Село", ["Всі"] + get_safe_sorted_list(df_all, 'Village'))
f_val = c_f2.selectbox("Поле", ["Всі"] + get_safe_sorted_list(df_all, 'FieldNumber'))

l_opts = ["Всі"] + get_safe_sorted_list(df_all, 'LessorType')
l_val = c_f3.selectbox("Орендодавець", l_opts, index=l_opts.index("Фізична особа") if "Фізична особа" in l_opts else 0)

y_val = c_f4.selectbox("Рік закінчення", ["Всі"] + get_safe_sorted_list(df_all, 'Рік'))
c_val = c_f5.selectbox("Культура", ["Всі"] + get_safe_sorted_list(df_all, 'CurrentCrop'))

def apply_filters(df):
    if df.empty:
        return df
    f_df = df.copy()
    if v_val != "Всі":
        f_df = f_df[f_df['Village'] == v_val]
    if f_val != "Всі":
        f_df = f_df[f_df['FieldNumber'] == f_val]
    if l_val != "Всі":
        f_df = f_df[f_df['LessorType'] == l_val]
    if y_val != "Всі":
        f_df = f_df[f_df['Рік'] == y_val]
    if c_val != "Всі":
        f_df = f_df[f_df['CurrentCrop'] == c_val]
    if search_q:
        f_df = f_df[f_df['CounterpartyName'].str.lower().str.contains(search_q) | f_df['CadastralNumber'].str.contains(search_q, na=False)]
    return f_df

f_new = apply_filters(df_new)
f_stay = apply_filters(df_done_stay)
f_out = apply_filters(df_done_out)
f_res = apply_filters(df_done_res)
f_edit = apply_filters(df_edit)

st.divider()

tabs = st.tabs([
    f"🆕 Необроблені ({len(f_new)})", 
    f"✅ Залишається ({len(f_stay)})", 
    f"❌ Вихід ({len(f_out)})", 
    f"⏸️ Резерв ({len(f_res)})", 
    f"🔓 На редагування ({len(f_edit)})"
])

def display_tab(df, tab_name):
    if df.empty:
        st.info("Не знайдено договорів.")
    else:
        for owner, group in df.groupby('CounterpartyName'):
            with st.expander(f"👤 {owner} ({len(group)})"):
                for _, row in group.iterrows():
                    render_contract_card(row, row['RecordUID'], row.get('ContractNumber', 'Б/Н'), owner, tab_name, on_update_callback=load_data.clear)

with tabs[0]:
    display_tab(f_new, "new")
with tabs[1]:
    display_tab(f_stay, "done")
with tabs[2]:
    display_tab(f_out, "done")
with tabs[3]:
    display_tab(f_res, "done")
with tabs[4]:
    display_tab(f_edit, "edit")