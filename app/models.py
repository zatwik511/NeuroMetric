from datetime import datetime, timezone
from flask_login import UserMixin
from app import db, login_manager


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


student_subjects = db.Table(
    'student_subjects',
    db.Column('student_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('subject_id', db.Integer, db.ForeignKey('subjects.id'), primary_key=True)
)


class Organization(db.Model):
    __tablename__ = 'organizations'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    org_type = db.Column(db.String(10), nullable=False)  # 'school' or 'university'

    courses = db.relationship('Course', backref='organization', lazy=True,
                              cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Organization {self.name} ({self.org_type})>'


class Course(db.Model):
    __tablename__ = 'courses'

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=False)
    name = db.Column(db.String(150), nullable=False)
    num_semesters = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return f'<Course {self.name} ({self.num_semesters} sem)>'


class Subject(db.Model):
    __tablename__ = 'subjects'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    min_standard = db.Column(db.Integer, nullable=False)
    max_standard = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return f'<Subject {self.name} (std {self.min_standard}-{self.max_standard})>'


class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(10), nullable=False)  # 'teacher' or 'student'
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=True)
    standard = db.Column(db.Integer, nullable=True)  # school accounts only
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=True)  # university accounts only
    semester = db.Column(db.Integer, nullable=True)  # university accounts only

    organization = db.relationship('Organization', backref='users', lazy=True)
    course = db.relationship('Course', backref='students', lazy=True, foreign_keys=[course_id])
    subjects = db.relationship('Subject', secondary=student_subjects, lazy='subquery',
                               backref=db.backref('students_taking', lazy=True))

    exams = db.relationship('Exam', backref='teacher', lazy=True,
                            foreign_keys='Exam.teacher_id')
    submissions = db.relationship('Submission', backref='student', lazy=True,
                                  foreign_keys='Submission.student_id')

    @property
    def profile_complete(self):
        if not self.organization_id:
            return False
        if self.organization.org_type == 'school':
            if not self.standard:
                return False
            if self.role == 'student' and len(self.subjects) == 0:
                return False
            return True
        return bool(self.course_id and self.semester)

    def __repr__(self):
        return f'<User {self.email} ({self.role})>'


class Exam(db.Model):
    __tablename__ = 'exams'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    time_limit_minutes = db.Column(db.Integer, nullable=False, default=60)
    is_active = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=False)
    standard = db.Column(db.Integer, nullable=True)  # school exams only
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=True)  # school exams only
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=True)  # university exams only
    semester = db.Column(db.Integer, nullable=True)  # university exams only

    organization = db.relationship('Organization', backref='exams', lazy=True)
    subject = db.relationship('Subject', backref='exams', lazy=True)
    course = db.relationship('Course', backref='exams', lazy=True, foreign_keys=[course_id])

    questions = db.relationship('Question', backref='exam', lazy=True,
                                order_by='Question.order', cascade='all, delete-orphan')
    submissions = db.relationship('Submission', backref='exam', lazy=True,
                                  cascade='all, delete-orphan')

    @property
    def context_label(self):
        """Human-readable scope: 'Standard 8 - Math' or 'B.Tech CS - Sem 3'."""
        if self.organization.org_type == 'school':
            label = f'Standard {self.standard}'
            if self.subject:
                label += f' - {self.subject.name}'
            return label
        label = self.course.name if self.course else 'Unknown Course'
        if self.semester:
            label += f' - Sem {self.semester}'
        return label

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
