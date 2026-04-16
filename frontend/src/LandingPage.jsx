import { useState, useEffect, useRef } from "react";
import { BarChart2, TrendingUp, Cpu, Layout, ArrowRight, ShieldCheck, Database, AlertTriangle, LineChart, PieChart } from "lucide-react";

export default function LandingPage({ onEnter }) {
  const [mounted, setMounted] = useState(false);
  const problemRef = useRef(null);
  
  useEffect(() => {
    setMounted(true);
  }, []);

  const scrollToProblem = () => {
    problemRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  // Palette constants
  const P_NAVY = "#152F61";
  const P_DEEP = "#1C3F82";
  const P_PRIMARY = "#234FA2";
  const P_BRAND = "#0075BE";
  const P_LIGHT = "#E6F1F8";
  const P_ACCENT = "#E07C3A";
  const P_SURFACE = "#FEF3EB";

  const HeroCircle = ({ size, color, top, right, bottom, left, blur = 100 }) => (
    <div style={{
      position: "absolute",
      width: size, height: size,
      background: color,
      borderRadius: "50%",
      top, right, bottom, left,
      filter: `blur(${blur}px)`,
      opacity: 0.12,
      zIndex: 0,
      pointerEvents: "none"
    }} />
  );

  return (
    <div style={{
      minHeight: "100vh",
      background: P_NAVY,
      color: P_LIGHT,
      fontFamily: "'Inter', sans-serif",
      overflowX: "hidden",
      position: "relative",
    }}>
      <HeroCircle size="600px" color={P_BRAND} top="-10%" right="-5%" />
      <HeroCircle size="500px" color={P_ACCENT} bottom="5%" left="-5%" />

      <style>{`
        @keyframes slideUp { from { opacity: 0; transform: translateY(30px); } to { opacity: 1; transform: translateY(0); } }
        .animate-up { animation: slideUp 0.8s cubic-bezier(0.16, 1, 0.3, 1) forwards; }
        .btn-hover:hover { transform: translateY(-2px); box-shadow: 0 10px 20px -5px rgba(0, 117, 190, 0.3); }
        .grid-card { transition: all 0.3s ease; }
        .grid-card:hover { transform: translateY(-5px); border-color: rgba(230, 241, 248, 0.2) !important; background: rgba(230,241,248,0.05) !important; }
      `}</style>

      {/* Navigation */}
      <nav style={{
        padding: "20px 80px",
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        zIndex: 50,
        position: "fixed",
        top: 0,
        left: 0,
        right: 0,
        background: `rgba(21, 47, 97, 0.85)`,
        backdropFilter: "blur(12px)",
        borderBottom: "1px solid rgba(255,255,255,0.05)"
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <div style={{
            width: 36, height: 36, background: P_BRAND, borderRadius: 10,
            display: "flex", alignItems: "center", justifyContent: "center",
          }}>
            <BarChart2 color="#fff" size={18} />
          </div>
          <span style={{ fontSize: "1.1rem", fontWeight: 800, letterSpacing: "-0.01em" }}>
            Demand <span style={{ color: P_BRAND }}>Analytics</span>
          </span>
        </div>

        <button
          onClick={onEnter}
          style={{
            padding: "10px 24px", background: "rgba(230,241,248,0.05)", border: "1px solid rgba(230,241,248,0.1)",
            borderRadius: "50px", color: P_LIGHT, fontWeight: 700, fontSize: "14px",
            cursor: "pointer", transition: "all 0.2s", display: "flex", alignItems: "center", gap: 8
          }}
          className="btn-hover"
        >
          Login <ArrowRight size={16} />
        </button>
      </nav>

      {/* Hero Header */}
      <header style={{
        maxWidth: 1200, margin: "0 auto", padding: "160px 20px 80px",
        textAlign: "center", position: "relative", zIndex: 1
      }}>
        <div className="animate-up">
          <h1 style={{
            fontSize: "clamp(3.5rem, 7vw, 5rem)",
            fontWeight: 900, lineHeight: 0.95,
            letterSpacing: "-0.05em", marginBottom: "40px"
          }}>
            Industrial Spare Part <br />
            <span style={{ color: P_BRAND }}>Demand Forecasting.</span>
          </h1>

          <div style={{ display: "flex", gap: "1.5rem", justifyContent: "center", marginBottom: "80px" }}>
            <button
               onClick={scrollToProblem}
               style={{
                padding: "20px 48px", background: P_BRAND, color: "#fff",
                borderRadius: "50px", border: "none", fontSize: "1.1rem",
                fontWeight: 800, cursor: "pointer", transition: "all 0.2s"
              }}
              className="btn-hover"
            >
              Explore Platform
            </button>
            <button
              onClick={onEnter}
              style={{
                padding: "20px 48px", background: "#fff", color: P_NAVY,
                borderRadius: "50px", border: "none", fontSize: "1.1rem",
                fontWeight: 800, cursor: "pointer", transition: "all 0.2s"
              }}
              className="btn-hover"
            >
              Get Started
            </button>
          </div>
        </div>

        {/* Stats Section */}
        <div style={{
          display: "grid", gridTemplateColumns: "repeat(4, 1fr)",
          gap: 1, background: "rgba(230,241,248,0.1)",
          borderRadius: "32px", overflow: "hidden",
          border: "1px solid rgba(230,241,248,0.1)"
        }}>
          {[
            { label: "Tracked Parts", value: "8" },
            { label: "AI Models", value: "6+" },
            { label: "Forecast Horizon", value: "12wk" },
            { label: "Training Records", value: "4.7K" },
          ].map(s => (
            <div key={s.label} style={{ background: P_DEEP, padding: "40px" }}>
              <div style={{ fontSize: "2.5rem", fontWeight: 900, color: P_BRAND, marginBottom: 4 }}>{s.value}</div>
              <div style={{ fontSize: "12px", color: "rgba(230, 241, 248, 0.5)", fontWeight: 800, textTransform: "uppercase", letterSpacing: "0.1em" }}>{s.label}</div>
            </div>
          ))}
        </div>
      </header>

      {/* The Problem Section */}
      <section 
        ref={problemRef}
        style={{
          padding: "120px 20px", background: P_SURFACE, color: P_NAVY,
          position: "relative", zIndex: 1
        }}
      >
        <div style={{ maxWidth: 1200, margin: "0 auto" }}>
          <div style={{ marginBottom: "80px" }}>
            <SectionTag label="The Problem" color={P_ACCENT} />
            <h2 style={{ fontSize: "3rem", fontWeight: 900, letterSpacing: "-0.04em", marginBottom: "20px" }}>
              Why traditional planning fails
            </h2>
            <p style={{ fontSize: "1.25rem", color: "rgba(21, 47, 97, 0.6)", maxWidth: 700, fontWeight: 500 }}>
              Industrial spare part demand is volatile, seasonal, and critical — yet most teams still rely on gut instinct.
            </p>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1.5rem" }}>
            {[
              { icon: AlertTriangle, title: "Reactive Procurement", desc: "Parts ordered only after stockouts — halting production lines and inflating emergency costs." },
              { icon: TrendingUp, title: "Manual Forecasting", desc: "Demand estimated by experience alone, ignoring seasonal patterns and historical signals." },
              { icon: Database, title: "Excess Inventory", desc: "Overstocking of low-demand parts ties up capital and warehouse capacity." },
              { icon: Cpu, title: "No Model Benchmarking", desc: "No systematic way to compare AR, SARIMA, Prophet, XGBoost — leaving accuracy on the table." },
            ].map(item => (
              <div key={item.title} style={{
                padding: "48px", background: "#fff", borderRadius: "32px",
                border: "1px solid rgba(21, 47, 97, 0.05)"
              }}>
                <div style={{ color: P_ACCENT, marginBottom: "24px" }}><item.icon size={32} /></div>
                <h3 style={{ fontSize: "1.5rem", fontWeight: 800, marginBottom: "12px" }}>{item.title}</h3>
                <p style={{ color: "rgba(21, 47, 97, 0.6)", lineHeight: 1.6, fontWeight: 500 }}>{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Our Solution Section */}
      <section style={{
        padding: "120px 20px", background: "#fff", color: P_NAVY,
        position: "relative", zIndex: 1
      }}>
        <div style={{ maxWidth: 1200, margin: "0 auto" }}>
          <div style={{ marginBottom: "80px" }}>
            <SectionTag label="Our Solution" color={P_BRAND} />
            <h2 style={{ fontSize: "3rem", fontWeight: 900, letterSpacing: "-0.04em", marginBottom: "20px" }}>
              How this platform solves this
            </h2>
            <p style={{ fontSize: "1.25rem", color: "rgba(21, 47, 97, 0.6)", maxWidth: 700, fontWeight: 500 }}>
              A full-stack AI pipeline — from raw despatch records to weekly forecasts — deployed and live.
            </p>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "1.5rem" }}>
            {[
              { icon: Cpu, title: "AI Model Competition", desc: "6+ models auto-scored per item — champion selected by lowest RMSE." },
              { icon: LineChart, title: "12-Week Forecasts", desc: "Weekly demand predictions per part with confidence intervals." },
              { icon: PieChart, title: "MSTL Decomposition", desc: "Trend, seasonal, and residual signals separated for deep insight." },
              { icon: Layout, title: "Live API + Dashboard", desc: "FastAPI backend + React dashboard — always up-to-date analytics." },
              { icon: Database, title: "8 Priority Items", desc: "ACR SPARES range tracked at weekly granularity from 2021–2024." },
              { icon: BarChart2, title: "Portfolio KPIs", desc: "Revenue, QTY, and order analytics aggregated across all items." },
            ].map(item => (
              <div key={item.title} style={{
                padding: "32px", background: P_LIGHT, borderRadius: "24px",
                border: `1px solid ${P_BRAND}10`,
                display: "flex", flexDirection: "column", gap: 16
              }} className="grid-card">
                <div style={{
                  width: 48, height: 48, background: P_BRAND, borderRadius: 12,
                  display: "flex", alignItems: "center", justifyContent: "center", color: "#fff"
                }}>
                  <item.icon size={24} />
                </div>
                <div>
                  <h3 style={{ fontSize: "1.25rem", fontWeight: 800, marginBottom: "8px" }}>{item.title}</h3>
                  <p style={{ color: "rgba(21, 47, 97, 0.6)", fontSize: "0.95rem", lineHeight: 1.5, fontWeight: 500 }}>{item.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Footer Section */}
      <footer style={{
        padding: "100px 20px", background: P_NAVY, textAlign: "center",
        borderTop: `1px solid rgba(255,255,255,0.05)`
      }}>
        <div style={{ maxWidth: 700, margin: "0 auto", marginBottom: "48px" }}>
          <h2 style={{ fontSize: "2.5rem", fontWeight: 900, marginBottom: "20px", letterSpacing: "-0.02em" }}>Ready to see your demand forecasts?</h2>
          <p style={{ color: "rgba(230, 241, 248, 0.6)", fontSize: "1.1rem", lineHeight: 1.6 }}>
            Log in to access live 12-week forecasts, model comparisons, and MSTL decomposition for all 8 ACR SPARES items.
          </p>
        </div>
        
        <button
          onClick={onEnter}
          style={{
            padding: "20px 60px", background: "#fff", color: P_NAVY,
            borderRadius: "50px", border: "none", fontSize: "1.1rem",
            fontWeight: 800, cursor: "pointer", transition: "all 0.2s"
          }}
          className="btn-hover"
        >
          Get Started
        </button>

        <div style={{ marginTop: "100px", color: "rgba(230, 241, 248, 0.4)", fontSize: "14px", fontWeight: 600 }}>
          © 2024 Spare Part Demand Forecasting Platform · ACR SPARES Forecasting
        </div>
      </footer>
    </div>
  );
}

function SectionTag({ label, color }) {
  return (
    <div style={{
      display: "inline-flex", alignItems: "center",
      padding: "6px 14px", background: `${color}15`, borderRadius: "50px",
      border: `1px solid ${color}30`, marginBottom: "20px"
    }}>
      <span style={{ fontSize: "12px", fontWeight: 900, color, textTransform: "uppercase", letterSpacing: "0.15em" }}>
        {label}
      </span>
    </div>
  );
}
