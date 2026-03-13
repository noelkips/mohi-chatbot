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

## Configure Real Responses
1. Edit `.env` in the project root and set `OPENAI_API_KEY`.
2. Put your PDF or DOCX files in `knowledge_base/`.
3. Build the local vector database:

```bash
python ingest_knowledge.py
```

4. Start Django:

```bash
python manage.py runserver 127.0.0.1:8000
```

If the Django development server exits unexpectedly on Windows, use the local WSGI server instead:

```bash
python serve.py
```

If the knowledge database is missing or the API key is blank, Rafiki falls back to the built-in responses.

## Google Drive Sync
If your manuals live in Google Drive instead of the local folder:

1. Put your Google service account file at `credentials.json`
2. Share the target Google Drive folder with that service account email
3. Set `GOOGLE_DRIVE_FOLDER_ID` in `.env`
4. Run:

```bash
python sync_brain.py
```

That script downloads supported files from Drive into `knowledge_base/` and rebuilds the local Chroma database from them.

## API Endpoints
- `GET /health`
- `GET /api/health`
- `POST /chat`
- `POST /api/chat`
- `POST /api/feedback`
- `GET /feedback/stats`

## Embed Widget
Add this to any page that should open Rafiki from a floating icon:

```html
<script>
  window.RafikiWidgetConfig = {
    title: "Rafiki IT",
    subtitle: "MOHI Support"
  };
</script>
<script src="http://127.0.0.1:8000/static/app/js/rafiki-embed.js"></script>
```

Optional config keys:
- `apiBase`: optional override. If omitted, the widget automatically uses the origin it was loaded from
- `logoUrl`: override the widget logo
- `title`: widget title
- `subtitle`: widget subtitle
- `primaryColor`: button/message accent color
- `headerColor`: widget header color

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
