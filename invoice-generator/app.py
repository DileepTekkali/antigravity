import os
import json
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, jsonify, send_file
from werkzeug.utils import secure_filename
import base64

app = Flask(__name__)
app.secret_key = 'invoice-generator-secret-key-2024'
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
    try:
        os.remove('invoice.db') # Reset DB for schema changes
    except:
        pass
        
    db = get_db()
    db.execute('''
        CREATE TABLE IF NOT EXISTS templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    db.execute('''
        CREATE TABLE IF NOT EXISTS bills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
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
            FOREIGN KEY (template_id) REFERENCES templates (id)
        )
    ''')
    db.commit()
    db.close()

# Initialize database on startup
init_db()

@app.route('/')
def index():
    db = get_db()
    template = db.execute('SELECT * FROM templates ORDER BY id DESC LIMIT 1').fetchone()
    recent_bills = db.execute('SELECT * FROM bills ORDER BY created_at DESC LIMIT 5').fetchall()
    db.close()
    return render_template('index.html', template=template, recent_bills=recent_bills)

@app.route('/template', methods=['GET', 'POST'])
def template():
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
        
        # Check if template exists
        existing = db.execute('SELECT * FROM templates ORDER BY id DESC LIMIT 1').fetchone()
        
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
                WHERE id=?
            ''', (business_name, business_address, owner_name, mobile, gst_number,
                  logo_path, signature_path, stamp_upload_path, stamp_data, stamp_type, 
                  stamp_business_name, stamp_place, existing['id']))
        else:
            db.execute('''
                INSERT INTO templates (business_name, business_address, owner_name, mobile,
                    gst_number, logo_path, signature_path, stamp_upload_path, 
                    stamp_data, stamp_type, stamp_business_name, stamp_place)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (business_name, business_address, owner_name, mobile, gst_number,
                  logo_path, signature_path, stamp_upload_path, stamp_data, stamp_type, 
                  stamp_business_name, stamp_place))
        
        db.commit()
        db.close()
        return redirect(url_for('index'))
    
    # GET request - show form
    existing_template = db.execute('SELECT * FROM templates ORDER BY id DESC LIMIT 1').fetchone()
    db.close()
    return render_template('template.html', template=existing_template)

@app.route('/bill/create', methods=['GET', 'POST'])
def create_bill():
    db = get_db()
    template = db.execute('SELECT * FROM templates ORDER BY id DESC LIMIT 1').fetchone()
    
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
        
        # Generate bill number
        last_bill = db.execute('SELECT bill_number FROM bills ORDER BY id DESC LIMIT 1').fetchone()
        if last_bill and last_bill['bill_number']:
            try:
                last_num = int(last_bill['bill_number'].split('-')[-1])
                bill_number = f"INV-{last_num + 1:04d}"
            except:
                bill_number = "INV-0001"
        else:
            bill_number = "INV-0001"
        
        db.execute('''
            INSERT INTO bills (template_id, bill_number, customer_name, customer_mobile,
                customer_address, items_json, subtotal, gst_enabled, gst_percentage,
                gst_amount, total, bill_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (template['id'], bill_number, customer_name, customer_mobile, customer_address,
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
def preview_bill(bill_id):
    db = get_db()
    bill = db.execute('SELECT * FROM bills WHERE id = ?', (bill_id,)).fetchone()
    
    if not bill:
        db.close()
        return redirect(url_for('history'))
    
    template = db.execute('SELECT * FROM templates WHERE id = ?', (bill['template_id'],)).fetchone()
    items = json.loads(bill['items_json']) if bill['items_json'] else []
    db.close()
    
    return render_template('preview.html', bill=bill, template=template, items=items)

@app.route('/history')
def history():
    db = get_db()
    bills = db.execute('''
        SELECT b.*, t.business_name 
        FROM bills b 
        LEFT JOIN templates t ON b.template_id = t.id 
        ORDER BY b.created_at DESC
    ''').fetchall()
    db.close()
    return render_template('history.html', bills=bills)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_file(os.path.join(app.config['UPLOAD_FOLDER'], filename))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
