import React, { useEffect, useState } from 'react';
import { FileText, Search, Trash2, Download, Check, X, Receipt } from 'lucide-react';

import { cajaApi, clientesApi, cotizacionesApi, productosApi } from '../../../services/api';
import { useToast } from '../../Toast/ToastProvider';
import { SkeletonFilas } from '../../Skeleton/Skeleton';
import './CotizacionesAdmin.scss';

const ETIQUETA_ESTADO = {
    PENDIENTE: 'Pendiente',
    APROBADA: 'Aprobada',
    RECHAZADA: 'Rechazada',
    FACTURADA: 'Facturada',
};

export default function CotizacionesAdmin() {
    const { mostrarToast } = useToast();

    // --- Formulario de nueva cotización ---
    const [textoCliente, setTextoCliente] = useState('');
    const [resultadosCliente, setResultadosCliente] = useState([]);
    const [clienteId, setClienteId] = useState(null);
    const [clienteNombreManual, setClienteNombreManual] = useState('');
    const [fechaVencimiento, setFechaVencimiento] = useState('');
    const [notas, setNotas] = useState('');
    const [descuento, setDescuento] = useState('0');

    const [textoBusqueda, setTextoBusqueda] = useState('');
    const [resultadosProducto, setResultadosProducto] = useState([]);
    const [lineas, setLineas] = useState([]);
    const [guardando, setGuardando] = useState(false);

    // --- Listado ---
    const [cotizaciones, setCotizaciones] = useState([]);
    const [cargando, setCargando] = useState(true);
    const [error, setError] = useState(null);

    // --- Facturar ---
    const [facturandoId, setFacturandoId] = useState(null);
    const [sesionesAbiertas, setSesionesAbiertas] = useState([]);
    const [sesionElegida, setSesionElegida] = useState('');
    const [metodoPago, setMetodoPago] = useState('EFECTIVO');

    const cargarCotizaciones = async () => {
        setCargando(true);
        try {
            setCotizaciones(await cotizacionesApi.listar());
        } catch (err) {
            setError(err.message);
        } finally {
            setCargando(false);
        }
    };

    useEffect(() => {
        cargarCotizaciones();
    }, []);

    useEffect(() => {
        if (textoCliente.trim().length < 2) {
            setResultadosCliente([]);
            return;
        }
        const t = setTimeout(async () => {
            try {
                setResultadosCliente(await clientesApi.buscar(textoCliente.trim()));
            } catch {
                setResultadosCliente([]);
            }
        }, 250);
        return () => clearTimeout(t);
    }, [textoCliente]);

    useEffect(() => {
        if (textoBusqueda.trim().length < 1) {
            setResultadosProducto([]);
            return;
        }
        const t = setTimeout(async () => {
            try {
                setResultadosProducto(await productosApi.buscar(textoBusqueda.trim()));
            } catch {
                setResultadosProducto([]);
            }
        }, 250);
        return () => clearTimeout(t);
    }, [textoBusqueda]);

    const agregarLinea = (producto, variante) => {
        setLineas((prev) => {
            if (prev.some((l) => l.variante_id === variante.id)) return prev;
            return [
                ...prev,
                {
                    variante_id: variante.id,
                    producto_nombre: producto.nombre,
                    color: variante.color,
                    cantidad: 1,
                    precio_unitario: variante.precio_venta,
                },
            ];
        });
        setTextoBusqueda('');
        setResultadosProducto([]);
    };

    const actualizarLinea = (varianteId, campo, valor) => {
        setLineas((prev) =>
            prev.map((l) => (l.variante_id === varianteId ? { ...l, [campo]: Number(valor) || 0 } : l))
        );
    };

    const quitarLinea = (varianteId) => {
        setLineas((prev) => prev.filter((l) => l.variante_id !== varianteId));
    };

    const subtotal = lineas.reduce((s, l) => s + l.cantidad * l.precio_unitario, 0);
    const total = Math.max(subtotal - (Number(descuento) || 0), 0);

    const crearCotizacion = async () => {
        if (lineas.length === 0) return;
        setGuardando(true);
        setError(null);
        try {
            const cotizacion = await cotizacionesApi.crear({
                cliente_id: clienteId,
                cliente_nombre: clienteId ? null : clienteNombreManual.trim() || null,
                fecha_vencimiento: fechaVencimiento || null,
                notas: notas.trim() || null,
                descuento_manual: Number(descuento) || 0,
                lineas: lineas.map((l) => ({
                    variante_id: l.variante_id,
                    cantidad: l.cantidad,
                    precio_unitario: l.precio_unitario,
                })),
            });
            mostrarToast(`Cotización ${cotizacion.numero} creada`, 'exito');
            setLineas([]);
            setClienteId(null);
            setTextoCliente('');
            setClienteNombreManual('');
            setFechaVencimiento('');
            setNotas('');
            setDescuento('0');
            await cargarCotizaciones();
        } catch (err) {
            setError(err.message);
        } finally {
            setGuardando(false);
        }
    };

    const cambiarEstado = async (id, estado) => {
        try {
            await cotizacionesApi.cambiarEstado(id, estado);
            await cargarCotizaciones();
        } catch (err) {
            setError(err.message);
        }
    };

    const iniciarFactura = async (id) => {
        setFacturandoId(id);
        try {
            setSesionesAbiertas(await cajaApi.sesionesAbiertas());
        } catch (err) {
            setError(err.message);
        }
    };

    const confirmarFactura = async () => {
        if (!sesionElegida) return;
        try {
            const venta = await cotizacionesApi.facturar(facturandoId, {
                sesion_caja_id: Number(sesionElegida),
                metodo_pago: metodoPago,
            });
            mostrarToast(`Facturada como venta #${venta.id} — $${venta.total.toLocaleString('es-CO')}`, 'exito');
            setFacturandoId(null);
            setSesionElegida('');
            await cargarCotizaciones();
        } catch (err) {
            setError(err.message);
        }
    };

    return (
        <div className="cotizaciones-admin">
            <h2 className="cotizaciones-admin__titulo">
                <FileText size={18} strokeWidth={2} />
                Cotizaciones
            </h2>
            <p className="cotizaciones-admin__ayuda">
                Crea una cotización, descárgala en PDF para enviarla, y si el cliente la aprueba,
                factúrala de un solo click — sin volver a digitar los productos.
            </p>

            {error && <p className="cotizaciones-admin__error">{error}</p>}

            {/* --- Formulario --- */}
            <div className="cotizaciones-admin__seccion">
                <h3>Nueva cotización</h3>

                <div className="cotizaciones-admin__cliente">
                    <input
                        type="text"
                        placeholder="Buscar cliente existente (opcional)…"
                        value={textoCliente}
                        onChange={(e) => {
                            setTextoCliente(e.target.value);
                            setClienteId(null);
                        }}
                    />
                    {resultadosCliente.length > 0 && (
                        <div className="cotizaciones-admin__resultados-cliente">
                            {resultadosCliente.map((c) => (
                                <button
                                    key={c.id}
                                    type="button"
                                    onClick={() => {
                                        setClienteId(c.id);
                                        setTextoCliente(c.nombre_completo);
                                        setResultadosCliente([]);
                                    }}
                                >
                                    {c.nombre_completo}
                                </button>
                            ))}
                        </div>
                    )}
                    <input
                        type="text"
                        placeholder="O nombre de cliente nuevo/mostrador (opcional)"
                        value={clienteNombreManual}
                        onChange={(e) => setClienteNombreManual(e.target.value)}
                        disabled={!!clienteId}
                    />
                    <input
                        type="date"
                        title="Válida hasta"
                        value={fechaVencimiento}
                        onChange={(e) => setFechaVencimiento(e.target.value)}
                    />
                </div>

                <div className="cotizaciones-admin__buscador">
                    <Search size={16} strokeWidth={2} />
                    <input
                        type="text"
                        placeholder="Buscar producto para agregar…"
                        value={textoBusqueda}
                        onChange={(e) => setTextoBusqueda(e.target.value)}
                    />
                    {resultadosProducto.length > 0 && (
                        <div className="cotizaciones-admin__resultados-producto">
                            {resultadosProducto.map((producto) => (
                                <div key={producto.id} className="cotizaciones-admin__resultado-item">
                                    <p>{producto.nombre}</p>
                                    <div className="cotizaciones-admin__resultado-variantes">
                                        {producto.variantes.map((v) => (
                                            <button key={v.id} type="button" onClick={() => agregarLinea(producto, v)}>
                                                {[v.color, v.grosor].filter(Boolean).join(' · ') || v.sku}
                                            </button>
                                        ))}
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>

                {lineas.length > 0 && (
                    <table className="cotizaciones-admin__lineas">
                        <thead>
                            <tr>
                                <th>Producto</th>
                                <th>Cantidad</th>
                                <th>Precio</th>
                                <th>Subtotal</th>
                                <th></th>
                            </tr>
                        </thead>
                        <tbody>
                            {lineas.map((l) => (
                                <tr key={l.variante_id}>
                                    <td>
                                        {l.producto_nombre}
                                        {l.color ? ` · ${l.color}` : ''}
                                    </td>
                                    <td>
                                        <input
                                            type="number"
                                            min="0"
                                            value={l.cantidad}
                                            onChange={(e) => actualizarLinea(l.variante_id, 'cantidad', e.target.value)}
                                        />
                                    </td>
                                    <td>
                                        <input
                                            type="number"
                                            min="0"
                                            value={l.precio_unitario}
                                            onChange={(e) =>
                                                actualizarLinea(l.variante_id, 'precio_unitario', e.target.value)
                                            }
                                        />
                                    </td>
                                    <td className="u-cifra">
                                        ${(l.cantidad * l.precio_unitario).toLocaleString('es-CO')}
                                    </td>
                                    <td>
                                        <button type="button" onClick={() => quitarLinea(l.variante_id)}>
                                            <Trash2 size={14} strokeWidth={2} />
                                        </button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                )}

                {lineas.length > 0 && (
                    <div className="cotizaciones-admin__totales">
                        <label>
                            Descuento
                            <input
                                type="number"
                                min="0"
                                value={descuento}
                                onChange={(e) => setDescuento(e.target.value)}
                            />
                        </label>
                        <textarea
                            placeholder="Notas (opcional)"
                            value={notas}
                            onChange={(e) => setNotas(e.target.value)}
                        />
                        <div className="cotizaciones-admin__total">
                            Total: <span className="u-cifra">${total.toLocaleString('es-CO')}</span>
                        </div>
                    </div>
                )}

                <button
                    type="button"
                    className="cotizaciones-admin__crear"
                    disabled={guardando || lineas.length === 0}
                    onClick={crearCotizacion}
                >
                    {guardando ? 'Creando…' : 'Crear cotización'}
                </button>
            </div>

            {/* --- Listado --- */}
            <div className="cotizaciones-admin__seccion">
                <h3>Historial</h3>
                {cargando ? (
                    <SkeletonFilas filas={3} columnas={6} />
                ) : cotizaciones.length === 0 ? (
                    <p className="cotizaciones-admin__vacio">Aún no hay cotizaciones.</p>
                ) : (
                    <table className="cotizaciones-admin__historial">
                        <thead>
                            <tr>
                                <th>N.º</th>
                                <th>Cliente</th>
                                <th>Fecha</th>
                                <th>Total</th>
                                <th>Estado</th>
                                <th></th>
                            </tr>
                        </thead>
                        <tbody>
                            {cotizaciones.map((c) => (
                                <React.Fragment key={c.id}>
                                    <tr>
                                        <td className="u-cifra">{c.numero}</td>
                                        <td>{c.cliente_nombre || 'Cliente registrado'}</td>
                                        <td className="u-cifra">{c.fecha_emision}</td>
                                        <td className="u-cifra">${c.total.toLocaleString('es-CO')}</td>
                                        <td>
                                            <span
                                                className={`cotizaciones-admin__badge cotizaciones-admin__badge--${c.estado.toLowerCase()}`}
                                            >
                                                {ETIQUETA_ESTADO[c.estado]}
                                            </span>
                                        </td>
                                        <td className="cotizaciones-admin__acciones">
                                            <button
                                                type="button"
                                                title="Descargar PDF"
                                                onClick={() => cotizacionesApi.descargarPdf(c.id, c.numero)}
                                            >
                                                <Download size={14} strokeWidth={2} />
                                            </button>
                                            {c.estado === 'PENDIENTE' && (
                                                <>
                                                    <button
                                                        type="button"
                                                        title="Aprobar"
                                                        onClick={() => cambiarEstado(c.id, 'APROBADA')}
                                                    >
                                                        <Check size={14} strokeWidth={2} />
                                                    </button>
                                                    <button
                                                        type="button"
                                                        title="Rechazar"
                                                        onClick={() => cambiarEstado(c.id, 'RECHAZADA')}
                                                    >
                                                        <X size={14} strokeWidth={2} />
                                                    </button>
                                                </>
                                            )}
                                            {c.estado === 'APROBADA' && (
                                                <button type="button" title="Facturar" onClick={() => iniciarFactura(c.id)}>
                                                    <Receipt size={14} strokeWidth={2} />
                                                </button>
                                            )}
                                        </td>
                                    </tr>
                                    {facturandoId === c.id && (
                                        <tr>
                                            <td colSpan={6}>
                                                <div className="cotizaciones-admin__facturar">
                                                    <select value={sesionElegida} onChange={(e) => setSesionElegida(e.target.value)}>
                                                        <option value="">Elige la caja donde se registra…</option>
                                                        {sesionesAbiertas.map((s) => (
                                                            <option key={s.id} value={s.id}>
                                                                Caja #{s.caja_fisica_id} — sesión #{s.id}
                                                            </option>
                                                        ))}
                                                    </select>
                                                    <select value={metodoPago} onChange={(e) => setMetodoPago(e.target.value)}>
                                                        <option value="EFECTIVO">Efectivo</option>
                                                        <option value="DATAFONO">Datáfono</option>
                                                        <option value="TRANSFERENCIA">Transferencia</option>
                                                    </select>
                                                    <button type="button" onClick={confirmarFactura} disabled={!sesionElegida}>
                                                        Confirmar y facturar
                                                    </button>
                                                    <button type="button" onClick={() => setFacturandoId(null)}>
                                                        Cancelar
                                                    </button>
                                                </div>
                                            </td>
                                        </tr>
                                    )}
                                </React.Fragment>
                            ))}
                        </tbody>
                    </table>
                )}
            </div>
        </div>
    );
}