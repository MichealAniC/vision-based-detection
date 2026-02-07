from flask import Flask, render_template, Response, request, redirect, url_for, jsonify, session, send_file
import cv2
import os
import time
import threading
import shutil
import csv
import io
import pickle
import uuid
import secrets
import base64
import numpy as np
from functools import wraps
try:
    from .database import init_db, DB_PATH
    from .face_logic import FaceRecognizer
except ImportError:
    from database import init_db, DB_PATH
    from face_logic import FaceRecognizer
import sqlite3

# Persistent Storage Path Configuration
# On Render, mount a disk to /var/data
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if os.path.exists('/var/data'):
    DATA_DIR = '/var/data'
else:
    # Fallback for local development
    DATA_DIR = os.path.join(BASE_DIR, 'data')
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

UPLOADS_DIR = os.path.join(DATA_DIR, 'uploads')
MODELS_DIR = os.path.join(DATA_DIR, 'models')
DB_PATH = os.path.join(DATA_DIR, 'attendance.db')

if not os.path.exists(UPLOADS_DIR):
    os.makedirs(UPLOADS_DIR)
if not os.path.exists(MODELS_DIR):
    os.makedirs(MODELS_DIR)

app = Flask(__name__, template_folder='Frontend', static_folder='Styles')
app.secret_key = secrets.token_hex(16)

# Initialize Face Engine with persistent paths
face_engine = FaceRecognizer(dataset_path=UPLOADS_DIR, model_dir=MODELS_DIR)
# Load existing models if any
face_engine.train()

# Global camera object and frame buffer
# NOTE: cv2.VideoCapture(0) accesses the server's local camera.
# In a cloud deployment (like Render), this will fail or find no camera.
# We now rely on client-side WebRTC to capture frames and send them to the server.
camera = cv2.VideoCapture()
last_frame = None

# Initialize DB on start with persistent path
init_db(DB_PATH)

# Performance Caching
student_name_cache = {} # {student_id: name}

def get_db_connection():
    conn = sqlite3.connect(DB_PATH, timeout=15)
    conn.row_factory = sqlite3.Row
    return conn

# --- Security: Authentication ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        lecturer_id = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM lecturers WHERE lecturer_id = ? AND password = ?', (lecturer_id, password)).fetchone()
        conn.close()
        
        if user:
            session['logged_in'] = True
            session['lecturer_id'] = user['lecturer_id']
            session['lecturer_name'] = user['name']
            session['course_code'] = user['course_code']
            return redirect(url_for('index'))
        else:
            error = 'Invalid Credentials. Please try again.'
    return render_template('login.html', error=error)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        lecturer_id = request.form['lecturer_id']
        course_code = request.form['course_code']
        password = request.form['password']
        
        conn = get_db_connection()
        try:
            conn.execute('INSERT INTO lecturers (name, lecturer_id, course_code, password) VALUES (?, ?, ?, ?)',
                         (name, lecturer_id, course_code, password))
            conn.commit()
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            return "Lecturer ID already exists", 400
        finally:
            conn.close()
    return render_template('signup.html')

@app.route('/create_session', methods=['POST'])
@login_required
def create_session():
    lecturer_id = session['lecturer_id']
    token = secrets.token_urlsafe(8)
    
    conn = get_db_connection()
    # Close any existing active sessions for this lecturer
    conn.execute('UPDATE sessions SET is_active = 0 WHERE lecturer_id = ?', (lecturer_id,))
    # Create new session
    conn.execute('INSERT INTO sessions (lecturer_id, session_token) VALUES (?, ?)', (lecturer_id, token))
    conn.commit()
    conn.close()
    
    return redirect(url_for('index'))

@app.route('/session/<token>')
def student_session(token):
    conn = get_db_connection()
    session_data = conn.execute('''
        SELECT s.*, l.name as lecturer_name, l.course_code 
        FROM sessions s 
        JOIN lecturers l ON s.lecturer_id = l.lecturer_id 
        WHERE s.session_token = ? AND s.is_active = 1
    ''', (token,)).fetchone()
    conn.close()
    
    if not session_data:
        return "Invalid or expired session link.", 404
        
    return render_template('student_attendance.html', session=session_data)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/privacy')
def privacy():
    return render_template('privacy.html')

@app.route('/help')
def help_page():
    return render_template('help.html')

# --- Main Routes ---
@app.route('/')
def landing():
    return render_template('landing.html')

