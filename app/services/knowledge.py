import io
import os
import shutil
from pathlib import Path

from dotenv import load_dotenv
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from langchain_chroma import Chroma
from langchain_community.document_loaders import DirectoryLoader, Docx2txtLoader, PyPDFLoader
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter


BASE_DIR = Path(__file__).resolve().parents[2]
ENV_PATH = BASE_DIR / ".env"

load_dotenv(ENV_PATH)

SUPPORTED_MIME_TYPES = {
    "application/pdf": ".pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
}


def get_paths() -> tuple[Path, Path]:
    knowledge_dir = Path(os.getenv("KNOWLEDGE_DIR", BASE_DIR / "knowledge_base"))
    chroma_dir = Path(os.getenv("CHROMA_DB_DIR", BASE_DIR / "chroma_db_openai"))
    return knowledge_dir, chroma_dir


def get_openai_settings() -> tuple[str, str]:
    api_key = os.getenv("OPENAI_API_KEY", "")
    embedding_model = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is missing in .env")
    return api_key, embedding_model


def get_drive_service():
    credentials_file = Path(os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE", BASE_DIR / "credentials.json"))
    if not credentials_file.exists():
        raise RuntimeError(f"Google service account file not found: {credentials_file}")

    credentials = service_account.Credentials.from_service_account_file(
        str(credentials_file),
        scopes=["https://www.googleapis.com/auth/drive.readonly"],
    )
    return build("drive", "v3", credentials=credentials)


def sync_drive_to_local() -> list[Path]:
    folder_id = os.getenv("GOOGLE_DRIVE_FOLDER_ID", "").strip()
    knowledge_dir, _ = get_paths()
    knowledge_dir.mkdir(parents=True, exist_ok=True)

    if not folder_id:
        return []

    service = get_drive_service()
    query = (
        f"'{folder_id}' in parents and trashed = false and "
        "("
        "mimeType = 'application/pdf' or "
        "mimeType = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'"
        ")"
    )

    results = service.files().list(
        q=query,
        fields="files(id,name,mimeType,modifiedTime)",
        pageSize=200,
    ).execute()

    downloaded_files: list[Path] = []
    for item in results.get("files", []):
        extension = SUPPORTED_MIME_TYPES.get(item["mimeType"])
        if not extension:
            continue

        safe_name = item["name"]
        if not safe_name.lower().endswith(extension):
            safe_name = f"{safe_name}{extension}"

        destination = knowledge_dir / safe_name
        request = service.files().get_media(fileId=item["id"])
        buffer = io.BytesIO()
        downloader = MediaIoBaseDownload(buffer, request)

        done = False
        while not done:
            _, done = downloader.next_chunk()

        content = buffer.getvalue()
        if destination.exists() and destination.read_bytes() == content:
            continue

        destination.write_bytes(content)
        downloaded_files.append(destination)

    return downloaded_files


def load_source_documents(knowledge_dir: Path):
    pdf_loader = DirectoryLoader(str(knowledge_dir), glob="*.pdf", loader_cls=PyPDFLoader)
    docx_loader = DirectoryLoader(str(knowledge_dir), glob="*.docx", loader_cls=Docx2txtLoader)
    return pdf_loader.load() + docx_loader.load()


def run_ingestion(reset_db: bool = True):
    knowledge_dir, chroma_dir = get_paths()
    api_key, embedding_model = get_openai_settings()

    knowledge_dir.mkdir(parents=True, exist_ok=True)
    docs = load_source_documents(knowledge_dir)

    if not docs:
        raise RuntimeError(f"No PDF or DOCX files found in {knowledge_dir}")

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
    chunks = text_splitter.split_documents(docs)

    if reset_db and chroma_dir.exists():
        shutil.rmtree(chroma_dir)

    embeddings = OpenAIEmbeddings(model=embedding_model, api_key=api_key)
    vector_db = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=str(chroma_dir),
    )

    print(f"Loaded {len(docs)} source documents from {knowledge_dir}")
    print(f"Created {len(chunks)} chunks")
    print(f"Saved Chroma database to {chroma_dir}")
    return vector_db


def run_automated_sync(reset_db: bool = True):
    downloaded_files = sync_drive_to_local()
    if downloaded_files:
        print(f"Downloaded {len(downloaded_files)} file(s) from Google Drive")
    else:
        print("No new Google Drive files downloaded")

    return run_ingestion(reset_db=reset_db)


if __name__ == "__main__":
    run_automated_sync(reset_db=True)
