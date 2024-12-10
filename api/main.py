import os
from dotenv import load_dotenv
from fastapi import FastAPI, File, UploadFile, HTTPException, Header
from .db_utils import get_document_by_id

# Load environment variables from .env file
load_dotenv()

from .db_utils import (
    insert_application_logs, get_chat_history, get_all_documents, 
    insert_document_record, delete_document_record, cleanup_old_documents
)

from .pydantic_models import QueryInput, QueryResponse, DocumentInfo, DeleteFileRequest
from .langchain_utils import get_rag_chain
from .db_utils import insert_application_logs, get_chat_history, get_all_documents, insert_document_record, delete_document_record
from .chroma_utils import index_document_to_chroma, delete_doc_from_chroma

import uuid
import logging

logging.basicConfig(filename='app.log', level=logging.INFO)

app = FastAPI()


@app.post("/chat", response_model=QueryResponse)
def chat(query_input: QueryInput):
    session_id = query_input.session_id
    logging.info(f"Session ID: {session_id}, User Query: {query_input.question}, Model: {query_input.model.value}")
    if not session_id:
        session_id = str(uuid.uuid4())

    

    chat_history = get_chat_history(session_id)
    rag_chain = get_rag_chain(query_input.model.value)
    answer = rag_chain.invoke({
        "input": query_input.question,
        "chat_history": chat_history
    })['answer']
    
    insert_application_logs(session_id, query_input.question, answer, query_input.model.value)
    logging.info(f"Session ID: {session_id}, AI Response: {answer}")
    return QueryResponse(answer=answer, session_id=session_id, model=query_input.model)

from fastapi import UploadFile, File, HTTPException
import os
import shutil

@app.post("/upload-doc")
async def upload_and_index_document(file: UploadFile = File(...)):
    try:
        # Log incoming request details
        print(f"Upload request received for file: {file.filename}")
        print(f"Content type: {file.content_type}")
        
        allowed_extensions = ['.pdf', '.docx', '.html']
        file_extension = os.path.splitext(file.filename)[1].lower()
        MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB limit
        
        print(f"File extension: {file_extension}")
        print(f"Checking against allowed extensions: {allowed_extensions}")
        
        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported file type. Allowed types are: {', '.join(allowed_extensions)}"
            )
        
        try:
            # Try to use /data first, fall back to /tmp if /data isn't available
            base_temp_dir = "/data/temp" if os.access("/data", os.W_OK) else "/tmp"
            print(f"Using base temp directory: {base_temp_dir}")
            print(f"Directory exists: {os.path.exists(base_temp_dir)}")
            print(f"Directory is writable: {os.access(base_temp_dir, os.W_OK)}")
            
            os.makedirs(base_temp_dir, exist_ok=True)
            temp_file_path = os.path.join(base_temp_dir, f"temp_{file.filename}")
            print(f"Created temp file path: {temp_file_path}")
            
            file_size = 0
            print("Starting to read file...")
            
            with open(temp_file_path, "wb") as buffer:
                while chunk := await file.read(8192):
                    file_size += len(chunk)
                    if file_size > MAX_FILE_SIZE:
                        os.remove(temp_file_path)  # Clean up
                        raise HTTPException(
                            status_code=413,
                            detail="File too large. Maximum size is 10MB."
                        )
                    buffer.write(chunk)
            
            print(f"File written to temp location. Size: {file_size} bytes")
            
            print("Inserting document record...")
            file_id = insert_document_record(file.filename)
            print(f"Document record inserted with ID: {file_id}")
            
            print("Indexing document to Chroma...")
            success = index_document_to_chroma(temp_file_path, file_id)
            print(f"Chroma indexing result: {success}")
            
            if success:
                try:
                    cleanup_old_documents()
                except Exception as cleanup_error:
                    print(f"Warning: Cleanup error: {cleanup_error}")
                    
                return {
                    "message": f"File {file.filename} uploaded and indexed.",
                    "file_id": file_id
                }
            else:
                print("Failed to index document in Chroma")
                delete_document_record(file_id)
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to index {file.filename}."
                )
                
        except Exception as e:
            print(f"Error in file processing: {str(e)}")
            print(f"Error type: {type(e)}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            raise HTTPException(
                status_code=500,
                detail=f"Error processing upload: {str(e)}"
            )
            
    except Exception as outer_e:
        print(f"Outer error: {str(outer_e)}")
        print(f"Outer error type: {type(outer_e)}")
        import traceback
        print(f"Outer traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing upload: {str(outer_e)}"
        )
        
    finally:
        try:
            if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
                os.remove(temp_file_path)
                print(f"Cleaned up temp file: {temp_file_path}")
        except Exception as cleanup_e:
            print(f"Error during cleanup: {cleanup_e}")

@app.get("/list-docs", response_model=list[DocumentInfo])
def list_documents():
    return get_all_documents()

@app.post("/delete-doc")
def delete_document(request: DeleteFileRequest):
    # Fetch the document details
    document = get_document_by_id(request.file_id)
    
    # Check if this is the default document  -- **** Failsafe here in main.py uses fuction in db_utils.py ****
    if document and document['filename'] == 'OpenStaxHSPhysics.pdf':
        raise HTTPException(
            status_code=403, 
            detail="The default document cannot be deleted."
        )

    # Delete from Chroma
    chroma_delete_success = delete_doc_from_chroma(request.file_id)

    if chroma_delete_success:
        # If successfully deleted from Chroma, delete from our database
        db_delete_success = delete_document_record(request.file_id)
        if db_delete_success:
            return {"message": f"Successfully deleted document with file_id {request.file_id} from the system."}
        else:
            return {"error": f"Deleted from Chroma but failed to delete document with file_id {request.file_id} from the database."}
    else:
        return {"error": f"Failed to delete document with file_id {request.file_id} from Chroma."}

#Add the ability for an admin to delete default documents
@app.post("/admin/delete-doc")
async def admin_delete_document(file_id: int, admin_token: str = Header(None)):
    if admin_token != os.getenv("ADMIN_TOKEN"):
        raise HTTPException(status_code=403, detail="Invalid admin token")
    
    # Delete from Chroma
    chroma_delete_success = delete_doc_from_chroma(file_id)

    if chroma_delete_success:
        # If successfully deleted from Chroma, delete from our database
        db_delete_success = delete_document_record(file_id)
        if db_delete_success:
            return {"message": f"Successfully deleted document with file_id {file_id} from the system."}
        else:
            return {"error": f"Deleted from Chroma but failed to delete document with file_id {file_id} from the database."}
    else:
        return {"error": f"Failed to delete document with file_id {file_id} from Chroma."}