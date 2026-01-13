import os
import requests
import time
import re
from dotenv import load_dotenv
from pinecone import Pinecone

# ---------------------------------------------------------
# 1. ⚙️ SETUP
# ---------------------------------------------------------
load_dotenv()
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
HARDCOVER_API_KEY = os.getenv("HARDCOVER_API_KEY")
INDEX_NAME = "calypso-books"

if not HARDCOVER_API_KEY:
    raise ValueError("❌ Missing HARDCOVER_API_KEY")

print(f"🌲 Connecting to Pinecone Index: {INDEX_NAME}...")
pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(INDEX_NAME)

# ---------------------------------------------------------
# 2. 🧠 THE LOGIC
# ---------------------------------------------------------
# This reconstructs exactly how we made the "Bad" IDs in the first script
def generate_bad_id(title):
    # 1. Replace spaces with underscores
    # 2. Remove special chars (like ' in 5B)
    # 3. Lowercase and limit to 50 chars
    clean_title = re.sub(r'[^a-zA-Z0-9_]', '', title.replace(' ', '_'))
    return f"hardcover_{clean_title.lower()[:50]}"

def fetch_books_cursor(last_id=0):
    url = "https://api.hardcover.app/v1/graphql"
    headers = {"Authorization": f"Bearer {HARDCOVER_API_KEY}", "Content-Type": "application/json"}
    
    # We only need ID and Title to find the duplicates
    query = """
    query FindDuplicates($last_id: Int!) {
      books(
        where: { id: {_gt: $last_id}, description: {_is_null: false} }
        order_by: {id: asc}
        limit: 100
      ) {
        id
        title
      }
    }
    """
    
    try:
        response = requests.post(url, json={'query': query, 'variables': {'last_id': last_id}}, headers=headers, timeout=10)
        return response.json().get('data', {}).get('books', [])
    except Exception as e:
        print(f"⚠️ API Error: {e}")
        return []

# ---------------------------------------------------------
# 3. 🚀 THE CLEANUP LOOP
# ---------------------------------------------------------
def run_cleanup():
    print("🧹 Starting Duplicate Cleanup...")
    print("   Target: Deleting IDs with 'underscores' (Old Format)")
    print("   Keeping: IDs with 'hyphens' (New Slug Format)\n")
    
    last_seen_id = 0
    total_deleted = 0
    
    while True:
        print(f"📡 Scanning batch (ID > {last_seen_id})...")
        books = fetch_books_cursor(last_seen_id)
        
        if not books:
            print("✅ Scan complete!")
            break
            
        # 1. Calculate the "Bad IDs" for this batch
        bad_ids_to_check = []
        for book in books:
            if book['id'] > last_seen_id:
                last_seen_id = book['id']
            
            # Generate the specific ID format we want to destroy
            bad_id = generate_bad_id(book['title'])
            bad_ids_to_check.append(bad_id)

        # 2. Ask Pinecone: "Do any of these exist?"
        # We fetch them to verify existence before deleting (saves "ghost" deletes)
        fetch_response = index.fetch(ids=bad_ids_to_check)
        ids_found = list(fetch_response['vectors'].keys())
        
        if ids_found:
            print(f"   🔥 Found {len(ids_found)} duplicates. Deleting...")
            # 3. Delete them!
            index.delete(ids=ids_found)
            total_deleted += len(ids_found)
            # visual feedback
            for deleted_id in ids_found[:3]:
                print(f"      - Deleted: {deleted_id}")
            if len(ids_found) > 3: print("      ...and more")
        else:
            print("   ✨ Clean batch (no duplicates found).")
            
        time.sleep(0.2)

    print(f"\n🎉 CLEANUP COMPLETE! Removed {total_deleted} duplicates.")

if __name__ == "__main__":
    run_cleanup()