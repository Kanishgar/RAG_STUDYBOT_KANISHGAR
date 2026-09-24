# 🎓 StudyBot — PSG College of Technology, Sem 7
### By Kanishgar | Powered by Gemini + Qdrant + RAG

**Live:** `https://kanishgar-studybot.vercel.app`

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  PHASE 1: INGEST  (YOU run this ONCE on your laptop)        │
│                                                             │
│  data/rf/2023_qp.pdf    python ingest.py                    │
│  data/mmc/2022_qp.pdf ──────────────────►  Qdrant Cloud     │
│  data/vr/...                               (free, 1GB)      │
│  data/rdbms/...         Parse → Embed                       │
│  data/foc/...           ↓                                   │
│                     1.a → 3 marks                           │
│                     b.(i) → 6 marks                         │
│                     b.(ii) → 6 marks                        │
│                     c.(i) → 10 marks (either)               │
│                     c.(ii) → 10 marks (or)                  │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  PHASE 2: USERS CHAT  (deployed, always free)               │
│                                                             │
│  [kanishgar-studybot.vercel.app]  ←── React + Vercel (free) │
│           │                                                 │
│           ▼ REST API                                        │
│  [kanishgar-sem7-api.onrender.com] ←── FastAPI + Render free│
│           │                                                 │
│           ▼ Vector search                                   │
│  [Qdrant Cloud] ←── Free tier (1GB, forever)               │
│           │                                                 │
│           ▼ LLM generation                                  │
│  [Gemini 3.8 Flash] ←── Free tier (1M tokens/day)          │
└─────────────────────────────────────────────────────────────┘
```

---

## 📋 PSG Tech Question Paper Format

```
1.a          →  3 marks   (Part A — unit number on 'a' only)
   b.(i)     →  6 marks   (Part B — no unit prefix)
   b.(ii)    →  6 marks
   c.(i)     → 10 marks   (Either)
   c.(ii)    → 10 marks   (Or)

2.a          →  next unit (Unit 2)
   b.(i)     →  6 marks
   ...
```

> ⚠️ PSG Tech watermark ("PSGTECH" diagonal text) is automatically stripped during parsing.

---

## 🚀 Full Setup Guide

### STEP 1 — Get Free API Keys

#### A. Gemini API Key (Google AI Studio)
1. Go to → https://aistudio.google.com/app/apikey
2. Click **"Create API Key"** → Copy it

#### B. Qdrant Cloud (Vector Database)
1. Go to → https://cloud.qdrant.io
2. Sign up for free
3. Click **"Create Cluster"** → choose **Free tier** → Region: `US East` or `EU`
4. Copy your **Cluster URL** and **API Key**

---

### STEP 2 — Local Setup & Ingest

```bash
# Navigate to project
cd sem7-rag-chatbot/backend

# Create virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Create your .env file
copy .env.example .env
```

Edit `.env`:
```env
GEMINI_API_KEY=AIza...your_key
QDRANT_URL=https://abc123.us-east4-0.gcp.cloud.qdrant.io
QDRANT_API_KEY=your_qdrant_api_key
```

Drop your PSG Tech question papers:
```
backend/data/
  rf/     ← RF Passive & Active Circuits PDFs
  mmc/    ← Multimedia Computing PDFs
  vr/     ← Virtual Reality PDFs
  rdbms/  ← RDBMS PDFs
  foc/    ← Fiber Optic Communication PDFs
```

**Run ingestion (trains the RAG model):**
```bash
python ingest.py

# Check what was stored:
python ingest.py --stats
```

---

### STEP 3 — Deploy Backend to Render (Free)

1. Push your project to **GitHub**
2. Go to → https://render.com → Sign up → **New Web Service**
3. Connect your GitHub repo
4. Settings:
   - **Root Directory:** `backend`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Plan:** Free
5. Add Environment Variables in Render dashboard:
   - `GEMINI_API_KEY` = your key
   - `QDRANT_URL` = your Qdrant cluster URL
   - `QDRANT_API_KEY` = your Qdrant key
6. Deploy → your API URL: `https://kanishgar-sem7-api.onrender.com`

---

### STEP 4 — Deploy Frontend to Vercel (Free)

1. Go to → https://vercel.com → Sign up → **New Project**
2. Connect your GitHub repo
3. Settings:
   - **Root Directory:** `frontend`
   - **Framework:** Vite
4. Add Environment Variable:
   - `VITE_API_URL` = `https://kanishgar-sem7-api.onrender.com`
5. **Project Name:** `kanishgar-studybot`
6. Deploy → Your site: **`https://kanishgar-studybot.vercel.app`** 🎉

---

## 🛠️ Tech Stack (100% Free)

| Layer | Tool | Free Tier |
|---|---|---|
| LLM | Gemini 3.8 Flash | 1M tokens/day |
| Embeddings | Gemini embedding-001 | Free |
| Vector DB | **Qdrant Cloud** | 1GB, forever free |
| Backend | FastAPI → **Render** | 750 hrs/month |
| Frontend | React → **Vercel** | 100GB bandwidth |
| PDF parsing | pdfplumber | Open source |

---

## 📚 Subjects (Sem 7 — PSG Tech)

| ID | Subject | Units |
|---|---|---|
| `rf` | RF Passive & Active Circuits | 5 |
| `mmc` | Multimedia Computing | 5 |
| `vr` | Virtual Reality | 5 |
| `rdbms` | RDBMS | 5 |
| `foc` | Fiber Optic Communication | 5 |

---

## 🔮 Future
- [ ] Add Sem 6 / Sem 8 support
- [ ] Show answer sources (which year QP)
- [ ] Dark mode
- [ ] Download answer as PDF
