import sqlite3

def upgrade():
    conn = sqlite3.connect('eye_diagnosis.db')
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE appointment ADD COLUMN is_emergency BOOLEAN DEFAULT 0")
        print("Added is_emergency to appointment table.")
    except Exception as e:
        print(f"Error adding is_emergency: {e}")
        
    try:
        cursor.execute("ALTER TABLE diagnosis_report ADD COLUMN verification_status VARCHAR(20) DEFAULT 'pending'")
        print("Added verification_status to diagnosis_report table.")
    except Exception as e:
        print(f"Error adding verification_status: {e}")
        
    conn.commit()
    conn.close()

if __name__ == '__main__':
    upgrade()
