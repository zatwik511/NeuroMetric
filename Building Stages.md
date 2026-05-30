# Building Stages — AI Exam Portal

Each stage below is a self-contained prompt to be given to Claude when ready to implement that stage.
Complete and test each stage before moving to the next.

---

## Stage 1 — Project Restructure & Database Foundation

```
We are rebuilding the Subjective Answer Evaluation app into a full AI-powered exam portal.

The current project is at: c:\Users\satwi\Documents\Work\Projects\Serious\Subjective answers evalutaion

Tasks for this stage:
1. Restructure the project into a clean Flask application layout:
   - app/__init__.py (app factory)
   - app/models.py (database models)
   - app/routes/ (split into auth.py, teacher.py, student.py, exam.py)
   - app/templates/ (organised by role: auth/, teacher/, student/)
   - app/static/ (keep existing CSS/JS)
   - config.py
   - run.py (entry point)

2. Set up SQLAlchemy with SQLite (db.sqlite3) with the following models:
   - User (id, name, email, password_hash, role: 'teacher'|'student', created_at)
   - Exam (id, title, subject, teacher_id, time_limit_minutes, is_active, created_at)
   - Question (id, exam_id, text, type: 'short'|'long'|'essay', max_marks, model_answer, rubric, order)
   - Submission (id, exam_id, student_id, submitted_at, total_score, status: 'pending'|'graded'|'flagged')
   - Answer (id, submission_id, question_id, answer_text, score, feedback, ai_flag_score, paste_events, tab_switches)

3. Install required packages and generate requirements.txt:
   flask, flask-sqlalchemy, flask-login, flask-bcrypt, python-dotenv

4. Create a .env file template (.env.example) with: SECRET_KEY, DATABASE_URL

5. Delete the old app.py, tester.py, templates/app1.py and all old templates.
   Keep: static/ folder (CSS, JS, images), reference.txt, test.txt for reference.

Do not build any UI yet. Just the structure, models, and database initialisation.
Verify by running run.py and confirming the database tables are created.
```

---

## Stage 2 — Authentication System (Teacher & Student Login)

```
We are building Stage 2 of the AI Exam Portal.
The project structure and database models from Stage 1 are already in place.
Project location: c:\Users\satwi\Documents\Work\Projects\Serious\Subjective answers evalutaion

Tasks for this stage:
1. Implement full authentication using Flask-Login and Flask-Bcrypt:
   - Register route: /auth/register (name, email, password, role selection: teacher/student)
   - Login route: /auth/login (email, password)
   - Logout route: /auth/logout
   - Redirect teachers to /teacher/dashboard after login
   - Redirect students to /student/dashboard after login
   - Protect all teacher routes with @login_required + role check
   - Protect all student routes with @login_required + role check

2. Build the following minimal templates (clean Bootstrap 5, no placeholder pages):
   - auth/register.html
   - auth/login.html
   - teacher/dashboard.html (just a welcome message and navbar for now)
   - student/dashboard.html (just a welcome message and navbar for now)

3. Seed the database with one test teacher and one test student account on first run.
   Print credentials to the console on startup if they don't exist yet.

Verify by: registering a new user, logging in as teacher, logging in as student,
confirming role-based redirects work, and confirming protected routes block the wrong role.
```

---

## Stage 3 — Teacher Dashboard: Exam & Question Builder

```
We are building Stage 3 of the AI Exam Portal.
Auth system from Stage 2 is in place. Teachers can log in and reach their dashboard.
Project location: c:\Users\satwi\Documents\Work\Projects\Serious\Subjective answers evalutaion

Tasks for this stage:
1. Teacher can create an exam:
   - Form: title, subject, time limit (minutes)
   - Exam is saved as inactive (is_active=False) until explicitly published

2. Teacher can add questions to an exam:
   - Form per question: question text, type (short/long/essay), max marks, model answer, rubric
   - Questions can be reordered (drag or up/down buttons)
   - Questions can be deleted

3. Teacher can publish/unpublish an exam (toggle is_active)

4. Teacher dashboard shows:
   - List of their exams with status (Draft / Live)
   - Number of submissions per exam
   - Link to view results for each exam

5. Templates to build:
   - teacher/exams.html (list of exams)
   - teacher/create_exam.html (exam creation form)
   - teacher/edit_exam.html (add/edit/delete questions)
   - teacher/exam_detail.html (submissions list for one exam)

Verify by: creating an exam, adding 3 questions of different types,
publishing it, and confirming it appears as Live.
```

