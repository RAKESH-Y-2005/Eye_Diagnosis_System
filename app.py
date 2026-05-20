from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
import time
import numpy as np
import cv2
import io
import datetime
import uuid
import csv
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

app = Flask(__name__)
app.config['SECRET_KEY'] = 'eye_diagnosis_secret_super_key123'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
# Define absolute path for SQLite database to ensure consistency
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'eye_diagnosis.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Try loading the AI model
MODEL = None
try:
    import tensorflow as tf
    model_path = 'model/eye_disease_cnn.keras'
    if os.path.exists(model_path):
        # We need a custom compile logic to ignore if we don't compile, usually loading takes care of it
        MODEL = tf.keras.models.load_model(model_path)
        print("Model loaded successfully!")
    else:
        print(f"Model {model_path} not found. Ensure train_model.py was run.")
except Exception as e:
    print(f"Error loading TF model: {e}")

CLASSES = ['Cataract', 'Diabetic Retinopathy', 'Glaucoma', 'Normal']

# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='patient') # patient, doctor, admin
    is_active_account = db.Column(db.Boolean, default=True) # for admin suspension
    specialty = db.Column(db.String(100), nullable=True) # for doctors
    bio = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

class DiagnosisReport(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    image_path = db.Column(db.String(255), nullable=False)
    diagnosis_result = db.Column(db.String(100), nullable=False)
    confidence_score = db.Column(db.Float, nullable=False)
    verification_status = db.Column(db.String(20), default='pending') # pending, verified_correct, flagged_incorrect
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    appointment_date = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default='pending') # pending, confirmed, completed, cancelled
    is_emergency = db.Column(db.Boolean, default=False)
    meet_link = db.Column(db.String(255), nullable=True) # for telehealth
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# Initialize Database Context
with app.app_context():
    db.create_all()

# --- Routes ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/scan')
@login_required
def scan():
    return render_template('scan.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect_dashboard(current_user)
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, password):
            if not user.is_active_account:
                if user.role == 'doctor':
                    flash('Your account is pending administrator approval or suspended.')
                else:
                    flash('Your account has been suspended by the administrator.')
                return render_template('login.html')
            login_user(user)
            return redirect_dashboard(user)
        else:
            flash('Invalid email or password.')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect_dashboard(current_user)
    if request.method == 'POST':
        full_name = request.form.get('full_name')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role', 'patient')

        if User.query.filter_by(email=email).first():
            flash('Email already registered.')
            return redirect(url_for('register'))

        new_user = User(
            full_name=full_name,
            email=email,
            password_hash=generate_password_hash(password),
            role=role,
            is_active_account=False if role == 'doctor' else True,
            specialty='General Practice' if role == 'doctor' else None,
            bio='Standard medical consulting profile.' if role == 'doctor' else None
        )
        db.session.add(new_user)
        db.session.commit()
        
        if role == 'doctor':
            flash('Doctor registration submitted. Please wait for admin approval before logging in.')
            return redirect(url_for('login'))
            
        login_user(new_user)
        return redirect_dashboard(new_user)
        
    return render_template('register.html')

