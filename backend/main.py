import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pinecone import Pinecone
from langchain_huggingface import HuggingFaceEmbeddings

# ---------------------------------------------------------
# 1. 🏗️ SETUP & CONFIGURATION
# ---------------------------------------------------------
load_dotenv()
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
INDEX_NAME = "calypso-books"

app = FastAPI(title="Calypso API", description="Vibe Matcher for Books 🌊")

# 🛑 CORS CONFIGURATION 🛑
# Tells browser: "Allow requests from localhost:3000"
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"], 
    allow_credentials=True,
    allow_methods=["*"], # Allow all types of requests (GET, POST, etc.)
    allow_headers=["*"], # Allow all headers
)

# ---------------------------------------------------------
# 2. 🧠 LOAD THE AI COMPONENTS
# ---------------------------------------------------------
print("🤖 Loading Embedding Model...")
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

print("🌲 Connecting to Pinecone...")
pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(INDEX_NAME)

# ---------------------------------------------------------
# 3. 🔌 DEFINE DATA MODELS
# ---------------------------------------------------------
class QueryRequest(BaseModel):
    query: str
    top_k: int = 5

# ---------------------------------------------------------
# 4. 🚦 API ENDPOINTS
# ---------------------------------------------------------
@app.get("/")
def home():
    return {"status": "online", "message": "Calypso API is surfing the waves! 🌊"}

@app.post("/search")
def search_books(request: QueryRequest):
    try:
        print(f"🔎 Received query: {request.query}")

        # 1. ENCODING
        query_vector = embeddings.embed_query(request.query)

        # 2. RETRIEVAL
        search_results = index.query(
            vector=query_vector,
            top_k=request.top_k,
            include_metadata=True
        )

        # 3. FORMATTING
        books = []
        for match in search_results['matches']:
            books.append({
                "id": match['id'],
                "score": match['score'],
                "title": match['metadata'].get('title', 'Unknown'),
                "authors": match['metadata'].get('authors', 'Unknown'),
                "description": match['metadata'].get('description', 'No description'),
                "categories": match['metadata'].get('categories', 'General'),
                "thumbnail": match['metadata'].get('thumbnail', '')
            })

        return {"results": books}

    except Exception as e:
        print(f"❌ Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))