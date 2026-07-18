import React, { useState } from "react";

import PosScreen from "./components/PosScreen/PosScreen";
import AdminScreen from "./components/admin/AdminScreen/AdminScreen";
import DevolucionesScreen from "./components/DevolucionesScreen/DevolucionesScreen";
import LoginScreen from "./components/Auth/LoginScreen";
import { useAuth } from "./components/Auth/AuthProvider";

/**
 * App.jsx
 * Ahora hay una capa de autenticación antes de todo: si no hay sesión
 * válida, se muestra LoginScreen y nada más. Una vez logueado, el mismo
 * toggle de 3 vistas de siempre (POS / Admin / Devoluciones).
 */
export default function App() {
  const { usuario, cargando } = useAuth();
  const [vista, setVista] = useState("pos"); // 'pos' | 'admin' | 'devoluciones'

  if (cargando) {
    return <div style={{ padding: 24 }}>Verificando sesión…</div>;
  }

  if (!usuario) {
    return <LoginScreen />;
  }

  if (vista === "admin") {
    return <AdminScreen onVolverAlPos={() => setVista("pos")} />;
  }

  if (vista === "devoluciones") {
    return <DevolucionesScreen onVolverAlPos={() => setVista("pos")} />;
  }

  return (
    <PosScreen
      onIrAdmin={() => setVista("admin")}
      onIrDevoluciones={() => setVista("devoluciones")}
    />
  );
}
