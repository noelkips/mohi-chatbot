# Rafiki IT: Missions of Hope International (MOHI) Support Chatbot

Rafiki IT has been consolidated into a Django project so the UI, templates, static assets, and chat API now run from one server while keeping the existing chatbot behavior.

## Stack
- Django for routing, templates, and API delivery
- LangChain + ChromaDB + OpenAI for the RAG workflow
- Django templates + static assets for the chat UI
- Optional legacy Streamlit client in `interface.py`

## Run
```bash
py -3.13 -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 127.0.0.1:8000
```

Open `http://127.0.0.1:8000/`.

## API Endpoints
- `GET /health`
- `GET /api/health`
- `POST /chat`
- `POST /api/chat`
- `POST /api/feedback`
- `GET /feedback/stats`

## Structure
- `config/`: Django project settings and top-level URLs
- `app/views.py`: page and API handlers
- `app/rafiki.py`: chatbot loading, fallback mode, and feedback storage
- `app/services/`: existing RAG logic and ingestion code
- `templates/app/`: Django template structure for the UI
- `static/app/`: frontend CSS and JavaScript for the widget

## Notes
- If the LangChain/OpenAI stack is unavailable, Rafiki falls back to built-in support responses.
- The old `frontend/` and `backend/` folders remain in the repo as reference during the migration, but Django is now the primary runtime.
