import React, { useEffect, useRef, useState } from "react";
import {
  Trash2,
  Keyboard,
  Lock,
  Settings,
  Minus,
  Plus,
  RotateCcw,
} from "lucide-react";

import { cajaApi } from "../../services/api";
import { useAtajosTeclado } from "../../hooks/useAtajosTeclado";
import { useToast } from "../toast/ToastProvider";
import BuscadorProducto from "../BuscadorProducto/BuscadorProducto";
import CheckoutPanel from "../CheckoutPanel/CheckoutPanel";
import ModalCliente from "../ModalCliente/ModalCliente";
import ProductosDestacados from "../ProductosDestacados/ProductosDestacados";
import CierreCajaModal from "../CierreCajaModal/CierreCajaModal";
import "./PosScreen.scss";

// TODO: reemplazar por el id del usuario autenticado cuando exista login.
const USUARIO_ID_TEMPORAL = 1;

/**
 * PosScreen — contenedor principal del punto de venta.
 *
 * Responsabilidades que junta:
 *  1. Verifica que haya una sesión de caja abierta (GET /caja/actual) antes
 *     de dejar vender nada — igual que exige la base de datos.
 *  2. Es el ÚNICO dueño de useAtajosTeclado. F2 y F7 los resuelve
 *     directamente (enfocar buscador / abrir modal de cliente); F4, F9,
 *     F10 y Ctrl+Shift+O los delega al CheckoutPanel a través de su ref.
 *  3. Mantiene el estado de la "venta actual" (líneas) y del cliente
 *     seleccionado — ninguno de los dos vive dentro de los componentes
 *     hijos, para que Esc pueda limpiarlos desde un solo lugar.
 */
