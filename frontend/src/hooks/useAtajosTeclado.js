import { useEffect } from "react";

/**
 * useAtajosTeclado
 * Centraliza los atajos globales del POS para que no queden listeners
 * de keydown repartidos por distintos componentes (eso fue justo lo que
 * teníamos en CheckoutPanel.jsx con F4/F9 — este hook los reemplaza).
 *
 * Uso:
 *   useAtajosTeclado({
 *     onBuscarProducto: () => refBuscador.current?.focus(),  // F2
 *     onSeleccionarPago: () => ciclarMetodoPago(),            // F4
 *     onBuscarCliente: () => abrirModalCliente(),             // F7
 *     onAplicarPuntos: () => activarInputPuntos(),            // F9
 *     onAbrirCajonManual: () => hardwareAgent.abrirCajon(),   // Ctrl+Shift+O
 *     onProcesarVenta: () => confirmarVenta(),                // F10
 *     onCancelarVenta: () => limpiarVentaActual(),            // Esc
 *   });
 *
 * Cualquier callback que no se pase, simplemente se ignora — cada pantalla
 * activa solo los atajos que le aplican (ej: la pantalla de apertura de
 * caja no necesita F2 ni F9).
 */
export function useAtajosTeclado({
  onBuscarProducto,
  onSeleccionarPago,
  onBuscarCliente,
  onAplicarPuntos,
  onAbrirCajonManual,
  onProcesarVenta,
  onCancelarVenta,
} = {}) {
  useEffect(() => {
    const manejarTecla = (evento) => {
      // Ctrl+Shift+O primero: es una combinación, no una tecla de función sola
      if (
        evento.ctrlKey &&
        evento.shiftKey &&
        evento.key.toUpperCase() === "O"
      ) {
        evento.preventDefault();
        onAbrirCajonManual?.();
        return;
      }

      switch (evento.key) {
        case "F2":
          evento.preventDefault();
          onBuscarProducto?.();
          break;
        case "F4":
          evento.preventDefault();
          onSeleccionarPago?.();
          break;
        case "F7":
          evento.preventDefault();
          onBuscarCliente?.();
          break;
        case "F9":
          evento.preventDefault();
          onAplicarPuntos?.();
          break;
        case "F10":
          evento.preventDefault();
          onProcesarVenta?.();
          break;
        case "Escape":
          evento.preventDefault();
          onCancelarVenta?.();
          break;
        default:
          break;
      }
    };

    window.addEventListener("keydown", manejarTecla);
    return () => window.removeEventListener("keydown", manejarTecla);
  }, [
    onBuscarProducto,
    onSeleccionarPago,
    onBuscarCliente,
    onAplicarPuntos,
    onAbrirCajonManual,
    onProcesarVenta,
    onCancelarVenta,
  ]);
}
