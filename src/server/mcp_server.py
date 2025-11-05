from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base, Session, relationship
from sqlalchemy.exc import OperationalError
from pydantic import BaseModel, ConfigDict
from typing import List, Optional
import os
import uvicorn
from dotenv import load_dotenv
from urllib.parse import quote_plus

load_dotenv()


# Database configuration (Update for SQL Server)

from sqlalchemy import create_engine
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

# engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ------------------- MODELS -------------------
class PatientInfo(Base):
    __tablename__ = "patients"

    # id = Column(Integer, primary_key=True, index=True)
    id = Column(Integer, primary_key=True)
    name = Column(String)
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

    id = Column(Integer, primary_key=True)
    doctor_name = Column(String)
    designation = Column(String)
    specialization = Column(String)
    title = Column(String)
    description = Column(String)
    patient_id = Column(Integer, ForeignKey("patients.id"))

    patient = relationship("PatientInfo", back_populates="doctors")
    studies = relationship("Study", back_populates="doctor")


class Study(Base):
    __tablename__ = "studies"

    study_id = Column(Integer, primary_key=True)
    patient_id = Column(Integer, ForeignKey("patients.id"))
    doctor_id = Column(Integer, ForeignKey("doctors.id"))
    study_type = Column(String)
    study_date = Column(String)
    findings = Column(String)

    patient = relationship("PatientInfo", back_populates="studies")
    doctor = relationship("Doctor", back_populates="studies")

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

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8001)
    
    
#To run command : python .\mcp_server.py    