import os
import requests
import time
import re
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

# 🛡️ FILTERS
MIN_READERS = 3          # Low threshold (catch gems), but no ghost data
REQUIRE_COVER = True     # Must have visuals
REQUIRE_AUTHOR = True    # Must have credit
MIN_DESC_LEN = 150       # Must make sense (paragraph length)

# 🚫 CONTENT POLICE (Deduplication & Spam Block)
BLOCKED_KEYWORDS = [
    "summary of", "analysis of", "study guide", "trivia", 
    "notebook", "journal", "planner", "calendar", "diary", 
    "untitled", "test book", "preview", "sampler", 
    "box set", "collection", "anthology" # Avoiding duplicates of series
]

# 🛑 SAFETY LIMITS
MAX_TOTAL_VECTORS = 85000  
BATCH_SIZE = 100     
START_FROM_ID = 0        

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
# 3. 📡 HARDCOVER API
# ---------------------------------------------------------
def fetch_books_cursor(last_id=0, retries=3):
    url = "https://api.hardcover.app/v1/graphql"
    headers = {
        "Authorization": f"Bearer {HARDCOVER_API_KEY}", 
        "Content-Type": "application/json"
    }
    
    query = """
    query MassIngest($last_id: Int!, $min_readers: Int!, $limit: Int!) {
      books(
        where: {
          id: {_gt: $last_id}, 
          users_read_count: {_gte: $min_readers},
          description: {_is_null: false}
        }
        order_by: {id: asc}
        limit: $limit
      ) {
        id
        title
        slug
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
        "last_id": last_id,
        "min_readers": MIN_READERS,
        "limit": BATCH_SIZE
    }

    for attempt in range(retries):
        try:
            response = requests.post(url, json={'query': query, 'variables': variables}, headers=headers, timeout=30)
            if response.status_code != 200:
                time.sleep(5)
                continue
            response_json = response.json()
            if 'errors' in response_json:
                print(f"\n❌ GRAPHQL ERROR: {response_json['errors']}")
                return []
            return response_json.get('data', {}).get('books', [])
        except Exception:
            time.sleep(5)
    return []

# ---------------------------------------------------------
# 4. 🚀 MASS INGESTION LOOP
# ---------------------------------------------------------
def run_mass_ingestion():
    print(f"🌊 Starting DUPLICATE-SAFE Ingestion...")
    print(f"   • Config: Readers>={MIN_READERS}, Desc>={MIN_DESC_LEN}")
    
    last_seen_id = START_FROM_ID
    total_added = 0
    skipped_count = 0
    
    while True:
        try:
            stats = index.describe_index_stats()
            if stats.total_vector_count >= MAX_TOTAL_VECTORS:
                print(f"🛑 Limit Reached ({MAX_TOTAL_VECTORS}). Stopping.")
                break
        except: pass

        print(f"\n📡 Fetching batch (Starting after ID: {last_seen_id})...")
        books = fetch_books_cursor(last_seen_id)
        
        if not books:
            print("✅ Sync complete!")
            break
            
        vectors_to_upsert = []
        
        for book in books:
            current_id = book.get('id')
            if current_id > last_seen_id:
                last_seen_id = current_id
                
            title = book.get('title')
            description = book.get('description') or ""
            slug = book.get('slug')
            
            # --- 🛡️ FILTERS ---
            if len(description) < MIN_DESC_LEN:
                skipped_count += 1; continue
            
            has_cover = book.get('images') and len(book['images']) > 0
            if REQUIRE_COVER and not has_cover:
                skipped_count += 1; continue

            authors = "Unknown"
            if book.get('contributions') and len(book['contributions']) > 0:
                authors = book['contributions'][0]['author']['name']
            
            if REQUIRE_AUTHOR and (not authors or authors == "Unknown"):
                skipped_count += 1; continue

            title_lower = title.lower()
            if any(bad_word in title_lower for bad_word in BLOCKED_KEYWORDS):
                print(f"   🚫 Blocked Garbage: '{title}'")
                skipped_count += 1; continue

            # --- 🆔 DEDUPLICATION LOGIC ---
            # We prioritize the 'slug' provided by Hardcover.
            # This ensures that "Harry Potter" always gets ID "hardcover_harry-potter-1"
            # no matter how many times you run this script.
            if slug:
                safe_id = f"hardcover_{slug}"
            else:
                # Fallback: strictly sanitize title to ensure consistency
                clean_title = re.sub(r'[^a-zA-Z0-9_]', '', title.replace(' ', '_'))
                safe_id = f"hardcover_{clean_title.lower()[:50]}"
            
            # --- PREPARE DATA ---
            category = "General"
            if book.get('taggable_counts') and len(book['taggable_counts']) > 0:
                category = book['taggable_counts'][0]['tag']['tag']
            
            thumbnail = book['images'][0]['url']
            text_to_embed = f"{title} by {authors}. {category}. {description}"
            vector = embeddings.embed_query(text_to_embed)
            
            vectors_to_upsert.append({
                "id": safe_id,
                "values": vector,
                "metadata": {
                    "title": title, "authors": authors, "description": description,
                    "categories": category, "thumbnail": thumbnail, "source": "hardcover_safe"
                }
            })
            print(f"   💎 Processing: {title[:30]}...")

        # --- UPSERT (OVERWRITE IF EXISTS) ---
        if vectors_to_upsert:
            print(f"🚀 Upserting {len(vectors_to_upsert)} vectors...")
            try: 
                index.upsert(vectors=vectors_to_upsert)
                total_added += len(vectors_to_upsert)
            except Exception as e: 
                print(f"⚠️ Upsert Error: {e}")
        
        print(f"   (Skipped {skipped_count} entries so far)")
        time.sleep(0.5)

    print(f"\n🎉 DONE! Added {total_added} high-quality books.")

if __name__ == "__main__":
    run_mass_ingestion()