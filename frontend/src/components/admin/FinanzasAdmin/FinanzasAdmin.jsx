import React, { useEffect, useState } from "react";
import { Wallet, Plus, Trash2, TrendingUp, TrendingDown } from "lucide-react";

import { finanzasApi } from "../../../services/api";
import { SkeletonFilas } from "../../Skeleton/Skeleton";
import "./FinanzasAdmin.scss";

const MESES = [
  "Ene",
  "Feb",
  "Mar",
  "Abr",
  "May",
  "Jun",
  "Jul",
  "Ago",
  "Sep",
  "Oct",
  "Nov",
  "Dic",
];
const hoyISO = () => new Date().toISOString().slice(0, 10);

export default function FinanzasAdmin() {
  const [categorias, setCategorias] = useState([]);
  const [nombreCategoria, setNombreCategoria] = useState("");
  const [tipoCategoria, setTipoCategoria] = useState("GASTO");
  const [creandoCategoria, setCreandoCategoria] = useState(false);

  const [categoriaMovId, setCategoriaMovId] = useState("");
  const [fechaMov, setFechaMov] = useState(hoyISO());
  const [descripcionMov, setDescripcionMov] = useState("");
  const [montoMov, setMontoMov] = useState("");
  const [guardandoMov, setGuardandoMov] = useState(false);

  const [movimientos, setMovimientos] = useState([]);
  const [cargandoMovimientos, setCargandoMovimientos] = useState(true);

  const [anio, setAnio] = useState(new Date().getFullYear());
  const [pyg, setPyg] = useState(null);
  const [cargandoPyg, setCargandoPyg] = useState(true);

  const [error, setError] = useState(null);

  const cargarCategorias = async () => {
    try {
      setCategorias(await finanzasApi.listarCategorias());
    } catch (err) {
      setError(err.message);
    }
  };

  const cargarMovimientos = async () => {
    setCargandoMovimientos(true);
    try {
      setMovimientos(await finanzasApi.listarMovimientos());
    } catch (err) {
      setError(err.message);
    } finally {
      setCargandoMovimientos(false);
    }
  };

  const cargarPyg = async (anioConsulta) => {
    setCargandoPyg(true);
    try {
      setPyg(await finanzasApi.perdidasGanancias(anioConsulta));
    } catch (err) {
      setError(err.message);
    } finally {
      setCargandoPyg(false);
    }
  };

  useEffect(() => {
    cargarCategorias();
    cargarMovimientos();
  }, []);

  useEffect(() => {
    cargarPyg(anio);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [anio]);

  const crearCategoria = async () => {
    if (!nombreCategoria.trim()) return;
    setCreandoCategoria(true);
    setError(null);
    try {
      const categoria = await finanzasApi.crearCategoria({
        nombre: nombreCategoria.trim(),
        tipo: tipoCategoria,
      });
      setCategorias((prev) =>
        [...prev, categoria].sort((a, b) => a.nombre.localeCompare(b.nombre)),
      );
      setNombreCategoria("");
    } catch (err) {
      setError(err.message);
    } finally {
      setCreandoCategoria(false);
    }
  };

  const registrarMovimiento = async () => {
    if (!categoriaMovId || !montoMov) return;
    setGuardandoMov(true);
    setError(null);
    try {
      await finanzasApi.crearMovimiento({
        categoria_id: Number(categoriaMovId),
        fecha: fechaMov,
        descripcion: descripcionMov.trim() || null,
        monto: Number(montoMov),
      });
      setDescripcionMov("");
      setMontoMov("");
      await cargarMovimientos();
      await cargarPyg(anio);
    } catch (err) {
      setError(err.message);
    } finally {
      setGuardandoMov(false);
    }
  };

  const borrarMovimiento = async (id) => {
    try {
      await finanzasApi.eliminarMovimiento(id);
      await cargarMovimientos();
      await cargarPyg(anio);
    } catch (err) {
      setError(err.message);
    }
  };

  const filaTabla = (fila) => (
    <tr key={fila.nombre}>
      <td>{fila.nombre}</td>
      {fila.valores_por_mes.map((v, i) => (
        <td key={i} className="u-cifra">
          {v ? `$${v.toLocaleString("es-CO")}` : "—"}
        </td>
      ))}
      <td className="u-cifra finanzas-admin__col-total">
        ${fila.total.toLocaleString("es-CO")}
      </td>
    </tr>
  );

  const filaTotales = (nombre, valores, icono) => {
    const total = valores.reduce((s, v) => s + v, 0);
    return (
      <tr className="finanzas-admin__fila--total" key={nombre}>
        <td>
          {icono} {nombre}
        </td>
        {valores.map((v, i) => (
          <td key={i} className="u-cifra">
            {v ? `$${v.toLocaleString("es-CO")}` : "—"}
          </td>
        ))}
        <td className="u-cifra finanzas-admin__col-total">
          ${total.toLocaleString("es-CO")}
        </td>
      </tr>
    );
  };

  return (
    <div className="finanzas-admin">
      <h2 className="finanzas-admin__titulo">
        <Wallet size={18} strokeWidth={2} />
        Finanzas
      </h2>
      <p className="finanzas-admin__ayuda">
        Registra aquí todo lo que NO sea venta ni compra de mercancía (esas ya
        se llevan solas) — arriendo, servicios, retiros, préstamos, etc. El
        reporte de Pérdidas y Ganancias de abajo las combina automáticamente con
        tus ventas y compras reales.
      </p>

      {error && <p className="finanzas-admin__error">{error}</p>}

      {/* --- Categorías --- */}
      <div className="finanzas-admin__seccion">
        <h3>Categorías</h3>
        <div className="finanzas-admin__form-categoria">
          <input
            type="text"
            placeholder="Nombre (ej: Arriendo, Servicios públicos, Retiro socio)"
            value={nombreCategoria}
            onChange={(e) => setNombreCategoria(e.target.value)}
          />
          <select
            value={tipoCategoria}
            onChange={(e) => setTipoCategoria(e.target.value)}
          >
            <option value="GASTO">Gasto</option>
            <option value="INGRESO">Ingreso</option>
          </select>
          <button
            type="button"
            disabled={creandoCategoria}
            onClick={crearCategoria}
          >
            <Plus size={14} strokeWidth={2} />
            {creandoCategoria ? "Creando…" : "Crear categoría"}
          </button>
        </div>
        <div className="finanzas-admin__chips">
          {categorias.map((c) => (
            <span
              key={c.id}
              className={`finanzas-admin__chip finanzas-admin__chip--${c.tipo.toLowerCase()}`}
            >
              {c.nombre}
            </span>
          ))}
        </div>
      </div>

      {/* --- Registrar movimiento --- */}
      <div className="finanzas-admin__seccion">
        <h3>Registrar movimiento</h3>
        <div className="finanzas-admin__form-movimiento">
          <select
            value={categoriaMovId}
            onChange={(e) => setCategoriaMovId(e.target.value)}
          >
            <option value="">Categoría…</option>
            {categorias.map((c) => (
              <option key={c.id} value={c.id}>
                {c.nombre} ({c.tipo === "INGRESO" ? "Ingreso" : "Gasto"})
              </option>
            ))}
          </select>
          <input
            type="date"
            value={fechaMov}
            onChange={(e) => setFechaMov(e.target.value)}
          />
          <input
            type="text"
            placeholder="Descripción (opcional)"
            value={descripcionMov}
            onChange={(e) => setDescripcionMov(e.target.value)}
          />
          <input
            type="number"
            min="0"
            placeholder="Monto"
            value={montoMov}
            onChange={(e) => setMontoMov(e.target.value)}
          />
          <button
            type="button"
            disabled={guardandoMov || !categoriaMovId || !montoMov}
            onClick={registrarMovimiento}
          >
            {guardandoMov ? "Guardando…" : "Registrar"}
          </button>
        </div>

        {cargandoMovimientos ? (
          <SkeletonFilas filas={3} columnas={4} />
        ) : (
          <table className="finanzas-admin__tabla-movimientos">
            <thead>
              <tr>
                <th>Fecha</th>
                <th>Categoría</th>
                <th>Descripción</th>
                <th>Monto</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {movimientos.map((m) => (
                <tr key={m.id}>
                  <td className="u-cifra">{m.fecha}</td>
                  <td>{m.categoria_nombre}</td>
                  <td>{m.descripcion || "—"}</td>
                  <td
                    className={`u-cifra finanzas-admin__monto finanzas-admin__monto--${m.categoria_tipo.toLowerCase()}`}
                  >
                    {m.categoria_tipo === "INGRESO" ? "+" : "−"}$
                    {m.monto.toLocaleString("es-CO")}
                  </td>
                  <td>
                    <button
                      type="button"
                      onClick={() => borrarMovimiento(m.id)}
                    >
                      <Trash2 size={13} strokeWidth={2} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* --- Pérdidas y Ganancias --- */}
      <div className="finanzas-admin__seccion">
        <div className="finanzas-admin__pyg-header">
          <h3>Pérdidas y Ganancias</h3>
          <select
            value={anio}
            onChange={(e) => setAnio(Number(e.target.value))}
          >
            {[0, 1, 2].map((offset) => {
              const a = new Date().getFullYear() - offset;
              return (
                <option key={a} value={a}>
                  {a}
                </option>
              );
            })}
          </select>
        </div>

        {cargandoPyg || !pyg ? (
          <SkeletonFilas filas={5} columnas={13} />
        ) : (
          <div className="finanzas-admin__tabla-scroll">
            <table className="finanzas-admin__tabla-pyg">
              <thead>
                <tr>
                  <th>Concepto</th>
                  {MESES.map((m) => (
                    <th key={m}>{m}</th>
                  ))}
                  <th>Total</th>
                </tr>
              </thead>
              <tbody>
                <tr className="finanzas-admin__fila--seccion">
                  <td colSpan={14}>Ingresos</td>
                </tr>
                {pyg.ingresos.map((f) => filaTabla(f))}
                {filaTotales("Total ingresos", pyg.total_ingresos)}

                <tr className="finanzas-admin__fila--seccion">
                  <td colSpan={14}>Costo de ventas</td>
                </tr>
                {pyg.costo_ventas.map((f) => filaTabla(f))}
                {filaTotales("Total costo de ventas", pyg.total_costo_ventas)}

                {filaTotales(
                  "Margen bruto",
                  pyg.margen_bruto,
                  <TrendingUp size={13} />,
                )}

                <tr className="finanzas-admin__fila--seccion">
                  <td colSpan={14}>Gastos</td>
                </tr>
                {pyg.gastos.map((f) => filaTabla(f))}
                {filaTotales("Total gastos", pyg.total_gastos)}

                {filaTotales(
                  "Ganancia (pérdida) neta",
                  pyg.ganancia_neta,
                  pyg.ganancia_neta.reduce((s, v) => s + v, 0) >= 0 ? (
                    <TrendingUp size={13} />
                  ) : (
                    <TrendingDown size={13} />
                  ),
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
