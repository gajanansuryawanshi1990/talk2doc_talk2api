import os
from dotenv import load_dotenv
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery
from openai import AzureOpenAI
 
# Load environment variables
load_dotenv()
 
def env(name: str, default: str = None, required: bool = False) -> str:
    val = os.getenv(name, default)
    if required and not val:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return val
 
def _validate_endpoint(name: str, url: str):
    if not url:
        return
    low = url.lower()
    if '<' in url or '>' in url or '%3c' in low or '%3e' in low:
        raise RuntimeError(f"Environment variable {name} looks like a placeholder.")
    if not (url.startswith("http://") or url.startswith("https://")):
        raise RuntimeError(f"Environment variable {name} should start with 'https://' - found: {url}")
 
# Azure Config
SEARCH_ENDPOINT = env("AZURE_SEARCH_ENDPOINT", required=True)
SEARCH_INDEX_NAME = env("AZURE_SEARCH_INDEX", required=True)
SEARCH_API_KEY = env("AZURE_SEARCH_KEY", required=True)
AZURE_OPENAI_ENDPOINT = env("AZURE_OPENAI_ENDPOINT", required=True)
AZURE_OPENAI_API_KEY = env("AZURE_OPENAI_API_KEY", required=True)
AZURE_OPENAI_API_VERSION = env("AZURE_OPENAI_API_VERSION", "2024-06-01")
AZURE_OPENAI_CHAT_DEPLOYMENT = env("AZURE_OPENAI_CHAT_DEPLOYMENT", required=True)
AZURE_OPENAI_EMBED_DEPLOYMENT = env("AZURE_OPENAI_EMBED_DEPLOYMENT", required=True)
 
_validate_endpoint("AZURE_OPENAI_ENDPOINT", AZURE_OPENAI_ENDPOINT)
_validate_endpoint("SEARCH_ENDPOINT", SEARCH_ENDPOINT)
 
# Clients
def get_search_client() -> SearchClient:
    return SearchClient(
        endpoint=SEARCH_ENDPOINT,
        index_name=SEARCH_INDEX_NAME,
        credential=AzureKeyCredential(SEARCH_API_KEY),
    )
 
def get_aoai_client() -> AzureOpenAI:
    return AzureOpenAI(
        azure_endpoint=AZURE_OPENAI_ENDPOINT,
        api_key=AZURE_OPENAI_API_KEY,
        api_version=AZURE_OPENAI_API_VERSION,
    )
 
search_client = get_search_client()
aoai_client = get_aoai_client()
 
# Embedding
def embed_query(text: str):
    resp = aoai_client.embeddings.create(
        model=AZURE_OPENAI_EMBED_DEPLOYMENT,
        input=text
    )
    return resp.data[0].embedding
 
# Retrieval
def retrieve_context(query: str, k: int = 5):
    try:
        qvec = embed_query(query)
        vq = VectorizedQuery(vector=qvec, k_nearest_neighbors=k, fields="content_vector")
        results = search_client.search(
            search_text=query,
            vector_queries=[vq],
            top=k,
        )
    except Exception:
        results = search_client.search(search_text=query, top=k)
 
    ctx = []
    content_fields = ["content", "text", "content_text", "body", "metadata_content"]
    source_fields = ["source", "metadata_storage_path", "metadata_storage_name", "file_name", "id", "sourcefile"]
 
    for r in results:
        content = next((r.get(f) for f in content_fields if r.get(f)), "")
        if not content:
            content = next((v for v in r.values() if isinstance(v, str) and v.strip()), "")
        source = next((r.get(f) for f in source_fields if r.get(f)), "Unknown Source")
        ctx.append({"content": content, "source": source})
    return ctx
 
# Context Builder
def build_context_text(chunks):
    if not chunks:
        return ""
    return "\n\n".join([f"Chunk {i+1} (source: {c['source']}):\n{c['content']}" for i, c in enumerate(chunks)])
 
# LLM Call
def ask_llm(query: str, context_text: str, history_msgs: list):
    system_prompt = (
        "You are a helpful assistant that answers ONLY using the provided context.\n"
        "If the answer is not present in the context, reply: 'I can’t find this in the uploaded PDF.'\n"
        "Do not include source links, citations, or document references in the responses."
    )
    messages = [{"role": "system", "content": system_prompt}] + history_msgs + [
        {"role": "user", "content": f"Context:\n{context_text}\n\nQuestion:\n{query}"}
    ]
    resp = aoai_client.chat.completions.create(
        model=AZURE_OPENAI_CHAT_DEPLOYMENT,
        messages=messages,
        temperature=0.2,
    )
    return resp.choices[0].message.content