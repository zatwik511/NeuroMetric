Deployment notes (automated):

Files added:
- Dockerfile: containerizes the Flask app using Gunicorn and Python 3.11-slim
- wsgi.py: WSGI entrypoint exposing `app` for Gunicorn
- .dockerignore: excludes local artifacts
- cloudbuild.yaml: Cloud Build steps to build, push, and deploy to Cloud Run

Quick deploy (local gcloud auth required):

1. Ensure gcloud is authenticated and project set:
   gcloud auth login
   gcloud config set project YOUR_PROJECT_ID

2. Build & push image (Cloud Build):
   gcloud builds submit --tag gcr.io/$(gcloud config get-value project)/neurometric

3. Deploy to Cloud Run:
   gcloud run deploy neurometric --image gcr.io/$(gcloud config get-value project)/neurometric \
     --region europe-west1 --platform managed --allow-unauthenticated \
     --set-env-vars SECRET_KEY=placeholder,GEMINI_API_KEY=placeholder,DATABASE_URL=sqlite:///exam_portal.db

After deploy: update SECRET_KEY and GEMINI_API_KEY in the Cloud Run service's Environment Variables (console or gcloud).
