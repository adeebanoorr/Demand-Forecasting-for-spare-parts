import { useState, useEffect } from "react";
import { BarChart2, Lock, User, Eye, EyeOff, ArrowRight, AlertCircle } from "lucide-react";

// Hardcoded admin credentials
const ADMIN_USER = "admin";
const ADMIN_PASS = "kpcl2024";

export default function LoginPage({ onLogin, onBack }) {
  const [form, setForm] = useState({ username: "", password: "" });
  const [showPass, setShowPass] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    const t = setTimeout(() => setMounted(true), 80);
    return () => clearTimeout(t);
  }, []);

  const handleSubmit = (e) => {
    e?.preventDefault?.();
    setError("");

    if (!form.username || !form.password) {
      setError("Please enter both username and password.");
      return;
    }

    setLoading(true);
    // Simulate brief auth check
    setTimeout(() => {
      if (form.username === ADMIN_USER && form.password === ADMIN_PASS) {
        setLoading(false);
        onLogin?.();
      } else {
        setLoading(false);
        setError("Invalid credentials. Try admin / kpcl2024");
      }
    }, 900);
  };

  return (
    <div style={{
      minHeight: "100vh",
      background: "linear-gradient(135deg, #0a1628 0%, #003a61 100%)",
      display: "flex",
      fontFamily: "'DM Sans', 'Segoe UI', sans-serif",
      color: "#e2e8f0",
      overflow: "hidden",
      position: "relative",
    }}>

      {/* Background effects */}
      <div style={{ position: "fixed", inset: 0, pointerEvents: "none", zIndex: 0 }}>
        <div style={{
          position: "absolute", top: "15%", right: "8%",
          width: "500px", height: "500px",
          background: "radial-gradient(circle, rgba(0,117,190,0.07) 0%, transparent 65%)",
          borderRadius: "50%",
        }} />
        <div style={{
          position: "absolute", bottom: "10%", left: "5%",
          width: "400px", height: "400px",
          background: "radial-gradient(circle, rgba(99,102,241,0.06) 0%, transparent 65%)",
          borderRadius: "50%",
        }} />
        <svg width="100%" height="100%" style={{ opacity: 0.025, position: "absolute", inset: 0 }}>
          <defs>
            <pattern id="lgrid" width="60" height="60" patternUnits="userSpaceOnUse">
              <path d="M 60 0 L 0 0 0 60" fill="none" stroke="#0075BE" strokeWidth="0.5" />
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="url(#lgrid)" />
        </svg>
      </div>

      {/* LEFT PANEL — Branding */}
      <div style={{
        flex: 1,
        display: "flex", flexDirection: "column",
        justifyContent: "center", alignItems: "flex-start",
        padding: "4rem 5rem",
        position: "relative", zIndex: 1,
        opacity: mounted ? 1 : 0,
        transform: mounted ? "translateX(0)" : "translateX(-20px)",
        transition: "all 0.7s cubic-bezier(0.16, 1, 0.3, 1)",
      }}>
        {/* Logo */}
        <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: "4rem" }}>
          <div style={{
            width: 44, height: 44,
            background: "linear-gradient(135deg, #0075BE, #234FA2)",
            borderRadius: 12,
            display: "flex", alignItems: "center", justifyContent: "center",
            boxShadow: "0 0 30px rgba(34,211,238,0.3)",
          }}>
            <BarChart2 size={22} color="#fff" />
          </div>
          <div>
            <div style={{ fontWeight: 700, fontSize: "1.1rem", letterSpacing: "0.01em" }}>
              KPCL <span style={{ color: "#0075BE" }}>Analytics</span>
            </div>
            <div style={{ fontSize: "0.72rem", color: "#475569", letterSpacing: "0.08em", textTransform: "uppercase" }}>
              Spare Parts Intelligence
            </div>
          </div>
        </div>

        <h1 style={{
          fontSize: "clamp(2rem, 3.5vw, 3rem)",
          fontWeight: 800,
          lineHeight: 1.1,
          marginBottom: "1.25rem",
          letterSpacing: "-0.02em",
          maxWidth: 460,
        }}>
          AI-Driven Demand{" "}
          <span style={{
            background: "linear-gradient(90deg, #0075BE, #234FA2)",
            WebkitBackgroundClip: "text",
            WebkitTextFillColor: "transparent",
          }}>
            Forecasting
          </span>
          {" "}for ACR SPARES
        </h1>

        <p style={{ color: "#64748b", fontSize: "1rem", lineHeight: 1.7, maxWidth: 420, marginBottom: "3rem" }}>
          Access real-time 12-week demand forecasts, model benchmarks,
          MSTL decomposition, and portfolio-level KPIs for Kirloskar Pneumatic's priority spare parts.
        </p>

        {/* Feature list */}
        <div style={{ display: "flex", flexDirection: "column", gap: "0.875rem" }}>
          {[
            { color: "#0075BE", text: "6+ AI models auto-benchmarked per item" },
            { color: "#34d399", text: "Weekly forecasts with confidence intervals" },
            { color: "#818cf8", text: "MSTL trend & seasonal decomposition" },
          ].map(({ color, text }) => (
            <div key={text} style={{ display: "flex", alignItems: "center", gap: 10 }}>
              <div style={{
                width: 8, height: 8, borderRadius: "50%",
                background: color,
                boxShadow: `0 0 8px ${color}80`,
                flexShrink: 0,
              }} />
              <span style={{ color: "#94a3b8", fontSize: "0.9rem" }}>{text}</span>
            </div>
          ))}
        </div>

        {/* Bottom quote */}
        <div style={{
          marginTop: "auto", paddingTop: "4rem",
          borderTop: "1px solid rgba(255,255,255,0.06)",
          maxWidth: 420,
        }}>
          <p style={{ color: "#334155", fontSize: "0.8rem", fontStyle: "italic", lineHeight: 1.6 }}>
            "Trained on 4,769 weekly despatch records · Tested on 12 hold-out weeks ·
            Champion model selected by lowest RMSE per item."
          </p>
        </div>
      </div>

      {/* RIGHT PANEL — Login Form */}
      <div style={{
        width: "480px",
        display: "flex", alignItems: "center", justifyContent: "center",
        padding: "2rem",
        position: "relative", zIndex: 1,
        opacity: mounted ? 1 : 0,
        transform: mounted ? "translateX(0)" : "translateX(20px)",
        transition: "all 0.7s cubic-bezier(0.16, 1, 0.3, 1) 0.1s",
      }}>
        <div style={{
          width: "100%", maxWidth: 400,
          background: "rgba(13,21,36,0.8)",
          backdropFilter: "blur(20px)",
          border: "1px solid rgba(255,255,255,0.08)",
          borderRadius: 24,
          padding: "40px 36px",
          boxShadow: "0 40px 80px rgba(0,0,0,0.4), 0 0 1px rgba(34,211,238,0.1)",
        }}>
          {/* Card header */}
          <div style={{ textAlign: "center", marginBottom: "2rem" }}>
            <div style={{
              width: 52, height: 52,
              background: "linear-gradient(135deg, rgba(34,211,238,0.15), rgba(99,102,241,0.15))",
              border: "1px solid rgba(34,211,238,0.2)",
              borderRadius: 14,
              display: "flex", alignItems: "center", justifyContent: "center",
              margin: "0 auto 1rem",
            }}>
              <Lock size={22} color="#0075BE" />
            </div>
            <h2 style={{ fontWeight: 700, fontSize: "1.3rem", marginBottom: 4 }}>Welcome back</h2>
            <p style={{ color: "#475569", fontSize: "0.875rem" }}>Sign in to your admin account</p>
          </div>

          <div style={{ marginBottom: '1.5rem' }}>
            <button
              onClick={onBack}
              style={{
                background: "transparent",
                border: "1px solid rgba(255,255,255,0.1)",
                color: "#64748b",
                borderRadius: 8, padding: "6px 12px",
                cursor: "pointer", fontSize: "0.75rem", fontWeight: 500,
                transition: "all 0.2s",
                display: "flex", alignItems: "center", gap: 6, margin: "0 auto"
              }}
              onMouseOver={e => { e.target.style.background = "rgba(255,255,255,0.05)"; e.target.style.color = "#e2e8f0"; }}
              onMouseOut={e => { e.target.style.background = "transparent"; e.target.style.color = "#64748b"; }}
            >
               ← Back to Home
            </button>
          </div>

          {/* Error message */}
          {error && (
            <div style={{
              background: "rgba(239,68,68,0.08)",
              border: "1px solid rgba(239,68,68,0.2)",
              borderRadius: 10, padding: "10px 14px",
              display: "flex", alignItems: "center", gap: 8,
              marginBottom: "1.25rem",
              animation: "fadeIn 0.3s ease",
            }}>
              <AlertCircle size={15} color="#ef4444" style={{ flexShrink: 0 }} />
              <span style={{ color: "#fca5a5", fontSize: "0.83rem" }}>{error}</span>
            </div>
          )}

          {/* Form */}
          <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>

            {/* Username */}
            <div>
              <label style={{ display: "block", fontSize: "0.8rem", fontWeight: 500, color: "#94a3b8", marginBottom: 6, letterSpacing: "0.03em" }}>
                USERNAME
              </label>
              <div style={{ position: "relative" }}>
                <User size={16} color="#475569" style={{
                  position: "absolute", left: 14, top: "50%", transform: "translateY(-50%)", pointerEvents: "none",
                }} />
                <input
                  type="text"
                  value={form.username}
                  onChange={e => setForm(f => ({ ...f, username: e.target.value }))}
                  onKeyDown={e => e.key === "Enter" && handleSubmit()}
                  placeholder="admin"
                  style={{
                    width: "100%", boxSizing: "border-box",
                    background: "rgba(255,255,255,0.04)",
                    border: "1px solid rgba(255,255,255,0.1)",
                    borderRadius: 10, padding: "12px 14px 12px 40px",
                    color: "#e2e8f0", fontSize: "0.9rem",
                    outline: "none",
                    transition: "border-color 0.2s",
                  }}
                  onFocus={e => { e.target.style.borderColor = "rgba(34,211,238,0.4)"; e.target.style.background = "rgba(34,211,238,0.04)"; }}
                  onBlur={e => { e.target.style.borderColor = "rgba(255,255,255,0.1)"; e.target.style.background = "rgba(255,255,255,0.04)"; }}
                />
              </div>
            </div>

            {/* Password */}
            <div>
              <label style={{ display: "block", fontSize: "0.8rem", fontWeight: 500, color: "#94a3b8", marginBottom: 6, letterSpacing: "0.03em" }}>
                PASSWORD
              </label>
              <div style={{ position: "relative" }}>
                <Lock size={16} color="#475569" style={{
                  position: "absolute", left: 14, top: "50%", transform: "translateY(-50%)", pointerEvents: "none",
                }} />
                <input
                  type={showPass ? "text" : "password"}
                  value={form.password}
                  onChange={e => setForm(f => ({ ...f, password: e.target.value }))}
                  onKeyDown={e => e.key === "Enter" && handleSubmit()}
                  placeholder="••••••••"
                  style={{
                    width: "100%", boxSizing: "border-box",
                    background: "rgba(255,255,255,0.04)",
                    border: "1px solid rgba(255,255,255,0.1)",
                    borderRadius: 10, padding: "12px 44px 12px 40px",
                    color: "#e2e8f0", fontSize: "0.9rem",
                    outline: "none",
                    transition: "border-color 0.2s",
                  }}
                  onFocus={e => { e.target.style.borderColor = "rgba(34,211,238,0.4)"; e.target.style.background = "rgba(34,211,238,0.04)"; }}
                  onBlur={e => { e.target.style.borderColor = "rgba(255,255,255,0.1)"; e.target.style.background = "rgba(255,255,255,0.04)"; }}
                />
                <button
                  onClick={() => setShowPass(s => !s)}
                  style={{
                    position: "absolute", right: 12, top: "50%", transform: "translateY(-50%)",
                    background: "none", border: "none", cursor: "pointer", padding: 4, color: "#475569",
                    display: "flex", alignItems: "center",
                  }}
                >
                  {showPass ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>

            {/* Hint */}
            <div style={{
              background: "rgba(34,211,238,0.05)",
              border: "1px solid rgba(34,211,238,0.1)",
              borderRadius: 8, padding: "8px 12px",
            }}>
              <p style={{ color: "#475569", fontSize: "0.78rem", margin: 0 }}>
                Demo credentials: <span style={{ color: "#0075BE", fontWeight: 600 }}>admin</span> / <span style={{ color: "#0075BE", fontWeight: 600 }}>kpcl2024</span>
              </p>
            </div>

            {/* Submit */}
            <button
              onClick={handleSubmit}
              disabled={loading}
              style={{
                marginTop: 4,
                background: loading
                  ? "rgba(0,117,190,0.3)"
                  : "linear-gradient(135deg, #0075BE, #234FA2)",
                border: "none", color: "#fff",
                borderRadius: 12, padding: "13px",
                cursor: loading ? "not-allowed" : "pointer",
                fontSize: "0.95rem", fontWeight: 600,
                display: "flex", alignItems: "center", justifyContent: "center", gap: 8,
                boxShadow: loading ? "none" : "0 0 30px rgba(34,211,238,0.2)",
                transition: "all 0.2s",
                width: "100%",
              }}
              onMouseOver={e => { if (!loading) { e.currentTarget.style.transform = "scale(1.01)"; e.currentTarget.style.boxShadow = "0 0 50px rgba(34,211,238,0.35)"; } }}
              onMouseOut={e => { e.currentTarget.style.transform = "scale(1)"; e.currentTarget.style.boxShadow = loading ? "none" : "0 0 30px rgba(34,211,238,0.2)"; }}
            >
              {loading ? (
                <>
                  <span style={{
                    width: 16, height: 16, borderRadius: "50%",
                    border: "2px solid rgba(255,255,255,0.3)",
                    borderTopColor: "#fff",
                    animation: "spin 0.7s linear infinite",
                    display: "inline-block",
                  }} />
                  Authenticating…
                </>
              ) : (
                <>Sign In <ArrowRight size={16} /></>
              )}
            </button>
          </div>

          {/* Footer */}
          <p style={{
            textAlign: "center", color: "#334155", fontSize: "0.75rem", marginTop: "1.75rem",
          }}>
            Kirloskar Pneumatic Co. Ltd. · Internal Platform · v1.0
          </p>
        </div>
      </div>

      <style>{`
        @keyframes spin { to { transform: rotate(360deg); } }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(-4px); } to { opacity: 1; transform: translateY(0); } }
        input::placeholder { color: #334155; }
      `}</style>
    </div>
  );
}
