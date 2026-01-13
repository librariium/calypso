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

if not HARDCOVER_API_KEY: raise ValueError("❌ Missing HARDCOVER_API_KEY")

print(f"🌲 Connecting to Pinecone Index: {INDEX_NAME}...")
pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(INDEX_NAME)

# 2. HELPER: Generate the same ID we used before
def get_safe_id(book):
    slug = book.get('slug')
    if slug:
        return f"hardcover_{slug}"
    # Fallback for old method (just in case)
    clean_title = re.sub(r'[^a-zA-Z0-9_]', '', book['title'].replace(' ', '_'))
    return f"hardcover_{clean_title.lower()[:50]}"

# 3. FETCH LOOP
def run_year_update():
    print("📅 Starting YEAR METADATA PATCH...")
    last_seen_id = 0
    total_updated = 0
    
    while True:
        # Fetch batch with release_date
        query = """
        query FetchYears($last_id: Int!) {
          books(
            where: { id: {_gt: $last_id}, description: {_is_null: false}, release_date: {_is_null: false} }
            order_by: {id: asc}
            limit: 100
          ) {
            id
            title
            slug
            release_date
          }
        }
        """
        try:
            resp = requests.post(
                "https://api.hardcover.app/v1/graphql",
                json={'query': query, 'variables': {'last_id': last_seen_id}},
                headers={"Authorization": f"Bearer {HARDCOVER_API_KEY}"}
            )
            books = resp.json().get('data', {}).get('books', [])
        except Exception as e:
            print(f"⚠️ API Error: {e}")
            time.sleep(2)
            continue

        if not books:
            print("✅ Update Complete!")
            break

        for book in books:
            if book['id'] > last_seen_id: last_seen_id = book['id']
            
            # extract year (YYYY) from "2023-05-04"
            date_str = book.get('release_date', '')
            if not date_str: continue
            
            try:
                year = int(date_str.split('-')[0]) # Get '2023'
                safe_id = get_safe_id(book)
                
                # ⚡ FAST UPDATE: Update metadata only (no vector recalculation)
                index.update(
                    id=safe_id,
                    set_metadata={"year": year}
                )
                total_updated += 1
                if total_updated % 50 == 0:
                    print(f"   ⏳ Patched {total_updated} books... (Last: {book['title']} -> {year})")
                    
            except Exception as e:
                # Often fails if the ID doesn't exist in Pinecone (which is fine, we skip it)
                pass

        time.sleep(0.2)

if __name__ == "__main__":
    run_year_update()