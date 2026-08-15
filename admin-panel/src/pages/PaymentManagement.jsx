import React, { useEffect, useState } from "react";
import Layout from "../components/Layout";
import api from "../api/api";

export default function PaymentManagement() {
  const [payments, setPayments] = useState([]);
  const [error, setError] = useState("");
  const [status, setStatus] = useState("");
  const [date, setDate] = useState("");

  const load = () => {
    const params = {};
    if (status) params.status = status;
    if (date) params.date = date;
    api
      .get("/admin/payments", { params })
      .then(({ data }) => setPayments(data))
      .catch((err) => setError(err.message));
  };

  useEffect(load, [status, date]);

  const totalSuccess = payments
    .filter((p) => p.payment_status === "success")
    .reduce((sum, p) => sum + p.amount, 0);

  return (
    <Layout>
      <div className="page-title">Payment Management</div>
      <div className="page-sub">All payments · Total successful: ₹{totalSuccess}</div>

      {error && <div className="error-banner">{error}</div>}

      <div className="filters-row">
        <select value={status} onChange={(e) => setStatus(e.target.value)}>
          <option value="">All statuses</option>
          <option value="pending">Pending</option>
          <option value="success">Success</option>
          <option value="failed">Failed</option>
        </select>
        <input type="date" value={date} onChange={(e) => setDate(e.target.value)} />
        {(status || date) && (
          <button
            className="btn btn-outline"
            onClick={() => {
              setStatus("");
              setDate("");
            }}
          >
            Clear filters
          </button>
        )}
      </div>

      <div className="card">
        {payments.length === 0 ? (
          <div className="empty-state">No payments found.</div>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Patient</th>
                <th>Doctor</th>
                <th>Amount</th>
                <th>Status</th>
                <th>Transaction ID</th>
                <th>Date</th>
              </tr>
            </thead>
            <tbody>
              {payments.map((p) => (
                <tr key={p.id}>
                  <td>{p.patient_name || "—"}</td>
                  <td>{p.doctor_name || "—"}</td>
                  <td>₹{p.amount}</td>
                  <td>
                    <span className={`badge ${p.payment_status}`}>{p.payment_status}</span>
                  </td>
                  <td style={{ fontFamily: "monospace", fontSize: 12 }}>{p.transaction_id}</td>
                  <td>{new Date(p.created_at).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </Layout>
  );
}
