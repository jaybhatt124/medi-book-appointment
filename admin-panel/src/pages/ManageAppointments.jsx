import React, { useEffect, useState } from "react";
import Layout from "../components/Layout";
import api from "../api/api";

export default function ManageAppointments() {
  const [appointments, setAppointments] = useState([]);
  const [error, setError] = useState("");
  const [status, setStatus] = useState("");
  const [date, setDate] = useState("");

  const load = () => {
    const params = {};
    if (status) params.status = status;
    if (date) params.date = date;
    api
      .get("/admin/appointments", { params })
      .then(({ data }) => setAppointments(data))
      .catch((err) => setError(err.message));
  };

  useEffect(load, [status, date]);

  return (
    <Layout>
      <div className="page-title">All Appointments</div>
      <div className="page-sub">View and filter appointments across the platform</div>

      {error && <div className="error-banner">{error}</div>}

      <div className="filters-row">
        <select value={status} onChange={(e) => setStatus(e.target.value)}>
          <option value="">All statuses</option>
          <option value="pending">Pending</option>
          <option value="booked">Booked</option>
          <option value="accepted">Accepted</option>
          <option value="completed">Completed</option>
          <option value="rejected">Rejected</option>
          <option value="cancelled">Cancelled</option>
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
        {appointments.length === 0 ? (
          <div className="empty-state">No appointments found.</div>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Patient</th>
                <th>Doctor</th>
                <th>Date</th>
                <th>Time</th>
                <th>Status</th>
                <th>Payment</th>
              </tr>
            </thead>
            <tbody>
              {appointments.map((a) => (
                <tr key={a.id}>
                  <td>{a.patient?.full_name}</td>
                  <td>{a.doctor?.full_name}</td>
                  <td>{a.appointment_date}</td>
                  <td>{a.appointment_time}</td>
                  <td>
                    <span className={`badge ${a.status}`}>{a.status}</span>
                  </td>
                  <td>
                    {a.payment_status ? (
                      <span className={`badge ${a.payment_status}`}>{a.payment_status}</span>
                    ) : (
                      "—"
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </Layout>
  );
}
