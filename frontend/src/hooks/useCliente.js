import { useCallback, useState } from "react";

import { clientesApi } from "../services/api";

/**
 * useCliente
 * Maneja el cliente seleccionado en la venta actual (el que se busca/crea
 * con F7) y expone helpers para buscar y limpiar. No guarda nada en
 * localStorage a propósito: el cliente seleccionado es válido solo
 * durante la venta activa, se limpia con Esc o al confirmar F10.
 */
export function useCliente() {
  const [cliente, setCliente] = useState(null);
  const [buscando, setBuscando] = useState(false);
  const [resultados, setResultados] = useState([]);
  const [error, setError] = useState(null);

  const buscar = useCallback(async (texto) => {
    if (!texto || texto.trim().length < 1) {
      setResultados([]);
      return;
    }
    setBuscando(true);
    setError(null);
    try {
      const encontrados = await clientesApi.buscar(texto.trim());
      setResultados(encontrados);
    } catch (err) {
      setError(err.message);
      setResultados([]);
    } finally {
      setBuscando(false);
    }
  }, []);

  /** Flujo típico de F7: documento + nombre, crea si no existe. */
  const buscarOCrearRapido = useCallback(
    async (numeroDocumento, nombreCompleto) => {
      setError(null);
      try {
        const clienteEncontradoOCreado = await clientesApi.crearRapido({
          numero_documento: numeroDocumento,
          nombre_completo: nombreCompleto,
        });
        setCliente(clienteEncontradoOCreado);
        return clienteEncontradoOCreado;
      } catch (err) {
        setError(err.message);
        return null;
      }
    },
    [],
  );

  const seleccionar = useCallback((clienteSeleccionado) => {
    setCliente(clienteSeleccionado);
    setResultados([]);
  }, []);

  const limpiar = useCallback(() => {
    setCliente(null);
    setResultados([]);
    setError(null);
  }, []);

  return {
    cliente,
    buscando,
    resultados,
    error,
    buscar,
    buscarOCrearRapido,
    seleccionar,
    limpiar,
  };
}
