# Margie's Travel Assistant

An AI-powered virtual travel assistant for Margie's Travel agency, built with **Microsoft Foundry**, **Azure OpenAI GPT-4.1**, and the **OpenAI Responses API**.

The assistant combines real-time web search with company travel brochures stored in a vector database to answer customer questions about destinations, hotel packages, tourist attractions, and travel events.

---

## Features

| Feature | Detail |
|---|---|
| Model | GPT-4.1 deployed via Microsoft Foundry |
| Real-time information | `web_search_preview` built-in tool |
| Company brochures | `file_search` built-in tool + Azure OpenAI vector store |
| Conversation memory | `previous_response_id` maintains multi-turn context |
| Interfaces | Python CLI **and** React web app |

---

## Project Structure

```
margies-travel-assistant/
├── .env                        # Your credentials (not committed to source control)
├── .env.example                # Credential template — copy this to .env
│
├── core.py                     # Shared config, client factories, and tool definitions
├── travel_assistant.py         # CLI interface (terminal chatbot)
├── setup_vector_store.py       # One-time setup: uploads brochures & creates vector store
│
├── backend/
│   ├── app.py                  # FastAPI server — REST API for the React frontend
│   └── requirements.txt        # Backend Python dependencies
│
├── frontend/
│   ├── package.json            # React + Vite + react-markdown
│   ├── vite.config.js          # Proxies /api requests to the FastAPI backend
│   └── src/
│       ├── main.jsx
│       ├── App.jsx             # Chat UI — messages, typing indicator, suggested prompts
│       └── App.css             # Travel-themed styles
│
└── brochures/                  # Margie's Travel destination guides (indexed in vector store)
    ├── london.txt
    ├── paris.txt
    ├── new_york.txt
    ├── tokyo.txt
    └── dubai.txt
```

### Key file relationships

```
core.py  ──imports──►  travel_assistant.py   (CLI)
         ──imports──►  backend/app.py         (FastAPI → React)
```

`core.py` is the single source of truth for the Azure OpenAI client, system prompt, and tool configuration. Both interfaces import from it — any change made there applies everywhere.

---

## Prerequisites

- Python 3.11+
- Node.js 18+
- A Microsoft Foundry project with a GPT-4.1 deployment

---

## Setup

### 1. Configure credentials

Copy `.env.example` to `.env` and fill in your values:

```env
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/openai/v1
AZURE_OPENAI_API_KEY=your-api-key-here
AZURE_OPENAI_DEPLOYMENT=gpt-4.1
VECTOR_STORE_ID=          # filled in automatically by setup_vector_store.py
```

Find these in your **Microsoft Foundry** project:
- **Endpoint & deployment name** — Models + Endpoints
- **API key** — Settings > Keys

### 2. Install Python dependencies

```bash
# CLI and setup scripts
pip install -r requirements.txt

# FastAPI backend
pip install -r backend/requirements.txt
```

### 3. Install frontend dependencies

```bash
cd frontend
npm install
```

### 4. Create the vector store (run once)

Uploads the brochures in `brochures/` to Azure OpenAI and writes the resulting `VECTOR_STORE_ID` back to `.env`:

```bash
python setup_vector_store.py
```

---

## Running the application

### Option A — React web app (recommended)

Open two terminals from the project root:

**Terminal 1 — Backend**
```bash
uvicorn backend.app:app --reload --port 8000
```

**Terminal 2 — Frontend**
```bash
cd frontend
npm run dev
```

Open **http://localhost:5173** in your browser.

---

### Option B — CLI (terminal only)

```bash
python travel_assistant.py
```

Type your question and press Enter. Type `quit` to exit.

---

## How it works

```
User message
     │
     ▼
Responses API  (GPT-4.1 via Microsoft Foundry)
     ├── web_search_preview ──► Live web results (events, advisories, current info)
     └── file_search        ──► Margie's Travel brochures (packages, prices, tips)
     │
     ▼
Reply  +  previous_response_id  (passed on next turn to maintain conversation context)
```

1. Every user message is sent to GPT-4.1 via the **OpenAI Responses API**.
2. The model automatically decides when to call `web_search_preview` or `file_search`.
3. Each response carries an `id`; passing it as `previous_response_id` on the next request gives the model full conversation memory without re-sending message history.

---

## API endpoints (backend)

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/chat` | Send a message, receive a reply |
| `DELETE` | `/api/chat/{session_id}` | Clear conversation context |
| `GET` | `/api/health` | Check backend status |

**Request body (`POST /api/chat`)**
```json
{ "message": "What hotels do you have in Tokyo?", "session_id": "" }
```

**Response**
```json
{ "reply": "...", "session_id": "abc-123" }
```

```
You: What are the best things to do in Tokyo?
Assistant: Based on Margie's Travel brochures and current information...
           [Senso-ji Temple, Shibuya Crossing, teamLab Planets...]
           Margie's Travel offers an 8-night Tokyo & Kyoto package from $195/night...

You: How about Paris? Do you have any romantic packages?
Assistant: Absolutely! For a romantic Paris experience, Margie's Travel offers...
           [continues with context from previous question]
```
