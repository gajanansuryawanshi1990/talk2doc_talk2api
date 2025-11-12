from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Enum, Date
from sqlalchemy.orm import sessionmaker, declarative_base, Session, relationship
from sqlalchemy.exc import OperationalError
from pydantic import BaseModel, ConfigDict, EmailStr
from typing import List, Optional
import os
import uvicorn
import enum
from passlib.hash import pbkdf2_sha256
from dotenv import load_dotenv
from datetime import date

load_dotenv()


# Database configuration (Update for SQL Server)
# server = 'CTAADHBBR8D3\\SQLEXPRESS22'  # Use double backslash for Python
# database = 'DemoDB'  # Keep your database name as is
# username = 'sa'  # Assuming you still use 'sa'
# password = 'password_123'  # Replace with actual password
# driver = 'ODBC Driver 17 for SQL Server'

# # Create the connection string
# DATABASE_URL = os.getenv("DATABASE_URL", f"mssql+pyodbc://{username}:{password}@{server}/{database}?driver={driver.replace(' ', '+')}")

# engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
import urllib
 
server = 'CTAAD9FLFFB3\\SQLEXPRESS_2022'
database = 'sample'
username = 'sa'
password = 'password_123'
driver = 'ODBC Driver 17 for SQL Server'
 
# Create the connection string
# DATABASE_URL = os.getenv("DATABASE_URL", f"mssql+pyodbc://{username}:{password}@{server}/{database}?driver={_driver.replace(' ', '+')}")
 
connection_string = (
    f"DRIVER={driver};"
    f"SERVER={server};"
    f"DATABASE={database};"
    f"UID={username};"
    f"PWD={password}"
)
 
params = urllib.parse.quote_plus(connection_string)
 
# Final SQLAlchemy connection URL
DATABASE_URL = f"mssql+pyodbc:///?odbc_connect={params}"
 
# Create engine
engine = create_engine(DATABASE_URL)
 
 

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ------------------- MODELS -------------------
class PatientInfo(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    age = Column(Integer)
    gender = Column(String)
    diagnosis = Column(String)
    contact_number = Column(String)
    email = Column(String)
    admission_date = Column(String)
    discharge_date = Column(String, nullable=True)

    doctors = relationship("Doctor", back_populates="patient")
    studies = relationship("Study", back_populates="patient")


class Doctor(Base):
    __tablename__ = "doctors"

    id = Column(Integer, primary_key=True, index=True)
    doctor_name = Column(String, index=True)
    designation = Column(String)
    specialization = Column(String)
    title = Column(String)
    description = Column(String)
    patient_id = Column(Integer, ForeignKey("patients.id"))

    patient = relationship("PatientInfo", back_populates="doctors")
    studies = relationship("Study", back_populates="doctor")

class Study(Base):
    __tablename__ = "studies"

    study_id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"))
    doctor_id = Column(Integer, ForeignKey("doctors.id"))
    study_type = Column(String)
    study_date = Column(String)
    findings = Column(String)

    patient = relationship("PatientInfo", back_populates="studies")
    doctor = relationship("Doctor", back_populates="studies")

# class RoleEnum(enum.Enum):
#     admin = "admin"
#     user = "user"

class Employee(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), nullable=False, unique=True)
    password = Column(String(255), nullable=False)  # Store hashed password
    email = Column(String(100), nullable=False, unique=True)
    # role = Column(Enum(RoleEnum), nullable=False, default=RoleEnum.user)
    role = Column(String(100), nullable=True, unique=False)
    doj = Column(Date, nullable=False)  # Date of Joining
    designation = Column(String(100), nullable=False)
    department = Column(String(100), nullable=False)
    location = Column(String(100), nullable=False)


    # def __repr__(self):
    #     return f"<Login(username={self.username}, email={self.email}, role={self.role})>"


Base.metadata.create_all(bind=engine)

# ------------------- FASTAPI APP -------------------
app = FastAPI()

# Dependency
def get_db():
    db = None
    try:
        db = SessionLocal()
        yield db
    except OperationalError as exc:
        raise HTTPException(status_code=503, detail="Database unavailable") from exc
    finally:
        if db:
            db.close()

# ------------------- SCHEMAS -------------------
class PatientSchema(BaseModel):
    id: int
    name: str
    age: int
    gender: str
    diagnosis: str
    contact_number: str
    email: str
    admission_date: str
    discharge_date: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class DoctorSchema(BaseModel):
    id: int
    doctor_name: str
    designation: str
    specialization: str
    title: str
    description: str
    patient_id: int
    model_config = ConfigDict(from_attributes=True)

