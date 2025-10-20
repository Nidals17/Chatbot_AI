# 🧠 RAG-Enhanced LLM Chatbot  
An intelligent chatbot system built with **Streamlit** (frontend) and **FastAPI** (backend), combining **Retrieval-Augmented Generation (RAG)** and **general LLM reasoning**.  
It can switch seamlessly between document-based answers and open-domain reasoning, powered by **DeepSeek**, **OpenAI**, or **Gemini** APIs.

---

## 🎬 Demo Video  
**Watch the app in action!**  
[![Demo Video](https://img.shields.io/badge/Demo%20Video-🎥-red)](https://drive.google.com/file/d/1gdHzO-lBwIDtDN4ioaMxsV0LVeTstewi/view?usp=drive_link)

---

## ✨ Features
- Hybrid **RAG + LLM** architecture  
- Toggle between **document-based** and **general** chatbot modes  
- Dynamic **system message customization** (personality & tone control)  
- Real-time **chat interface** with persistent history  
- Supports multiple **LLMs** (DeepSeek, OpenAI, Gemini)  
- Vector database management using **ChromaDB**  
- RAG context generation via **sentence-transformer embeddings**  
- Streamlit-based UI with configurable model parameters (temperature, max tokens)  
- Fully Dockerized for easy deployment  

---

## 🧩 Project Structure

```bash
chatbot/
├── chatbot.py                     # Streamlit frontend main entry
│
├── backend/
│   ├── app.py                     # FastAPI backend
│   ├── config.py                  # Global configuration (models, constants)
│   ├── rag_engine.py              # RAG logic (ChromaDB vector search)
│   ├── app_logger.py              # Logging utilities
│
├── pages/                         # Streamlit multipage UI
│   ├── LLM.py                     # LLM model configuration page
│   ├── RAG.py                     # RAG control and database selection
│   ├── Database_Manager.py        # Manage ChromaDB collections
│   └── System_Config.py           # Customize system messages & parameters
│
├── requirements.txt               # Dependencies
├── Dockerfile.backend             # FastAPI backend image
├── Dockerfile.frontend            # Streamlit frontend image
├── docker-compose.yml             # Multi-container orchestration
└── README.md                      # Project documentation

```

## System Requirements

Python 3.9+

Docker 24+

At least 4GB RAM

Internet connection for LLM APIs

API keys for one or more models:

-   DeepSeek

-   OpenAI

-   Google Gemini

## Getting Started

### Method 1: Local Development

1. Clone the repository
```bash
git clone https://github.com/Nidals17/Chatbot-AI.git
```

2. Set up environment variables:
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate
```

3. Install Dependencies:
```bash
pip install -r requirements.txt
```


4. Run Backend (FastAPI):
```bash
uvicorn backend.app:app --reload
```


➡️ Access FastAPI docs at http://127.0.0.1:8000/docs


5. Run Frontend(Streamlit):
```bash
streamlit run chatbot.py
```
➡️ Access UI at http://localhost:8501


### Method 2: 🐳 Docker Deployment (Recommended)

1. Build and Start Containers

```bash
docker-compose build
docker-compose up
```

2️⃣ Access the Services

🖥️ Frontend (Streamlit) → http://localhost:8501

⚙️ Backend (FastAPI) → http://localhost:8000/docs


## 🧠 Usage

1. Go to LLM Page → Select model (DeepSeek, Gemini, OpenAI) and provide API key

2. Go to RAG Page → Choose to enable/disable document-based retrieval

3. Go to System Config Page → Adjust system message, temperature, and token limits

4. Go to Chatbot Page → Start chatting!

    - If RAG is enabled, responses will be grounded in your document database

    - If RAG is disabled, the chatbot answers using general LLM knowledge


## ⚙️ Configuration
🔹 Backend Settings (in backend/config.py)

```bash
deepseek_base_url = "https://api.deepseek.com/v1/chat/completions"
gemini_model = "gemini-pro"
openai_model = "gpt-3.5-turbo"
```

🔹 RAG Embedding Settings (in backend/rag_engine.py)


```bash
embedding_model = "sentence-transformers/all-mpnet-base-v2"
chunk_size = 800
chunk_overlap = 100
```

## 🧰 Dependencies

Key libraries used in the project:

- fastapi==0.115.0
- uvicorn==0.30.0
- streamlit==1.38.0
- httpx==0.27.0
- pydantic==2.7.0
- langchain==0.2.7
- chromadb==0.4.24
- sentence-transformers==2.2.2
- google-generativeai==0.5.4
- openai==1.34.0

## 🧪 API Endpoints

POST /query_llm

Query any supported model (DeepSeek / Gemini / OpenAI) with or without RAG context.

## ⚡ Performance Tips

Use smaller embedding models for faster RAG retrieval

Adjust chunk_size and overlap for document balance

Keep prompts short when using long context

Regularly clean old ChromaDB indexes

## License
[MIT License](LICENSE)