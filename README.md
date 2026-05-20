# AI Integrated Eye Diagnosis and Doctor Consultation Management System

## Overview
The AI Integrated Eye Diagnosis and Doctor Consultation Management System is a web-based healthcare platform designed for early detection of retinal diseases using Artificial Intelligence and Deep Learning techniques. The system analyzes retinal fundus images and predicts eye diseases such as Diabetic Retinopathy, Cataract, and Glaucoma while also providing online doctor consultation and appointment management features.

The project combines AI-powered diagnosis with telemedicine services to improve healthcare accessibility and reduce delays in medical consultation, especially for remote and underserved populations.

---

## Features

- Secure user registration and login system
- Retinal image upload and validation
- AI-based retinal disease detection
- Detection of:
  - Diabetic Retinopathy
  - Cataract
  - Glaucoma
  - Normal Eye Condition
- Real-time prediction results
- Confidence score generation
- PDF diagnosis report generation
- Doctor consultation module
- Appointment booking system
- Medical history management
- Centralized database storage

---

## System Workflow

1. User registers and logs into the system
2. Retinal image is uploaded
3. Image preprocessing is performed
4. YOLOv11-based CNN model analyzes the image
5. Disease prediction is generated
6. Report is created and stored
7. User can consult doctors and book appointments

---

## Technologies Used

### Frontend
- HTML
- CSS
- JavaScript
- Bootstrap

### Backend
- Python
- Flask

### Artificial Intelligence
- YOLOv11
- CNN
- TensorFlow
- OpenCV
- NumPy

### Database
- SQL
- SQLAlchemy

### Additional Libraries
- ReportLab
- Pandas

---

## Project Structure

```bash
AI-Eye-Diagnosis-System/
│
├── static/
│   ├── css/
│   ├── js/
│   └── images/
│
├── templates/
│   ├── login.html
│   ├── register.html
│   ├── dashboard.html
│   └── reports.html
│
├── model/
│   └── eye_disease_model.keras
│
├── uploads/
│
├── app.py
├── requirements.txt
├── database.db
└── README.md
