from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv
import os
from pinecone import Pinecone
from langchain_huggingface import HuggingFaceEmbeddings
from fastapi.middleware.cors import CORSMiddleware

# 1. SETUP
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

class SearchQuery(BaseModel):
    query: str = ""
    author_filter: str = ""
    year_filter: str = ""
    mode: str = "discovery"
    top_k: int = 20

@app.post("/search")
async def search(query: SearchQuery):
    # 1. Construct Search Text
    search_parts = []
    if query.query.strip(): search_parts.append(query.query)
    if query.author_filter.strip(): search_parts.append(f"written by {query.author_filter}")
    if query.year_filter.strip(): search_parts.append(f"published in {query.year_filter}")
    
    search_text = " ".join(search_parts) if search_parts else "books"
    vector = embeddings.embed_query(search_text)
    
    # 2. 🧠 THE DEEP DIVE STRATEGY
    # If looking for an Author, we cannot trust the vector score (Description might not name them).
    # We must fetch a MASSIVE number of results to ensure they are in the pile.
    if query.author_filter.strip():
        fetch_k = 10000  # 🚨 Fetch 10,000 books to find the author
    else:
        fetch_k = 1000   # Standard fetch for vibes
        
    search_results = index.query(
        vector=vector, 
        top_k=fetch_k, 
        include_metadata=True
    )
    
    reranked_matches = []
    
    # Prepare Filters
    target_author = query.author_filter.lower().strip()
    target_year = query.year_filter.strip()
    
    for match in search_results['matches']:
        score = match['score']
        meta = match['metadata']
        
        # Extract Metadata
        title = meta.get('title', 'Unknown')
        authors = meta.get('authors', 'Unknown') # Keep original casing for display
        authors_lower = authors.lower()
        
        # Handle Year
        book_year_val = meta.get('year', 0)
        book_year = str(int(book_year_val)) if book_year_val else "0"

        # --- 🛡️ FILTERS ---
        
        # 1. Author Filter (Strict substring check)
        # "Rebecca Yarros" must be inside "Rebecca Yarros, Mike Smith"
        if target_author and target_author not in authors_lower:
            continue

        # 2. Year Filter
        if target_year and target_year != book_year:
            continue

        # --- SCORING BOOSTS ---
        
        # Library Mode: Boost Author Matches to the moon 🚀
        if query.mode == "library":
            if target_author and target_author in authors_lower:
                score += 100.0 # Force Author matches to #1
            
            if query.query and query.query.lower() in title.lower():
                score += 50.0

        # Discovery Mode: Tiny nudge for new books
        elif query.mode == "discovery":
            if 'hardcover' in meta.get('source', ''):
                score += 0.05

        reranked_matches.append({
            "id": match['id'],
            "score": score,
            "title": title,
            "authors": authors,
            "description": meta.get('description'),
            "categories": meta.get('categories'),
            "thumbnail": meta.get('thumbnail'),
            "rating": meta.get('rating'),
            "readers": meta.get('users_read_count'),
            "year": book_year 
        })

    # 3. Sort & Return
    reranked_matches.sort(key=lambda x: x['score'], reverse=True)
    final_results = reranked_matches[:query.top_k]

    return {"results": final_results}