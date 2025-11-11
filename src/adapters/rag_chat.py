# import os
# from dotenv import load_dotenv
# from azure.core.credentials import AzureKeyCredential
# from azure.search.documents import SearchClient
# from azure.search.documents.models import VectorizedQuery
# from openai import AzureOpenAI
 
# # Load environment variables
# load_dotenv()
 
# def env(name: str, default: str = None, required: bool = False) -> str:
#     val = os.getenv(name, default)
#     if required and not val:
#         raise RuntimeError(f"Missing required environment variable: {name}")
#     return val
 
# def _validate_endpoint(name: str, url: str):
#     if not url:
#         return
#     low = url.lower()
#     if '<' in url or '>' in url or '%3c' in low or '%3e' in low:
#         raise RuntimeError(f"Environment variable {name} looks like a placeholder.")
#     if not (url.startswith("http://") or url.startswith("https://")):
#         raise RuntimeError(f"Environment variable {name} should start with 'https://' - found: {url}")
 
# # Azure Config
# SEARCH_ENDPOINT = env("AZURE_SEARCH_ENDPOINT", required=True)
# SEARCH_INDEX_NAME = env("AZURE_SEARCH_INDEX", required=True)
# SEARCH_API_KEY = env("AZURE_SEARCH_KEY", required=True)
# AZURE_OPENAI_ENDPOINT = env("AZURE_OPENAI_ENDPOINT", required=True)
# AZURE_OPENAI_API_KEY = env("AZURE_OPENAI_API_KEY", required=True)
# AZURE_OPENAI_API_VERSION = env("AZURE_OPENAI_API_VERSION", "2024-06-01")
# AZURE_OPENAI_CHAT_DEPLOYMENT = env("AZURE_OPENAI_CHAT_DEPLOYMENT", required=True)
# AZURE_OPENAI_EMBED_DEPLOYMENT = env("AZURE_OPENAI_EMBED_DEPLOYMENT", required=True)
 
# _validate_endpoint("AZURE_OPENAI_ENDPOINT", AZURE_OPENAI_ENDPOINT)
# _validate_endpoint("SEARCH_ENDPOINT", SEARCH_ENDPOINT)
 
# # Clients
# def get_search_client() -> SearchClient:
#     return SearchClient(
#         endpoint=SEARCH_ENDPOINT,
#         index_name=SEARCH_INDEX_NAME,
#         credential=AzureKeyCredential(SEARCH_API_KEY),
#     )
 
# def get_aoai_client() -> AzureOpenAI:
#     return AzureOpenAI(
#         azure_endpoint=AZURE_OPENAI_ENDPOINT,
#         api_key=AZURE_OPENAI_API_KEY,
#         api_version=AZURE_OPENAI_API_VERSION,
#     )
 
# search_client = get_search_client()
# aoai_client = get_aoai_client()
 
# # Embedding
# def embed_query(text: str):
#     resp = aoai_client.embeddings.create(
#         model=AZURE_OPENAI_EMBED_DEPLOYMENT,
#         input=text
#     )
#     return resp.data[0].embedding
 
# # Retrieval
# def retrieve_context(query: str, k: int = 5):
#     try:
#         qvec = embed_query(query)
#         vq = VectorizedQuery(vector=qvec, k_nearest_neighbors=k, fields="content_vector")
#         results = search_client.search(
#             search_text=query,
#             vector_queries=[vq],
#             top=k,
#         )
#     except Exception:
#         results = search_client.search(search_text=query, top=k)
 
#     ctx = []
#     content_fields = ["content", "text", "content_text", "body", "metadata_content"]
#     source_fields = ["source", "metadata_storage_path", "metadata_storage_name", "file_name", "id", "sourcefile"]
 
#     for r in results:
#         content = next((r.get(f) for f in content_fields if r.get(f)), "")
#         if not content:
#             content = next((v for v in r.values() if isinstance(v, str) and v.strip()), "")
#         source = next((r.get(f) for f in source_fields if r.get(f)), "Unknown Source")
#         ctx.append({"content": content, "source": source})
#     return ctx
 
