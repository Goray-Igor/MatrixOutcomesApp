import streamlit as st
import pandas as pd
import io
from navigation import show_nav
from queries.brigadier_queries import get_brigade_data

show_nav()

# === 1. ЗАХИСТ СТОРІНКИ ===
if not st.session_state.get('logged_in') or st.session_state.get('user_role') not in ['Brigadier', 'Admin']:
    st.error("🚫 Доступ заборонено. Ця сторінка тільки для Менеджерів та Адміністраторів.")
    st.stop()

# === 2. ДОПОМІЖНІ ФУНКЦІЇ ===
@st.cache_data(ttl=60)
def load_brigade_data(user_id, role):
    return get_brigade_data(user_id, role)

def to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Реєстр')
    return output.getvalue()

def clean_str(val, default="-"):
    if pd.isna(val) or str(val).strip().lower() in ['nan', 'none', 'nat', '']:
        return default
    return str(val)

# === 3. ІНТЕРФЕЙС ===
brigade_name, df_all = load_brigade_data(st.session_state['user_id'], st.session_state['user_role'])

st.title(f"📊 Дашборд Менеджера: :blue[{brigade_name}]")

if df_all.empty:
    st.warning("У вашій команді поки що немає закріплених договорів або фахівців.")
    st.stop()

df_new = df_all[df_all['ResultID'].isna()]
df_done = df_all[df_all['ResultID'].notna()].copy()

if not df_done.empty:
    df_done['DateOnly'] = pd.to_datetime(df_done['UpdatedAt']).dt.date

# === РОЗБИВКА НА ВКЛАДКИ ===
tab_main, tab_dynamics, tab_details = st.tabs(["📊 Загальна статистика", "📈 Динаміка обробки", "🔍 Деталізація"])

# --- ВКЛАДКА 1: ЗАГАЛЬНА СТАТИСТИКА ---
with tab_main:
    total_contracts = len(df_all)
    done_contracts = len(df_done)
    new_contracts = len(df_new)
    progress_pct = int((done_contracts / total_contracts) * 100) if total_contracts > 0 else 0
    
    stayed_contracts = len(df_done[df_done['Outcome'] == 'Залишається'])
    retention_rate = int((stayed_contracts / done_contracts) * 100) if done_contracts > 0 else 0

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("📋 Всього", total_contracts)
    col2.metric("✅ Оброблено", done_contracts)
    col3.metric("⏳ Залишилось", new_contracts)
    col4.metric("🎯 Виконання", f"{progress_pct}%")
    col5.metric("🤝 Утримання", f"{retention_rate}%", help="Відсоток тих, хто погодився залишитись.")

    st.progress(progress_pct / 100)
    st.markdown("---")

    st.subheader("Розподіл результатів")
    if not df_done.empty:
        status_counts = df_done['Outcome'].value_counts()
        st.bar_chart(status_counts, color="#1f77b4")
        
        competitors = df_done[df_done['CompetitorName'].notna() & (df_done['CompetitorName'] != '')]
        if not competitors.empty:
            st.write("**Топ конкурентів:**")
            comp_counts = competitors['CompetitorName'].value_counts()
            st.dataframe(comp_counts, column_config={"count": "Втрачені договори"}, use_container_width=True)
    else:
        st.info("Немає даних для графіків.")

    st.markdown("---")

    st.subheader("👥 Рейтинг Фахівців")
    leaderboard = df_all.groupby('ManagerName').agg(
        Всього=('RecordUID', 'count'), 
        Оброблено=('ResultID', 'count')
    ).reset_index()
    
    leaderboard['Залишилось'] = leaderboard['Всього'] - leaderboard['Оброблено']
    leaderboard['Прогрес (%)'] = (leaderboard['Оброблено'] / leaderboard['Всього'] * 100).fillna(0).astype(int)
    
    st.dataframe(
        leaderboard, 
        hide_index=True, 
        use_container_width=True,
        column_config={"Прогрес (%)": st.column_config.ProgressColumn("Прогрес", format="%d%%", min_value=0, max_value=100)}
    )

