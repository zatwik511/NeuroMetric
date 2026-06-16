from app import create_app, db, bcrypt
from app.models import User, Organization, Course, Subject, Exam, Question

app = create_app()


def get_or_create_org(name, org_type):
    org = Organization.query.filter_by(name=name, org_type=org_type).first()
    if not org:
        org = Organization(name=name, org_type=org_type)
        db.session.add(org)
        db.session.flush()
    return org


def get_or_create_course(org, name, num_semesters):
    course = Course.query.filter_by(organization_id=org.id, name=name).first()
    if not course:
        course = Course(organization_id=org.id, name=name, num_semesters=num_semesters)
        db.session.add(course)
        db.session.flush()
    return course


def get_or_create_subject(name, min_standard, max_standard):
    subject = Subject.query.filter_by(name=name).first()
    if not subject:
        subject = Subject(name=name, min_standard=min_standard, max_standard=max_standard)
        db.session.add(subject)
        db.session.flush()
    return subject


def get_or_create_user(email, name, role, password, organization,
                       standard=None, course=None, semester=None, subjects=None):
    user = User.query.filter_by(email=email).first()
    if user:
        return user, False
    user = User(
        name=name, email=email, role=role,
        password_hash=bcrypt.generate_password_hash(password).decode('utf-8'),
        organization_id=organization.id,
        standard=standard,
        course_id=course.id if course else None,
        semester=semester
    )
    if subjects:
        user.subjects = subjects
    db.session.add(user)
    db.session.flush()
    return user, True


def get_or_create_exam(title, teacher, organization, time_limit_minutes,
                       standard=None, subject=None, course=None, semester=None,
                       questions=None):
    exam = Exam.query.filter_by(title=title, teacher_id=teacher.id).first()
    if exam:
        return exam
    exam = Exam(
        title=title, teacher_id=teacher.id, organization_id=organization.id,
        time_limit_minutes=time_limit_minutes, is_active=True,
        standard=standard, subject_id=subject.id if subject else None,
        course_id=course.id if course else None, semester=semester
    )
    db.session.add(exam)
    db.session.flush()
    for i, q in enumerate(questions or [], start=1):
        db.session.add(Question(
            exam_id=exam.id, text=q['text'], type=q['type'], max_marks=q['max_marks'],
            model_answer=q.get('model_answer'), rubric=q.get('rubric'), order=i
        ))
    return exam


