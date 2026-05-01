# Quick Start Guide

## Prerequisites Check

Before running, ensure you have:
- ✅ Python 3.9+ installed
- ✅ Ollama installed with Llama 3.1 model
- ✅ Tesseract OCR installed
- ✅ Ghostscript installed
- ✅ Node.js and npm installed (for frontend)

## Step-by-Step: Running the Application

### 1. Start Ollama Server (Required)

Open a terminal and run:
```bash
ollama serve
```

**Keep this terminal open** - Ollama must be running for the application to work.

---

### 2. Activate Python Virtual Environment

**Windows:**
```bash
venv\Scripts\activate
```

**Linux/Mac:**
```bash
source venv/bin/activate
```

You should see `(venv)` in your terminal prompt.

---

### 3. Start the FastAPI Backend Server

**Option A - Using the startup script (Windows):**
```bash
start_backend.bat
```

**Option B - Using the startup script (Linux/Mac):**
```bash
chmod +x start_backend.sh  # First time only
./start_backend.sh
```

**Option C - Manual start:**
```bash
python -m uvicorn src.api.server:app --reload --port 8000
```

**Expected output:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

**Keep this terminal open** - This is your backend server.

You can verify it's working by visiting:
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

---

### 4. Start the Next.js Frontend (New Terminal)

Open a **new terminal** and run:

```bash
cd frontend
npm install  # First time only - installs dependencies
npm run dev
```

**Expected output:**
```
> frontend@0.1.0 dev
> next dev

  ▲ Next.js 14.x.x
  - Local:        http://localhost:3000
  - Ready in X.Xs
```

**Keep this terminal open** - This is your frontend server.

---

### 5. Open the Application

Open your web browser and go to:
```
http://localhost:3000
```

You should see the Karnataka Government E-Procurement Portal interface.

---

## Quick Test

### Test as Bidder:
1. Select "Bidder" role
2. Navigate to "Document Upload Portal"
3. Click "Choose Files" and select a PDF
4. Click "Start Upload"
5. Check the Network tab in browser DevTools - you should see a POST request to `http://localhost:8000/api/bidder/upload`

### Test as Officer:
1. Select "Officer" role
2. Navigate to "Tender Configuration"
3. Upload a tender PDF
4. Check that criteria are extracted and displayed

---

## Troubleshooting

### "Could not connect to Ollama"
- Make sure Ollama is running: `ollama serve`
- Check if Llama 3.1 is installed: `ollama list`
- If not installed: `ollama pull llama3.1`

### "Port 8000 already in use"
- Stop any other process using port 8000
- Or change the port in the startup command: `--port 8001`

### "Port 3000 already in use"
- Stop any other process using port 3000
- Or Next.js will automatically suggest port 3001

### "Module not found" errors
- Make sure virtual environment is activated
- Reinstall dependencies: `pip install -r requirements.txt`

### Frontend shows "Failed to fetch"
- Make sure backend server is running on port 8000
- Check browser console for CORS errors
- Verify backend is accessible at http://localhost:8000/api/health

### "Tesseract not found"
- Install Tesseract OCR
- Add to PATH or set environment variable: `TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe`

---

## Stopping the Application

1. **Stop Frontend**: Press `Ctrl+C` in the frontend terminal
2. **Stop Backend**: Press `Ctrl+C` in the backend terminal
3. **Stop Ollama**: Press `Ctrl+C` in the Ollama terminal (optional - can keep running)

---

## Alternative: Run Streamlit UI (Legacy)

If you prefer the simpler Streamlit interface:

```bash
# Make sure virtual environment is activated
streamlit run src/ui/app.py
```

This will open at http://localhost:8501

**Note**: The Streamlit UI doesn't require the FastAPI backend or Next.js frontend.

---

## Summary of Running Services

When everything is running, you should have:

| Service | URL | Terminal |
|---------|-----|----------|
| Ollama | http://localhost:11434 | Terminal 1 |
| FastAPI Backend | http://localhost:8000 | Terminal 2 |
| Next.js Frontend | http://localhost:3000 | Terminal 3 |

**OR**

| Service | URL | Terminal |
|---------|-----|----------|
| Ollama | http://localhost:11434 | Terminal 1 |
| Streamlit UI | http://localhost:8501 | Terminal 2 |

---

## First Time Setup Checklist

- [ ] Python 3.9+ installed
- [ ] Virtual environment created: `python -m venv venv`
- [ ] Virtual environment activated
- [ ] Python dependencies installed: `pip install -r requirements.txt`
- [ ] Ollama installed
- [ ] Llama 3.1 model pulled: `ollama pull llama3.1`
- [ ] Tesseract OCR installed and in PATH
- [ ] Ghostscript installed and in PATH
- [ ] Node.js and npm installed
- [ ] Frontend dependencies installed: `cd frontend && npm install`

---

## Need Help?

- Check the full README.md for detailed installation instructions
- Check the Manual Testing Guide: `.kiro/specs/frontend-backend-integration-fix/MANUAL_TESTING_GUIDE.md`
- Check API documentation: http://localhost:8000/docs (when backend is running)
