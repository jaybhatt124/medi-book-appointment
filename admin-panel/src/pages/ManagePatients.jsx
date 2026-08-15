import React, { useEffect, useState } from "react";
import Layout from "../components/Layout";
import api from "../api/api";

export default function ManagePatients() {
  const [patients, setPatients] = useState([]);
  const [error, setError] = useState("");

  const load = () => {
    api.get("/admin/patients").then(({ data }) => setPatients(data)).catch((err) => setError(err.message));
  };

  useEffect(load, []);

  const handleDelete = async (id) => {
    if (!window.confirm("Delete this patient account?")) return;
    try {
      await api.delete(`/admin/patients/${id}`);
      load();
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <Layout>
      <div className="page-title">Manage Patients</div>
      <div className="page-sub">View and manage registered patients</div>

      {error && <div className="error-banner">{error}</div>}

      <div className="card">
        {patients.length === 0 ? (
          <div className="empty-state">No patients yet.</div>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Name</th>
                <th>Email</th>
                <th>Phone</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {patients.map((p) => (
                <tr key={p.id}>
                  <td>{p.full_name}</td>
                  <td>{p.email}</td>
                  <td>{p.phone || "—"}</td>
                  <td>
                    <span className={`badge ${p.is_active ? "completed" : "rejected"}`}>
                      {p.is_active ? "active" : "disabled"}
                    </span>
                  </td>
                  <td>
                    <button className="btn btn-danger" onClick={() => handleDelete(p.id)}>
                      Delete
                    </button>
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
