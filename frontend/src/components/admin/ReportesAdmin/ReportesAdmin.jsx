import React, { useEffect, useState } from "react";
import { BarChart2, TrendingUp, Calendar } from "lucide-react";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from "recharts";

import { reportesApi } from "../../../services/api";
import { SkeletonFilas } from "../../Skeleton/Skeleton";
import "./ReportesAdmin.scss";

const hoyISO = () => new Date().toISOString().slice(0, 10);
const hace30DiasISO = () => {
  const f = new Date();
  f.setDate(f.getDate() - 30);
  return f.toISOString().slice(0, 10);
};
const primerDiaDelMesISO = () => {
  const f = new Date();
  f.setDate(1);
  return f.toISOString().slice(0, 10);
};
const primerDiaDelAnioISO = () => `${new Date().getFullYear()}-01-01`;

const NOMBRES_MES = [
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

export default function ReportesAdmin() {
  const [fechaDesde, setFechaDesde] = useState(hace30DiasISO());
  const [fechaHasta, setFechaHasta] = useState(hoyISO());

  const [resumen, setResumen] = useState(null);
  const [ventasPorDia, setVentasPorDia] = useState([]);
  const [ventasPorMes, setVentasPorMes] = useState([]);
  const [productosTop, setProductosTop] = useState([]);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState(null);

  const cargarTodo = async () => {
    setCargando(true);
    setError(null);
    try {
      const params = { fecha_desde: fechaDesde, fecha_hasta: fechaHasta };
      const [r, vd, vm, pt] = await Promise.all([
        reportesApi.resumen(params),
        reportesApi.ventasPorDia(params),
        reportesApi.ventasPorMes(12),
        reportesApi.productosMasVendidos({ ...params, limite: 10 }),
      ]);
      setResumen(r);
      setVentasPorDia(vd.map((v) => ({ ...v, etiqueta: v.fecha.slice(5) })));
      setVentasPorMes(
        vm.map((v) => ({
          ...v,
          etiqueta: `${NOMBRES_MES[v.mes - 1]} ${v.anio}`,
        })),
      );
      setProductosTop(pt);
    } catch (err) {
      setError(err.message);
    } finally {
      setCargando(false);
    }
  };

  useEffect(() => {
    cargarTodo();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [fechaDesde, fechaHasta]);

  return (
    <div className="reportes-admin">
      <h2 className="reportes-admin__titulo">
        <BarChart2 size={18} strokeWidth={2} />
        Reportes y estadísticas
      </h2>

      <div className="reportes-admin__filtro-fecha">
        <Calendar size={16} strokeWidth={2} />
        <input
          type="date"
          value={fechaDesde}
          onChange={(e) => setFechaDesde(e.target.value)}
        />
        <span>a</span>
        <input
          type="date"
          value={fechaHasta}
          onChange={(e) => setFechaHasta(e.target.value)}
        />
        <button
          type="button"
          onClick={() => {
            setFechaDesde(hace30DiasISO());
            setFechaHasta(hoyISO());
          }}
        >
          Últimos 30 días
        </button>
        <button
          type="button"
          onClick={() => {
            setFechaDesde(primerDiaDelMesISO());
            setFechaHasta(hoyISO());
          }}
        >
          Este mes
        </button>
        <button
          type="button"
          onClick={() => {
            setFechaDesde(primerDiaDelAnioISO());
            setFechaHasta(hoyISO());
          }}
        >
          Este año
        </button>
      </div>

      {error && <p className="reportes-admin__error">{error}</p>}

      {cargando ? (
        <SkeletonFilas filas={4} columnas={3} />
      ) : (
        <>
          {resumen && (
            <div className="reportes-admin__resumen">
              <div className="reportes-admin__tarjeta-resumen">
                <span className="reportes-admin__resumen-label">
                  Total vendido
                </span>
                <span className="reportes-admin__resumen-valor u-cifra">
                  ${resumen.total_ventas.toLocaleString("es-CO")}
                </span>
              </div>
              <div className="reportes-admin__tarjeta-resumen">
                <span className="reportes-admin__resumen-label">
                  Ventas realizadas
                </span>
                <span className="reportes-admin__resumen-valor u-cifra">
                  {resumen.cantidad_ventas}
                </span>
              </div>
              <div className="reportes-admin__tarjeta-resumen">
                <span className="reportes-admin__resumen-label">
                  Ticket promedio
                </span>
                <span className="reportes-admin__resumen-valor u-cifra">
                  ${resumen.ticket_promedio.toLocaleString("es-CO")}
                </span>
              </div>
            </div>
          )}

          <h3 className="reportes-admin__subtitulo">Ventas por día</h3>
          {ventasPorDia.length === 0 ? (
            <p className="reportes-admin__vacio">
              Sin ventas en este rango de fechas.
            </p>
          ) : (
            <div className="reportes-admin__grafica">
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={ventasPorDia}>
                  <CartesianGrid
                    strokeDasharray="3 3"
                    stroke="var(--tp-color-border)"
                  />
                  <XAxis dataKey="etiqueta" tick={{ fontSize: 11 }} />
                  <YAxis tick={{ fontSize: 11 }} />
                  <Tooltip
                    formatter={(value) => [
                      `$${value.toLocaleString("es-CO")}`,
                      "Total",
                    ]}
                  />
                  <Bar
                    dataKey="total"
                    fill="var(--tp-color-primary)"
                    radius={[4, 4, 0, 0]}
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}

          <h3 className="reportes-admin__subtitulo">
            <TrendingUp size={16} strokeWidth={2} />
            Ventas por mes (últimos 12 meses)
          </h3>
          <div className="reportes-admin__grafica">
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={ventasPorMes}>
                <CartesianGrid
                  strokeDasharray="3 3"
                  stroke="var(--tp-color-border)"
                />
                <XAxis dataKey="etiqueta" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip
                  formatter={(value) => [
                    `$${value.toLocaleString("es-CO")}`,
                    "Total",
                  ]}
                />
                <Bar
                  dataKey="total"
                  fill="var(--tp-color-accent)"
                  radius={[4, 4, 0, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>

          <h3 className="reportes-admin__subtitulo">
            Productos más vendidos en el rango
          </h3>
          {productosTop.length === 0 ? (
            <p className="reportes-admin__vacio">
              Sin ventas en este rango de fechas.
            </p>
          ) : (
            <table className="reportes-admin__tabla">
              <thead>
                <tr>
                  <th>Producto</th>
                  <th>Cantidad vendida</th>
                  <th>Total vendido</th>
                </tr>
              </thead>
              <tbody>
                {productosTop.map((p) => (
                  <tr key={p.variante_id}>
                    <td>
                      {p.producto_nombre}
                      {p.color ? ` · ${p.color}` : ""}
                    </td>
                    <td className="u-cifra">{p.cantidad_vendida}</td>
                    <td className="u-cifra">
                      ${p.total_vendido.toLocaleString("es-CO")}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </>
      )}
    </div>
  );
}