export default function PosScreen({ onIrAdmin, onIrDevoluciones }) {
  const [sesion, setSesion] = useState(undefined); // undefined = cargando, null = sin sesión
  const [montoApertura, setMontoApertura] = useState("");
  const [abriendoCaja, setAbriendoCaja] = useState(false);

  const [lineas, setLineas] = useState([]);
  const [cliente, setCliente] = useState(null);
  const [modalClienteAbierto, setModalClienteAbierto] = useState(false);
  const [cierreCajaAbierto, setCierreCajaAbierto] = useState(false);
  const [ultimaVenta, setUltimaVenta] = useState(null);

  const refBuscador = useRef(null);
  const refCheckout = useRef(null);
  const { mostrarToast } = useToast();
  const [atajoActivo, setAtajoActivo] = useState(null); // { etiqueta, key }
  const timeoutAtajoRef = useRef(null);
  const contadorAtajoRef = useRef(0);

  /**
   * Envuelve cada handler de atajo para mostrar un flash visual breve
   * (junto al ícono de teclado en el topbar) confirmando que la tecla
   * sí hizo algo — el cajero no tiene que mirar el panel completo para
   * saber si F9/F4/etc. surtieron efecto.
   */
  const dispararAtajo = (etiqueta, accion) => {
    contadorAtajoRef.current += 1;
    setAtajoActivo({ etiqueta, key: contadorAtajoRef.current });
    clearTimeout(timeoutAtajoRef.current);
    timeoutAtajoRef.current = setTimeout(() => setAtajoActivo(null), 650);
    accion();
  };

  useEffect(() => {
    cajaApi
      .sesionActual()
      .then(setSesion)
      .catch(() => setSesion(null));
  }, []);

  const abrirCaja = async () => {
    setAbriendoCaja(true);
    try {
      const nuevaSesion = await cajaApi.abrir({
        usuario_apertura_id: USUARIO_ID_TEMPORAL,
        monto_apertura: Number(montoApertura) || 0,
      });
      setSesion(nuevaSesion);
    } catch (err) {
      mostrarToast(err.message, "error");
    } finally {
      setAbriendoCaja(false);
    }
  };

  const agregarLinea = (nuevaLinea) => {
    setLineas((prev) => {
      const existente = prev.find(
        (l) => l.variante_id === nuevaLinea.variante_id,
      );
      if (existente) {
        const incremento = nuevaLinea.unidad_medida === "kg" ? 0.5 : 1;
        return prev.map((l) =>
          l.variante_id === nuevaLinea.variante_id
            ? { ...l, cantidad: l.cantidad + incremento }
            : l,
        );
      }
      return [...prev, nuevaLinea];
    });
  };

  const actualizarCantidad = (variante_id, nuevaCantidad) => {
    if (nuevaCantidad <= 0) {
      quitarLinea(variante_id);
      return;
    }
    setLineas((prev) =>
      prev.map((l) =>
        l.variante_id === variante_id ? { ...l, cantidad: nuevaCantidad } : l,
      ),
    );
  };

  const quitarLinea = (variante_id) => {
    setLineas((prev) => prev.filter((l) => l.variante_id !== variante_id));
  };

  const cancelarVentaActual = () => {
    setLineas([]);
    setCliente(null);
  };

  const manejarVentaCreada = (venta) => {
    setUltimaVenta(venta);
    setLineas([]);
    setCliente(null);
    mostrarToast(
      `Venta #${venta.id} registrada — $${venta.total.toLocaleString("es-CO")}`,
      "exito",
    );
  };

  const manejarCajaCerrada = (sesionCerrada) => {
    setCierreCajaAbierto(false);
    setSesion(null); // vuelve a la pantalla de apertura de caja
    const diferencia = sesionCerrada.diferencia ?? 0;
    const mensajeDiferencia =
      diferencia === 0
        ? "Caja cuadrada exacta."
        : diferencia > 0
          ? `Sobraron $${diferencia.toLocaleString("es-CO")}.`
          : `Faltaron $${Math.abs(diferencia).toLocaleString("es-CO")}.`;
    mostrarToast(
      `Caja #${sesionCerrada.id} cerrada. ${mensajeDiferencia}`,
      "info",
      6000,
    );
  };

  useAtajosTeclado({
    onBuscarProducto: () =>
      dispararAtajo("F2", () => refBuscador.current?.focus()),
    onBuscarCliente: () =>
      dispararAtajo("F7", () => setModalClienteAbierto(true)),
    onCancelarVenta: () => dispararAtajo("Esc", cancelarVentaActual),
    onSeleccionarPago: () =>
      dispararAtajo("F4", () => refCheckout.current?.ciclarMetodoPago()),
    onAplicarPuntos: () =>
      dispararAtajo("F9", () => refCheckout.current?.activarRedencion()),
    onProcesarVenta: () =>
      dispararAtajo("F10", () => refCheckout.current?.confirmarVenta()),
    onAbrirCajonManual: () =>
      dispararAtajo("Ctrl+Shift+O", () =>
        refCheckout.current?.abrirCajonManual(),
      ),
  });

  // --- Estado 1: verificando si hay sesión abierta ---
  if (sesion === undefined) {
    return (
      <div className="pos-screen__estado">Verificando sesión de caja…</div>
    );
  }

  // --- Estado 2: no hay sesión — bloquear venta hasta abrir caja ---
  if (sesion === null) {
    return (
      <div className="pos-screen__apertura">
        <Lock size={28} strokeWidth={1.5} />
        <h1>Apertura de caja</h1>
        <p>
          No hay una sesión de caja abierta. Ingresa el monto inicial para
          empezar a vender.
        </p>
        <input
          type="number"
          min="0"
          className="pos-screen__apertura-input"
          placeholder="Monto de apertura"
          value={montoApertura}
          onChange={(e) => setMontoApertura(e.target.value)}
        />
        <button
          type="button"
          className="pos-screen__apertura-btn"
          disabled={abriendoCaja}
          onClick={abrirCaja}
        >
          {abriendoCaja ? "Abriendo…" : "Abrir caja"}
        </button>
      </div>
    );
  }

  // --- Estado 3: sesión abierta, POS operativo ---
  return (
    <div className="pos-screen">
      <header className="pos-screen__topbar">
        <span className="pos-screen__marca">TramaPos</span>
        <span className="pos-screen__sesion">
          Caja #{sesion.id} · sesión abierta
        </span>
        <span className="pos-screen__atajos">
          <Keyboard size={14} strokeWidth={2} />
          F2 buscar · F7 cliente · F9 puntos · F4 pago · F10 cobrar · Esc
          cancelar
          {atajoActivo && (
            <span key={atajoActivo.key} className="pos-screen__atajo-flash">
              {atajoActivo.etiqueta}
            </span>
          )}
        </span>
        <button
          type="button"
          className="pos-screen__devoluciones-btn"
          onClick={onIrDevoluciones}
        >
          <RotateCcw size={14} strokeWidth={2} />
          Devoluciones
        </button>
        <button
          type="button"
          className="pos-screen__cerrar-caja-btn"
          onClick={() => setCierreCajaAbierto(true)}
        >
          <Lock size={14} strokeWidth={2} />
          Cerrar caja
        </button>
        <button
          type="button"
          className="pos-screen__admin-btn"
          onClick={onIrAdmin}
        >
          <Settings size={14} strokeWidth={2} />
          Administración
        </button>
      </header>

      <div className="pos-screen__cuerpo">
        <div className="pos-screen__columna-izquierda">
          <BuscadorProducto
            ref={refBuscador}
            onSeleccionarVariante={agregarLinea}
          />

          <div className="pos-screen__venta-actual">
            <p className="pos-screen__venta-actual-titulo">Venta actual</p>
            {lineas.length === 0 ? (
              <p className="pos-screen__venta-actual-vacio">
                Sin productos — busca con F2 o escanea un código
              </p>
            ) : (
              <ul className="pos-screen__lineas">
                {lineas.map((linea) => {
                  const esPorPeso = linea.unidad_medida === "kg";
                  return (
                    <li key={linea.variante_id} className="pos-screen__linea">
                      <span className="pos-screen__linea-texto">
                        {linea.nombre}
                        {linea.color ? ` · ${linea.color}` : ""}
                      </span>

                      {esPorPeso ? (
                        <div className="pos-screen__linea-peso">
                          <input
                            type="number"
                            min="1"
                            step="1"
                            className="pos-screen__linea-peso-input u-cifra"
                            value={Math.round(linea.cantidad * 1000)}
                            onChange={(e) =>
                              actualizarCantidad(
                                linea.variante_id,
                                (Number(e.target.value) || 0) / 1000,
                              )
                            }
                          />
                          <span className="pos-screen__linea-peso-unidad">
                            g
                          </span>
                        </div>
                      ) : (
                        <div className="pos-screen__linea-stepper">
                          <button
                            type="button"
                            onClick={() =>
                              actualizarCantidad(
                                linea.variante_id,
                                linea.cantidad - 1,
                              )
                            }
                            aria-label="Restar"
                          >
                            <Minus size={12} strokeWidth={2.5} />
                          </button>
                          <span className="u-cifra">{linea.cantidad}</span>
                          <button
                            type="button"
                            onClick={() =>
                              actualizarCantidad(
                                linea.variante_id,
                                linea.cantidad + 1,
                              )
                            }
                            aria-label="Sumar"
                          >
                            <Plus size={12} strokeWidth={2.5} />
                          </button>
                        </div>
                      )}

                      <span className="pos-screen__linea-precio u-cifra">
                        $
                        {(
                          linea.cantidad * linea.precio_unitario
                        ).toLocaleString("es-CO")}
                      </span>
                      <button
                        type="button"
                        className="pos-screen__linea-quitar"
                        onClick={() => quitarLinea(linea.variante_id)}
                        aria-label="Quitar producto"
                      >
                        <Trash2 size={14} strokeWidth={2} />
                      </button>
                    </li>
                  );
                })}
              </ul>
            )}
          </div>

          {ultimaVenta && (
            <p className="pos-screen__ultima-venta">
              Última venta #{ultimaVenta.id} — total $
              {ultimaVenta.total.toLocaleString("es-CO")}
            </p>
          )}

          <ProductosDestacados onSeleccionarVariante={agregarLinea} />
        </div>

        <div className="pos-screen__columna-derecha">
          <CheckoutPanel
            ref={refCheckout}
            cliente={cliente}
            lineas={lineas}
            sesionCajaId={sesion.id}
            canal="POS"
            onBuscarCliente={() => setModalClienteAbierto(true)}
            onVentaCreada={manejarVentaCreada}
          />
        </div>
      </div>

      <ModalCliente
        abierto={modalClienteAbierto}
        onCerrar={() => setModalClienteAbierto(false)}
        onClienteSeleccionado={setCliente}
      />

      {cierreCajaAbierto && (
        <CierreCajaModal
          sesion={sesion}
          onCerrar={() => setCierreCajaAbierto(false)}
          onCajaCerrada={manejarCajaCerrada}
        />
      )}
    </div>
  );
}
