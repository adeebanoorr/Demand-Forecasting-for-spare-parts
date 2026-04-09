# Enterprise AI Analyst - Standalone UI

This is a standalone web interface for the Spare Parts AI Analyst chatbot. It is designed to match the professional dashboard aesthetics and operates independently of the main forecasting platform.

## Prerequisites

1.  **Ollama**: Ensure Ollama is running locally with the `mistral` model installed.
    ```bash
    ollama run mistral
    ```
2.  **Node.js**: Version 18+ is required for the frontend.
3.  **Python**: Version 3.10+ is required for the backend.

## Setup & Running

### 1. Start the Chatbot API (Backend)
Open a terminal in the `chatbot` directory:
```bash
# Install dependencies if not already present
pip install fastapi uvicorn pydantic

# Run the API
python chatbot_api.py
```
The API will run on `http://localhost:8001`.

### 2. Start the Chatbot UI (Frontend)
Open another terminal in the `chatbot/chatbot_ui` directory:
```bash
# Install frontend dependencies
npm install

# Start the development server
npm run dev
```
The UI will be available at `http://localhost:5173`.

## Features
- **Sidebar Navigation**: Quick access to recent analysis and suggested queries.
- **Enterprise Aesthetics**: Professional color scheme (#234FA2, #0075BE) and modern typography.
- **Data Visualization**: Support for markdown tables and data reports directly in the chat.
- **Dynamic Interaction**: Real-time analysis with pulsing status indicators.
