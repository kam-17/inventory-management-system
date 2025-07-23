from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.urls import url_parse
from datetime import datetime, timedelta
from models.user import User
from extensions import db

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        remember_me = bool(request.form.get('remember_me'))
        
        if not username or not password:
            flash('Username and password are required.', 'error')
            return render_template('auth/login.html')
        
        # Find user by username or email
        user = User.query.filter(
            (User.username == username) | (User.email == username)
        ).first()
        
        if user is None:
            flash('Invalid username or password.', 'error')
            return render_template('auth/login.html')
        
        # Check if account is locked
        if user.locked_until and user.locked_until > datetime.utcnow():
            flash(f'Account is locked until {user.locked_until.strftime("%Y-%m-%d %H:%M:%S")}. Please try again later.', 'error')
            return render_template('auth/login.html')
        
        # Check if account is active
        if not user.is_active:
            flash('Your account has been deactivated. Please contact administrator.', 'error')
            return render_template('auth/login.html')
        
        # Verify password
        if not user.check_password(password):
            # Increment failed login attempts
            user.failed_login_attempts += 1
            
            # Lock account after 5 failed attempts
            if user.failed_login_attempts >= 5:
                user.locked_until = datetime.utcnow() + timedelta(minutes=30)
                flash('Too many failed login attempts. Account locked for 30 minutes.', 'error')
            else:
                remaining_attempts = 5 - user.failed_login_attempts
                flash(f'Invalid username or password. {remaining_attempts} attempts remaining.', 'error')
            
            db.session.commit()
            return render_template('auth/login.html')
        
        # Successful login
        user.failed_login_attempts = 0
        user.locked_until = None
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        login_user(user, remember=remember_me)
        
        # Log the login action
        from utils.auth import log_user_action
        log_user_action('LOGIN', 'users', user.id)
        
        flash(f'Welcome back, {user.get_full_name()}!', 'success')
        
        # Redirect to next page or dashboard
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('main.index')
        
        return redirect(next_page)
    
    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    """User logout"""
    # Log the logout action
    from utils.auth import log_user_action
    log_user_action('LOGOUT', 'users', current_user.id)
    
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Change user password"""
    if request.method == 'POST':
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        if not current_password or not new_password or not confirm_password:
            flash('All fields are required.', 'error')
            return render_template('auth/change_password.html')
        
        # Verify current password
        if not current_user.check_password(current_password):
            flash('Current password is incorrect.', 'error')
            return render_template('auth/change_password.html')
        
        # Validate new password
        if len(new_password) < 8:
            flash('New password must be at least 8 characters long.', 'error')
            return render_template('auth/change_password.html')
        
        if new_password != confirm_password:
            flash('New passwords do not match.', 'error')
            return render_template('auth/change_password.html')
        
        if current_password == new_password:
            flash('New password must be different from current password.', 'error')
            return render_template('auth/change_password.html')
        
        # Update password
        current_user.set_password(new_password)
        db.session.commit()
        
        # Log the action
        from utils.auth import log_user_action
        log_user_action('PASSWORD_CHANGE', 'users', current_user.id)
        
        flash('Password changed successfully.', 'success')
        return redirect(url_for('main.profile'))
    
    return render_template('auth/change_password.html')

@auth_bp.route('/profile')
@login_required
def profile():
    """User profile page"""
    return render_template('auth/profile.html', user=current_user)