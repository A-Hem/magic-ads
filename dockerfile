
# 1. Base Image: Use an official Python runtime. Slim is smaller.
FROM python:3.11-slim

# 2. Set Environment Variables:
#    - Prevents Python from writing .pyc files
#    - Ensures logs are output immediately (good for containerized apps)
#    - Sets the default port Cloud Run expects (can be overridden)
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

# 3. Set Working Directory: Where the app code will live inside the container.
WORKDIR /app

# 4. Install Python Dependencies:
#    - Copy *only* requirements.txt first to leverage Docker's layer caching.
#      This layer only rebuilds if requirements.txt changes.
COPY requirements.txt .
#    - Upgrade pip and install packages listed in requirements.txt.
#    - --no-cache-dir reduces image size slightly.
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 5. Copy Application Code:
#    - Copy all files from the current directory (where Dockerfile is)
#      into the container's /app directory.
#    - This includes main.py, gemini_service.py, static/, templates/, .env (though .env shouldn't be used in production this way)
#    - IMPORTANT: Ensure your .dockerignore file excludes unnecessary files/folders
#      (like .git, __pycache__, venv) to keep the image clean and build fast.
COPY . .

# 6. Expose Port: Inform Docker that the container listens on this port.
#    Cloud Run uses the PORT environment variable primarily.
EXPOSE 8080

# 7. Define Run Command: How to start the application.
#    - Use uvicorn to run the FastAPI app defined in main.py (the 'app' instance).
#    - --host 0.0.0.0 makes the server accessible from outside the container network bridge.
#    - --port $PORT uses the environment variable set earlier (or injected by Cloud Run).
#      Using 8080 directly is also common: ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]

# --- Notes for Cloud Run ---
# - Build this image: docker build -t your-image-name .
# - Push to a registry (like Google Artifact Registry): docker push gcr.io/your-project-id/your-image-name
# - Deploy on Cloud Run, selecting the pushed image.
# - **IMPORTANT**: Configure the GEMINI_API_KEY as a secret/environment variable directly in the Cloud Run service settings.
#   DO NOT include the actual key in the Dockerfile or bake it into the image.