@app.route('/dashboard')
@login_required
def index():
    # Dashboard Statistics
    lecturer_id = session.get('lecturer_id')
    if not lecturer_id:
        return redirect(url_for('login'))
        
    conn = get_db_connection()
    
    total_students = conn.execute('SELECT COUNT(*) FROM students').fetchone()[0]
    
    # Get active session
    active_session = conn.execute('SELECT * FROM sessions WHERE lecturer_id = ? AND is_active = 1', (lecturer_id,)).fetchone()
    
    today_attendance = 0
    if active_session:
        today_attendance = conn.execute('SELECT COUNT(DISTINCT student_id) FROM attendance WHERE session_id = ?', (active_session['id'],)).fetchone()[0]
    
    conn.close()
    
    return render_template('index.html', stats={
        'total_students': total_students,
        'today_attendance': today_attendance,
        'active_session': active_session
    })

@app.route('/attendance')
@login_required
def view_attendance():
    lecturer_id = session['lecturer_id']
    conn = get_db_connection()
    records = conn.execute('''
        SELECT a.*, s.name, sess.session_token
        FROM attendance a 
        JOIN students s ON a.student_id = s.student_id 
        JOIN sessions sess ON a.session_id = sess.id
        WHERE sess.lecturer_id = ?
        ORDER BY a.date DESC, a.time DESC
    ''', (lecturer_id,)).fetchall()
    conn.close()
    return render_template('attendance.html', records=records)

@app.route('/export_attendance')
@login_required
def export_attendance():
    lecturer_id = session['lecturer_id']
    conn = get_db_connection()
    records = conn.execute('''
        SELECT a.date, a.time, a.student_id, s.name, a.status 
        FROM attendance a 
        JOIN students s ON a.student_id = s.student_id 
        JOIN sessions sess ON a.session_id = sess.id
        WHERE sess.lecturer_id = ?
        ORDER BY a.date DESC, a.time DESC
    ''', (lecturer_id,)).fetchall()
    conn.close()

    proxy = io.StringIO()
    writer = csv.writer(proxy)
    writer.writerow(['Date', 'Time', 'Student ID', 'Name', 'Status'])
    for row in records:
        writer.writerow([row['date'], row['time'], row['student_id'], row['name'], row['status']])

    mem = io.BytesIO()
    mem.write(proxy.getvalue().encode('utf-8'))
    mem.seek(0)
    proxy.close()

    return send_file(
        mem,
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'attendance_{time.strftime("%Y%m%d_%H%M%S")}.csv'
    )

@app.route('/students')
@login_required
def manage_students():
    conn = get_db_connection()
    students = conn.execute('SELECT * FROM students ORDER BY created_at DESC').fetchall()
    conn.close()
    return render_template('manage_students.html', students=students)

@app.route('/delete_student/<path:student_id>', methods=['POST'])
@login_required
def delete_student(student_id):
    conn = get_db_connection()
    try:
        # 1. Delete from DB
        conn.execute('DELETE FROM attendance WHERE student_id = ?', (student_id,))
        conn.execute('DELETE FROM students WHERE student_id = ?', (student_id,))
        conn.commit()
        
        # 2. Delete Images
        folder_name = student_id.replace('/', '-')
        student_dir = os.path.join('uploads', folder_name)
        if os.path.exists(student_dir):
            shutil.rmtree(student_dir)
            
        # 3. Retrain model
        face_engine.train()
        
    except Exception as e:
        print(f"Error deleting student: {e}")
    finally:
        conn.close()
    return redirect(url_for('manage_students'))

