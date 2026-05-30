from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from functools import wraps

teacher_bp = Blueprint('teacher', __name__, url_prefix='/teacher')


def teacher_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'teacher':
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated


@teacher_bp.route('/dashboard')
@login_required
@teacher_required
def dashboard():
    return render_template('teacher/dashboard.html')
