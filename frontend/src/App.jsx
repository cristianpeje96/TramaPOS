import React, { useState } from "react";

import PosScreen from "./components/PosScreen/PosScreen";
import AdminScreen from "./components/admin/AdminScreen/AdminScreen";
import DevolucionesScreen from "./components/DevolucionesScreen/DevolucionesScreen";

/**
 * App.jsx
 * Tres vistas con un simple toggle de estado (sin router): POS,
 * Administración y Devoluciones. Devoluciones es una pantalla propia
 * (no un modal ni una pestaña dentro del POS) a propósito — ver el
 * comentario en DevolucionesScreen.jsx sobre por qué.
 */
export default function App() {
  const [vista, setVista] = useState("pos"); // 'pos' | 'admin' | 'devoluciones'

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
