import React, { useEffect, useState } from "react";
import Layout from "../components/Layout";
import api from "../api/api";
import { useAuth } from "../context/AuthContext";

export default function Profile() {
  const { user } = useAuth();
  const [doctorId, setDoctorId] = useState(null);
  const [form, setForm] = useState({
    bio: "",
    experience_years: 0,
    consultation_fee: 100,
  });
  const [clinics, setClinics] = useState([]);
  const [specializations, setSpecializations] = useState([]);
  const [clinicId, setClinicId] = useState("");
  const [specializationId, setSpecializationId] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    api.get("/clinics").then(({ data }) => setClinics(data)).catch(() => {});
  }, []);


  const handleSubmit = async (e) => {
    e.preventDefault();
    setMessage("");
    setError("");
    try {
      const payload = {
        bio: form.bio || undefined,
        experience_years: Number(form.experience_years) || undefined,
        consultation_fee: Number(form.consultation_fee) || undefined,
        clinic_id: clinicId || undefined,
        specialization_id: specializationId || undefined,
      };
      await api.put("/doctor/profile", payload);
      setMessage("Profile updated successfully.");
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <Layout>
      <div className="page-title">My Profile</div>
      <div className="page-sub">Update your bio, experience, fee and clinic</div>

      {message && (
        <div className="error-banner" style={{ background: "#DCFCE7", color: "var(--success)" }}>
          {message}
        </div>
      )}
      {error && <div className="error-banner">{error}</div>}

      <form onSubmit={handleSubmit} className="card" style={{ maxWidth: 560 }}>
        <div className="form-group">
          <label className="form-label">Bio</label>
          <textarea
            className="form-input"
            rows={4}
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
        <div className="form-group">
          <label className="form-label">Clinic</label>
          <select className="form-input" value={clinicId} onChange={(e) => setClinicId(e.target.value)}>
            <option value="">Keep current clinic</option>
            {clinics.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name} — {c.city}
              </option>
            ))}
          </select>
        </div>
        <button className="btn btn-primary">Save Changes</button>
      </form>
    </Layout>
  );
}
