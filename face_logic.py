import cv2
import os
import numpy as np

class FaceRecognizer:
    def __init__(self, dataset_path='uploads'):
        self.dataset_path = dataset_path
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.recognizer = cv2.face.LBPHFaceRecognizer_create()
        self.trained = False
        self.label_map = {} # {int_label: student_id}

    def train(self):
        faces = []
        labels = []
        current_id = 0
        
        if not os.path.exists(self.dataset_path):
            return False

        for student_dir in os.listdir(self.dataset_path):
            student_path = os.path.join(self.dataset_path, student_dir)
            if not os.path.isdir(student_path):
                continue
                
            self.label_map[current_id] = student_dir
            
            for img_name in os.listdir(student_path):
                img_path = os.path.join(student_path, img_name)
                img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
                if img is None:
                    continue
                
                faces.append(img)
                labels.append(current_id)
            
            current_id += 1
            
        if len(faces) > 0:
            self.recognizer.train(faces, np.array(labels))
            self.trained = True
            return True
        return False

    def detect_and_recognize(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)
        
        results = []
        for (x, y, w, h) in faces:
            student_id = "Unknown"
            confidence = 0
            
            if self.trained:
                roi_gray = gray[y:y+h, x:x+w]
                label, confidence = self.recognizer.predict(roi_gray)
                if confidence < 100: # Threshold for LBPH
                    student_id = self.label_map.get(label, "Unknown")
            
            results.append({
                'box': (x, y, w, h),
                'student_id': student_id,
                'confidence': confidence
            })
        return results
