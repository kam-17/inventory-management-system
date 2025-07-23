from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Home page - redirect to appropriate dashboard based on user role"""
    if current_user.is_authenticated:
        # Redirect to role-specific dashboard
        if current_user.has_role('SUPER_ADMIN'):
            return redirect(url_for('admin.dashboard'))
        elif current_user.has_role('ADMIN'):
            return redirect(url_for('admin.dashboard'))
        elif current_user.has_role('OFFICE'):
            return redirect(url_for('office.dashboard'))
        elif current_user.has_role('STORE'):
            return redirect(url_for('store.dashboard'))
        elif current_user.has_role('SERVICE_ENTRY'):
            return redirect(url_for('service.dashboard'))
        else:
            return redirect(url_for('auth.login'))
    else:
        return redirect(url_for('auth.login'))

@main_bp.route('/dashboard')
@login_required
def dashboard():
    """Generic dashboard route"""
    return redirect(url_for('main.index'))

@main_bp.route('/profile')
@login_required
def profile():
    """User profile page"""
    return render_template('auth/profile.html', user=current_user)

@main_bp.route('/help')
def help():
    """Help page"""
    return render_template('base/help.html')

@main_bp.route('/about')
def about():
    """About page"""
    return render_template('base/about.html')