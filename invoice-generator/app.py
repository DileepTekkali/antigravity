import os
import json
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, jsonify, send_file, session, flash
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import base64

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'invoice-generator-secret-key-2024-change-in-production')
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_db():
    db = sqlite3.connect('invoice.db')
    db.row_factory = sqlite3.Row
    return db

def init_db():
    db = get_db()
    
    # Create users table
    db.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            business_name TEXT NOT NULL,
            business_address TEXT NOT NULL,
            owner_name TEXT NOT NULL,
            mobile TEXT NOT NULL,
            gst_number TEXT,
            gst_verified INTEGER DEFAULT 0,
            is_admin INTEGER DEFAULT 0,
            is_approved INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            approved_at TIMESTAMP,
            approved_by INTEGER,
            FOREIGN KEY (approved_by) REFERENCES users (id)
        )
    ''')
    
    # Create templates table with user_id
    db.execute('''
        CREATE TABLE IF NOT EXISTS templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            business_name TEXT NOT NULL,
            business_address TEXT NOT NULL,
            owner_name TEXT NOT NULL,
            mobile TEXT NOT NULL,
            gst_number TEXT,
            default_date TEXT,
            logo_path TEXT,
            signature_path TEXT,
            stamp_upload_path TEXT,
            stamp_data TEXT,
            stamp_type TEXT,
            stamp_business_name TEXT,
            stamp_place TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Create bills table with user_id
    db.execute('''
        CREATE TABLE IF NOT EXISTS bills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            template_id INTEGER,
            bill_number TEXT,
            customer_name TEXT NOT NULL,
            customer_mobile TEXT,
            customer_address TEXT,
            items_json TEXT,
            subtotal REAL,
            gst_enabled INTEGER DEFAULT 0,
            gst_percentage REAL,
            gst_amount REAL,
            total REAL,
            bill_date TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (template_id) REFERENCES templates (id)
        )
    ''')
    
    # Create default admin user if not exists
    admin = db.execute('SELECT * FROM users WHERE email = ?', ('admin@invoice.com',)).fetchone()
    if not admin:
        admin_password = generate_password_hash('admin123')
        db.execute('''
            INSERT INTO users (email, password_hash, business_name, business_address, 
                owner_name, mobile, is_admin, is_approved, is_active)
            VALUES (?, ?, ?, ?, ?, ?, 1, 1, 1)
        ''', ('admin@invoice.com', admin_password, 'Admin Business', 'Admin Address', 
              'Admin User', '0000000000'))
    
    db.commit()
    db.close()

# Initialize database on startup
init_db()

# Import auth decorators
from auth import login_required, admin_required, get_current_user
from gst_verification import verify_gst

@app.route('/')
@login_required
def index():
    user = get_current_user()
    db = get_db()
    template = db.execute('SELECT * FROM templates WHERE user_id = ? ORDER BY id DESC LIMIT 1', 
                         (user['id'],)).fetchone()
    recent_bills = db.execute('SELECT * FROM bills WHERE user_id = ? ORDER BY created_at DESC LIMIT 5',
                              (user['id'],)).fetchall()
    db.close()
    return render_template('index.html', template=template, recent_bills=recent_bills, user=user)

