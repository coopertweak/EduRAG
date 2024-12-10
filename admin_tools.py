import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv('FAST_API_URL', 'http://localhost:8000')
ADMIN_TOKEN = os.getenv('ADMIN_TOKEN')

def list_documents():
    response = requests.get(f"{API_URL}/list-docs")
    return response.json()

def delete_document(file_id: int):
    headers = {
        'admin_token': ADMIN_TOKEN,
        'Content-Type': 'application/json'
    }
    try:
        # Now using query parameter instead of JSON body
        response = requests.post(
            f"{API_URL}/admin/delete-doc?file_id={file_id}",
            headers=headers,
            timeout=30
        )
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error: Status code {response.status_code}")
            print(f"Response: {response.text}")
            return None
    except requests.exceptions.ConnectionError:
        print(f"Connection error. Make sure your API_URL ({API_URL}) is correct and the service is running.")
        return None
    except Exception as e:
        print(f"Error: {str(e)}")
        return None

def upload_default_document():
    default_doc_path = 'default_docs/OpenStaxHSPhysics.pdf'
    
    if not os.path.exists(default_doc_path):
        print(f"Error: Default document not found at {default_doc_path}")
        return
    
    file_size = os.path.getsize(default_doc_path)
    print(f"Starting upload of {file_size/(1024*1024):.2f}MB file...")
    
    try:
        with open(default_doc_path, 'rb') as f:
            # Use a Session for better control
            session = requests.Session()
            session.mount('https://', requests.adapters.HTTPAdapter(max_retries=3))
            
            # Prepare the file upload
            files = {
                "file": (
                    "OpenStaxHSPhysics.pdf",
                    f,
                    'application/pdf'
                )
            }
            
            # Increase timeout and add streaming
            response = session.post(
                f"{API_URL}/upload-doc",
                files=files,
                timeout=300,  # 5 minutes
                stream=True
            )
            
            if response.status_code == 200:
                print("Default document uploaded successfully!")
                print(response.json())
                return True
            else:
                print(f"Error uploading document: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
    except requests.exceptions.Timeout:
        print("Upload timed out, but the file might have been uploaded successfully.")
        print("Please check the document list to confirm.")
        return False
    except requests.exceptions.ConnectionError:
        print("Connection error occurred, but the file might have been uploaded successfully.")
        print("Please check the document list to confirm.")
        return False
    except Exception as e:
        print(f"Upload error: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

def upload_custom_document(file_path: str):
    if not os.path.exists(file_path):
        print(f"Error: File not found at {file_path}")
        return
        
    try:
        with open(file_path, 'rb') as f:
            files = {"file": (os.path.basename(file_path), f)}
            response = requests.post(
                f"{API_URL}/upload-doc",
                files=files
            )
            
        if response.status_code == 200:
            print("Document uploaded successfully!")
            print(response.json())
        else:
            print(f"Error uploading document: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    while True:
        print("\nAdmin Tools Menu:")
        print("1. List all documents")
        print("2. Delete a document")
        print("3. Upload default document")
        print("4. Upload custom document")
        print("5. Exit")
        
        choice = input("\nEnter your choice (1-5): ")
        
        if choice == "1":
            docs = list_documents()
            print("\nCurrent documents:")
            for doc in docs:
                print(f"ID: {doc['id']}, Name: {doc['filename']}, Uploaded: {doc['upload_timestamp']}")
        
        elif choice == "2":
            file_id = int(input("Enter the document ID to delete: "))
            confirm = input(f"Are you sure you want to delete document {file_id}? (y/n): ")
            if confirm.lower() == 'y':
                result = delete_document(file_id)
                print(result)
            else:
                print("Deletion cancelled.")

        elif choice == "3":
            confirm = input("Are you sure you want to upload the default document? (y/n): ")
            if confirm.lower() == 'y':
                upload_default_document()
            else:
                print("Upload cancelled.")

        elif choice == "4":
            file_path = input("Enter the full path to the document: ")
            confirm = input(f"Are you sure you want to upload {file_path}? (y/n): ")
            if confirm.lower() == 'y':
                upload_custom_document(file_path)
            else:
                print("Upload cancelled.")
        
        elif choice == "5":
            break
        
        else:
            print("Invalid choice. Please try again.")