# # Context Builder
# def build_context_text(chunks):
#     if not chunks:
#         return ""
#     return "\n\n".join([f"Chunk {i+1} (source: {c['source']}):\n{c['content']}" for i, c in enumerate(chunks)])
 
# # LLM Call
# def ask_llm(query: str, context_text: str, history_msgs: list):
#     system_prompt = (
#         "You are a helpful assistant that answers ONLY using the provided context.\n"
#         "If the answer is not present in the context, reply: 'I can’t find this in the uploaded PDF.'\n"
#         "Do not include source links, citations, or document references in the responses."
#     )
#     messages = [{"role": "system", "content": system_prompt}] + history_msgs + [
#         {"role": "user", "content": f"Context:\n{context_text}\n\nQuestion:\n{query}"}
#     ]
#     resp = aoai_client.chat.completions.create(
#         model=AZURE_OPENAI_CHAT_DEPLOYMENT,
#         messages=messages,
#         temperature=0.2,
#     )
#     return resp.choices[0].message.content


import os
import base64
from urllib.parse import urlparse, unquote # Import unquote
from dotenv import load_dotenv
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery
from openai import AzureOpenAI
import re # Import re for regex
 
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
 
 
def extract_pdf_name(source_value: str) -> str:
    """
    Extract clean PDF filename from various source formats,
    including handling URL decoding for spaces.
   
    Args:
        source_value: Source string (could be base64, URL, or filename)
       
    Returns:
        Clean PDF filename
    """
    try:
        # If it's already a clean filename, return it
        if source_value.lower().endswith('.pdf') and '/' not in source_value and '\\' not in source_value:
            return source_value
       
        # Try to decode if it looks like base64
        if not source_value.startswith('http') and len(source_value) > 50:
            try:
                # Fix padding if needed
                missing_padding = len(source_value) % 4
                if missing_padding:
                    source_value += '=' * (4 - missing_padding)
               
                # Decode base64
                decoded_url = base64.b64decode(source_value).decode('utf-8')
                source_value = decoded_url
            except Exception:
                pass  # Not base64, continue with original value
       
        # Extract filename from URL path and decode URL-encoded characters
        if 'http' in source_value:
            parsed = urlparse(source_value)
            path = parsed.path
            filename = os.path.basename(path)
           
            # Decode URL-encoded characters like %20 to spaces
            filename = unquote(filename) # Added unquote
           
            # Clean up the filename
            if filename and filename.lower().endswith('.pdf'):
                return filename
       
        # Try to find PDF filename in the string and decode
        pdf_match = re.search(r'([^/\\]+\.pdf)', source_value, re.IGNORECASE)
        if pdf_match:
            return unquote(pdf_match.group(1)) # Added unquote
       
        # If all else fails, return the last part of the path and decode
        parts = source_value.replace('\\', '/').split('/')
        for part in reversed(parts):
            if part and '.pdf' in part.lower():
                return unquote(part) # Added unquote
       
        # Ultimate fallback, ensure it's decoded
        return unquote("Unknown.pdf")
       
    except Exception as e:
        print(f"Error extracting PDF name from '{source_value}': {e}")
        return unquote("Unknown.pdf")
 
 
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
       
        # Get source and extract clean PDF name
        raw_source = next((r.get(f) for f in source_fields if r.get(f)), "Unknown Source")
        clean_source = extract_pdf_name(raw_source)
       
        ctx.append({
            "content": content,
            "source": clean_source,
            "raw_source": raw_source  # Keep original for debugging if needed
        })
   
    return ctx
 
 
def get_unique_sources(chunks: list) -> list:
    """
    Get unique PDF sources from chunks
   
    Args:
        chunks: List of chunk dictionaries with 'source' key
       
    Returns:
        List of unique PDF filenames
    """
    seen = set()
    unique_sources = []
   
    for chunk in chunks:
        source = chunk.get('source', 'Unknown.pdf')
        if source not in seen:
            seen.add(source)
            unique_sources.append(source)
   
    return unique_sources
 
 
