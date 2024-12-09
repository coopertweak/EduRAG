import os
from dotenv import load_dotenv
from fastapi import FastAPI, File, UploadFile, HTTPException, Header
from .db_utils import get_document_by_id

# Load environment variables from .env file
load_dotenv()

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
def upload_and_index_document(file: UploadFile = File(...)):
    allowed_extensions = ['.pdf', '.docx', '.html']
    file_extension = os.path.splitext(file.filename)[1].lower()
    
    if file_extension not in allowed_extensions:
        raise HTTPException(status_code=400, detail=f"Unsupported file type. Allowed types are: {', '.join(allowed_extensions)}")
    
    # Create temp directory if it doesn't exist
    os.makedirs("temp", exist_ok=True)
    temp_file_path = os.path.join("temp", f"temp_{file.filename}")
    
    try:
        # Save the uploaded file to a temporary file
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        file_id = insert_document_record(file.filename)
        success = index_document_to_chroma(temp_file_path, file_id)
        
        if success:
            return {"message": f"File {file.filename} has been successfully uploaded and indexed.", "file_id": file_id}
        else:
            delete_document_record(file_id)
            raise HTTPException(status_code=500, detail=f"Failed to index {file.filename}.")
    except Exception as e:
        print(f"Error during upload: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

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