import cv2
import os
import numpy as np
import pickle

class FaceRecognizer:
    def __init__(self, dataset_path='uploads', model_dir='models'):
        self.dataset_path = dataset_path
        self.model_dir = model_dir
        self.model_path = os.path.join(model_dir, 'trained_model.yml')
        self.label_map_path = os.path.join(model_dir, 'label_map.pkl')
        
        # Using LBP Cascade for significantly faster detection compared to Haar
        # Fallback to Haar if LBP is unavailable
        lbp_path = cv2.data.haarcascades + 'lbpcascade_frontalface_improved.xml'
        if os.path.exists(lbp_path):
            self.face_cascade = cv2.CascadeClassifier(lbp_path)
        else:
            self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        
        # Using LBPH for recognition (as dlib is unavailable in this env)
        # We will structure it to use persistent storage as requested
        self.recognizer = cv2.face.LBPHFaceRecognizer_create()
        self.trained = False
        self.label_map = {} # {int_label: student_id}
        
        if not os.path.exists(self.model_dir):
            os.makedirs(self.model_dir)
            
        self.load_model()

    def load_model(self):
        if os.path.exists(self.model_path) and os.path.exists(self.label_map_path):
            try:
                self.recognizer.read(self.model_path)
                with open(self.label_map_path, 'rb') as f:
                    self.label_map = pickle.load(f)
                self.trained = True
                print("Model loaded successfully.")
            except Exception as e:
                print(f"Error loading model: {e}")

    def save_model(self):
        try:
            self.recognizer.write(self.model_path)
            with open(self.label_map_path, 'wb') as f:
                pickle.dump(self.label_map, f)
            print("Model saved to disk.")
        except Exception as e:
            print(f"Error saving model: {e}")

    def train(self):
        faces = []
        labels = []
        current_id = 0
        new_label_map = {}
        
        if not os.path.exists(self.dataset_path):
            return False

        for student_dir in os.listdir(self.dataset_path):
            student_path = os.path.join(self.dataset_path, student_dir)
            if not os.path.isdir(student_path):
                continue
                
            new_label_map[current_id] = student_dir
            
            for img_name in os.listdir(student_path):
                img_path = os.path.join(student_path, img_name)
                img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
                if img is None:
                    continue
                
                # Standardize size for training
                img = cv2.resize(img, (200, 200))
                faces.append(img)
                labels.append(current_id)
            
            current_id += 1
            
        if len(faces) > 0:
            self.recognizer.train(faces, np.array(labels))
            self.label_map = new_label_map
            self.trained = True
            self.save_model()
            return True
        else:
            self.trained = False
            # Clean up old models if no data
            if os.path.exists(self.model_path): os.remove(self.model_path)
            if os.path.exists(self.label_map_path): os.remove(self.label_map_path)
            return False

    def detect_and_recognize(self, frame):
        # Determine target detection width for consistent speed
        target_width = 320
        h, w = frame.shape[:2]
        scale = target_width / float(w)
        
        # Grayscale and resize for faster detection
        small_frame = cv2.resize(frame, (0, 0), fx=scale, fy=scale)
        gray = cv2.cvtColor(small_frame, cv2.COLOR_BGR2GRAY)
        
        # Apply Histogram Equalization to normalize lighting
        gray = cv2.equalizeHist(gray)
        
        # Increased minNeighbors to 7 for stricter face detection
        # minSize increased to ignore tiny background blobs
        faces = self.face_cascade.detectMultiScale(gray, 1.1, 7, minSize=(30, 30))
        
        results = []
        inv_scale = 1.0 / scale
        
        # Optimize: Only process the first face for recognition in real-time streams
        # to ensure high FPS, unless we need multi-person support.
        # Keeping multi-person for now but optimizing ROI extraction.
        
        full_gray = None # Lazy initialization
        
        for (x, y, w_f, h_f) in faces:
            # Upscale coordinates back to original size
            orig_x, orig_y, orig_w, orig_h = int(x*inv_scale), int(y*inv_scale), int(w_f*inv_scale), int(h_f*inv_scale)
            
            student_id = "Unknown"
            confidence_score = 0
            
            if self.trained:
                if full_gray is None:
                    full_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                
                roi_gray = full_gray[orig_y:orig_y+orig_h, orig_x:orig_x+orig_w]
                if roi_gray.size == 0: continue
                
                roi_gray = cv2.resize(roi_gray, (200, 200), interpolation=cv2.INTER_AREA)
                # Normalize ROI lighting
                roi_gray = cv2.equalizeHist(roi_gray)
                
                label, confidence = self.recognizer.predict(roi_gray)
                
                # LOWERED THRESHOLD: LBPH score below 55 is required for a positive match
                if confidence < 55: 
                    student_id = self.label_map.get(label, "Unknown")
                
                confidence_score = confidence
            
            results.append({
                'box': (orig_x, orig_y, orig_w, orig_h),
                'student_id': student_id,
                'confidence': round(max(0, 100 - confidence_score), 2)
            })
        return results
