import React, { useState } from "react";
import {
  ArrowLeft,
  Package,
  AlertTriangle,
  Receipt,
  Gift,
  Award,
} from "lucide-react";

import ProductosAdmin from "../ProductosAdmin/ProductosAdmin";
import StockBajoPanel from "../StockBajoPanel/StockBajoPanel";
import HistorialVentas from "../HistorialVentas/HistorialVentas";
import HistorialPuntos from "../HistorialPuntos/HistorialPuntos";
import ConfiguracionFidelizacion from "../ConfiguracionFidelizacion/ConfiguracionFidelizacion";
import "./AdminScreen.scss";

const PESTANAS = [
  {
    id: "productos",
    label: "Productos",
    icon: Package,
    Componente: ProductosAdmin,
  },
  {
    id: "stock-bajo",
    label: "Stock bajo",
    icon: AlertTriangle,
    Componente: StockBajoPanel,
  },
  {
    id: "ventas",
    label: "Historial ventas",
    icon: Receipt,
    Componente: HistorialVentas,
  },
  {
    id: "puntos",
    label: "Historial puntos",
    icon: Gift,
    Componente: HistorialPuntos,
  },
  {
    id: "fidelizacion",
    label: "Fidelización",
    icon: Award,
    Componente: ConfiguracionFidelizacion,
  },
];

export default function AdminScreen({ onVolverAlPos }) {
  const [pestanaActiva, setPestanaActiva] = useState("productos");
  const { Componente } = PESTANAS.find((p) => p.id === pestanaActiva);

  return (
    <div className="admin-screen">
      <header className="admin-screen__topbar">
        <button
          type="button"
          className="admin-screen__volver"
          onClick={onVolverAlPos}
        >
          <ArrowLeft size={16} strokeWidth={2} />
          Volver al POS
        </button>
        <span className="admin-screen__marca">TramaPos · Administración</span>
      </header>

      <div className="admin-screen__cuerpo">
        <nav className="admin-screen__tabs">
          {PESTANAS.map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              type="button"
              className={`admin-screen__tab ${
                pestanaActiva === id ? "admin-screen__tab--activa" : ""
              }`}
              onClick={() => setPestanaActiva(id)}
            >
              <Icon size={16} strokeWidth={2} />
              {label}
            </button>
          ))}
        </nav>

        <div className="admin-screen__contenido">
          <Componente />
        </div>
      </div>
    </div>
  );
}
