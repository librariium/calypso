import os
import httpx
import asyncio
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pinecone import Pinecone
from langchain_huggingface import HuggingFaceEmbeddings

# ---------------------------------------------------------
# 1. 🏗️ SETUP
# ---------------------------------------------------------
load_dotenv()
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
HARDCOVER_API_KEY = os.getenv("HARDCOVER_API_KEY")
INDEX_NAME = "calypso-books"

app = FastAPI(title="Calypso API", description="Vibe Matcher for Books 🌊")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"], 
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"], 
)

# ---------------------------------------------------------
# 2. 🧠 LOAD AI & DATABASE
# ---------------------------------------------------------
print("🤖 Loading Embedding Model...")
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

print("🌲 Connecting to Pinecone...")
pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(INDEX_NAME)

class QueryRequest(BaseModel):
    query: str
    top_k: int = 6

# ---------------------------------------------------------
# 3. 🚀 HARDCOVER ENRICHMENT LOGIC
# ---------------------------------------------------------
async def fetch_hardcover_metadata(client, title):
    """
    Asks Hardcover: 'Do you know this book? Give me the HQ cover!'
    """
    if not HARDCOVER_API_KEY:
        return None

    url = "https://api.hardcover.app/v1/graphql"
    headers = {
        "Authorization": HARDCOVER_API_KEY,
        "Content-Type": "application/json"
    }
    
    # GraphQL Query: Fuzzy search by title
    query = """
    query BookSearch($q: String!) {
      books(where: {title: {_ilike: $q}}, limit: 1) {
        title
        rating
        users_read_count
        images {
          url
        }
      }
    }
    """
    
    try:
        response = await client.post(url, json={'query': query, 'variables': {'q': title}}, headers=headers)
        data = response.json()
        
        # Check if we got a hit
        if data.get('data') and data['data'].get('books'):
            book_data = data['data']['books'][0]
            
            # Extract the best image
            image_url = ""
            if book_data.get('images') and len(book_data['images']) > 0:
                image_url = book_data['images'][0]['url']
            
            return {
                "thumbnail": image_url,
                "rating": book_data.get('rating', 0),
                "readers": book_data.get('users_read_count', 0)
            }
    except Exception as e:
        print(f"⚠️ Hardcover fetch failed for {title}: {e}")
    
    return None 

# ---------------------------------------------------------
# 4. 🚦 SEARCH ENDPOINT
# ---------------------------------------------------------
@app.post("/search")
async def search_books(request: QueryRequest):
    try:
        print(f"🔎 Vibe Check: {request.query}")

        # 1. EMBED & SEARCH (Static Data from Pinecone)
        query_vector = embeddings.embed_query(request.query)
        search_results = index.query(
            vector=query_vector,
            top_k=request.top_k,
            include_metadata=True
        )

        # 2. PREPARE FOR ENRICHMENT
        books = []
        enrichment_tasks = []
        
        # Async Client for parallel requests
        async with httpx.AsyncClient() as client:
            for match in search_results['matches']:
                meta = match['metadata']
                
                # Default Object (From Kaggle/Pinecone)
                book = {
                    "id": match['id'],
                    "score": match['score'],
                    "title": meta.get('title', 'Unknown'),
                    "authors": meta.get('authors', 'Unknown'),
                    "description": meta.get('description', 'No description'),
                    "categories": meta.get('categories', 'General'),
                    "thumbnail": meta.get('thumbnail', ''), 
                    "rating": 0
                }
                
                # Queue up the enrichment
                enrichment_tasks.append(
                    fetch_hardcover_metadata(client, book['title'])
                )
                books.append(book)
            
            # 3. EXECUTE LIVE FETCH
            # This runs all 6 requests at the same time!
            live_data = await asyncio.gather(*enrichment_tasks)
            
            # Merge live data back into the books
            for i, data in enumerate(live_data):
                if data:
                    if data['thumbnail']: books[i]['thumbnail'] = data['thumbnail']
                    if data['rating']: books[i]['rating'] = data['rating']

        return {"results": books}

    except Exception as e:
        print(f"❌ Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))