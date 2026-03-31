# 🚀 Deployment Guide: KPCL on Render.com

This guide provides step-by-step instructions for deploying your project on **Render.com** as two separate services: a **Web Service** for the backend and a **Static Site** for the frontend.

## 🏗️ Step 1: Deploying the Backend (Web Service)

As seen in your screenshot:
- **Name**: `kpcl-backend`
- **Source Code**: Select `adeebanoorr/Demand-Forecasting-for-spare-parts`.
- **Runtime**: Select **Docker**.
- **Plan**: Select **Free** (or *Starter* for more RAM).
- **Environment Variables**: Add `PORT` = `8000`.

Render will automatically see your root `Dockerfile` and start the backend.

---

## 🖼️ Step 2: Deploying the Frontend (Static Site)

1. Go to the Render Dashboard and click **New+** -> **Static Site**.
2. **Source Code**: Select the same repository.
3. **Name**: `kpcl-frontend`
4. **Root Directory**: `frontend`
5. **Build Command**: `npm install && npm run build`
6. **Publish Directory**: `dist`
7. **Environment Variables**:
   - Add `VITE_API_URL` = `https://your-backend-url.onrender.com/api` (Replace with your actual backend URL from Step 1).

---

## 🔗 Step 3: Unified Routing (Alternative)

Instead of manual setup, you can use the **Render Blueprint** file (`render.yaml`) I've added to your project:
1. Go to the Render Dashboard and click **New+** -> **Blueprint**.
2. Connect your repository.
3. Render will automatically detect the `render.yaml` and create both services for you.

### 🛡️ Why the `_redirects` file is important:
I've added a `frontend/public/_redirects` file to your project. This is required by Render to handle Single-Page Application (SPA) routing, so refreshing the page won't result in a 404 error.

---

## 🔄 Maintenance & Updates

Any time you `git push` to your `main` branch, Render will automatically rebuild and redeploy your backend and frontend services.
