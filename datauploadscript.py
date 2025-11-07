import pandas as pd
from src.server.mcp_server import engine


df = pd.read_excel(r'C:\Users\36299\Downloads\Talk2doc&Talk2API - Copy\Talk2doc&Talk2API - Copy\data\excel\patients.xlsx')


# Rename columns to match SQL table
df.rename(columns={
    'Patient ID': 'id',
    'Name': 'name',
    'Age': 'age',
    'Gender': 'gender',
    'Diagnosis': 'diagnosis',
    'Contact Number': 'contact_number',
    'Email': 'email',
    'Admission Date': 'admission_date',
    'Discharge Date': 'discharge_date'
}, inplace=True)
df.drop(columns=['id'], inplace=True)


# Upload to SQL Server
df.to_sql('patients', con=engine, if_exists='append', index=False)