#!/bin/bash
uvicorn api.main:app --host 0.0.0.0 --port $PORT & 
streamlit run app/streamlit_app.py --server.port 8501 --server.address 0.0.0.0