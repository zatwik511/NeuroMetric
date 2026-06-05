# AI Exam Portal

A full-stack web application for conducting AI-powered subjective exams. Teachers create and publish exams; students take them with anti-cheating monitoring; Google Gemini grades written answers automatically; teachers review, override, and release results.

---

## Features

### For Teachers
- Create exams with title, subject, and time limit
- Build question sets (short / long / essay) with model answers and rubrics
- Publish / unpublish exams at any time
- AI grades all pending submissions in one click using Google Gemini
- Per-submission review: student answers vs. model answers, AI scores, AI feedback
- Override any AI score before releasing to students
- Approve & Release results to individual students
- Suspicion dashboard showing tab switches, paste events, AI-generated text probability, and cross-student similarity flags
- Results overview table with sort by score or suspicion, exportable to CSV

### For Students
- View all active exams from their dashboard
- Take exams with a live countdown timer; auto-submits on expiry
- See result score and per-question AI feedback once teacher approves

### Anti-Cheating (Stage 5)
- Tab / window switch tracking
- Paste event detection per question
- Typing speed anomaly detection (>50 chars in <500 ms)
- Fullscreen enforcement with exit logging
- Right-click disabled during exam
- Cross-student cosine similarity check (TF-IDF); flags pairs above 85% similarity

### AI Grading (Stage 6)
- Google Gemini 1.5 Flash grades each answer against the model answer and rubric
- Returns score, 2–3 sentence feedback, and confidence level
- Separately estimates probability (0–100%) that the answer was AI-generated

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11+, Flask 3.1 |
| Database | SQLite via Flask-SQLAlchemy |
| Auth | Flask-Login + Flask-Bcrypt |
| AI Grading | Google Gemini (`google-genai`) |
| Similarity | scikit-learn (TF-IDF + cosine similarity) |
| Frontend | Bootstrap 5.3, Bootstrap Icons |

---

## Local Setup

### 1. Clone and install

```bash
git clone <repo-url>
cd "Subjective answers evalutaion"
pip install -r requirements.txt
```

### 2. Configure environment

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

```
SECRET_KEY=your-secret-key-here
GEMINI_API_KEY=your-google-gemini-api-key
```

Get a free Gemini API key at [aistudio.google.com](https://aistudio.google.com).

### 3. Run

```bash
python run.py
```

The app starts at `http://127.0.0.1:5000`. On first run, the database is created and two test accounts are seeded:

| Role | Email | Password |
|---|---|---|
| Teacher | teacher@test.com | teacher123 |
| Student | student@test.com | student123 |

---

## How It Works

### Grading Pipeline

1. Teacher clicks **Grade** (single) or **Grade All Pending** (batch) on the submissions page.
2. For each answer, the app sends a structured prompt to Gemini containing the question text, model answer, rubric, max marks, and student answer.
3. Gemini returns a JSON object: `{ score, feedback, confidence }`.
4. A second prompt asks Gemini to estimate the probability (0–100) that the answer was AI-generated.
5. Scores are summed and the submission is marked `graded`.
6. Teacher reviews scores in the suspicion dashboard, optionally overrides them, then clicks **Approve & Release**.

### Anti-Cheating Pipeline

| Signal | How detected | Where stored |
|---|---|---|
| Tab switch | `visibilitychange` + `blur` JS events | `ExamEvent` table; aggregated to `Answer.tab_switches` |
| Paste | `paste` event per textarea | `ExamEvent` table; aggregated to `Answer.paste_events` |
| Typing anomaly | >50 chars added in <500 ms | `ExamEvent` table |
| Fullscreen exit | Fullscreen API | `ExamEvent` table |
| Cross-student similarity | TF-IDF cosine similarity ≥ 0.85 on any question pair | Sets `Submission.status = 'flagged'` |

Suspicion levels in the teacher dashboard are computed as:
- **Flagged** — similarity triggered, or AI score >70%, or >5 tab switches, or >3 pastes
- **Review** — AI score ≥30%, or ≥3 tab switches, or ≥2 pastes
- **Clean** — everything below the above thresholds

---

## Project Structure

```
app/
├── __init__.py          # App factory, error handlers
├── models.py            # SQLAlchemy models
├── grading.py           # Gemini grading + AI detection
├── routes/
│   ├── auth.py          # Login, register, logout
│   ├── teacher.py       # Dashboard, exam builder, grading, results
│   ├── student.py       # Dashboard, exam taking, result view
│   └── exam.py          # Anti-cheating event logging endpoint
└── templates/
    ├── base.html
    ├── auth/
    ├── teacher/
    ├── student/
    └── errors/
```
