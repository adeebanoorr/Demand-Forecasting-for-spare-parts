# Deploying Frontend and Backend Separately

This guide explains how to deploy the KPCL Spare Part Consumption project with the backend on **Railway** and the frontend on **Vercel**.

## 1. Backend Deployment (Railway)

1.  **Create a New Service**: In Railway, create a new service from your GitHub repository.
2.  **Configure Build**: Ensure it uses the `Procfile` or the `nixpacks.toml` in the root directory.
3.  **Set Environment Variables**:
    *   `ALLOWED_ORIGINS`: Set this to your Vercel deployment URL (e.g., `https://your-app.vercel.app`). Use `*` to allow all (not recommended for production) or a comma-separated list of domains.
    *   `PORT`: Keep as `8080` (or whatever Railway provides).
4.  **Deploy**: Let Railway build and deploy the service. Note down the provided Railway URL (e.g., `https://backend-production.up.railway.app`).

## 2. Frontend Deployment (Vercel)

1.  **Create a New Project**: In Vercel, import your GitHub repository.
2.  **Root Directory**: Set the root directory to `src/webapp`.
3.  **Framework Preset**: Select **Vite**.
4.  **Set Environment Variables**:
    *   `VITE_API_URL`: Set this to your Backend Railway URL (e.g., `https://backend-production.up.railway.app/api`). **Note the `/api` suffix**.
    *   `VITE_ANALYTICS_URL`: Set this to your Backend Railway URL with the analytics path (e.g., `https://backend-production.up.railway.app/analytics/`).
5.  **Deploy**: Vercel will build your React application using the provided environment variables.

## 3. Important Notes

- **CORS**: If the frontend cannot fetch data, double-check that the `ALLOWED_ORIGINS` on Railway exactly matches your Vercel URL (including `https://`).
- **Shared Assets**: Since the frontend and backend are now separate, images or other assets must be present in the frontend's `public` directory or hosted where the frontend can access them.
- **Analytics**: The Dash analytics dashboard remains hosted on the backend (Railway) and is accessed via the `VITE_ANALYTICS_URL` in the frontend iframe.
