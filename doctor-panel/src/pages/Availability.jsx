import React, { useEffect, useState } from "react";
import Layout from "../components/Layout";
import api from "../api/api";

const DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];

export default function Availability() {
  const [slots, setSlots] = useState([]);
  const [day, setDay] = useState(0);
  const [time, setTime] = useState("10:00 AM");
  const [error, setError] = useState("");

  const load = () => {
    api
      .get("/doctor/availability")
      .then(({ data }) => setSlots(data))
      .catch((err) => setError(err.message));
  };

  useEffect(load, []);

  const handleAdd = async (e) => {
    e.preventDefault();
    setError("");
    try {
      await api.post("/doctor/availability", { day_of_week: Number(day), slot_time: time });
      load();
    } catch (err) {
      setError(err.message);
    }
  };

  const handleRemove = async (id) => {
    try {
      await api.delete(`/doctor/availability/${id}`);
      load();
    } catch (err) {
      setError(err.message);
    }
  };

  const grouped = DAYS.map((label, idx) => ({
    label,
    idx,
    slots: slots.filter((s) => s.day_of_week === idx),
  }));

  return (
    <Layout>
      <div className="page-title">Availability</div>
      <div className="page-sub">Manage the days and time slots patients can book</div>

      {error && <div className="error-banner">{error}</div>}

      <form onSubmit={handleAdd} className="card" style={{ marginBottom: 24, maxWidth: 560 }}>
        <div className="filters-row" style={{ marginBottom: 0 }}>
          <select value={day} onChange={(e) => setDay(e.target.value)}>
            {DAYS.map((d, idx) => (
              <option key={d} value={idx}>
                {d}
              </option>
            ))}
          </select>
          <input
            className="form-input"
            style={{ width: 140 }}
            value={time}
            onChange={(e) => setTime(e.target.value)}
            placeholder="e.g. 10:00 AM"
          />
          <button className="btn btn-primary">Add Slot</button>
        </div>
      </form>

      {grouped.map((g) => (
        <div className="card" key={g.idx} style={{ marginBottom: 16 }}>
          <div style={{ fontWeight: 700, marginBottom: 10 }}>{g.label}</div>
          {g.slots.length === 0 ? (
            <div style={{ color: "var(--text-muted)", fontSize: 13 }}>No slots set for this day.</div>
          ) : (
            <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
              {g.slots.map((s) => (
                <div
                  key={s.id}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 8,
                    border: "1px solid var(--border)",
                    borderRadius: 8,
                    padding: "6px 10px",
                    fontSize: 13,
                  }}
                >
                  {s.slot_time}
                  <button
                    onClick={() => handleRemove(s.id)}
                    style={{
                      border: "none",
                      background: "none",
                      color: "var(--danger)",
                      cursor: "pointer",
                      fontWeight: 700,
                    }}
                  >
                    ×
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      ))}
    </Layout>
  );
}
