import pandas as pd
import bcrypt
from database.connection import execute_query

def get_pending_requests():
    """Отримує список нових запитів на розблокування від Фахівців"""
    query = """
        SELECT eq.RequestID, eq.ResultID, m.ContractNumber, m.CounterpartyName, 
               u.FullName AS ManagerName, eq.RequestDate, eq.RequestReason, m.Village
        FROM tbl_EditRequests eq
        INNER JOIN tbl_Manager_Results r ON eq.ResultID = r.ResultID
        INNER JOIN tbl_MainRegistry m ON r.RecordUID = m.RecordUID
        INNER JOIN tbl_Users u ON eq.ManagerID = u.UserID
        WHERE eq.Status = 'Pending'
        ORDER BY eq.RequestDate DESC
    """
    data = execute_query(query)
    return pd.DataFrame(data) if data else pd.DataFrame()

def get_request_history():
    """Отримує історію вже оброблених (схвалених/відхилених) запитів"""
    query = """
        SELECT eq.RequestID, m.ContractNumber, u.FullName AS ManagerName, 
               eq.RequestReason, eq.Status, eq.AdminComment, eq.ProcessedDate
        FROM tbl_EditRequests eq
        INNER JOIN tbl_Manager_Results r ON eq.ResultID = r.ResultID
        INNER JOIN tbl_MainRegistry m ON r.RecordUID = m.RecordUID
        INNER JOIN tbl_Users u ON eq.ManagerID = u.UserID
        WHERE eq.Status != 'Pending'
        ORDER BY eq.ProcessedDate DESC
    """
    data = execute_query(query)
    return pd.DataFrame(data) if data else pd.DataFrame()

def get_all_users():
    """Отримує список усіх користувачів системи"""
    query = "SELECT UserID, Username, FullName, Role, IsActive FROM tbl_Users ORDER BY FullName"
    data = execute_query(query)
    return pd.DataFrame(data) if data else pd.DataFrame()

def process_edit_request(request_id, result_id, admin_id, status, comment=None):
    """Оновлює статус запиту і розблоковує/залишає заблокованим договір"""
    # Оновлюємо статус самого запиту в реєстрі
    q_req = "UPDATE tbl_EditRequests SET Status = ?, AdminID = ?, AdminComment = ?, ProcessedDate = GETDATE() WHERE RequestID = ?"
    execute_query(q_req, (status, admin_id, comment, request_id), fetch=False)
    
    # Оновлюємо статус договору для фахівця (1 - заблоковано, 0 - відкрито)
    is_locked = 0 if status == 'Approved' else 1
    q_res = "UPDATE tbl_Manager_Results SET IsLocked = ?, ProcessingStatus = 'Submitted' WHERE ResultID = ?"
    execute_query(q_res, (is_locked, result_id), fetch=False)

def reset_user_password(user_id, new_password):
    """Скидає пароль користувача на вказаний та вимагає його заміни при вході"""
    hashed = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    query = "UPDATE tbl_Users SET PasswordHash = ?, RequirePasswordChange = 1 WHERE UserID = ?"
    execute_query(query, (hashed, user_id), fetch=False)