import React, { useEffect, useState } from "react";
import Layout from "../components/Layout";
import api from "../api/api";

export default function PaymentHistory() {
  const [payments, setPayments] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .get("/doctor/payments")
      .then(({ data }) => setPayments(data))
      .catch((err) => setError(err.message));
  }, []);

  const totalEarned = payments
    .filter((p) => p.payment_status === "success")
    .reduce((sum, p) => sum + p.amount, 0);

  return (
    <Layout>
      <div className="page-title">Payment History</div>
      <div className="page-sub">All payments received from patients · Total earned: ₹{totalEarned}</div>

      {error && <div className="error-banner">{error}</div>}

      <div className="card">
        {payments.length === 0 ? (
          <div className="empty-state">No payments yet.</div>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Patient</th>
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
