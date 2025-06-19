# genai_chat_app

This application is a Streamlit-based GUI that allows you to chat with a local LLM (Large Language Model). The app leverages a tool-calling workflow to fetch data from external sources or execute commands automatically.

## Key Features
- Simple chat interface, powered by Streamlit, that enables interaction with a local LLM.  
- "Tool calling" implementation: LangChain tools, MCP tools.  
- Real-time feedback on the command execution results.

## Prerequisites
1. [Ollama](https://ollama.com/) must be installed on your machine.  
2. The model `llama3.2:1b` must be pulled locally via Ollama (`ollama run llama3.2:1b` or similar).  
3. Python 3.9+ is recommended.

## Setup and Run
1. Clone or download this repository.  
2. Navigate to the `genai_chat_app` folder in a terminal.
3. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Start the Streamlit application:
   ```bash
   streamlit run llm_chat_app.py
   ```
5. Open your web browser and go to the displayed local URL (e.g., http://localhost:8501) to interact with the chat app.

## Links and Resources
- Streamlit tutorial on LLM chat apps:  
  https://docs.streamlit.io/develop/tutorials/llms/build-conversational-apps  
- Additional reference on official Streamlit docs:  
  https://docs.streamlit.io/
- Ollama website:  
  https://ollama.com/  
- Ollama library (models):  
  https://ollama.com/library  
- LangChain documentation:  
  https://python.langchain.com/docs/introduction/  
- LangChain RAG tutorial:  
  https://python.langchain.com/docs/tutorials/rag/   
- Article: LLM Powered Autonomous Agents:  
  https://lilianweng.github.io/posts/2023-06-23-agent/

