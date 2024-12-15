# 🤖 Retrieval Augmented Chatbot - Chatbot Tutor

## 📋 Overview
A RAG AI Chatbot designed for exploring textbooks and educational materials. The application includes OpenStax High School Physics as a default document and allows users to upload additional documents for AI context. Built with FastAPI backend and Streamlit frontend, organized in `api` and `app` directories.

## 📚 Default Educational Content
This application comes pre-loaded with OpenStax High School Physics textbook, which is licensed under Creative Commons Attribution License 4.0 (CC BY 4.0) by Texas Education Agency (TEA). The content is used for educational purposes and proper attribution is maintained throughout the application.

### Attribution
- **Source**: OpenStax High School Physics
- **Provider**: Texas Education Agency (TEA)
- **License**: [Creative Commons Attribution License v4.0](https://creativecommons.org/licenses/by/4.0/deed.en)
- **Usage**: Content is used for educational purposes through AI-assisted retrieval and generation

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

## 📄 Licensing
This project combines multiple licenses:

1. **Application Code**: MIT License
2. **Default Content**: Creative Commons Attribution License 4.0 (CC BY 4.0)
   - When using content from the default OpenStax textbook, proper attribution must be maintained
   - Any modifications or adaptations must be indicated
   - Commercial use is permitted under the terms of CC BY 4.0

For more information about the CC BY 4.0 license, visit the [official license deed](https://creativecommons.org/licenses/by/4.0/deed.en).