# from fastapi import FastAPI, Depends, HTTPException
# from sqlalchemy.orm import Session
# from models import PatientInfo, Doctor
# from database import SessionLocal, init_db
# from pydantic import BaseModel, ConfigDict
# from typing import List
# from sqlalchemy.exc import OperationalError
# from dotenv import load_dotenv
# from azure.search.documents.indexes import SearchIndexerClient
# from contextlib import asynccontextmanager
# from azure.core.credentials import AzureKeyCredential
# from azure.identity import DefaultAzureCredential

# # Init DB
# try:
#     init_db()
# except OperationalError as exc:
#     # Database not available at startup; log and let endpoints return 503 when used
#     import logging
#     logging.error("Database initialization failed: %s", exc)

# # app = FastAPI()
# #=====================================================================================
# from fastapi import FastAPI, HTTPException
# from azure.search.documents.indexes import SearchIndexerClient
# from azure.core.credentials import AzureKeyCredential
# from azure.identity import DefaultAzureCredential
# from dotenv import load_dotenv
# from contextlib import asynccontextmanager
# import os

# # Load environment variables
# load_dotenv()

# # Configuration
# SEARCH_SERVICE_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT")
# SEARCH_API_KEY = os.getenv("AZURE_SEARCH_API_KEY")
# SEARCH_INDEXER_NAME = os.getenv("AZURE_SEARCH_INDEXER_NAME", "talk2doc-indexer")

# # Global client
# search_indexer_client: SearchIndexerClient = None

# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     global search_indexer_client

#     if not SEARCH_SERVICE_ENDPOINT:
#         print("❌ AZURE_SEARCH_ENDPOINT is not set.")
#         yield
#         return

#     # Choose credential
#     credential = AzureKeyCredential(SEARCH_API_KEY) if SEARCH_API_KEY else DefaultAzureCredential()
#     print("🔐 Using", "API Key" if SEARCH_API_KEY else "DefaultAzureCredential", "for Azure AI Search authentication.")

#     # Initialize client
#     search_indexer_client = SearchIndexerClient(endpoint=SEARCH_SERVICE_ENDPOINT, credential=credential)

#     # Optional: Check indexer existence
#     try:
#         indexer_status = search_indexer_client.get_indexer_status(SEARCH_INDEXER_NAME)
#         print(f"✅ Connected to indexer '{SEARCH_INDEXER_NAME}'. Status: {indexer_status.last_result.status}")
#     except Exception as e:
#         print(f"⚠️ Indexer '{SEARCH_INDEXER_NAME}' not found or inaccessible: {e}")

#     yield
#     print("🛑 Application shutting down.")

# # Initialize FastAPI with lifespan
# app = FastAPI(lifespan=lifespan)

# @app.post("/trigger-indexer")
# async def trigger_azure_ai_search_indexer():
#     if not search_indexer_client:
#         raise HTTPException(status_code=500, detail="Azure AI Search client not initialized.")

#     try:
#         print(f"🚀 Triggering indexer: {SEARCH_INDEXER_NAME}")
#         search_indexer_client.run_indexer(SEARCH_INDEXER_NAME)
#         return {"message": f"Indexer '{SEARCH_INDEXER_NAME}' triggered successfully."}
#     except Exception as e:
#         print(f"❌ Error triggering indexer: {e}")
#         raise HTTPException(status_code=500, detail=f"Failed to trigger indexer: {str(e)}")

# @app.get("/")
# async def read_root():
#     return {"message": "Azure AI Search Indexer Trigger API. Use POST /trigger-indexer to trigger the default indexer."}

# #=====================================================================================

# # Dependency to get DB session
# def get_db():
#     try:
#         db = SessionLocal()
#     except OperationalError as exc:
#         raise HTTPException(status_code=503, detail="Database unavailable") from exc
#     try:
#         yield db
#     finally:
#         db.close()

# # Pydantic Schemas
# class PatientSchema(BaseModel):
#     id: int
#     name: str
#     age: int
#     gender: str
#     diagnosis: str
#     contact_number: str
#     email: str
#     admission_date: str
#     discharge_date: str

#     model_config = ConfigDict(from_attributes=True)

