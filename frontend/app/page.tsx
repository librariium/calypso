"use client";

import { useState } from "react";
import axios from "axios";
import { Search, BookHeart, Sparkles, Coffee } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

// ---------------------------------------------------------
// 🍬 TYPE DEFINITIONS
// ---------------------------------------------------------
interface Book {
  id: string;
  title: string;
  authors: string;
  description: string;
  categories: string;
  thumbnail: string;
  score: number;
}

export default function Home() {
  // ---------------------------------------------------------
  // 🎣 STATE MANAGEMENT
  // ---------------------------------------------------------
  const [query, setQuery] = useState("");
  const [books, setBooks] = useState<Book[]>([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);

  // ---------------------------------------------------------
  // 🚀 SEARCH LOGIC
  // ---------------------------------------------------------
  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setSearched(true);
    setBooks([]);

    try {
      // Sends request to backend
      const response = await axios.post("http://127.0.0.1:8000/search", {
        query: query,
        top_k: 6 
      });

      setBooks(response.data.results);
    } catch (error) {
      console.error("Search failed:", error);
    } finally {
      setLoading(false);
    }
  };

  // ---------------------------------------------------------
  // 🎨 UI RENDER (Pastel Edition)
  // ---------------------------------------------------------
  return (
    <main className="min-h-screen p-6 md:p-12 flex flex-col items-center">
      
      <div className="max-w-6xl w-full flex flex-col items-center">
        
        {/* 🔹 HERO SECTION */}
        <motion.div 
          initial={{ opacity: 0, y: -20 }} 
          animate={{ opacity: 1, y: 0 }}
          className="text-center space-y-4 mb-12 max-w-2xl mt-8"
        >
          {/* Logo Icon Bubble */}
          <div className="inline-flex p-5 bg-white rounded-full shadow-xl shadow-rose-100 mb-4">
            <BookHeart size={48} className="text-rose-400" />
          </div>
          
          {/* Title Group */}
          <div>
            <h1 className="text-6xl font-black tracking-tight text-slate-800 leading-tight">
              Calypso
              <span className="text-rose-400">.</span>
            </h1>
            
            <p className="text-rose-400 font-serif italic text-xl tracking-wide opacity-90 mt-2">
              uncovering the hidden
            </p>
          </div>
          
          {/* 👇 UPDATED: Short, poetic, and keeps the 'Concealed/Found' metaphor */}
          <p className="text-slate-500 text-lg font-medium pt-4 leading-relaxed max-w-xl mx-auto">
            Stories concealed in the deep, waiting to be found.
          </p>
        </motion.div>

        {/* 🔹 SEARCH BAR */}
        <motion.div 
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="w-full max-w-2xl relative mb-16 z-10"
        >
          <form 
            onSubmit={handleSearch} 
            className="relative flex items-center bg-white p-2 rounded-full shadow-2xl shadow-rose-100/50 border border-rose-50 transition-all focus-within:ring-4 focus-within:ring-rose-100"
          >
            <div className="pl-6 text-rose-300">
              <Search className="w-6 h-6" />
            </div>
            
            <input
              type="text"
              placeholder="e.g., 'a story about a lost robot finding home'..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="w-full p-4 bg-transparent text-lg text-slate-700 placeholder-slate-300 focus:outline-none"
            />
            
            <button 
              type="submit"
              disabled={loading}
              className="px-8 py-4 bg-gradient-to-r from-rose-400 to-orange-300 hover:from-rose-500 hover:to-orange-400 text-white rounded-full font-bold shadow-lg transition-transform active:scale-95 disabled:opacity-50 flex items-center gap-2"
            >
              {loading ? <Sparkles className="animate-spin w-5 h-5" /> : "Search"}
            </button>
          </form>
        </motion.div>

        {/* 🔹 RESULTS GRID */}
        <div className="w-full grid grid-cols-1 lg:grid-cols-2 gap-8">
          <AnimatePresence>
            {books.map((book, index) => (
              <motion.div
                key={book.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.95 }}
                transition={{ delay: index * 0.1 }}
                className="group flex flex-col sm:flex-row bg-white rounded-3xl overflow-hidden shadow-sm hover:shadow-xl hover:shadow-rose-100 transition-all duration-300 border border-slate-100"
              >
                {/* 🖼️ BOOK COVER */}
                <div className="sm:w-40 h-64 sm:h-auto bg-slate-100 relative flex-shrink-0 overflow-hidden">
                   {book.thumbnail ? (
                     <img 
                       src={book.thumbnail} 
                       alt={book.title} 
                       className="w-full h-full object-cover mix-blend-multiply opacity-90 group-hover:opacity-100 group-hover:scale-105 transition-all duration-500"
                     />
                   ) : (
                     <div className="w-full h-full flex items-center justify-center text-rose-200">
                       <BookHeart size={40} />
                     </div>
                   )}
                   
                   <div className="absolute top-3 left-3 bg-white/90 backdrop-blur text-xs font-bold px-3 py-1.5 rounded-full text-rose-500 shadow-sm">
                     {Math.round(book.score * 100)}% Match
                   </div>
                </div>

                {/* 📝 CONTENT */}
                <div className="p-8 flex flex-col justify-between w-full">
                  <div>
                    <div className="flex items-start mb-3">
                      <span className="bg-rose-50 text-rose-500 text-xs font-bold px-3 py-1 rounded-full uppercase tracking-wider">
                        {book.categories}
                      </span>
                    </div>
                    
                    <h3 className="text-xl font-bold text-slate-800 leading-tight mb-2 group-hover:text-rose-500 transition-colors">
                      {book.title}
                    </h3>
                    <p className="text-sm text-slate-400 font-medium mb-4">{book.authors}</p>
                    
                    <p className="text-sm text-slate-500 leading-relaxed line-clamp-3">
                      {book.description}
                    </p>
                  </div>
                  
                  <div className="mt-6 pt-4 border-t border-slate-50 flex justify-end">
                    <button className="text-xs font-bold text-rose-400 hover:text-rose-600 transition-colors uppercase tracking-widest flex items-center gap-1">
                      Details <span>→</span>
                    </button>
                  </div>
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
        </div>

        {/* 👻 EMPTY STATE */}
        {searched && books.length === 0 && !loading && (
          <motion.div 
            initial={{ opacity: 0 }} 
            animate={{ opacity: 1 }}
            className="text-center py-20 bg-white/50 rounded-3xl p-12 w-full max-w-lg mt-8"
          >
            <div className="inline-block p-6 bg-rose-50 rounded-full mb-4">
              <Coffee className="w-10 h-10 text-rose-300" />
            </div>
            <h3 className="text-xl font-bold text-slate-700">No matches found</h3>
            <p className="text-slate-400 mt-2">The ocean is vast, but this search came up empty.</p>
          </motion.div>
        )}

      </div>
    </main>
  );
}