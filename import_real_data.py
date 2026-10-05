import pandas as pd
import numpy as np
from database.connection import get_connection

def import_from_excel(file_path):
    print(f"📂 Читаємо файл: {file_path}...")
    try:
        df = pd.read_excel(file_path)
    except FileNotFoundError:
        print(f"❌ Помилка: Файл '{file_path}' не знайдено.")
        return

    # 1. ЗАХИСТ ВІД ДУБЛІКАТІВ КОЛОНОК (напр. два "Контрагент")
    # Цей рядок залишає лише першу колонку, якщо імена повторюються
    df = df.loc[:, ~df.columns.duplicated()]

    # 2. Шукаємо колонку "Термін договору", бо вона має перенос рядка в 1С
    term_col = next((col for col in df.columns if "Термін договору" in str(col)), None)

    # 3. Очищення числових полів
    if 'Площадь' in df.columns:
        df['Площадь'] = pd.to_numeric(df['Площадь'].astype(str).str.replace(',', '.').str.replace(' ', ''), errors='coerce').fillna(0)

    if 'Кво. паев' in df.columns:
        df['Кво. паев'] = pd.to_numeric(df['Кво. паев'].astype(str).str.replace(',', '.').str.replace(' ', ''), errors='coerce').fillna(0)

    # 4. Очищення дат
    date_columns = ['Дата', 'Дата окончания действия', 'Дата листа наміру']
    for d_col in date_columns:
        if d_col in df.columns:
            df[d_col] = pd.to_datetime(df[d_col], dayfirst=True, errors='coerce').dt.date

    # 5. Заміна NaN на None для бази
    df = df.replace({np.nan: None})

    conn = get_connection()
    cursor = conn.cursor()

    print(f"🚀 Починаємо імпорт {len(df)} записів у базу даних...")
    success_count = 0
    error_count = 0

    for index, row in df.iterrows():
        try:
            # Отримуємо ключові дані
            cadastral = str(row.get('Кадастровый номер', '')).strip()
            agreement = str(row.get('Номер', '')).strip()

            # ГЕНЕРУЄМО RecordUID (Унікальний ідентифікатор)
            if not cadastral or cadastral.lower() == 'none' or cadastral == '':
                db_cadastral = None
                record_uid = f"{agreement}_TBD_{index}"
            else:
                db_cadastral = cadastral
                record_uid = f"{agreement}_{cadastral}"

            # Формуємо запис строго по порядку SQL таблиці
            record = (
                record_uid,                                   # 1. RecordUID
                db_cadastral,                                 # 2. CadastralNumber
                agreement,                                    # 3. AgreementUID
                agreement,                                    # 4. ContractNumber
                
                row.get('Село'),                              # 5. Village
                row.get('Хозяйство'),                         # 6. Cluster
                row.get('Головна організація'),               # 7. MainOrg
                row.get('Базовое поле'),                      # 8. FieldNumber
                '-',                                          # 9. CurrentCrop
                
                row.get('Контрагент'),                        # 10. CounterpartyName (візьме першого)
                str(row.get('ИНН', '')).strip() if row.get('ИНН') else None, # 11. INN
                
                row.get('Дата'),                              # 12. ContractDate
                row.get('Дата окончания действия'),           # 13. ExpiryDate
                row.get(term_col) if term_col else None,      # 14. TermYears
                row.get('Вид договора'),                      # 15. ContractType
                row.get('Вид арендодателя'),                  # 16. LessorType
                
                row.get('Площадь', 0),                        # 17. Area
                row.get('Вид земельного участка'),            # 18. PlotType
                row.get('Кво. паев', 0),                      # 19. ShareCount
                str(row.get('№ по карте роспаювання', '')),   # 20. ShareNumber
                row.get('Состояние'),                         # 21. RegStatus
                row.get('Статус земельного участка'),         # 22. PlotStatus
                
                '-',                                          # 23. CropProject
                row.get('Намір орендодавця'),                 # 24. LessorIntent
                row.get('Дата листа наміру')                  # 25. IntentLetterDate
            )

            query = """
                INSERT INTO tbl_MainRegistry (
                    RecordUID, CadastralNumber, AgreementUID, ContractNumber,
                    Village, Cluster, MainOrg, FieldNumber, CurrentCrop,
                    CounterpartyName, INN, ContractDate, ExpiryDate, TermYears,
                    ContractType, LessorType, Area, PlotType, ShareCount,
                    ShareNumber, RegStatus, PlotStatus, CropProject,
                    LessorIntent, IntentLetterDate
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            cursor.execute(query, record)
            success_count += 1

        except Exception as e:
            print(f"❌ Помилка в рядку {index + 1}: {e}")
            error_count += 1

    conn.commit()
    conn.close()
    
    print("-" * 30)
    print("✅ Імпорт завершено!")
    print(f"🟩 Успішно додано: {success_count}")
    print(f"🟥 Помилок/Пропущено: {error_count}")

if __name__ == "__main__":
    import_from_excel("data_from_1c.xlsx")