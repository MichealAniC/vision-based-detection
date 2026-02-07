import cv2
import os
import numpy as np
import pickle
import time

class FaceRecognizer:
    def __init__(self, dataset_path=None, model_dir=None):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        
        # If paths are not provided, try to detect environment
        if dataset_path is None:
            if os.path.exists('/var/data'):
                self.dataset_path = '/var/data/uploads'
            else:
                self.dataset_path = os.path.join(base_dir, 'data', 'uploads')
        else:
            self.dataset_path = dataset_path

        if model_dir is None:
            if os.path.exists('/var/data'):
                self.model_dir = '/var/data/models'
            else:
                self.model_dir = os.path.join(base_dir, 'data', 'models')
        else:
            self.model_dir = model_dir
            
        self.model_path = os.path.join(self.model_dir, 'trained_model.yml')
        self.label_map_path = os.path.join(self.model_dir, 'label_map.pkl')
        
        # Using LBP Cascade for significantly faster detection compared to Haar
        # Fallback to Haar if LBP is unavailable
        lbp_path = cv2.data.haarcascades + 'lbpcascade_frontalface_improved.xml'
        if os.path.exists(lbp_path):
            self.face_cascade = cv2.CascadeClassifier(lbp_path)
        else:
            self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        
        # RADIUS=1, NEIGHBORS=8 is the standard set.
        self.recognizer = cv2.face.LBPHFaceRecognizer_create(radius=1, neighbors=8, grid_x=8, grid_y=8)
        self.trained = False
        self.label_map = {} # {int_label: student_id}
        self.last_train_time = 0 # Prevent excessive training calls
        
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

    def train(self, force=False):
        # Optimization: Cooldown to avoid CPU spikes on rapid registrations
        current_time = time.time()
        if not force and (current_time - self.last_train_time < 5):
            print("Training skipped: Cooldown active.")
            return True
            
        faces = []
        labels = []
        current_id = 0
        new_label_map = {}
        
        if not os.path.exists(self.dataset_path):
            return False

        # CRITICAL: Sort directories to ensure consistent label mapping across retrains
        sorted_dirs = sorted(os.listdir(self.dataset_path))
        
        for student_dir in sorted_dirs:
            student_path = os.path.join(self.dataset_path, student_dir)
            if not os.path.isdir(student_path):
                continue
                
            new_label_map[current_id] = student_dir
            
            # Load images for training
            img_list = os.listdir(student_path)
            # Use only a representative sample if dataset is huge, but here we take all
            for img_name in img_list:
                img_path = os.path.join(student_path, img_name)
                img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
                if img is None:
                    continue
                
                # Standardize size for training (LBPH needs consistent sizing for best results)
                img = cv2.resize(img, (200, 200), interpolation=cv2.INTER_LANCZOS4)
                # Normalization
                clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
                img = clahe.apply(img)
                img = cv2.GaussianBlur(img, (3, 3), 0)
                
                faces.append(img)
                labels.append(current_id)
            
            current_id += 1
            
        if len(faces) > 0:
            # Recreate recognizer for clean training
            self.recognizer = cv2.face.LBPHFaceRecognizer_create(radius=1, neighbors=8, grid_x=8, grid_y=8)
            self.recognizer.train(faces, np.array(labels))
            self.label_map = new_label_map
            self.trained = True
            self.save_model()
            self.last_train_time = time.time()
            print(f"Training complete: {len(new_label_map)} students, {len(faces)} images")
            return True
        else:
            self.trained = False
            if os.path.exists(self.model_path): os.remove(self.model_path)
            if os.path.exists(self.label_map_path): os.remove(self.label_map_path)
            return False

    def detect_and_recognize(self, frame, strict_threshold=50):
        # target_width 400 for better detection.
        target_width = 400 
        h, w = frame.shape[:2]
        scale = target_width / float(w)
        
        small_frame = cv2.resize(frame, (0, 0), fx=scale, fy=scale)
        gray = cv2.cvtColor(small_frame, cv2.COLOR_BGR2GRAY)
        
        # USE CLAHE for better light normalization
        clahe = cv2.createCLAHE(clipLimit=1.5, tileGridSize=(8,8))
        gray = clahe.apply(gray)
        
        # Detection - Optimized for speed
        # scaleFactor 1.05 (matches local), minNeighbors 10 (strict)
        # FORCE UPDATE CHECK: 1.05 / 10
        faces = self.face_cascade.detectMultiScale(gray, 1.05, 10, minSize=(40, 40))
        
        results = []
        inv_scale = 1.0 / scale
        full_gray = None 
        
        for (x, y, w_f, h_f) in faces:
            orig_x, orig_y, orig_w, orig_h = int(x*inv_scale), int(y*inv_scale), int(w_f*inv_scale), int(h_f*inv_scale)
            
            student_id = "Unknown"
            confidence_score = 0
            
            if self.trained:
                if full_gray is None:
                    full_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                
                roi_gray = full_gray[orig_y:orig_y+orig_h, orig_x:orig_x+orig_w]
                if roi_gray.size == 0: continue
                
                # Optimized Interpolation
                roi_gray = cv2.resize(roi_gray, (200, 200), interpolation=cv2.INTER_LINEAR)
                # Apply lighter CLAHE on ROI to avoid over-sharpening noise
                roi_gray = clahe.apply(roi_gray)
                roi_gray = cv2.GaussianBlur(roi_gray, (3, 3), 0)
                
                label, confidence = self.recognizer.predict(roi_gray)
                
                # LBPH confidence is DISTANCE: 0 is perfect match.
                # Threshold of 50 allows more variation while keeping bad matches out.
                if confidence < strict_threshold: 
                    student_id = self.label_map.get(label, "Unknown")
                
                confidence_score = confidence
            
            results.append({
                'box': (orig_x, orig_y, orig_w, orig_h),
                'student_id': student_id,
                'confidence_raw': confidence_score,
                'confidence': round(max(0, 100 - confidence_score), 2)
            })
        return results