@app.route('/template', methods=['GET', 'POST'])
@login_required
def template():
    user = get_current_user()
    db = get_db()
    
    if request.method == 'POST':
        # Get form data
        business_name = request.form.get('business_name', '').strip()
        business_address = request.form.get('business_address', '').strip()
        owner_name = request.form.get('owner_name', '').strip()
        mobile = request.form.get('mobile', '').strip()
        gst_number = request.form.get('gst_number', '').strip()

        
        # Stamp data
        stamp_data = request.form.get('stamp_data', '')
        stamp_type = request.form.get('stamp_type', 'rectangle')
        stamp_business_name = request.form.get('stamp_business_name', '')
        stamp_place = request.form.get('stamp_place', '')
        
        # Handle logo upload
        logo_path = None
        if 'logo' in request.files:
            logo = request.files['logo']
            if logo and logo.filename and allowed_file(logo.filename):
                filename = secure_filename(f"logo_{datetime.now().strftime('%Y%m%d%H%M%S')}_{logo.filename}")
                logo_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                logo.save(logo_path)
                logo_path = filename
        
        # Handle signature upload
        signature_path = None
        if 'signature' in request.files:
            sig = request.files['signature']
            if sig and sig.filename and allowed_file(sig.filename):
                filename = secure_filename(f"sig_{datetime.now().strftime('%Y%m%d%H%M%S')}_{sig.filename}")
                signature_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                sig.save(signature_path)
                signature_path = filename

        # Handle stamp upload
        stamp_upload_path = None
        if 'stamp_upload' in request.files:
            stamp_file = request.files['stamp_upload']
            if stamp_file and stamp_file.filename and allowed_file(stamp_file.filename):
                filename = secure_filename(f"stamp_{datetime.now().strftime('%Y%m%d%H%M%S')}_{stamp_file.filename}")
                stamp_upload_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                stamp_file.save(stamp_upload_path)
                stamp_upload_path = filename
        
        # Check if template exists for this user
        existing = db.execute('SELECT * FROM templates WHERE user_id = ? ORDER BY id DESC LIMIT 1', 
                            (user['id'],)).fetchone()
        
        if existing:
            # Keep existing files if no new ones uploaded
            if not logo_path and existing['logo_path']:
                logo_path = existing['logo_path']
            if not signature_path and existing['signature_path']:
                signature_path = existing['signature_path']
            if not stamp_upload_path and existing['stamp_upload_path']:
                stamp_upload_path = existing['stamp_upload_path']
            
            db.execute('''
                UPDATE templates SET 
                    business_name=?, business_address=?, owner_name=?, mobile=?,
                    gst_number=?, logo_path=?, signature_path=?, 
                    stamp_upload_path=?, stamp_data=?, stamp_type=?, 
                    stamp_business_name=?, stamp_place=?
                WHERE id=? AND user_id=?
            ''', (business_name, business_address, owner_name, mobile, gst_number,
                  logo_path, signature_path, stamp_upload_path, stamp_data, stamp_type, 
                  stamp_business_name, stamp_place, existing['id'], user['id']))
        else:
            db.execute('''
                INSERT INTO templates (user_id, business_name, business_address, owner_name, mobile,
                    gst_number, logo_path, signature_path, stamp_upload_path, 
                    stamp_data, stamp_type, stamp_business_name, stamp_place)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (user['id'], business_name, business_address, owner_name, mobile, gst_number,
                  logo_path, signature_path, stamp_upload_path, stamp_data, stamp_type, 
                  stamp_business_name, stamp_place))
        
        db.commit()
        db.close()
        return redirect(url_for('index'))
    
    # GET request - show form
    existing_template = db.execute('SELECT * FROM templates WHERE user_id = ? ORDER BY id DESC LIMIT 1', 
                                   (user['id'],)).fetchone()
    db.close()
    return render_template('template.html', template=existing_template)

@app.route('/bill/create', methods=['GET', 'POST'])
@login_required
def create_bill():
    user = get_current_user()
    db = get_db()
    template = db.execute('SELECT * FROM templates WHERE user_id = ? ORDER BY id DESC LIMIT 1', 
                         (user['id'],)).fetchone()
    
    if not template:
        db.close()
        return redirect(url_for('template'))
    
    if request.method == 'POST':
        customer_name = request.form.get('customer_name', '').strip()
        customer_mobile = request.form.get('customer_mobile', '').strip()
        customer_address = request.form.get('customer_address', '').strip()
        bill_date = request.form.get('bill_date')
        
        if not bill_date:
            bill_date = datetime.now().strftime('%Y-%m-%d')

        # Get items
        item_names = request.form.getlist('item_name[]')
        quantities = request.form.getlist('quantity[]')
        rates = request.form.getlist('rate[]')
        
        items = []
        subtotal = 0
        for i in range(len(item_names)):
            if item_names[i].strip():
                try:
                    qty = float(quantities[i]) if quantities[i] else 0
                    rate = float(rates[i]) if rates[i] else 0
                    amount = qty * rate
                    items.append({
                        'name': item_names[i].strip(),
                        'quantity': qty,
                        'rate': rate,
                        'amount': amount
                    })
                    subtotal += amount
                except ValueError:
                    continue
        
        gst_enabled = request.form.get('gst_enabled') == 'on'
        gst_percentage = float(request.form.get('gst_percentage', 0)) if gst_enabled else 0
        gst_amount = (subtotal * gst_percentage / 100) if gst_enabled else 0
        total = subtotal + gst_amount
        
        # Generate bill number for this user
        last_bill = db.execute('SELECT bill_number FROM bills WHERE user_id = ? ORDER BY id DESC LIMIT 1', 
                              (user['id'],)).fetchone()
        if last_bill and last_bill['bill_number']:
            try:
                last_num = int(last_bill['bill_number'].split('-')[-1])
                bill_number = f"INV-{last_num + 1:04d}"
            except:
                bill_number = "INV-0001"
        else:
            bill_number = "INV-0001"
        
        db.execute('''
            INSERT INTO bills (user_id, template_id, bill_number, customer_name, customer_mobile,
                customer_address, items_json, subtotal, gst_enabled, gst_percentage,
                gst_amount, total, bill_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user['id'], template['id'], bill_number, customer_name, customer_mobile, customer_address,
              json.dumps(items), subtotal, gst_enabled, gst_percentage, gst_amount, total, bill_date))
        
        db.commit()
        bill_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]
        db.close()
        
        return redirect(url_for('preview_bill', bill_id=bill_id))
    
    # Set default date to today
    default_date = datetime.now().strftime('%Y-%m-%d')
    
    db.close()
    return render_template('bill.html', template=template, default_date=default_date)

