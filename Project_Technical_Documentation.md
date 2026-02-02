# 🎯 USER STORY — FACE RECOGNITION ATTENDANCE SYSTEM

## 🧩 System Goal
Create a web-based facial recognition attendance system that allows students to register once and later mark attendance via face verification, while lecturers manage attendance sessions and export records easily.

The system is designed to be **fast, simple, and low-friction**, especially for students marking attendance in real-time.

---

## 👤 USER ROLES

### 1. Student
- **Registration**: Registers once with identity details and face data.
- **Verification**: Marks attendance via face verification only (no login required).

### 2. Admin (Lecturer)
- **Session Management**: Manages attendance logs and system state.
- **Data Control**: Views, exports, and clears attendance records for specific sessions.

---

## 🧑‍🎓 STUDENT USER STORY
> "As a student, I want to register my personal details and facial data once, so that I can later mark attendance quickly using face recognition without logging in."

### Student Registration Flow (Backend Logic)
1. **Visit**: Student accesses the `/register` portal.
2. **Details**: Enters Full Name and Student ID (Matric Number).
3. **Capture**: The system captures 30 biometric frames via the webcam.
4. **AI Logic (`face_logic.py`)**: 
    - The system **learns and classifies** the face using the LBPH algorithm.
    - **Facial embeddings** (histograms) are processed and linked to the unique Student ID.
5. **Confirmation**: Data is stored in the `students` table of the SQLite database.

### Attendance Marking Flow (AI Verification)
1. **Access**: Student stands before the "Live Recognition" dashboard.
2. **Detection**: The system detects a face in the live feed using Haar Cascades.
3. **Recognition**: 
    - The AI matches the live face against stored embeddings.
    - **Match Logic**: If the confidence score is high (LBPH distance < 55), the student is identified.
4. **Success**:
    - Attendance is marked as **Present**.
    - **Toast Notification**: A real-time popup appears saying "Recognized: [Name]".
    - **Logging**: Date and time are recorded in the `attendance` table.

---

## 👨‍🏫 ADMIN (LECTURER) USER STORY
> "As a lecturer, I want to manage attendance sessions and verify students via facial recognition, so that attendance is accurate, fast, and exportable."

### Admin Access & Dashboard
- **Authentication**: Secured via `@login_required` decorator and session encryption.
- **Live Monitoring**: The **Attendance Dashboard** updates in real-time as students are recognized by the AI.

### 📊 ATTENDANCE DASHBOARD
- **Live Records**: Displays Student Name, Matric Number, Date, Time, and Status.
- **System Stats**: Shows total registered students and today's attendance count at a glance.

### 📥 DATA EXPORT & MANAGEMENT
- **Spreadsheet Export**: Lecturers can download a CSV file containing all attendance data.
- **Session Reset Rules**:
    - **Clear Logs**: Manually deletes attendance records to start a new session while keeping student registrations.
    - **Full Reset**: Wipes all student data and logs for a complete system reboot.

---

## ⚙️ SYSTEM CONSTRAINTS & RULES

1. **One-Time Registration**: The system blocks duplicate registrations if the AI recognizes an existing face during the capture process.
2. **No Duplicate Entries**: A **10-second cooldown** ensures a student cannot be logged twice in a single recognition event.
3. **Simple UI**: The Student-facing interface is limited to a high-tech webcam feed with automated recognition (no buttons needed to mark attendance).
4. **Security**: Only registered faces can trigger a "Present" status; all other faces are labeled as "Unknown" by the AI.

---

## ✅ ACCEPTANCE CRITERIA (Technical Implementation)
- [x] Students can register once and store face data successfully.
- [x] AI accurately matches registered students with a strict confidence threshold.
- [x] Students mark attendance via face capture only (frictionless).
- [x] Attendance data updates live on the dashboard using JavaScript polling.
- [x] Lecturers can export attendance as a `.csv` spreadsheet.
- [x] Attendance records can be cleared cleanly between sessions.
