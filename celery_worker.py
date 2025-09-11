from app.celery_app import celery_app  # ✅ only imports the app

# 👇 This is what makes sure your tasks are registered
import app.tasks