---

## Stage 4 — Student Dashboard: Exam Taking Interface

```
We are building Stage 4 of the AI Exam Portal.
Teachers can create and publish exams. Students can log in.
Project location: c:\Users\satwi\Documents\Work\Projects\Serious\Subjective answers evalutaion

Tasks for this stage:
1. Student dashboard shows all currently active (published) exams available to them.

2. Student can start an exam:
   - Show all questions on one page with textarea fields per question
   - Show a countdown timer (based on exam time_limit_minutes) in the corner
   - When timer hits zero, auto-submit whatever is filled in

3. On submission:
   - Save all answers to the Answer table
   - Create a Submission record with status='pending'
   - Redirect to a "Submitted successfully" confirmation page
   - Prevent re-submission (if submission exists for this student+exam, show result instead)

4. Templates to build:
   - student/dashboard.html (available exams list)
   - student/take_exam.html (exam interface with timer)
   - student/submitted.html (confirmation page)

Verify by: logging in as student, opening an active exam, filling answers,
submitting, and confirming the submission is saved in the database.
```

---

## Stage 5 — Anti-Cheating Detection System

```
We are building Stage 5 of the AI Exam Portal.
Students can take and submit exams. Answers are stored in the database.
Project location: c:\Users\satwi\Documents\Work\Projects\Serious\Subjective answers evalutaion

Tasks for this stage:
1. Browser-side monitoring (add to student/take_exam.html via JavaScript):
   - Track tab/window switches: listen to visibilitychange and blur events.
     On each switch, increment a counter and POST to /exam/log_event with {type: 'tab_switch', question_id, timestamp}
   - Track paste events: listen to paste event on each textarea.
     Log {type: 'paste', question_id, char_count, timestamp} to the same endpoint.
   - Track typing speed: on each textarea, record first keystroke timestamp and
     monitor for suspiciously large jumps in character count (>50 chars in <500ms = flag).
   - Disable right-click on the exam page.
   - Force fullscreen on exam start using the Fullscreen API.
     Log a fullscreen_exit event if the student exits fullscreen.

2. Server-side event logging:
   - POST /exam/log_event endpoint: saves events to a JSON column or
     a new ExamEvent table (submission_id, event_type, question_id, metadata, timestamp)
   - On submission, aggregate events per answer: count paste_events and tab_switches,
     save to the Answer table columns.

3. Cross-student similarity check (runs after all answers are submitted):
   - After each new submission, run cosine similarity (TF-IDF) between this student's
     answers and all other students' answers for the same questions.
   - If similarity > 0.85 for any question pair, flag both submissions as status='flagged'
     and record which question and which student pair triggered it.

Verify by: taking an exam, switching tabs several times, pasting text into an answer,
then checking the database confirms events were logged and aggregated on the Answer record.
```

---

## Stage 6 — LLM Grading Engine

