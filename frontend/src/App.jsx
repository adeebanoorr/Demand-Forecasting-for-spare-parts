import React, { useState, useEffect, useCallback, useMemo } from 'react';
import LandingPage from './LandingPage';
import LoginPage from './LoginPage';
import {
  LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Area, ComposedChart, Cell
} from 'recharts';
import {
  LayoutDashboard,
  BarChart3,
  TrendingUp,
  Info,
  Download,
  ChevronRight,
  ArrowUpRight,
  Activity,
  Database,
  Search,
  CheckCircle2,
  AlertCircle,
  Loader2,
  RefreshCw,
  Play,
  Home,
  FileText,
  Boxes,
  PieChart,
  Cpu
} from 'lucide-react';

const API_BASE = import.meta.env.VITE_API_URL || "/api/v1";
const ANALYTICS_URL = import.meta.env.VITE_ANALYTICS_URL || "/analytics/";

// --- Analysis Page Component (MSTL Decomposition Charts) ---
const AnalysisPage = ({ items, selectedItem, setSelectedItem }) => {
  const [mstlData, setMstlData] = useState([]);
  const [mstlLoading, setMstlLoading] = useState(false);
  const [mstlError, setMstlError] = useState(null);
  const [mstlItem, setMstlItem] = useState(selectedItem || '');

  useEffect(() => {
    if (!mstlItem) return;
    setMstlLoading(true);
    setMstlError(null);
    fetch(`${API_BASE}/forecast/mstl/${encodeURIComponent(mstlItem)}`)
      .then(r => r.ok ? r.json() : r.text().then(t => Promise.reject(t)))
      .then(d => { setMstlData(d); setMstlLoading(false); })
      .catch(e => { setMstlError(String(e)); setMstlLoading(false); });
  }, [mstlItem]);

  const panels = [
    { key: 'observed', label: 'Observed Consumption', color: '#0075BE' },
    { key: 'trend', label: 'Underlying Trend', color: '#E07C3A' },
    { key: 'seasonal', label: 'Seasonal Pattern', color: '#6366F1' },
    { key: 'residual', label: 'Residual Volatility', color: '#94A3B8' },
  ];
  const tick = { fontSize: 12, fontWeight: 600, fill: '#94A3B8' };

  return (
    <div className="animate-in fade-in slide-in-from-bottom-8 duration-700 space-y-8">
      <div className="bg-white p-10 rounded-3xl border border-slate-100 shadow-sm space-y-8">
        <div className="flex justify-between items-start flex-wrap gap-8">
          <div className="space-y-2">
            <SectionTitle title="MSTL Decomposition Analysis" />
            <h2 className="text-3xl font-extrabold text-slate-800 tracking-tight">MSTL Analysis</h2>
            <p className="text-sm text-slate-500 leading-relaxed max-w-xl">
              Decomposing the time-series into trend, seasonal, and irregular components to understand the fundamental drivers of demand for this part.
            </p>
          </div>
          
          <div className="flex items-center gap-4 bg-slate-50 p-4 rounded-2xl border border-slate-100">
            <div className="flex flex-col">
               <span className="text-xs font-black text-slate-400 uppercase tracking-widest mb-1">Active Item Reference</span>
               <select
                  value={mstlItem}
                  onChange={(e) => { setMstlItem(e.target.value); setSelectedItem(e.target.value); }}
                  className="bg-transparent border-none text-sm font-bold text-slate-900 focus:ring-0 cursor-pointer p-0"
                >
                  {items.map(code => <option key={code} value={code}>{code}</option>)}
                </select>
            </div>
            <div className="w-px h-8 bg-slate-200 mx-2" />
            <div className="p-2 bg-blue-50 text-blue-600 rounded-lg">
               <Activity size={18} />
            </div>
          </div>
        </div>

        {mstlLoading && (
          <div className="flex flex-col items-center justify-center h-80 text-blue-600 gap-4">
            <Loader2 className="animate-spin" size={32} />
            <span className="text-xs font-black uppercase tracking-[0.2em]">Analyzing Time Series...</span>
          </div>
        )}
        
        {mstlError && (
          <div className="text-red-500 text-sm p-6 bg-red-50 rounded-2xl border border-red-100 flex items-center gap-3 font-medium">
             <AlertCircle size={20} /> Failed to process decomposition: {mstlError}
          </div>
        )}

        {!mstlLoading && !mstlError && mstlData.length > 0 && (
          <div className="grid grid-cols-1 gap-6">
            {panels.map(({ key, label, color }) => (
              <div key={key} className="bg-slate-50/40 rounded-2xl p-6 border border-slate-100 transition-all hover:bg-slate-50">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <div className="w-2 h-2 rounded-full shadow-[0_0_8px_rgba(0,0,0,0.1)]" style={{ background: color }} />
                    <span className="text-[11px] font-black text-slate-400 uppercase tracking-widest">{label}</span>
                  </div>
                  <div className="text-[10px] font-extrabold text-slate-400 bg-white px-3 py-1 rounded-full border border-slate-100 shadow-sm uppercase tracking-tighter">
                     Values over 156 weeks
                  </div>
                </div>
                <ResponsiveContainer width="100%" height={160}>
                  <ComposedChart data={mstlData} margin={{ top: 10, right: 30, left: 10, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
                    <XAxis
                      dataKey="week"
                      tick={tick}
                      axisLine={false}
                      tickLine={false}
                      tickFormatter={v => v ? v.slice(0, 7) : ''}
                      interval={Math.floor(mstlData.length / 10)}
                    />
                    <YAxis axisLine={false} tickLine={false} tick={tick} width={40} />
                    <Tooltip
                      contentStyle={{ borderRadius: '16px', border: 'none', boxShadow: '0 20px 40px -12px rgba(0,0,0,0.15)', fontSize: 12, fontWeight: 700 }}
                      formatter={(v) => [Number(v).toFixed(2), label]}
                    />
                    {key === 'residual' ? (
                      <Area type="monotone" dataKey={key} stroke={color} fill={color} fillOpacity={0.15} strokeWidth={2} dot={false} />
                    ) : (
                      <Line type="monotone" dataKey={key} stroke={color} strokeWidth={3} dot={false} activeDot={{ r: 5, fill: '#fff', stroke: color, strokeWidth: 2 }} />
                    )}
                  </ComposedChart>
                </ResponsiveContainer>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

// --- Components ---

const SidebarItem = ({ icon: Icon, label, active, onClick }) => (
  <div
    onClick={onClick}
    className={`flex items-center gap-3 px-5 py-3.5 rounded-xl cursor-pointer transition-all duration-200 group ${active 
      ? 'bg-blue-600/10 text-white font-bold shadow-sm' 
      : 'text-slate-400 hover:bg-white/5 hover:text-white'
    }`}
  >
    <div className={`transition-transform duration-200 ${active ? 'scale-110' : 'group-hover:scale-110'}`}>
      <Icon size={18} className={active ? 'text-blue-400' : 'text-inherit'} />
    </div>
    <span className="text-sm tracking-wide">{label}</span>
    {active && <div className="ml-auto w-1.5 h-1.5 rounded-full bg-blue-400 shadow-[0_0_10px_rgba(96,165,250,0.6)]" />}
  </div>
);

const KPICard = ({ title, value, subtext, icon: Icon, isLoading, accent }) => {
  const hideKeywords = ['rmse', 'smape', 'mae', 'auto'];
  if (hideKeywords.some(key => title.toLowerCase().includes(key))) return null;

  return (
    <div className="bg-white p-6 rounded-2xl border border-slate-100 shadow-[0_2px_8px_rgba(0,0,0,0.02)] flex flex-col gap-4 flex-1 min-w-[240px] transition-all hover:shadow-xl hover:shadow-slate-200/50">
      <div className="flex justify-between items-start">
        <div className={`p-2.5 rounded-xl ${accent || 'bg-blue-50 text-blue-600'}`}>
          <Icon size={20} />
        </div>
        <span className="text-slate-400 text-xs font-extrabold uppercase tracking-[0.15em]">{title}</span>
      </div>
      <div>
        {isLoading ? (
          <div className="h-8 bg-slate-50 animate-pulse rounded-lg w-2/3"></div>
        ) : (
          <div className="text-2xl font-black text-slate-800 tracking-tight leading-none mb-1">{value}</div>
        )}
        {subtext && <p className="text-xs text-slate-400 font-bold uppercase">{subtext}</p>}
      </div>
    </div>
  );
};

const SectionTitle = ({ title }) => (
  <h3 className="text-xs font-black text-slate-400 uppercase tracking-[0.25em] mb-6 flex items-center gap-3">
    <div className="w-1.5 h-4 bg-gradient-to-b from-blue-500 to-blue-700 rounded-full" />
    {title}
  </h3>
);

// --- Main Dashboard Component ---

function Dashboard({ onLogout }) {
  const [page, setPage] = useState('home');
  const [items, setItems] = useState([]);
  const [selectedItem, setSelectedItem] = useState('');
  const [selectedModel, setSelectedModel] = useState('Best');
  const [metrics, setMetrics] = useState(null);
  const [globalMetrics, setGlobalMetrics] = useState(null);
  const [forecast, setForecast] = useState([]);
  const [validation, setValidation] = useState([]);
  const [aggregateForecast, setAggregateForecast] = useState([]);
  const [comparison, setComparison] = useState({ ml: [], ts: [] });
  const [loading, setLoading] = useState({ items: true, metrics: false, forecast: false, global: true, aggregate: true });

  // Initial Load
  useEffect(() => {
    // Items
    fetch(`${API_BASE}/items`)
      .then(res => res.ok ? res.json() : [])
      .then(data => {
        const itemsList = Array.isArray(data) ? data : [];
        setItems(itemsList);
        if (itemsList.length > 0) setSelectedItem(itemsList[0]);
        setLoading(prev => ({ ...prev, items: false }));
      });

    // Global Metrics
    fetch(`${API_BASE}/metrics/global/stat`)
      .then(res => res.ok ? res.json() : null)
      .then(data => {
        if (data) setGlobalMetrics(data);
        setLoading(prev => ({ ...prev, global: false }));
      });

    // Portfolio Demand Aggregate
    fetch(`${API_BASE}/forecast/aggregate`)
      .then(res => res.ok ? res.json() : [])
      .then(data => {
        setAggregateForecast(Array.isArray(data) ? data : []);
        setLoading(prev => ({ ...prev, aggregate: false }));
      })
      .catch(err => {
        console.error("Failed to fetch aggregate forecast:", err);
        setLoading(prev => ({ ...prev, aggregate: false }));
      });
  }, []);

  const [modelNames, setModelNames] = useState({ champion: 'Champion', ml: 'Best ML', ts: 'Best TS' });

  const fetchDashboardData = useCallback(async (itemCode) => {
    if (!itemCode) return;
    setLoading(prev => ({ ...prev, metrics: true, forecast: true }));
    try {
      const [mRes, cRes, compRes, valRes] = await Promise.all([
        fetch(`${API_BASE}/metrics/${itemCode}`).then(r => r.json()),
        fetch(`${API_BASE}/metrics/comparison/${itemCode}`).then(r => r.json()),
        fetch(`${API_BASE}/forecast/comparison/${itemCode}`).then(r => r.json()),
        fetch(`${API_BASE}/metrics/validation/${itemCode}`).then(r => r.ok ? r.json() : null).catch(() => null)
      ]);
      setMetrics(mRes || null);
      setComparison(cRes || { ml: [], ts: [] });
      setForecast(compRes?.data || []);
      setModelNames(compRes?.models || { champion: 'Champion', ml: 'Best ML', ts: 'Best TS' });
      setValidation(valRes?.data || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(prev => ({ ...prev, metrics: false, forecast: false }));
    }
  }, []);

  useEffect(() => {
    if (selectedItem && page === 'dashboard') {
      fetchDashboardData(selectedItem);
    }
  }, [selectedItem, page, fetchDashboardData]);

  return (
    <div className="flex min-h-screen bg-[#E6F1F8] font-sans selection:bg-blue-100">
      {/* Sidebar - Clean Deep Blue */}
      <aside className="w-64 bg-[#0075BE] text-white flex flex-col fixed h-full z-20 shadow-xl">
        <div className="p-6">
          <span className="text-xs font-bold text-white/60 uppercase tracking-widest pl-2">Navigation</span>
        </div>

        <div className="flex-1 px-4 space-y-2">
          <SidebarItem icon={Home} label="Home" active={page === 'home'} onClick={() => setPage('home')} />
          <SidebarItem icon={PieChart} label="Analysis" active={page === 'analysis'} onClick={() => setPage('analysis')} />
          <SidebarItem icon={LayoutDashboard} label="Forecasting" active={page === 'dashboard'} onClick={() => setPage('dashboard')} />
          <SidebarItem icon={Info} label="About" active={page === 'about'} onClick={() => setPage('about')} />
        </div>

        <div className="p-6 border-t border-white/10">
           <button
            onClick={onLogout}
            className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-white/10 hover:bg-white/20 rounded-lg text-xs font-bold transition-all text-white border border-white/10"
          >
            <Activity size={16} /> Log Out
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 ml-64 min-h-screen bg-white">
        {/* Modern Header matching Indi4 screenshot */}
        <header className="h-16 bg-white border-b border-slate-100 flex items-center justify-between px-10 sticky top-0 z-10 w-full shadow-sm">
          <div className="flex-1" />
          
          <div className="flex flex-col items-center">
            <div className="flex items-center gap-1">
               <img src="/indi4-logo.png" alt="Indi4 Logo" className="h-8 object-contain" />
            </div>
            <div className="flex items-center gap-1.5 -mt-1">
               <Cpu size={16} className="text-[#0075BE]" />
               <p className="text-xs text-[#0075BE] font-black uppercase tracking-[0.1em]">ACR SPARES Demand Forecasting Platform</p>
            </div>
          </div>

          <div className="flex-1 flex justify-end">
             <button onClick={onLogout} className="flex items-center gap-2 text-xs font-bold text-slate-400 hover:text-red-500 transition-colors bg-slate-50 px-3 py-1.5 rounded-lg border border-slate-200">
                <Activity size={14} /> Log Out
             </button>
          </div>
        </header>

        <div className="w-full h-[calc(100vh-64px)] overflow-y-auto bg-white">
          {page === 'home' && (
            <div className="w-full h-full animate-in fade-in duration-500">
              <iframe
                src={`${ANALYTICS_URL}?v=4`}
                className="w-full h-full border-none"
                title="Intelligence Analytics"
                loading="lazy"
              />
            </div>
          )}

          {page === 'about' && (
            <div className="p-8 space-y-10 animate-in fade-in slide-in-from-bottom-8 duration-700">
              {/* Dataset Overview */}
              <div className="bg-white p-10 rounded-3xl border border-[#1C3F82]/10 shadow-sm space-y-8">
                <SectionTitle title="Intelligence Data Profile" />
                <p className="text-[#152F61]/70 leading-relaxed max-w-2xl text-sm font-bold">
                  The primary data source consists of institutional despatch records,
                  covering deep-history outward flows through Q3 2024.
                </p>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
                  {[
                    { label: 'Raw Observations', value: '65,536' },
                    { label: 'Features Ingested', value: '40' },
                    { label: 'Training Pool', value: '4,769' },
                    { label: 'Validation Pool', value: '1,617' },
                  ].map(s => (
                    <div key={s.label} className="bg-[#E6F1F8] rounded-2xl p-6 text-center space-y-1 border border-[#0075BE]/10 transition-all hover:bg-white hover:shadow-xl">
                      <div className="text-2xl font-black text-[#0075BE] tracking-tighter">{s.value}</div>
                      <div className="text-xs font-black text-[#152F61]/40 uppercase tracking-widest">{s.label}</div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Selected Features */}
              <div className="bg-white p-10 rounded-3xl border border-slate-100 shadow-sm space-y-8">
                <SectionTitle title="Columns Selected for Training" />
                <p className="text-slate-500 text-sm leading-relaxed max-w-2xl font-medium">
                  Out of 40 raw columns, 5 critical features were isolated for demand forecasting. All transactional fields (taxes, GST, transporter, etc.) were pruned.
                </p>
                <div className="overflow-x-auto rounded-2xl border border-slate-50">
                  <table className="w-full text-left text-sm">
                    <thead>
                      <tr className="bg-slate-50/50">
                        <th className="px-8 py-4 text-xs font-black text-slate-400 uppercase tracking-widest">Column (Raw)</th>
                        <th className="px-8 py-4 text-xs font-black text-slate-400 uppercase tracking-widest">Renamed To</th>
                        <th className="px-8 py-4 text-xs font-black text-slate-400 uppercase tracking-widest text-center">Type</th>
                        <th className="px-8 py-4 text-xs font-black text-slate-400 uppercase tracking-widest">Purpose</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-50">
                      {[
                        ['OA DATE', 'OA_DATE', 'Date', 'Temporal reference point'],
                        ['ITEM CODE', 'ITEM_CODE', 'String', 'Unique SKU identifier'],
                        ['QTY', 'QTY', 'Numeric', 'Quantity dispatched (Target)'],
                        ['MODEL', 'MODEL', 'String', 'Filtered to ACR SPARES'],
                        ['ITEM DESCRIPTION', 'ITEM_DESCRIPTION', 'String', 'Human-readable nomenclature'],
                      ].map(([raw, renamed, type, purpose]) => (
                        <tr key={raw} className="group hover:bg-slate-50/50 transition-all">
                          <td className="px-8 py-4 font-mono text-xs font-extrabold text-slate-700">{raw}</td>
                          <td className="px-8 py-4 font-mono text-xs text-[#0075BE] font-black uppercase">{renamed}</td>
                          <td className="px-8 py-4 text-xs text-center font-bold text-slate-400 uppercase tracking-tighter">{type}</td>
                          <td className="px-8 py-4 text-xs text-slate-500 font-medium">{purpose}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* 8 Items */}
              <div className="bg-white p-10 rounded-3xl border border-slate-100 shadow-sm space-y-8">
                <SectionTitle title="SKU Priority Pool" />
                <p className="text-slate-500 text-sm leading-relaxed mb-2">
                  These 8 items were selected based on highest dispatch frequency within the ACR SPARES model. Training rows per item reflect order-level records (before weekly aggregation).
                </p>
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-sm">
                    <thead>
                      <tr className="bg-slate-50">
                        <th className="px-6 py-3 text-xs font-black text-slate-400 uppercase tracking-widest">#</th>
                        <th className="px-6 py-3 text-xs font-black text-slate-400 uppercase tracking-widest">Item Code</th>
                        <th className="px-6 py-3 text-xs font-black text-slate-400 uppercase tracking-widest">Item Description</th>
                        <th className="px-6 py-3 text-xs font-black text-slate-400 uppercase tracking-widest">Training Rows</th>
                        <th className="px-6 py-3 text-xs font-black text-slate-400 uppercase tracking-widest">Champion Model</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-50">
                      {[
                        ['082.03.110.50.', 'Piston KC/KCX', '1,055', 'AR'],
                        ['082.04.030.50.', 'Bearing Bush Big End Con Rod KC/KCX', '1,052', 'AR'],
                        ['082.08.000.50.', 'Shaft Seal Assembly KC/KCX', '973', 'Prophet'],
                        ['336.40.401.50.', 'Cylinder Liner KC/KCX', '932', 'AR'],
                        ['993.00.311.00.', 'Gasket Suct Strainer & Side Cover KC/KCX', '337', 'AR'],
                        ['085.00.003.50.', 'Kirloskar Advantage Oil, 20 Ltr Drum', '243', 'MA'],
                        ['084.19.001.50.', 'Gasket Set KC4', '150', 'MA'],
                        ['351.03.301.50.', 'Liner Cylinder AC70', '27', 'MA'],
                      ].map(([code, desc, rows, champ], i) => (
                        <tr key={code} className="hover:bg-slate-50 transition-colors">
                          <td className="px-6 py-4 text-slate-400 font-bold">{i + 1}</td>
                          <td className="px-6 py-4 font-mono text-xs font-bold text-slate-800">{code}</td>
                          <td className="px-6 py-4 text-slate-600 text-xs">{desc}</td>
                          <td className="px-6 py-4 text-slate-500 text-xs">{rows}</td>
                          <td className="px-6 py-4 font-bold text-[#234FA2] text-xs">{champ}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Train / Test Split */}
              <div className="bg-white p-10 rounded-2xl border border-slate-100 shadow-sm space-y-6">
                <SectionTitle title="Training & Validation Split" />
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="bg-[#0075BE]/5 border border-[#0075BE]/20 rounded-2xl p-6 space-y-2">
                    <div className="text-[#0075BE] font-black text-lg">Training Set</div>
                    <div className="text-slate-700 font-bold text-sm">June 2021 — December 2023</div>
                    <div className="text-slate-400 text-sm font-medium">4,769 observations aggregated to weekly time series. Models were optimized on this historical signal.</div>
                  </div>
                  <div className="bg-[#234FA2]/5 border border-[#234FA2]/20 rounded-2xl p-6 space-y-2">
                    <div className="text-[#234FA2] font-black text-lg">Test / Validation Set</div>
                    <div className="text-slate-700 font-bold text-sm">January 2024 — September 2024</div>
                    <div className="text-slate-400 text-sm font-medium">1,617 rows (≈ 12 hold-out weeks per item). Models were never trained on this data — used only for validation.</div>
                  </div>
                </div>
              </div>

              {/* Feature Engineering */}
              <div className="bg-white p-10 rounded-2xl border border-slate-100 shadow-sm space-y-6">
                <SectionTitle title="Feature Engineering (ML Models)" />
                <p className="text-slate-500 text-sm leading-relaxed">
                  Weekly aggregated QTY was transformed into a supervised learning dataset for ML models (XGBoost, Random Forest, etc.) using the following features:
                </p>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {[
                    { name: 'Lag Features', desc: 'QTY at lag 1, 2, 3, 4, 8, 12 weeks — captures short and medium-term momentum.' },
                    { name: 'Rolling Statistics', desc: 'Rolling mean (4-week, 12-week) and rolling std (4-week) to capture trend and volatility.' },
                    { name: 'Temporal Features', desc: 'Week-of-year, month, quarter — captures seasonal patterns and calendar effects.' },
                  ].map(f => (
                    <div key={f.name} className="bg-slate-50 rounded-xl p-5 space-y-2">
                      <div className="font-black text-slate-700 text-sm">{f.name}</div>
                      <p className="text-xs text-slate-400 leading-relaxed">{f.desc}</p>
                    </div>
                  ))}
                </div>
              </div>

              {/* Methodology */}
              <div className="bg-white p-10 rounded-2xl border border-slate-100 shadow-sm space-y-6">
                <SectionTitle title="Forecasting Pipeline" />
                <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                  {[
                    { n: '01', title: 'Data Engineering', desc: 'Raw despatch records cleaned, filtered to ACR SPARES & 8 items, aggregated to weekly QTY series per item.' },
                    { n: '02', title: 'Model Competition', desc: 'ML (XGBoost, RF), Time Series (AR, MA, SARIMA, Prophet), and Auto-SARIMA models trained independently per item. Best from each category selected.' },
                    { n: '03', title: 'Validation & Champion', desc: 'All models scored on 12 hold-out weeks. The single lowest-RMSE model becomes the "Champion" and drives production forecasts.' },
                  ].map(s => (
                    <div key={s.n} className="flex gap-4">
                      <div className="text-[#0075BE] font-black text-3xl shrink-0">{s.n}</div>
                      <div>
                        <div className="font-bold text-slate-700 mb-1">{s.title}</div>
                        <p className="text-sm text-slate-400 leading-relaxed">{s.desc}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="pt-2">
                <button onClick={() => setPage('home')} className="text-[#0075BE] font-black hover:underline text-sm">← Back to Home</button>
              </div>
            </div>
          )}

          {page === 'analysis' && (
            <AnalysisPage
              items={items}
              selectedItem={selectedItem}
              setSelectedItem={setSelectedItem}
            />
          )}






          {page === 'dashboard' && (
            <>

              {/* Item Selector & Header */}
              <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-8 p-10 bg-white border border-slate-100 rounded-3xl shadow-sm">
                <div className="space-y-1">
                   <SectionTitle title="Predictive Engines" />
                   <h2 className="text-3xl font-extrabold text-slate-800 tracking-tight">Forecasting Channel</h2>
                   <p className="text-sm text-slate-400 font-medium">Monitoring 12-week rolling demand patterns per item code.</p>
                </div>
                
                <div className="flex items-center gap-4 bg-slate-50 p-4 rounded-2xl border border-slate-100">
                  <div className="flex flex-col">
                    <span className="text-xs font-black text-slate-400 uppercase tracking-widest mb-1">Select Part Number</span>
                    <select
                      value={selectedItem}
                      onChange={(e) => setSelectedItem(e.target.value)}
                      className="bg-transparent border-none text-sm font-bold text-slate-900 focus:ring-0 cursor-pointer p-0 min-w-[220px]"
                    >
                      {items.map(code => <option key={code} value={code}>{code}</option>)}
                    </select>
                  </div>
                  <div className="w-px h-8 bg-slate-200 mx-2" />
                  <div className="p-2 bg-blue-50 text-blue-600 rounded-lg shadow-sm">
                    <Database size={18} />
                  </div>
                </div>
              </div>

              {/* Forecast Chart */}
              <div className="bg-white p-10 rounded-3xl border border-slate-100 shadow-sm">
                <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6 mb-12">
                  <div className="space-y-1">
                    <SectionTitle title="12-Week Rolling Projection" />
                    <div className="flex items-center gap-2">
                      <div className="w-2 h-2 rounded-full bg-blue-500 shadow-[0_0_8px_rgba(59,130,246,0.5)]" />
                      <span className="text-xl font-extrabold text-slate-800">Demand Trajectory</span>
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-6 flex-wrap">
                    {[
                      { label: 'Champion', color: '#234FA2', type: 'solid' },
                      { label: 'ML Target', color: '#0075BE', type: 'dashed' },
                      { label: 'Actuals', color: '#cbd5e1', type: 'bold' }
                    ].map(l => (
                      <div key={l.label} className="flex items-center gap-2">
                        <div className={`w-3 h-1 rounded-full ${l.type === 'dashed' ? 'border-t-2 border-dashed' : 'bg-current'}`} style={{ color: l.color }} />
                        <span className="text-xs font-black text-slate-400 uppercase tracking-widest">{l.label}</span>
                      </div>
                    ))}
                  </div>
                </div>
                
                <div className="h-[550px] w-full relative">
                  {loading.forecast ? (
                    <div className="h-full flex flex-col items-center justify-center gap-5">
                      <div className="relative">
                        <Loader2 className="animate-spin text-blue-600" size={40} />
                        <div className="absolute inset-0 blur-xl bg-blue-400/20 animate-pulse" />
                      </div>
                      <span className="text-xs font-black text-slate-400 uppercase tracking-[0.3em]">Querying ML Models...</span>
                    </div>
                  ) : (
                    <ResponsiveContainer width="100%" height="100%">
                      <ComposedChart data={forecast} margin={{ top: 20, right: 20, left: 10, bottom: 20 }}>
                        <CartesianGrid strokeDasharray="4 4" vertical={false} stroke="#f1f5f9" />
                        <XAxis 
                           dataKey="week" 
                           axisLine={false} 
                           tickLine={false} 
                           tick={{ fontSize: 12, fontWeight: 700, fill: '#94a3b8' }} 
                           dy={10}
                        />
                        <YAxis 
                           axisLine={false} 
                           tickLine={false} 
                           tick={{ fontSize: 12, fontWeight: 700, fill: '#94a3b8' }} 
                           dx={-10}
                        />
                        <Tooltip
                          contentStyle={{ 
                            borderRadius: '20px', 
                            border: 'none', 
                            boxShadow: '0 30px 60px -12px rgba(0,0,0,0.25)',
                            padding: '20px',
                            background: 'rgba(10, 17, 33, 0.95)',
                            color: '#fff'
                          }}
                          itemStyle={{ fontSize: '12px', fontWeight: 600, padding: '2px 0' }}
                          labelStyle={{ fontWeight: 800, marginBottom: '8px', color: '#60A5FA', fontSize: '12px' }}
                          formatter={(val) => val !== null && val !== undefined ? Number(val).toFixed(2) : '--'}
                        />
                        <Area type="monotone" dataKey="ci_upper" stroke="none" fill="#234FA2" fillOpacity={0.07} />
                        <Area type="monotone" dataKey="ci_lower" stroke="none" fill="#234FA2" fillOpacity={0.07} />
                        <Line name={`ML Engine`} type="monotone" dataKey="ml" stroke="#0075BE" strokeWidth={3} dot={false} strokeDasharray="6 4" />
                        <Line name={`TS Engine`} type="monotone" dataKey="ts" stroke="#94A3B8" strokeWidth={2} dot={false} strokeDasharray="3 3" />
                        <Line name="Actual Consumption" type="monotone" dataKey="actual" stroke="#cbd5e1" strokeWidth={3} dot={{ r: 4, fill: '#fff', stroke: '#cbd5e1', strokeWidth: 2 }} />
                        <Line name="Production Champion" type="monotone" dataKey="champion" stroke="#234FA2" strokeWidth={4} dot={{ r: 5, fill: '#fff', stroke: '#234FA2', strokeWidth: 3 }} />
                      </ComposedChart>
                    </ResponsiveContainer>
                  )}
                </div>
              </div>

              {/* Detailed Data Table */}
              <div className="bg-white rounded-3xl border border-slate-100 shadow-sm overflow-hidden">
                <div className="p-10 border-b border-slate-50 flex justify-between items-center">
                  <div className="space-y-1">
                    <SectionTitle title="Granular Observations" />
                    <h3 className="text-xl font-extrabold text-slate-800">Weekly Quantitative Log</h3>
                  </div>
                  <div className="px-4 py-2 bg-slate-50 rounded-xl border border-slate-100 text-[10px] font-black text-slate-500 uppercase tracking-widest">
                    P/N: {selectedItem}
                  </div>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full text-left">
                    <thead>
                      <tr className="bg-slate-50/50">
                        <th className="px-10 py-6 text-[10px] font-black text-slate-400 uppercase tracking-[0.2em]">Week Schedule</th>
                        <th className="px-10 py-6 text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] text-center">Historical Actual</th>
                        <th className="px-10 py-6 text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] text-center">ML Optimized</th>
                        <th className="px-10 py-6 text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] text-center">Champion Result</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-50">
                      {forecast.map((row, i) => (
                        <tr key={i} className="group hover:bg-slate-50/80 transition-all duration-200">
                          <td className="px-10 py-5 font-extrabold text-slate-700 text-sm">{row.week}</td>
                          <td className="px-10 py-5 text-center font-mono text-sm text-slate-500 italic">{row.actual ?? '--'}</td>
                          <td className="px-10 py-5 text-center font-mono text-sm font-bold text-[#0075BE]">{row.ml !== null ? Number(row.ml).toFixed(2) : '--'}</td>
                          <td className="px-10 py-5 text-center">
                             <span className="inline-block px-4 py-1.5 bg-blue-50 text-[#234FA2] rounded-lg font-black font-mono text-sm border border-blue-100">
                               {row.champion !== null ? Number(row.champion).toFixed(2) : '--'}
                             </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                    <tfoot className="bg-[#0A1121] text-white">
                      <tr className="divide-x divide-white/5">
                        <td className="px-10 py-8 uppercase tracking-[0.25em] text-[10px] font-black text-slate-400">Total Aggregate Demand</td>
                        <td className="px-10 py-8 text-center font-black text-xl">
                          {forecast.reduce((acc, r) => acc + (r.actual || 0), 0).toFixed(1)}
                        </td>
                        <td className="px-10 py-8 text-center font-black text-xl text-blue-400">
                          {forecast.reduce((acc, r) => acc + (r.ml || 0), 0).toFixed(1)}
                        </td>
                        <td className="px-10 py-8 text-center">
                           <div className="inline-block px-6 py-2 bg-blue-600 rounded-xl shadow-lg shadow-blue-900/40 text-xl font-black">
                             {forecast.reduce((acc, r) => acc + (r.champion || 0), 0).toFixed(1)}
                           </div>
                        </td>
                      </tr>
                    </tfoot>
                  </table>
                </div>
              </div>

              {/* Forecast vs Actual Validation Chart */}
              {validation.length > 0 && (
                <div className="bg-white p-8 rounded-2xl border border-slate-100 shadow-sm">
                  <div className="flex justify-between items-center mb-8">
                    <SectionTitle title="Forecast vs Actual Validation" />
                    <div className="text-[10px] font-black uppercase text-[#0075BE] bg-[#0075BE]/10 px-3 py-1 rounded-full">
                      Champion Model — Held-Out 12 Weeks
                    </div>
                  </div>
                  <div className="h-[380px]">
                    <ResponsiveContainer width="100%" height="100%">
                      <ComposedChart data={validation} margin={{ top: 10, right: 20, left: 10, bottom: 10 }}>
                        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                        <XAxis dataKey="week" axisLine={false} tickLine={false} tick={{ fontSize: 11, fontWeight: 700, fill: '#94a3b8' }} />
                        <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 11, fontWeight: 700, fill: '#94a3b8' }} />
                        <Tooltip
                          formatter={(val) => val !== null && val !== undefined ? Number(val).toFixed(2) : '---'}
                          contentStyle={{ borderRadius: '16px', border: 'none', boxShadow: '0 25px 50px -12px rgb(0 0 0 / 0.2)', fontSize: 12 }}
                        />
                        <Legend verticalAlign="top" height={36} />
                        <Area type="monotone" dataKey="ci_upper" stroke="none" fill="#234FA2" fillOpacity={0.08} name="95% CI" legendType="square" />
                        <Area type="monotone" dataKey="ci_lower" stroke="none" fill="#234FA2" fillOpacity={0.08} legendType="none" />
                        <Line name="Actual (Hold-Out)" type="monotone" dataKey="actual" stroke="#0075BE" strokeWidth={3} dot={{ r: 5, fill: '#fff', stroke: '#0075BE', strokeWidth: 2 }} />
                        <Line name={`Forecast (${modelNames.champion || 'Champion'})`} type="monotone" dataKey="forecast" stroke="#234FA2" strokeWidth={3} strokeDasharray="6 3" dot={{ r: 4, fill: '#fff', stroke: '#234FA2', strokeWidth: 2 }} />
                      </ComposedChart>
                    </ResponsiveContainer>
                  </div>
                  <p className="text-xs text-slate-400 mt-4 text-center">
                    Shaded band shows the 95% confidence interval. Validation was performed on 12 hold-out weeks not seen during model training.
                  </p>
                </div>
              )}

              {/* Champion Highlight - MOVED BELOW TABLE */}
              <div className="bg-white p-8 rounded-2xl border border-slate-100 shadow-sm border-l-4 border-l-[#234FA2]">
                <div className="flex flex-col lg:flex-row justify-between gap-10">
                  <div className="flex-1 space-y-4">
                    <div className="flex items-center gap-3">
                      <div className="p-2 bg-[#234FA2]/10 text-[#234FA2] rounded-lg"><CheckCircle2 size={24} /></div>
                      <h3 className="text-2xl font-black text-slate-800 tracking-tight">Champion Model: {metrics?.champion}</h3>
                    </div>
                    <p className="text-slate-500 text-sm leading-relaxed max-w-2xl">
                      {metrics?.champion} is identified as the most accurate model for this item's historical pattern.
                      It is currently the designated engine for automatic demand projections.
                    </p>
                  </div>
                </div>
                     {/* Model Insights */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                <div className="bg-white p-6 rounded-2xl border border-slate-100 shadow-sm text-center space-y-2">
                  <span className="text-xs font-bold text-slate-400 uppercase tracking-widest">Trend</span>
                  <div className="text-lg font-black text-slate-800">Stable / Linear</div>
                </div>
                <div className="bg-white p-6 rounded-2xl border border-slate-100 shadow-sm text-center space-y-2">
                  <span className="text-xs font-bold text-slate-400 uppercase tracking-widest">Seasonality</span>
                  <div className="text-lg font-black text-slate-800">None Detected</div>
                </div>
                <div className="bg-white p-6 rounded-2xl border border-slate-100 shadow-sm text-center space-y-2">
                  <span className="text-xs font-bold text-slate-400 uppercase tracking-widest">Volatility</span>
                  <div className="text-lg font-black text-accent">Medium</div>
                </div>
                <div className="bg-white p-6 rounded-2xl border border-slate-100 shadow-sm text-center space-y-2">
                  <span className="text-xs font-bold text-slate-400 uppercase tracking-widest">Observations</span>
                  <div className="text-lg font-black text-slate-800">156 Weeks</div>
                </div>
              </div>          </div>

              {/* Export Footer */}
              <div className="p-10 bg-slate-900 rounded-3xl text-white flex flex-col lg:flex-row justify-between items-center gap-10">
                <div className="space-y-2">
                  <h3 className="text-xl font-black tracking-tight">Export Production Data</h3>
                  <p className="text-slate-400 text-sm font-medium">Download the latest validated results and model metadata for external reporting.</p>
                </div>
                <div className="flex flex-wrap gap-4">
                  <button
                    onClick={() => window.open(`${API_BASE}/download/forecast/${selectedItem}`, '_blank')}
                    className="flex items-center gap-2 px-6 py-3 bg-white/10 hover:bg-white/20 rounded-xl font-bold text-sm transition-all"
                  >
                    <Download size={18} /> Forecast CSV
                  </button>
                  <button
                    onClick={() => window.open(`${API_BASE}/download/validation/${selectedItem}`, '_blank')}
                    className="flex items-center gap-2 px-6 py-3 bg-white/10 hover:bg-white/20 rounded-xl font-bold text-sm transition-all"
                  >
                    <FileText size={18} /> Validation Report
                  </button>
                  <button
                    onClick={() => window.open(`${API_BASE}/download/comparison/summary`, '_blank')}
                    className="flex items-center gap-2 px-6 py-3 bg-white/10 hover:bg-white/20 rounded-xl font-bold text-sm transition-all"
                  >
                    <PieChart size={18} /> Comparison CSV
                  </button>
                </div>
              </div>
            </>
          )}
        </div>
      </main>
    </div>
  );
}

// --- App Entry Point with Routing ---

export default function App() {
  const [view, setView] = useState("landing");

  if (view === "landing") {
    return <LandingPage onEnter={() => setView("login")} />;
  }

  if (view === "login") {
    return <LoginPage onLogin={() => setView("dashboard")} onBack={() => setView("landing")} />;
  }

  return <Dashboard onLogout={() => setView("login")} />;
}

