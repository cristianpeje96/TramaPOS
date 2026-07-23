import React, { useEffect, useState } from 'react';
import { Receipt, Download } from 'lucide-react';

import { ventasApi } from '../../../services/api';
import { SkeletonFilas } from '../../Skeleton/Skeleton';
import './HistorialVentas.scss';

const ETIQUETAS_ESTADO_DIAN = {
  NO_APLICA: 'No aplica',
  PENDIENTE: 'Pendiente',
  ENVIADA: 'Enviada',
  ACEPTADA: 'Aceptada',
  RECHAZADA: 'Rechazada',
};

const ETIQUETAS_ESTADO_VENTA = {
  COMPLETADA: 'Completada',
  ANULADA: 'Devuelta',
  PENDIENTE_PAGO: 'Pendiente de pago',
};

export default function HistorialVentas() {
  const [ventas, setVentas] = useState([]);
  const [canal, setCanal] = useState('');
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState(null);

  const cargar = async (filtroCanal) => {
    setCargando(true);
    setError(null);
    try {
      const params = filtroCanal ? { canal: filtroCanal } : {};
      setVentas(await ventasApi.listar(params));
    } catch (err) {
      setError(err.message);
    } finally {
      setCargando(false);
    }
  };

  useEffect(() => {
    cargar(canal);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [canal]);

  return (
    <div className="historial-ventas">
      <header className="historial-ventas__header">
        <h2 className="historial-ventas__titulo">
          <Receipt size={18} strokeWidth={2} />
          Historial de ventas
        </h2>
        <select value={canal} onChange={(e) => setCanal(e.target.value)}>
          <option value="">Todos los canales</option>
          <option value="POS">POS</option>
          <option value="WEB">WEB</option>
        </select>
      </header>

      {error && <p className="historial-ventas__error">{error}</p>}

      {cargando ? (
        <SkeletonFilas filas={5} columnas={7} />
      ) : ventas.length === 0 ? (
        <p className="historial-ventas__estado">No hay ventas registradas todavía.</p>
      ) : (
        <table className="historial-ventas__tabla">
          <thead>
            <tr>
              <th>#</th>
              <th>Fecha</th>
              <th>Estado</th>
              <th>Canal</th>
              <th>Método pago</th>
              <th>Total</th>
              <th>IVA</th>
              <th>Puntos</th>
              <th>Factura DIAN</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {ventas.map((venta) => (
              <tr
                key={venta.id}
                className={
                  venta.estado === 'ANULADA' ? 'historial-ventas__fila--anulada' : ''
                }
              >
                <td className="u-cifra">{venta.id}</td>
                <td className="u-cifra">
                  {new Date(venta.creado_en).toLocaleString('es-CO')}
                </td>
                <td>
                  <span
                    className={`historial-ventas__badge historial-ventas__badge-estado--${venta.estado.toLowerCase()}`}
                  >
                    {ETIQUETAS_ESTADO_VENTA[venta.estado]}
                  </span>
                </td>
                <td>{venta.canal}</td>
                <td>{venta.metodo_pago}</td>
                <td className="u-cifra">${venta.total.toLocaleString('es-CO')}</td>
                <td className="u-cifra">
                  {venta.total_iva > 0 ? `$${venta.total_iva.toLocaleString('es-CO')}` : '—'}
                </td>
                <td className="u-cifra">
                  {venta.puntos_ganados > 0 && `+${venta.puntos_ganados}`}
                  {venta.puntos_redimidos > 0 && ` -${venta.puntos_redimidos}`}
                  {venta.puntos_ganados === 0 && venta.puntos_redimidos === 0 && '—'}
                </td>
                <td>
                  <span
                    className={`historial-ventas__badge historial-ventas__badge--${venta.estado_factura_dian.toLowerCase()}`}
                  >
                    {ETIQUETAS_ESTADO_DIAN[venta.estado_factura_dian]}
                  </span>
                </td>
                <td>
                  <button
                    type="button"
                    className="historial-ventas__boton-pdf"
                    title="Descargar factura formal en PDF"
                    onClick={() => ventasApi.descargarFacturaPdf(venta.id)}
                  >
                    <Download size={14} strokeWidth={2} />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}