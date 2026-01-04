import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pinecone import Pinecone
from langchain_huggingface import HuggingFaceEmbeddings

# ---------------------------------------------------------
# 1. 🏗️ SETUP & CONFIGURATION
# ---------------------------------------------------------
# Loads environment variables from the .env file
load_dotenv()
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
INDEX_NAME = "calypso-books" # Matches the index created in Phase 1

# Initializes the FastAPI app (The Web Server)
app = FastAPI(title="Calypso API", description="Vibe Matcher for Books 🌊")

# ---------------------------------------------------------
# 2. 🧠 LOAD THE AI COMPONENTS
# ---------------------------------------------------------
print("🤖 Loading Embedding Model...")
# Initializes the specific AI model used to understand book text
# Must match the model used in seed.py (all-MiniLM-L6-v2)
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

print("🌲 Connecting to Pinecone...")
# Establishes connection to the Vector Database
pc = Pinecone(api_key=PINECONE_API_KEY)

# Connects specifically to the 'calypso-books' index
index = pc.Index(INDEX_NAME)

# ---------------------------------------------------------
# 3. 🔌 DEFINE DATA MODELS
# ---------------------------------------------------------
# Defines the strict shape of data expected from the frontend
# Pydantic ensures the API rejects invalid requests automatically
class QueryRequest(BaseModel):
    query: str       # The user's search text (e.g., "sad sci-fi")
    top_k: int = 5   # How many books to return (defaults to 5)

# ---------------------------------------------------------
# 4. 🚦 API ENDPOINTS
# ---------------------------------------------------------
@app.get("/")
def home():
    # Simple health check endpoint to prove the server is alive
    return {"status": "online", "message": "Calypso API is surfing the waves! 🌊"}

@app.post("/search")
def search_books(request: QueryRequest):
    # 🕵️‍♀️ THE SEARCH LOGIC
    try:
        print(f"🔎 Received query: {request.query}")

        # 1. ENCODING: Converts user text -> Vector (List of numbers)
        query_vector = embeddings.embed_query(request.query)

        # 2. RETRIEVAL: Searches Pinecone for the closest matching vectors
        # 'include_metadata=True' ensures book details (Title, Cover) return with the IDs
        search_results = index.query(
            vector=query_vector,
            top_k=request.top_k,
            include_metadata=True
        )

        # 3. FORMATTING: Cleans up the raw database response for the frontend
        books = []
        for match in search_results['matches']:
            books.append({
                "id": match['id'],
                "score": match['score'], # Similarity score (0.0 to 1.0)
                "title": match['metadata'].get('title', 'Unknown'),
                "authors": match['metadata'].get('authors', 'Unknown'),
                "description": match['metadata'].get('description', 'No description'),
                "categories": match['metadata'].get('categories', 'General'),
                "thumbnail": match['metadata'].get('thumbnail', '')
            })

        # Returns the clean list of books as JSON
        return {"results": books}

    except Exception as e:
        # Logs the error and returns a 500 Server Error to the user
        print(f"❌ Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))