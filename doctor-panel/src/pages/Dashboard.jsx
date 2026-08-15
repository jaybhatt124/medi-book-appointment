import React, { useEffect, useState } from "react";
import Layout from "../components/Layout";
import api from "../api/api";

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .get("/doctor/dashboard")
      .then(({ data }) => setStats(data))
      .catch((err) => setError(err.message));
  }, []);

  const cards = stats
    ? [
        { label: "Total Appointments", value: stats.total_appointments },
        { label: "Today's Appointments", value: stats.today_appointments },
        { label: "Upcoming", value: stats.upcoming_appointments },
        { label: "Completed", value: stats.completed_appointments },
        { label: "Pending", value: stats.pending_appointments },
        { label: "Rejected", value: stats.rejected_appointments },
        { label: "Total Earnings", value: `₹${stats.total_earnings}` },
      ]
    : [];

  return (
    <Layout>
      <div className="page-title">Dashboard</div>
      <div className="page-sub">Overview of your appointments and earnings</div>

      {error && <div className="error-banner">{error}</div>}

      <div className="stats-grid">
        {cards.map((c) => (
          <div className="stat-card" key={c.label}>
            <div className="stat-label">{c.label}</div>
            <div className="stat-value">{c.value}</div>
          </div>
        ))}
      </div>
    </Layout>
  );
}
