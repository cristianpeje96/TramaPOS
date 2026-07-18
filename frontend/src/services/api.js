/**
 * TramaPos · Cliente HTTP centralizado.
 * Todos los componentes hablan con el backend A TRAVÉS de este archivo —
 * ninguno debe hacer fetch/axios directo. Así, si algún día cambia la URL
 * base, el manejo de auth, o se agrega un interceptor de errores, se toca
 * un solo lugar.
 */

import axios from "axios";

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1",
  timeout: 10000,
  headers: { "Content-Type": "application/json" },
});

// --- Interceptor de autenticación: agrega el token a cada request ---
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem("tramapos_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// --- Interceptor de errores: normaliza el mensaje de error del backend ---
apiClient.interceptors.response.use(
  (respuesta) => respuesta,
  (error) => {
    // Token vencido o inválido: limpia la sesión y fuerza volver al login.
    if (error.response?.status === 401) {
      localStorage.removeItem("tramapos_token");
      localStorage.removeItem("tramapos_usuario");
      window.location.reload();
    }
    const mensaje =
      error.response?.data?.detail ||
      error.message ||
      "Error de conexión con el backend";
    return Promise.reject(new Error(mensaje));
  },
);

// =====================================================================
// AUTENTICACIÓN
// =====================================================================
export const authApi = {
  login: (username, password) =>
    apiClient.post("/auth/login", { username, password }).then((r) => r.data),
  me: () => apiClient.get("/auth/me").then((r) => r.data),
};

export const usuariosApi = {
  listar: () => apiClient.get("/usuarios").then((r) => r.data),
  crear: (datos) => apiClient.post("/usuarios", datos).then((r) => r.data),
};

export const configuracionEmpresaApi = {
  obtener: () => apiClient.get("/configuracion-empresa").then((r) => r.data),
  actualizar: (datos) =>
    apiClient.patch("/configuracion-empresa", datos).then((r) => r.data),
};

export const proveedoresApi = {
  listar: () => apiClient.get("/proveedores").then((r) => r.data),
  buscar: (texto) =>
    apiClient
      .get("/proveedores/buscar", { params: { q: texto } })
      .then((r) => r.data),
  crear: (datos) => apiClient.post("/proveedores", datos).then((r) => r.data),
  actualizar: (id, datos) =>
    apiClient.patch(`/proveedores/${id}`, datos).then((r) => r.data),
};

export const comprasApi = {
  listar: (params = {}) =>
    apiClient.get("/compras", { params }).then((r) => r.data),
  obtener: (id) => apiClient.get(`/compras/${id}`).then((r) => r.data),
  crear: (datos) => apiClient.post("/compras", datos).then((r) => r.data),
  anular: (id, motivo) =>
    apiClient.post(`/compras/${id}/anular`, { motivo }).then((r) => r.data),
};

export const reportesApi = {
  resumen: (params = {}) =>
    apiClient.get("/reportes/resumen", { params }).then((r) => r.data),
  ventasPorDia: (params = {}) =>
    apiClient.get("/reportes/ventas-por-dia", { params }).then((r) => r.data),
  ventasPorMes: (meses = 12) =>
    apiClient
      .get("/reportes/ventas-por-mes", { params: { meses } })
      .then((r) => r.data),
  productosMasVendidos: (params = {}) =>
    apiClient
      .get("/reportes/productos-mas-vendidos", { params })
      .then((r) => r.data),
};

// =====================================================================
// PRODUCTOS
// =====================================================================
export const productosApi = {
  listar: (incluirInactivos = false) =>
    apiClient
      .get("/productos", { params: { incluir_inactivos: incluirInactivos } })
      .then((r) => r.data),
  buscar: (texto) =>
    apiClient
      .get("/productos/buscar", { params: { q: texto } })
      .then((r) => r.data),
  buscarPorCodigo: (codigo) =>
    apiClient.get(`/productos/codigo/${codigo}`).then((r) => r.data),
  crear: (datos) => apiClient.post("/productos", datos).then((r) => r.data),
  actualizar: (id, datos) =>
    apiClient.patch(`/productos/${id}`, datos).then((r) => r.data),
  actualizarVariante: (varianteId, datos) =>
    apiClient
      .patch(`/productos/variantes/${varianteId}`, datos)
      .then((r) => r.data),
  stockBajo: () => apiClient.get("/productos/stock-bajo").then((r) => r.data),
  favoritos: () => apiClient.get("/productos/favoritos").then((r) => r.data),
  masVendidos: (params = {}) =>
    apiClient.get("/productos/mas-vendidos", { params }).then((r) => r.data),
  descargarPlantilla: () =>
    apiClient
      .get("/productos/plantilla", { responseType: "blob" })
      .then((r) => r.data),
  subirCargaMasiva: (archivo) => {
    const formData = new FormData();
    formData.append("archivo", archivo);
    return apiClient
      .post("/productos/carga-masiva", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      })
      .then((r) => r.data);
  },
};