def format_sources_list(sources: list) -> str:
    """
    Format sources as a numbered list
   
    Args:
        sources: List of PDF filenames
       
    Returns:
        Formatted string like "1. FOOTBALL.pdf\n2. Cricket.pdf"
    """
    if not sources:
        return "No sources available"
   
    if len(sources) == 1:
        return sources[0]
   
    # Multiple sources - numbered list
    formatted = []
    for i, source in enumerate(sources, 1):
        formatted.append(f"{i}. {source}")
   
    return "\n".join(formatted)
 
 
# Context Builder
def build_context_text(chunks):
    if not chunks:
        return ""
    return "\n\n".join([f"Chunk {i+1} (source: {c['source']}):\n{c['content']}" for i, c in enumerate(chunks)])
 
# LLM Call
def ask_llm(query: str, context_text: str, history_msgs: list, chunks: list = None):
    """
    Ask LLM with context and automatically format sources.
   
    Args:
        query: User's question
        context_text: Retrieved context
        history_msgs: Conversation history
        chunks: List of chunk dictionaries (to extract sources)
       
    Returns:
        Answer with properly formatted sources
    """
    # Get all unique sources from the retrieved chunks (before LLM answers)
    all_retrieved_unique_sources = []
    if chunks:
        all_retrieved_unique_sources = get_unique_sources(chunks)
   
    # Create a simple list of sources for the LLM to refer to
    source_reference_text = ""
    if all_retrieved_unique_sources:
        source_reference_text = "\n\nAvailable Document Sources: " + ", ".join(all_retrieved_unique_sources) + "\n"
   
    system_prompt = (
        "You are a helpful assistant that answers ONLY using the provided context.\n"
        "If the answer is not present in the context, reply: 'I can't find this in the uploaded PDF.'\n"
        "When referencing sources, only list the specific document name(s) (e.g., 'cricket.pdf') that were directly used to answer the question.\n"
        "At the end of your answer, if any sources were used, include a 'Sources' section listing ONLY those documents. "
        "Format the sources as a numbered list (e.g., 'Sources:\n1. document1.pdf\n2. document2.pdf') if more than one, or 'Source: document1.pdf' if only one.\n"
    )
   
    messages = [{"role": "system", "content": system_prompt}] + history_msgs + [
        {"role": "user", "content": f"Context:\n{context_text}{source_reference_text}\n\nQuestion:\n{query}"}
    ]
   
    resp = aoai_client.chat.completions.create(
        model=AZURE_OPENAI_CHAT_DEPLOYMENT,
        messages=messages,
        temperature=0.2,
    )
   
    answer = resp.choices[0].message.content
   
    # Post-process to ensure sources are correctly listed and only used ones are present
    # This involves trying to extract what the LLM *said* it used
   
    # Regex to find a Sources section and extract items
    source_section_match = re.search(r'Sources:\s*\n((?:\d+\.\s*.+\.pdf\n?)+)', answer, re.IGNORECASE)
    single_source_match = re.search(r'Source:\s*(.+\.pdf)', answer, re.IGNORECASE)
 
    extracted_sources = set()
    if source_section_match:
        # Multiple sources
        source_lines = source_section_match.group(1).strip().split('\n')
        for line in source_lines:
            match = re.search(r'\d+\.\s*(.+\.pdf)', line, re.IGNORECASE)
            if match:
                extracted_sources.add(match.group(1).strip())
    elif single_source_match:
        # Single source
        extracted_sources.add(single_source_match.group(1).strip())
 
    # Filter extracted sources against what was actually retrieved
    # This is a critical step to avoid hallucinated sources
    final_sources_for_output = []
    retrieved_source_names = {s.lower() for s in all_retrieved_unique_sources} # For case-insensitive comparison
 
    # Only include extracted sources that were actually part of the retrieved chunks
    for es in extracted_sources:
        if es.lower() in retrieved_source_names:
            final_sources_for_output.append(es)
   
    # If LLM didn't include sources or included invalid ones,
    # or if we found valid sources but the LLM's formatting was off,
    # then append/replace with a correctly formatted list of *all retrieved* sources as a fallback.
    # This is a compromise: if the LLM fails to identify, we show all retrieved.
    # A more advanced approach would involve a separate LLM call to identify sources.
    if not final_sources_for_output and all_retrieved_unique_sources:
        # Fallback: Use all retrieved unique sources if LLM didn't specify or specified incorrectly
        formatted_sources = format_sources_list(all_retrieved_unique_sources)
        if "Sources:" not in answer and "Source:" not in answer:
            if len(all_retrieved_unique_sources) == 1:
                answer += f"\n\nSource: {formatted_sources}"
            else:
                answer += f"\n\nSources:\n{formatted_sources}"
        else:
            # If a source section exists but was empty/incorrect, try to replace it
            if source_section_match:
                answer = answer.replace(source_section_match.group(0), f"Sources:\n{formatted_sources}")
            elif single_source_match:
                 answer = answer.replace(single_source_match.group(0), f"Source: {formatted_sources}")
            else: # Should not happen if matches worked
                if len(all_retrieved_unique_sources) == 1:
                    answer += f"\n\nSource: {formatted_sources}"
                else:
                    answer += f"\n\nSources:\n{formatted_sources}"
 
    elif final_sources_for_output:
        # If the LLM successfully extracted sources and they were valid,
        # ensure they are formatted correctly at the end.
        formatted_final_sources = format_sources_list(list(final_sources_for_output))
        # Remove any existing Source/Sources section to replace it with the clean one
        if source_section_match:
            answer = re.sub(r'Sources:\s*\n((?:\d+\.\s*.+\.pdf\n?)+)', '', answer, flags=re.IGNORECASE).strip()
        elif single_source_match:
            answer = re.sub(r'Source:\s*(.+\.pdf)', '', answer, flags=re.IGNORECASE).strip()
 
        if len(final_sources_for_output) == 1:
            answer += f"\n\nSource: {formatted_final_sources}"
        else:
            answer += f"\n\nSources:\n{formatted_final_sources}"
 
 
    return answer
 
