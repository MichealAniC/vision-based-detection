import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'attendance.db')

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Lecturers Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS lecturers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            lecturer_id TEXT UNIQUE NOT NULL,
            course_code TEXT NOT NULL,
            password TEXT NOT NULL
        )
    ''')

    # Students Table (Keep existing)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            student_id TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Sessions Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lecturer_id TEXT NOT NULL,
            session_token TEXT UNIQUE NOT NULL,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (lecturer_id) REFERENCES lecturers (lecturer_id)
        )
    ''')

    # Attendance Table (Updated to link to session)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL,
            session_id INTEGER,
            date DATE DEFAULT (DATE('now')),
            time TIME DEFAULT (TIME('now')),
            status TEXT DEFAULT 'Present',
            FOREIGN KEY (student_id) REFERENCES students (student_id),
            FOREIGN KEY (session_id) REFERENCES sessions (id)
        )
    ''')
    
    # Add Index for performance
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_attendance_sid ON attendance(student_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_attendance_date ON attendance(date)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_attendance_session ON attendance(session_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(session_token)')
    
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
    print("Database initialized.")
