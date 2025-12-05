# TourAI Guide - Deployment Guide

## Step 1: Push Code to GitHub

### 1a. Initialize Git and Commit Code
```powershell
cd 'C:\Users\usrajh00\Documents\GenAI\WeatherPlaceSuggestApp'

# Initialize git repository (if not done)
git init

# Add all files to staging
git add .

# Commit with a message
git commit -m "Initial commit: TourAI Guide - Elite Weather & Travel Assistant"
```

### 1b. Add Remote and Push to GitHub
```powershell
# Add the remote repository
git remote add origin https://github.com/HariKrishnaKR/WeatherPlaceSuggestApp.git

# Push code to GitHub (main branch)
git branch -M main
git push -u origin main
```

**Note:** You may need to authenticate with GitHub. If prompted:
- Use a **Personal Access Token** (recommended) instead of your password:
  - Go to https://github.com/settings/tokens
  - Create a new token with `repo` scope
  - Copy the token and paste it when prompted for password

---

## Step 2: Deploy to Render

### 2a. Create a Render Account
1. Go to https://render.com
2. Sign up (free tier available)
3. Verify your email

### 2b. Connect GitHub Repository
1. Log in to Render dashboard
2. Click **"New +"** → **"Web Service"**
3. Select **"Connect a repository"**
4. Authorize Render with your GitHub account
5. Select the `WeatherPlaceSuggestApp` repository
6. Click **"Connect"**

### 2c. Configure Service Settings
- **Name:** `touraid-guide`
- **Environment:** `Python 3`
- **Region:** `Ohio` (or choose closest to you)
- **Branch:** `main`
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `gunicorn -w 4 -b 0.0.0.0:$PORT app:app`

### 2d. Add Environment Variables
Click **"Environment"** and add these variables:

| Key | Value |
|-----|-------|
| `GEMINI_API_KEY` | Paste your actual Gemini API key |
| `GEMINI_MODEL` | `gemini-2.5-flash` |
| `PYTHON_VERSION` | `3.11.0` |

**IMPORTANT:** Keep `GEMINI_API_KEY` secret—Render won't display it after saving.

### 2e. Select Plan & Deploy
1. Choose **"Free"** plan (or paid if desired)
2. Click **"Create Web Service"**
3. Render will start building automatically:
   - Installs dependencies from `requirements.txt`
   - Starts the Flask app via `gunicorn`
   - Assigns a public URL (e.g., `https://touraid-guide.onrender.com`)

---

## Step 3: Access Your App

Once deployment is complete (takes 2-5 minutes):
- Your app will be live at: `https://touraid-guide.onrender.com`
- Share this URL with anyone to access your elite travel assistant!

---

## Troubleshooting

### Build fails with "ModuleNotFoundError"
- Check `requirements.txt` includes all dependencies
- Ensure `render.yaml` has correct Python version

### App crashes after deployment
- Check **"Logs"** tab on Render dashboard for error details
- Verify `GEMINI_API_KEY` environment variable is set correctly
- Ensure `PORT` environment variable binding in `run.py` works (it should)

### App times out
- This may happen on Render's free tier during cold starts
- Free tier suspends after 15 min of inactivity and takes ~1 min to restart
- Consider upgrading to **Starter Plan** ($7/month) for better performance

---

## Quick Reference: Commands to Run Now

```powershell
# 1. Navigate to project
cd 'C:\Users\usrajh00\Documents\GenAI\WeatherPlaceSuggestApp'

# 2. Initialize git and push
git init
git add .
git commit -m "Initial commit: TourAI Guide"
git remote add origin https://github.com/HariKrishnaKR/WeatherPlaceSuggestApp.git
git branch -M main
git push -u origin main

# 3. Then go to https://render.com and follow steps 2b-2e above
```

---

## After Deployment

- **Monitoring:** Use Render dashboard to view logs, CPU/memory usage
- **Updates:** Push new commits to GitHub → Render auto-redeploys
- **Custom Domain:** Render supports custom domains (e.g., touraid.com)
- **Scaling:** Free tier has limitations; upgrade as your user base grows

Enjoy your elite AI travel assistant on the internet! 🌍✈️
