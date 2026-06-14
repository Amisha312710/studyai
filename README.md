# StudyAI 

> Your intelligent ML & NLP study companion — built for engineering students who want to actually understand, not just memorize.

## What is StudyAI?

StudyAI is a full-stack AI-powered study platform built specifically for Machine Learning and NLP students. It replaces passive reading with active, personalized learning — combining smart content generation, adaptive quizzes, voice tutoring, and an AI-planned weekly scheduler.

This is **Version 1.0** — a fully working first draft with five core modules.

---

## Features

### ⚡ Dashboard
- Personalized welcome with exam countdown timers
- Daily study streak tracking
- Today's sessions linked to scheduler
- AI-generated daily study strategy via Groq LLaMA

### 📖 Study Studio
- Upload your own lecture notes (PDF/TXT)
- AI generates Detailed Notes, Flashcards, Quick Summary, or In-depth Explanation
- Content grounded in your uploaded material
- 38 topics across ML and NLP

### 🧪 Quiz Mode
- AI-generated MCQs with adjustable difficulty and question count
- Per-question countdown timer
- Instant answer feedback with explanations
- Animated score ring on results screen
- Full answer review

### 📅 Study Scheduler
- AI builds a personalized 7-day study plan
- Manual schedule building without AI
- Mark sessions as done with live progress tracking
- Browser reminders for upcoming sessions
- Linked to dashboard — today's sessions shown on home

### 🤖 AI Voice Tutor
- Ask anything in English or Hindi
- Voice input via Groq Whisper transcription
- Neural TTS responses
- Hinglish support
- Conversation memory across the session
- Grounded in your uploaded notes

---

## Tech Stack

**Frontend**
- Vanilla HTML, CSS, JavaScript
- No framework, no bundler

**Backend**
- Python + Flask
- Flask-CORS
- python-dotenv

**AI & APIs**
- Groq API — LLaMA 3.3 70B
- Groq Whisper Large V3 Turbo — voice transcription
- ElevenLabs / Microsoft Edge TTS — text-to-speech

---

## Project Structure
studyai/

├── backend/

│   ├── server.py

│   ├── requirements.txt

│   └── routes/

│       ├── onboarding.py

│       ├── dashboard.py

│       ├── study.py

│       ├── uploads.py

│       ├── quiz.py

│       ├── tutor.py

│       └── scheduler.py

├── frontend/

│   └── index.html

└── README.md
---

## Getting Started

### Prerequisites
- Python 3.11+
- Groq API key — free at [console.groq.com](https://console.groq.com)

### Installation

```bash
git clone https://github.com/Amisha312710/studyai.git
cd studyai
pip install -r backend/requirements.txt
```

### Environment Setup

Create a `.env` file in `backend/`:

```env
GROQ_API_KEY=your_groq_api_key_here
ELEVENLABS_API_KEY=your_elevenlabs_key_here
```

### Running

**Terminal 1 — Backend:**
```bash
cd backend
export $(cat .env | xargs) && python3 server.py
```

**Terminal 2 — Frontend:**
```bash
cd frontend
python3 -m http.server 8080
```

Open `http://localhost:8080` 🚀

---

## Roadmap

### V2 — Smarter Learning
- [ ] Personalized ML/NLP learning roadmap
- [ ] Progress tracking — "You are 54% through the ML path"
- [ ] Prerequisite-aware topic unlocking
- [ ] Wikipedia → Teacher mode (Feynman-style explanations)

### V3 — Visual Learning
- [ ] Interactive visualizations for Decision Trees, Neural Networks, Gradient Descent, CNNs
- [ ] "Teach Me Like..." buttons — ELI5 / College / Interview / Math / Analogy
- [ ] Confusion Detector — regenerate only the confusing section

### V4 — Platform RAG Assistant
- [ ] Platform-wide AI assistant over your entire study history
- [ ] Answers "What did I study last week?" or "Where am I weakest?"
- [ ] Full RAG over uploaded notes, quiz history, and scheduler data

---

## License

MIT — free to use, modify, and build on.

---

*StudyAI — from a summarizer to a teacher. That's where the magic is.* 🧠
