import React, { useEffect, useState } from "react";
import Layout from "../components/Layout";
import api from "../api/api";

const emptyForm = {
  full_name: "",
  email: "",
  phone: "",
  password: "",
  clinic_id: "",
  specialization_id: "",
  bio: "",
  experience_years: 0,
  consultation_fee: 100,
};

export default function ManageDoctors() {
  const [doctors, setDoctors] = useState([]);
  const [clinics, setClinics] = useState([]);
  const [specializations, setSpecializations] = useState([]);
  const [error, setError] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [form, setForm] = useState(emptyForm);

  const load = () => {
    api.get("/admin/doctors").then(({ data }) => setDoctors(data)).catch((err) => setError(err.message));
    api.get("/clinics").then(({ data }) => setClinics(data)).catch(() => {});
    api.get("/admin/specializations").then(({ data }) => setSpecializations(data)).catch(() => {});
  };

  useEffect(load, []);

  const resetForm = () => {
    setForm(emptyForm);
    setEditingId(null);
    setShowForm(false);
  };

  const handleAddNew = () => {
    setForm(emptyForm);
    setEditingId(null);
    setShowForm(true);
  };

  const handleEdit = (doctor) => {
    setForm({
      full_name: doctor.full_name,
      email: doctor.email,
      phone: doctor.phone || "",
      password: "",
      clinic_id: doctor.clinic?.id || "",
      specialization_id: doctor.specialization?.id || "",
      bio: doctor.bio || "",
      experience_years: doctor.experience_years,
      consultation_fee: doctor.consultation_fee,
    });
    setEditingId(doctor.id);
    setShowForm(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    try {
      if (editingId) {
        await api.patch(`/admin/doctors/${editingId}`, {
          full_name: form.full_name,
          phone: form.phone || undefined,
          clinic_id: form.clinic_id || undefined,
          specialization_id: form.specialization_id || undefined,
          bio: form.bio || undefined,
          experience_years: Number(form.experience_years),
          consultation_fee: Number(form.consultation_fee),
        });
      } else {
        await api.post("/admin/doctors", {
          full_name: form.full_name,
          email: form.email,
          phone: form.phone || undefined,
          password: form.password,
          clinic_id: form.clinic_id || undefined,
          specialization_id: form.specialization_id || undefined,
          bio: form.bio || undefined,
          experience_years: Number(form.experience_years),
          consultation_fee: Number(form.consultation_fee),
        });
      }
      resetForm();
      load();
    } catch (err) {
      setError(err.message);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm("Delete this doctor? This cannot be undone.")) return;
    try {
      await api.delete(`/admin/doctors/${id}`);
      load();
    } catch (err) {
      setError(err.message);
    }
  };

  const handleApprove = async (id) => {
    try {
      await api.patch(`/admin/doctors/${id}/approve`);
      load();
    } catch (err) {
      setError(err.message);
    }
  };

  const handleReject = async (id) => {
    try {
      await api.patch(`/admin/doctors/${id}/reject`);
      load();
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <Layout>
      <div className="topbar">
        <div>
          <div className="page-title">Manage Doctors</div>
          <div className="page-sub">Add, edit, approve, or remove doctors</div>
        </div>
        <button className="btn btn-primary" onClick={handleAddNew}>
          + Add Doctor
        </button>
      </div>

      {error && <div className="error-banner">{error}</div>}

      {showForm && (
        <form onSubmit={handleSubmit} className="card" style={{ marginBottom: 24, maxWidth: 640 }}>
          <div style={{ fontWeight: 700, marginBottom: 16 }}>
            {editingId ? "Edit Doctor" : "Add New Doctor"}
          </div>
          <div className="form-group">
            <label className="form-label">Full Name</label>
            <input
              className="form-input"
              value={form.full_name}
              onChange={(e) => setForm({ ...form, full_name: e.target.value })}
              required
            />
          </div>
          {!editingId && (
            <>
              <div className="form-group">
                <label className="form-label">Email</label>
                <input
                  className="form-input"
                  type="email"
                  value={form.email}
                  onChange={(e) => setForm({ ...form, email: e.target.value })}
                  required
                />
              </div>
              <div className="form-group">
                <label className="form-label">Password</label>
                <input
                  className="form-input"
                  type="password"
                  value={form.password}
                  onChange={(e) => setForm({ ...form, password: e.target.value })}
                  required
                />
              </div>
            </>
          )}
          <div className="form-group">
            <label className="form-label">Phone</label>
            <input
              className="form-input"
              value={form.phone}
              onChange={(e) => setForm({ ...form, phone: e.target.value })}
            />
          </div>
          <div className="form-group">
            <label className="form-label">Clinic</label>
            <select
              className="form-input"
              value={form.clinic_id}
              onChange={(e) => setForm({ ...form, clinic_id: e.target.value })}
            >
              <option value="">Select clinic</option>
              {clinics.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name} — {c.city}
                </option>
              ))}
            </select>
          </div>
          <div className="form-group">
            <label className="form-label">Specialization</label>
            <select
              className="form-input"
              value={form.specialization_id}
              onChange={(e) => setForm({ ...form, specialization_id: e.target.value })}
            >
              <option value="">Select specialization</option>
              {specializations.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name}
                </option>
              ))}
            </select>
          </div>
          <div className="form-group">
            <label className="form-label">Bio</label>
            <textarea
              className="form-input"
              rows={3}
              value={form.bio}
              onChange={(e) => setForm({ ...form, bio: e.target.value })}
            />
          </div>
          <div className="form-group">
            <label className="form-label">Experience (years)</label>
            <input
              type="number"
              className="form-input"
              value={form.experience_years}
              onChange={(e) => setForm({ ...form, experience_years: e.target.value })}
            />
          </div>
          <div className="form-group">
            <label className="form-label">Consultation Fee (₹)</label>
            <input
              type="number"
              className="form-input"
              value={form.consultation_fee}
              onChange={(e) => setForm({ ...form, consultation_fee: e.target.value })}
            />
          </div>
          <div className="btn-row">
            <button className="btn btn-primary">{editingId ? "Save Changes" : "Add Doctor"}</button>
            <button type="button" className="btn btn-outline" onClick={resetForm}>
              Cancel
            </button>
          </div>
        </form>
      )}

      <div className="card">
        {doctors.length === 0 ? (
          <div className="empty-state">No doctors yet.</div>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Name</th>
                <th>Clinic</th>
                <th>Specialization</th>
                <th>Fee</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {doctors.map((d) => (
                <tr key={d.id}>
                  <td>{d.full_name}</td>
                  <td>{d.clinic?.name || "—"}</td>
                  <td>{d.specialization?.name || "—"}</td>
                  <td>₹{d.consultation_fee}</td>
                  <td>
                    <span
                      className={`badge ${
                        d.approval_status === "approved"
                          ? "completed"
                          : d.approval_status === "rejected"
                          ? "rejected"
                          : "pending"
                      }`}
                    >
                      {d.approval_status}
                    </span>
                  </td>
                  <td>
                    <div className="btn-row">
                      <button className="btn btn-outline" onClick={() => handleEdit(d)}>
                        Edit
                      </button>
                      {d.approval_status !== "approved" && (
                        <button className="btn btn-success" onClick={() => handleApprove(d.id)}>
                          Approve
                        </button>
                      )}
                      {d.approval_status !== "rejected" && (
                        <button className="btn btn-danger" onClick={() => handleReject(d.id)}>
                          Reject
                        </button>
                      )}
                      <button className="btn btn-danger" onClick={() => handleDelete(d.id)}>
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
