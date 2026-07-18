import React, { createContext, useContext, useEffect, useState } from "react";

import { authApi } from "../../services/api";

const AuthContext = createContext(null);

/**
 * AuthProvider
 * Envuelve toda la app (en main.jsx). Al arrancar, si hay un token
 * guardado en localStorage, valida que siga siendo válido contra
 * GET /auth/me antes de dar por hecho que la sesión sigue activa —
 * así un token vencido no deja a alguien "logueado" con una sesión
 * que en realidad el backend ya rechaza.
 */
export function AuthProvider({ children }) {
  const [usuario, setUsuario] = useState(null);
  const [cargando, setCargando] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("tramapos_token");
    if (!token) {
      setCargando(false);
      return;
    }
    authApi
      .me()
      .then(setUsuario)
      .catch(() => {
        localStorage.removeItem("tramapos_token");
        localStorage.removeItem("tramapos_usuario");
      })
      .finally(() => setCargando(false));
  }, []);

  const login = async (username, password) => {
    const respuesta = await authApi.login(username, password);
    localStorage.setItem("tramapos_token", respuesta.access_token);
    localStorage.setItem("tramapos_usuario", JSON.stringify(respuesta.usuario));
    setUsuario(respuesta.usuario);
  };

  const logout = () => {
    localStorage.removeItem("tramapos_token");
    localStorage.removeItem("tramapos_usuario");
    setUsuario(null);
  };

  return (
    <AuthContext.Provider value={{ usuario, cargando, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const contexto = useContext(AuthContext);
  if (!contexto) {
    throw new Error("useAuth debe usarse dentro de <AuthProvider>");
  }
  return contexto;
}
