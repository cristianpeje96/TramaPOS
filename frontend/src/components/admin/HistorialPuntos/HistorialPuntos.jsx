import React, { useEffect, useState } from "react";
import { Gift, Search } from "lucide-react";

import { fidelizacionApi } from "../../../services/api";
import { useCliente } from "../../../hooks/useCliente";
import "./HistorialPuntos.scss";

const ETIQUETAS_TIPO = {
  GANADO: "Ganado",
  REDIMIDO: "Redimido",
  AJUSTE_MANUAL: "Ajuste manual",
  EXPIRADO: "Expirado",
};

export default function HistorialPuntos() {
  const { buscando, resultados, buscar, seleccionar, cliente } = useCliente();
  const [texto, setTexto] = useState("");
  const [movimientos, setMovimientos] = useState([]);
  const [cargandoHistorial, setCargandoHistorial] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!cliente) {
      setMovimientos([]);
      return;
    }
    setCargandoHistorial(true);
    setError(null);
    fidelizacionApi
      .historial(cliente.id)
      .then(setMovimientos)
      .catch((err) => setError(err.message))
      .finally(() => setCargandoHistorial(false));
  }, [cliente]);

  return (
    <div className="historial-puntos">
      <header className="historial-puntos__header">
        <h2 className="historial-puntos__titulo">
          <Gift size={18} strokeWidth={2} />
          Historial de puntos por cliente
        </h2>
      </header>

      <div className="historial-puntos__buscador">
        <Search size={16} strokeWidth={2} />
        <input
          type="text"
          placeholder="Buscar cliente por nombre o documento"
          value={texto}
          onChange={(e) => {
            setTexto(e.target.value);
            buscar(e.target.value);
          }}
        />
      </div>

      {buscando && <p className="historial-puntos__estado">Buscando…</p>}

      {resultados.length > 0 && (
        <ul className="historial-puntos__resultados">
          {resultados.map((c) => (
            <li key={c.id}>
              <button
                type="button"
                onClick={() => {
                  seleccionar(c);
                  setTexto("");
                }}
              >
                {c.nombre_completo} ·{" "}
                <span className="u-cifra">{c.numero_documento}</span>
              </button>
            </li>
          ))}
        </ul>
      )}

      {cliente && (
        <div className="historial-puntos__cliente">
          <p>
            <strong>{cliente.nombre_completo}</strong> — saldo actual:{" "}
            <span className="u-cifra">{cliente.puntos_balance}</span> pts
          </p>

          {error && <p className="historial-puntos__error">{error}</p>}

          {cargandoHistorial ? (
            <p className="historial-puntos__estado">Cargando historial…</p>
          ) : movimientos.length === 0 ? (
            <p className="historial-puntos__estado">
              Sin movimientos registrados.
            </p>
          ) : (
            <table className="historial-puntos__tabla">
              <thead>
                <tr>
                  <th>Fecha</th>
                  <th>Tipo</th>
                  <th>Puntos</th>
                  <th>Saldo resultante</th>
                  <th>Nota</th>
                </tr>
              </thead>
              <tbody>
                {movimientos.map((m) => (
                  <tr key={m.id}>
                    <td className="u-cifra">
                      {new Date(m.creado_en).toLocaleString("es-CO")}
                    </td>
                    <td>{ETIQUETAS_TIPO[m.tipo_movimiento]}</td>
                    <td className="u-cifra">
                      {m.puntos > 0 ? `+${m.puntos}` : m.puntos}
                    </td>
                    <td className="u-cifra">{m.saldo_resultante}</td>
                    <td>{m.nota || "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}
    </div>
  );
}
