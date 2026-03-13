import os
import logging
from pathlib import Path

from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_classic.chains import RetrievalQA
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI, OpenAIEmbeddings


BASE_DIR = Path(__file__).resolve().parents[2]
ENV_PATH = BASE_DIR / ".env"
logger = logging.getLogger("app.rafiki")

load_dotenv(ENV_PATH)


def get_settings() -> dict[str, str]:
    knowledge_dir = Path(os.getenv("KNOWLEDGE_DIR", BASE_DIR / "knowledge_base"))
    chroma_dir = Path(os.getenv("CHROMA_DB_DIR", BASE_DIR / "chroma_db_openai"))

    return {
        "knowledge_dir": str(knowledge_dir),
        "chroma_dir": str(chroma_dir),
        "chat_model": os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini"),
        "embedding_model": os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"),
        "api_key": os.getenv("OPENAI_API_KEY", ""),
    }


def get_rafiki_answer(query: str, chat_history: list | None = None) -> str:
    settings = get_settings()
    chroma_dir = Path(settings["chroma_dir"])
    logger.info("Starting chatbot response generation")

    if not settings["api_key"]:
        raise RuntimeError("OPENAI_API_KEY is missing in .env")

    if not chroma_dir.exists():
        raise RuntimeError(
            "Knowledge database not found. Add PDF files to the knowledge folder and run `python ingest_knowledge.py`."
        )

    embeddings = OpenAIEmbeddings(
        model=settings["embedding_model"],
        api_key=settings["api_key"],
    )
    logger.info("Embeddings client initialized")
    vector_db = Chroma(
        persist_directory=str(chroma_dir),
        embedding_function=embeddings,
    )
    logger.info("Chroma database opened from %s", chroma_dir)

    llm = ChatOpenAI(
        model=settings["chat_model"],
        temperature=0.4,
        api_key=settings["api_key"],
    )
    logger.info("Chat model initialized: %s", settings["chat_model"])

    history_str = ""
    for msg in (chat_history or [])[-5:]:
        role = "Staff" if msg["role"] == "user" else "Rafiki"
        history_str += f"{role}: {msg['content']}\n"

    template = """You are Rafiki, the friendly and supportive I.T. Assistant for Missions of Hope International (MOHI).
    MOHI is a Christ-centered NGO dedicated to transforming impoverished communities in Kenya through holistic ministry.
    Your goal is to help staff with technical issues while reflecting MOHI's values of grace.

    GUIDELINES:
    1. If the answer is in the context, explain it clearly and warmly.
    2. If a user mentions stress or illness, acknowledge it with empathy first.
    3. Conciseness: Use numbered steps and bold text for menu items (e.g., **Employee** > **Leave**).
    4. If unknown, suggest contacting the I.T. department at Pangani (Ext 303/304).

    CONTEXT: {context}

    CHAT HISTORY:
    {chat_history}

    STAFF MEMBER: {question}
    RAFIKI:"""

    rafiki_prompt = PromptTemplate(
        template=template,
        input_variables=["context", "question"],
    ).partial(chat_history=history_str)

    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=vector_db.as_retriever(search_kwargs={"k": 5}),
        chain_type_kwargs={"prompt": rafiki_prompt},
    )
    logger.info("RetrievalQA chain created")

    logger.info("Invoking retrieval chain")
    response = qa_chain.invoke({"query": query, "question": query})
    logger.info("Retrieval chain completed")
    return response["result"]