# # class PatientSchema(BaseModel): # Create a PatientCreateSchema Without id, If you want to avoid passing id in POST requests, define:
# #     name: str
# #     age: int
# #     gender: str
# #     diagnosis: str
# #     contact_number: str
# #     email: str
# #     admission_date: str
# #     discharge_date: str

# #     model_config = ConfigDict(from_attributes=True)
# class DoctorSchema(BaseModel):
#     id: int
#     doctor_name: str
#     designation: str
#     specialization: str 
#     title: str
#     description: str
#     patient_id: int

#     model_config = ConfigDict(from_attributes=True)

# # Routes
# @app.get("/patient/{patient_id}", response_model=PatientSchema)
# def get_user(patient_id: int, db: Session = Depends(get_db)):
#     patient = db.query(PatientInfo).filter(PatientInfo.id == patient_id).first()
#     if not patient:
#         raise HTTPException(status_code=404, detail="patient not found")
#     return patient

# @app.get("/patient", response_model=List[PatientSchema])
# def get_patient(db: Session = Depends(get_db)):
#     return db.query(PatientInfo).all()

# @app.get("/doctor", response_model=List[DoctorSchema])
# def get_projects(db: Session = Depends(get_db)):
#     return db.query(Doctor).all()

# @app.post("/patient", response_model=PatientSchema)
# def create_patient(patient: PatientSchema, db: Session = Depends(get_db)):
#     new_patient = PatientInfo(**patient.model_dump(exclude={"id"}))  # exclude id for auto-increment
#     db.add(new_patient)
#     db.commit()
#     db.refresh(new_patient)
#     return new_patient

# # @app.post("/users", response_model=PatientSchema) # Create User Endpoint without id in request body
# # def create_user(user: PatientSchema, db: Session = Depends(get_db)):
# #     new_user = PatientInfo(**user.model_dump())
# #     db.add(new_user)
# #     db.commit()
# #     db.refresh(new_user)
# #     return new_user

# @app.put("/patient/{patient_id}", response_model=PatientSchema)
# def update_patient(patient_id: int, updated_patient: PatientSchema, db: Session = Depends(get_db)):
#     patient = db.query(PatientInfo).filter(PatientInfo.id == patient_id).first()
#     if not patient:
#         raise HTTPException(status_code=404, detail="patient not found")
    
#     for key, value in updated_patient.model_dump(exclude={"id"}).items():
#         setattr(patient, key, value)
    
#     db.commit()
#     db.refresh(patient)
#     return patient

# @app.delete("/patient/{patient_id}")
# def delete_patient(patient_id: int, db: Session = Depends(get_db)):
#     patient = db.query(PatientInfo).filter(PatientInfo.id == patient_id).first()
#     if not patient:
#         raise HTTPException(status_code=404, detail="User not found")
    
#     db.delete(patient)
#     db.commit()
#     return {"detail": f"patient with ID {patient_id} deleted successfully"}


# from fastapi import FastAPI, File, UploadFile
# from azure.storage.blob import BlobServiceClient
# import os

# # app = FastAPI()

# # Replace with your actual connection string
# AZURE_CONNECTION_STRING = os.getenv('AZURE_CONNECTION_STRING')
# CONTAINER_NAME = os.getenv('CONTAINER_NAME')

# SEARCH_SERVICE_ENDPOINT = os.environ.get("AZURE_SEARCH_ENDPOINT") # Updated variable name
# SEARCH_API_KEY = os.environ.get("AZURE_SEARCH_API_KEY") # Updated variable name
# SEARCH_INDEXER_NAME = os.environ.get("AZURE_SEARCH_INDEXER_NAME", "talk2doc-indexer") # Updated variable name, and default


# blob_service_client = BlobServiceClient.from_connection_string(AZURE_CONNECTION_STRING)
# container_client = blob_service_client.get_container_client(CONTAINER_NAME)

# @app.post("/upload/")
# async def upload_file(file: UploadFile = File(...)):
#     blob_client = container_client.get_blob_client(file.filename)
#     file_data = await file.read()
#     blob_client.upload_blob(file_data, overwrite=True)
    
#     print(f"✅ File '{file.filename}' uploaded to blob storage.")

#         # Trigger the indexer after successful upload
#     print(f"🚀 Triggering indexer: {SEARCH_INDEXER_NAME}")
#     search_indexer_client.run_indexer(SEARCH_INDEXER_NAME)

