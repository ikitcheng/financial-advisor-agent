import os
import uuid
import time
from typing import List, Dict, Any
from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from pathlib import Path

# Import the mock database client (assuming relative path within 'service' directory)
from services.db_storage import db_client 
from services.finance_logic import CreditCardStatementPipeline

# --- Configuration ---
# NOTE: These paths are simulated. In a real environment, they must exist.

BASE_DIR = Path(__file__).resolve().parent.parent  # Go up from service/ to backend/
UPLOAD_BASE_DIR = BASE_DIR / "uploads" / "credit_card_statements"
OUTPUT_BASE_DIR = BASE_DIR / "output" / "credit_card_statements"

router = APIRouter()

# --- Pydantic Models ---
class ChatMessage(BaseModel):
    """Model for incoming chat messages."""
    session_id: str
    user_message: str

# class ExtractionResult(BaseModel):
#     """Model for the simulated document extraction output."""
#     file_name: str
#     transactions: List[Dict[str, Any]]
#     summary: str

# # --- Mock Analysis/Processing Function ---

# def process_document(input_path: str, output_path: str, file_name: str) -> ExtractionResult:
#     """
#     MOCK FUNCTION: Simulates calling the Document AI/Landing.AI model.
    
#     This function takes the saved file path, processes it, and saves a resulting
#     structured data file (e.g., JSON) to the output path before returning the data.
#     """
#     print(f"Processing document: {file_name} from {input_path}...")
    
#     # 1. Create mock output directory structure
#     os.makedirs(output_path, exist_ok=True)
    
#     # 2. Mock extracted data (the valuable data for analysis)
#     mock_transactions = [
#         {"date": "2025-05-01", "description": "Dining Out", "amount": 1500, "category": "Dining"},
#         {"date": "2025-05-10", "description": "Rent Payment", "amount": 35000, "category": "Housing"},
#         {"date": "2025-05-15", "description": "Online Shopping", "amount": 4200, "category": "Others"},
#     ]
    
#     mock_summary = f"Successfully extracted 15 transactions from {file_name}. Total spending detected: NT$42,120."

#     # 3. Simulate saving extraction output file (required by the prompt)
#     mock_output_filepath = os.path.join(output_path, f"{file_name}_extraction.json")
#     print(f"Simulating saving extraction output to: {mock_output_filepath}")

#     return ExtractionResult(
#         file_name=file_name,
#         transactions=mock_transactions,
#         summary=mock_summary
#     )

# --- API Routes ---

@router.post("/sessions/new")
def new_session():
    """Generates a new session ID for a new chat and analysis context."""
    session_id = str(uuid.uuid4())
    # Note: No need to save a new session in DB yet, as it's tracked by the ID.
    return {"session_id": session_id, "message": "New session created. Use this ID for uploads and messages."}

@router.post("/{session_id}/upload_file")
async def upload_file_and_process(
    session_id: str,
    file: UploadFile = File(...)
):
    """
    Receives an uploaded file, saves it to the session-specific upload path, 
    triggers the document processing, and stores the structured results in MongoDB.
    """
    
    upload_path = os.path.join(UPLOAD_BASE_DIR, session_id)
    output_path = os.path.join(OUTPUT_BASE_DIR, session_id)
    file_name = file.filename
    
    # 1. Simulate saving the uploaded file to the required path
    os.makedirs(upload_path, exist_ok=True)
    mock_upload_filepath = os.path.join(upload_path, file_name)


    try:
        # Read file content to simulate handling (not saving to disk here)
        file_content = await file.read()
        print(f"API Log: Simulating file upload to {mock_upload_filepath}. Size: {len(file_content)} bytes.")
        # Write file content to disk
        with open(mock_upload_filepath, "wb") as f:
            f.write(file_content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File read error: {e}")
    finally:
        await file.close()

    # 2. Call the document processing function (MOCK)
    try:
        # extraction_data = process_document(mock_upload_filepath, output_path, file_name)
        pipeline = CreditCardStatementPipeline()
        extraction_data = pipeline.process_statement(
            file_path=mock_upload_filepath,
            output_dir=output_path,
            save_markdown=True,
            save_json=True
        )
        
    except Exception as e:
        print(f"API Log: Document processing failed: {e}") 
        raise HTTPException(status_code=500, detail="Document analysis failed. Check processing service.")

    # 3. Store the structured results in MongoDB (MOCK)
    db_client.save_document_extraction(
        session_id=session_id,
        file_name=file_name,
        extraction_data=extraction_data
    )
    
    return {
        "file_name": file_name,
        "session_id": session_id,
        "status": "Processing complete and results stored.",
    }

@router.post("/{session_id}/send_message")
async def send_message(session_id: str, message: ChatMessage):
    """
    Handles an incoming chat message, stores the message, calls the LLM service (MOCK),
    and returns a response.
    """
    
    # 1. Store the user message
    db_client.save_chat_history(
        session_id=session_id, 
        message={"role": "user", "content": message.user_message}
    )

    # 2. Mock LLM Response Generation (This is where the LLM call happens)
    llm_response_content = (
        f"FastAPI Backend Response for session **{session_id}**: "
        f"Your message '{message.user_message}' has been processed. "
        "The LLM retrieved the relevant spending history and suggests focusing on reducing dining costs. "
        "I've saved this conversation turn to your history."
    )

    # 3. Store the assistant's response
    db_client.save_chat_history(
        session_id=session_id, 
        message={"role": "assistant", "content": llm_response_content}
    )

    return {
        "session_id": session_id,
        "assistant_response": llm_response_content,
        "status": "Message processed and history updated."
    }