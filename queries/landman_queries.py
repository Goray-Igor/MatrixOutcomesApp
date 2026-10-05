import pandas as pd

from database.connection import execute_query


def get_landman_contracts(user_id, role):
    """Отримує договори з рішеннями Фахівців та самої Зем. служби.
       Оскільки Земельна служба та Адміністратор мають глобальний доступ,
       ми прибираємо фільтрацію по tbl_User_Villages."""
       
    query = """
        SELECT 
            m.*, 
            r.ResultID, r.Outcome AS ManagerOutcome, r.ProcessingStatus AS ManagerStatus,
            r.ExitOrder, r.CompetitorName, r.ContactType, r.ContactInfo, r.Comment AS ManagerComment, r.IsConflict, r.UpdatedAt,
            d.DecisionID, d.OfficerID, uo.FullName AS OfficerName,
            d.RemovedCadastralNumbers, d.RemovedVillage, d.RemovedField, d.RemovedShareNumber, d.RemovedArea,
            d.Counterparty AS LandmanCounterparty, d.Comment AS LandmanComment,
            d.BoundarySettingDate, d.TerminationDate1C, d.DecisionDate
        FROM tbl_MainRegistry m
        LEFT JOIN tbl_Manager_Results r ON m.RecordUID = r.RecordUID
                LEFT JOIN tbl_LandOfficer_Decisions d ON m.RecordUID = d.RecordUID AND d.IsActive = 1
        LEFT JOIN tbl_Users uo ON d.OfficerID = uo.UserID
    """
    
    # Виконуємо запит без прив'язки до UserID, бо доступ потрібен до всього масиву
    data = execute_query(query)
    
    return pd.DataFrame(data) if data else pd.DataFrame()

def save_landman_decision(record_uid, officer_id, rem_cad, rem_vil, rem_field, rem_share, rem_area, counterparty, comment, bound_date, term_date, notification_id=None):
    """Зберігає рішення Зем. служби. Попереднє активне рішення архівується (IsActive=0)."""
    # 1. Архівуємо попереднє рішення (якщо це повторна обробка)
    execute_query(
        "UPDATE tbl_LandOfficer_Decisions SET IsActive = 0 WHERE RecordUID = ? AND IsActive = 1",
        (record_uid,), fetch=False
    )

    # 2. Нове активне рішення
    query_insert = """
        INSERT INTO tbl_LandOfficer_Decisions 
        (RecordUID, OfficerID, RemovedCadastralNumbers, RemovedVillage, RemovedField, RemovedShareNumber, RemovedArea, Counterparty, Comment, BoundarySettingDate, TerminationDate1C)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    execute_query(query_insert, (record_uid, officer_id, rem_cad, rem_vil, rem_field, rem_share, rem_area, counterparty, comment, bound_date, term_date), fetch=False)

    # 3. Статус для всіх
    query_update = "UPDATE tbl_Manager_Results SET ProcessingStatus = 'Processed' WHERE RecordUID = ?"
    execute_query(query_update, (record_uid,), fetch=False)

    # 4. Закриваємо сповіщення (якщо обробка була з вкладки сповіщень)
    if notification_id:
        execute_query(
            "UPDATE tbl_LandOfficer_Notifications SET Status = 'Processed', ProcessedBy = ?, ProcessedAt = GETDATE() WHERE NotificationID = ? AND Status = 'New'",
            (officer_id, notification_id), fetch=False
        )

def get_landman_notifications():
    """Нові сповіщення про зміни фахівців у вже опрацьованих ЗС записах"""
    query = """
        SELECT NotificationID, RecordUID, OldOutcome, NewOutcome, CreatedAt
        FROM tbl_LandOfficer_Notifications
        WHERE Status = 'New'
        ORDER BY CreatedAt DESC
    """
    data = execute_query(query)
    return pd.DataFrame(data) if data else pd.DataFrame()

def deactivate_decision(record_uid, notification_id, officer_id):
    """Деактивує активне рішення ЗС (фахівець змінив результат на 'Залишається').
       Нове рішення не створюється; сповіщення закривається зі статусом 'Deactivated'."""
    execute_query(
        "UPDATE tbl_LandOfficer_Decisions SET IsActive = 0 WHERE RecordUID = ? AND IsActive = 1",
        (record_uid,), fetch=False
    )
    # Знімаємо 'Processed' — запис більше не в роботі ЗС
    execute_query(
        "UPDATE tbl_Manager_Results SET ProcessingStatus = 'Submitted' WHERE RecordUID = ?",
        (record_uid,), fetch=False
    )
    execute_query(
        "UPDATE tbl_LandOfficer_Notifications SET Status = 'Deactivated', ProcessedBy = ?, ProcessedAt = GETDATE() WHERE NotificationID = ? AND Status = 'New'",
        (officer_id, notification_id), fetch=False
    )