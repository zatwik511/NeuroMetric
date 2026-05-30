from datetime import datetime, timezone
from flask_login import UserMixin
from app import db, login_manager


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(10), nullable=False)  # 'teacher' or 'student'
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    exams = db.relationship('Exam', backref='teacher', lazy=True,
                            foreign_keys='Exam.teacher_id')
    submissions = db.relationship('Submission', backref='student', lazy=True,
                                  foreign_keys='Submission.student_id')

    def __repr__(self):
        return f'<User {self.email} ({self.role})>'


class Exam(db.Model):
    __tablename__ = 'exams'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    time_limit_minutes = db.Column(db.Integer, nullable=False, default=60)
    is_active = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    questions = db.relationship('Question', backref='exam', lazy=True,
                                order_by='Question.order', cascade='all, delete-orphan')
    submissions = db.relationship('Submission', backref='exam', lazy=True,
                                  cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Exam {self.title}>'


class Question(db.Model):
    __tablename__ = 'questions'

    id = db.Column(db.Integer, primary_key=True)
    exam_id = db.Column(db.Integer, db.ForeignKey('exams.id'), nullable=False)
    text = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(10), nullable=False)  # 'short', 'long', 'essay'
    max_marks = db.Column(db.Integer, nullable=False, default=10)
    model_answer = db.Column(db.Text, nullable=True)
    rubric = db.Column(db.Text, nullable=True)
    order = db.Column(db.Integer, nullable=False, default=0)

    answers = db.relationship('Answer', backref='question', lazy=True,
                              cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Question {self.id} (Exam {self.exam_id})>'


class Submission(db.Model):
    __tablename__ = 'submissions'

    id = db.Column(db.Integer, primary_key=True)
    exam_id = db.Column(db.Integer, db.ForeignKey('exams.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    submitted_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    total_score = db.Column(db.Float, nullable=True)
    status = db.Column(db.String(10), default='pending')  # 'pending', 'graded', 'flagged'
    released = db.Column(db.Boolean, default=False)

    answers = db.relationship('Answer', backref='submission', lazy=True,
                              cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Submission {self.id} (Student {self.student_id}, Exam {self.exam_id})>'


class Answer(db.Model):
    __tablename__ = 'answers'

    id = db.Column(db.Integer, primary_key=True)
    submission_id = db.Column(db.Integer, db.ForeignKey('submissions.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'), nullable=False)
    answer_text = db.Column(db.Text, nullable=True)
    score = db.Column(db.Float, nullable=True)
    feedback = db.Column(db.Text, nullable=True)
    ai_flag_score = db.Column(db.Float, nullable=True)  # 0-100 probability answer is AI-generated
    paste_events = db.Column(db.Integer, default=0)
    tab_switches = db.Column(db.Integer, default=0)

    def __repr__(self):
        return f'<Answer {self.id} (Submission {self.submission_id}, Question {self.question_id})>'


class ExamEvent(db.Model):
    __tablename__ = 'exam_events'

    id = db.Column(db.Integer, primary_key=True)
    submission_id = db.Column(db.Integer, db.ForeignKey('submissions.id'), nullable=False)
    event_type = db.Column(db.String(30), nullable=False)  # 'tab_switch', 'paste', 'fullscreen_exit'
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'), nullable=True)
    metadata_ = db.Column(db.Text, nullable=True)  # JSON string for extra event data
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f'<ExamEvent {self.event_type} (Submission {self.submission_id})>'
