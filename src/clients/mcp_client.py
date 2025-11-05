import json
import httpx
import os

from dotenv import load_dotenv
load_dotenv()
# FastAPI Server Base URL - This will be configured in .env or passed
FASTAPI_BASE_URL = os.getenv("FASTAPI_BASE_URL", "http://127.0.0.1:8001")

# --- Manual Tool Definitions for OpenAI's Function Calling ---
# These mimic the OpenAPI spec for your routes.
# Crucially, 'parameters' should match your Pydantic schemas and path/query parameters.
TOOLS_SPEC = [
    {
        "type": "function",
        "function": {
            "name": "get_patient_by_id",
            "description": "Get patient details by patient ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "patient_id": {"type": "integer", "description": "The ID of the patient"}
                },
                "required": ["patient_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_all_patients",
            "description": "Get a list of all patients.",
            "parameters": {
                "type": "object",
                "properties": {}, # No parameters
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_all_doctors",
            "description": "Get a list of all doctors.",
            "parameters": {
                "type": "object",
                "properties": {}, # No parameters
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_doctor_by_id",
            "description": "Get doctor details by doctor ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "doctor_id": {"type": "integer", "description": "The ID of the doctor"}
                },
                "required": ["doctor_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_all_studies",
            "description": "Get a list of all studies.",
            "parameters": {
                "type": "object",
                "properties": {}, # No parameters
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_study_by_id",
            "description": "Get study details by study ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "study_id": {"type": "integer", "description": "The ID of the study"}
                },
                "required": ["study_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_doctors_for_patient",
            "description": "Get all doctors associated with a specific patient.",
            "parameters": {
                "type": "object",
                "properties": {
                    "patient_id": {"type": "integer", "description": "The ID of the patient"}
                },
                "required": ["patient_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_studies_for_patient",
            "description": "Get all studies for a specific patient.",
            "parameters": {
                "type": "object",
                "properties": {
                    "patient_id": {"type": "integer", "description": "The ID of the patient"}
                },
                "required": ["patient_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_studies_for_doctor",
            "description": "Get all studies conducted by a specific doctor.",
            "parameters": {
                "type": "object",
                "properties": {
                    "doctor_id": {"type": "integer", "description": "The ID of the doctor"}
                },
                "required": ["doctor_id"],
            },
        },
    },
]


# --- Custom Tool Execution Function ---
async def call_fastapi_tool(tool_call, base_url: str = FASTAPI_BASE_URL):
    """
    Executes a FastAPI tool based on the OpenAI tool call object.
    Uses httpx for async HTTP requests.
    """
    function_name = tool_call.function.name
    function_args = json.loads(tool_call.function.arguments)

    url = ""
    method = "GET"
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            if function_name == "get_patient_by_id":
                patient_id = function_args.get("patient_id")
                if patient_id is None:
                    raise ValueError("patient_id is required for get_patient_by_id")
                url = f"{base_url}/patient/{patient_id}"
                response = await client.get(url)

            elif function_name == "get_all_patients":
                url = f"{base_url}/patients"
                response = await client.get(url)

            elif function_name == "get_all_doctors":
                url = f"{base_url}/doctors"
                response = await client.get(url)

            elif function_name == "get_doctor_by_id":
                doctor_id = function_args.get("doctor_id")
                if doctor_id is None:
                    raise ValueError("doctor_id is required for get_doctor_by_id")
                url = f"{base_url}/doctor/{doctor_id}"
                response = await client.get(url)

            elif function_name == "get_all_studies":
                url = f"{base_url}/studies"
                response = await client.get(url)

            elif function_name == "get_study_by_id":
                study_id = function_args.get("study_id")
                if study_id is None:
                    raise ValueError("study_id is required for get_study_by_id")
                url = f"{base_url}/study/{study_id}"
                response = await client.get(url)

            elif function_name == "get_doctors_for_patient":
                patient_id = function_args.get("patient_id")
                if patient_id is None:
                    raise ValueError("patient_id is required for get_doctors_for_patient")
                url = f"{base_url}/patient/{patient_id}/doctors"
                response = await client.get(url)

            elif function_name == "get_studies_for_patient":
                patient_id = function_args.get("patient_id")
                if patient_id is None:
                    raise ValueError("patient_id is required for get_studies_for_patient")
                url = f"{base_url}/patient/{patient_id}/studies"
                response = await client.get(url)

            elif function_name == "get_studies_for_doctor":
                doctor_id = function_args.get("doctor_id")
                if doctor_id is None:
                    raise ValueError("doctor_id is required for get_studies_for_doctor")
                url = f"{base_url}/doctor/{doctor_id}/studies"
                response = await client.get(url)

            else:
                return {"error": f"Unknown function: {function_name}"}

            response.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx)
            return response.json()

        except httpx.HTTPStatusError as e:
            return {
                "error": f"HTTP error occurred: {e.response.status_code}",
                "detail": e.response.text,
                "function_name": function_name,
                "url": url
            }
        except httpx.RequestError as e:
            return {
                "error": f"HTTP Request failed: {str(e)}",
                "function_name": function_name,
                "url": url
            }
        except json.JSONDecodeError as e:
            return {
                "error": f"Failed to decode JSON from response",
                "detail": str(e),
                "function_name": function_name,
                "url": url
            }
        except ValueError as e:
            return {
                "error": str(e),
                "function_name": function_name,
                "args": function_args
            }
        except Exception as e:
            return {
                "error": f"An unexpected error occurred: {str(e)}",
                "function_name": function_name,
                "url": url
            }