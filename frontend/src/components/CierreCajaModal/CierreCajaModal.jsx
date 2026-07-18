import React, { useEffect, useState } from "react";
import { X, Lock, CheckCircle2 } from "lucide-react";

import { cajaApi } from "../../services/api";
import "./CierreCajaModal.scss";

/**
 * CierreCajaModal
 * Arqueo de caja: muestra cuánto DEBERÍA haber en efectivo según el
 * sistema (apertura + ventas en efectivo de la sesión), para que el
 * cajero cuente la caja física y lo compare antes de confirmar. Misma
 * confirmación en dos pasos que usamos en Devoluciones — cerrar caja
 * no se puede deshacer, así que un solo click nunca alcanza.
 */
export default function CierreCajaModal({ sesion, onCerrar, onCajaCerrada }) {
  const [preview, setPreview] = useState(null);
  const [cargandoPreview, setCargandoPreview] = useState(true);
  const [montoReal, setMontoReal] = useState("");
  const [confirmando, setConfirmando] = useState(false);
  const [procesando, setProcesando] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    cajaApi
      .previewCierre(sesion.id)
      .then(setPreview)
      .catch((err) => setError(err.message))
      .finally(() => setCargandoPreview(false));
  }, [sesion.id]);

  const diferencia = preview
    ? Number(montoReal || 0) - preview.monto_cierre_esperado
    : 0;

  const confirmarCierre = async () => {
    if (!confirmando) {
      setConfirmando(true);
      return;
    }
    setProcesando(true);
    setError(null);
    try {
      const sesionCerrada = await cajaApi.cerrar(sesion.id, {
        monto_cierre_real: Number(montoReal) || 0,
      });
      onCajaCerrada?.(sesionCerrada);
    } catch (err) {
      setError(err.message);
      setConfirmando(false);
    } finally {
      setProcesando(false);
    }
  };

  return (
    <div className="cierre-caja__overlay" onClick={onCerrar}>
      <div className="cierre-caja" onClick={(e) => e.stopPropagation()}>
        <header className="cierre-caja__header">
          <h2 className="cierre-caja__title">
            <Lock size={18} strokeWidth={2} />
            Cerrar caja #{sesion.id}
          </h2>
          <button
            type="button"
            className="cierre-caja__cerrar"
            onClick={onCerrar}
          >
            <X size={18} strokeWidth={2} />
          </button>
        </header>

        {cargandoPreview ? (
          <p className="cierre-caja__estado">Calculando arqueo…</p>
        ) : (
          preview && (
            <div className="cierre-caja__resumen">
              <div className="cierre-caja__resumen-fila">
                <span>Monto de apertura</span>
                <span className="u-cifra">
                  ${preview.monto_apertura.toLocaleString("es-CO")}
                </span>
              </div>
              <div className="cierre-caja__resumen-fila cierre-caja__resumen-fila--destacada">
                <span>Efectivo esperado en caja</span>
                <span className="u-cifra">
                  ${preview.monto_cierre_esperado.toLocaleString("es-CO")}
                </span>
              </div>
              <p className="cierre-caja__ayuda">
                Cuenta el efectivo físico del cajón y escribe el total abajo.
              </p>
            </div>
          )
        )}

        {error && <p className="cierre-caja__error">{error}</p>}

        <input
          type="number"
          min="0"
          className="cierre-caja__input"
          placeholder="Monto real contado"
          value={montoReal}
          onChange={(e) => {
            setMontoReal(e.target.value);
            setConfirmando(false);
          }}
        />

        {montoReal !== "" && preview && (
          <div
            className={`cierre-caja__diferencia ${
              diferencia === 0
                ? "cierre-caja__diferencia--exacta"
                : diferencia > 0
                  ? "cierre-caja__diferencia--sobrante"
                  : "cierre-caja__diferencia--faltante"
            }`}
          >
            {diferencia === 0 ? (
              <>
                <CheckCircle2 size={16} strokeWidth={2} />
                <span>Caja cuadrada exacta</span>
              </>
            ) : (
              <span>
                {diferencia > 0 ? "Sobran" : "Faltan"} $
                {Math.abs(diferencia).toLocaleString("es-CO")}
              </span>
            )}
          </div>
        )}

        <button
          type="button"
          className={`cierre-caja__confirmar ${
            confirmando ? "cierre-caja__confirmar--paso2" : ""
          }`}
          disabled={procesando || montoReal === ""}
          onClick={confirmarCierre}
        >
          {procesando
            ? "Cerrando…"
            : confirmando
              ? "¿Seguro? Click de nuevo para confirmar"
              : "Cerrar caja"}
        </button>
      </div>
    </div>
  );
}
