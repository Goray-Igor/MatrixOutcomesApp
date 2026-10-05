import pandas as pd
from database.connection import execute_query

def get_brigade_data(user_id, role):
    """Отримує дані для дашборду керівника (Бригадира/Менеджера)"""
    if role == 'Admin':
        brigade_name = "Всі бригади (Адмін-режим)"
        query = """
            SELECT 
                m.RecordUID, m.ContractNumber, m.CounterpartyName, m.Village, 
                m.CadastralNumber, m.Area, m.LessorIntent, m.IntentLetterDate,
                u.FullName AS ManagerName, u.BrigadeName,
                r.ResultID, r.Outcome, r.ProcessingStatus, r.UpdatedAt,
                r.IsConflict, r.ExitOrder, r.CompetitorName, r.ContactType, r.ContactInfo, r.Comment
            FROM tbl_MainRegistry m
            INNER JOIN tbl_User_Villages uv ON m.Village = uv.VillageName
            INNER JOIN tbl_Users u ON uv.UserID = u.UserID
            LEFT JOIN tbl_Manager_Results r ON m.RecordUID = r.RecordUID AND r.ManagerID = u.UserID
            WHERE u.Role = 'Manager'
        """
        data = execute_query(query)
    else:
        q_name = "SELECT BrigadeName FROM tbl_Users WHERE UserID = ?"
        res = execute_query(q_name, (user_id,))
        brigade_name = res[0]['BrigadeName'] if res else "Невідома бригада"
        
        query = """
            SELECT 
                m.RecordUID, m.ContractNumber, m.CounterpartyName, m.Village, 
                m.CadastralNumber, m.Area, m.LessorIntent, m.IntentLetterDate,
                u.FullName AS ManagerName,
                r.ResultID, r.Outcome, r.ProcessingStatus, r.UpdatedAt,
                r.IsConflict, r.ExitOrder, r.CompetitorName, r.ContactType, r.ContactInfo, r.Comment
            FROM tbl_MainRegistry m
            INNER JOIN tbl_User_Villages uv ON m.Village = uv.VillageName
            INNER JOIN tbl_Users u ON uv.UserID = u.UserID
            LEFT JOIN tbl_Manager_Results r ON m.RecordUID = r.RecordUID AND r.ManagerID = u.UserID
            WHERE u.BrigadeName = ? AND u.Role = 'Manager'
        """
        data = execute_query(query, (brigade_name,))
        
    return brigade_name, pd.DataFrame(data) if data else pd.DataFrame()