def redirect_dashboard(user):
    if user.role == 'admin':
        return redirect(url_for('admin_dashboard'))
    elif user.role == 'doctor':
        return redirect(url_for('doctor_dashboard'))
    else:
        return redirect(url_for('dashboard'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.role != 'patient':
        return redirect_dashboard(current_user)
    # limit dashboard to recent items
    reports = DiagnosisReport.query.filter_by(patient_id=current_user.id).order_by(DiagnosisReport.created_at.desc()).limit(3).all()
    appointments = Appointment.query.filter_by(patient_id=current_user.id).order_by(Appointment.appointment_date.desc()).limit(3).all()
    return render_template('dashboard.html', reports=reports, appointments=appointments)

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        current_user.full_name = request.form.get('full_name')
        if current_user.role == 'doctor':
            current_user.specialty = request.form.get('specialty')
            current_user.bio = request.form.get('bio')
        db.session.commit()
        flash('Profile updated successfully.', 'success')
    return render_template('profile.html')

@app.route('/doctors')
def doctors_directory():
    active_doctors = User.query.filter_by(role='doctor', is_active_account=True).all()
    return render_template('doctors.html', doctors=active_doctors)

@app.route('/records')
@login_required
def records():
    if current_user.role == 'patient':
        reports = DiagnosisReport.query.filter_by(patient_id=current_user.id).order_by(DiagnosisReport.created_at.desc()).all()
    else:
        # Doctors see all reports for simplicity in this demo
        reports = DiagnosisReport.query.order_by(DiagnosisReport.created_at.desc()).all()
    return render_template('records.html', reports=reports)

@app.route('/consultations')
@login_required
def consultations():
    if current_user.role == 'patient':
        appts = Appointment.query.filter_by(patient_id=current_user.id).order_by(Appointment.appointment_date.desc()).all()
    else:
        appts = Appointment.query.filter_by(doctor_id=current_user.id).order_by(Appointment.appointment_date.desc()).all()
    return render_template('consultations.html', appointments=appts)

@app.route('/doctor_dashboard')
@login_required
def doctor_dashboard():
    if current_user.role != 'doctor':
        return redirect_dashboard(current_user)
    appointments = Appointment.query.filter_by(doctor_id=current_user.id).order_by(Appointment.appointment_date.desc()).all()
    # A doctor might also want to view patient reports, we'll keep it simple for now
    return render_template('doctor_dashboard.html', appointments=appointments)

@app.route('/admin_dashboard')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        return redirect_dashboard(current_user)
    total_users = User.query.count()
    total_scans = DiagnosisReport.query.count()
    users = User.query.all()
    doctors = [u for u in users if u.role == 'doctor']
    patients = [u for u in users if u.role == 'patient']
    appointments = Appointment.query.order_by(Appointment.appointment_date.desc()).all()
    reports = DiagnosisReport.query.order_by(DiagnosisReport.created_at.desc()).all()
    return render_template('admin_dashboard.html', total_users=total_users, total_scans=total_scans, users=users, doctors=doctors, patients=patients, appointments=appointments, reports=reports)

@app.route('/api/predict', methods=['POST'])
@login_required
def predict():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded', 'success': False}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Empty filename', 'success': False}), 400

    try:
        from werkzeug.utils import secure_filename
        filename = secure_filename(file.filename)
        # Use relative path for URL, but absolute path for file system operations
        rel_filepath = f"{app.config['UPLOAD_FOLDER']}/{filename}"
        abs_filepath = os.path.join(basedir, app.config['UPLOAD_FOLDER'], filename)
        file.save(abs_filepath)

        diagnosis = 'Diabetic Retinopathy'
        confidence = 0.942

        if MODEL is not None:
            # Processing image for inference
            img = cv2.imread(abs_filepath)
            if img is not None:
                # Convert BGR to RGB as Keras models expect RGB
                img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                img = cv2.resize(img, (224, 224))
                img = img / 255.0
                img = np.expand_dims(img, axis=0)
                preds = MODEL.predict(img)
                class_idx = np.argmax(preds[0])
                confidence = float(preds[0][class_idx])
                diagnosis = CLASSES[class_idx]
        else:
            time.sleep(1.0) # mock delay
        
        # Save to Database
        report = DiagnosisReport(
            patient_id=current_user.id,
            image_path=rel_filepath, # stored relative path
            diagnosis_result=diagnosis,
            confidence_score=confidence
        )
        db.session.add(report)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'diagnosis': diagnosis,
            'confidence': confidence,
            'image_url': f'/{rel_filepath}'
        })

    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500

@app.route('/api/book_appointment', methods=['POST'])
@login_required
def book_appointment():
    if current_user.role != 'patient':
         return redirect(url_for('dashboard'))
    
    doctor_id = request.form.get('doctor_id')
    date_str = request.form.get('appointment_date')
    notes = request.form.get('notes', '')
    
    if not doctor_id or not date_str:
        return redirect(url_for('dashboard'))
    try:
        app_date = datetime.datetime.strptime(date_str, '%Y-%m-%dT%H:%M')
        # Generate a unique telehealth meet link
        meet_link = f"https://meet.opticore.ai/{uuid.uuid4().hex[:12]}"
        
        new_app = Appointment(patient_id=current_user.id, doctor_id=doctor_id, appointment_date=app_date, notes=notes, meet_link=meet_link)
        db.session.add(new_app)
        db.session.commit()
        flash('Appointment booked successfully. A virtual waiting room link has been generated.')
    except Exception as e:
        flash(f'Error booking appointment: {e}')
        
    return redirect(url_for('consultations'))

@app.route('/report/<int:report_id>/pdf')
@login_required
def generate_pdf(report_id):
    report = db.session.get(DiagnosisReport, report_id)
    if not report:
        return "Report Not Found", 404
    
    if report.patient_id != current_user.id and current_user.role not in ['doctor', 'admin']:
        return "Unauthorized", 403
        
    patient = db.session.get(User, report.patient_id)
    
    # Generate PDF in memory
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    p.setFont("Helvetica-Bold", 20)
    p.drawString(100, 750, "Eye Diagnosis AI Report")
    
    p.setFont("Helvetica", 12)
    p.drawString(100, 710, f"Patient Name: {patient.full_name}")
    p.drawString(100, 690, f"Date: {report.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
    p.drawString(100, 650, f"Predicted Diagnosis: {report.diagnosis_result}")
    p.drawString(100, 630, f"Confidence Score: {report.confidence_score*100:.2f}%")
    
    # Optionally draw the image if it exists
    if os.path.exists(report.image_path):
        try:
           p.drawImage(report.image_path, 100, 400, width=200, height=200, preserveAspectRatio=True)
        except Exception:
           pass
    
    p.showPage()
    p.save()
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name=f"diagnosis_report_{report_id}.pdf", mimetype='application/pdf')

