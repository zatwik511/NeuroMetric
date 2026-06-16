from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app import db, bcrypt
from app.models import User, Organization, Course, Subject

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@auth_bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('auth.dashboard_redirect'))
    return redirect(url_for('auth.login'))


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('auth.dashboard_redirect'))

    preset_role = request.values.get('role')
    if preset_role not in ('teacher', 'student'):
        preset_role = None

    def render_form():
        schools = Organization.query.filter_by(org_type='school').order_by(Organization.name).all()
        universities = Organization.query.filter_by(org_type='university').order_by(Organization.name).all()
        subjects = Subject.query.order_by(Subject.min_standard, Subject.name).all()

        courses_by_org = {}
        for uni in universities:
            courses_by_org[uni.id] = [
                {'id': c.id, 'name': c.name, 'num_semesters': c.num_semesters}
                for c in Course.query.filter_by(organization_id=uni.id).order_by(Course.name).all()
            ]
        subjects_data = [
            {'id': s.id, 'name': s.name, 'min_standard': s.min_standard, 'max_standard': s.max_standard}
            for s in subjects
        ]

        return render_template('auth/register.html',
                               schools=schools, universities=universities,
                               courses_by_org=courses_by_org, subjects_data=subjects_data,
                               preset_role=preset_role)

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        role = request.form.get('role', '')
        org_type = request.form.get('org_type', '')

        if not all([name, email, password, role]) or role not in ('teacher', 'student'):
            flash('Name, email, password, and role are all required.', 'danger')
            return render_form()

        if org_type not in ('school', 'university'):
            flash('Please choose School or University.', 'danger')
            return render_form()

        if User.query.filter_by(email=email).first():
            flash('An account with that email already exists.', 'danger')
            return render_form()

        organization_id = request.form.get('organization_id', type=int)
        organization = Organization.query.filter_by(id=organization_id, org_type=org_type).first()
        if not organization:
            flash('Please select a valid organization.', 'danger')
            return render_form()

        standard = None
        course_id = None
        semester = None
        subject_ids = []

        if org_type == 'school':
            standard = request.form.get('standard', type=int)
            if not standard or not (1 <= standard <= 12):
                flash('Please select a valid standard (1-12).', 'danger')
                return render_form()

            if role == 'student':
                subject_ids = request.form.getlist('subject_ids', type=int)
                if not subject_ids:
                    flash('Please select at least one subject.', 'danger')
                    return render_form()
                subjects = Subject.query.filter(
                    Subject.id.in_(subject_ids),
                    Subject.min_standard <= standard,
                    Subject.max_standard >= standard
                ).all()
                if len(subjects) != len(subject_ids):
                    flash('One or more selected subjects are not valid for that standard.', 'danger')
                    return render_form()
        else:
            course_id = request.form.get('course_id', type=int)
            course = Course.query.filter_by(id=course_id, organization_id=organization.id).first()
            if not course:
                flash('Please select a valid course.', 'danger')
                return render_form()

            semester = request.form.get('semester', type=int)
            if not semester or not (1 <= semester <= course.num_semesters):
                flash('Please select a valid semester for that course.', 'danger')
                return render_form()

        password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
        user = User(name=name, email=email, password_hash=password_hash, role=role,
                   organization_id=organization.id, standard=standard,
                   course_id=course_id, semester=semester)
        if org_type == 'school' and role == 'student':
            user.subjects = Subject.query.filter(Subject.id.in_(subject_ids)).all()

        db.session.add(user)
        db.session.commit()

        flash('Account created! Please log in.', 'success')
        return redirect(url_for('auth.login', role=role))

    return render_form()


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('auth.dashboard_redirect'))

    role = request.args.get('role')
    if role not in ('teacher', 'student'):
        role = None

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        user = User.query.filter_by(email=email).first()
        if user and bcrypt.check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('auth.dashboard_redirect'))

        flash('Invalid email or password.', 'danger')

    return render_template('auth/login.html', role=role)


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/dashboard')
@login_required
def dashboard_redirect():
    if current_user.role == 'teacher':
        return redirect(url_for('teacher.dashboard'))
    return redirect(url_for('student.dashboard'))
