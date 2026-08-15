import React, { useEffect, useState } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import Layout from "../components/Layout";
import api from "../api/api";

export default function AppointmentDetails() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [appointment, setAppointment] = useState(null);
  const [error, setError] = useState("");

  const load = () => {
    api
      .get("/doctor/appointments")
      .then(({ data }) => {
        const found = data.find((a) => a.id === id);
        if (!found) {
          setError("Appointment not found.");
        } else {
          setAppointment(found);
        }
      })
      .catch((err) => setError(err.message));
  };

  useEffect(load, [id]);

  const handleAction = async (action) => {
    try {
      await api.patch(`/doctor/appointments/${id}/${action}`);
      load();
    } catch (err) {
      alert(err.message);
    }
  };

  return (
    <Layout>
      <Link to="/appointments" style={{ fontSize: 13, color: "var(--primary-dark)" }}>
        ← Back to Appointments
      </Link>
      <div className="page-title" style={{ marginTop: 12 }}>
        Appointment Details
      </div>

      {error && <div className="error-banner">{error}</div>}

      {appointment && (
        <div className="card" style={{ maxWidth: 560 }}>
          <div className="form-group">
            <div className="form-label">Patient Name</div>
            <div>{appointment.patient?.full_name}</div>
          </div>
          <div className="form-group">
            <div className="form-label">Patient Email</div>
            <div>{appointment.patient?.email}</div>
          </div>
          <div className="form-group">
            <div className="form-label">Patient Phone</div>
            <div>{appointment.patient?.phone || "—"}</div>
          </div>
          <div className="form-group">
            <div className="form-label">Date & Time</div>
            <div>
              {appointment.appointment_date} at {appointment.appointment_time}
            </div>
          </div>
          <div className="form-group">
            <div className="form-label">Status</div>
            <span className={`badge ${appointment.status}`}>{appointment.status}</span>
          </div>
          <div className="form-group">
            <div className="form-label">Payment</div>
            {appointment.payment_status ? (
              <span className={`badge ${appointment.payment_status}`}>{appointment.payment_status}</span>
            ) : (
              "—"
            )}
            {appointment.amount ? ` · ₹${appointment.amount}` : ""}
          </div>

          <div className="btn-row" style={{ marginTop: 20 }}>
            {(appointment.status === "booked" || appointment.status === "pending") && (
              <>
                <button className="btn btn-success" onClick={() => handleAction("accept")}>
                  Accept
                </button>
                <button className="btn btn-danger" onClick={() => handleAction("reject")}>
                  Reject
                </button>
              </>
            )}
            {appointment.status === "accepted" && (
              <button className="btn btn-primary" onClick={() => handleAction("complete")}>
                Mark Completed
              </button>
            )}
          </div>
        </div>
      )}
    </Layout>
  );
}
