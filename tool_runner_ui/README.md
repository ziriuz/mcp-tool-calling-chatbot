# Tool runner streamlit app

This application is a Streamlit‑based GUI that lets you chat with a local LLM (Large Language Model).  
It uses a **tool‑calling** workflow to fetch data from external sources or execute system commands automatically, giving you a simple natural‑language interface for system actions.

## Key Features
- **Chat interface** powered by Streamlit.
- **Tool‑calling**: LangChain tools, MCP tools, and a custom SQL executor.
- **Real‑time feedback** on command execution results.
- **SQLite integration**: queries a local `data/test-hr.db` database.
- **History persistence**: save and load chat sessions as `.pkl` files.

## Prerequisites
1. **Ollama** must be installed on your machine.
   ```bash
   curl -fsSL https://ollama.com/install.sh | sh
   ```
2. Pull the required LLMs (the app ships with defaults, but you can change them in the sidebar).
   ```bash
   ollama pull llama3.2:1b   # example model
   ```
3. Python 3.10+ is recommended.

## Setup
### 1. Navigate to the project directory
```bash
cd tool_runner_ui
```

### 2. Install `uv` (if not already installed)
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 3. Create a virtual environment and install dependencies
```bash
uv venv
source .venv/bin/activate          # On Windows: .venv\Scripts\activate
uv sync
```

> **Alternative** – using `pip`
> ```bash
> pip install -r requirements.txt
> ```

## Running the Streamlit application
```bash
streamlit run llm_chat_app.py
```
Open your browser and navigate to the displayed local URL (e.g., `http://localhost:8501`).

## Configuration
- The app reads the Ollama base URL from the environment variable `OLLAMA_BASE_URL`.  
  If not set, it defaults to `http://localhost:11434`.
- Default LLMs used by the app are:
  - **Agent model**: `LLAMA_3B`
  - **Coder model**: `LLAMA_3B`
  - Additional models (`QWEN25_CODER_7B`, `QWEN3_8B`, `MISTRAL`, `GPT_4O_MINI`, `GPT_OSS`) are available in the sidebar for quick switching.
- The SQLite database file is located at `data/test-hr.db`.  
  Ensure this file exists before starting the app.

## MCP Tool Integration
The sidebar contains an **MCP tools** section.
- Paste a JSON configuration or an SSE URL to attach an MCP server.
- Once attached, MCP tools become available for use in the chat.

## Links and Resources
- Streamlit tutorial on LLM chat apps:  
  https://docs.streamlit.io/develop/tutorials/llms/build-conversational-apps
- Official Streamlit docs:  
  https://docs.streamlit.io/
- Ollama website:  
  https://ollama.com/
- LangChain documentation:  
  https://python.langchain.com/docs/introduction/
- LangChain RAG tutorial:  
  https://python.langchain.com/docs/tutorials/rag/
- Article: LLM Powered Autonomous Agents:  
  https://lilianweng.github.io/posts/2023-06-23-agent/
