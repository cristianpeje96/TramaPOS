import React, { useEffect, useState } from "react";
import {
  ArrowLeft,
  RotateCcw,
  AlertTriangle,
  CheckCircle2,
  Calendar,
} from "lucide-react";

import { devolucionesApi, ventasApi } from "../../services/api";
import { SkeletonFilas } from "../Skeleton/Skeleton";
import "./DevolucionesScreen.scss";

const ETIQUETAS_METODO_PAGO = {
  EFECTIVO: "Efectivo",
  DATAFONO: "Datáfono",
  TRANSFERENCIA: "Transferencia",
  PASARELA_WEB: "Pasarela web",
  MIXTO: "Mixto",
};

const fechaISO = (fecha) => fecha.toISOString().slice(0, 10);
const hoyISO = () => fechaISO(new Date());
const ayerISO = () => {
  const ayer = new Date();
  ayer.setDate(ayer.getDate() - 1);
  return fechaISO(ayer);
};

/**
 * DevolucionesScreen — pantalla propia, separada del POS.
 *
 * Flujo por FECHA en vez de número de venta: buscar un número exacto se
 * vuelve poco práctico apenas hay volumen de ventas — es mucho más
 * natural para el cajero pensar "la venta de hace un rato, hoy" que
 * recordar el id. Se elige un día, se ve la lista de ventas de ESE día
 * nada más, y se hace click en la correcta.
 *
 * Sigue siendo una pantalla separada del POS a propósito — ver nota
 * anterior sobre por qué (evitar que el cajero confunda devolver con
 * cobrar), y sigue con confirmación en dos pasos antes de ejecutar nada.
 */
