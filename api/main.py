import os
import uuid
import logging
import shutil
from dotenv import load_dotenv
from fastapi import FastAPI, File, UploadFile, HTTPException, Header, Query
from .db_utils import (
    insert_application_logs, get_chat_history, get_all_documents, 
    insert_document_record, delete_document_record, cleanup_old_documents, get_document_by_id
)
from .pydantic_models import QueryInput, QueryResponse, DocumentInfo, DeleteFileRequest
from .langchain_utils import get_rag_chain
from .chroma_utils import index_document_to_chroma, delete_doc_from_chroma

# Load environment variables from .env file
load_dotenv()

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

@app.post("/upload-doc")
async def upload_and_index_document(file: UploadFile = File(...)):
    try:
        print(f"Upload request received for file: {file.filename}")
        print(f"Content type: {file.content_type}")
        
        allowed_extensions = ['.pdf', '.docx', '.html']
        file_extension = os.path.splitext(file.filename)[1].lower()
        # Increase size limit to 25MB
        MAX_FILE_SIZE = 25 * 1024 * 1024  
        
        print(f"File extension: {file_extension}")
        
        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported file type. Allowed types are: {', '.join(allowed_extensions)}"
            )
        
        base_temp_dir = "/data/temp" if os.access("/data", os.W_OK) else "/tmp"
        os.makedirs(base_temp_dir, exist_ok=True)
        temp_file_path = os.path.join(base_temp_dir, f"temp_{file.filename}")
        
        print(f"Writing to temp file: {temp_file_path}")
        file_size = 0
        chunk_size = 1024 * 1024  # 1MB chunks
        
        try:
            with open(temp_file_path, "wb") as buffer:
                while True:
                    chunk = await file.read(chunk_size)
                    if not chunk:
                        break
                    file_size += len(chunk)
                    if file_size > MAX_FILE_SIZE:
                        raise HTTPException(
                            status_code=413,
                            detail=f"File too large. Maximum size is {MAX_FILE_SIZE/(1024*1024)}MB"
                        )
                    buffer.write(chunk)
                    print(f"Progress: {file_size/(1024*1024):.2f}MB written")
                    
            print(f"File successfully written. Total size: {file_size/(1024*1024):.2f}MB")
            
            print("Inserting document record...")
            file_id = insert_document_record(file.filename)
            
            print("Starting Chroma indexing...")
            success = index_document_to_chroma(temp_file_path, file_id)
            
            if success:
                return {
                    "message": f"File {file.filename} uploaded and indexed.",
                    "file_id": file_id
                }
            else:
                print("Failed to index document")
                delete_document_record(file_id)
                raise HTTPException(
                    status_code=500,
                    detail="Failed to index document in Chroma"
                )
                
        finally:
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
                print("Cleaned up temp file")
                
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@app.get("/list-docs", response_model=list[DocumentInfo])
def list_documents():
    return get_all_documents()

@app.post("/delete-doc")
def delete_document(request: DeleteFileRequest):
    # Fetch the document details
    document = get_document_by_id(request.file_id)
    
    # Check if this is the default document
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

@app.post("/admin/delete-doc")
async def admin_delete_document(
    file_id: int = Query(..., description="The ID of the document to delete"),
    admin_token: str = Header(None, description="Admin authorization token")
):
    # Check the admin token from headers against the environment variable
    if admin_token != os.getenv("ADMIN_TOKEN"):
        raise HTTPException(status_code=403, detail="Invalid admin token")
    
    # If token is valid, proceed with deletion logic
    chroma_delete_success = delete_doc_from_chroma(file_id)
    if chroma_delete_success:
        db_delete_success = delete_document_record(file_id)
        if db_delete_success:
            return {"message": f"Successfully deleted document with file_id {file_id} from the system."}
        else:
            return {"error": f"Deleted from Chroma but failed to delete document with file_id {file_id} from the database."}
    else:
        return {"error": f"Failed to delete document with file_id {file_id} from Chroma."}