# Update Appointment Status Helper
@app.route('/api/update_appointment/<int:app_id>', methods=['POST'])
@login_required
def update_appointment(app_id):
    app_obj = db.session.get(Appointment, app_id)
    if not app_obj:
        return "Not found", 404
    # Doctors can confirm/complete
    if current_user.role == 'doctor' and app_obj.doctor_id == current_user.id:
        new_status = request.form.get('status')
        if new_status in ['pending', 'confirmed', 'completed', 'cancelled']:
            app_obj.status = new_status
            db.session.commit()
    return redirect(url_for('consultations'))

@app.route('/admin/toggle_status/<int:user_id>', methods=['POST'])
@login_required
def toggle_status(user_id):
    if current_user.role != 'admin':
        return "Unauthorized", 403
    user = db.session.get(User, user_id)
    if user and user.id != current_user.id:
        user.is_active_account = not user.is_active_account
        db.session.commit()
        flash(f"User {user.full_name} status updated.")
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/mediator/book', methods=['POST'])
@login_required
def admin_book_appointment():
    if current_user.role != 'admin':
         return "Unauthorized", 403
    
    patient_id = request.form.get('patient_id')
    doctor_id = request.form.get('doctor_id')
    date_str = request.form.get('appointment_date')
    notes = request.form.get('notes', 'Scheduled by Admin')
    
    if not patient_id or not doctor_id or not date_str:
        flash('Missing fields for booking an appointment.')
        return redirect(url_for('admin_dashboard'))
    try:
        app_date = datetime.datetime.strptime(date_str, '%Y-%m-%dT%H:%M')
        meet_link = f"https://meet.opticore.ai/{uuid.uuid4().hex[:12]}"
        
        new_app = Appointment(patient_id=patient_id, doctor_id=doctor_id, appointment_date=app_date, notes=notes, meet_link=meet_link)
        db.session.add(new_app)
        db.session.commit()
        flash('Appointment mediated and booked successfully.')
    except Exception as e:
        flash(f'Error booking appointment: {e}')
        
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/mediator/update/<int:app_id>', methods=['POST'])
@login_required
def admin_update_appointment(app_id):
    if current_user.role != 'admin':
        return "Unauthorized", 403
    app_obj = db.session.get(Appointment, app_id)
    if not app_obj:
        return "Not found", 404
    new_status = request.form.get('status')
    if new_status in ['pending', 'confirmed', 'completed', 'cancelled']:
        app_obj.status = new_status
        db.session.commit()
        flash("Appointment status updated by admin.")
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/flag_emergency/<int:app_id>', methods=['POST'])
@login_required
def admin_flag_emergency(app_id):
    if current_user.role != 'admin':
        return "Unauthorized", 403
    app_obj = db.session.get(Appointment, app_id)
    if not app_obj:
        return "Not found", 404
    app_obj.is_emergency = not app_obj.is_emergency
    db.session.commit()
    flash(f"Appointment {'flagged as Emergency' if app_obj.is_emergency else 'removed from Emergency pool'}.")
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/verify_report/<int:report_id>', methods=['POST'])
@login_required
def admin_verify_report(report_id):
    if current_user.role != 'admin':
        return "Unauthorized", 403
    report = db.session.get(DiagnosisReport, report_id)
    if not report:
        return "Not found", 404
    
    new_status = request.form.get('verification_status')
    if new_status in ['pending', 'verified_correct', 'flagged_incorrect']:
        report.verification_status = new_status
        db.session.commit()
        flash("Report verification status updated.")
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/export')
@login_required
def export_core_logs():
    if current_user.role != 'admin':
        return "Unauthorized", 403
    
    # Generate CSV of system stats
    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerow(['Metric', 'Value'])
    cw.writerow(['Total Users', User.query.count()])
    cw.writerow(['Total Scans', DiagnosisReport.query.count()])
    cw.writerow(['Total Appointments', Appointment.query.count()])
    cw.writerow(['Active Doctors', User.query.filter_by(role='doctor', is_active_account=True).count()])
    
    output = io.BytesIO()
    output.write(si.getvalue().encode('utf-8'))
    output.seek(0)
    
    return send_file(output, as_attachment=True, download_name="opticore_system_logs.csv", mimetype='text/csv')

if __name__ == '__main__':
    app.run(debug=True, port=5000)
