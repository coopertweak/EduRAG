#!/bin/bash
# Start the FastAPI backend using the PORT environment variable
uvicorn api.main:app --host 0.0.0.0 --port $PORT &

# Start Streamlit on a different port (we'll use 8501)
streamlit run app/streamlit_app.py --server.port 8501 --server.address 0.0.0.0 &

# Wait for any process to exit
wait -n

# Exit with status of process that exited first
exit $?