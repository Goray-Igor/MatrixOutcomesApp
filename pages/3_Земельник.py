import streamlit as st
import pandas as pd
from navigation import show_nav
from queries.landman_queries import get_landman_contracts
from components.landman_components import render_landman_card, render_landman_form

show_nav()

if not st.session_state.get('logged_in') or st.session_state.get('user_role') not in ['Landman', 'Admin']:
    st.error("🚫 Доступ заборонено.")
    st.stop()

user_role = st.session_state.get('user_role')
subrole = st.session_state.get('user_subrole')

@st.cache_data(ttl=60)
def load_data(user_id, role):
    return get_landman_contracts(user_id, role)

def get_safe_sorted_list(series):
    if series.empty:
        return []
    return sorted(series.dropna().astype(str).unique().tolist())

st.title("🗺️ Робоче місце Земельної служби")

# 1. Форма опрацювання
if 'process_contract_uid' in st.session_state:
    render_landman_form(on_save_callback=load_data.clear)
    st.stop()

# 2. Завантаження даних та логіка
df_all = load_data(st.session_state['user_id'], user_role)

if not df_all.empty:
    df_all['ExpiryDate'] = pd.to_datetime(df_all['ExpiryDate'], errors='coerce')
    df_all['Рік'] = df_all['ExpiryDate'].dt.year.astype('Int64').astype(str).replace('<NA>', 'Невідомо')
    
    # Фільтрація по вкладках
    df_stay = df_all[df_all['ManagerOutcome'] == 'Залишається']
    df_out = df_all[(df_all['ManagerOutcome'] == 'Вилучається') & df_all['DecisionID'].isna()]
    df_res = df_all[(df_all['ManagerOutcome'] == 'Резервується') & df_all['DecisionID'].isna()]
    df_done = df_all[df_all['DecisionID'].notna()]
else:
    df_stay = df_out = df_res = df_done = pd.DataFrame()

# 3. Метрики та Фільтри
cols_m = st.columns(4)
cols_m[0].metric("✅ Залишається", len(df_stay))
cols_m[1].metric("❌ На вилучення", len(df_out))
cols_m[2].metric("⏸️ В резерві", len(df_res))
cols_m[3].metric("📁 Оброблено ЗС", len(df_done))

search_q = st.text_input("🔍 Швидкий пошук (ПІБ або Кадастровий)", key="search_q_landman").lower()

st.write("### Фільтри")
c_f1, c_f2, c_f3, c_f4, c_f5 = st.columns(5)
v_val = c_f1.selectbox("Село", ["Всі"] + get_safe_sorted_list(df_all['Village']))
f_val = c_f2.selectbox("Поле", ["Всі"] + get_safe_sorted_list(df_all['FieldNumber']))
l_opts = ["Всі"] + get_safe_sorted_list(df_all['LessorType'])
l_val = c_f3.selectbox("Орендодавець", l_opts, index=l_opts.index("Фізична особа") if "Фізична особа" in l_opts else 0)
y_val = c_f4.selectbox("Рік закінчення", ["Всі"] + get_safe_sorted_list(df_all['Рік']))
c_val = c_f5.selectbox("Проект культури", ["Всі"] + get_safe_sorted_list(df_all['CropProject']))

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
        f_df = f_df[f_df['CropProject'] == c_val]
    if search_q:
        f_df = f_df[f_df['CounterpartyName'].str.lower().str.contains(search_q) | f_df['CadastralNumber'].str.contains(search_q, na=False)]
    return f_df

f_stay = apply_filters(df_stay)
f_out = apply_filters(df_out)
f_res = apply_filters(df_res)
f_done = apply_filters(df_done)

st.divider()

# 4. Рендеринг Вкладок через Компоненти
tabs = st.tabs([
    f"✅ Залишається ({len(f_stay)})", 
    f"❌ На вилучення ({len(f_out)})", 
    f"⏸️ Резерв ({len(f_res)})", 
    f"📁 Оброблено ЗС ({len(f_done)})"
])

def on_process_click(uid, contract_num, owner, row):
    st.session_state.update({
        'process_contract_uid': uid,
        'process_contract_num': contract_num,
        'process_owner': owner,
        'process_data': row
    })
    st.rerun()

def display_tab(df, tab_name):
    if df.empty:
        st.info("Немає записів.")
    else:
        for owner, group in df.groupby('CounterpartyName'):
            with st.expander(f"👤 {owner} ({len(group)})"):
                for _, row in group.iterrows():
                    render_landman_card(row, row['RecordUID'], row.get('ContractNumber', 'Б/Н'), owner, tab_name, subrole, user_role, on_process_click)

with tabs[0]:
    display_tab(f_stay, "stay")
with tabs[1]:
    st.error("Увага! Фахівці подали ці договори на вилучення. Потрібна ваша обробка.")
    display_tab(f_out, "out")
with tabs[2]:
    st.warning("Договори в резерві. Потребують подальшого оформлення.")
    display_tab(f_res, "res")
with tabs[3]:
    st.info("Реєстр договорів, які вже взяті в роботу Земельною службою.")
    display_tab(f_done, "done")