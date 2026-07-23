import React, { forwardRef, useEffect, useImperativeHandle, useRef, useState } from 'react';
import { User, Gift, CreditCard, Banknote, Landmark, Keyboard, Tag, Award, Wallet } from 'lucide-react';

import { configuracionEmpresaApi, fidelizacionApi, ventasApi } from '../../services/api';
import { useHardwareAgent } from '../../hooks/useHardwareAgent';
import { useAuth } from '../Auth/AuthProvider';
import './CheckoutPanel.scss';

const METODOS_PAGO = [
  { id: 'EFECTIVO', label: 'Efectivo', icon: Banknote },
  { id: 'DATAFONO', label: 'Datáfono', icon: CreditCard },
  { id: 'TRANSFERENCIA', label: 'Transferencia', icon: Landmark },
];

// Denominaciones de billetes/monedas COP para el conteo rápido en efectivo
const DENOMINACIONES_COP = [1000, 2000, 5000, 10000, 20000, 50000, 100000];

/**
 * CheckoutPanel — versión reintegrada.
 *
 * Cambios respecto a la primera versión (mockup inicial):
 *  - El descuento por puntos YA NO se calcula en el frontend: se pide a
 *    GET /fidelizacion/simular-redencion, la misma cuenta que hace el
 *    backend al confirmar (evita que el POS le muestre al cajero un
 *    número que luego el backend rechace o recalcule distinto).
 *  - F10 ahora sí llama a POST /ventas (ventasApi.crear) y, si la venta
 *    se crea con éxito, dispara el ticket físico vía useHardwareAgent.
 *
 * Los atajos F4/F9/F10/Ctrl+Shift+O ya NO los maneja este componente:
 * PosScreen (el contenedor) tiene el único useAtajosTeclado de la app y
 * llama a ciclarMetodoPago/activarRedencion/confirmarVenta/abrirCajonManual
 * a través de la ref expuesta más abajo (useImperativeHandle). Esto evita
 * dos listeners de teclado compitiendo por la misma tecla.
 */
