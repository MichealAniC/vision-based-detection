import sys
import os

print("Current working directory:", os.getcwd())
print("Python path:", sys.path)
print("File location:", os.path.abspath(__file__))
print("Directory of this file:", os.path.dirname(os.path.abspath(__file__)))

try:
    from database import init_db, DB_PATH
    print("Import successful!")
except ImportError as e:
    print("Import failed:", e)
    
    # Try alternative import methods
    try:
        from .database import init_db, DB_PATH
        print("Relative import successful!")
    except ImportError as e2:
        print("Relative import failed:", e2)
        
        try:
            from vision_attendance.database import init_db, DB_PATH
            print("Absolute import successful!")
        except ImportError as e3:
            print("Absolute import failed:", e3)