import React, { useEffect, useState } from "react";
import { AlertTriangle, RefreshCw } from "lucide-react";

import { productosApi } from "../../../services/api";
import { SkeletonFilas } from "../../Skeleton/Skeleton";
import "./StockBajoPanel.scss";

export default function StockBajoPanel() {
  const [alertas, setAlertas] = useState([]);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState(null);

  const cargar = async () => {
    setCargando(true);
    setError(null);
    try {
      setAlertas(await productosApi.stockBajo());
    } catch (err) {
      setError(err.message);
    } finally {
      setCargando(false);
    }
  };

  useEffect(() => {
    cargar();
  }, []);

  return (
    <div className="stock-bajo">
      <header className="stock-bajo__header">
        <h2 className="stock-bajo__titulo">
          <AlertTriangle size={18} strokeWidth={2} />
          Stock bajo
        </h2>
        <button
          type="button"
          className="stock-bajo__refrescar"
          onClick={cargar}
        >
          <RefreshCw size={14} strokeWidth={2} />
          Refrescar
        </button>
      </header>

      {error && <p className="stock-bajo__error">{error}</p>}

      {cargando ? (
        <SkeletonFilas filas={3} columnas={5} />
      ) : alertas.length === 0 ? (
        <p className="stock-bajo__vacio">
          Sin alertas — todas las variantes están por encima de su stock mínimo.
        </p>
      ) : (
        <table className="stock-bajo__tabla">
          <thead>
            <tr>
              <th>Producto</th>
              <th>Variante</th>
              <th>SKU</th>
              <th>Stock actual</th>
              <th>Stock mínimo</th>
            </tr>
          </thead>
          <tbody>
            {alertas.map((alerta) => (
              <tr key={alerta.sku} className="stock-bajo__fila">
                <td>{alerta.producto}</td>
                <td>
                  {[alerta.color, alerta.grosor].filter(Boolean).join(" · ") ||
                    "—"}
                </td>
                <td className="u-cifra">{alerta.sku}</td>
                <td className="u-cifra stock-bajo__cifra-critica">
                  {alerta.stock_actual}
                </td>
                <td className="u-cifra">{alerta.stock_minimo}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
