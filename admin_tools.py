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
        # Make sure we're using the full URL
        response = requests.post(
            f"{API_URL}/admin/delete-doc",
            headers=headers,
            json={"file_id": file_id},
            timeout=30  # Add timeout
        )
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error: Status code {response.status_code}")
            print(f"Response: {response.text}")
            return None
    except requests.exceptions.ConnectionError:
        print(f"Connection error. Make sure your API_URL environment variable ({API_URL}) is correct and the service is running.")
        return None
    except Exception as e:
        print(f"Error: {str(e)}")
        return None

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