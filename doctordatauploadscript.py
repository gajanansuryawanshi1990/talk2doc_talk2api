
import pandas as pd
from src.server.mcp_server import engine


df = pd.read_excel(r'C:\Users\36299\Downloads\Talk2doc&Talk2API - Copy\Talk2doc&Talk2API - Copy\data\excel\doctors.xlsx')


# Rename columns to match SQL table
df.rename(columns={
    'id': 'id',
    'doctor_name': 'doctor_name',
    'designation': 'designation',
    'specialization': 'specialization',
    'title': 'title',
    'description': 'description',
    'patient_id': 'patient_id'
}, inplace=True)
df.drop(columns=['id'], inplace=True)


# Upload to SQL Server
df.to_sql('doctors', con=engine, if_exists='append', index=False)