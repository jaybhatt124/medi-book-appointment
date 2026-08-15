import React, { useEffect, useState } from "react";
import Layout from "../components/Layout";
import api from "../api/api";

const emptyForm = { name: "", address: "", city: "", phone: "" };

export default function ManageClinics() {
  const [clinics, setClinics] = useState([]);
  const [error, setError] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [form, setForm] = useState(emptyForm);

  const load = () => {
    api.get("/admin/clinics").then(({ data }) => setClinics(data)).catch((err) => setError(err.message));
  };

  useEffect(load, []);

  const resetForm = () => {
    setForm(emptyForm);
    setEditingId(null);
    setShowForm(false);
  };

  const handleEdit = (clinic) => {
    setForm({ name: clinic.name, address: clinic.address, city: clinic.city, phone: clinic.phone || "" });
    setEditingId(clinic.id);
    setShowForm(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    try {
      if (editingId) {
        await api.patch(`/admin/clinics/${editingId}`, form);
      } else {
        await api.post("/admin/clinics", form);
      }
      resetForm();
      load();
    } catch (err) {
      setError(err.message);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm("Delete this clinic?")) return;
    try {
      await api.delete(`/admin/clinics/${id}`);
      load();
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <Layout>
      <div className="topbar">
        <div>
          <div className="page-title">Manage Clinics</div>
          <div className="page-sub">Add, edit, or remove clinics</div>
        </div>
        <button
          className="btn btn-primary"
          onClick={() => {
            setForm(emptyForm);
            setEditingId(null);
            setShowForm(true);
          }}
        >
          + Add Clinic
        </button>
      </div>

      {error && <div className="error-banner">{error}</div>}

      {showForm && (
        <form onSubmit={handleSubmit} className="card" style={{ marginBottom: 24, maxWidth: 560 }}>
          <div style={{ fontWeight: 700, marginBottom: 16 }}>{editingId ? "Edit Clinic" : "Add Clinic"}</div>
          <div className="form-group">
            <label className="form-label">Name</label>
            <input
              className="form-input"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              required
            />
          </div>
          <div className="form-group">
            <label className="form-label">Address</label>
            <input
              className="form-input"
              value={form.address}
              onChange={(e) => setForm({ ...form, address: e.target.value })}
              required
            />
          </div>
          <div className="form-group">
            <label className="form-label">City</label>
            <input
              className="form-input"
              value={form.city}
              onChange={(e) => setForm({ ...form, city: e.target.value })}
              required
            />
          </div>
          <div className="form-group">
            <label className="form-label">Phone</label>
            <input
              className="form-input"
              value={form.phone}
              onChange={(e) => setForm({ ...form, phone: e.target.value })}
            />
          </div>
          <div className="btn-row">
            <button className="btn btn-primary">{editingId ? "Save Changes" : "Add Clinic"}</button>
            <button type="button" className="btn btn-outline" onClick={resetForm}>
              Cancel
            </button>
          </div>
        </form>
      )}

      <div className="card">
        {clinics.length === 0 ? (
          <div className="empty-state">No clinics yet.</div>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Name</th>
                <th>Address</th>
                <th>City</th>
                <th>Phone</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {clinics.map((c) => (
                <tr key={c.id}>
                  <td>{c.name}</td>
                  <td>{c.address}</td>
                  <td>{c.city}</td>
                  <td>{c.phone || "—"}</td>
                  <td>
                    <div className="btn-row">
                      <button className="btn btn-outline" onClick={() => handleEdit(c)}>
                        Edit
                      </button>
                      <button className="btn btn-danger" onClick={() => handleDelete(c.id)}>
                        Delete
                      </button>
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
