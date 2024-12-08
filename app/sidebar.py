import streamlit as st
from api_utils import upload_document, list_documents, delete_document
import os

def auto_upload_default_document():
    default_docs_dir = 'default_docs'
    
    print(f"Attempting to auto-upload from {os.path.abspath(default_docs_dir)}")
    
    # Check if the directory exists
    if not os.path.exists(default_docs_dir):
        print(f"Warning: {default_docs_dir} directory does not exist!")
        return
    
    # Check if documents are already uploaded
    existing_documents = list_documents()
    print(f"Existing documents: {existing_documents}")
    
    if existing_documents:
        print("Documents already exist, skipping auto-upload")
        return
    
    # List contents of the default_docs directory
    try:
        default_files = os.listdir(default_docs_dir)
        print(f"Files in {default_docs_dir}: {default_files}")
    except Exception as e:
        print(f"Error listing directory contents: {e}")
        return

    # Attempt to upload files
    for filename in default_files:
        file_path = os.path.join(default_docs_dir, filename)
        if os.path.isfile(file_path):
            print(f"Attempting to upload {filename}")
            try:
                # Open the file and create a file-like object
                with open(file_path, 'rb') as f:
                    # Create a custom file-like object that mimics Streamlit's UploadedFile
                    class MockUploadedFile:
                        def __init__(self, file, filename):
                            self._file = file
                            self.name = filename
                            self.type = filename.split('.')[-1]
                        
                        def read(self, size=-1):
                            return self._file.read(size)
                        
                        def close(self):
                            self._file.close()

                    # Create the mock uploaded file
                    uploaded_file = MockUploadedFile(f, filename)
                    
                    # Attempt to upload
                    upload_response = upload_document(uploaded_file)
                    print(f"Upload response for {filename}: {upload_response}")
                    
                    # If upload is successful, break the loop
                    if upload_response:
                        st.toast(f"Auto-uploaded {filename} successfully!")
                        break
                
            except Exception as e:
                print(f"Error uploading {filename}: {e}")
                st.error(f"Failed to auto-upload {filename}: {e}")

def display_sidebar():
    # Define protected documents that cannot be deleted
    PROTECTED_DOCUMENTS = ['OpenStaxHSPhysics.pdf']  # Add any more default documents here with a comma between like 'OpenStaxHSPhysics.pdf', 'Document2.pdf', 'Document3.pdf' 
    
    # First, attempt to auto-upload a default document
    auto_upload_default_document()

    # Sidebar: Model Selection
    model_options = ["gpt-4o", "gpt-4o-mini"]
    st.sidebar.selectbox("Select Model", options=model_options, key="model")

    # Sidebar: Upload Document
    st.sidebar.header("Upload Document")
    uploaded_file = st.sidebar.file_uploader("Choose a file", type=["pdf", "docx", "html"])
    if uploaded_file is not None:
        if st.sidebar.button("Upload"):
            with st.spinner("Uploading..."):
                upload_response = upload_document(uploaded_file)
                if upload_response:
                    st.sidebar.success(f"File '{uploaded_file.name}' uploaded successfully with ID {upload_response['file_id']}.")
                    st.session_state.documents = list_documents()

    # Sidebar: List Documents
    st.sidebar.header("Uploaded Documents")
    if st.sidebar.button("Refresh Document List"):
        with st.spinner("Refreshing..."):
            st.session_state.documents = list_documents()

    # Initialize document list if not present
    if "documents" not in st.session_state:
        st.session_state.documents = list_documents()

    documents = st.session_state.documents
    if documents:
        # Display all documents first
        for doc in documents:
            st.sidebar.text(f"{doc['filename']} (ID: {doc['id']}, Uploaded: {doc['upload_timestamp']})")
        
        # Get deletable documents (documents that aren't in the protected list)
        non_default_docs = [(str(doc['id']), doc['filename']) 
                           for doc in documents 
                           if doc['filename'] not in PROTECTED_DOCUMENTS]
        
        # Only show deletion UI if there are non-protected documents
        if non_default_docs:
            st.sidebar.header("Delete Documents")
            
            selected = st.sidebar.selectbox(
                "Select a document to delete",
                options=non_default_docs,
                format_func=lambda x: x[1]  # Show filename
            )
            
            if st.sidebar.button("Delete Selected Document"):
                file_id = int(selected[0])  # Convert back to integer
                with st.spinner("Deleting..."):
                    delete_response = delete_document(file_id)
                    if delete_response:
                        st.sidebar.success(f"Document deleted successfully.")
                        st.session_state.documents = list_documents()
                    else:
                        st.sidebar.error("Failed to delete document.")

