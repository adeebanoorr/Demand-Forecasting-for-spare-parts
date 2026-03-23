import React, { useState, useEffect, useCallback, useMemo } from 'react';
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

const API_BASE = import.meta.env.VITE_API_URL || "/api";
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
    fetch(`${API_BASE}/mstl/${encodeURIComponent(mstlItem)}`)
      .then(r => r.ok ? r.json() : r.text().then(t => Promise.reject(t)))
      .then(d => { setMstlData(d); setMstlLoading(false); })
      .catch(e => { setMstlError(String(e)); setMstlLoading(false); });
  }, [mstlItem]);

  const panels = [
    { key: 'observed', label: 'Observed (Weekly QTY)', color: '#0075BE' },
    { key: 'trend', label: 'Trend Component', color: '#e74c3c' },
    { key: 'seasonal', label: 'Seasonal Component', color: '#27ae60' },
    { key: 'residual', label: 'Residual', color: '#7f8c8d' },
  ];
  const tick = { fontSize: 10, fill: '#94a3b8' };

  return (
    <div className="animate-in fade-in slide-in-from-bottom-8 duration-700 space-y-6">
      <div className="bg-white p-8 rounded-2xl border border-slate-100 shadow-sm space-y-6">
        <div className="flex justify-between items-center flex-wrap gap-4">
          <div className="space-y-1">
            <h2 className="text-slate-800 font-black text-lg tracking-tight">MSTL Component Analysis</h2>
            <p className="text-xs text-slate-400">Trend, Seasonality & Residual Decomposition</p>
          </div>
          <div className="flex items-center gap-4 flex-wrap">
            <div className="flex items-center gap-2">
              <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Select Item:</span>
              <select
                value={mstlItem}
                onChange={(e) => { setMstlItem(e.target.value); setSelectedItem(e.target.value); }}
                className="px-3 py-1.5 bg-slate-50 border border-slate-100 rounded-lg text-xs font-bold text-slate-900 focus:ring-2 focus:ring-teal/20 transition-all cursor-pointer"
              >
                {items.map(code => <option key={code} value={code}>{code}</option>)}
              </select>
            </div>
            <div className="text-[10px] font-black uppercase text-teal bg-teal/10 px-3 py-1 rounded-full">
              Trend & Seasonality Decomposition
            </div>
          </div>
        </div>

        <p className="text-xs text-slate-400 leading-relaxed max-w-2xl">
          MSTL (Multiple Seasonal-Trend decomposition using Loess) extracts the underlying structure
          of each item's weekly demand history into four interactive components below.
        </p>

        {mstlLoading && (
          <div className="flex items-center justify-center h-48 text-teal gap-3">
            <Loader2 className="animate-spin" size={20} />
            <span className="text-sm font-bold">Computing decomposition…</span>
          </div>
        )}
        {mstlError && (
          <div className="text-red-400 text-sm p-4 bg-red-50 rounded-xl">Error loading data: {mstlError}</div>
        )}
        {!mstlLoading && !mstlError && mstlData.length > 0 && (
          <div className="space-y-4">
            {panels.map(({ key, label, color }) => (
              <div key={key} className="bg-slate-50/60 rounded-xl p-4">
                <div className="flex items-center gap-2 mb-2 pl-1">
                  <div className="w-2.5 h-2.5 rounded-full" style={{ background: color }} />
                  <span className="text-[10px] font-black text-slate-500 uppercase tracking-widest">{label}</span>
                </div>
                <ResponsiveContainer width="100%" height={130}>
                  <ComposedChart data={mstlData} margin={{ top: 4, right: 20, left: 10, bottom: 4 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
                    <XAxis
                      dataKey="week"
                      tick={tick}
                      tickFormatter={v => v ? v.slice(0, 7) : ''}
                      interval={Math.floor(mstlData.length / 8)}
                    />
                    <YAxis tick={tick} tickFormatter={v => Number(v).toFixed(0)} width={52} />
                    <Tooltip
                      contentStyle={{ fontSize: 11, borderRadius: 8, border: '1px solid #e2e8f0' }}
                      formatter={(v) => [Number(v).toFixed(2), label]}
                      labelFormatter={l => `Week: ${l}`}
                    />
                    {key === 'residual' ? (
                      <Area type="monotone" dataKey={key} stroke={color} fill={color} fillOpacity={0.2} strokeWidth={1.5} dot={false} />
                    ) : (
                      <Line type="monotone" dataKey={key} stroke={color} strokeWidth={2} dot={false} activeDot={{ r: 4 }} />
                    )}
                  </ComposedChart>
                </ResponsiveContainer>
              </div>
            ))}
          </div>
        )}
        {!mstlLoading && !mstlError && mstlData.length === 0 && mstlItem && (
          <div className="text-slate-400 text-center py-16 text-sm">No data available for this item.</div>
        )}
      </div>
    </div>
  );
};

// --- Components ---

const SidebarItem = ({ icon: Icon, label, active, onClick }) => (
  <div
    onClick={onClick}
    className={`flex items-center gap-3 px-4 py-3 rounded-lg cursor-pointer transition-all ${active ? 'bg-white/10 text-white font-bold' : 'text-white/60 hover:bg-white/5 hover:text-white'
      }`}
  >
    <Icon size={18} />
    <span className="text-sm tracking-wide">{label}</span>
  </div>
);

const KPICard = ({ title, value, subtext, icon: Icon, isLoading }) => {
  // Hide cards that mention technical scores (RMSE, etc.)
  const hideKeywords = ['rmse', 'smape', 'mae', 'auto'];
  if (hideKeywords.some(key => title.toLowerCase().includes(key))) return null;

  return (
    <div className="bg-white p-5 rounded-xl border border-slate-100 shadow-sm flex flex-col gap-2 flex-1 min-w-[200px]">
      <div className="flex justify-between items-start">
        <div className="p-2 bg-slate-50 rounded-lg text-teal">
          <Icon size={18} />
        </div>
        <span className="text-slate-400 text-[10px] font-bold uppercase tracking-widest">{title}</span>
      </div>
      {isLoading ? (
        <div className="h-8 bg-slate-50 animate-pulse rounded w-1/2"></div>
      ) : (
        <div className="text-xl font-black text-slate-800 tracking-tight">{value}</div>
      )}
    </div>
  );
};

const SectionTitle = ({ title }) => (
  <h3 className="text-xs font-black text-slate-400 uppercase tracking-[0.2em] mb-4 flex items-center gap-2">
    <div className="w-1.5 h-3 bg-teal rounded-full" />
    {title}
  </h3>
);

// --- Main Application ---

export default function App() {
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
      .then(res => res.json())
      .then(data => {
        setItems(data);
        if (data.length > 0) setSelectedItem(data[0]);
        setLoading(prev => ({ ...prev, items: false }));
      });

    // Global Metrics
    fetch(`${API_BASE}/global_metrics`)
      .then(res => res.json())
      .then(data => {
        setGlobalMetrics(data);
        setLoading(prev => ({ ...prev, global: false }));
      });

    // Portfolio Demand Aggregate
    fetch(`${API_BASE}/aggregate_forecast`)
      .then(res => res.json())
      .then(data => {
        setAggregateForecast(data);
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
        fetch(`${API_BASE}/comparison/${itemCode}`).then(r => r.json()),
        fetch(`${API_BASE}/forecast_comparison/${itemCode}`).then(r => r.json()),
        fetch(`${API_BASE}/validation/${itemCode}`).then(r => r.ok ? r.json() : null).catch(() => null)
      ]);
      setMetrics(mRes);
      setComparison(cRes);
      setForecast(compRes.data);
      setModelNames(compRes.models);
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
    <div className="flex min-h-screen bg-slate-50 font-sans">
      {/* Sidebar - Solid Teal */}
      <aside className="w-64 bg-[#0075BE] text-white flex flex-col fixed h-full z-20 shadow-xl">

        <div className="p-6 space-y-8 flex-1">
          <div className="space-y-4">
            <span className="text-[10px] font-bold text-white/40 uppercase tracking-widest pl-4">Navigation</span>
            <nav className="space-y-1">
              <SidebarItem icon={Home} label="Home" active={page === 'home'} onClick={() => setPage('home')} />
              <SidebarItem icon={PieChart} label="Analysis" active={page === 'analysis'} onClick={() => setPage('analysis')} />
              <SidebarItem icon={LayoutDashboard} label="Forecasting" active={page === 'dashboard'} onClick={() => setPage('dashboard')} />
              <SidebarItem icon={Info} label="About" active={page === 'about'} onClick={() => setPage('about')} />
            </nav>
          </div>
        </div>

      </aside>

      {/* Main Content */}
      <main className="flex-1 ml-64 min-h-screen">
        {/* Header Bar */}
        <header className="h-20 bg-white border-b border-slate-100 flex items-center justify-between px-10 sticky top-0 z-10 shadow-sm">
          <div className="w-48 hidden lg:block">
            {/* Left placeholder to balance the header */}
          </div>

          <div className="flex flex-col items-center justify-center gap-1 flex-1">
            <img src="/logo.png" alt="Indi4 Logo" className="h-10 w-auto" />
            <div className="flex items-center gap-2">
              <Boxes className="text-teal" size={16} />
              <h1 className="text-sm font-bold text-slate-700 uppercase tracking-widest text-center">AI Spare Parts Demand Forecasting</h1>
            </div>
          </div>

          <div className="flex items-center gap-6 w-48 justify-end">
            <div className="flex items-center gap-2 px-3 py-1 bg-[#234FA2]/10 rounded-full">
              <div className="w-1.5 h-1.5 rounded-full bg-[#234FA2] animate-pulse" />
              <span className="text-[10px] font-black text-[#234FA2] uppercase">Production Active</span>
            </div>
          </div>
        </header>

        <div className="p-6 w-full space-y-6">
          {page === 'home' && (
            <div className="animate-in fade-in slide-in-from-bottom-8 duration-700">
              <div className="bg-white p-6 rounded-2xl border border-slate-100 shadow-sm space-y-4">
                <div className="flex justify-between items-center">
                  <SectionTitle title="Spare Parts Performance Dashboard" />
                  <div className="flex items-center gap-2 px-3 py-1 bg-teal/10 rounded-full text-[10px] font-black text-teal uppercase tracking-widest">
                    Regional &amp; Revenue Analytics
                  </div>
                </div>
                <div className="relative rounded-2xl overflow-hidden border border-slate-100 bg-slate-50" style={{ height: '85vh' }}>
                  <iframe
                    src={`${ANALYTICS_URL}?v=4`}
                    className="w-full h-full border-none"
                    title="Spare Parts Performance Dashboard"
                    loading="lazy"
                  />
                </div>
              </div>
            </div>
          )}

          {page === 'about' && (
            <div className="animate-in fade-in slide-in-from-bottom-8 duration-700 space-y-6">

              {/* Dataset Overview */}
              <div className="bg-white p-10 rounded-2xl border border-slate-100 shadow-sm space-y-6">
                <SectionTitle title="Dataset Overview" />
                <p className="text-slate-500 leading-relaxed">
                  The source data is KPCL's internal despatch records (<code className="bg-slate-100 px-1 rounded text-xs">KPC___Despatch_Details_260924.xlsx</code>),
                  covering all outward dispatches up to September 2024. From the full dataset, only records belonging to the <strong>ACR SPARES</strong> product model were retained,
                  and further filtered to the 8 highest-demand spare part codes prioritized for forecasting.
                </p>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  {[
                    { label: 'Raw Rows', value: '65,536' },
                    { label: 'Raw Columns', value: '40' },
                    { label: 'Training Rows', value: '4,769' },
                    { label: 'Test Rows', value: '1,617' },
                  ].map(s => (
                    <div key={s.label} className="bg-slate-50 rounded-xl p-5 text-center space-y-1">
                      <div className="text-2xl font-black text-teal">{s.value}</div>
                      <div className="text-[10px] font-black text-slate-400 uppercase tracking-widest">{s.label}</div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Selected Features */}
              <div className="bg-white p-10 rounded-2xl border border-slate-100 shadow-sm space-y-6">
                <SectionTitle title="Columns Selected for Training" />
                <p className="text-slate-500 text-sm leading-relaxed mb-2">
                  Out of 40 raw columns, only 5 were selected as relevant to demand forecasting. All other fields (invoice details, taxes, GST, transporter, etc.) were dropped.
                </p>
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-sm">
                    <thead>
                      <tr className="bg-slate-50">
                        <th className="px-6 py-3 text-[10px] font-black text-slate-400 uppercase tracking-widest">Column (Raw)</th>
                        <th className="px-6 py-3 text-[10px] font-black text-slate-400 uppercase tracking-widest">Renamed To</th>
                        <th className="px-6 py-3 text-[10px] font-black text-slate-400 uppercase tracking-widest">Type</th>
                        <th className="px-6 py-3 text-[10px] font-black text-slate-400 uppercase tracking-widest">Purpose</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-50">
                      {[
                        ['OA DATE', 'OA_DATE', 'Date', 'Order acceptance date — used as the time axis'],
                        ['ITEM CODE', 'ITEM_CODE', 'String', 'Unique spare part identifier (e.g., 082.04.030.50.)'],
                        ['QTY', 'QTY', 'Numeric', 'Quantity dispatched — the target variable for forecasting'],
                        ['MODEL', 'MODEL', 'String', 'Product model — filtered to ACR SPARES only'],
                        ['ITEM DESCRIPTION', 'ITEM_DESCRIPTION', 'String', 'Human-readable name of the spare part'],
                      ].map(([raw, renamed, type, purpose]) => (
                        <tr key={raw} className="hover:bg-slate-50 transition-colors">
                          <td className="px-6 py-4 font-mono text-xs font-bold text-slate-700">{raw}</td>
                          <td className="px-6 py-4 font-mono text-xs text-teal font-bold">{renamed}</td>
                          <td className="px-6 py-4 text-xs text-slate-500">{type}</td>
                          <td className="px-6 py-4 text-xs text-slate-500">{purpose}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* 8 Items */}
              <div className="bg-white p-10 rounded-2xl border border-slate-100 shadow-sm space-y-6">
                <SectionTitle title="8 Selected Spare Part Codes" />
                <p className="text-slate-500 text-sm leading-relaxed mb-2">
                  These 8 items were selected based on highest dispatch frequency within the ACR SPARES model. Training rows per item reflect order-level records (before weekly aggregation).
                </p>
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-sm">
                    <thead>
                      <tr className="bg-slate-50">
                        <th className="px-6 py-3 text-[10px] font-black text-slate-400 uppercase tracking-widest">#</th>
                        <th className="px-6 py-3 text-[10px] font-black text-slate-400 uppercase tracking-widest">Item Code</th>
                        <th className="px-6 py-3 text-[10px] font-black text-slate-400 uppercase tracking-widest">Item Description</th>
                        <th className="px-6 py-3 text-[10px] font-black text-slate-400 uppercase tracking-widest">Training Rows</th>
                        <th className="px-6 py-3 text-[10px] font-black text-slate-400 uppercase tracking-widest">Champion Model</th>
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
                          <td className="px-6 py-4 font-mono text-sm font-bold text-slate-800">{code}</td>
                          <td className="px-6 py-4 text-slate-600 text-sm">{desc}</td>
                          <td className="px-6 py-4 text-slate-500">{rows}</td>
                          <td className="px-6 py-4 font-bold text-[#234FA2]">{champ}</td>
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
                  <div className="bg-teal/5 border border-teal/20 rounded-2xl p-6 space-y-2">
                    <div className="text-teal font-black text-lg">Training Set</div>
                    <div className="text-slate-700 font-bold text-sm">June 2021 — December 2023</div>
                    <div className="text-slate-400 text-sm">4,769 order-level rows → aggregated to weekly QTY time series per item. Models were trained on these weekly series.</div>
                  </div>
                  <div className="bg-[#234FA2]/5 border border-[#234FA2]/20 rounded-2xl p-6 space-y-2">
                    <div className="text-[#234FA2] font-black text-lg">Test / Validation Set</div>
                    <div className="text-slate-700 font-bold text-sm">January 2024 — September 2024</div>
                    <div className="text-slate-400 text-sm">1,617 rows (≈ 12 hold-out weeks per item). Models were never trained on this data — used only for final RMSE validation.</div>
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
                      <div className="text-teal font-black text-3xl shrink-0">{s.n}</div>
                      <div>
                        <div className="font-bold text-slate-700 mb-1">{s.title}</div>
                        <p className="text-sm text-slate-400 leading-relaxed">{s.desc}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="pt-2">
                <button onClick={() => setPage('home')} className="text-teal font-bold hover:underline text-sm">← Back to Home</button>
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

              {/* Item Selector */}
              <div className="flex items-center gap-4 p-8 bg-white border border-slate-100 rounded-2xl shadow-sm">
                <span className="text-sm font-bold text-slate-600">Select Item Code:</span>
                <select
                  value={selectedItem}
                  onChange={(e) => setSelectedItem(e.target.value)}
                  className="px-4 py-2 bg-slate-50 border border-slate-100 rounded-lg text-sm font-bold text-slate-900 focus:ring-2 focus:ring-teal/20 min-w-[200px]"
                >
                  {items.map(code => <option key={code} value={code}>{code}</option>)}
                </select>
              </div>



              {/* Forecast Chart */}
              <div className="bg-white p-10 rounded-2xl border border-slate-100 shadow-sm">
                <div className="flex justify-between items-center mb-10">
                  <SectionTitle title="12-Week Forecast Projection" />
                  <div className="flex items-center gap-2 text-xs font-bold text-slate-400">
                    <div className="flex items-center gap-1"><div className="w-3 h-3 rounded-full bg-slate-200" /> Historical</div>
                    <div className="flex items-center gap-1 ml-4"><div className="w-3 h-3 rounded-full bg-[#234FA2]" /> Projection</div>
                  </div>
                </div>
                <div className="h-[500px] w-full min-h-[500px] relative">
                  {loading.forecast ? (
                    <div className="h-full flex flex-col items-center justify-center gap-4 text-slate-400">
                      <Loader2 className="animate-spin" size={40} />
                      <span className="text-xs font-bold uppercase tracking-widest">Generating Engine Logic...</span>
                    </div>
                  ) : (
                    <div className="h-full w-full">
                      <ResponsiveContainer width="100%" height="100%">
                        <ComposedChart data={forecast} margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
                          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                          <XAxis dataKey="week" axisLine={false} tickLine={false} tick={{ fontSize: 11, fontWeight: 700, fill: '#94a3b8' }} />
                          <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 11, fontWeight: 700, fill: '#94a3b8' }} />
                          <Tooltip
                            formatter={(val) => val !== null && val !== undefined ? Number(val).toFixed(2) : '---'}
                            contentStyle={{ borderRadius: '16px', border: 'none', boxShadow: '0 25px 50px -12px rgb(0 0 0 / 0.2)' }}
                          />
                          <Legend verticalAlign="top" height={40} />
                          <Area type="monotone" dataKey="ci_upper" stroke="none" fill="#234FA2" fillOpacity={0.05} />
                          <Area type="monotone" dataKey="ci_lower" stroke="none" fill="#234FA2" fillOpacity={0.05} />
                          <Line name={`Best ML (${modelNames.ml})`} type="monotone" dataKey="ml" stroke="#0075BE" strokeWidth={3} dot={{ r: 3, fill: '#fff', stroke: '#0075BE', strokeWidth: 2 }} strokeDasharray="5 5" />
                          <Line name={`Best TS (${modelNames.ts})`} type="monotone" dataKey="ts" stroke="#64748b" strokeWidth={3} dot={{ r: 3, fill: '#fff', stroke: '#64748b', strokeWidth: 2 }} strokeDasharray="3 3" />
                          <Line name={`Champion (${modelNames.champion})`} type="monotone" dataKey="champion" stroke="#234FA2" strokeWidth={4} dot={{ r: 4, fill: '#fff', stroke: '#234FA2', strokeWidth: 2 }} />
                          <Line name="Actual History" type="monotone" dataKey="actual" stroke="#cbd5e1" strokeWidth={3} dot={{ r: 4, fill: '#fff', stroke: '#cbd5e1', strokeWidth: 2 }} />
                        </ComposedChart>
                      </ResponsiveContainer>
                    </div>
                  )}
                </div>
              </div>

              {/* Forecast Comparison Table */}
              <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden animate-in fade-in slide-in-from-bottom-4">
                <div className="p-8 border-b border-slate-50 flex justify-between items-center bg-slate-50/20">
                  <SectionTitle title="Detailed Forecast Data" />
                  <div className="text-[10px] font-black uppercase text-[#234FA2] bg-[#234FA2]/10 px-3 py-1 rounded-full">{selectedItem} Metrics</div>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full text-left">
                    <thead>
                      <tr className="bg-slate-50/50">
                        <th className="px-10 py-5 text-[10px] font-black text-slate-400 uppercase tracking-widest">Week Index</th>
                        <th className="px-10 py-5 text-[10px] font-black text-slate-400 uppercase tracking-widest text-center">Actual Consumption</th>
                        <th className="px-10 py-5 text-[10px] font-black text-slate-400 uppercase tracking-widest text-center">Best ML</th>
                        <th className="px-10 py-5 text-[10px] font-black text-slate-400 uppercase tracking-widest text-center">Best TS</th>
                        <th className="px-10 py-5 text-[10px] font-black text-slate-400 uppercase tracking-widest text-center">Champion</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-50">
                      {forecast.map((row, i) => (
                        <tr key={i} className="hover:bg-slate-50 transition-colors">
                          <td className="px-10 py-4 font-bold text-slate-700">{row.week}</td>
                          <td className="px-10 py-4 text-center font-mono text-sm">{row.actual !== null && row.actual !== undefined ? Number(row.actual).toFixed(2) : '---'}</td>
                          <td className="px-10 py-4 text-center font-mono text-sm font-bold text-[#0075BE]">{row.ml !== null && row.ml !== undefined ? Number(row.ml).toFixed(2) : '---'}</td>
                          <td className="px-10 py-4 text-center font-mono text-sm font-bold text-[#64748b]">{row.ts !== null && row.ts !== undefined ? Number(row.ts).toFixed(2) : '---'}</td>
                          <td className="px-10 py-4 text-center font-mono text-sm font-bold text-[#234FA2]">{row.champion !== null && row.champion !== undefined ? Number(row.champion).toFixed(2) : '---'}</td>
                        </tr>
                      ))}
                    </tbody>
                    <tfoot className="bg-slate-900 text-white font-black overflow-hidden rounded-b-2xl">
                      <tr>
                        <td className="px-10 py-6 uppercase tracking-widest text-[10px]">Total Demand (12 Weeks)</td>
                        <td className="px-10 py-6 text-center font-mono text-lg">
                          {forecast.reduce((acc, r) => acc + (r.actual || 0), 0).toFixed(2)}
                        </td>
                        <td className="px-10 py-6 text-center font-mono text-lg text-[#0075BE]">
                          {forecast.reduce((acc, r) => acc + (r.ml || 0), 0).toFixed(2)}
                        </td>
                        <td className="px-10 py-6 text-center font-mono text-lg text-[#64748b]">
                          {forecast.reduce((acc, r) => acc + (r.ts || 0), 0).toFixed(2)}
                        </td>
                        <td className="px-10 py-6 text-center font-mono text-lg text-[#234FA2]">
                          {forecast.reduce((acc, r) => acc + (r.champion || 0), 0).toFixed(2)}
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
              </div>

              {/* Model Insights */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                <div className="bg-white p-6 rounded-2xl border border-slate-100 shadow-sm text-center space-y-2">
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Trend</span>
                  <div className="text-lg font-black text-slate-800">Stable / Linear</div>
                </div>
                <div className="bg-white p-6 rounded-2xl border border-slate-100 shadow-sm text-center space-y-2">
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Seasonality</span>
                  <div className="text-lg font-black text-slate-800">None Detected</div>
                </div>
                <div className="bg-white p-6 rounded-2xl border border-slate-100 shadow-sm text-center space-y-2">
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Volatility</span>
                  <div className="text-lg font-black text-accent">Medium</div>
                </div>
                <div className="bg-white p-6 rounded-2xl border border-slate-100 shadow-sm text-center space-y-2">
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Observations</span>
                  <div className="text-lg font-black text-slate-800">156 Weeks</div>
                </div>
              </div>

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
                    onClick={() => window.open(`${API_BASE}/download/comparison`, '_blank')}
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
