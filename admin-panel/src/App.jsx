import React from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider, useAuth } from "./context/AuthContext";

import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import ManageDoctors from "./pages/ManageDoctors";
import ManageClinics from "./pages/ManageClinics";
import Specializations from "./pages/Specializations";
import ManagePatients from "./pages/ManagePatients";
import ManageAppointments from "./pages/ManageAppointments";
import PaymentManagement from "./pages/PaymentManagement";

function PrivateRoute({ children }) {
  const { user, loading } = useAuth();
  if (loading) return null;
  return user ? children : <Navigate to="/login" replace />;
}

function AppRoutes() {
  const { user } = useAuth();
  return (
    <Routes>
      <Route path="/login" element={user ? <Navigate to="/dashboard" replace /> : <Login />} />
      <Route path="/dashboard" element={<PrivateRoute><Dashboard /></PrivateRoute>} />
      <Route path="/doctors" element={<PrivateRoute><ManageDoctors /></PrivateRoute>} />
      <Route path="/clinics" element={<PrivateRoute><ManageClinics /></PrivateRoute>} />
      <Route path="/specializations" element={<PrivateRoute><Specializations /></PrivateRoute>} />
      <Route path="/patients" element={<PrivateRoute><ManagePatients /></PrivateRoute>} />
      <Route path="/appointments" element={<PrivateRoute><ManageAppointments /></PrivateRoute>} />
      <Route path="/payments" element={<PrivateRoute><PaymentManagement /></PrivateRoute>} />
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <AppRoutes />
    </AuthProvider>
  );
}
