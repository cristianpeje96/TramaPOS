import React, { useState } from "react";
import { X, Search, UserPlus } from "lucide-react";

import { useCliente } from "../../hooks/useCliente";
import "./ModalCliente.scss";

/**
 * ModalCliente
 * Se abre con F7. Busca por nombre o documento contra GET /clientes/buscar;
 * si no hay resultados, deja crear al vuelo con POST /clientes/rapido
 * (solo documento + nombre — sin frenar la fila pidiendo más datos).
 */
export default function ModalCliente({
  abierto,
  onCerrar,
  onClienteSeleccionado,
}) {
  const { buscando, resultados, error, buscar, buscarOCrearRapido } =
    useCliente();
  const [texto, setTexto] = useState("");
  const [documentoNuevo, setDocumentoNuevo] = useState("");
  const [nombreNuevo, setNombreNuevo] = useState("");
  const [creando, setCreando] = useState(false);

  if (!abierto) return null;

  const manejarBusqueda = (valor) => {
    setTexto(valor);
    buscar(valor);
  };

  const elegirCliente = (cliente) => {
    onClienteSeleccionado?.(cliente);
    onCerrar?.();
  };

  const crearRapido = async () => {
    if (!documentoNuevo.trim() || !nombreNuevo.trim()) return;
    setCreando(true);
    const cliente = await buscarOCrearRapido(
      documentoNuevo.trim(),
      nombreNuevo.trim(),
    );
    setCreando(false);
    if (cliente) elegirCliente(cliente);
  };

  return (
    <div className="modal-cliente__overlay" onClick={onCerrar}>
      <div className="modal-cliente" onClick={(e) => e.stopPropagation()}>
        <header className="modal-cliente__header">
          <h2 className="modal-cliente__title">Buscar cliente (F7)</h2>
          <button
            type="button"
            className="modal-cliente__cerrar"
            onClick={onCerrar}
          >
            <X size={18} strokeWidth={2} />
          </button>
        </header>

        <div className="modal-cliente__input-wrap">
          <Search size={16} strokeWidth={2} />
          <input
            autoFocus
            type="text"
            className="modal-cliente__input"
            placeholder="Nombre o número de documento"
            value={texto}
            onChange={(e) => manejarBusqueda(e.target.value)}
          />
        </div>

        {error && <p className="modal-cliente__error">{error}</p>}

        {buscando && <p className="modal-cliente__estado">Buscando…</p>}

        {resultados.length > 0 && (
          <ul className="modal-cliente__resultados">
            {resultados.map((cliente) => (
              <li key={cliente.id}>
                <button
                  type="button"
                  className="modal-cliente__resultado"
                  onClick={() => elegirCliente(cliente)}
                >
                  <span className="modal-cliente__resultado-nombre">
                    {cliente.nombre_completo}
                  </span>
                  <span className="modal-cliente__resultado-doc u-cifra">
                    {cliente.numero_documento}
                  </span>
                  <span className="modal-cliente__resultado-puntos u-cifra">
                    {cliente.puntos_balance} pts
                  </span>
                </button>
              </li>
            ))}
          </ul>
        )}

        {!buscando && texto.trim().length > 0 && resultados.length === 0 && (
          <div className="modal-cliente__crear">
            <p className="modal-cliente__crear-hint">
              <UserPlus size={16} strokeWidth={2} />
              No se encontró — crear cliente nuevo
            </p>
            <div className="modal-cliente__crear-campos">
              <input
                type="text"
                className="modal-cliente__crear-input"
                placeholder="Documento (CC)"
                value={documentoNuevo}
                onChange={(e) => setDocumentoNuevo(e.target.value)}
              />
              <input
                type="text"
                className="modal-cliente__crear-input"
                placeholder="Nombre completo"
                value={nombreNuevo}
                onChange={(e) => setNombreNuevo(e.target.value)}
              />
              <button
                type="button"
                className="modal-cliente__crear-btn"
                disabled={
                  creando || !documentoNuevo.trim() || !nombreNuevo.trim()
                }
                onClick={crearRapido}
              >
                {creando ? "Creando…" : "Crear y seleccionar"}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
