import React from "react";
import { NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

const links = [
  { to: "/dashboard", label: "Dashboard" },
  { to: "/doctors", label: "Manage Doctors" },
  { to: "/clinics", label: "Manage Clinics" },
  { to: "/specializations", label: "Specializations" },
  { to: "/patients", label: "Manage Patients" },
  { to: "/appointments", label: "Appointments" },
  { to: "/payments", label: "Payments" },
];

export default function Layout({ children }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="sidebar-logo">MediBook</div>
        <div className="sidebar-sub">Admin Panel · {user?.full_name}</div>
        {links.map((link) => (
          <NavLink
            key={link.to}
            to={link.to}
            className={({ isActive }) => "nav-link" + (isActive ? " active" : "")}
          >
            {link.label}
          </NavLink>
        ))}
        <button className="logout-btn" onClick={handleLogout}>
          Logout
        </button>
      </aside>
      <main className="main-content">{children}</main>
    </div>
  );
}