const CheckoutPanel = forwardRef(function CheckoutPanel(
  {
    cliente = null, // { id, nombre_completo, puntos_balance }
    lineas = [], // [{ variante_id, cantidad, precio_unitario, nombre, color }]
    sesionCajaId,
    canal = 'POS',
    onBuscarCliente, // callback F7 — abre el modal de cliente (aún no construido)
    onVentaCreada, // callback tras confirmar la venta con éxito
  },
  ref
) {
  const [metodoPago, setMetodoPago] = useState('EFECTIVO');
  const [puntosARedimir, setPuntosARedimir] = useState(0);
  const [redimiendo, setRedimiendo] = useState(false);
  const [simulacion, setSimulacion] = useState(null);
  const [rangoCliente, setRangoCliente] = useState(null);
  const [mostrarDescuentoManual, setMostrarDescuentoManual] = useState(false);
  const [tipoDescuentoManual, setTipoDescuentoManual] = useState('porcentaje'); // 'porcentaje' | 'monto'
  const [valorDescuentoManual, setValorDescuentoManual] = useState('');
  const [motivoDescuentoManual, setMotivoDescuentoManual] = useState('');
  const [procesando, setProcesando] = useState(false);
  const [errorVenta, setErrorVenta] = useState(null);
  const [montoRecibido, setMontoRecibido] = useState('');
  const [configEmpresa, setConfigEmpresa] = useState(null);
  const { usuario } = useAuth();

  useEffect(() => {
    configuracionEmpresaApi.obtener().then(setConfigEmpresa).catch(() => { });
  }, []);

  const inputPuntosRef = useRef(null);
  const { procesarVenta: imprimirYAbrirCajon, abrirCajonManual } = useHardwareAgent();

  const puntosDisponibles = cliente?.puntos_balance ?? 0;
  const subtotal = lineas.reduce((suma, l) => suma + l.cantidad * l.precio_unitario, 0);
  const descuentoPuntos = simulacion?.valor_descuento ?? 0;
  const descuentoFidelizacion = rangoCliente
    ? subtotal * (rangoCliente.porcentaje_descuento / 100)
    : 0;
  const descuentoManualCalculado =
    tipoDescuentoManual === 'porcentaje'
      ? subtotal * ((Number(valorDescuentoManual) || 0) / 100)
      : Math.min(Number(valorDescuentoManual) || 0, subtotal);
  const descuentoManualActivo = mostrarDescuentoManual && Number(valorDescuentoManual) > 0;
  const totalConDescuento = Math.max(
    subtotal -
    descuentoPuntos -
    descuentoFidelizacion -
    (descuentoManualActivo ? descuentoManualCalculado : 0),
    0
  );
  const cambioADevolver = Number(montoRecibido || 0) - totalConDescuento;

  const agregarBillete = (valor) =>
    setMontoRecibido((prev) => String((Number(prev) || 0) + valor));
  const marcarMontoExacto = () => setMontoRecibido(String(totalConDescuento));
  const limpiarMontoRecibido = () => setMontoRecibido('');

  useEffect(() => {
    if (metodoPago !== 'EFECTIVO') setMontoRecibido('');
  }, [metodoPago]);

  const activarRedencion = () => {
    if (puntosDisponibles <= 0) return;
    setRedimiendo(true);
    setTimeout(() => inputPuntosRef.current?.focus(), 0);
  };

  const ciclarMetodoPago = () => {
    const indiceActual = METODOS_PAGO.findIndex((m) => m.id === metodoPago);
    setMetodoPago(METODOS_PAGO[(indiceActual + 1) % METODOS_PAGO.length].id);
  };

  // --- Rango de fidelización: se consulta apenas hay cliente seleccionado ---
  useEffect(() => {
    if (!cliente) {
      setRangoCliente(null);
      return;
    }
    fidelizacionApi
      .rangoCliente(cliente.id)
      .then(setRangoCliente)
      .catch(() => setRangoCliente(null));
  }, [cliente]);

  // --- Simulación de redención: se recalcula contra el backend, con un
  // pequeño debounce para no golpear la API en cada tecla ---
  useEffect(() => {
    if (!cliente || puntosARedimir <= 0) {
      setSimulacion(null);
      return;
    }
    const temporizador = setTimeout(async () => {
      try {
        const resultado = await fidelizacionApi.simularRedencion(cliente.id, puntosARedimir);
        setSimulacion(resultado);
      } catch (err) {
        setSimulacion(null);
        setErrorVenta(err.message);
      }
    }, 300);
    return () => clearTimeout(temporizador);
  }, [cliente, puntosARedimir]);

  const manejarCambioPuntos = (evento) => {
    const valor = Math.min(Number(evento.target.value) || 0, puntosDisponibles);
    setPuntosARedimir(valor);
  };

  const construirTicketTexto = (venta) => {
    const ahora = new Date();
    const fechaHora = ahora.toLocaleString('es-CO', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
    const separador = '--------------------------------';

    const lineasTicket = [
      configEmpresa?.razon_social || 'TRAMAPOS',
      ...(configEmpresa?.nit ? [`NIT: ${configEmpresa.nit}`] : []),
      ...(configEmpresa?.direccion ? [configEmpresa.direccion] : []),
      ...(configEmpresa?.telefono ? [`Tel: ${configEmpresa.telefono}`] : []),
      separador,
      `Venta #${venta.id}`,
      fechaHora,
      `Cajero: ${usuario?.nombre_completo || '-'}`,
      `Cliente: ${cliente?.nombre_completo || 'Mostrador'}`,
      separador,
      ...lineas.map(
        (l) => `${l.cantidad} x ${l.nombre}${l.color ? ` (${l.color})` : ''}  $${l.precio_unitario.toLocaleString('es-CO')}`
      ),
      separador,
      `Subtotal: $${venta.subtotal.toLocaleString('es-CO')}`,
      ...(venta.descuento_manual > 0
        ? [`Descuento${venta.motivo_descuento_manual ? ` (${venta.motivo_descuento_manual})` : ''}: -$${venta.descuento_manual.toLocaleString('es-CO')}`]
        : []),
      ...(venta.descuento_puntos > 0
        ? [`Descuento por puntos: -$${venta.descuento_puntos.toLocaleString('es-CO')}`]
        : []),
      ...(venta.descuento_fidelizacion > 0
        ? [`Descuento ${venta.rango_fidelizacion_aplicado || 'fidelización'}: -$${venta.descuento_fidelizacion.toLocaleString('es-CO')}`]
        : []),
      ...(venta.total_iva > 0 ? [`IVA incluido: $${venta.total_iva.toLocaleString('es-CO')}`] : []),
      separador,
      `TOTAL: $${venta.total.toLocaleString('es-CO')}`,
      `Pago: ${METODOS_PAGO.find((m) => m.id === venta.metodo_pago)?.label || venta.metodo_pago}`,
      ...(venta.puntos_ganados > 0 ? [`Puntos ganados: ${venta.puntos_ganados}`] : []),
      separador,
      'Gracias por su compra',
    ];

    return lineasTicket.join('\n');
  };

  const confirmarVenta = async () => {
    if (lineas.length === 0 || procesando) return;
    if (descuentoManualActivo && !motivoDescuentoManual.trim()) {
      setErrorVenta('El descuento manual requiere indicar un motivo');
      return;
    }
    setProcesando(true);
    setErrorVenta(null);

    try {
      const venta = await ventasApi.crear({
        canal,
        sesion_caja_id: sesionCajaId,
        cliente_id: cliente?.id ?? null,
        metodo_pago: metodoPago,
        lineas: lineas.map((l) => ({ variante_id: l.variante_id, cantidad: l.cantidad })),
        puntos_a_redimir: puntosARedimir,
        ...(descuentoManualActivo && {
          motivo_descuento_manual: motivoDescuentoManual.trim(),
          ...(tipoDescuentoManual === 'porcentaje'
            ? { descuento_manual_porcentaje: Number(valorDescuentoManual) }
            : { descuento_manual_monto: Number(valorDescuentoManual) }),
        }),
      });

      imprimirYAbrirCajon(construirTicketTexto(venta));
      onVentaCreada?.(venta);

      // Reset del panel para la siguiente venta
      setMetodoPago('EFECTIVO');
      setPuntosARedimir(0);
      setRedimiendo(false);
      setSimulacion(null);
      setMostrarDescuentoManual(false);
      setValorDescuentoManual('');
      setMotivoDescuentoManual('');
      setMontoRecibido('');
    } catch (err) {
      setErrorVenta(err.message);
    } finally {
      setProcesando(false);
    }
  };

  // API imperativa: PosScreen (el contenedor) es el único dueño de
  // useAtajosTeclado y llama a estos métodos por referencia, para que
  // F4/F9/F10/Ctrl+Shift+O nunca tengan dos listeners compitiendo.
  useImperativeHandle(ref, () => ({
    ciclarMetodoPago,
    activarRedencion,
    confirmarVenta,
    abrirCajonManual,
  }));

  return (
    <section className="checkout-panel">
      <header className="checkout-panel__header">
        <h2 className="checkout-panel__title">Cobro rápido</h2>
        <span className="checkout-panel__hint">
          <Keyboard size={14} strokeWidth={2} />
          F7 cliente · F9 puntos · F4 pago · F10 cobrar
        </span>
      </header>

      <div className="checkout-panel__customer">
        <button type="button" className="checkout-panel__customer-btn" onClick={onBuscarCliente}>
          <User size={18} strokeWidth={2} />
          <span>{cliente ? cliente.nombre_completo : 'Buscar cliente (F7)'}</span>
        </button>
        {rangoCliente?.rango && (
          <span className="checkout-panel__rango-badge">
            <Award size={13} strokeWidth={2} />
            {rangoCliente.rango}
            {rangoCliente.porcentaje_descuento > 0 &&
              ` · ${rangoCliente.porcentaje_descuento}% dcto.`}
          </span>
        )}
      </div>

      {cliente && (
        <div
          className={`checkout-panel__points ${redimiendo ? 'checkout-panel__points--active' : ''
            }`}
        >
          <div className="checkout-panel__points-info">
            <Gift size={18} strokeWidth={2} />
            <span>
              Saldo: <strong className="u-cifra">{puntosDisponibles}</strong> pts
            </span>
          </div>

          {redimiendo ? (
            <input
              ref={inputPuntosRef}
              type="number"
              className="checkout-panel__points-input"
              min={0}
              max={puntosDisponibles}
              value={puntosARedimir}
              onChange={manejarCambioPuntos}
              onBlur={() => puntosARedimir === 0 && setRedimiendo(false)}
              placeholder="Puntos a redimir"
            />
          ) : (
            <button
              type="button"
              className="checkout-panel__points-toggle"
              onClick={activarRedencion}
              disabled={puntosDisponibles <= 0}
            >
              Redimir (F9)
            </button>
          )}
        </div>
      )}

      <div className="checkout-panel__payment-methods">
        {METODOS_PAGO.map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            type="button"
            className={`checkout-panel__payment-btn ${metodoPago === id ? 'checkout-panel__payment-btn--selected' : ''
              }`}
            onClick={() => setMetodoPago(id)}
          >
            <Icon size={20} strokeWidth={2} />
            <span>{label}</span>
          </button>
        ))}
      </div>

      {metodoPago === 'EFECTIVO' && (
        <div className="checkout-panel__cash">
          <div className="checkout-panel__cash-header">
            <Wallet size={14} strokeWidth={2} />
            <span>¿Con cuánto paga?</span>
          </div>

          <div className="checkout-panel__cash-input-row">
            <input
              type="number"
              min={0}
              className="checkout-panel__cash-input u-cifra"
              placeholder="Monto recibido"
              value={montoRecibido}
              onChange={(e) => setMontoRecibido(e.target.value)}
            />
            <button type="button" onClick={marcarMontoExacto}>
              Exacto
            </button>
            <button type="button" onClick={limpiarMontoRecibido}>
              Limpiar
            </button>
          </div>

          <div className="checkout-panel__cash-billetes">
            {DENOMINACIONES_COP.map((valor) => (
              <button key={valor} type="button" onClick={() => agregarBillete(valor)}>
                +{valor >= 1000 ? `${valor / 1000}k` : valor}
              </button>
            ))}
          </div>

          {montoRecibido !== '' && (
            <div
              className={`checkout-panel__cash-resultado ${cambioADevolver < 0
                  ? 'checkout-panel__cash-resultado--falta'
                  : 'checkout-panel__cash-resultado--cambio'
                }`}
            >
              <span>{cambioADevolver < 0 ? 'Falta' : 'Cambio a devolver'}</span>
              <span className="u-cifra">
                ${Math.abs(cambioADevolver).toLocaleString('es-CO')}
              </span>
            </div>
          )}
        </div>
      )}

      <div className="checkout-panel__manual-discount">
        <button
          type="button"
          className="checkout-panel__manual-discount-toggle"
          onClick={() => setMostrarDescuentoManual((v) => !v)}
        >
          <Tag size={14} strokeWidth={2} />
          {mostrarDescuentoManual ? 'Quitar descuento manual' : 'Aplicar descuento manual'}
        </button>

        {mostrarDescuentoManual && (
          <div className="checkout-panel__manual-discount-form">
            <div className="checkout-panel__manual-discount-tipo">
              <button
                type="button"
                className={tipoDescuentoManual === 'porcentaje' ? 'checkout-panel__manual-discount-tipo-btn--activo' : ''}
                onClick={() => setTipoDescuentoManual('porcentaje')}
              >
                %
              </button>
              <button
                type="button"
                className={tipoDescuentoManual === 'monto' ? 'checkout-panel__manual-discount-tipo-btn--activo' : ''}
                onClick={() => setTipoDescuentoManual('monto')}
              >
                $
              </button>
            </div>
            <input
              type="number"
              min={0}
              max={tipoDescuentoManual === 'porcentaje' ? 100 : undefined}
              placeholder={tipoDescuentoManual === 'porcentaje' ? '% descuento' : 'Monto $'}
              value={valorDescuentoManual}
              onChange={(e) => setValorDescuentoManual(e.target.value)}
            />
            <input
              type="text"
              placeholder="Motivo (obligatorio)"
              value={motivoDescuentoManual}
              onChange={(e) => setMotivoDescuentoManual(e.target.value)}
            />
          </div>
        )}
      </div>

      <div className="checkout-panel__totals">
        <div className="checkout-panel__totals-row">
          <span>Subtotal</span>
          <span className="u-cifra">${subtotal.toLocaleString('es-CO')}</span>
        </div>
        {descuentoPuntos > 0 && (
          <div className="checkout-panel__totals-row checkout-panel__totals-row--discount">
            <span>Descuento puntos</span>
            <span className="u-cifra">-${descuentoPuntos.toLocaleString('es-CO')}</span>
          </div>
        )}
        {descuentoFidelizacion > 0 && (
          <div className="checkout-panel__totals-row checkout-panel__totals-row--discount">
            <span>Descuento {rangoCliente?.rango}</span>
            <span className="u-cifra">-${descuentoFidelizacion.toLocaleString('es-CO')}</span>
          </div>
        )}
        {descuentoManualActivo && (
          <div className="checkout-panel__totals-row checkout-panel__totals-row--discount">
            <span>Descuento manual</span>
            <span className="u-cifra">
              -${descuentoManualCalculado.toLocaleString('es-CO')}
            </span>
          </div>
        )}
        <div className="checkout-panel__totals-row checkout-panel__totals-row--final">
          <span>Total</span>
          <span className="u-cifra">${totalConDescuento.toLocaleString('es-CO')}</span>
        </div>
      </div>

      {errorVenta && <p className="checkout-panel__error">{errorVenta}</p>}

      <button
        type="button"
        className="checkout-panel__submit"
        disabled={procesando || lineas.length === 0}
        onClick={confirmarVenta}
      >
        {procesando ? 'Procesando…' : 'Cobrar (F10)'}
      </button>
    </section>
  );
});

export default CheckoutPanel;