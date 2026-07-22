import React, { useEffect, useState } from "react";
import {
  ArrowLeft,
  Package,
  AlertTriangle,
  Receipt,
  Gift,
  Award,
  Percent,
  Store,
  Truck,
  ShoppingBag,
  BarChart2,
  Sparkles,
  Wallet,
} from "lucide-react";

import ProductosAdmin from "../ProductosAdmin/ProductosAdmin";
import StockBajoPanel from "../StockBajoPanel/StockBajoPanel";
import HistorialVentas from "../HistorialVentas/HistorialVentas";
import HistorialPuntos from "../HistorialPuntos/HistorialPuntos";
import ConfiguracionFidelizacion from "../ConfiguracionFidelizacion/ConfiguracionFidelizacion";
import ConfiguracionIVA from "../ConfiguracionIVA/ConfiguracionIVA";
import CajasFisicasAdmin from "../CajasFisicasAdmin/CajasFisicasAdmin";
import ProveedoresAdmin from "../ProveedoresAdmin/ProveedoresAdmin";
import ComprasAdmin from "../ComprasAdmin/ComprasAdmin";
import ReportesAdmin from "../ReportesAdmin/ReportesAdmin";
import AsistenteIA from "../AsistenteIA/AsistenteIA";
import FinanzasAdmin from "../FinanzasAdmin/FinanzasAdmin";
import { useAuth } from "../../Auth/AuthProvider";
import "./AdminScreen.scss";

const PESTANAS = [
  {
    id: "reportes",
    label: "Reportes",
    icon: BarChart2,
    Componente: ReportesAdmin,
  },
  {
    id: "finanzas",
    label: "Finanzas",
    icon: Wallet,
    Componente: FinanzasAdmin,
  },
  {
    id: "asistente",
    label: "Asistente IA",
    icon: Sparkles,
    Componente: AsistenteIA,
  },
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
  { id: "iva", label: "IVA", icon: Percent, Componente: ConfiguracionIVA },
  {
    id: "cajas",
    label: "Cajas físicas",
    icon: Store,
    Componente: CajasFisicasAdmin,
  },
  {
    id: "proveedores",
    label: "Proveedores",
    icon: Truck,
    Componente: ProveedoresAdmin,
  },
  {
    id: "compras",
    label: "Compras",
    icon: ShoppingBag,
    Componente: ComprasAdmin,
  },
];

export default function AdminScreen({ onVolverAlPos }) {
  const { usuario } = useAuth();
  const [pestanaActiva, setPestanaActiva] = useState("reportes");
  const { Componente } = PESTANAS.find((p) => p.id === pestanaActiva);

  // Defensa extra: el botón para llegar aquí ya está oculto para cajeros,
  // pero si de alguna forma entran (ej. estado viejo en memoria), los
  // devolvemos al POS — el backend igual rechazaría cada request con 403.
  useEffect(() => {
    if (usuario && usuario.rol !== "ADMIN") {
      onVolverAlPos?.();
    }
  }, [usuario, onVolverAlPos]);

  if (!usuario || usuario.rol !== "ADMIN") {
    return null;
  }

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
