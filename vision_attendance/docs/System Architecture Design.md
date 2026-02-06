# 🏗️ FaceReg System Architecture Design

This document provides an extensive technical breakdown of the **FaceReg Attendance System**, an AI-powered biometric solution designed for high-accuracy student identification and session-based attendance management.

---

## 1. Pipeline Approach
The system follows a sequential data pipeline that transforms physical light into a digital attendance record:

1.  **Image Acquisition**: Light reflected from the student's face is captured by the hardware sensor (Webcam).
2.  **Preprocessing**: The raw frame is normalized using **CLAHE** (Contrast Limited Adaptive Histogram Equalization) and Gaussian blurring to mitigate lighting variations and sensor noise.
3.  **Face Detection**: The "Where" stage—locating facial coordinates within the frame using LBP/Haar Cascades.
4.  **Feature Extraction**: The ROI (Region of Interest) is resized and processed into a unique facial histogram (LBPH).
5.  **Classification/Recognition**: The "Who" stage—the engine compares the live histogram against stored biometric templates using a strict confidence threshold.
6.  **Business Logic**: The backend verifies if the student is registered and if attendance for the current session has already been logged.
7.  **Data Persistence**: A successful match triggers a write operation to the SQLite database, creating a permanent, timestamped digital record.

---

## 2. Component Overview

### 📸 Camera
- **Hardware Interface**: Utilizes the system's primary imaging sensor.
- **Driver Integration**: Optimized with `cv2.CAP_DSHOW` on Windows for sub-second initialization and high-FPS throughput.

### 🔍 Face Detection
- **Technology**: Uses OpenCV's Cascade Classifiers (LBP Cascade for speed, Haar as fallback).
- **Function**: Scans the frame for facial patterns and returns bounding box coordinates `(x, y, w, h)`.

### 🧠 Face Recognition
- **Algorithm**: **LBPH** (Local Binary Patterns Histograms).
- **Logic**: Extracts spatial structures of the face, converting them into a multi-dimensional feature vector.
- **Accuracy**: Enhanced with CLAHE normalization and a production-grade confidence threshold of **42**.

### ⚙️ Backend (The "Brain")
- **Framework**: **Flask** (Python-based micro-framework).
- **Role**: Manages the application lifecycle, orchestrates the vision pipeline, handles authentication, and serves as the bridge between the UI and the database.

### 🗄️ Database
- **Engine**: **SQLite3**.
- **Role**: Lightweight, serverless relational database storing lecturer credentials, student biometric links, and historical attendance logs.

### 🌐 Web Interface
- **Framework**: **Bootstrap 5** & **Vanilla JavaScript**.
- **Role**: Provides a responsive, mobile-friendly portal for both students (standalone attendance marking) and lecturers (management dashboard).

---

## 3. Architectural Pattern (MVC)
FaceReg is structured using the **Model-View-Controller (MVC)** design pattern to ensure separation of concerns:

-   **Model (`database.py` & SQLite)**: Defines the data structure (Lecturers, Students, Sessions, Attendance).
-   **View (`Frontend/` folder)**: Handles the presentation layer using Jinja2 templates (HTML/CSS/JS).
-   **Controller (`app.py`)**: The logic layer that processes user input, interacts with the Face Engine (`face_logic.py`), and updates the Model.

---

## 4. Module Breakdown & Design

### 4.1 Image Acquisition Module
- **Hardware**: Laptop/Webcam.
- **Performance**: Frames are captured at 30 FPS.
- **Optimization**: To save CPU, recognition logic is throttled to run every 3rd frame, while the UI display remains smooth.

### 4.2 Face Detection Module (The "Where")
- **Engine**: OpenCV `CascadeClassifier`.
- **Bounding Boxes**: Rectangles are dynamically drawn around detected faces in real-time.
- **MinSize Constraint**: Configured to `40x40` pixels to ignore background noise and focus only on subjects close to the camera.

### 4.3 Face Recognition Module (The "Who")
- **LBPH (Implemented)**: Chosen for its robustness to lighting changes and efficiency in low-resource environments. It creates a local representation of the face by comparing pixels with their neighbors.
- **Comparison Logic**: The system calculates the "Euclidean Distance" between the live face and stored templates. A distance lower than **42** is required for a positive identity match.

---

## 5. Backend & Data Management

### 5.1 The Flask Server
- Manages encrypted sessions for lecturers.
- Handles multi-part video streaming (`multipart/x-mixed-replace`).
- Coordinates the "Mirror Effect" UI for intuitive student positioning.

### 5.2 Database Schema (SQLite)
#### **Lecturers Table**
| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | INTEGER | Primary Key |
| `lecturer_id` | TEXT | Unique Identifier (Login) |
| `name` | TEXT | Full Name |
| `course_code` | TEXT | Assigned Course |
| `password` | TEXT | Hashed/Plain Password |

#### **Students Table**
| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | INTEGER | Primary Key |
| `student_id` | TEXT | Unique Matric Number |
| `name` | TEXT | Full Name |
| `created_at` | TIMESTAMP | Enrollment Date |

#### **Attendance Table**
| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | INTEGER | Primary Key |
| `student_id` | TEXT | Foreign Key to Students |
| `session_id` | INTEGER | Foreign Key to Sessions |
| `date` | DATE | Log Date |
| `time` | TIME | Log Time |
| `status` | TEXT | Default: 'Present' |

---

## 6. Process Maps & Logic Flow

### 6.1 Attendance Sequence
When a student stands before the camera:
1.  **Frame Capture**: Backend grabs a frame via `cv2.VideoCapture`.
2.  **Detection**: Face coordinates are identified.
3.  **Preprocessing**: CLAHE normalization is applied.
4.  **Scoring**: The Face Engine calculates the match score against all registered students.
5.  **Verification**: 
    - If `Score < 42`: Identity is confirmed.
    - If `Score >= 42`: Identity is "Unknown".
6.  **Double-Marking Check**: Backend queries the `attendance` table for `(student_id, session_id)`.
7.  **Execution**: 
    - If new: Insert record -> Notify student "Attendance Marked!".
    - If exists: Notify student "Already Marked".

---

## 7. User Interface (UI) Design

### 7.1 Dashboard Layout
- **Lecturer Dashboard**: Features high-level stats (Global Registered vs. Session Count), session link generator, and real-time recognition toasts.
- **Attendance Logs**: A searchable, sortable table with granular delete controls for data integrity.

### 7.2 Real-Time Feedback
- **Scanning Line**: A CSS-animated laser line indicates active biometric scanning.
- **Guide Frame**: A circular overlay ensures students align their faces correctly for optimal recognition.
- **Toasts**: Instant non-intrusive popups confirm identity recognition: *"Recognized: Michael Ani"*.
