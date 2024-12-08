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
    # First, attempt to auto-upload a default document
    auto_upload_default_document()

    # Sidebar: Model Selection
    model_options = ["gpt-4o", "gpt-4o-mini"]
    st.sidebar.selectbox("Select Model", options=model_options, key="model")

    # Sidebar: Upload Document
    st.sidebar.header("Upload Additional Resources")
    uploaded_file = st.sidebar.file_uploader("Choose a file", type=["pdf", "docx", "html"])
    if uploaded_file is not None:
        if st.sidebar.button("Upload"):
            with st.spinner("Uploading..."):
                upload_response = upload_document(uploaded_file)
                if upload_response:
                    st.sidebar.success(f"File '{uploaded_file.name}' uploaded successfully with ID {upload_response['file_id']}.")
                    st.session_state.documents = list_documents()  # Refresh the list after upload

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
        for doc in documents:
            st.sidebar.text(f"{doc['filename']} (ID: {doc['id']}, Uploaded: {doc['upload_timestamp']})")
        
         # Filter out the default document from deletion options
        deletable_documents = [doc for doc in documents if doc['filename'] != 'OpenStaxHSPhysics.pdf']
        
        if deletable_documents:
            selected_file_id = st.sidebar.selectbox(
                "Select a document to delete", 
                options=[doc['id'] for doc in deletable_documents], 
                format_func=lambda x: next(doc['filename'] for doc in deletable_documents if doc['id'] == x)
            )
            
            if st.sidebar.button("Delete Selected Document"):
                with st.spinner("Deleting..."):
                    delete_response = delete_document(selected_file_id)
                    if delete_response:
                        st.sidebar.success(f"Document with ID {selected_file_id} deleted successfully.")
                        st.session_state.documents = list_documents()  # Refresh the list after deletion
                    else:
                        st.sidebar.error(f"Failed to delete document with ID {selected_file_id}.")
        else:
            st.sidebar.info("No additional documents available for deletion.")
            
        # Delete Document
        selected_file_id = st.sidebar.selectbox("Select a document to delete", options=[doc['id'] for doc in documents], format_func=lambda x: next(doc['filename'] for doc in documents if doc['id'] == x))
        if st.sidebar.button("Delete Selected Document"):
            with st.spinner("Deleting..."):
                delete_response = delete_document(selected_file_id)
                if delete_response:
                    st.sidebar.success(f"Document with ID {selected_file_id} deleted successfully.")
                    st.session_state.documents = list_documents()  # Refresh the list after deletion
                else:
                    st.sidebar.error(f"Failed to delete document with ID {selected_file_id}.")
