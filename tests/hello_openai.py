#Test OpenAI key is working and Everything is Connected to LangSmith
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

# Load the .env file
load_dotenv()

# Retrieve the OpenAI API key from the environment variable
api_key = os.getenv("OPENAI_API_KEY")

# Use the API key to initialize the ChatOpenAI object
llm = ChatOpenAI(openai_api_key=api_key)

# Invoke the LLM
response = llm.invoke("Hello, OpenAI!")
print(response)
