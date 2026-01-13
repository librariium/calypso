"use client";

import { useState } from "react";
import axios from "axios";
import { Search, BookHeart, Sparkles, Coffee, Library, Compass, X, User, BookOpen, Calendar } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

interface Book {
  id: string;
  title: string;
  authors: string;
  description: string;
  categories: string;
  thumbnail: string;
  score: number;
  rating?: number;
  readers?: number;
  year?: string;
}

export default function Home() {
  const [mainQuery, setMainQuery] = useState("");     
  const [authorQuery, setAuthorQuery] = useState(""); 
  const [yearQuery, setYearQuery] = useState(""); // 👈 NEW: Year State
  
  const [books, setBooks] = useState<Book[]>([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);
  const [mode, setMode] = useState<"discovery" | "library">("discovery");

  const switchMode = (newMode: "discovery" | "library") => {
    setMode(newMode);
    setBooks([]);
    setSearched(false);
    setMainQuery("");
    setAuthorQuery("");
    setYearQuery("");
  };

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!mainQuery.trim() && !authorQuery.trim() && !yearQuery.trim()) return;

    setLoading(true);
    setSearched(true);
    setBooks([]);

    try {
      const response = await axios.post("http://127.0.0.1:8000/search", {
        query: mainQuery,
        author_filter: authorQuery,
        year_filter: yearQuery, // 👈 Send Year
        mode: mode,
        top_k: 20
      });

      setBooks(response.data.results);
    } catch (error) {
      console.error("Search failed:", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen p-6 md:p-12 flex flex-col items-center bg-slate-50/50">
      <div className="max-w-6xl w-full flex flex-col items-center">
        
        {/* HEADER */}
        <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }} className="text-center space-y-4 mb-8 max-w-2xl mt-8">
          <div className="inline-flex p-5 bg-white rounded-full shadow-xl shadow-rose-100 mb-4">
            <BookHeart size={48} className="text-rose-400" />
          </div>
          <div>
            <h1 className="text-6xl font-black tracking-tight text-slate-800 leading-tight">Calypso<span className="text-rose-400">.</span></h1>
            <p className="text-rose-400 font-serif italic text-xl tracking-wide opacity-90 mt-2">uncovering the hidden</p>
          </div>
        </motion.div>

        {/* MODE TOGGLE */}
        <div className="flex bg-white p-1 rounded-full shadow-md border border-slate-100 mb-6 relative z-20">
            <button onClick={() => switchMode("discovery")} className={`flex items-center gap-2 px-6 py-2 rounded-full text-sm font-bold transition-all ${mode === "discovery" ? "bg-rose-100 text-rose-600 shadow-sm" : "text-slate-400 hover:text-slate-600"}`}>
                <Compass size={16} /> Discovery
            </button>
            <button onClick={() => switchMode("library")} className={`flex items-center gap-2 px-6 py-2 rounded-full text-sm font-bold transition-all ${mode === "library" ? "bg-cyan-100 text-cyan-700 shadow-sm" : "text-slate-400 hover:text-slate-600"}`}>
                <Library size={16} /> Library
            </button>
        </div>

        {/* 🔹 3-PART SEARCH BAR */}
        <motion.div className="w-full max-w-4xl relative mb-16 z-10">
          <form onSubmit={handleSearch} className={`flex flex-col md:flex-row gap-3 bg-white p-3 rounded-3xl shadow-2xl border transition-all ${mode === "discovery" ? "shadow-rose-100/50 border-rose-50" : "shadow-cyan-100/50 border-cyan-50"}`}>
            
            {/* 1. MAIN QUERY */}
            <div className="flex-grow relative group w-full md:w-2/5">
                <div className={`absolute top-4 left-4 ${mode === "discovery" ? "text-rose-300" : "text-cyan-300"}`}>
                    {mode === "discovery" ? <Sparkles size={20} /> : <BookOpen size={20} />}
                </div>
                <input
                    type="text"
                    value={mainQuery}
                    onChange={(e) => setMainQuery(e.target.value)}
                    placeholder={mode === "discovery" ? "Describe vibe..." : "Book Title..."}
                    className="w-full pl-12 pr-4 py-4 bg-slate-50 rounded-2xl focus:outline-none focus:ring-2 focus:ring-opacity-50 transition-all text-slate-700 placeholder-slate-400"
                    style={{ '--tw-ring-color': mode === 'discovery' ? '#fda4af' : '#67e8f9' } as any}
                />
            </div>

            {/* 2. AUTHOR FILTER */}
            <div className="flex-grow md:w-1/4 relative">
                <div className="absolute top-4 left-4 text-slate-300">
                    <User size={20} />
                </div>
                <input
                    type="text"
                    value={authorQuery}
                    onChange={(e) => setAuthorQuery(e.target.value)}
                    placeholder="Author..."
                    className="w-full pl-12 pr-4 py-4 bg-slate-50 rounded-2xl focus:outline-none focus:ring-2 focus:ring-slate-200 transition-all text-slate-700 placeholder-slate-400"
                />
            </div>
            
            {/* 3. YEAR FILTER (NEW) */}
            <div className="flex-grow md:w-1/5 relative">
                <div className="absolute top-4 left-4 text-slate-300">
                    <Calendar size={20} />
                </div>
                <input
                    type="text"
                    value={yearQuery}
                    onChange={(e) => setYearQuery(e.target.value)}
                    placeholder="Year..."
                    className="w-full pl-12 pr-4 py-4 bg-slate-50 rounded-2xl focus:outline-none focus:ring-2 focus:ring-slate-200 transition-all text-slate-700 placeholder-slate-400"
                />
            </div>
            
            {/* SEARCH BUTTON */}
            <button 
              type="submit"
              disabled={loading}
              className={`px-6 py-4 text-white rounded-2xl font-bold shadow-lg transition-transform active:scale-95 disabled:opacity-50 flex items-center justify-center gap-2 md:w-auto w-full ${
                  mode === "discovery" 
                  ? "bg-gradient-to-r from-rose-400 to-orange-300 hover:from-rose-500 hover:to-orange-400"
                  : "bg-gradient-to-r from-cyan-500 to-blue-500 hover:from-cyan-600 hover:to-blue-600"
              }`}
            >
              {loading ? <div className="animate-spin w-5 h-5 border-2 border-white border-t-transparent rounded-full"/> : <Search size={20} />}
            </button>
          </form>
        </motion.div>

        {/* RESULTS GRID */}
        <div className="w-full grid grid-cols-1 lg:grid-cols-2 gap-8">
          <AnimatePresence>
            {books.map((book, index) => (
              <motion.div
                key={book.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.95 }}
                transition={{ delay: index * 0.1 }}
                className="group flex flex-col sm:flex-row bg-white rounded-3xl overflow-hidden shadow-sm hover:shadow-xl transition-all duration-300 border border-slate-100"
              >
                <div className="sm:w-40 h-64 sm:h-auto bg-slate-100 relative flex-shrink-0 overflow-hidden">
                   {book.thumbnail ? <img src={book.thumbnail} alt={book.title} className="w-full h-full object-cover mix-blend-multiply opacity-90 group-hover:opacity-100 transition-all duration-500" /> : <div className="w-full h-full flex items-center justify-center text-rose-200"><BookHeart size={40} /></div>}
                   <div className="absolute top-3 left-3 bg-white/90 backdrop-blur text-xs font-bold px-3 py-1.5 rounded-full text-slate-600 shadow-sm">
                     {mode === "discovery" ? `${Math.round(book.score * 100)}% Match` : "Result"}
                   </div>
                </div>

                <div className="p-8 flex flex-col justify-between w-full">
                  <div>
                    <div className="flex items-center gap-2 mb-3 flex-wrap">
                      <span className="bg-slate-100 text-slate-500 text-xs font-bold px-3 py-1 rounded-full uppercase tracking-wider">{book.categories}</span>
                      {/* Show YEAR in the card too! */}
                      {book.year && book.year !== "0" && <span className="bg-slate-100 text-slate-500 text-xs font-bold px-3 py-1 rounded-full">{book.year}</span>}
                      {book.rating && book.rating > 0 && <span className="bg-amber-50 text-amber-500 text-xs font-bold px-3 py-1 rounded-full border border-amber-100">⭐ {book.rating.toFixed(1)}</span>}
                    </div>
                    <h3 className={`text-xl font-bold text-slate-800 leading-tight mb-1 transition-colors ${mode === "discovery" ? "group-hover:text-rose-500" : "group-hover:text-cyan-600"}`}>{book.title}</h3>
                    <p className="text-sm text-slate-400 font-medium mb-2">{book.authors}</p>
                    {book.readers && book.readers > 10000 && <div className="flex items-center gap-1 text-xs text-orange-400 font-bold mb-4"><span>🔥 Trending ({book.readers.toLocaleString()})</span></div>}
                    <p className="text-sm text-slate-500 leading-relaxed line-clamp-3">{book.description}</p>
                  </div>
                  <div className="mt-6 pt-4 border-t border-slate-50 flex justify-end">
                    <button className={`text-xs font-bold transition-colors uppercase tracking-widest flex items-center gap-1 ${mode === "discovery" ? "text-rose-400 hover:text-rose-600" : "text-cyan-500 hover:text-cyan-700"}`}>Details <span>→</span></button>
                  </div>
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
        </div>
        
        {searched && books.length === 0 && !loading && <div className="text-center py-20 text-slate-400"><Coffee className="w-10 h-10 mx-auto mb-4 opacity-50" /><p>No matches found.</p></div>}
      </div>
    </main>
  );
}