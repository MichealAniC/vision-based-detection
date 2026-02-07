# Backend Deployment Guide

This guide covers deploying only the backend portion of the Vision Attendance System.

## Deployment Options

### Option 1: Deploy to Render

1. Connect your GitHub repository to Render
2. Use the `render.yaml` file in the root directory
3. Render will automatically detect the Python environment and deploy

### Option 2: Deploy with Docker

1. Build the Docker image:
   ```bash
   docker build -t vision-attendance-backend .
   ```

2. Run the container:
   ```bash
   docker run -p 5000:5000 vision-attendance-backend
   ```

### Option 3: Deploy to Heroku

1. Create a new app in Heroku dashboard
2. Connect to your GitHub repository
3. Use the `Procfile` in the root directory
4. Enable automatic deploys

### Option 4: Manual Deployment

1. Clone the repository to your server
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   cd vision_attendance
   gunicorn -w 4 -b 0.0.0.0:5000 app:app
   ```

## Environment Variables

The backend uses the following environment variables:

- `PORT` - Port number to run the server on (defaults to 5000)
- `FLASK_ENV` - Environment setting (production/development)

## Health Check

The backend provides a basic health check at the `/` route. The server should respond with the landing page.

## Scaling Considerations

- The face recognition engine is CPU-intensive
- Consider scaling horizontally with multiple instances behind a load balancer
- For high-traffic deployments, consider implementing a queue system for face recognition tasks

## Troubleshooting

### Common Issues:

1. **Import errors**: Make sure all dependencies are installed
2. **Camera access**: In containerized environments, camera access isn't available
3. **Memory issues**: Face recognition can be memory-intensive with large datasets

### Logs:

Check application logs for errors:
- Local: Standard output
- Cloud platforms: Platform-specific logging dashboard