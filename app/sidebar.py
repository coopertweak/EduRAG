import streamlit as st
from api_utils import upload_document, list_documents, delete_document
import os

def auto_upload_default_document():
    """
    Automatically upload a default document if no documents exist.
    """
    default_docs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'default_docs')
    
    print(f"Attempting to auto-upload from {os.path.abspath(default_docs_dir)}")
    
    # Check if documents are already uploaded
    existing_documents = list_documents()
    print(f"Existing documents: {existing_documents}")
    
    if existing_documents:
        print("Documents already exist, skipping auto-upload")
        return
    
    # Check if the directory exists
    if not os.path.exists(default_docs_dir):
        print(f"Warning: {default_docs_dir} directory does not exist!")
        # Try alternative path for production
        alt_path = os.path.join(os.getcwd(), 'default_docs')
        if os.path.exists(alt_path):
            default_docs_dir = alt_path
        else:
            print(f"Alternative path {alt_path} also does not exist!")
            return

    # List contents of the default_docs directory
    try:
        default_files = os.listdir(default_docs_dir)
        print(f"Files in {default_docs_dir}: {default_files}")
        
        if not default_files:
            print("No files found in default_docs directory")
            return
            
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
                    
                    if upload_response:
                        st.toast(f"Auto-uploaded {filename} successfully!")
                        break
                    else:
                        print(f"Failed to upload {filename}, response was None")
                
            except Exception as e:
                print(f"Error uploading {filename}: {str(e)}")
                st.error(f"Failed to auto-upload {filename}: {str(e)}")

def display_sidebar():
    # Define protected documents that cannot be deleted
    PROTECTED_DOCUMENTS = ['OpenStaxHSPhysics.pdf']  # Add any more default documents here with a comma between like 'OpenStaxHSPhysics.pdf', 'Document2.pdf', 'Document3.pdf' 
    
    # Sidebar: Model Selection
    model_options = ["gpt-4o", "gpt-4o-mini"]
    st.sidebar.selectbox("AI Model", options=model_options, key="model")

    # Sidebar: Upload Document
    st.sidebar.header("Add Documents:")
    uploaded_file = st.sidebar.file_uploader("Choose a file", type=["pdf", "docx", "html"])
    if uploaded_file is not None:
        if st.sidebar.button("Upload"):
            with st.spinner("Uploading..."):
                upload_response = upload_document(uploaded_file)
                if upload_response:
                    st.sidebar.success(f"File '{uploaded_file.name}' uploaded successfully with ID {upload_response['file_id']}.")
                    st.session_state.documents = list_documents()

    # Sidebar: List Documents
    st.sidebar.header("Current Context")
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

    # After all other sidebar elements, add a spacer and then the attribution
    st.sidebar.markdown("---")  # Adds a horizontal line
    st.sidebar.markdown("<br>" * 2, unsafe_allow_html=True)  # Add some space
    st.sidebar.markdown("""
    <div style='font-size: 0.8em; color: #666;'>
    📚 <b>Educational Content Attribution:</b><br>
    Default content provided by OpenStax High School Physics,<br>licensed under 
    <a href='https://creativecommons.org/licenses/by/4.0/deed.en'>CC BY 4.0</a> by Texas Education Agency (TEA)
    </div>
    """, unsafe_allow_html=True)