#     return {"filename": file.filename, "status": "uploaded"}

# #=====================================================================


from fastapi import FastAPI, Depends, HTTPException, File, UploadFile
from azure.search.documents.indexes import SearchIndexerClient
from contextlib import asynccontextmanager
from azure.core.credentials import AzureKeyCredential
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobClient, BlobServiceClient # Ensure BlobServiceClient is imported
from dotenv import load_dotenv
import os
import uvicorn
 
# Load environment variables
load_dotenv()
 
# Configuration for Azure AI Search
SEARCH_SERVICE_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT")
SEARCH_API_KEY = os.getenv("AZURE_SEARCH_API_KEY")
SEARCH_INDEXER_NAME = os.getenv("AZURE_SEARCH_INDEXER_NAME", "talk2doc-indexer")
 
# Configuration for Azure Blob Storage
AZURE_CONNECTION_STRING = os.getenv('AZURE_CONNECTION_STRING')
CONTAINER_NAME = os.getenv('CONTAINER_NAME')
 
# NEW: Define the list of fixed PDF names
# For now, it's empty as requested. Add your critical PDF names here.
FIXED_PDF_NAMES = ["A77_ACONF14-en.pdf"]
 
# Global clients
search_indexer_client: SearchIndexerClient = None
blob_service_client: BlobServiceClient = None
container_client = None
 
@asynccontextmanager
async def lifespan(app: FastAPI):
    global search_indexer_client, blob_service_client, container_client
 
    # Initialize Azure AI Search client
    if not SEARCH_SERVICE_ENDPOINT:
        print("❌ AZURE_SEARCH_ENDPOINT is not set for Azure AI Search.")
    else:
        credential = AzureKeyCredential(SEARCH_API_KEY) if SEARCH_API_KEY else DefaultAzureCredential()
        print("🔐 Using", "API Key" if SEARCH_API_KEY else "DefaultAzureCredential", "for Azure AI Search authentication.")
        search_indexer_client = SearchIndexerClient(endpoint=SEARCH_SERVICE_ENDPOINT, credential=credential)
        try:
            indexer_status = search_indexer_client.get_indexer_status(SEARCH_INDEXER_NAME)
            print(f"✅ Connected to indexer '{SEARCH_INDEXER_NAME}'. Status: {indexer_status.last_result.status}")
        except Exception as e:
            print(f"⚠️ Indexer '{SEARCH_INDEXER_NAME}' not found or inaccessible: {e}")
 
    # Initialize Azure Blob Storage client
    if not AZURE_CONNECTION_STRING or not CONTAINER_NAME:
        print("❌ AZURE_CONNECTION_STRING or CONTAINER_NAME is not set for Azure Blob Storage.")
    else:
        try:
            blob_service_client = BlobServiceClient.from_connection_string(AZURE_CONNECTION_STRING)
            container_client = blob_service_client.get_container_client(CONTAINER_NAME)
            print(f"✅ Connected to Azure Blob Storage container '{CONTAINER_NAME}'.")
        except Exception as e:
            print(f"❌ Error connecting to Azure Blob Storage: {e}")
 
    yield
    print("🛑 Application shutting down.")
 
app = FastAPI(lifespan=lifespan)
 
# Rest of your FastAPI routes remain as they are, with the following modifications:
 
@app.post("/trigger-indexer")
async def trigger_azure_ai_search_indexer():
    if not search_indexer_client:
        raise HTTPException(status_code=500, detail="Azure AI Search client not initialized.")
    try:
        print(f"🚀 Triggering indexer: {SEARCH_INDEXER_NAME}")
        search_indexer_client.run_indexer(SEARCH_INDEXER_NAME)
        return {"message": f"Indexer '{SEARCH_INDEXER_NAME}' triggered successfully."}
    except Exception as e:
        print(f"❌ Error triggering indexer: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to trigger indexer: {str(e)}")
 
@app.get("/")
async def read_root():
    return {"message": "Azure AI Search Indexer Trigger API. Use POST /trigger-indexer to trigger the default indexer."}
 
