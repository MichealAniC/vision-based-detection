# Frontend & UI Development Guide

Welcome to the **Face Recognition Attendance System** frontend team! This guide will help you understand the project structure, what to touch, what to avoid, and how to use AI (like Qoder) to build a stunning UI.

## Where to Work (Your Territory)
All your magic happens in these two directories:

1.  **`templates/`**: Contains all HTML files (Jinja2 templates).
    *   `index.html`: The main layout/landing page.
    *   `dashboard.html`: The lecturer's command center.
    *   `signup.html` / `login.html`: Authentication pages.
    *   `register.html` / `capture.html`: Student registration flow.
    *   `student_attendance.html`: The clean, standalone marking view.
2.  **`static/`**: Contains your assets.
    *   `static/css/style.css`: All custom styling should go here.
    *   `static/js/`: Create this folder for any custom JavaScript (polling, animations, etc.).

## What to Avoid (The Backend "Engine Room")
Please do not modify these files unless you are coordinating with the backend team, as they contain the core AI and database logic:
- `app.py`: Handles routing and session logic.
- `face_logic.py`: The AI engine (Face Detection & Recognition).
- `database.py`: The SQLite schema and data handling.
- `models/`: Stored AI training artifacts.

## Working with Qoder (Your AI Assistant)
When you are working on the UI, you can use specific prompts to get the best out of the AI. Here are some examples:

### Example Prompts for UI Enhancements:
- *"I want to make the lecturer dashboard more modern. Use Bootstrap 5 cards with shadow-sm and add FontAwesome icons for the stats."*
- *"Refactor the landing page to be more professional. Add a hero section with a 'Get Started' button and make it mobile-responsive."*
- *"Add a loading spinner to the face capture button in `capture.html` while it's processing."*
- *"Update `style.css` to use a clean, dark-themed color palette for the entire application."*

## Key UI Guidelines
- **Framework**: We are using **Bootstrap 5**. Try to stick to its utility classes for consistency.
- **Icons**: We have **FontAwesome 6** integrated. Use it for buttons and headers.
- **Responsiveness**: Ensure all dashboards and tables use `table-responsive` and grid classes (`col-md-*`) so they look good on tablets/phones.
- **Student View**: The `student_attendance.html` should be kept **clean and isolated**. No navbars or footer links—just the camera and the marking process.

## How to Test Your Changes
Simply run the server:
```powershell
python app.py
```
Open `http://localhost:5000` in your browser. Any changes you make to `templates/` or `static/` will be reflected after a page refresh.

Happy Coding! 
