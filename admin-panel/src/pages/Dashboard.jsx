import React, { useEffect, useState } from "react";
import Layout from "../components/Layout";
import api from "../api/api";

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .get("/admin/dashboard")
      .then(({ data }) => setStats(data))
      .catch((err) => setError(err.message));
  }, []);

  const cards = stats
    ? [
        { label: "Total Doctors", value: stats.total_doctors },
        { label: "Total Patients", value: stats.total_patients },
        { label: "Total Clinics", value: stats.total_clinics },
        { label: "Total Appointments", value: stats.total_appointments },
        { label: "Successful Payments", value: stats.total_payments_success },
        { label: "Total Earnings", value: `₹${stats.total_earnings}` },
        { label: "Pending Doctor Approvals", value: stats.pending_doctor_approvals },
      ]
    : [];

  return (
    <Layout>
      <div className="page-title">Dashboard</div>
      <div className="page-sub">Platform-wide overview</div>

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
