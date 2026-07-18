import React, { useEffect, useState } from "react";
import { Plus, Store, CircleDot } from "lucide-react";

import { cajaApi, cajasFisicasApi } from "../../../services/api";
import { SkeletonFilas } from "../../Skeleton/Skeleton";
import "./CajasFisicasAdmin.scss";

export default function CajasFisicasAdmin() {
  const [cajas, setCajas] = useState([]);
  const [sesionesAbiertas, setSesionesAbiertas] = useState([]);
  const [cargando, setCargando] = useState(true);
  const [nombreNuevo, setNombreNuevo] = useState("");
  const [guardando, setGuardando] = useState(false);
  const [error, setError] = useState(null);

  const cargar = async () => {
    setCargando(true);
    try {
      const [listaCajas, listaSesiones] = await Promise.all([
        cajasFisicasApi.listar(),
        cajaApi.sesionesAbiertas(),
      ]);
      setCajas(listaCajas);
      setSesionesAbiertas(listaSesiones);
    } catch (err) {
      setError(err.message);
    } finally {
      setCargando(false);
    }
  };

  useEffect(() => {
    cargar();
  }, []);

  const crearCaja = async () => {
    if (!nombreNuevo.trim()) return;
    setGuardando(true);
    setError(null);
    try {
      await cajasFisicasApi.crear({ nombre: nombreNuevo.trim() });
      setNombreNuevo("");
      await cargar();
    } catch (err) {
      setError(err.message);
    } finally {
      setGuardando(false);
    }
  };

  const sesionDe = (cajaId) =>
    sesionesAbiertas.find((s) => s.caja_fisica_id === cajaId);

  return (
    <div className="cajas-fisicas-admin">
      <h2 className="cajas-fisicas-admin__titulo">
        <Store size={18} strokeWidth={2} />
        Cajas físicas
      </h2>
      <p className="cajas-fisicas-admin__ayuda">
        Cada registradora de la tienda es una "caja física" — cada una puede
        tener su propia sesión abierta al mismo tiempo, sin pisarse entre ellas.
      </p>

      {error && <p className="cajas-fisicas-admin__error">{error}</p>}

      <div className="cajas-fisicas-admin__crear">
        <input
          type="text"
          placeholder="Nombre (ej: Caja 2, Mostrador principal)"
          value={nombreNuevo}
          onChange={(e) => setNombreNuevo(e.target.value)}
        />
        <button type="button" disabled={guardando} onClick={crearCaja}>
          <Plus size={14} strokeWidth={2} />
          {guardando ? "Creando…" : "Crear caja física"}
        </button>
      </div>

      {cargando ? (
        <SkeletonFilas filas={2} columnas={3} />
      ) : (
        <div className="cajas-fisicas-admin__lista">
          {cajas.map((caja) => {
            const sesion = sesionDe(caja.id);
            return (
              <div key={caja.id} className="cajas-fisicas-admin__item">
                <span className="cajas-fisicas-admin__item-nombre">
                  {caja.nombre}
                </span>
                {sesion ? (
                  <span className="cajas-fisicas-admin__estado cajas-fisicas-admin__estado--abierta">
                    <CircleDot size={13} strokeWidth={2} />
                    Sesión abierta (#{sesion.id})
                  </span>
                ) : (
                  <span className="cajas-fisicas-admin__estado cajas-fisicas-admin__estado--cerrada">
                    Sin sesión abierta
                  </span>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
