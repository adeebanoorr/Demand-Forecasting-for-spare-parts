import { useState, useEffect, useRef } from "react";
import {
  BarChart2,
  Cpu,
  AlertTriangle,
  TrendingUp,
  Package,
  Clock,
  ChevronRight,
  ArrowRight,
  Activity,
  Layers,
  Database,
  Zap,
} from "lucide-react";

const PROBLEMS = [
  {
    icon: AlertTriangle,
    title: "Reactive Procurement",
    desc: "Parts ordered only after stockouts — halting production lines and inflating emergency costs.",
  },
  {
    icon: Clock,
    title: "Manual Forecasting",
    desc: "Demand estimated by experience alone, ignoring seasonal patterns and historical signals.",
  },
  {
    icon: Package,
    title: "Excess Inventory",
    desc: "Overstocking of low-demand parts ties up capital and warehouse capacity.",
  },
  {
    icon: BarChart2,
    title: "No Model Benchmarking",
    desc: "No systematic way to compare AR, SARIMA, Prophet, XGBoost — leaving accuracy on the table.",
  },
];

const SOLUTIONS = [
  {
    icon: Cpu,
    label: "AI Model Competition",
    desc: "6+ models auto-scored per item — champion selected by lowest RMSE.",
    accent: "#22d3ee",
  },
  {
    icon: TrendingUp,
    label: "12-Week Forecasts",
    desc: "Weekly demand predictions per part with confidence intervals.",
    accent: "#34d399",
  },
  {
    icon: Activity,
    label: "MSTL Decomposition",
    desc: "Trend, seasonal, and residual signals separated for deep insight.",
    accent: "#818cf8",
  },
  {
    icon: Database,
    label: "Live API + Dashboard",
    desc: "FastAPI backend + React dashboard — always up-to-date analytics.",
    accent: "#fb923c",
  },
  {
    icon: Layers,
    label: "8 Priority Items",
    desc: "ACR SPARES range tracked at weekly granularity from 2021–2024.",
    accent: "#f472b6",
  },
  {
    icon: Zap,
    label: "Portfolio KPIs",
    desc: "Revenue, QTY, and order analytics aggregated across all items.",
    accent: "#facc15",
  },
];

const STATS = [
  { value: "8", label: "Tracked Parts" },
  { value: "6+", label: "AI Models" },
  { value: "12wk", label: "Forecast Horizon" },
  { value: "4.7K", label: "Training Records" },
];