@app.route('/delete_all_students', methods=['POST'])
@login_required
def delete_all_students():
    conn = get_db_connection()
    try:
        # 1. Clear students and attendance from DB
        conn.execute('DELETE FROM attendance')
        conn.execute('DELETE FROM students')
        conn.commit()
        
        # 2. Clear Uploaded Images
        if os.path.exists(UPLOADS_DIR):
            for filename in os.listdir(UPLOADS_DIR):
                file_path = os.path.join(UPLOADS_DIR, filename)
                if os.path.isdir(file_path):
                    shutil.rmtree(file_path)
                    
        # 3. Retrain (to empty model)
        face_engine.train()
    except Exception as e:
        print(f"Error resetting students: {e}")
    finally:
        conn.close()
    return redirect(url_for('manage_students'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    # Crucial: Ensure no admin session is active during student registration
    # but we don't want to log out an admin if they are just registering a student
    # Wait, the user says students are accessing admin features. 
    # Let's ensure 'logged_in' is only for lecturers.
    
    error = None
    if request.method == 'POST':
        name = request.form['name']
        student_id = request.form['student_id']
        
        conn = get_db_connection()
        # Check if ID exists
        existing_student = conn.execute('SELECT * FROM students WHERE student_id = ?', (student_id,)).fetchone()
        
        if existing_student:
            error = f"Student ID {student_id} is already registered to {existing_student['name']}."
        else:
            try:
                conn.execute('INSERT INTO students (name, student_id) VALUES (?, ?)', (name, student_id))
                conn.commit()
                
                # Create folder for student photos
                # Note: We replace slashes with dashes for the folder name to avoid OS issues
                folder_name = student_id.replace('/', '-')
                student_dir = os.path.join(UPLOADS_DIR, folder_name)
                if not os.path.exists(student_dir):
                    os.makedirs(student_dir)
                    
                return redirect(url_for('capture', student_id=student_id))
            except sqlite3.Error as e:
                error = f"Database error: {str(e)}"
        conn.close()
            
    return render_template('register.html', error=error)

@app.route('/capture/<path:student_id>')
def capture(student_id):
    return render_template('capture.html', student_id=student_id)

@app.route('/save_capture', methods=['POST'])
def save_capture():
    data = request.json
    image_data = data['image']
    student_id = data['student_id']

    # Decode base64 image
    header, encoded = image_data.split(",", 1)
    binary_data = base64.b64decode(encoded)
    image_array = np.frombuffer(binary_data, dtype=np.uint8)
    frame = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

    if frame is None:
        return jsonify({'status': 'error', 'message': 'Failed to decode image'}), 400

    # Face Detection for Validation & Cropping
    # Convert to grayscale for detection
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    # Use LBP or Haar Cascade (LBP is faster for validation)
    # Optimized for CAPTURE: scaleFactor 1.1 (faster), minNeighbors 5
    # Relaxed minSize to 100x100 to catch faces faster when user is close
    faces = face_engine.face_cascade.detectMultiScale(
        gray, scaleFactor=1.1, minNeighbors=5, minSize=(100, 100)
    )

    if len(faces) == 0:
        return jsonify({'status': 'retry', 'message': 'No face detected'}), 200
    
    if len(faces) > 1:
        return jsonify({'status': 'retry', 'message': 'Multiple faces detected'}), 200

    # Crop the first face found
    (x, y, w, h) = faces[0]
    # Add a small margin if possible, but keep it simple for now
    face_img = frame[y:y+h, x:x+w]
    
    # Check if crop is valid
    if face_img.size == 0:
        return jsonify({'status': 'retry', 'message': 'Invalid face crop'}), 200

    # Create folder if not exists
    folder_name = student_id.replace('/', '-')
    student_dir = os.path.join(UPLOADS_DIR, folder_name)
    if not os.path.exists(student_dir):
        os.makedirs(student_dir)

    # Save cropped image
        filename = f"{uuid.uuid4()}.jpg"
        filepath = os.path.join(student_dir, filename)
        cv2.imwrite(filepath, face_img)

        # Count existing images
        count = len([name for name in os.listdir(student_dir) if os.path.isfile(os.path.join(student_dir, name))])
        
        # Return success with box coordinates for drawing
        return jsonify({
            'status': 'success', 
            'count': count,
            'box': [int(x), int(y), int(w), int(h)] 
        })

@app.route('/process_attendance_frame', methods=['POST'])
def process_attendance_frame():
    data = request.json
    image_data = data['image']
    token = data['token']

    # Validate session
    conn = get_db_connection()
    session_data = conn.execute('SELECT id FROM sessions WHERE session_token = ? AND is_active = 1', (token,)).fetchone()
    conn.close()

    if not session_data:
        return jsonify({'status': 'error', 'message': 'Invalid session'}), 400
    
    session_id = session_data['id']

    # Decode image
    header, encoded = image_data.split(",", 1)
    binary_data = base64.b64decode(encoded)
    image_array = np.frombuffer(binary_data, dtype=np.uint8)
    frame = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

    if frame is None:
        return jsonify({'status': 'error', 'message': 'Failed to decode image'}), 400

    # Detect and recognize
    # STRICTER threshold to prevent false positives (42 - matching local spec)
    # FORCE UPDATE CHECK: If you see this comment, the code is updated.
    results = face_engine.detect_and_recognize(frame, strict_threshold=42)
    
    recognized_status = 'no_match'
    student_name = "Unknown"
    
    # Prepare response data with boxes
    faces_data = []
    
    for res in results:
        face_info = {
            'box': res['box'], # [x, y, w, h]
            'tag': res['student_id'] # "Unknown" or ID
        }
        
        if res['student_id'] != "Unknown":
            # Check for existing attendance FIRST
            conn = get_db_connection()
            exists = conn.execute('SELECT id FROM attendance WHERE student_id = ? AND session_id = ?', (res['student_id'], session_id)).fetchone()
            
            student = conn.execute('SELECT name FROM students WHERE student_id = ?', (res['student_id'],)).fetchone()
            if student:
                student_name = student['name']
                face_info['name'] = student_name
            conn.close()

            if exists:
                recognized_status = 'already_marked'
                face_info['status'] = 'already_marked'
            else:
                # If not marked, mark it
                mark_attendance(res['student_id'], session_id)
                recognized_status = 'marked'
                face_info['status'] = 'marked'
        else:
            face_info['status'] = 'unknown'

        faces_data.append(face_info)

    # Return the first recognized status (priority: marked > already_marked > no_match)
    # But include ALL face boxes for drawing
    return jsonify({
        'status': recognized_status, 
        'student_name': student_name,
        'faces': faces_data
    })

def gen_frames(session_id=None):
    global last_frame
    if not camera.isOpened():
        # Using CAP_DSHOW on Windows for significantly faster startup (0.5s vs 10s)
        camera.open(0, cv2.CAP_DSHOW)
        
        # Optimize camera resolution for faster processing if needed
        camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        camera.set(cv2.CAP_PROP_FPS, 30)
        
    frame_count = 0
    last_results = []
    
    while camera.isOpened():
        start_time = time.time()
        success, frame = camera.read()
        if not success:
            break
        
        last_frame = frame.copy()
        
        # Optimization: Detect frequently for students (every frame) but skip for admin (every 3rd) to save CPU
        should_detect = (session_id is not None) or (frame_count % 3 == 0)
        
        if should_detect:
            # Use a slightly more relaxed threshold (48) for attendance recognition to speed it up,
            # but keep it strict enough to avoid mixing.
            current_threshold = 48 if session_id else 45
            last_results = face_engine.detect_and_recognize(frame, strict_threshold=current_threshold)
        
        frame_count += 1
        
        # Draw results (even on skipped frames for smooth UI)
        for res in last_results:
            x, y, w, h = res['box']
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
            cv2.putText(frame, res['student_id'], (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (36,255,12), 2)
            
            # Auto-mark attendance if recognized AND session_id is provided
            if res['student_id'] != "Unknown" and session_id:
                mark_attendance(res['student_id'], session_id)

        # Optimize encoding: Use lower JPEG quality (70) for faster streaming
        ret, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 70])
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        
        # Throttle FPS to ~15 to reduce CPU load
        elapsed_time = time.time() - start_time
        sleep_time = max(0, (1.0 / 15.0) - elapsed_time)
        time.sleep(sleep_time)

@app.route('/video_feed')
def video_feed():
    # If a session token is provided, link to that session
    token = request.args.get('token')
    session_id = None
    if token:
        conn = get_db_connection()
        s = conn.execute('SELECT id FROM sessions WHERE session_token = ? AND is_active = 1', (token,)).fetchone()
        conn.close()
        if s:
            session_id = s['id']
            
    return Response(gen_frames(session_id), mimetype='multipart/x-mixed-replace; boundary=frame')

last_recognition_status = None # {'name': '...', 'status': '...'}

def mark_attendance(student_id, session_id):
    global last_recognition_status
    # Map folder-safe ID back to real ID if necessary
    
    # Quick check in cache first
    actual_id = student_id
    student_name = student_name_cache.get(student_id)
    
    conn = get_db_connection()
    if not student_name:
        # Search DB and update cache
        actual_student = conn.execute('''
            SELECT student_id, name FROM students 
            WHERE student_id = ? OR REPLACE(student_id, '/', '-') = ?
        ''', (student_id, student_id)).fetchone()
        
        if not actual_student:
            conn.close()
            return
            
        actual_id = actual_student['student_id']
        student_name = actual_student['name']
        student_name_cache[student_id] = student_name
        student_name_cache[actual_id] = student_name
    else:
        # If cache hit, we still need actual_id for the INSERT
        actual_student = conn.execute('''
            SELECT student_id FROM students 
            WHERE student_id = ? OR REPLACE(student_id, '/', '-') = ?
        ''', (student_id, student_id)).fetchone()
        if actual_student:
            actual_id = actual_student['student_id']
        else:
            conn.close()
            return

    student_id = actual_id

    # Cooldown logic (Per Session)
    current_time = time.time()
    cooldown_key = f"{student_id}_{session_id}"
    if not hasattr(mark_attendance, 'cooldowns'):
        mark_attendance.cooldowns = {}
        
    if cooldown_key in mark_attendance.cooldowns:
        # If recognized again within 10 seconds, notify that they are already marked
        # BUT only if they haven't been notified in the last 2 seconds to avoid spam
        if current_time - mark_attendance.cooldowns[cooldown_key] < 10: 
            if current_time - getattr(mark_attendance, 'last_notify', 0) > 2:
                last_recognition_status = {'name': student_name, 'status': 'already_marked'}
                mark_attendance.last_notify = current_time
            conn.close()
            return

    # Check if already marked in THIS session
    exists = conn.execute('SELECT id FROM attendance WHERE student_id = ? AND session_id = ?', (student_id, session_id)).fetchone()
    
    if not exists:
        try:
            conn.execute('INSERT INTO attendance (student_id, session_id, date, time, status) VALUES (?, ?, date("now"), time("now"), "Present")', (student_id, session_id))
            conn.commit()
            last_recognition_status = {'name': student_name, 'status': 'marked'}
            print(f"Attendance recorded: {student_id}")
            mark_attendance.last_notify = current_time
        except sqlite3.Error as e:
            print(f"DB Error marking attendance: {e}")
    else:
        # If already marked, notify the student
        last_recognition_status = {'name': student_name, 'status': 'already_marked'}
        mark_attendance.last_notify = current_time
        print(f"Student {student_id} already marked.")
    
    mark_attendance.cooldowns[cooldown_key] = current_time
    conn.close()

@app.route('/save_frame', methods=['POST'])
def save_frame():
    global last_frame
    data = request.json
    student_id = data.get('student_id')
    count = data.get('count')
    
    if last_frame is not None:
        # RECOGNITION CHECK: Prevent re-registering an already known face
        # Use a VERY STRICT threshold (35) to ensure we don't block new students unnecessarily,
        # but catch clear duplicates.
        results = face_engine.detect_and_recognize(last_frame, strict_threshold=35)
        
        # If no face is detected at all during capture, return error
        if not results:
             return jsonify({
                "status": "error", 
                "message": "Face not detected. Please look into the camera."
            }), 400

        for res in results:
            # If recognized as someone else (high confidence)
            if res['student_id'] != "Unknown" and res['student_id'] != student_id:
                # STRICT duplicate detection: 70+ confidence (which is < 30 distance) means strong match
                if res['confidence'] > 70: 
                    # Resolve Name for better feedback
                    conn = get_db_connection()
                    existing_student = conn.execute('SELECT name FROM students WHERE student_id = ?', (res['student_id'],)).fetchone()
                    conn.close()
                    duplicate_name = existing_student['name'] if existing_student else res['student_id']

                    return jsonify({
                        "status": "duplicate", 
                        "message": f"Security Alert: This face is already registered to {duplicate_name} ({res['student_id']})."
                    }), 400

        # Optimization: Use a higher quality face detection for the final save
        gray_frame = cv2.cvtColor(last_frame, cv2.COLOR_BGR2GRAY)
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        faces = face_cascade.detectMultiScale(gray_frame, 1.1, 10, minSize=(100, 100))
        
        save_img = gray_frame
        if len(faces) > 0:
            (x, y, w, h) = faces[0]
            save_img = gray_frame[y:y+h, x:x+w]
        
        save_img = cv2.resize(save_img, (200, 200))

        folder_name = student_id.replace('/', '-')
        student_dir = os.path.join('uploads', folder_name)
        img_path = os.path.join(student_dir, f"{count}.jpg")
        cv2.imwrite(img_path, save_img)
        return jsonify({"status": "success"})
    
    return jsonify({"status": "error", "message": "No frame available"}), 500

@app.route('/train')
def train_model():
    try:
        # Check if uploads directory has content
        if not os.path.exists(UPLOADS_DIR) or not os.listdir(UPLOADS_DIR):
             return jsonify({"status": "error", "message": "No student data found to train."}), 400

        # Synchronous training for registration to ensure data is immediately ready
        success = face_engine.train()
        if success:
            return jsonify({"status": "training_started"})
        else:
            return jsonify({"status": "error", "message": "Training failed. No valid face data found."}), 500
    except Exception as e:
        print(f"Training Error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

import shutil

@app.route('/delete_attendance_record/<int:record_id>', methods=['POST'])
@login_required
def delete_attendance_record(record_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM attendance WHERE id = ?', (record_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('view_attendance'))

@app.route('/reset_system', methods=['POST'])
def reset_system():
    conn = get_db_connection()
    try:
        # 1. Clear Database Tables
        conn.execute('DELETE FROM attendance')
        conn.execute('DELETE FROM students')
        conn.commit()
        
        # 2. Clear Uploaded Images
        folder = 'uploads'
        for filename in os.listdir(folder):
            file_path = os.path.join(folder, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print('Failed to delete %s. Reason: %s' % (file_path, e))
        
        # 3. Reload/Reset the Face Engine
        face_engine.trained = False
        face_engine.label_map = {}
        
        return jsonify({"status": "success", "message": "System has been completely reset. All students and records deleted."})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        conn.close()

@app.route('/delete_all_records', methods=['POST'])
@login_required
def delete_all_records():
    lecturer_id = session['lecturer_id']
    conn = get_db_connection()
    try:
        conn.execute('''
            DELETE FROM attendance 
            WHERE session_id IN (SELECT id FROM sessions WHERE lecturer_id = ?)
        ''', (lecturer_id,))
        conn.commit()
    except sqlite3.Error:
        pass
    finally:
        conn.close()
    return redirect(url_for('view_attendance'))

@app.route('/stop_camera')
def stop_camera():
    if camera.isOpened():
        camera.release()
    return jsonify({"status": "camera off"})

@app.route('/get_last_recognition')
def get_last_recognition():
    global last_recognition_status
    status = last_recognition_status
    last_recognition_status = None # Clear after fetching
    return jsonify(status if status else {})

# New endpoint for client-side camera capture
@app.route('/save_frame_client', methods=['POST'])
def save_frame_client():
    global last_frame
    student_id = request.form.get('student_id')
    count = int(request.form.get('count', 0))
    
    # Get the uploaded image
    if 'image' not in request.files:
        return jsonify({'status': 'error', 'message': 'No image provided'}), 400
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({'status': 'error', 'message': 'No image selected'}), 400
    
    try:
        # Read image data
        import numpy as np
        from PIL import Image
        
        # Convert to OpenCV format
        image = Image.open(file.stream)
        frame = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        
        # Store as last_frame for face recognition
        last_frame = frame.copy()
        
        # RECOGNITION CHECK: Prevent re-registering an already known face
        results = face_engine.detect_and_recognize(last_frame, strict_threshold=35)
        
        # If no face is detected at all during capture, return error
        if not results:
             return jsonify({
                'status': 'error', 
                'message': 'Face not detected. Please look into the camera.'
            }), 400

        for res in results:
            # If recognized as someone else (high confidence)
            if res['student_id'] != 'Unknown' and res['student_id'] != student_id:
                if res['confidence'] > 70: 
                    return jsonify({
                        'status': 'duplicate', 
                        'message': f'Security Alert: This face is already registered under Student ID: {res["student_id"]}.'
                    }), 400

        # Save the image
        gray_frame = cv2.cvtColor(last_frame, cv2.COLOR_BGR2GRAY)
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        faces = face_cascade.detectMultiScale(gray_frame, 1.1, 10, minSize=(100, 100))
        
        save_img = gray_frame
        if len(faces) > 0:
            (x, y, w, h) = faces[0]
            save_img = gray_frame[y:y+h, x:x+w]
        
        save_img = cv2.resize(save_img, (200, 200))

        folder_name = student_id.replace('/', '-')
        student_dir = os.path.join('uploads', folder_name)
        img_path = os.path.join(student_dir, f'{count}.jpg')
        cv2.imwrite(img_path, save_img)
        return jsonify({'status': 'success'})
    
    except Exception as e:
        print(f'Error saving frame: {e}')
        return jsonify({'status': 'error', 'message': 'Failed to process image'}), 500

if __name__ == '__main__':
    # Use 0.0.0.0 to bind to all network interfaces, allowing external connections
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)