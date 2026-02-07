#!/usr/bin/env python3
"""
Backend Deployment Script for Vision Attendance System
This script prepares and deploys the backend-only portion of the application.
"""

import os
import sys
import subprocess
import shutil


def install_dependencies():
    """Install required Python packages"""
    print("Installing dependencies...")
    requirements_path = "requirements.txt"
    if os.path.exists(requirements_path):
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", requirements_path])
    else:
        print(f"Warning: {requirements_path} not found")


def prepare_backend():
    """Prepare backend for deployment"""
    print("Preparing backend for deployment...")
    
    # Create a deployment-specific app structure
    if not os.path.exists("dist"):
        os.makedirs("dist")
    
    # Copy backend files
    shutil.copytree("vision_attendance", "dist/vision_attendance", dirs_exist_ok=True)
    
    # Ensure all necessary files are present
    backend_files = [
        "dist/vision_attendance/app.py",
        "dist/vision_attendance/database.py", 
        "dist/vision_attendance/face_logic.py"
    ]
    
    for file_path in backend_files:
        if not os.path.exists(file_path):
            print(f"Warning: {file_path} not found")


def run_backend():
    """Run the backend server"""
    print("Starting backend server...")
    os.chdir("vision_attendance")
    subprocess.check_call([sys.executable, "app.py"])


def main():
    """Main deployment function"""
    print("Vision Attendance System - Backend Deployment")
    print("=" * 50)
    
    # Install dependencies
    install_dependencies()
    
    # Prepare backend
    prepare_backend()
    
    print("\nBackend deployment prepared successfully!")
    print("Files are located in the 'dist/' directory.")
    print("\nTo run the backend:")
    print("  cd vision_attendance")
    print("  python app.py")
    

if __name__ == "__main__":
    main()