// Animated counter hook
function useCounter(target, duration = 1200, start = false) {
  const [count, setCount] = useState(0);
  useEffect(() => {
    if (!start) return;
    const isFloat = String(target).includes(".");
    const num = parseFloat(target);
    if (isNaN(num)) { setCount(target); return; }
    let startTime = null;
    const step = (timestamp) => {
      if (!startTime) startTime = timestamp;
      const progress = Math.min((timestamp - startTime) / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      setCount(isFloat ? (eased * num).toFixed(1) : Math.floor(eased * num));
      if (progress < 1) requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
  }, [start, target, duration]);
  return count;
}

export default function LandingPage({ onLogin }) {
  const problemRef = useRef(null);
  const [visible, setVisible] = useState(false);
  const [statsVisible, setStatsVisible] = useState(false);

  useEffect(() => {
    const t1 = setTimeout(() => setVisible(true), 100);
    const t2 = setTimeout(() => setStatsVisible(true), 800);
    return () => { clearTimeout(t1); clearTimeout(t2); };
  }, []);

  return (
    <div
      style={{
        minHeight: "100vh",
        background: "linear-gradient(135deg, #0a1628 0%, #003a61 100%)",
        fontFamily: "'DM Sans', 'Segoe UI', sans-serif",
        color: "#e2e8f0",
        overflowX: "hidden",
      }}
    >
      {/* Mesh background */}
      <div style={{ position: "fixed", inset: 0, zIndex: 0, pointerEvents: "none" }}>
        <div style={{
          position: "absolute", top: "-20%", right: "-10%",
          width: "600px", height: "600px",
          background: "radial-gradient(circle, rgba(0,117,190,0.06) 0%, transparent 70%)",
          borderRadius: "50%",
        }} />
        <div style={{
          position: "absolute", bottom: "10%", left: "-10%",
          width: "500px", height: "500px",
          background: "radial-gradient(circle, rgba(99,102,241,0.05) 0%, transparent 70%)",
          borderRadius: "50%",
        }} />
        {/* Grid lines */}
        <svg width="100%" height="100%" style={{ opacity: 0.03 }}>
          <defs>
            <pattern id="grid" width="60" height="60" patternUnits="userSpaceOnUse">
              <path d="M 60 0 L 0 0 0 60" fill="none" stroke="#0075BE" strokeWidth="0.5" />
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="url(#grid)" />
        </svg>
      </div>

      {/* NAV */}
      <nav style={{
        position: "sticky", top: 0, zIndex: 100,
        background: "rgba(10,15,30,0.85)",
        backdropFilter: "blur(16px)",
        borderBottom: "1px solid rgba(34,211,238,0.1)",
        padding: "0 2rem",
        display: "flex", alignItems: "center", justifyContent: "space-between",
        height: "64px",
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <div style={{
            width: 32, height: 32,
            background: "linear-gradient(135deg, #0075BE, #234FA2)",
            borderRadius: 8,
            display: "flex", alignItems: "center", justifyContent: "center",
          }}>
            <BarChart2 size={18} color="#fff" />
          </div>
          <span style={{ fontWeight: 700, fontSize: "1rem", letterSpacing: "0.02em" }}>
            KPCL <span style={{ color: "#0075BE" }}>Analytics</span>
          </span>
        </div>
        <div style={{ display: "flex", gap: "1rem", alignItems: "center" }}>
          <button
            onClick={onLogin}
            style={{
              background: "transparent",
              border: "1px solid rgba(0,117,190,0.3)",
              color: "#0075BE",
              borderRadius: 8, padding: "8px 20px",
              cursor: "pointer", fontSize: "0.875rem", fontWeight: 500,
              transition: "all 0.2s",
            }}
            onMouseOver={e => { e.target.style.background = "rgba(34,211,238,0.08)"; }}
            onMouseOut={e => { e.target.style.background = "transparent"; }}
          >
            Login
          </button>
        </div>
      </nav>

      <div style={{ position: "relative", zIndex: 1 }}>

        {/* HERO */}
        <section style={{
          maxWidth: 1100, margin: "0 auto",
          padding: "100px 2rem 80px",
          textAlign: "center",
          opacity: visible ? 1 : 0,
          transform: visible ? "translateY(0)" : "translateY(24px)",
          transition: "all 0.8s cubic-bezier(0.16, 1, 0.3, 1)",
        }}>
          <div style={{
            display: "inline-flex", alignItems: "center", gap: 8,
            background: "rgba(0,117,190,0.08)",
            border: "1px solid rgba(0,117,190,0.2)",
            borderRadius: 100, padding: "6px 16px",
            fontSize: "0.8rem", color: "#0075BE", letterSpacing: "0.06em",
            textTransform: "uppercase", fontWeight: 600, marginBottom: "2rem",
          }}>
            <span style={{ width: 6, height: 6, borderRadius: "50%", background: "#22d3ee", display: "inline-block" }} />
            AI-Powered Spare Parts Intelligence
          </div>

          <h1 style={{
            fontSize: "clamp(2.4rem, 5vw, 4rem)",
            fontWeight: 800,
            lineHeight: 1.1,
            marginBottom: "1.5rem",
            letterSpacing: "-0.02em",
          }}>
            Stop Guessing.{" "}
            <span style={{
              background: "linear-gradient(90deg, #0075BE, #234FA2)",
              WebkitBackgroundClip: "text",
              WebkitTextFillColor: "transparent",
            }}>
              Start Forecasting.
            </span>
          </h1>

          <p style={{
            fontSize: "1.15rem", color: "#94a3b8",
            maxWidth: 640, margin: "0 auto 3rem",
            lineHeight: 1.7,
          }}>
            Kirloskar Pneumatic's AI platform predicts weekly spare part demand for ACR SPARES —
            reducing stockouts, cutting excess inventory, and benchmarking 6+ ML models automatically.
          </p>

          <div style={{ display: "flex", gap: "1rem", justifyContent: "center", flexWrap: "wrap" }}>
            <button
              onClick={() => problemRef.current?.scrollIntoView({ behavior: 'smooth' })}
              style={{
                background: "linear-gradient(135deg, #0075BE, #234FA2)",
                border: "none", color: "#fff",
                borderRadius: 12, padding: "14px 32px",
                cursor: "pointer", fontSize: "1rem", fontWeight: 600,
                display: "flex", alignItems: "center", gap: 8,
                boxShadow: "0 0 40px rgba(0,117,190,0.25)",
                transition: "all 0.2s",
              }}
              onMouseOver={e => { e.currentTarget.style.transform = "scale(1.03)"; e.currentTarget.style.boxShadow = "0 0 60px rgba(34,211,238,0.4)"; }}
              onMouseOut={e => { e.currentTarget.style.transform = "scale(1)"; e.currentTarget.style.boxShadow = "0 0 40px rgba(34,211,238,0.25)"; }}
            >
              Explore Platform <ArrowRight size={18} />
            </button>
            <button
              onClick={onLogin}
              style={{
                background: "rgba(255,255,255,0.04)",
                border: "1px solid rgba(255,255,255,0.12)",
                color: "#e2e8f0",
                borderRadius: 12, padding: "14px 32px",
                cursor: "pointer", fontSize: "1rem", fontWeight: 500,
                transition: "all 0.2s",
              }}
              onMouseOver={e => { e.currentTarget.style.background = "rgba(255,255,255,0.08)"; }}
              onMouseOut={e => { e.currentTarget.style.background = "rgba(255,255,255,0.04)"; }}
            >
              Login →
            </button>
          </div>
        </section>

        {/* STATS BAR */}
        <section style={{
          maxWidth: 900, margin: "0 auto 80px",
          padding: "0 2rem",
          opacity: statsVisible ? 1 : 0,
          transition: "opacity 0.8s",
        }}>
          <div style={{
            display: "grid", gridTemplateColumns: "repeat(4, 1fr)",
            gap: "1px",
            background: "rgba(34,211,238,0.1)",
            border: "1px solid rgba(34,211,238,0.1)",
            borderRadius: 16, overflow: "hidden",
          }}>
            {STATS.map(({ value, label }) => (
              <div key={label} style={{
                background: "rgba(13,27,42,0.8)",
                padding: "28px 20px",
                textAlign: "center",
                backdropFilter: "blur(10px)",
              }}>
                <div style={{
                  fontSize: "2.2rem", fontWeight: 800,
                  background: "linear-gradient(135deg, #0075BE, #234FA2)",
                  WebkitBackgroundClip: "text",
                  WebkitTextFillColor: "transparent",
                  lineHeight: 1,
                }}>
                  {value}
                </div>
                <div style={{ color: "#64748b", fontSize: "0.8rem", marginTop: 6, fontWeight: 500, letterSpacing: "0.04em", textTransform: "uppercase" }}>
                  {label}
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* PROBLEM SECTION */}
        <section ref={problemRef} style={{ maxWidth: 1100, margin: "0 auto 100px", padding: "0 2rem" }}>
          <div style={{ textAlign: "center", marginBottom: "3rem" }}>
            <div style={{
              display: "inline-block",
              background: "rgba(251,146,60,0.1)",
              border: "1px solid rgba(251,146,60,0.2)",
              color: "#fb923c",
              borderRadius: 100, padding: "4px 14px",
              fontSize: "0.75rem", fontWeight: 600, letterSpacing: "0.07em",
              textTransform: "uppercase", marginBottom: "1rem",
            }}>
              The Problem
            </div>
            <h2 style={{ fontSize: "2rem", fontWeight: 700, marginBottom: "0.5rem" }}>
              Why traditional planning fails
            </h2>
            <p style={{ color: "#64748b", fontSize: "1rem" }}>
              Industrial spare part demand is volatile, seasonal, and critical — yet most teams still rely on gut instinct.
            </p>
          </div>

          <div style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))",
            gap: "1rem",
          }}>
            {PROBLEMS.map(({ icon: Icon, title, desc }) => (
              <div key={title} style={{
                background: "rgba(251,146,60,0.04)",
                border: "1px solid rgba(251,146,60,0.12)",
                borderRadius: 16, padding: "24px",
                transition: "all 0.25s",
                cursor: "default",
              }}
                onMouseOver={e => { e.currentTarget.style.background = "rgba(251,146,60,0.08)"; e.currentTarget.style.borderColor = "rgba(251,146,60,0.25)"; e.currentTarget.style.transform = "translateY(-3px)"; }}
                onMouseOut={e => { e.currentTarget.style.background = "rgba(251,146,60,0.04)"; e.currentTarget.style.borderColor = "rgba(251,146,60,0.12)"; e.currentTarget.style.transform = "translateY(0)"; }}
              >
                <div style={{
                  width: 40, height: 40, borderRadius: 10,
                  background: "rgba(251,146,60,0.12)",
                  display: "flex", alignItems: "center", justifyContent: "center",
                  marginBottom: 14,
                }}>
                  <Icon size={20} color="#fb923c" />
                </div>
                <h3 style={{ fontWeight: 600, fontSize: "1rem", marginBottom: 6 }}>{title}</h3>
                <p style={{ color: "#64748b", fontSize: "0.875rem", lineHeight: 1.6 }}>{desc}</p>
              </div>
            ))}
          </div>
        </section>

        {/* SOLUTION SECTION */}
        <section style={{
          maxWidth: 1100, margin: "0 auto 100px", padding: "0 2rem",
        }}>
          <div style={{ textAlign: "center", marginBottom: "3rem" }}>
            <div style={{
              display: "inline-block",
              background: "rgba(34,211,238,0.08)",
              border: "1px solid rgba(34,211,238,0.2)",
              color: "#22d3ee",
              borderRadius: 100, padding: "4px 14px",
              fontSize: "0.75rem", fontWeight: 600, letterSpacing: "0.07em",
              textTransform: "uppercase", marginBottom: "1rem",
            }}>
              Our Solution
            </div>
            <h2 style={{ fontSize: "2rem", fontWeight: 700, marginBottom: "0.5rem" }}>
              How KPCL Analytics solves this
            </h2>
            <p style={{ color: "#64748b", fontSize: "1rem" }}>
              A full-stack AI pipeline — from raw despatch records to weekly forecasts — deployed and live.
            </p>
          </div>

          <div style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))",
            gap: "1rem",
          }}>
            {SOLUTIONS.map(({ icon: Icon, label, desc, accent }) => (
              <div key={label} style={{
                background: "rgba(13,27,42,0.6)",
                border: "1px solid rgba(255,255,255,0.06)",
                borderRadius: 16, padding: "24px",
                display: "flex", gap: 16, alignItems: "flex-start",
                transition: "all 0.25s",
              }}
                onMouseOver={e => {
                  e.currentTarget.style.borderColor = `${accent}40`;
                  e.currentTarget.style.background = "rgba(13,27,42,0.9)";
                  e.currentTarget.style.transform = "translateY(-2px)";
                }}
                onMouseOut={e => {
                  e.currentTarget.style.borderColor = "rgba(255,255,255,0.06)";
                  e.currentTarget.style.background = "rgba(13,27,42,0.6)";
                  e.currentTarget.style.transform = "translateY(0)";
                }}
              >
                <div style={{
                  width: 42, height: 42, borderRadius: 10, flexShrink: 0,
                  background: `${accent}18`,
                  border: `1px solid ${accent}30`,
                  display: "flex", alignItems: "center", justifyContent: "center",
                }}>
                  <Icon size={20} color={accent} />
                </div>
                <div>
                  <h3 style={{ fontWeight: 600, fontSize: "0.975rem", marginBottom: 4 }}>{label}</h3>
                  <p style={{ color: "#64748b", fontSize: "0.85rem", lineHeight: 1.6 }}>{desc}</p>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* CTA BANNER */}
        <section style={{ maxWidth: 1100, margin: "0 auto 80px", padding: "0 2rem" }}>
          <div style={{
            background: "linear-gradient(135deg, rgba(34,211,238,0.08) 0%, rgba(99,102,241,0.08) 100%)",
            border: "1px solid rgba(34,211,238,0.15)",
            borderRadius: 24, padding: "60px 40px",
            textAlign: "center",
            position: "relative", overflow: "hidden",
          }}>
            <div style={{
              position: "absolute", top: -80, right: -80,
              width: 300, height: 300,
              background: "radial-gradient(circle, rgba(34,211,238,0.1) 0%, transparent 60%)",
              borderRadius: "50%",
            }} />
            <h2 style={{ fontSize: "1.75rem", fontWeight: 700, marginBottom: "1rem" }}>
              Ready to see your demand forecasts?
            </h2>
            <p style={{ color: "#94a3b8", marginBottom: "2rem", fontSize: "1rem" }}>
              Log in to access live 12-week forecasts, model comparisons, and MSTL decomposition for all 8 ACR SPARES items.
            </p>
            <div style={{ display: "flex", gap: "1rem", justifyContent: "center", flexWrap: "wrap" }}>
              <button
                onClick={onLogin}
                style={{
                  background: "linear-gradient(135deg, #0075BE, #234FA2)",
                  border: "none", color: "#fff",
                  borderRadius: 12, padding: "14px 36px",
                  cursor: "pointer", fontSize: "1rem", fontWeight: 600,
                  display: "flex", alignItems: "center", gap: 8,
                  boxShadow: "0 0 40px rgba(0,117,190,0.2)",
                  transition: "all 0.2s",
                }}
                onMouseOver={e => { e.currentTarget.style.transform = "scale(1.03)"; }}
                onMouseOut={e => { e.currentTarget.style.transform = "scale(1)"; }}
              >
                Get Started <ChevronRight size={18} />
              </button>
            </div>
          </div>
        </section>

        {/* FOOTER */}
        <footer style={{
          borderTop: "1px solid rgba(255,255,255,0.06)",
          padding: "2rem",
          textAlign: "center",
          color: "#475569",
          fontSize: "0.8rem",
        }}>
          © 2024 Kirloskar Pneumatic Co. Ltd. · KPCL Analytics Platform · ACR SPARES Forecasting
        </footer>
      </div>
    </div>
  );
}
