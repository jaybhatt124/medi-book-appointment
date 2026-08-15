import React, { createContext, useContext, useEffect, useState } from "react";
import api from "../api/api";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("doctor_token");
    const userJson = localStorage.getItem("doctor_user");
    if (token && userJson) {
      setUser(JSON.parse(userJson));
    }
    setLoading(false);
  }, []);

  const login = async (email, password) => {
    const { data } = await api.post("/auth/login", { email, password });
    if (data.role !== "doctor") {
      throw new Error("This portal is for doctors only. Please use the correct login.");
    }
    localStorage.setItem("doctor_token", data.access_token);
    const userObj = { user_id: data.user_id, full_name: data.full_name, role: data.role };
    localStorage.setItem("doctor_user", JSON.stringify(userObj));
    setUser(userObj);
    return userObj;
  };

  const logout = () => {
    localStorage.removeItem("doctor_token");
    localStorage.removeItem("doctor_user");
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, logout }}>{children}</AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