# CLI Testing
if __name__ == "__main__":
    print("RAG Chat System - Test Mode")
    print("=" * 60)
   
    # Test source extraction
    test_sources = [
        "aHR0cHM6Ly9jYXBzdG9uZWdyb3VwMS5ibG9iLmNvcmUud2luZG93cy5uZXQvZG9jdW1lbnRzL0E3N19BQ09ORjE0LWVuLnBkZg",
        "FOOTBALL.pdf",
        "https://example.blob.core.windows.net/documents/Cricket.pdf",
        "/path/to/document/Basketball.pdf",
        "https://example.com/docs/Malaria%20Guidelines.pdf", # Added for testing issue 2
        "Another%20Document.pdf" # Added for testing issue 2
    ]
   
    print("\nTesting Source Extraction:")
    print("-" * 60)
    for source in test_sources:
        clean = extract_pdf_name(source)
        print(f"Input:  {source[:50]}...")
        print(f"Output: {clean}\n")
   
    # Test retrieve and format
    print("\nTest Query:")
    query = input("Enter your question (or press Enter to skip): ").strip()
   
    if query:
        print(f"\nSearching for: {query}")
        chunks = retrieve_context(query, k=5)
       
        print(f"\nFound {len(chunks)} chunks")
       
        unique_sources = get_unique_sources(chunks)
        print(f"\nUnique Sources Found: {len(unique_sources)}")
        print(format_sources_list(unique_sources))
       
        context_text = build_context_text(chunks)
        answer = ask_llm(query, context_text, [], chunks)
       
        print("\n" + "=" * 60)
        print("Answer:")
        print("=" * 60)
        print(answer)
 