"""
Authentication and authorization utilities for the invoice generator
"""
from functools import wraps
from flask import session, redirect, url_for, flash
import sqlite3

def get_db():
    """Get database connection"""
    db = sqlite3.connect('invoice.db')
    db.row_factory = sqlite3.Row
    return db

def login_required(f):
    """Decorator to require login for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page', 'warning')
            return redirect(url_for('login'))
        
        # Check if user is approved
        db = get_db()
        user = db.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
        db.close()
        
        if not user:
            session.clear()
            flash('User not found', 'error')
            return redirect(url_for('login'))
        
        if not user['is_approved']:
            return redirect(url_for('pending_approval'))
        
        if not user['is_active']:
            session.clear()
            flash('Your account has been deactivated', 'error')
            return redirect(url_for('login'))
        
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator to require admin privileges"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page', 'warning')
            return redirect(url_for('login'))
        
        db = get_db()
        user = db.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
        db.close()
        
        if not user or not user['is_admin']:
            flash('Admin access required', 'error')
            return redirect(url_for('index'))
        
        return f(*args, **kwargs)
    return decorated_function

def get_current_user():
    """Get current logged in user"""
    if 'user_id' not in session:
        return None
    
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    db.close()
    return user