// =====================================================================
// CLIENTES
// =====================================================================
export const clientesApi = {
  buscar: (texto) =>
    apiClient
      .get("/clientes/buscar", { params: { q: texto } })
      .then((r) => r.data),
  crearRapido: (datos) =>
    apiClient.post("/clientes/rapido", datos).then((r) => r.data),
  crear: (datos) => apiClient.post("/clientes", datos).then((r) => r.data),
};

// =====================================================================
// FIDELIZACIÓN
// =====================================================================
export const fidelizacionApi = {
  simularRedencion: (clienteId, puntos) =>
    apiClient
      .get(`/fidelizacion/simular-redencion/${clienteId}`, {
        params: { puntos },
      })
      .then((r) => r.data),
  historial: (clienteId) =>
    apiClient.get(`/fidelizacion/historial/${clienteId}`).then((r) => r.data),
  configuracion: () =>
    apiClient.get("/fidelizacion/configuracion").then((r) => r.data),
  actualizarConfiguracion: (datos) =>
    apiClient.patch("/fidelizacion/configuracion", datos).then((r) => r.data),
  rangoCliente: (clienteId) =>
    apiClient
      .get(`/fidelizacion/rango-cliente/${clienteId}`)
      .then((r) => r.data),
  rangos: {
    listar: () => apiClient.get("/fidelizacion/rangos").then((r) => r.data),
    crear: (datos) =>
      apiClient.post("/fidelizacion/rangos", datos).then((r) => r.data),
    actualizar: (id, datos) =>
      apiClient.patch(`/fidelizacion/rangos/${id}`, datos).then((r) => r.data),
  },
};

// =====================================================================
// VENTAS
// =====================================================================
export const ventasApi = {
  crear: (datos) => apiClient.post("/ventas", datos).then((r) => r.data),
  listar: (params = {}) =>
    apiClient.get("/ventas", { params }).then((r) => r.data),
  obtener: (ventaId) => apiClient.get(`/ventas/${ventaId}`).then((r) => r.data),
};

// =====================================================================
// CAJA
// =====================================================================
export const cajaApi = {
  sesionActual: (cajaFisicaId) =>
    apiClient
      .get("/caja/actual", { params: { caja_fisica_id: cajaFisicaId } })
      .then((r) => r.data),
  sesionesAbiertas: () => apiClient.get("/caja/abiertas").then((r) => r.data),
  abrir: (datos) => apiClient.post("/caja/abrir", datos).then((r) => r.data),
  previewCierre: (sesionId) =>
    apiClient.get(`/caja/${sesionId}/preview-cierre`).then((r) => r.data),
  cerrar: (sesionId, datos) =>
    apiClient.post(`/caja/${sesionId}/cerrar`, datos).then((r) => r.data),
};

export const cajasFisicasApi = {
  listar: () => apiClient.get("/cajas-fisicas").then((r) => r.data),
  crear: (datos) => apiClient.post("/cajas-fisicas", datos).then((r) => r.data),
};

export const devolucionesApi = {
  crear: (datos) => apiClient.post("/devoluciones", datos).then((r) => r.data),
  obtenerPorVenta: (ventaId) =>
    apiClient.get(`/devoluciones/venta/${ventaId}`).then((r) => r.data),
};

export default apiClient;
