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
        LEFT JOIN tbl_LandOfficer_Decisions d ON m.RecordUID = d.RecordUID
        LEFT JOIN tbl_Users uo ON d.OfficerID = uo.UserID
    """
    
    # Виконуємо запит без прив'язки до UserID, бо доступ потрібен до всього масиву
    data = execute_query(query)
    
    return pd.DataFrame(data) if data else pd.DataFrame()

def save_landman_decision(record_uid, officer_id, rem_cad, rem_vil, rem_field, rem_share, rem_area, counterparty, comment, bound_date, term_date):
    """Зберігає рішення Зем. служби та блокує договір для фахівця"""
    query_insert = """
        INSERT INTO tbl_LandOfficer_Decisions 
        (RecordUID, OfficerID, RemovedCadastralNumbers, RemovedVillage, RemovedField, RemovedShareNumber, RemovedArea, Counterparty, Comment, BoundarySettingDate, TerminationDate1C)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    execute_query(query_insert, (record_uid, officer_id, rem_cad, rem_vil, rem_field, rem_share, rem_area, counterparty, comment, bound_date, term_date), fetch=False)
    
    # Оновлюємо статус, щоб усі бачили, що Земельник взяв це в роботу
    query_update = "UPDATE tbl_Manager_Results SET ProcessingStatus = 'Processed' WHERE RecordUID = ?"
    execute_query(query_update, (record_uid,), fetch=False)