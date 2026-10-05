import pandas as pd

from database.connection import execute_query


def get_contracts(user_id, role):
    """Отримує всі договори. Адмін бачить все, фахівець - тільки свої села."""
    if role == 'Admin':
        query = """
            SELECT m.*, r.ResultID, r.Outcome, r.ExitOrder, r.CompetitorName, r.ContactType, 
                   r.ContactInfo, r.Comment, r.IsConflict, r.ProcessingStatus, r.UpdatedAt, r.IsLocked,
                   (SELECT TOP 1 eq.Status FROM tbl_EditRequests eq WHERE eq.ResultID = r.ResultID ORDER BY eq.RequestDate DESC) AS LastRequestStatus,
                   (SELECT TOP 1 eq.AdminComment FROM tbl_EditRequests eq WHERE eq.ResultID = r.ResultID ORDER BY eq.RequestDate DESC) AS AdminComment
            FROM tbl_MainRegistry m
            LEFT JOIN tbl_Manager_Results r ON m.RecordUID = r.RecordUID 
        """
        data = execute_query(query)
    else:
        query = """
            SELECT m.*, r.ResultID, r.Outcome, r.ExitOrder, r.CompetitorName, r.ContactType, 
                   r.ContactInfo, r.Comment, r.IsConflict, r.ProcessingStatus, r.UpdatedAt, r.IsLocked,
                   (SELECT TOP 1 eq.Status FROM tbl_EditRequests eq WHERE eq.ResultID = r.ResultID ORDER BY eq.RequestDate DESC) AS LastRequestStatus,
                   (SELECT TOP 1 eq.AdminComment FROM tbl_EditRequests eq WHERE eq.ResultID = r.ResultID ORDER BY eq.RequestDate DESC) AS AdminComment
            FROM tbl_MainRegistry m
            INNER JOIN tbl_User_Villages v ON m.Village = v.VillageName AND v.UserID = ?
            LEFT JOIN tbl_Manager_Results r ON m.RecordUID = r.RecordUID 
        """
        data = execute_query(query, (user_id,))
        
    return pd.DataFrame(data) if data else pd.DataFrame()

def request_edit(result_id, manager_id, reason):
    q_req = "INSERT INTO tbl_EditRequests (ResultID, ManagerID, RequestReason) VALUES (?, ?, ?)"
    execute_query(q_req, (result_id, manager_id, reason), fetch=False)
    q_res = "UPDATE tbl_Manager_Results SET ProcessingStatus = 'EditRequest' WHERE ResultID = ?"
    execute_query(q_res, (result_id,), fetch=False)

def save_manager_result(record_uid, manager_id, outcome, exit_order, competitor, contact_type, contact_info, comment, is_conflict, status_calc):
    query = """
        INSERT INTO tbl_Manager_Results 
        (RecordUID, ManagerID, Outcome, ExitOrder, CompetitorName, ContactType, ContactInfo, Comment, IsConflict, ProcessingStatus, IsLocked)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
    """
    execute_query(query, (record_uid, manager_id, outcome, exit_order, competitor, contact_type, contact_info, comment, is_conflict, status_calc), fetch=False)

def update_manager_result(result_id, outcome, exit_order, competitor, contact_type, contact_info, comment, is_conflict, status_calc):
    # Стан ДО змін: старий результат і наявність активного рішення ЗС
    prev = execute_query("""
        SELECT r.RecordUID, r.Outcome, d.DecisionID
        FROM tbl_Manager_Results r
        LEFT JOIN tbl_LandOfficer_Decisions d ON d.RecordUID = r.RecordUID AND d.IsActive = 1
        WHERE r.ResultID = ?
    """, (result_id,))

    query = """
        UPDATE tbl_Manager_Results 
        SET Outcome=?, ExitOrder=?, CompetitorName=?, ContactType=?, ContactInfo=?, Comment=?, IsConflict=?, ProcessingStatus=?, IsLocked=1, UpdatedAt=GETDATE()
        WHERE ResultID=?
    """
    ok = execute_query(query, (outcome, exit_order, competitor, contact_type, contact_info, comment, is_conflict, status_calc, result_id), fetch=False)

    # Якщо ЗС вже опрацювала цей запис — сповіщаємо про повторну обробку
    if ok and prev and prev[0]['DecisionID'] is not None:
        p = prev[0]
        q_notify = """
            IF EXISTS (SELECT 1 FROM tbl_LandOfficer_Notifications WHERE RecordUID = ? AND Status = 'New')
                UPDATE tbl_LandOfficer_Notifications
                SET NewOutcome = ?, CreatedAt = GETDATE()
                WHERE RecordUID = ? AND Status = 'New'
            ELSE
                INSERT INTO tbl_LandOfficer_Notifications (RecordUID, ResultID, DecisionID, OldOutcome, NewOutcome)
                VALUES (?, ?, ?, ?, ?)
        """
        execute_query(q_notify, (p['RecordUID'], outcome, p['RecordUID'],
                                 p['RecordUID'], result_id, p['DecisionID'], p['Outcome'], outcome), fetch=False)