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
        'admin_token': ADMIN_TOKEN
    }
    response = requests.post(
        f"{API_URL}/admin/delete-doc",
        headers=headers,
        json={"file_id": file_id}
    )
    return response.json()

if __name__ == "__main__":
    while True:
        print("\nAdmin Tools Menu:")
        print("1. List all documents")
        print("2. Delete a document")
        print("3. Exit")
        
        choice = input("\nEnter your choice (1-3): ")
        
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
            break
        
        else:
            print("Invalid choice. Please try again.")