import json
import logging
import os
from datetime import datetime, timedelta
from fastapi import HTTPException
import jwt
import requests


# SECRET_KEY = os.getenv("SECRET_KEY")
SECRET_KEY = "30b3a89d9455ac87121a7b960a1"

 
def create_service_token():
    payload = {
        "service": "my_app",
        "exp": datetime.utcnow() + timedelta(minutes=5)
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    return token
 
def evaluate_task(caseid, sessionid, task, query, response, context, latency, cost):
    try:
        data = {
            "case_id": f"{caseid}",
            "session_id": f"{sessionid}",
            "task": f"{task}",
            "query": f"{query}",
            "app_name": "Prior Authorization",
            "response": f"{response}",
            "context": f"{context}",
            "model_name": "gpt-35-turbo",
            "latency": latency,
            "cost": cost,
            "confidence_flag": True
        }
        data = json.dumps(data).encode("utf8")
 
        data_eval = {
            "prompt": "string",
            "query":  f"{query}",
            "response": f"{response}",
            "context": f"{context}",
            "metrics": "string",
            "reference": "string"
        }
        data_eval = json.dumps(data_eval).encode("utf8")
        print(data_eval)
        token = create_service_token()
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }
 
        # print(data)
 
        response = requests.post(
            "http://localhost:8009/evaluate_request",
            data=data,
            timeout=500,
            headers=headers,
        )
        return response.json()
    except Exception as error:
        logging.error("Error: %s", str(error))
        raise HTTPException(status_code=403, detail=str(error))



def get_confidence_score(
    query=None, response=None, context=None, tasks=None, metric=None
):
    try:
        if tasks == "Q & A":
            metric = "QA Confidence Score"
        elif tasks == "Summarization":
            metric = "Summarization Confidence Score"
 
        data = {
            "query": f"{query}",
            "response": f"{response}",
            "context": f"{context}",
            "metrics": f"{metric}",
            "app_name": "Prior Authorization"
        }
        data = json.dumps(data).encode("utf8")
 
        token = create_service_token()
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }
 
        response = requests.post(
            "http://localhost:8009/evaluate",
            data=data,
            timeout=500,
            headers=headers,
        )
        return response.json()
    except Exception as error:
        logging.error("Error: %s", str(error))
        raise HTTPException(status_code=403, detail=str(error))