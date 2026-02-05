# User Guide – Face Recognition Attendance System

This guide explains how students and lecturers use the **Face Recognition Attendance System**.  
It focuses on **easy, step-by-step instructions** for registration, attendance marking, and session management.

---

## Table of Contents

1. [System Overview](#system-overview)  
2. [Student Guide](#student-guide)  
   - [Registration](#student-registration)  
   - [Marking Attendance](#marking-attendance)  
3. [Lecturer Guide](#lecturer-guide)  
   - [Creating Attendance Sessions](#creating-attendance-sessions)  
   - [Monitoring Attendance](#monitoring-attendance)  
   - [Exporting & Clearing Attendance Records](#exporting--clearing-attendance-records)  
4. [Rules & System Constraints](#rules--system-constraints)

---

## System Overview

The system is a **web-based attendance platform** that uses **facial recognition** to record student attendance.  
Key goals:

- Fast and low-friction attendance for students  
- Easy session creation and record management for lecturers  
- Accurate, secure, and duplicate-free attendance records  

---

## Student Guide

### Student Registration

Students register **once** to store their personal and facial data.

**Steps:**

1. Visit the system website.
2. Click **Register**.
3. Enter your details:
   - Full Name
   - Student ID / Matric Number
4. Complete face registration:
   - Webcam will capture multiple images of your face.
   - The system encodes and securely stores your facial embeddings.
5. Registration confirmation appears once the process is complete.

> Tip: Ensure your face is clearly visible and well-lit during registration.

---

### Marking Attendance

Students can mark attendance **without logging in**.

**Steps:**

1. Receive the attendance link from your lecturer.
2. Open the link in your web browser.
3. Position your face in front of the webcam.
4. Click **Capture**.
5. The system will:
   - Detect your face
   - Compare it with your registered facial data
6. If a match is successful:
   - Attendance is recorded with **date and time**
   - A confirmation message is displayed

> The system prevents multiple attendance attempts and unregistered faces from being marked.

---

## Lecturer Guide

Lecturers manage attendance sessions via the **Attendance Dashboard**.

### Creating Attendance Sessions

1. Sign up / log in as a lecturer.
2. Provide:
   - Full Name
   - Lecturer ID
   - Course Code
3. Access the **Attendance Dashboard**.
4. Generate a **unique attendance link** for the session.
5. Share the link with students.

---

### Monitoring Attendance

1. Students begin marking attendance via the shared link.
2. Attendance records appear live on the dashboard.
3. Each record includes:
   - Student Name
   - Student ID / Matric Number
   - Date
   - Time
   - Status (Present)

---

### Exporting & Clearing Attendance Records

1. Export attendance:
   - Click **Export**
   - Download the data as a spreadsheet (CSV or Excel)
   - Columns: Student Name | Matric Number | Date | Time | Status
2. Clearing attendance:
   - Records can be manually cleared after a session
   - Or automatically reset when a new session is created

> Tip: Always ensure records are reset before starting a new session.

---

## Rules & System Constraints

- **Face registration is one-time per student**.  
- **Attendance marking requires a successful face match**.  
- **Duplicate entries per student per session are not allowed**.  
- **User interface for attendance is minimal**: webcam + capture button only.  
- The system prevents:
  - Unregistered faces from marking attendance  
  - Multiple attempts by the same student  

---

## Acceptance Criteria (For Reference)

The system is considered complete when:

- Students can register successfully and store face data  
- Face recognition accurately matches students  
- Lecturers can generate attendance links  
- Students mark attendance via face capture only  
- Attendance records update live  
- Lecturers can export attendance data  
- Attendance records reset correctly between sessions

---