export default function DevolucionesScreen({ onVolverAlPos }) {
  const [fecha, setFecha] = useState(hoyISO());
  const [ventasDelDia, setVentasDelDia] = useState([]);
  const [cargandoLista, setCargandoLista] = useState(true);

  const [ventaSeleccionada, setVentaSeleccionada] = useState(null);
  const [motivo, setMotivo] = useState("");
  const [confirmando, setConfirmando] = useState(false);
  const [procesando, setProcesando] = useState(false);
  const [resultado, setResultado] = useState(null);
  const [error, setError] = useState(null);

  const cargarVentasDelDia = async (fechaBuscar) => {
    setCargandoLista(true);
    setError(null);
    try {
      const ventas = await ventasApi.listar({ fecha: fechaBuscar });
      setVentasDelDia(ventas);
    } catch (err) {
      setError(err.message);
    } finally {
      setCargandoLista(false);
    }
  };

  useEffect(() => {
    cargarVentasDelDia(fecha);
    setVentaSeleccionada(null);
    setResultado(null);
    setConfirmando(false);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [fecha]);

  const seleccionarVenta = (venta) => {
    if (venta.estado === "ANULADA") return; // ya devuelta, no se puede seleccionar
    setVentaSeleccionada(venta);
    setMotivo("");
    setConfirmando(false);
    setError(null);
  };

  const confirmarDevolucion = async () => {
    if (!confirmando) {
      setConfirmando(true);
      return;
    }
    if (!motivo.trim()) {
      setError("Debes indicar el motivo de la devolución");
      return;
    }

    setProcesando(true);
    setError(null);
    try {
      const devolucion = await devolucionesApi.crear({
        venta_id: ventaSeleccionada.id,
        motivo: motivo.trim(),
      });
      setResultado(devolucion);
      setVentaSeleccionada(null);
      setMotivo("");
      setConfirmando(false);
      await cargarVentasDelDia(fecha); // refresca la lista para que se vea "Devuelta" de una vez
    } catch (err) {
      setError(err.message);
    } finally {
      setProcesando(false);
    }
  };

  return (
    <div className="devoluciones-screen">
      <header className="devoluciones-screen__topbar">
        <button
          type="button"
          className="devoluciones-screen__volver"
          onClick={onVolverAlPos}
        >
          <ArrowLeft size={16} strokeWidth={2} />
          Volver al POS
        </button>
        <span className="devoluciones-screen__marca">
          <RotateCcw size={16} strokeWidth={2} />
          TramaPos · Devoluciones
        </span>
      </header>

      <div className="devoluciones-screen__cuerpo">
        {error && (
          <p className="devoluciones-screen__error">
            <AlertTriangle size={14} strokeWidth={2} />
            {error}
          </p>
        )}

        {resultado && (
          <div className="devoluciones-screen__resultado">
            <CheckCircle2 size={18} strokeWidth={2} />
            <div>
              <p>
                <strong>Devolución #{resultado.id} registrada.</strong>
              </p>
              <p>
                Se repuso el stock y se revirtieron los puntos de fidelización
                de la venta #{resultado.venta_id}. Monto devuelto:{" "}
                <span className="u-cifra">
                  ${resultado.monto_devuelto.toLocaleString("es-CO")}
                </span>
              </p>
            </div>
          </div>
        )}

        {!ventaSeleccionada && (
          <>
            <div className="devoluciones-screen__filtro-fecha">
              <Calendar size={16} strokeWidth={2} />
              <input
                type="date"
                value={fecha}
                onChange={(e) => setFecha(e.target.value)}
              />
              <button
                type="button"
                className={
                  fecha === hoyISO() ? "devoluciones-screen__chip--activo" : ""
                }
                onClick={() => setFecha(hoyISO())}
              >
                Hoy
              </button>
              <button
                type="button"
                className={
                  fecha === ayerISO() ? "devoluciones-screen__chip--activo" : ""
                }
                onClick={() => setFecha(ayerISO())}
              >
                Ayer
              </button>
            </div>

            {cargandoLista ? (
              <SkeletonFilas filas={4} columnas={3} />
            ) : ventasDelDia.length === 0 ? (
              <p className="devoluciones-screen__estado">
                No hay ventas registradas ese día.
              </p>
            ) : (
              <ul className="devoluciones-screen__lista-ventas">
                {ventasDelDia.map((venta) => (
                  <li key={venta.id}>
                    <button
                      type="button"
                      disabled={venta.estado === "ANULADA"}
                      className="devoluciones-screen__venta-item"
                      onClick={() => seleccionarVenta(venta)}
                    >
                      <span className="devoluciones-screen__venta-item-hora u-cifra">
                        {new Date(venta.creado_en).toLocaleTimeString("es-CO", {
                          hour: "2-digit",
                          minute: "2-digit",
                        })}
                      </span>
                      <span className="devoluciones-screen__venta-item-info">
                        Venta #{venta.id} · {venta.canal} ·{" "}
                        {ETIQUETAS_METODO_PAGO[venta.metodo_pago]}
                      </span>
                      <span className="u-cifra devoluciones-screen__venta-item-total">
                        ${venta.total.toLocaleString("es-CO")}
                      </span>
                      {venta.estado === "ANULADA" && (
                        <span className="devoluciones-screen__venta-item-badge">
                          Devuelta
                        </span>
                      )}
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </>
        )}

        {ventaSeleccionada && (
          <div className="devoluciones-screen__venta">
            <button
              type="button"
              className="devoluciones-screen__cambiar-venta"
              onClick={() => setVentaSeleccionada(null)}
            >
              <ArrowLeft size={14} strokeWidth={2} />
              Elegir otra venta
            </button>

            <div className="devoluciones-screen__venta-header">
              <div>
                <p className="devoluciones-screen__venta-titulo">
                  Venta #{ventaSeleccionada.id}
                </p>
                <p className="devoluciones-screen__venta-fecha">
                  {new Date(ventaSeleccionada.creado_en).toLocaleString(
                    "es-CO",
                  )}{" "}
                  · {ETIQUETAS_METODO_PAGO[ventaSeleccionada.metodo_pago]} ·
                  Canal {ventaSeleccionada.canal}
                </p>
              </div>
              <span className="u-cifra devoluciones-screen__venta-total">
                ${ventaSeleccionada.total.toLocaleString("es-CO")}
              </span>
            </div>

            <ul className="devoluciones-screen__lineas">
              {ventaSeleccionada.detalles.map((d, i) => (
                <li key={i}>
                  <span>
                    {d.cantidad} × {d.producto_nombre}
                    {d.color ? ` · ${d.color}` : ""}
                    {d.grosor ? ` · ${d.grosor}` : ""}
                  </span>
                  <span className="u-cifra">
                    ${(d.cantidad * d.precio_unitario).toLocaleString("es-CO")}
                  </span>
                </li>
              ))}
            </ul>

            <input
              type="text"
              className="devoluciones-screen__motivo"
              placeholder="Motivo de la devolución (obligatorio)"
              value={motivo}
              onChange={(e) => setMotivo(e.target.value)}
            />

            <button
              type="button"
              className={`devoluciones-screen__confirmar ${
                confirmando ? "devoluciones-screen__confirmar--paso2" : ""
              }`}
              disabled={procesando}
              onClick={confirmarDevolucion}
            >
              {procesando
                ? "Procesando…"
                : confirmando
                  ? "¿Seguro? Click de nuevo para confirmar"
                  : "Devolver esta venta"}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