@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    if not container_client:
        raise HTTPException(status_code=500, detail="Azure Blob Storage client not initialized.")
   
    try:
        blob_client = container_client.get_blob_client(file.filename)
        file_data = await file.read()
        blob_client.upload_blob(file_data, overwrite=True)
       
        print(f"✅ File '{file.filename}' uploaded to blob storage.")
 
        if search_indexer_client:
            print(f"🚀 Triggering indexer: {SEARCH_INDEXER_NAME}")
            search_indexer_client.run_indexer(SEARCH_INDEXER_NAME)
        else:
            print("⚠️ Azure AI Search client not initialized, skipping indexer trigger.")
   
        return {"filename": file.filename, "status": "uploaded", "indexer_triggered": bool(search_indexer_client)}
    except Exception as e:
        print(f"❌ Error during file upload or indexer trigger: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to upload file or trigger indexer: {str(e)}")
 
# MODIFIED: Endpoint to delete a file from Azure Blob Storage with fixed PDF check
@app.delete("/delete-file/{filename}")
async def delete_blob_file(filename: str):
    if not container_client:
        raise HTTPException(status_code=500, detail="Azure Blob Storage client not initialized.")
   
    # NEW: Check if the file is in the fixed list
    if filename in FIXED_PDF_NAMES:
        raise HTTPException(status_code=403, detail=f"File '{filename}' is a protected system document and cannot be deleted.")
 
    try:
        blob_client = BlobClient.from_connection_string(AZURE_CONNECTION_STRING, CONTAINER_NAME, filename)
       
        if not blob_client.exists():
            raise HTTPException(status_code=404, detail=f"File '{filename}' not found in blob storage.")
           
        blob_client.delete_blob()
        print(f"✅ File '{filename}' deleted from blob storage.")
 
        if search_indexer_client:
            print(f"🚀 Resetting indexer: {SEARCH_INDEXER_NAME} to ensure deletions are processed.")
            search_indexer_client.reset_indexer(SEARCH_INDEXER_NAME)
            print(f"🚀 Triggering indexer: {SEARCH_INDEXER_NAME} after deletion.")
            search_indexer_client.run_indexer(SEARCH_INDEXER_NAME)
        else:
            print("⚠️ Azure AI Search client not initialized, skipping indexer reset/trigger after deletion.")
       
        return {"message": f"File '{filename}' deleted successfully."}
    except HTTPException:
        raise # Re-raise HTTPExceptions (like 403 or 404)
    except Exception as e:
        print(f"❌ Error deleting file '{filename}': {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete file: {str(e)}")
 
# NEW: Endpoint to delete all non-fixed PDFs
@app.delete("/cleanup-temporary-pdfs")
async def cleanup_temporary_pdfs():
    if not container_client:
        raise HTTPException(status_code=500, detail="Azure Blob Storage client not initialized.")
   
    deleted_count = 0
    skipped_count = 0
    deleted_files = []
 
    try:
        blob_list = container_client.list_blobs()
        for blob in blob_list:
            if blob.name not in FIXED_PDF_NAMES:
                try:
                    blob_client = container_client.get_blob_client(blob.name)
                    blob_client.delete_blob()
                    print(f"✅ Cleaned up temporary file: '{blob.name}'")
                    deleted_count += 1
                    deleted_files.append(blob.name)
                except Exception as e:
                    print(f"❌ Error deleting temporary file '{blob.name}': {e}")
            else:
                skipped_count += 1
                print(f"ℹ️ Skipping protected file: '{blob.name}'")
 
        if deleted_count > 0 and search_indexer_client:
            print(f"🚀 Resetting indexer: {SEARCH_INDEXER_NAME} after cleanup.")
            search_indexer_client.reset_indexer(SEARCH_INDEXER_NAME)
            print(f"🚀 Triggering indexer: {SEARCH_INDEXER_NAME} after cleanup.")
            search_indexer_client.run_indexer(SEARCH_INDEXER_NAME)
        elif deleted_count > 0:
            print("⚠️ Azure AI Search client not initialized, skipping indexer reset/trigger after cleanup.")
       
        return {
            "message": f"Cleanup complete. Deleted {deleted_count} temporary PDFs. Skipped {skipped_count} protected PDFs.",
            "deleted_files": deleted_files
        }
    except Exception as e:
        print(f"❌ Error during cleanup process: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to perform cleanup: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
#to run command : uvicorn main:app --reload --host 127.0.0.1 --port 8080    
 