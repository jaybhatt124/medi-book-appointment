import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import Layout from "../components/Layout";
import api from "../api/api";

export default function Appointments() {
  const [appointments, setAppointments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [statusFilter, setStatusFilter] = useState("");

  const load = () => {
    setLoading(true);
    api
      .get("/doctor/appointments")
      .then(({ data }) => setAppointments(data))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  };

  useEffect(load, []);

  const handleAction = async (id, action) => {
    try {
      await api.patch(`/doctor/appointments/${id}/${action}`);
      load();
    } catch (err) {
      alert(err.message);
    }
  };

  const filtered = statusFilter
    ? appointments.filter((a) => a.status === statusFilter)
    : appointments;

  return (
    <Layout>
      <div className="page-title">Appointments</div>
      <div className="page-sub">Manage all patient appointments</div>

      {error && <div className="error-banner">{error}</div>}

      <div className="filters-row">
        <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
          <option value="">All statuses</option>
          <option value="booked">Booked</option>
          <option value="accepted">Accepted</option>
          <option value="completed">Completed</option>
          <option value="rejected">Rejected</option>
        </select>
      </div>

      <div className="card">
        {loading ? (
          <p>Loading...</p>
        ) : filtered.length === 0 ? (
          <div className="empty-state">No appointments found.</div>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Patient</th>
                <th>Date</th>
                <th>Time</th>
                <th>Status</th>
                <th>Payment</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((a) => (
                <tr key={a.id}>
                  <td>
                    <Link to={`/appointments/${a.id}`}>{a.patient?.full_name}</Link>
                  </td>
                  <td>{a.appointment_date}</td>
                  <td>{a.appointment_time}</td>
                  <td>
                    <span className={`badge ${a.status}`}>{a.status}</span>
                  </td>
                  <td>
                    {a.payment_status ? (
                      <span className={`badge ${a.payment_status}`}>{a.payment_status}</span>
                    ) : (
                      "-"
                    )}
                  </td>
                  <td>
                    <div className="btn-row">
                      {(a.status === "booked" || a.status === "pending") && (
                        <>
                          <button className="btn btn-success" onClick={() => handleAction(a.id, "accept")}>
                            Accept
                          </button>
                          <button className="btn btn-danger" onClick={() => handleAction(a.id, "reject")}>
                            Reject
                          </button>
                        </>
                      )}
                      {a.status === "accepted" && (
                        <button className="btn btn-primary" onClick={() => handleAction(a.id, "complete")}>
                          Mark Completed
                        </button>
                      )}
                    </div>
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
