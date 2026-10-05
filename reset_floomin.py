import bcrypt
from database.connection import get_connection

def reset_floomin_password():
    conn = get_connection()
    if not conn:
        print("❌ Помилка підключення до БД")
        return
        
    cursor = conn.cursor()
    
    # Встановимо тимчасовий пароль
    temp_password = "admin_reset_2026"
    hashed = bcrypt.hashpw(temp_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    try:
        # Оновлюємо пароль для Floomin та змушуємо його змінити при вході
        cursor.execute("""
            UPDATE tbl_Users 
            SET PasswordHash = ?, RequirePasswordChange = 1 
            WHERE Username = 'Floomin'
        """, (hashed,))
        
        if cursor.rowcount > 0:
            conn.commit()
            print("✅ Пароль для Floomin успішно скинуто!")
            print(f"Тимчасовий пароль: {temp_password}")
            print("💡 Після входу система попросить вас встановити новий постійний пароль.")
        else:
            print("⚠️ Користувача з логіном 'Floomin' не знайдено в базі.")
            
    except Exception as e:
        print(f"❌ Помилка: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    reset_floomin_password()