# 📄 Document RAG App

An end-to-end **Retrieval-Augmented Generation (RAG)** application that allows you to upload documents, process them into a vector database, and ask questions with AI-powered answers. It also includes summarization and utility modules for enhanced document understanding.

---

## 🚀 Features
- **Document Upload & Processing** → Parse and preprocess documents into embeddings.
- **Vector Database (ChromaDB)** → Store and retrieve document chunks efficiently.
- **Question Answering (QA System)** → Ask questions and get context-aware answers from your documents.
- **Summarization** → Generate concise summaries of uploaded documents.
- **Utility Functions** → Reusable helpers for text cleaning, chunking, and embedding generation.
- **Environment Configurations** → `.env` file support for API keys and environment variables.

---

## 🗂️ Project Structure
DOCUMENT-RAG-APP/
│── app.py # Main application entry point
│── document_processor.py # Handles document loading, preprocessing & embedding
│── qa_system.py # Core RAG pipeline for question answering
│── summary_generator.py # Summarizes documents
│── utils.py # Helper utilities (chunking, cleaning, etc.)
│── requirements.txt # Python dependencies
│── .gitignore # Ignored files & folders (rag-env, pycache, etc.)
│── .env # Environment variables (API keys, etc.)
│── documents/ # Folder for storing uploaded docs
│── chroma_db/ # Local vector database storage
│── rag-env/ # (Ignored) Python virtual environment
│── pycache/ # (Ignored) Compiled Python cache

yaml
Copy code

---

## ⚙️ Setup & Installation

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/document-rag-app.git
cd document-rag-app
2. Create Virtual Environment
bash
Copy code
python -m venv rag-env
3. Activate Virtual Environment
Windows (PowerShell):

bash
Copy code
.\rag-env\Scripts\activate
Linux / MacOS:

bash
Copy code
source rag-env/bin/activate
4. Install Dependencies
bash
Copy code
pip install -r requirements.txt
5. Setup Environment Variables
Create a .env file and add your keys (example):

ini
Copy code
OPENAI_API_KEY=your_api_key_here
▶️ Running the App
bash
Copy code
python app.py
📖 Usage
Place your documents in the documents/ folder.

Run the app to process documents into chroma_db/.

Use the QA system to query your documents.

Use the summary generator to get concise document summaries.

📌 Notes
Do not commit your rag-env/ (virtual environment) or __pycache__/.

Use requirements.txt for sharing dependencies.

Extend this project with a frontend UI (Streamlit/FastAPI/React) for production use.

🛠️ Tech Stack
Python 3.10+

LangChain

ChromaDB

Transformers / OpenAI API

dotenv for environment configs

✨ Future Improvements
Web-based UI for uploading & querying documents.

Multi-document support with source highlighting.

Advanced summarization using LLMs.

Integration with external APIs (Google Drive, Notion, Slack, etc.).
