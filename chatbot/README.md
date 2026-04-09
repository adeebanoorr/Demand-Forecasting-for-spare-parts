# KPCL Spare Parts AI Analyst (v2.0) 🚀

An enterprise-grade analytical chatbot for **KPCL Spare Part Consumption** and **Demand Forecasting**. This system combines a high-speed **LangGraph State Machine** with persistent **PostgresSaver** memory and a premium **React/Vite** frontend.

---

## 🛠️ Tech Stack
*   **Brain**: [LangGraph](https://github.com/langchain-ai/langgraph) (Stateful AI Workflow)
*   **Memory**: [PostgresSaver](https://github.com/langchain-ai/langgraph-checkpoint-postgres) (Automatic LTM + STM Checkpointing)
*   **Engine**: FastAPI + Python 3.12 (Vectorized Data Processing)
*   **Database**: PostgreSQL 16 (Housed in Docker)
*   **UI**: React 19 + Vite + TailwindCSS + Lucide Icons
*   **Containerization**: Docker Compose

---

## 📂 Project Structure
```text
chatbot/
├── backend/            # FastAPI + LangGraph Logic
│   ├── agent.py        # Core AI Analyst & Graph Definition
│   ├── chatbot_api.py  # REST Endpoints
│   ├── Dockerfile      # Backend Image Configuration
│   └── requirements.txt
├── frontend/           # React/Vite User Interface
│   ├── src/           # UI Components & Styling
│   └── package.json
├── docker-compose.yml  # Orchestrates PostgreSQL + Backend
└── spare_parts_data.csv # 65k+ Row Dataset (Mounted via Volume)
```

---

## 🚀 Quick Start Instructions

### 1. Requirements
*   **Docker Desktop** (Make sure it is running)
*   **Node.js** (v20+)
*   **Ollama** (Running locally with `mistral` model)

### 2. Start the Backend (API & DB)
Navigate to the root `chatbot/` folder and run:
```powershell
docker compose up -d --build
```
*   **Verify Health**: Go to [http://localhost:8001/health](http://localhost:8001/health)

### 3. Start the Frontend (UI)
Open a new terminal in the `frontend/` folder:
```powershell
cd frontend
npm install
npm run dev
```
*   **Access Interface**: [http://localhost:5173](http://localhost:5173) (Check terminal for the exact port)

---

## 🧠 Core Features
*   **3-Tier Execution**:
    1.  **Deterministic**: Instant answers for simple totals (e.g., "Total revenue in 2024").
    2.  **Template**: Precise logic for complex rankings (e.g., "Top 5 Models").
    3.  **LLM (mistral)**: Advanced natural language reasoning with a **Self-Correcting (Ralph) Loop**.
*   **PostgresSaver Persistence**: Every message and analytical state is saved to PostgreSQL. Threads are isolated using `thread_id`.
*   **Security Guardrails**:
    *   **Execution Sandbox**: Restricts AI to safe Python operations.
    *   **Column Whitelisting**: Prevents the AI from accessing unauthorized data columns.
    *   **Zero-Infection**: Automatically strips malicious Python keywords from AI-generated plans.

---

## 📈 Analysis Examples
*   *"What was the total revenue in Ahmedabad for 2024?"*
*   *"Show me a list of the top 10 models by quantity sold."*
*   *"Which state had the highest dispatch delay last year?"*
*   *"What is the month-on-month growth of the 'BOM-123' model?"*


