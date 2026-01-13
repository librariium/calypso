import os
import requests
import time
import re  # 👈 ADDED: Regular Expressions for text cleaning
from dotenv import load_dotenv
from pinecone import Pinecone
from langchain_huggingface import HuggingFaceEmbeddings

# ---------------------------------------------------------
# 1. ⚙️ SETUP
# ---------------------------------------------------------
load_dotenv()
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
HARDCOVER_API_KEY = os.getenv("HARDCOVER_API_KEY")
INDEX_NAME = "calypso-books"

MIN_READERS = 10       
YEAR_TO_INGEST = 2024  

if not HARDCOVER_API_KEY:
    raise ValueError("❌ Missing HARDCOVER_API_KEY in .env")

# ---------------------------------------------------------
# 2. 🧠 INITIALIZE
# ---------------------------------------------------------
print("🤖 Loading Embedding Model...")
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

print(f"🌲 Connecting to Pinecone Index: {INDEX_NAME}...")
pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(INDEX_NAME)

# ---------------------------------------------------------
# 3. 📡 HARDCOVER API FUNCTION
# ---------------------------------------------------------
def fetch_trending_books(offset=0):
    url = "https://api.hardcover.app/v1/graphql"
    headers = {
        "Authorization": f"Bearer {HARDCOVER_API_KEY}", 
        "Content-Type": "application/json"
    }
    
    query = """
    query NewBooks($year: date!, $min_readers: Int!, $offset: Int!) {
      books(
        where: {
          release_date: {_gte: $year}, 
          users_read_count: {_gte: $min_readers},
          description: {_is_null: false}
        }
        order_by: {users_read_count: desc}
        limit: 50
        offset: $offset
      ) {
        title
        description
        users_read_count
        images { url }
        contributions { author { name } }
        taggable_counts(
          limit: 1, 
          order_by: {count: desc}, 
          where: {tag: {tag_category: {slug: {_eq: "genre"}}}}
        ) {
          tag {
            tag 
          }
        }
      }
    }
    """
    
    variables = {
        "year": f"{YEAR_TO_INGEST}-01-01",
        "min_readers": MIN_READERS,
        "offset": offset
    }

    response = requests.post(url, json={'query': query, 'variables': variables}, headers=headers)
    
    response_json = response.json()
    if 'errors' in response_json:
        print(f"\n❌ GRAPHQL ERROR: {response_json['errors']}")
        return []
        
    return response_json.get('data', {}).get('books', [])

# ---------------------------------------------------------
# 4. 🚀 MAIN INGESTION LOOP
# ---------------------------------------------------------
def run_ingestion():
    print(f"🌊 Starting Ingestion (Year >= {YEAR_TO_INGEST}, Readers >= {MIN_READERS})...")
    offset = 0
    total_added = 0
    
    while True:
        print(f"\n📡 Fetching batch (Offset: {offset})...")
        books = fetch_trending_books(offset)
        
        if not books:
            print("✅ No more books found (or empty batch). Ingestion complete!")
            break
            
        vectors_to_upsert = []
        
        for book in books:
            title = book.get('title')
            description = book.get('description') or ""
            
            if len(description) < 50: continue 

            # Extract Metadata
            authors = "Unknown"
            if book.get('contributions'):
                authors = book['contributions'][0]['author']['name']
            
            category = "General"
            if book.get('taggable_counts') and len(book['taggable_counts']) > 0:
                category = book['taggable_counts'][0]['tag']['tag']
            
            thumbnail = ""
            if book.get('images') and len(book['images']) > 0:
                thumbnail = book['images'][0]['url']

            # Embed
            text_to_embed = f"{title} by {authors}. {category}. {description}"
            vector = embeddings.embed_query(text_to_embed)
            
            # 👇 FIXED: ID Sanitization
            # 1. Replace spaces with underscores
            # 2. Remove ANYTHING that is not a letter, number, or underscore (ASCII only)
            clean_title = re.sub(r'[^a-zA-Z0-9_]', '', title.replace(' ', '_'))
            
            # 3. Create ID
            safe_id = f"hardcover_{clean_title.lower()[:50]}"
            
            record = {
                "id": safe_id,
                "values": vector,
                "metadata": {
                    "title": title,
                    "authors": authors,
                    "description": description,
                    "categories": category,
                    "thumbnail": thumbnail,
                    "source": "hardcover_ingest"
                }
            }
            vectors_to_upsert.append(record)
            print(f"   🔹 Found: {title[:30]} ({category})")

        # Upsert
        if vectors_to_upsert:
            print(f"🚀 Upserting {len(vectors_to_upsert)} vectors...")
            index.upsert(vectors=vectors_to_upsert)
            total_added += len(vectors_to_upsert)
        
        offset += 50
        time.sleep(1) 

    print(f"\n🎉 Success! Added {total_added} new books to Calypso.")

if __name__ == "__main__":
    run_ingestion()