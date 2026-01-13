from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv
import os
from pinecone import Pinecone
from langchain_huggingface import HuggingFaceEmbeddings
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index("calypso-books")

# 👇 UPDATED: Added year_filter
class SearchQuery(BaseModel):
    query: str = ""
    author_filter: str = ""
    year_filter: str = ""     # NEW: "2024", "2023", etc.
    mode: str = "discovery"
    top_k: int = 20

@app.post("/search")
async def search(query: SearchQuery):
    search_text = query.query if query.query else "books"
    vector = embeddings.embed_query(search_text)
    
    # Fetch 1000 to cast a wide net
    search_results = index.query(
        vector=vector, 
        top_k=1000, 
        include_metadata=True
    )
    
    reranked_matches = []
    
    target_author = query.author_filter.lower().strip()
    target_year = query.year_filter.strip() # "2024"
    
    for match in search_results['matches']:
        score = match['score']
        meta = match['metadata']
        
        title = meta.get('title', 'Unknown').lower()
        authors = meta.get('authors', 'Unknown').lower()
        
        # Safe Year Check (some old books might not have a year yet)
        book_year = str(int(meta.get('year', 0))) if meta.get('year') else "0"

        # --- 🛡️ FILTERS ---
        
        # 1. Author Filter
        if target_author and target_author not in authors:
            continue

        # 2. Year Filter (Exact Match)
        # If user types "2023", we only show books from 2023.
        if target_year and target_year != book_year:
            continue

        # --- SCORING ---
        if query.mode == "library":
            if query.query and query.query.lower() in title:
                score += 100.0
            elif not query.query and target_author in authors:
                score += 50.0

        elif query.mode == "discovery":
            # Small boost for new books still applies
            if 'hardcover' in meta.get('source', ''):
                score += 0.05

        reranked_matches.append({
            "id": match['id'],
            "score": score,
            "title": meta.get('title'),
            "authors": meta.get('authors'),
            "description": meta.get('description'),
            "categories": meta.get('categories'),
            "thumbnail": meta.get('thumbnail'),
            "rating": meta.get('rating'),
            "readers": meta.get('users_read_count'),
            "year": book_year # Send year back to frontend!
        })

    reranked_matches.sort(key=lambda x: x['score'], reverse=True)
    final_results = reranked_matches[:query.top_k]

    return {"results": final_results}