# --- ВКЛАДКА 2: ДИНАМІКА ОБРОБКИ ---
with tab_dynamics:
    st.subheader("Активність у часі")
    if not df_done.empty:
        st.write("**1. Загальна кількість оброблених договорів по днях**")
        timeline_overall = df_done['DateOnly'].value_counts().sort_index()
        st.line_chart(timeline_overall, color="#2ca02c")
        
        col_dyn1, col_dyn2 = st.columns(2)
        with col_dyn1:
            st.write("**2. Динаміка по фахівцях**")
            timeline_managers = pd.crosstab(df_done['DateOnly'], df_done['ManagerName'])
            st.line_chart(timeline_managers)
        with col_dyn2:
            st.write("**3. Динаміка за статусами**")
            timeline_status = pd.crosstab(df_done['DateOnly'], df_done['Outcome'])
            st.line_chart(timeline_status)
    else:
        st.info("Немає оброблених договорів.")

# --- ВКЛАДКА 3: ДЕТАЛІЗАЦІЯ (З EXCEL) ---
with tab_details:
    st.subheader("Реєстри договорів")
    
    if not df_done.empty:
        conflicts = df_done[df_done['IsConflict'] == 1]
        if not conflicts.empty:
            st.error(f"⚠️ **Увага! Виявлено конфліктних пайовиків ({len(conflicts)} шт.):**")
            st.dataframe(conflicts[['ManagerName', 'CounterpartyName', 'Village', 'Outcome']], hide_index=True, use_container_width=True)
            st.markdown("---")

    type_filter = st.radio("Оберіть реєстр для перегляду:", ["В роботі (Необроблені)", "Оброблені"], horizontal=True)
    
    if type_filter == "В роботі (Необроблені)":
        if not df_new.empty:
            display_new = df_new[['ManagerName', 'CounterpartyName', 'ContractNumber', 'Village', 'CadastralNumber', 'Area', 'LessorIntent', 'IntentLetterDate']].copy()
            
            # Очищуємо поля намірів перед виводом
            display_new['LessorIntent'] = display_new['LessorIntent'].apply(lambda x: clean_str(x))
            display_new['IntentLetterDate'] = pd.to_datetime(display_new['IntentLetterDate'], errors='coerce').dt.strftime('%d.%m.%Y').fillna('-')
            
            display_new.columns = ['Фахівець', 'Пайовик', 'Договір', 'Село', 'Кадастровий', 'Площа (га)', 'Намір (з 1С)', 'Дата листа']
            st.dataframe(display_new, hide_index=True, use_container_width=True)
            
            excel_data = to_excel(display_new)
            st.download_button(
                label="📥 Завантажити в Excel",
                data=excel_data,
                file_name="Необроблені_договори.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.success("Всі договори оброблено!")
            
    else:
        if not df_done.empty:
            # Беремо розширені дані для оброблених договорів
            cols_to_show = ['ManagerName', 'CounterpartyName', 'ContractNumber', 'Outcome', 'Village', 'CompetitorName', 'LessorIntent', 'ContactInfo', 'Comment', 'UpdatedAt']
            display_done = df_done[cols_to_show].copy()
            
            display_done['LessorIntent'] = display_done['LessorIntent'].apply(lambda x: clean_str(x))
            display_done['UpdatedAt'] = pd.to_datetime(display_done['UpdatedAt']).dt.strftime('%d.%m.%Y %H:%M')
            
            display_done.columns = ['Фахівець', 'Пайовик', 'Договір', 'Результат', 'Село', 'Конкурент', 'Намір (з 1С)', 'Контакти', 'Коментар', 'Дата обробки']
            st.dataframe(display_done, hide_index=True, use_container_width=True)
            
            excel_data = to_excel(display_done)
            st.download_button(
                label="📥 Завантажити в Excel",
                data=excel_data,
                file_name="Оброблені_договори.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.info("Немає оброблених договорів.")