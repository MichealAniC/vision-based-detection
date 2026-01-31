from flask import Flask, render_template, Response, request, redirect, url_for, jsonify
import cv2
import os
from database import init_db, DB_PATH
import sqlite3
from face_logic import FaceRecognizer

app = Flask(__name__)
face_engine = FaceRecognizer()
face_engine.train()

# Global camera object and frame buffer
camera = cv2.VideoCapture()
last_frame = None

# Initialize DB on start
init_db()

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/attendance')
def view_attendance():
    conn = get_db_connection()
    records = conn.execute('''
        SELECT a.*, s.name 
        FROM attendance a 
        JOIN students s ON a.student_id = s.student_id 
        ORDER BY a.date DESC, a.time DESC
    ''').fetchall()
    conn.close()
    return render_template('attendance.html', records=records)

@app.route('/register', methods=['GET', 'POST'])
def register():
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
                student_dir = os.path.join('uploads', folder_name)
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

def gen_frames():
    global last_frame
    if not camera.isOpened():
        camera.open(0)
        
    while camera.isOpened():
        success, frame = camera.read()
        if not success:
            break
        
        last_frame = frame.copy()
        
        # Detect faces for display
        results = face_engine.detect_and_recognize(frame)
        for res in results:
            x, y, w, h = res['box']
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
            cv2.putText(frame, res['student_id'], (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (36,255,12), 2)
            
            # Auto-mark attendance if recognized
            if res['student_id'] != "Unknown":
                mark_attendance(res['student_id'])

        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

def mark_attendance(student_id):
    conn = get_db_connection()
    # Check if already marked today
    exists = conn.execute('SELECT id FROM attendance WHERE student_id = ? AND date = date("now")', (student_id,)).fetchone()
    if not exists:
        conn.execute('INSERT INTO attendance (student_id) VALUES (?)', (student_id,))
        conn.commit()
    conn.close()

@app.route('/save_frame', methods=['POST'])
def save_frame():
    global last_frame
    data = request.json
    student_id = data.get('student_id')
    count = data.get('count')
    
    if last_frame is not None:
        # RECOGNITION CHECK: Prevent re-registering an already known face
        results = face_engine.detect_and_recognize(last_frame)
        for res in results:
            # If recognized as someone else (not "Unknown" and not the current ID being registered)
            if res['student_id'] != "Unknown" and res['student_id'] != student_id:
                return jsonify({
                    "status": "duplicate", 
                    "message": f"Face already recognized as Student: {res['student_id']}. Duplicate registration denied."
                }), 400

        folder_name = student_id.replace('/', '-')
        student_dir = os.path.join('uploads', folder_name)
        img_path = os.path.join(student_dir, f"{count}.jpg")
        cv2.imwrite(img_path, last_frame)
        return jsonify({"status": "success"})
    
    return jsonify({"status": "error", "message": "No frame available"}), 500

@app.route('/train')
def train_model():
    success = face_engine.train()
    return jsonify({"status": "success" if success else "error"})

@app.route('/stop_camera')
def stop_camera():
    if camera.isOpened():
        camera.release()
    return jsonify({"status": "camera off"})

if __name__ == '__main__':
    app.run(debug=True)
