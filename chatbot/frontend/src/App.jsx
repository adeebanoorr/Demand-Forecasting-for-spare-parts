import React, { useState, useRef, useEffect } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import {
  Send,
  Bot,
  User,
  MessageSquare,
  Plus,
  History,
  Settings as SettingsIcon,
  Info,
  ChevronRight,
  Loader2,
  Trash2,
  Download,
  Copy,
  Boxes,
  Activity
} from 'lucide-react'

const API_BASE = 'http://localhost:8001'

export default function App() {
  const [messages, setMessages] = useState([
    {
      role: 'ai',
      content: 'Hello! I am your Enterprise AI Analyst. How can I help you today with your dispatch and demand data?'
    }
  ])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [chatHistory, setChatHistory] = useState([
    { id: 1, title: 'Revenue Analysis 2023', query: 'What was the total revenue in 2023?' },
    { id: 2, title: 'Top 10 Spare Parts', query: 'What are the top 10 spare parts by quantity?' },
    { id: 3, title: 'Regional Performance', query: 'Give me a breakdown of revenue by region.' }
  ])
  const [showDataSpecs, setShowDataSpecs] = useState(false)
  const [showSettings, setShowSettings] = useState(false)

  const scrollRef = useRef(null)

  // Persistence Layer
  useEffect(() => {
    const saved = localStorage.getItem('ai_analyst_messages')
    if (saved) {
      try {
        setMessages(JSON.parse(saved))
      } catch (e) {
        console.error("Failed to load history")
      }
    }
  }, [])

  useEffect(() => {
    if (messages.length > 1) {
      localStorage.setItem('ai_analyst_messages', JSON.stringify(messages))
    }
  }, [messages])

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [messages])

  const handleSend = async (e) => {
    e?.preventDefault()
    if (!input.trim() || isLoading) return

    const userMsg = input.trim()
    setInput('')
    setMessages(prev => [...prev, { role: 'user', content: userMsg }])
    setIsLoading(true)

    try {
      const response = await fetch(`${API_BASE}/ask`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: userMsg }),
      })

      const data = await response.json()
      setMessages(prev => [...prev, { role: 'ai', content: data.answer }])
    } catch (error) {
      setMessages(prev => [...prev, { role: 'ai', content: 'Sorry, I encountered an error. Please make sure the backend is running.' }])
    } finally {
      setIsLoading(false)
    }
  }

  const handleQuery = async (queryText) => {
    if (isLoading) return
    setInput(queryText)
    // We wrapped in a timeout to ensure state update for input is reflected or just use the text directly
    const userMsg = queryText.trim()
    setMessages(prev => [...prev, { role: 'user', content: userMsg }])
    setIsLoading(true)
    try {
      const response = await fetch(`${API_BASE}/ask`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: userMsg }),
      })
      const data = await response.json()
      setMessages(prev => [...prev, { role: 'ai', content: data.answer }])
    } catch (error) {
      setMessages(prev => [...prev, { role: 'ai', content: 'Error connecting to analytics engine.' }])
    } finally {
      setIsLoading(false)
      setInput('')
    }
  }

  const suggestedQueries = [
    "What was the total revenue in 2023?",
    "Who is the top customer by quantity in 2024?",
    "What is our On-Time Dispatch % for Ahmedabad?",
    "Which year had the highest revenue?",
    "Most sold item in 2023?"
  ]

  const downloadCSV = (content) => {
    // Basic markdown table to CSV converter
    const lines = content.split('\n')
    const tableLines = lines.filter(l => l.includes('|'))
    if (tableLines.length < 2) {
      alert("No table found to export.")
      return
    }

    const csvContent = tableLines
      .map(row => row.split('|')
        .filter(cell => cell.trim() !== '')
        .map(cell => `"${cell.trim().replace(/"/g, '""')}"`)
        .join(',')
      ).join('\n')

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    const url = URL.createObjectURL(blob)
    link.setAttribute('href', url)
    link.setAttribute('download', `analysis_export_${new Date().toISOString().slice(0, 10)}.csv`)
    link.style.visibility = 'hidden'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text).then(() => {
      alert('Copied to clipboard!');
    }).catch(err => {
      console.error('Failed to copy: ', err);
    });
  }

  return (
    <div className="flex h-screen bg-slate-50 font-sans text-slate-900 overflow-hidden">

      {/* Sidebar - Matching Indi4 Dashboard Style */}
      <aside className="w-72 bg-[#0075BE] text-white flex flex-col shadow-xl z-20">
        <div className="p-6 flex items-center gap-3 border-b border-white/10 h-20 shrink-0">
          <div className="bg-white/20 p-2 rounded-lg">
            <Boxes size={24} className="text-white" />
          </div>
          <div>
            <h1 className="font-black text-base leading-tight tracking-tight">AI Analyst</h1>
            <p className="text-[10px] uppercase font-bold tracking-[0.2em] text-white/60">Spare Parts Analyst</p>
          </div>
        </div>

        <div className="p-4 flex-1 overflow-y-auto space-y-6">
          <div>
            <button
              onClick={() => setMessages([{ role: 'ai', content: 'Hello! I am your Enterprise AI Analyst. How can I help you today?' }])}
              className="w-full flex items-center gap-3 px-4 py-3 bg-white/10 hover:bg-white/20 rounded-xl transition-all font-bold text-sm"
            >
              <Plus size={18} /> New Analysis
            </button>
          </div>

          <div className="space-y-4">
            <h2 className="text-[10px] font-black uppercase tracking-widest text-white/40 pl-2">Recent Queries</h2>
            <div className="space-y-1">
              {chatHistory.map(item => (
                <div
                  key={item.id}
                  onClick={() => handleQuery(item.query)}
                  className="group flex items-center justify-between px-4 py-2 hover:bg-white/5 rounded-lg cursor-pointer transition-colors"
                >
                  <div className="flex items-center gap-3 overflow-hidden">
                    <History size={14} className="text-white/40 shrink-0" />
                    <span className="text-sm text-white/80 truncate font-medium">{item.title}</span>
                  </div>
                  <ChevronRight size={14} className="text-white/20 group-hover:text-white/60" />
                </div>
              ))}
            </div>
          </div>

          <div className="space-y-4">
            <h2 className="text-[10px] font-black uppercase tracking-widest text-white/40 pl-2">Suggested</h2>
            <div className="space-y-1">
              {suggestedQueries.map((q, i) => (
                <div
                  key={i}
                  onClick={() => handleQuery(q)}
                  className="px-4 py-2 hover:bg-white/5 rounded-lg cursor-pointer transition-colors text-xs text-white/60 hover:text-white line-clamp-1 italic"
                >
                  "{q}"
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="p-4 mt-auto border-t border-white/10 space-y-1 shrink-0">
          <div
            onClick={() => setShowDataSpecs(true)}
            className="flex items-center gap-3 px-4 py-3 text-white/60 hover:text-white hover:bg-white/5 rounded-lg cursor-pointer transition-all"
          >
            <Info size={18} />
            <span className="text-sm font-bold">Data Specs</span>
          </div>
          <div
            onClick={() => setShowSettings(true)}
            className="flex items-center gap-3 px-4 py-3 text-white/60 hover:text-white hover:bg-white/5 rounded-lg cursor-pointer transition-all"
          >
            <SettingsIcon size={18} />
            <span className="text-sm font-bold">Settings</span>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col overflow-hidden">

        {/* Header Bar */}
        <header className="h-20 bg-white border-b border-slate-100 flex items-center justify-between px-10 sticky top-0 z-10 shadow-sm shrink-0">
          <div className="flex items-center gap-4">
            <div className="p-2 bg-slate-50 rounded-lg text-[#0075BE]">
              <Activity size={20} />
            </div>
            <div>
              <h2 className="font-black text-base text-slate-800 tracking-tight">Analytics Copilot</h2>
              <div className="flex items-center gap-1.5">
                <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Connected to local dataset</span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-6">
            <div className="flex items-center gap-2 px-3 py-1 bg-[#234FA2]/10 rounded-full">
              <div className="w-1.5 h-1.5 rounded-full bg-[#234FA2] animate-pulse" />
              <span className="text-[10px] font-black text-[#234FA2] uppercase">Mistral Engine Active</span>
            </div>
            <button
              onClick={() => {
                if (window.confirm('Are you sure you want to clear this conversation?')) {
                  localStorage.removeItem('ai_analyst_messages');
                  setMessages([{ role: 'ai', content: 'Hello! I am your Enterprise AI Analyst. How can I help you today?' }]);
                }
              }}
              className="p-2 text-slate-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-all"
              title="Clear Chat"
            >
              <Trash2 size={20} />
            </button>
          </div>
        </header>

        {/* Chat Interface */}
        <div className="flex-1 overflow-hidden relative flex flex-col">

          {/* Scrollable Message Container */}
          <div
            ref={scrollRef}
            className="flex-1 overflow-y-auto p-10 space-y-8 scroll-smooth"
          >
            {messages.map((msg, idx) => (
              <div
                key={idx}
                className={`flex gap-6 max-w-5xl mx-auto animate-in fade-in slide-in-from-bottom-4 duration-500 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}
              >
                <div className={`shrink-0 w-12 h-12 rounded-xl flex items-center justify-center shadow-sm ${msg.role === 'ai' ? 'bg-[#0075BE] text-white' : 'bg-[#234FA2] text-white'
                  }`}>
                  {msg.role === 'ai' ? <Bot size={24} /> : <User size={24} />}
                </div>

                <div className={`space-y-4 max-w-[85%] ${msg.role === 'user' ? 'text-right' : ''}`}>
                  <div className={`px-6 py-4 rounded-2xl shadow-sm border border-slate-100 prose prose-slate text-sm max-w-none ${msg.role === 'ai' ? 'chat-bubble-ai' : 'chat-bubble-user text-white'
                    }`}>
                    {msg.role === 'ai' ? (
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>
                        {msg.content}
                      </ReactMarkdown>
                    ) : (
                      <p className="font-medium text-sm leading-relaxed">{msg.content}</p>
                    )}
                  </div>

                  {msg.role === 'ai' && (
                    <div className="flex items-center gap-4 px-2">
                      <button
                        onClick={() => copyToClipboard(msg.content)}
                        className="flex items-center gap-1.5 text-[10px] font-black text-slate-400 uppercase tracking-widest hover:text-[#0075BE] transition-colors"
                      >
                        <Copy size={12} /> Copy Output
                      </button>
                      <button
                        onClick={() => downloadCSV(msg.content)}
                        className="flex items-center gap-1.5 text-[10px] font-black text-slate-400 uppercase tracking-widest hover:text-[#0075BE] transition-colors"
                      >
                        <Download size={12} /> Export CSV
                      </button>
                    </div>
                  )}
                </div>
              </div>
            ))}

            {isLoading && (
              <div className="flex gap-6 max-w-5xl mx-auto items-start">
                <div className="shrink-0 w-12 h-12 rounded-xl bg-[#0075BE] text-white flex items-center justify-center shadow-sm animate-pulse">
                  <Bot size={24} />
                </div>
                <div className="px-8 py-6 rounded-3xl chat-bubble-ai shadow-sm border border-slate-100 flex items-center gap-3">
                  <Loader2 className="animate-spin text-[#0075BE]" size={20} />
                  <span className="text-sm font-bold text-slate-500 uppercase tracking-widest animate-pulse-slow">Analyzing KPI Patterns...</span>
                </div>
              </div>
            )}
          </div>

          {/* Input Area */}
          <div className="p-8 border-t border-slate-100 bg-white shadow-[0_-10px_20px_-15px_rgba(0,0,0,0.1)] shrink-0">
            <form
              onSubmit={handleSend}
              className="max-w-5xl mx-auto relative group"
            >
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask about revenue, dispatches, or model performance..."
                className="w-full bg-slate-50 border border-slate-200 rounded-2xl px-6 py-4 pr-16 text-sm font-medium focus:outline-none focus:ring-2 focus:ring-[#0075BE]/20 focus:bg-white transition-all shadow-inner"
              />
              <button
                type="submit"
                disabled={!input.trim() || isLoading}
                className={`absolute right-3 top-3 bottom-3 px-6 rounded-xl flex items-center justify-center transition-all ${input.trim() && !isLoading ? 'bg-[#234FA2] text-white shadow-lg hover:translate-x-1' : 'bg-slate-200 text-slate-400 cursor-not-allowed'
                  }`}
              >
                <Send size={24} />
              </button>
            </form>
            <p className="text-center mt-4 text-[10px] font-black text-slate-400 uppercase tracking-widest">
              Powered by Enterprise Intelligence — Dynamic Execution Enabled
            </p>
          </div>
        </div>
      </main>

      {/* --- MODALS --- */}

      {showDataSpecs && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-6 bg-slate-900/60 backdrop-blur-sm animate-in fade-in duration-300">
          <div className="bg-white rounded-3xl shadow-2xl w-full max-w-2xl overflow-hidden animate-in zoom-in-95 duration-300">
            <div className="bg-[#0075BE] p-8 text-white flex justify-between items-center">
              <div>
                <h3 className="text-2xl font-black tracking-tight">System Data Specifications</h3>
                <p className="text-white/60 text-xs uppercase font-bold tracking-widest mt-1">Inventory Intelligence Schema</p>
              </div>
              <button onClick={() => setShowDataSpecs(false)} className="p-2 hover:bg-white/10 rounded-full transition-colors">
                <Plus className="rotate-45" size={24} />
              </button>
            </div>
            <div className="p-8 space-y-6">
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-slate-50 p-4 rounded-2xl border border-slate-100">
                  <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1">Total Records</p>
                  <p className="text-xl font-black text-slate-800">65,293 Rows</p>
                </div>
                <div className="bg-slate-50 p-4 rounded-2xl border border-slate-100">
                  <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1">Date Range</p>
                  <p className="text-xl font-black text-slate-800">2021 — 2024</p>
                </div>
              </div>
              <div className="space-y-3">
                <h4 className="text-sm font-bold text-slate-700">Available Core Columns</h4>
                <div className="grid grid-cols-2 gap-x-8 gap-y-2">
                  {['ITEM_CODE', 'ITEM_DESCRIPTION', 'MODEL', 'QTY', 'UNIT_PRICE', 'BASIC_VALUE', 'TAX_VALUE', 'GROSS_VALUE', 'REGION', 'INV_DATE'].map(col => (
                    <div key={col} className="flex items-center gap-2 text-xs text-slate-500 font-medium">
                      <div className="w-1 h-1 rounded-full bg-[#0075BE]" /> {col}
                    </div>
                  ))}
                </div>
              </div>
              <p className="text-xs text-slate-400 leading-relaxed italic border-t border-slate-100 pt-6">
                This AI is trained exclusively on enterprise spare parts dispatch data. Automated guards are active for data privacy and column whitening.
              </p>
            </div>
          </div>
        </div>
      )}

      {showSettings && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-6 bg-slate-900/60 backdrop-blur-sm animate-in fade-in duration-300">
          <div className="bg-white rounded-3xl shadow-2xl w-full max-w-lg overflow-hidden animate-in zoom-in-95 duration-300">
            <div className="bg-[#234FA2] p-8 text-white flex justify-between items-center">
              <h3 className="text-2xl font-black tracking-tight">Settings</h3>
              <button onClick={() => setShowSettings(false)} className="p-2 hover:bg-white/10 rounded-full transition-colors">
                <Plus className="rotate-45" size={24} />
              </button>
            </div>
            <div className="p-8 space-y-6">
              <div className="space-y-4">
                <div className="flex items-center justify-between p-4 bg-slate-50 rounded-2xl">
                  <div>
                    <p className="text-sm font-bold text-slate-700">Persistent History</p>
                    <p className="text-[10px] text-slate-400">Save your analysis sessions locally</p>
                  </div>
                  <div className="w-12 h-6 bg-[#0075BE] rounded-full relative cursor-pointer">
                    <div className="absolute right-1 top-1 w-4 h-4 bg-white rounded-full transition-all shadow-sm" />
                  </div>
                </div>
                <div className="flex items-center justify-between p-4 bg-slate-50 rounded-2xl opacity-50">
                  <div>
                    <p className="text-sm font-bold text-slate-700">Dark Mode</p>
                    <p className="text-[10px] text-slate-400">Coming soon in V2.0</p>
                  </div>
                  <div className="w-12 h-6 bg-slate-300 rounded-full relative cursor-not-allowed">
                    <div className="absolute left-1 top-1 w-4 h-4 bg-white rounded-full transition-all shadow-sm" />
                  </div>
                </div>
              </div>
              <button
                onClick={() => {
                  if (window.confirm('Delete all cached analysis data?')) {
                    localStorage.removeItem('ai_analyst_messages');
                    setMessages([{ role: 'ai', content: 'Hello! I am your Enterprise AI Analyst. How can I help you today?' }]);
                    setShowSettings(false);
                  }
                }}
                className="w-full py-4 text-red-500 font-bold text-sm bg-red-50 hover:bg-red-100 rounded-2xl transition-colors mt-4"
              >
                Clear All Cached Data
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
