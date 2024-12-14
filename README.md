# 🤖 Retreval Augmented Chatbot - Chatbot Tutor

## 📋 Overview
Configured as a RAG AI Chatbot for exploring textbooks, a default document is loaded with an admin tool and the user can upload their own documents for AI context as well. This application combines FastAPI for the backend API service and Streamlit for the frontend user interface. The project is organized into `api` and `app` directories respectively.

## ⚙️ Setup
1. Create a `.env` file using the provided example
   - `FAST_API_URL` is only required for production (defaults to localhost:8000)
   - Set a secure `ADMIN_TOKEN` to enable default document deletion
   - External APIs can be tested using `tests/hello_openai.py`

## 📦 Installation
Install dependencies from `requirements.txt`:
```bash
pip install -r requirements.txt
```

## 🛠️ Development Environment

### Running the Application
1. Start FastAPI Backend:
```bash
uvicorn api.main:app --reload
```

2. Start Streamlit Frontend:
```bash
streamlit run app/streamlit_app.py
```

### Access Points
- FastAPI Documentation: `http://127.0.0.1:8000/docs`
- Streamlit Interface: `http://localhost:8501`

## 🌐 Production Deployment

### Backend Service
```bash
# Build
pip install -r requirements.txt

# Start
uvicorn api.main:app --host 0.0.0.0 --port $PORT
```

### Frontend Service
```bash
# Build
pip install -r requirements.txt

# Start
streamlit run app/streamlit_app.py --server.port $PORT --server.address 0.0.0.0
```

**Note**: Deploy as two separate services on render - backend API and frontend

## 🔧 Admin Tools
A local script is provided for document management:
- Upload default documents
- Delete any document (including defaults)
- List all documents
- Upload custom documents

### Running Admin Tools
```bash
python admin_tools.py
```