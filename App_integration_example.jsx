/**
 * KPCL Analytics — Updated App.jsx
 * 
 * Adds LandingPage → LoginPage → Dashboard flow using simple state routing.
 * Replace your existing App.jsx content with this, keeping all your existing
 * tab/dashboard logic inside the "dashboard" view.
 * 
 * Credentials: admin / kpcl2024
 */

import { useState } from "react";
import LandingPage from "./LandingPage";
import LoginPage from "./LoginPage";

// ─── Import all your existing dashboard content here ────────────────────────
// (move your current App.jsx JSX into a Dashboard component, or keep it inline)
// import Dashboard from "./Dashboard";

// ─── Temporary placeholder — replace with your actual dashboard JSX ─────────
function Dashboard() {
  return (
    <div style={{ minHeight: "100vh", background: "#0a0f1e", color: "#e2e8f0", display: "flex", alignItems: "center", justifyContent: "center" }}>
      <p style={{ color: "#22d3ee", fontSize: "1.25rem" }}>
        ✅ Your existing dashboard renders here
      </p>
    </div>
  );
}
// ─────────────────────────────────────────────────────────────────────────────

type View = "landing" | "login" | "dashboard";

export default function App() {
  const [view, setView] = useState<View>("landing");

  if (view === "landing") {
    return (
      <LandingPage
        onExplore={() => setView("login")}
      />
    );
  }

  if (view === "login") {
    return (
      <LoginPage
        onLogin={() => setView("dashboard")}
      />
    );
  }

  return <Dashboard />;
}
