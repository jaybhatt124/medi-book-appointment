import React, { useEffect, useState } from "react";
import Layout from "../components/Layout";
import api from "../api/api";

export default function Specializations() {
  const [specializations, setSpecializations] = useState([]);
  const [name, setName] = useState("");
  const [error, setError] = useState("");

  const load = () => {
    api
      .get("/admin/specializations")
      .then(({ data }) => setSpecializations(data))
      .catch((err) => setError(err.message));
  };

  useEffect(load, []);

  const handleAdd = async (e) => {
    e.preventDefault();
    setError("");
    if (!name.trim()) return;
    try {
      await api.post("/admin/specializations", { name: name.trim() });
      setName("");
      load();
    } catch (err) {
      setError(err.message);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm("Delete this specialization?")) return;
    try {
      await api.delete(`/admin/specializations/${id}`);
      load();
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <Layout>
      <div className="page-title">Specializations</div>
      <div className="page-sub">Manage the list of doctor specializations</div>

      {error && <div className="error-banner">{error}</div>}

      <form onSubmit={handleAdd} className="card" style={{ marginBottom: 24, maxWidth: 480 }}>
        <div className="filters-row" style={{ marginBottom: 0 }}>
          <input
            className="form-input"
            placeholder="e.g. Cardiologist"
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
          <button className="btn btn-primary">Add</button>
        </div>
      </form>

      <div className="card">
        {specializations.length === 0 ? (
          <div className="empty-state">No specializations yet.</div>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Name</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {specializations.map((s) => (
                <tr key={s.id}>
                  <td>{s.name}</td>
                  <td>
                    <button className="btn btn-danger" onClick={() => handleDelete(s.id)}>
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
