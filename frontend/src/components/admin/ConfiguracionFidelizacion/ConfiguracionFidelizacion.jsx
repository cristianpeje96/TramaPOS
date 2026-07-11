import React, { useEffect, useState } from "react";
import { Settings2, Award, Plus, Pencil, Check, X } from "lucide-react";

import { fidelizacionApi } from "../../../services/api";
import "./ConfiguracionFidelizacion.scss";

const RANGO_VACIO = {
  nombre: "",
  puntos_minimo: "",
  puntos_maximo: "",
  porcentaje_descuento: "",
};

export default function ConfiguracionFidelizacion() {
  // --- Configuración de puntos por compra ---
  const [config, setConfig] = useState(null);
  const [pesosPorPunto, setPesosPorPunto] = useState("");
  const [valorPuntoRedimido, setValorPuntoRedimido] = useState("");
  const [guardandoConfig, setGuardandoConfig] = useState(false);

  // --- Rangos de descuento ---
  const [rangos, setRangos] = useState([]);
  const [cargandoRangos, setCargandoRangos] = useState(true);
  const [mostrarFormularioRango, setMostrarFormularioRango] = useState(false);
  const [nuevoRango, setNuevoRango] = useState({ ...RANGO_VACIO });
  const [rangoEditandoId, setRangoEditandoId] = useState(null);
  const [rangoEdicion, setRangoEdicion] = useState({ ...RANGO_VACIO });
  const [guardando, setGuardando] = useState(false);

  const [error, setError] = useState(null);

  const cargarTodo = async () => {
    try {
      const [configuracion, listaRangos] = await Promise.all([
        fidelizacionApi.configuracion(),
        fidelizacionApi.rangos.listar(),
      ]);
      setConfig(configuracion);
      setPesosPorPunto(String(configuracion.pesos_por_punto));
      setValorPuntoRedimido(String(configuracion.valor_punto_redimido));
      setRangos(listaRangos);
    } catch (err) {
      setError(err.message);
    } finally {
      setCargandoRangos(false);
    }
  };

  useEffect(() => {
    cargarTodo();
  }, []);

  const guardarConfig = async () => {
    setGuardandoConfig(true);
    setError(null);
    try {
      const actualizado = await fidelizacionApi.actualizarConfiguracion({
        pesos_por_punto: Number(pesosPorPunto),
        valor_punto_redimido: Number(valorPuntoRedimido),
      });
      setConfig(actualizado);
    } catch (err) {
      setError(err.message);
    } finally {
      setGuardandoConfig(false);
    }
  };

  const crearRango = async () => {
    if (
      !nuevoRango.nombre.trim() ||
      nuevoRango.puntos_minimo === "" ||
      nuevoRango.porcentaje_descuento === ""
    ) {
      setError("Nombre, puntos mínimo y porcentaje son obligatorios");
      return;
    }
    setGuardando(true);
    setError(null);
    try {
      await fidelizacionApi.rangos.crear({
        nombre: nuevoRango.nombre.trim(),
        puntos_minimo: Number(nuevoRango.puntos_minimo),
        puntos_maximo:
          nuevoRango.puntos_maximo === ""
            ? null
            : Number(nuevoRango.puntos_maximo),
        porcentaje_descuento: Number(nuevoRango.porcentaje_descuento),
      });
      setNuevoRango({ ...RANGO_VACIO });
      setMostrarFormularioRango(false);
      setRangos(await fidelizacionApi.rangos.listar());
    } catch (err) {
      setError(err.message);
    } finally {
      setGuardando(false);
    }
  };

  const iniciarEdicionRango = (rango) => {
    setRangoEditandoId(rango.id);
    setRangoEdicion({
      nombre: rango.nombre,
      puntos_minimo: rango.puntos_minimo,
      puntos_maximo: rango.puntos_maximo ?? "",
      porcentaje_descuento: rango.porcentaje_descuento,
    });
  };

  const guardarEdicionRango = async () => {
    setGuardando(true);
    setError(null);
    try {
      await fidelizacionApi.rangos.actualizar(rangoEditandoId, {
        nombre: rangoEdicion.nombre.trim(),
        puntos_minimo: Number(rangoEdicion.puntos_minimo),
        puntos_maximo:
          rangoEdicion.puntos_maximo === ""
            ? null
            : Number(rangoEdicion.puntos_maximo),
        porcentaje_descuento: Number(rangoEdicion.porcentaje_descuento),
      });
      setRangoEditandoId(null);
      setRangos(await fidelizacionApi.rangos.listar());
    } catch (err) {
      setError(err.message);
    } finally {
      setGuardando(false);
    }
  };

  const alternarActivoRango = async (rango) => {
    setError(null);
    try {
      await fidelizacionApi.rangos.actualizar(rango.id, {
        activo: !rango.activo,
      });
      setRangos(await fidelizacionApi.rangos.listar());
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <div className="config-fidelizacion">
      <section className="config-fidelizacion__seccion">
        <h2 className="config-fidelizacion__titulo">
          <Settings2 size={18} strokeWidth={2} />
          Puntos por compra
        </h2>
        <p className="config-fidelizacion__ayuda">
          Define cuántos puntos gana un cliente por cada compra, y cuánto vale 1
          punto al redimirlo (atajo F9 en el POS).
        </p>
        <div className="config-fidelizacion__form-puntos">
          <label>
            $ por cada punto ganado
            <input
              type="number"
              min="0"
              value={pesosPorPunto}
              onChange={(e) => setPesosPorPunto(e.target.value)}
            />
          </label>
          <label>
            Valor de 1 punto al redimir ($)
            <input
              type="number"
              min="0"
              value={valorPuntoRedimido}
              onChange={(e) => setValorPuntoRedimido(e.target.value)}
            />
          </label>
          <button
            type="button"
            disabled={guardandoConfig}
            onClick={guardarConfig}
          >
            {guardandoConfig ? "Guardando…" : "Guardar"}
          </button>
        </div>
        {config && (
          <p className="config-fidelizacion__ejemplo">
            Ejemplo actual: una compra de $10.000 gana{" "}
            <strong>
              {Math.floor(
                10000 / Number(pesosPorPunto || config.pesos_por_punto),
              )}
            </strong>{" "}
            puntos · 100 puntos redimidos valen{" "}
            <strong>
              $
              {(
                100 * Number(valorPuntoRedimido || config.valor_punto_redimido)
              ).toLocaleString("es-CO")}
            </strong>
          </p>
        )}
      </section>

      <section className="config-fidelizacion__seccion">
        <header className="config-fidelizacion__header-rangos">
          <h2 className="config-fidelizacion__titulo">
            <Award size={18} strokeWidth={2} />
            Rangos de descuento (niveles de fidelización)
          </h2>
          <button
            type="button"
            onClick={() => setMostrarFormularioRango((v) => !v)}
          >
            <Plus size={14} strokeWidth={2} />
            {mostrarFormularioRango ? "Cancelar" : "Nuevo rango"}
          </button>
        </header>
        <p className="config-fidelizacion__ayuda">
          Se calculan sobre los puntos históricos del cliente (nunca bajan al
          redimir). El descuento se aplica automáticamente en cada venta, sumado
          a los demás descuentos.
        </p>

        {error && <p className="config-fidelizacion__error">{error}</p>}

        {mostrarFormularioRango && (
          <div className="config-fidelizacion__fila-form">
            <input
              type="text"
              placeholder="Nombre (ej: Platino)"
              value={nuevoRango.nombre}
              onChange={(e) =>
                setNuevoRango({ ...nuevoRango, nombre: e.target.value })
              }
            />
            <input
              type="number"
              min="0"
              placeholder="Puntos mínimo"
              value={nuevoRango.puntos_minimo}
              onChange={(e) =>
                setNuevoRango({ ...nuevoRango, puntos_minimo: e.target.value })
              }
            />
            <input
              type="number"
              min="0"
              placeholder="Puntos máximo (vacío = sin techo)"
              value={nuevoRango.puntos_maximo}
              onChange={(e) =>
                setNuevoRango({ ...nuevoRango, puntos_maximo: e.target.value })
              }
            />
            <input
              type="number"
              min="0"
              max="100"
              placeholder="% descuento"
              value={nuevoRango.porcentaje_descuento}
              onChange={(e) =>
                setNuevoRango({
                  ...nuevoRango,
                  porcentaje_descuento: e.target.value,
                })
              }
            />
            <button type="button" disabled={guardando} onClick={crearRango}>
              <Check size={14} strokeWidth={2} />
              Crear
            </button>
          </div>
        )}

        {cargandoRangos ? (
          <p className="config-fidelizacion__estado">Cargando…</p>
        ) : (
          <table className="config-fidelizacion__tabla">
            <thead>
              <tr>
                <th>Rango</th>
                <th>Puntos mínimo</th>
                <th>Puntos máximo</th>
                <th>% descuento</th>
                <th>Activo</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {rangos.map((rango) =>
                rangoEditandoId === rango.id ? (
                  <tr key={rango.id}>
                    <td>
                      <input
                        type="text"
                        value={rangoEdicion.nombre}
                        onChange={(e) =>
                          setRangoEdicion({
                            ...rangoEdicion,
                            nombre: e.target.value,
                          })
                        }
                      />
                    </td>
                    <td>
                      <input
                        type="number"
                        min="0"
                        value={rangoEdicion.puntos_minimo}
                        onChange={(e) =>
                          setRangoEdicion({
                            ...rangoEdicion,
                            puntos_minimo: e.target.value,
                          })
                        }
                      />
                    </td>
                    <td>
                      <input
                        type="number"
                        min="0"
                        value={rangoEdicion.puntos_maximo}
                        onChange={(e) =>
                          setRangoEdicion({
                            ...rangoEdicion,
                            puntos_maximo: e.target.value,
                          })
                        }
                      />
                    </td>
                    <td>
                      <input
                        type="number"
                        min="0"
                        max="100"
                        value={rangoEdicion.porcentaje_descuento}
                        onChange={(e) =>
                          setRangoEdicion({
                            ...rangoEdicion,
                            porcentaje_descuento: e.target.value,
                          })
                        }
                      />
                    </td>
                    <td>—</td>
                    <td className="config-fidelizacion__acciones-fila">
                      <button
                        type="button"
                        disabled={guardando}
                        onClick={guardarEdicionRango}
                      >
                        <Check size={14} strokeWidth={2} />
                      </button>
                      <button
                        type="button"
                        onClick={() => setRangoEditandoId(null)}
                      >
                        <X size={14} strokeWidth={2} />
                      </button>
                    </td>
                  </tr>
                ) : (
                  <tr
                    key={rango.id}
                    className={
                      !rango.activo ? "config-fidelizacion__fila--inactiva" : ""
                    }
                  >
                    <td>{rango.nombre}</td>
                    <td className="u-cifra">{rango.puntos_minimo}</td>
                    <td className="u-cifra">
                      {rango.puntos_maximo ?? "Sin techo"}
                    </td>
                    <td className="u-cifra">{rango.porcentaje_descuento}%</td>
                    <td>
                      <button
                        type="button"
                        className="config-fidelizacion__toggle-activo"
                        onClick={() => alternarActivoRango(rango)}
                      >
                        {rango.activo ? "Sí" : "No"}
                      </button>
                    </td>
                    <td className="config-fidelizacion__acciones-fila">
                      <button
                        type="button"
                        onClick={() => iniciarEdicionRango(rango)}
                      >
                        <Pencil size={14} strokeWidth={2} />
                      </button>
                    </td>
                  </tr>
                ),
              )}
            </tbody>
          </table>
        )}
      </section>
    </div>
  );
}