```
We are building Stage 6 of the AI Exam Portal.
Anti-cheating events are logged. Submissions are stored with status='pending'.
Project location: c:\Users\satwi\Documents\Work\Projects\Serious\Subjective answers evalutaion

Tasks for this stage:
1. Integrate the Anthropic Claude API (claude-haiku-4-5 for cost efficiency) for grading.
   Add ANTHROPIC_API_KEY to .env.

2. Build a grading function grade_answer(question, answer_text) that sends this prompt to Claude:

   "You are an exam grader. Grade the following student answer.
    Question: {question.text}
    Model Answer: {question.model_answer}
    Rubric: {question.rubric}
    Max Marks: {question.max_marks}
    Student Answer: {answer_text}

    Respond in this exact JSON format:
    {
      "score": <number between 0 and max_marks>,
      "feedback": "<2-3 sentence explanation of what was correct, partially correct, and missing>",
      "confidence": "<high|medium|low>"
    }"

3. Build a grading pipeline:
   - POST /teacher/grade/<submission_id> triggers grading for all answers in a submission
   - Or, add a "Grade All Pending" button on the teacher dashboard that batches all
     ungraded submissions for an exam
   - After grading, sum all answer scores into Submission.total_score
   - Set Submission.status = 'graded'

4. Add AI-generated text detection:
   - After grading, send the student's answer to the Claude API with a second prompt asking
     it to estimate the probability (0-100) that this text was AI-generated.
   - Save the result to Answer.ai_flag_score.

Verify by: submitting a test answer, triggering grading, and confirming the Answer record
has a score, feedback, and ai_flag_score populated.
```

---

## Stage 7 — Teacher Results & Suspicion Dashboard

```
We are building Stage 7 of the AI Exam Portal.
LLM grading is complete. Submissions have scores, feedback, and flag data.
Project location: c:\Users\satwi\Documents\Work\Projects\Serious\Subjective answers evalutaion

Tasks for this stage:
1. Build the teacher results view for a single submission (teacher/submission_detail.html):
   - Student name and exam title
   - Per-question breakdown: question text, student answer, model answer,
     AI score, AI feedback, teacher override score input
   - Suspicion report panel showing:
       - Tab switches count
       - Paste events count + which questions
       - Typing speed anomalies
       - AI-generated text probability per answer (colour coded: green <30%, amber 30-70%, red >70%)
       - Cross-student similarity flag (if triggered, show which student and which question)
   - Overall suspicion level badge: Clean / Review / Flagged
   - "Approve & Release" button to finalise the grade and make it visible to the student
   - "Override Score" fields so the teacher can adjust any AI score before releasing

2. Build the exam results overview (teacher/exam_results.html):
   - Table of all submissions: student name, total score, status, suspicion badge
   - Sort by score or suspicion level
   - Export to CSV button (scores + flags)

Verify by: opening a graded submission as teacher, reviewing the suspicion report,
overriding one score, and approving the result.
```

---

## Stage 8 — Student Results View & Polish

```
We are building Stage 8 of the AI Exam Portal.
Teachers can review, override, and approve graded submissions.
Project location: c:\Users\satwi\Documents\Work\Projects\Serious\Subjective answers evalutaion

Tasks for this stage:
1. Student results page (student/result.html):
   - Only visible after teacher has approved the submission
   - Show: total score, per-question score, AI feedback per answer
   - Do NOT show the suspicion report to the student

2. Student dashboard updates:
   - Show exam status per exam: Not Started / Submitted / Result Available
   - If result is available, show score and link to full result

3. General UI polish across all pages:
   - Consistent navbar with role-aware links (teacher vs student)
   - Mobile responsive layout using Bootstrap 5 grid
   - Flash messages for all actions (login success, exam submitted, etc.)
   - 404 and 403 error pages

4. Write a proper README.md covering:
   - What the app does
   - How to set it up locally (pip install, .env setup, flask run)
   - Screenshots of key pages
   - How the grading and anti-cheating work (brief)

5. Final cleanup:
   - Remove all unused files and old code
   - Confirm requirements.txt is complete and accurate
   - Push all changes to GitHub

Verify by: full end-to-end walkthrough — teacher creates exam, student takes it,
teacher grades and approves, student views result. Then push to GitHub.
```

---

## Summary

| Stage | What gets built | Est. complexity |
|---|---|---|
| 1 | Project structure + database models | Low |
| 2 | Auth system (login/register, roles) | Low |
| 3 | Teacher exam & question builder | Medium |
| 4 | Student exam-taking interface + timer | Medium |
| 5 | Anti-cheating detection (browser + server) | High |
| 6 | LLM grading engine (Claude API) | Medium |
| 7 | Teacher results & suspicion dashboard | Medium |
| 8 | Student results view + final polish | Low |
