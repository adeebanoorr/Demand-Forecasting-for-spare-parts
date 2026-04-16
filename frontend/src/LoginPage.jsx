import { useState, useEffect } from "react";
import { BarChart2, Lock, User, Eye, EyeOff, ArrowRight, AlertCircle, ShieldCheck } from "lucide-react";

// Updated demo credentials
const ADMIN_USER = "admin";
const ADMIN_PASS = "admin2024";

export default function LoginPage({ onLogin, onBack }) {
  const [form, setForm] = useState({ username: "", password: "" });
  const [showPass, setShowPass] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [mounted, setMounted] = useState(false);

  // Palette constants
  const P_NAVY = "#152F61";
  const P_DEEP = "#1C3F82";
  const P_PRIMARY = "#234FA2";
  const P_BRAND = "#0075BE";
  const P_LIGHT = "#E6F1F8";
  const P_ACCENT = "#E07C3A";
  const P_SURFACE = "#FEF3EB";

  useEffect(() => {
    setMounted(true);
  }, []);

  const handleSubmit = (e) => {
    e?.preventDefault?.();
    setError("");

    if (!form.username || !form.password) {
      setError("Authorization credentials required.");
      return;
    }

    setLoading(true);
    setTimeout(() => {
      if (form.username === ADMIN_USER && form.password === ADMIN_PASS) {
        setLoading(false);
        onLogin?.();
      } else {
        setLoading(false);
        setError("Access Denied. Check your credentials.");
      }
    }, 800);
  };

  return (
    <div style={{
      minHeight: "100vh",
      background: P_NAVY,
      display: "flex",
      fontFamily: "'Inter', sans-serif",
      color: P_LIGHT,
      overflow: "hidden",
      position: "relative",
    }}>
      {/* Background blobs */}
      <div style={{ position: "fixed", inset: 0, pointerEvents: "none", zIndex: 0 }}>
        <div style={{
          position: "absolute", top: "20%", right: "10%",
          width: "600px", height: "600px",
          background: `radial-gradient(circle, ${P_BRAND}15 0%, transparent 70%)`,
        }} />
        <div style={{
          position: "absolute", bottom: "10%", left: "5%",
          width: "500px", height: "500px",
          background: `radial-gradient(circle, ${P_ACCENT}10 0%, transparent 70%)`,
        }} />
      </div>

      <div style={{
        flex: 1,
        display: "flex",
        maxWidth: 1440,
        margin: "0 auto",
        zIndex: 1,
        opacity: mounted ? 1 : 0,
        transition: "opacity 1s ease",
      }}>
        {/* Left: Brand Visuals */}
        <div style={{
          flex: 1.2,
          padding: "60px 80px",
          display: "flex",
          flexDirection: "column",
          justifyContent: "space-between",
        }}>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: "100px" }}>
               <div style={{
                width: 40, height: 40,
                background: P_BRAND,
                borderRadius: 10,
                display: "flex", alignItems: "center", justifyContent: "center",
                boxShadow: `0 8px 16px ${P_BRAND}30`
              }}>
                <BarChart2 size={22} color="#fff" />
              </div>
              <span style={{ fontWeight: 800, fontSize: "1.25rem", letterSpacing: "-0.02em" }}>
                Intelligence <span style={{ fontWeight: 400, color: "rgba(230,241,248,0.5)" }}>Portal</span>
              </span>
            </div>

            <h1 style={{
              fontSize: "clamp(2.5rem, 4vw, 3.5rem)",
              fontWeight: 800,
              lineHeight: 1.1,
              marginBottom: "1.5rem",
              letterSpacing: "-0.03em",
              maxWidth: 500,
            }}>
              Enterprise <br />
              <span style={{ color: P_BRAND }}>Forecasting Dashboard.</span>
            </h1>
            <p style={{ color: "rgba(230,241,248,0.6)", fontSize: "1.1rem", lineHeight: 1.6, maxWidth: 440 }}>
              Authorized access to the Demand Sensing engine. 
              Monitor SKUs, Lead Times, and AI Benchmarks.
            </p>
          </div>

          <div style={{ display: "flex", gap: "2rem" }}>
              <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                <ShieldCheck size={18} color={P_BRAND} />
                <span style={{ fontSize: "14px", fontWeight: 700, color: "rgba(230,241,248,0.5)" }}>SECURE SESSION</span>
             </div>
             <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                <ShieldCheck size={18} color={P_BRAND} />
                <span style={{ fontSize: "14px", fontWeight: 700, color: "rgba(230,241,248,0.5)" }}>AUDITED LOGS</span>
             </div>
          </div>
        </div>

        {/* Right: Login Card */}
        <div style={{
          flex: 1,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          padding: "0 40px",
        }}>
          <div style={{
            width: "100%",
            maxWidth: 440,
            background: "rgba(230, 241, 248, 0.03)",
            border: "1px solid rgba(230, 241, 248, 0.08)",
            borderRadius: 32,
            padding: "50px 48px",
            backdropFilter: "blur(40px)",
            boxShadow: "0 40px 100px -20px rgba(0,0,0,0.5)",
          }}>
            <div style={{ textAlign: "center", marginBottom: "40px" }}>
              <h2 style={{ fontSize: "1.75rem", fontWeight: 800, marginBottom: 8 }}>Authorized Node</h2>
              <p style={{ color: "rgba(230,241,248,0.5)", fontSize: "15px" }}>Entry credentials required</p>
            </div>

            <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
              <div>
                <label style={{ display: "block", fontSize: "14px", fontWeight: 800, textTransform: "uppercase", letterSpacing: "0.1em", color: "rgba(230,241,248,0.4)", marginBottom: 10 }}>
                  Account Identifier
                </label>
                <div style={{ position: "relative" }}>
                  <User size={18} color={P_BRAND} style={{ position: "absolute", left: 16, top: "50%", transform: "translateY(-50%)" }} />
                  <input
                    type="text"
                    value={form.username}
                    onChange={e => setForm(f => ({ ...f, username: e.target.value }))}
                    placeholder="Username"
                    style={{
                      width: "100%", padding: "14px 16px 14px 48px",
                      background: "rgba(255, 255, 255, 0.05)",
                      border: "1px solid rgba(255, 255, 255, 0.1)",
                      borderRadius: 12, color: "#fff", fontSize: "14px",
                      outline: "none", transition: "all 0.2s"
                    }}
                  />
                </div>
              </div>

              <div>
                <label style={{ display: "block", fontSize: "12px", fontWeight: 800, textTransform: "uppercase", letterSpacing: "0.1em", color: "rgba(230,241,248,0.4)", marginBottom: 10 }}>
                  Security Key
                </label>
                <div style={{ position: "relative" }}>
                  <Lock size={18} color={P_BRAND} style={{ position: "absolute", left: 16, top: "50%", transform: "translateY(-50%)" }} />
                  <input
                    type={showPass ? "text" : "password"}
                    value={form.password}
                    onChange={e => setForm(f => ({ ...f, password: e.target.value }))}
                    placeholder="••••••••"
                    style={{
                      width: "100%", padding: "14px 48px 14px 48px",
                      background: "rgba(255, 255, 255, 0.05)",
                      border: "1px solid rgba(255, 255, 255, 0.1)",
                      borderRadius: 12, color: "#fff", fontSize: "14px",
                      outline: "none", transition: "all 0.2s"
                    }}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPass(!showPass)}
                    style={{ position: "absolute", right: 12, top: "50%", transform: "translateY(-50%)", background: "none", border: "none", color: "rgba(230,241,248,0.4)", cursor: "pointer" }}
                  >
                    {showPass ? <EyeOff size={18} /> : <Eye size={18} />}
                  </button>
                </div>
              </div>

              {error && (
                <div style={{ display: "flex", gap: 10, alignItems: "center", color: "#EF4444", fontSize: "14px", fontStyle: "italic" }}>
                  <AlertCircle size={16} /> {error}
                </div>
              )}

              <button
                disabled={loading}
                style={{
                  background: P_BRAND,
                  color: "#fff",
                  border: "none",
                  borderRadius: 12, padding: "16px",
                  fontSize: "14px", fontWeight: 800,
                  cursor: loading ? "wait" : "pointer",
                  display: "flex", alignItems: "center", justifyContent: "center", gap: 10,
                  transition: "all 0.2s",
                  marginTop: 8,
                }}
              >
                {loading ? "Authenticating..." : "Sign In"} <ArrowRight size={20} />
              </button>

              <button
                type="button"
                onClick={onBack}
                style={{
                  background: "transparent", border: "none", color: "rgba(230,241,248,0.4)",
                  fontSize: "14px", fontWeight: 600, cursor: "pointer",
                  marginTop: "10px",
                }}
              >
                ← Return to Platform
              </button>
            </form>
          </div>
          
          <div style={{ position: "absolute", bottom: 40, color: "rgba(230,241,248,0.2)", fontSize: "14px", textAlign: "center", width: "100%", maxWidth: 440, fontWeight: 700 }}>
            PRIVATE NODE · v1.2 · ENCRYPTED
          </div>
        </div>
      </div>
    </div>
  );
}
