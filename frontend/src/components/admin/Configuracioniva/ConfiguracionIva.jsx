import React, { useEffect, useState } from "react";
import { Percent, AlertTriangle } from "lucide-react";

import { configuracionEmpresaApi } from "../../../services/api";
import "./ConfiguracionIVA.scss";

export default function ConfiguracionIVA() {
  const [config, setConfig] = useState(null);
  const [aplicaIva, setAplicaIva] = useState(false);
  const [porcentajeDefault, setPorcentajeDefault] = useState("19");
  const [cargando, setCargando] = useState(true);
  const [guardando, setGuardando] = useState(false);
  const [error, setError] = useState(null);
  const [confirmandoActivacion, setConfirmandoActivacion] = useState(false);

  const cargar = async () => {
    try {
      const c = await configuracionEmpresaApi.obtener();
      setConfig(c);
      setAplicaIva(c.aplica_iva);
      setPorcentajeDefault(String(c.porcentaje_iva_default));
    } catch (err) {
      setError(err.message);
    } finally {
      setCargando(false);
    }
  };

  useEffect(() => {
    cargar();
  }, []);

  const alternarInterruptor = () => {
    // Activar IVA es un cambio importante (empieza a discriminarse en cada
    // venta nueva) — pedimos confirmación en dos pasos solo para PRENDERLO.
    // Apagarlo no necesita confirmación, es la opción segura.
    if (!aplicaIva) {
      setConfirmandoActivacion(true);
      return;
    }
    setAplicaIva(false);
  };

  const confirmarActivacion = () => {
    setAplicaIva(true);
    setConfirmandoActivacion(false);
  };

  const guardar = async () => {
    setGuardando(true);
    setError(null);
    try {
      const actualizado = await configuracionEmpresaApi.actualizar({
        aplica_iva: aplicaIva,
        porcentaje_iva_default: Number(porcentajeDefault) || 0,
      });
      setConfig(actualizado);
    } catch (err) {
      setError(err.message);
    } finally {
      setGuardando(false);
    }
  };

  if (cargando) return <p className="config-iva__estado">Cargando…</p>;

  return (
    <div className="config-iva">
      <h2 className="config-iva__titulo">
        <Percent size={18} strokeWidth={2} />
        Configuración de IVA
      </h2>

      <p className="config-iva__ayuda">
        Mientras el negocio sea persona natural no obligada a declarar IVA, deja
        este interruptor <strong>apagado</strong> — el sistema sigue funcionando
        exactamente igual que hoy. El día que se constituyan como empresa y
        queden obligados, actívalo aquí mismo, sin necesidad de tocar nada más.
      </p>

      {error && <p className="config-iva__error">{error}</p>}

      <div className="config-iva__interruptor-fila">
        <button
          type="button"
          className={`config-iva__interruptor ${aplicaIva ? "config-iva__interruptor--activo" : ""}`}
          onClick={alternarInterruptor}
        >
          <span className="config-iva__interruptor-bola" />
        </button>
        <span>
          {aplicaIva
            ? "IVA activo — se discrimina en cada venta"
            : "IVA inactivo (recomendado por ahora)"}
        </span>
      </div>

      {confirmandoActivacion && (
        <div className="config-iva__confirmacion">
          <AlertTriangle size={16} strokeWidth={2} />
          <div>
            <p>
              Vas a activar el IVA. A partir de guardar, cada venta nueva va a
              discriminar el impuesto (el precio que paga el cliente no cambia,
              solo se reporta el desglose).
            </p>
            <div className="config-iva__confirmacion-botones">
              <button type="button" onClick={confirmarActivacion}>
                Sí, activar
              </button>
              <button
                type="button"
                onClick={() => setConfirmandoActivacion(false)}
              >
                Cancelar
              </button>
            </div>
          </div>
        </div>
      )}

      <label className="config-iva__campo">
        % IVA por defecto para productos nuevos
        <input
          type="number"
          min="0"
          max="100"
          value={porcentajeDefault}
          onChange={(e) => setPorcentajeDefault(e.target.value)}
        />
      </label>

      <p className="config-iva__nota">
        Cada producto puede tener su propio % de IVA (editable en la pestaña
        Productos) — este valor es solo el que se sugiere por defecto al crear
        uno nuevo.
      </p>

      <button
        type="button"
        className="config-iva__guardar"
        disabled={guardando}
        onClick={guardar}
      >
        {guardando ? "Guardando…" : "Guardar cambios"}
      </button>

      {config && (
        <p className="config-iva__estado-actual">
          Estado guardado actualmente:{" "}
          <strong>{config.aplica_iva ? "Activo" : "Inactivo"}</strong>
        </p>
      )}
    </div>
  );
}
