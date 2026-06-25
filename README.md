# 🔍 FactLens: Evidence-Grounded Verification of Claims in YouTube Videos

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge&logo=python)
![JavaScript](https://img.shields.io/badge/JavaScript-ES6+-yellow?style=for-the-badge&logo=javascript)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green?style=for-the-badge&logo=fastapi)
![Chrome Extension](https://img.shields.io/badge/Chrome-Extension-red?style=for-the-badge&logo=googlechrome)
![License](https://img.shields.io/badge/License-MIT-purple?style=for-the-badge)

**A real-time, evidence-grounded fact-checking Chrome extension that automatically detects and verifies factual claims in YouTube videos — as you watch them.**

[Overview](#-overview) • [Demo](#-demo) • [Architecture](#-architecture) • [Setup](#-setup) • [Results](#-results) • [Limitations](#-limitations)

</div>

---

## 📌 Overview

The internet is flooded with misinformation, and YouTube is no exception. Billions of videos make factual claims that viewers rarely have the time or tools to verify. **FactLens** bridges this gap.

Once enabled, FactLens runs silently in the background while you watch a YouTube video. It captures audio in real time, extracts verifiable claims using a large language model, gathers evidence from five trusted external sources, and displays a timestamped verdict — **Support**, **Contradict**, or **Inconclusive** — directly on the video page as an overlay.

No tab switching. No manual input. No interruption to your viewing experience.

---

## 🎬 Demo

> 📽️ **[Watch the Demo Video](#)** ← *(https://drive.google.com/file/d/14Pfw4NezvTIxNBZqBUxUlwtvTXDCJQNj/view?usp=sharing)*
> <p align="center">
  <img src="assets/thumbnail.png" alt="FactLens Thumbnail" width="900"/>
</p>

### What the overlay looks like:

| Claim | Timestamp | Verdict |
|-------|-----------|---------|
| There was an attempt on Putin's life that was foiled. | 31.1s | ✅ Support |
| Putin's security is good because of assassination experiences. | 21.8s | ⬜ Inconclusive |
| Putin has six layers of security. | 10.9s | ❌ Contradict |

---

## 🏗️ Architecture

FactLens follows a **client-server architecture**:

```
YouTube Page
     │
     │  Audio chunks (every 10s) + timestamp
     ▼
Chrome Extension (Frontend)
     │  background.js → content.js → popup.html
     │
     │  POST /upload  (WAV + session_id + timestamp)
     ▼
FastAPI Backend (Python)
     │
     ├── 1. Whisper Base Model         → Audio Transcription
     ├── 2. Llama 3.3 70B (Groq API)  → Claim Detection + Filtering
     ├── 3. Parallel Evidence Fetch    → Wikipedia, SerpAPI, Tavily, ArXiv, NewsAPI
     ├── 4. Evidence Ranking           → Sequence similarity, top-3 snippets
     └── 5. Llama 3.3 70B             → Verdict Generation (Support / Contradict / Inconclusive)
     │
     │  JSON response (claim, verdict, explanation, timestamp)
     ▼
Overlay rendered on YouTube page
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Chrome Extension | Manifest V3, HTML, CSS, JavaScript |
| Speech-to-Text | OpenAI Whisper (base model) |
| Claim Detection & Verdict | Llama 3.3 70B Versatile via Groq API |
| Evidence Sources | Wikipedia, SerpAPI, Tavily, ArXiv, NewsAPI |
| Backend Framework | Python, FastAPI, Uvicorn |
| Tunneling | Ngrok |
| Evaluation Dataset | FEVER (Fact Extraction and VERification) |

---

## ⚙️ Setup

### Prerequisites

- Python 3.10 or higher
- Google Chrome browser
- A free [Ngrok account](https://ngrok.com)
- API keys for: Groq, SerpAPI, Tavily, NewsAPI

---

### Step 1 — Clone the Repository

```bash
git clone https://github.com/YOURUSERNAME/FactLens.git
cd FactLens
```

---

### Step 2 — Set Up the Backend

#### Install dependencies

```bash
pip install -r requirements.txt
```

#### Create your `.env` file

Create a file named `.env` in the `backend/` folder:

```env
GROQ_API_KEY=your_groq_api_key_here
SERPAPI_KEY=your_serpapi_key_here
TAVILY_API_KEY=your_tavily_api_key_here
NEWS_API_KEY=your_newsapi_key_here
```

> 🔑 **Where to get your keys:**
> - Groq API → [console.groq.com](https://console.groq.com)
> - SerpAPI → [serpapi.com](https://serpapi.com)
> - Tavily → [tavily.com](https://tavily.com)
> - NewsAPI → [newsapi.org](https://newsapi.org)

#### Start the backend server

```bash
cd backend
uvicorn backend:app --reload --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

---

### Step 3 — Expose the Backend with Ngrok

Open a **new terminal** and run:

```bash
ngrok http 8000
```

Copy the HTTPS URL that appears, for example:
```
https://abc123xyz.ngrok-free.app
```

---

### Step 4 — Update the Extension with your Ngrok URL

Open `extension/background.js` and replace the backend URL:

```javascript
// Find this line:
const BACKEND_URL = "https://YOUR_NGROK_URL_HERE/upload";

// Replace with your actual ngrok URL, e.g.:
const BACKEND_URL = "https://abc123xyz.ngrok-free.app/upload";
```

---

### Step 5 — Load the Chrome Extension

1. Open Chrome and go to: `chrome://extensions`
2. Toggle **Developer Mode** ON (top right corner)
3. Click **"Load Unpacked"**
4. Select the `extension/` folder from this repository
5. The FactLens icon will appear in your Chrome toolbar

---

### Step 6 — Run FactLens

1. Go to any YouTube video
2. Click the **FactLens icon** in your Chrome toolbar
3. Click **"Start Capture"**
4. Watch the overlay appear on the top right of the video with verified claims

> ⚠️ Make sure both the **backend server** and **ngrok** are running before clicking Start Capture.

---

## 📊 Results

The verification pipeline was evaluated on **1,000 claims** from the [FEVER dataset](https://fever.ai/) (labelled development split).

| Verdict Category | Correct | Total | Accuracy |
|-----------------|---------|-------|----------|
| Support | 311 | 331 | 94.0% |
| Contradict | 285 | 312 | 91.3% |
| Inconclusive | 334 | 357 | 93.6% |
| **Overall** | **930** | **1000** | **93.0%** |

> Most errors were claims assigned **Inconclusive** instead of Support/Contradict — the preferred failure mode for a fact-checking system, as it avoids misleading the viewer with a wrong confident verdict.

---

## 📁 Project Structure

```
FactLens/
├── extension/                  # Chrome Extension (Frontend)
│   ├── manifest.json           # Extension configuration (Manifest V3)
│   ├── background.js           # Service worker: coordinates extension ↔ backend
│   ├── content.js              # Injected into YouTube: captures audio, renders overlay
│   ├── popup.html              # Extension popup UI
│   └── popup.js                # Start/Stop capture logic
│
├── backend/                    # Python Backend
│   ├── backend.py              # FastAPI app: main endpoint
│   ├── claim_detection.py      # Whisper transcription + Llama claim extraction
│   ├── test.py                 # Unit tests
│   └── .env                    # API keys (not committed)
│
├── evaluation/
│   └── evaluation.ipynb        # FEVER dataset evaluation notebook
│
├── report/
│   └── FactLens_Report.pdf     # Full project report (NIT Trichy, 2026)
│
├── demo/                       # Demo video / screenshots
├── .env.example                # Template for required API keys
├── .gitignore
├── requirements.txt
└── README.md
```

---

## 🔑 Environment Variables

| Variable | Description | Where to Get |
|----------|-------------|--------------|
| `GROQ_API_KEY` | LLM inference (Llama 3.3 70B) | [console.groq.com](https://console.groq.com) |
| `SERPAPI_KEY` | Google Search results | [serpapi.com](https://serpapi.com) |
| `TAVILY_API_KEY` | AI-focused web search | [tavily.com](https://tavily.com) |
| `NEWS_API_KEY` | Live news articles | [newsapi.org](https://newsapi.org) |

---

## ⚠️ Limitations

- **English only** — Whisper is configured for English; other languages are not supported
- **Near real-time** — There is a ~10 second delay as the system waits for a full audio chunk before processing
- **Audio quality** — Videos with heavy background music, multiple speakers, or poor recording may produce less accurate transcriptions
- **Local backend** — The backend must be actively running with ngrok for the extension to work
- **API rate limits** — Heavy use may occasionally cause one or more evidence sources to return no results, pushing verdicts toward Inconclusive

---

## 🚀 Future Work

- [ ] Multi-language support
- [ ] Reduce processing delay toward true real-time
- [ ] Persistent session storage (replace in-memory store)
- [ ] Publish on Chrome Web Store
- [ ] Fine-tune claim detection for domain-specific content (health, finance, politics)

---

## 📄 Report

This project was completed as part of the M.Sc. Computer Science programme at the **National Institute of Technology, Tiruchirappalli (NIT Trichy)**, 2025–2026.

**Turnitin Similarity Score: 10%**

Full report available in `report/FactLens_Report.pdf`

---

## 👤 Author

**Yuvraj Singh**
M.Sc. Computer Science, NIT Trichy (2024–2026)
📧 yuvraj.singh.nitt@gmail.com
🔗 [LinkedIn](https://www.linkedin.com/in/yuvraj-singh-37a70b2a0)



<div align="center">
Made with ❤️ at NIT Trichy
</div>