def seed_db():
    """Seed organizations, courses, subjects, demo accounts, and demo exams (idempotent)."""

    # ── Organizations ──────────────────────────────────────────────────────────
    greenwood = get_or_create_org('Greenwood High School', 'school')
    sunrise = get_or_create_org('Sunrise Public School', 'school')
    dit = get_or_create_org('Delhi Institute of Technology', 'university')
    maple = get_or_create_org('Maple State University', 'university')

    # ── Courses (university only) ───────────────────────────────────────────────
    dit_cse = get_or_create_course(dit, 'B.Tech Computer Science', 8)
    get_or_create_course(dit, 'B.Tech Mechanical Engineering', 8)
    get_or_create_course(maple, 'BBA', 6)
    get_or_create_course(maple, 'B.Sc Physics', 6)

    # ── Subjects (global catalog, school only) ──────────────────────────────────
    english = get_or_create_subject('English', 1, 12)
    math = get_or_create_subject('Math', 1, 12)
    get_or_create_subject('EVS', 1, 5)
    science = get_or_create_subject('Science', 6, 8)
    get_or_create_subject('Social Studies', 6, 10)
    get_or_create_subject('Physics', 9, 12)
    get_or_create_subject('Chemistry', 9, 12)
    get_or_create_subject('Biology', 9, 12)
    get_or_create_subject('Computer Science', 6, 12)
    get_or_create_subject('History', 6, 12)
    get_or_create_subject('Geography', 6, 12)

    db.session.commit()

    # ── Demo accounts ────────────────────────────────────────────────────────────
    teacher, created = get_or_create_user(
        'teacher@test.com', 'Test Teacher', 'teacher', 'teacher123',
        organization=greenwood, standard=8
    )
    if created:
        print('[SEED] Teacher created -> teacher@test.com / teacher123 (Greenwood High, Standard 8)')

    student, created = get_or_create_user(
        'student@test.com', 'Test Student', 'student', 'student123',
        organization=greenwood, standard=8, subjects=[math, science, english]
    )
    if created:
        print('[SEED] Student created -> student@test.com / student123 (Greenwood High, Standard 8)')

    teacher2, created = get_or_create_user(
        'teacher2@test.com', 'Sunrise Teacher', 'teacher', 'teacher123',
        organization=sunrise, standard=8
    )
    if created:
        print('[SEED] Teacher created -> teacher2@test.com / teacher123 (Sunrise Public School, Standard 8)')

    student2, created = get_or_create_user(
        'student2@test.com', 'Sunrise Student', 'student', 'student123',
        organization=sunrise, standard=8, subjects=[math, english]
    )
    if created:
        print('[SEED] Student created -> student2@test.com / student123 (Sunrise Public School, Standard 8)')

    uni_teacher, created = get_or_create_user(
        'uni.teacher@test.com', 'Uni Teacher', 'teacher', 'teacher123',
        organization=dit, course=dit_cse, semester=3
    )
    if created:
        print('[SEED] Teacher created -> uni.teacher@test.com / teacher123 (DIT, B.Tech CS, Sem 3)')

    uni_student, created = get_or_create_user(
        'uni.student@test.com', 'Uni Student', 'student', 'student123',
        organization=dit, course=dit_cse, semester=3
    )
    if created:
        print('[SEED] Student created -> uni.student@test.com / student123 (DIT, B.Tech CS, Sem 3)')

    db.session.commit()

    # ── Demo exams ───────────────────────────────────────────────────────────────
    get_or_create_exam(
        'Math Basics', teacher, greenwood, time_limit_minutes=30,
        standard=8, subject=math,
        questions=[
            {'text': 'What is the value of pi (to 2 decimal places)?', 'type': 'short', 'max_marks': 5,
             'model_answer': 'Pi is approximately 3.14.', 'rubric': 'Full marks for 3.14 or close approximation.'},
            {'text': 'Explain the Pythagorean theorem with an example.', 'type': 'long', 'max_marks': 10,
             'model_answer': 'In a right triangle, a^2 + b^2 = c^2, where c is the hypotenuse. Example: 3-4-5 triangle.',
             'rubric': 'Award marks for stating the formula correctly and giving a valid example.'},
        ]
    )

    get_or_create_exam(
        'Math Basics', teacher2, sunrise, time_limit_minutes=30,
        standard=8, subject=math,
        questions=[
            {'text': 'What is the value of pi (to 2 decimal places)?', 'type': 'short', 'max_marks': 5,
             'model_answer': 'Pi is approximately 3.14.', 'rubric': 'Full marks for 3.14 or close approximation.'},
            {'text': 'Solve for x: 2x + 5 = 15.', 'type': 'short', 'max_marks': 5,
             'model_answer': 'x = 5.', 'rubric': 'Full marks for correctly isolating x and arriving at 5.'},
        ]
    )

    get_or_create_exam(
        'Data Structures Quiz', uni_teacher, dit, time_limit_minutes=45,
        course=dit_cse, semester=3,
        questions=[
            {'text': 'What is the time complexity of binary search?', 'type': 'short', 'max_marks': 5,
             'model_answer': 'O(log n).', 'rubric': 'Full marks for stating O(log n) with brief reasoning.'},
            {'text': 'Compare arrays and linked lists in terms of insertion and access time.', 'type': 'long',
             'max_marks': 10,
             'model_answer': 'Arrays offer O(1) access but O(n) insertion (except at the end); linked lists offer O(n) access but O(1) insertion at the head.',
             'rubric': 'Award marks for correctly comparing access time and insertion time for both structures.'},
        ]
    )

    db.session.commit()


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        seed_db()
    app.run(debug=True)