class StudySchema(BaseModel):
    study_id: int
    patient_id: int
    doctor_id: int
    study_type: str
    study_date: str
    findings: str
    model_config = ConfigDict(from_attributes=True)


class EmployeeSchema(BaseModel):
    id: int
    username: str
    password: str  # This will hold hashed password, not plain text
    email: EmailStr
    role: str  # "admin" or "user"
    doj: date  # Date of Joining
    designation: str
    department: str
    location: str


    # Enable ORM mode for SQLAlchemy compatibility
    model_config = ConfigDict(from_attributes=True)


# ------------------- ROUTES -------------------
@app.get("/")
async def read_root():
    return {"message": "Welcome to the Patient-Doctor-Study API."}

# Patients
@app.get("/patients", response_model=List[PatientSchema])
def get_all_patients(db: Session = Depends(get_db)):
    return db.query(PatientInfo).all()

@app.get("/patient/{patient_id}", response_model=PatientSchema)
def get_patient_by_id(patient_id: int, db: Session = Depends(get_db)):
    patient = db.query(PatientInfo).filter(PatientInfo.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient

# Doctors
@app.get("/doctors", response_model=List[DoctorSchema])
def get_all_doctors(db: Session = Depends(get_db)):
    return db.query(Doctor).all()

@app.get("/doctor/{doctor_id}", response_model=DoctorSchema)
def get_doctor_by_id(doctor_id: int, db: Session = Depends(get_db)):
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    return doctor

# Studies
@app.get("/studies", response_model=List[StudySchema])
def get_all_studies(db: Session = Depends(get_db)):
    return db.query(Study).all()

@app.get("/study/{study_id}", response_model=StudySchema)
def get_study_by_id(study_id: int, db: Session = Depends(get_db)):
    study = db.query(Study).filter(Study.study_id == study_id).first()
    if not study:
        raise HTTPException(status_code=404, detail="Study not found")
    return study

# Related Data APIs
@app.get("/patient/{patient_id}/doctors", response_model=List[DoctorSchema])
def get_doctors_for_patient(patient_id: int, db: Session = Depends(get_db)):
    return db.query(Doctor).filter(Doctor.patient_id == patient_id).all()

@app.get("/patient/{patient_id}/studies", response_model=List[StudySchema])
def get_studies_for_patient(patient_id: int, db: Session = Depends(get_db)):
    return db.query(Study).filter(Study.patient_id == patient_id).all()

@app.get("/doctor/{doctor_id}/studies", response_model=List[StudySchema])
def get_studies_for_doctor(doctor_id: int, db: Session = Depends(get_db)):
    return db.query(Study).filter(Study.doctor_id == doctor_id).all()


@app.post("/register")
def register_user(username: str, email: str, password: str, doj:str, designation: str, department: str, location: str, db: Session = Depends(get_db)):
    # Check if username or email exists
    if db.query(Employee).filter_by(username=username).first():
        raise HTTPException(status_code=400, detail="Username already exists")
    if db.query(Employee).filter_by(email=email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    # Create new user
    hashed_password = pbkdf2_sha256.hash(password)
    new_employee = Employee(username=username, email=email, password=hashed_password, doj=doj, designation=designation, department=department, location=location)
    db.add(new_employee)
    db.commit()
    db.refresh(new_employee)
    return {"message": "Registration successful", "user_id": new_employee.id}

# @app.post("/register")
# def register_user(data: EmployeeSchema, db: Session = Depends(get_db)):
#     # Hash password
#     hashed_password = pbkdf2_sha256.hash(data.password)

#     # Create new employee
#     new_employee = Employee(
#         username=data.username,
#         email=data.email,
#         password=hashed_password,
#         role="user",  # default role
#         doj=data.doj,
#         designation=data.designation,
#         department=data.department,
#         location=data.location
#     )

#     db.add(new_employee)
#     db.commit()
#     db.refresh(new_employee)

#     return {"message": "Registration successful", "id": new_employee.id}


from datetime import datetime
@app.get("/authenticate")
def authenticate_user(username: str, password: str, db: Session = Depends(get_db)):
    # Fetch user from DB
    employee = db.query(Employee).filter_by(username=username).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Username not found!")

    # Verify password
    if not pbkdf2_sha256.verify(password, employee.password):
        raise HTTPException(status_code=401, detail="Incorrect password!")

    # Update last login timestamp
    employee.last_login = datetime.utcnow()
    db.commit()

    return {"status": "success", "message": "Login successful!", "username": employee.username,"role": employee.role}


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8001)
    
    
#To run command : python .\mcp_server.py    