@app.route('/bill/preview/<int:bill_id>')
@login_required
def preview_bill(bill_id):
    user = get_current_user()
    db = get_db()
    bill = db.execute('SELECT * FROM bills WHERE id = ? AND user_id = ?', 
                     (bill_id, user['id'])).fetchone()
    
    if not bill:
        db.close()
        return redirect(url_for('history'))
    
    template = db.execute('SELECT * FROM templates WHERE id = ?', (bill['template_id'],)).fetchone()
    items = json.loads(bill['items_json']) if bill['items_json'] else []
    db.close()
    
    return render_template('preview.html', bill=bill, template=template, items=items)

@app.route('/history')
@login_required
def history():
    user = get_current_user()
    db = get_db()
    bills = db.execute('''
        SELECT b.*, t.business_name 
        FROM bills b 
        LEFT JOIN templates t ON b.template_id = t.id 
        WHERE b.user_id = ?
        ORDER BY b.created_at DESC
    ''', (user['id'],)).fetchall()
    db.close()
    return render_template('history.html', bills=bills)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_file(os.path.join(app.config['UPLOAD_FOLDER'], filename))

# ============================================
# Authentication Routes
# ============================================

@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        business_name = request.form.get('business_name', '').strip()
        business_address = request.form.get('business_address', '').strip()
        owner_name = request.form.get('owner_name', '').strip()
        mobile = request.form.get('mobile', '').strip()
        gst_number = request.form.get('gst_number', '').strip().upper()
        
        # Validation
        if not all([email, password, business_name, business_address, owner_name, mobile]):
            flash('All fields except GST number are required', 'error')
            return render_template('register.html')
        
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('register.html')
        
        if len(password) < 6:
            flash('Password must be at least 6 characters', 'error')
            return render_template('register.html')
        
        # Verify GST if provided
        gst_verified = 0
        if gst_number:
            gst_result = verify_gst(gst_number)
            if not gst_result['valid']:
                flash(f"GST Verification Failed: {gst_result.get('error', 'Invalid GST')}", 'error')
                return render_template('register.html')
            gst_verified = 1
        
        db = get_db()
        
        # Check if email already exists
        existing = db.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        if existing:
            flash('Email already registered', 'error')
            db.close()
            return render_template('register.html')
        
        # Create user
        password_hash = generate_password_hash(password)
        try:
            db.execute('''
                INSERT INTO users (email, password_hash, business_name, business_address,
                    owner_name, mobile, gst_number, gst_verified, is_approved)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0)
            ''', (email, password_hash, business_name, business_address, owner_name, 
                  mobile, gst_number, gst_verified))
            db.commit()
            db.close()
            
            flash('Registration successful! Please wait for admin approval.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.close()
            flash(f'Registration failed: {str(e)}', 'error')
            return render_template('register.html')
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        
        if not email or not password:
            flash('Email and password are required', 'error')
            return render_template('login.html')
        
        db = get_db()
        user = db.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        db.close()
        
        if not user or not check_password_hash(user['password_hash'], password):
            flash('Invalid email or password', 'error')
            return render_template('login.html')
        
        if not user['is_active']:
            flash('Your account has been deactivated', 'error')
            return render_template('login.html')
        
        if not user['is_approved'] and not user['is_admin']:
            session['user_id'] = user['id']
            return redirect(url_for('pending_approval'))
        
        # Login successful
        session['user_id'] = user['id']
        session['is_admin'] = user['is_admin']
        flash(f"Welcome back, {user['owner_name']}!", 'success')
        return redirect(url_for('index'))
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('login'))

@app.route('/pending-approval')
def pending_approval():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = get_current_user()
    if user and user['is_approved']:
        return redirect(url_for('index'))
    
    return render_template('pending_approval.html', user=user)

