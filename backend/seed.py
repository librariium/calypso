import os
import pandas as pd
import kagglehub
from dotenv import load_dotenv
from pinecone import Pinecone
from sentence_transformers import SentenceTransformer
from tqdm.auto import tqdm

# ---------------------------------------------------------
# 1. 🕵️‍♀️ SECRET AGENT STUFF (Loading Keys)
# ---------------------------------------------------------
# Loads the invisible .env file
load_dotenv()
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")

if not PINECONE_API_KEY:
    raise ValueError("❌ PINECONE_API_KEY is missing! Check .env file!")

# ---------------------------------------------------------
# 2. 🌲 CONNECTING TO PINECONE
# ---------------------------------------------------------
pc = Pinecone(api_key=PINECONE_API_KEY)
index_name = "calypso-books"

if index_name not in pc.list_indexes().names():
    print(f"⚠️ Index '{index_name}' not found. Create it in the UI first!")
    exit()

index = pc.Index(index_name)

# ---------------------------------------------------------
# 3. 🧠 WAKING UP THE BRAIN
# ---------------------------------------------------------
print("🤖 Waking up the AI Model (all-MiniLM-L6-v2)...")
model = SentenceTransformer('all-MiniLM-L6-v2') 

# ---------------------------------------------------------
# 4. ⚡️ THE DOWNLOAD
# ---------------------------------------------------------
print("⬇️  Downloading data via kagglehub...")
path = kagglehub.dataset_download("dylanjcastillo/7k-books-with-metadata")
csv_path = os.path.join(path, "books.csv")

# ---------------------------------------------------------
# 5. 📚 READING & CLEANING
# ---------------------------------------------------------
print(f"📖 Reading {csv_path}...")
df = pd.read_csv(csv_path)

# 🧹 Step 1: Remove books with no description or ID
df = df.dropna(subset=['description', 'isbn13'])

# 🧼 Step 2: "The Deep Clean" - Filling in the blanks!
df['categories'] = df['categories'].fillna('General')
df['authors'] = df['authors'].fillna('Unknown')
df['thumbnail'] = df['thumbnail'].fillna('')
df['title'] = df['title'].fillna('Untitled')

# 🏎️ Speed Mode: First 2,000 books
df = df.head(2000) 

# ---------------------------------------------------------
# 6. 🚀 THE MEGA LOOP
# ---------------------------------------------------------
batch_size = 100
total_books = len(df)

print(f"🚀 Launching {total_books} books into the vector space...")

for i in tqdm(range(0, total_books, batch_size)):
    i_end = min(i + batch_size, total_books)
    batch = df.iloc[i:i_end]
    
    # ✍️ Combine Title + Description for the AI to read
    texts_to_embed = batch.apply(lambda x: f"{x['title']}: {x['description']}", axis=1).tolist()
    
    # ✨ Turn text into vectors
    embeddings = model.encode(texts_to_embed).tolist()
    
    # 📦 Pack metadata 
    # 👇 Added 'description' to this list!
    ids = batch['isbn13'].astype(str).tolist()
    metadata = batch[['title', 'authors', 'categories', 'thumbnail', 'description']].to_dict('records')
    
    # 🔗 Zip and Upload
    to_upsert = list(zip(ids, embeddings, metadata))
    index.upsert(vectors=to_upsert)

print("✅ MISSION ACCOMPLISHED! Calypso's brain (and memory) is updated! 🎉")