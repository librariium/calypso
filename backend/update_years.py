import os
import requests
import time
import re
from dotenv import load_dotenv
from pinecone import Pinecone

# 1. SETUP
load_dotenv()
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
HARDCOVER_API_KEY = os.getenv("HARDCOVER_API_KEY")
INDEX_NAME = "calypso-books"
CHECKPOINT_FILE = "year_update_checkpoint.txt"

if not HARDCOVER_API_KEY: raise ValueError("❌ Missing HARDCOVER_API_KEY")

print(f"🌲 Connecting to Pinecone Index: {INDEX_NAME}...")
pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(INDEX_NAME)

def get_safe_id(book, slug):
    if slug: return f"hardcover_{slug}"
    return None

def save_checkpoint(last_id):
    with open(CHECKPOINT_FILE, "w") as f: f.write(str(last_id))

def load_checkpoint():
    if os.path.exists(CHECKPOINT_FILE):
        with open(CHECKPOINT_FILE, "r") as f:
            try: return int(f.read().strip())
            except: return 0
    return 0

# 3. MAIN LOOP
def run_year_update():
    start_id = load_checkpoint()
    # If start_id is huge from previous jumps, you can reset it to 0 manually in the .txt file if you want
    print(f"🪶 FEATHERWEIGHT UPDATE: Resuming from ID: {start_id}...")
    
    last_seen_id = start_id
    total_updated = 0
    batch_size = 20 # Safe size
    fails_in_a_row = 0

    while True:
        # 👇 THE FIX: A query so simple it cannot fail.
        # We removed "release_date: {_is_null: false}" to save their CPU.
        query = """
        query FeatherFetch($last_id: Int!, $limit: Int!) {
          books(
            where: { id: {_gt: $last_id} } 
            order_by: {id: asc}
            limit: $limit
          ) {
            id
            slug
            release_date
          }
        }
        """
        try:
            resp = requests.post(
                "https://api.hardcover.app/v1/graphql",
                json={'query': query, 'variables': {'last_id': last_seen_id, 'limit': batch_size}},
                headers={"Authorization": f"Bearer {HARDCOVER_API_KEY}"},
                timeout=30
            )
            
            if resp.status_code >= 500:
                print(f"⚠️ API Busy ({resp.status_code})... Sleeping 5s.")
                time.sleep(5)
                fails_in_a_row += 1
                if fails_in_a_row > 5:
                    print("🛑 Server is completely down right now. Try again in 1 hour.")
                    break
                continue

            data = resp.json()
            books = data.get('data', {}).get('books', [])
            fails_in_a_row = 0 

        except Exception as e:
            print(f"⚠️ Net Error: {e}")
            time.sleep(5)
            continue

        if not books:
            print("✅ Update Complete!")
            break

        # Process the batch
        for book in books:
            current_id = book['id']
            if current_id > last_seen_id: last_seen_id = current_id
            
            # 👇 WE do the filtering now, not the server
            date_str = book.get('release_date', '')
            if not date_str: 
                continue # Skip books with no date
            
            try:
                year = int(date_str.split('-')[0])
                safe_id = get_safe_id(book, book.get('slug'))
                
                if safe_id:
                    # Update Pinecone
                    index.update(
                        id=safe_id,
                        set_metadata={"year": str(year)}
                    )
                    total_updated += 1
            except Exception:
                pass
        
        save_checkpoint(last_seen_id)
        print(f"   ⏳ Saved {total_updated} years... (Current ID: {last_seen_id})")
        time.sleep(0.2) 

if __name__ == "__main__":
    run_year_update()