# ============================================
# Admin Routes
# ============================================

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    user = get_current_user()
    db = get_db()
    
    # Get statistics
    total_users = db.execute('SELECT COUNT(*) as count FROM users WHERE is_admin = 0').fetchone()['count']
    pending_users = db.execute('SELECT COUNT(*) as count FROM users WHERE is_approved = 0 AND is_admin = 0').fetchone()['count']
    total_bills = db.execute('SELECT COUNT(*) as count FROM bills').fetchone()['count']
    
    # Get pending users
    pending = db.execute('''
        SELECT * FROM users 
        WHERE is_approved = 0 AND is_admin = 0 
        ORDER BY created_at DESC
    ''').fetchall()
    
    # Get all users
    all_users = db.execute('''
        SELECT * FROM users 
        WHERE is_admin = 0 
        ORDER BY created_at DESC
    ''').fetchall()
    
    db.close()
    
    return render_template('admin_dashboard.html', 
                         user=user,
                         total_users=total_users,
                         pending_users=pending_users,
                         total_bills=total_bills,
                         pending=pending,
                         all_users=all_users)

@app.route('/admin/approve/<int:user_id>')
@admin_required
def approve_user(user_id):
    admin = get_current_user()
    db = get_db()
    
    user = db.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    if not user:
        flash('User not found', 'error')
    else:
        db.execute('''
            UPDATE users 
            SET is_approved = 1, approved_at = ?, approved_by = ?
            WHERE id = ?
        ''', (datetime.now(), admin['id'], user_id))
        db.commit()
        flash(f"User {user['email']} has been approved", 'success')
    
    db.close()
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/reject/<int:user_id>')
@admin_required
def reject_user(user_id):
    db = get_db()
    
    user = db.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    if not user:
        flash('User not found', 'error')
    else:
        db.execute('DELETE FROM users WHERE id = ?', (user_id,))
        db.commit()
        flash(f"User {user['email']} has been rejected and removed", 'info')
    
    db.close()
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/toggle-active/<int:user_id>')
@admin_required
def toggle_user_active(user_id):
    db = get_db()
    
    user = db.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    if not user:
        flash('User not found', 'error')
    else:
        new_status = 0 if user['is_active'] else 1
        db.execute('UPDATE users SET is_active = ? WHERE id = ?', (new_status, user_id))
        db.commit()
        status_text = 'activated' if new_status else 'deactivated'
        flash(f"User {user['email']} has been {status_text}", 'success')
    
    db.close()
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete-user/<int:user_id>')
@admin_required
def delete_user(user_id):
    db = get_db()
    
    user = db.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    if not user:
        flash('User not found', 'error')
    elif user['is_admin']:
        flash('Cannot delete admin account', 'error')
    else:
        # Delete associated data
        db.execute('DELETE FROM bills WHERE user_id = ?', (user_id,))
        db.execute('DELETE FROM templates WHERE user_id = ?', (user_id,))
        db.execute('DELETE FROM users WHERE id = ?', (user_id,))
        db.commit()
        flash(f"User {user['email']} and all their data permanently deleted", 'success')
    
    db.close()
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/profile', methods=['GET', 'POST'])
@admin_required
def admin_profile():
    user = get_current_user()
    db = get_db()
    
    if request.method == 'POST':
        new_email = request.form.get('email', '').strip().lower()
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Verify current password
        if not check_password_hash(user['password_hash'], current_password):
            flash('Current password is incorrect', 'error')
            db.close()
            return render_template('admin_profile.html', user=user)
        
        # Validate new email
        if new_email != user['email']:
            existing = db.execute('SELECT * FROM users WHERE email = ? AND id != ?', 
                                 (new_email, user['id'])).fetchone()
            if existing:
                flash('Email already in use by another user', 'error')
                db.close()
                return render_template('admin_profile.html', user=user)
        
        # Update email
        if new_email != user['email']:
            db.execute('UPDATE users SET email = ? WHERE id = ?', (new_email, user['id']))
            flash('Email updated successfully', 'success')
        
        # Update password if provided
        if new_password:
            if len(new_password) < 6:
                flash('Password must be at least 6 characters', 'error')
                db.close()
                return render_template('admin_profile.html', user=user)
            
            if new_password != confirm_password:
                flash('New passwords do not match', 'error')
                db.close()
                return render_template('admin_profile.html', user=user)
            
            password_hash = generate_password_hash(new_password)
            db.execute('UPDATE users SET password_hash = ? WHERE id = ?', 
                      (password_hash, user['id']))
            flash('Password updated successfully', 'success')
        
        db.commit()
        db.close()
        
        # If email changed, update session and redirect to login
        if new_email != user['email']:
            session.clear()
            flash('Email updated. Please login with your new email.', 'info')
            return redirect(url_for('login'))
        
        return redirect(url_for('admin_profile'))
    
    db.close()
    return render_template('admin_profile.html', user=user)

# ============================================
# API Routes
# ============================================

@app.route('/api/verify-gst', methods=['POST'])
def api_verify_gst():
    data = request.get_json()
    gst_number = data.get('gst_number', '').strip().upper()
    
    result = verify_gst(gst_number)
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

