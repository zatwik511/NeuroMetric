from app import create_app, db, bcrypt
from app.models import User

app = create_app()


def seed_db():
    """Create test accounts on first run if they don't exist."""
    teacher_email = 'teacher@test.com'
    student_email = 'student@test.com'

    if not User.query.filter_by(email=teacher_email).first():
        teacher = User(
            name='Test Teacher',
            email=teacher_email,
            password_hash=bcrypt.generate_password_hash('teacher123').decode('utf-8'),
            role='teacher'
        )
        db.session.add(teacher)
        print(f'\n[SEED] Teacher account created -> {teacher_email} / teacher123')

    if not User.query.filter_by(email=student_email).first():
        student = User(
            name='Test Student',
            email=student_email,
            password_hash=bcrypt.generate_password_hash('student123').decode('utf-8'),
            role='student'
        )
        db.session.add(student)
        print(f'[SEED] Student account created -> {student_email} / student123\n')

    db.session.commit()


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        seed_db()
    app.run(debug=True)
