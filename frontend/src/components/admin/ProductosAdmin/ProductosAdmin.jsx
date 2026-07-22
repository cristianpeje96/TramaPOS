import React, { useEffect, useRef, useState } from "react";
import {
  Plus,
  Trash2,
  Package,
  Pencil,
  Check,
  X,
  Download,
  Upload,
  Star,
} from "lucide-react";

import { productosApi, categoriasApi } from "../../../services/api";
import { SkeletonFilas } from "../../Skeleton/Skeleton";
import "./ProductosAdmin.scss";

const VARIANTE_VACIA = {
  sku: "",
  codigo_barras: "",
  color: "",
  grosor: "",
  precio_venta: "",
  costo_unitario: "",
  porcentaje_iva: "19",
  stock_actual: "",
  stock_minimo: "",
};

export default function ProductosAdmin() {
  const [productos, setProductos] = useState([]);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState(null);
  const [mostrarInactivos, setMostrarInactivos] = useState(false);
  const [categorias, setCategorias] = useState([]);
  const [categoriaId, setCategoriaId] = useState("");
  const [nuevaCategoriaNombre, setNuevaCategoriaNombre] = useState("");
  const [creandoCategoria, setCreandoCategoria] = useState(false);

  // --- Creación de producto nuevo ---
  const [mostrarFormulario, setMostrarFormulario] = useState(false);
  const [nombre, setNombre] = useState("");
  const [descripcion, setDescripcion] = useState("");
  const [unidadMedida, setUnidadMedida] = useState("unidad");
  const [variantes, setVariantes] = useState([{ ...VARIANTE_VACIA }]);
  const [guardando, setGuardando] = useState(false);

  // --- Edición de producto existente ---
  const [edicion, setEdicion] = useState(null); // { productoId, nombre, descripcion, unidad_medida, variantes: [...] }
  const [guardandoEdicion, setGuardandoEdicion] = useState(false);

  // --- Carga masiva ---
  const [subiendoArchivo, setSubiendoArchivo] = useState(false);
  const [resultadoCarga, setResultadoCarga] = useState(null);
  const inputArchivoRef = useRef(null);

  const cargarProductos = async () => {
    setCargando(true);
    try {
      setProductos(await productosApi.listar(mostrarInactivos));
    } catch (err) {
      setError(err.message);
    } finally {
      setCargando(false);
    }
  };

  useEffect(() => {
    cargarProductos();
    categoriasApi
      .listar()
      .then(setCategorias)
      .catch(() => setCategorias([]));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [mostrarInactivos]);

  const crearCategoriaRapida = async () => {
    if (!nuevaCategoriaNombre.trim()) return;
    setCreandoCategoria(true);
    try {
      const categoria = await categoriasApi.crear({
        nombre: nuevaCategoriaNombre.trim(),
      });
      setCategorias((prev) =>
        [...prev, categoria].sort((a, b) => a.nombre.localeCompare(b.nombre)),
      );
      setCategoriaId(String(categoria.id));
      setNuevaCategoriaNombre("");
    } catch (err) {
      setError(err.message);
    } finally {
      setCreandoCategoria(false);
    }
  };

  // ================= Creación =================
  const actualizarVariante = (indice, campo, valor) => {
    setVariantes((prev) =>
      prev.map((v, i) => (i === indice ? { ...v, [campo]: valor } : v)),
    );
  };

  const agregarFilaVariante = () =>
    setVariantes((prev) => [...prev, { ...VARIANTE_VACIA }]);
  const quitarFilaVariante = (indice) =>
    setVariantes((prev) => prev.filter((_, i) => i !== indice));

  const resetearFormulario = () => {
    setNombre("");
    setDescripcion("");
    setUnidadMedida("unidad");
    setCategoriaId("");
    setVariantes([{ ...VARIANTE_VACIA }]);
    setMostrarFormulario(false);
  };

  const guardarProducto = async () => {
    if (
      !nombre.trim() ||
      variantes.some((v) => !v.sku.trim() || !v.precio_venta)
    ) {
      setError(
        "Nombre y al menos una variante con SKU y precio son obligatorios",
      );
      return;
    }
    setGuardando(true);
    setError(null);
    try {
      await productosApi.crear({
        nombre: nombre.trim(),
        descripcion: descripcion.trim() || null,
        unidad_medida: unidadMedida,
        categoria_id: categoriaId ? Number(categoriaId) : null,
        visible_web: false,
        variantes: variantes.map((v) => ({
          sku: v.sku.trim(),
          codigo_barras: v.codigo_barras.trim() || null,
          color: v.color.trim() || null,
          grosor: v.grosor.trim() || null,
          precio_venta: Number(v.precio_venta),
          costo_unitario: v.costo_unitario ? Number(v.costo_unitario) : null,
          porcentaje_iva: Number(v.porcentaje_iva) || 0,
          stock_actual: Number(v.stock_actual) || 0,
          stock_minimo: Number(v.stock_minimo) || 0,
        })),
      });
      resetearFormulario();
      await cargarProductos();
    } catch (err) {
      setError(err.message);
    } finally {
      setGuardando(false);
    }
  };

  // ================= Edición =================
  const alternarFavorito = async (producto) => {
    setError(null);
    try {
      await productosApi.actualizar(producto.id, {
        favorito: !producto.favorito,
      });
      await cargarProductos();
    } catch (err) {
      setError(err.message);
    }
  };

  const reactivarProducto = async (producto) => {
    setError(null);
    try {
      await productosApi.actualizar(producto.id, { activo: true });
      await cargarProductos();
    } catch (err) {
      setError(err.message);
    }
  };

  const iniciarEdicion = (producto) => {
    setEdicion({
      productoId: producto.id,
      nombre: producto.nombre,
      descripcion: producto.descripcion || "",
      unidad_medida: producto.unidad_medida,
      categoria_id: producto.categoria_id || "",
      activo: producto.activo,
      variantes: producto.variantes.map((v) => ({
        id: v.id,
        sku: v.sku,
        codigo_barras: v.codigo_barras || "",
        color: v.color || "",
        grosor: v.grosor || "",
        precio_venta: v.precio_venta,
        costo_unitario: v.costo_unitario ?? "",
        porcentaje_iva: v.porcentaje_iva ?? 19,
        stock_actual: v.stock_actual,
        stock_minimo: v.stock_minimo,
      })),
    });
  };

  const cancelarEdicion = () => setEdicion(null);

  const actualizarCampoEdicion = (campo, valor) =>
    setEdicion((prev) => ({ ...prev, [campo]: valor }));

  const actualizarVarianteEdicion = (indice, campo, valor) =>
    setEdicion((prev) => ({
      ...prev,
      variantes: prev.variantes.map((v, i) =>
        i === indice ? { ...v, [campo]: valor } : v,
      ),
    }));

  const guardarEdicion = async () => {
    setGuardandoEdicion(true);
    setError(null);
    try {
      await productosApi.actualizar(edicion.productoId, {
        nombre: edicion.nombre.trim(),
        descripcion: edicion.descripcion.trim() || null,
        unidad_medida: edicion.unidad_medida,
        categoria_id: edicion.categoria_id
          ? Number(edicion.categoria_id)
          : null,
        activo: edicion.activo,
      });

      await Promise.all(
        edicion.variantes.map((v) =>
          productosApi.actualizarVariante(v.id, {
            sku: v.sku.trim(),
            codigo_barras: v.codigo_barras.trim() || null,
            color: v.color.trim() || null,
            grosor: v.grosor.trim() || null,
            precio_venta: Number(v.precio_venta),
            costo_unitario: v.costo_unitario ? Number(v.costo_unitario) : null,
            porcentaje_iva: Number(v.porcentaje_iva) || 0,
            stock_actual: Number(v.stock_actual),
            stock_minimo: Number(v.stock_minimo),
          }),
        ),
      );

      setEdicion(null);
      await cargarProductos();
    } catch (err) {
      setError(err.message);
    } finally {
      setGuardandoEdicion(false);
    }
  };

  // ================= Carga masiva =================
  const descargarPlantilla = async () => {
    try {
      const blob = await productosApi.descargarPlantilla();
      const url = window.URL.createObjectURL(blob);
      const enlace = document.createElement("a");
      enlace.href = url;
      enlace.download = "plantilla_productos_tramapos.xlsx";
      document.body.appendChild(enlace);
      enlace.click();
      enlace.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setError(err.message);
    }
  };

  const subirArchivo = async (evento) => {
    const archivo = evento.target.files?.[0];
    if (!archivo) return;

    setSubiendoArchivo(true);
    setResultadoCarga(null);
    setError(null);
    try {
      const resultado = await productosApi.subirCargaMasiva(archivo);
      setResultadoCarga(resultado);
      await cargarProductos();
    } catch (err) {
      setError(err.message);
    } finally {
      setSubiendoArchivo(false);
      if (inputArchivoRef.current) inputArchivoRef.current.value = "";
    }
  };

  return (
    <div className="productos-admin">
      <header className="productos-admin__header">
        <h2 className="productos-admin__titulo">
          <Package size={18} strokeWidth={2} />
          Productos
        </h2>
        <div className="productos-admin__acciones-header">
          <label className="productos-admin__checkbox-activo">
            <input
              type="checkbox"
              checked={mostrarInactivos}
              onChange={(e) => setMostrarInactivos(e.target.checked)}
            />
            Mostrar inactivos
          </label>
          <button
            type="button"
            className="productos-admin__boton-plantilla"
            onClick={descargarPlantilla}
          >
            <Download size={14} strokeWidth={2} />
            Plantilla Excel
          </button>
          <button
            type="button"
            className="productos-admin__boton-subir"
            onClick={() => inputArchivoRef.current?.click()}
            disabled={subiendoArchivo}
          >
            <Upload size={14} strokeWidth={2} />
            {subiendoArchivo ? "Subiendo…" : "Cargar Excel"}
          </button>
          <input
            ref={inputArchivoRef}
            type="file"
            accept=".xlsx,.xlsm"
            style={{ display: "none" }}
            onChange={subirArchivo}
          />
          <button
            type="button"
            className="productos-admin__boton-nuevo"
            onClick={() => setMostrarFormulario((v) => !v)}
          >
            <Plus size={16} strokeWidth={2} />
            {mostrarFormulario ? "Cancelar" : "Nuevo producto"}
          </button>
        </div>
      </header>

      {resultadoCarga && (
        <div className="productos-admin__resultado-carga">
          <p>
            <strong>{resultadoCarga.productos_creados}</strong> productos nuevos
            · <strong>{resultadoCarga.variantes_creadas}</strong> variantes
            creadas
          </p>
          {resultadoCarga.errores.length > 0 && (
            <ul>
              {resultadoCarga.errores.map((err, i) => (
                <li key={i}>{err}</li>
              ))}
            </ul>
          )}
        </div>
      )}

      {error && <p className="productos-admin__error">{error}</p>}

      {mostrarFormulario && (
        <div className="productos-admin__formulario">
          <div className="productos-admin__campos-basicos">
            <input
              type="text"
              placeholder="Nombre del producto (ej: Hilo Guajira)"
              value={nombre}
              onChange={(e) => setNombre(e.target.value)}
            />
            <input
              type="text"
              placeholder="Descripción (opcional)"
              value={descripcion}
              onChange={(e) => setDescripcion(e.target.value)}
            />
            <select
              value={unidadMedida}
              onChange={(e) => setUnidadMedida(e.target.value)}
            >
              <option value="unidad">Unidad</option>
              <option value="madeja">Madeja</option>
              <option value="metro">Metro</option>
              <option value="kg">Peso (kg / gramos en el POS)</option>
            </select>
            <select
              value={categoriaId}
              onChange={(e) => setCategoriaId(e.target.value)}
            >
              <option value="">Sin categoría</option>
              {categorias.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.nombre}
                </option>
              ))}
            </select>
          </div>

          <div className="productos-admin__nueva-categoria">
            <input
              type="text"
              placeholder="O crea una categoría nueva (ej: Mercería)"
              value={nuevaCategoriaNombre}
              onChange={(e) => setNuevaCategoriaNombre(e.target.value)}
            />
            <button
              type="button"
              disabled={creandoCategoria}
              onClick={crearCategoriaRapida}
            >
              {creandoCategoria ? "Creando…" : "Crear categoría"}
            </button>
          </div>

          <p className="productos-admin__subtitulo">Variantes (color/grosor)</p>
          <div className="productos-admin__variantes">
            {variantes.map((variante, indice) => (
              <div key={indice} className="productos-admin__variante-fila">
                <input
                  type="text"
                  placeholder="SKU"
                  value={variante.sku}
                  onChange={(e) =>
                    actualizarVariante(indice, "sku", e.target.value)
                  }
                />
                <input
                  type="text"
                  placeholder="Código de barras"
                  value={variante.codigo_barras}
                  onChange={(e) =>
                    actualizarVariante(indice, "codigo_barras", e.target.value)
                  }
                />
                <input
                  type="text"
                  placeholder="Color"
                  value={variante.color}
                  onChange={(e) =>
                    actualizarVariante(indice, "color", e.target.value)
                  }
                />
                <input
                  type="text"
                  placeholder="Grosor"
                  value={variante.grosor}
                  onChange={(e) =>
                    actualizarVariante(indice, "grosor", e.target.value)
                  }
                />
                <input
                  type="number"
                  min="0"
                  placeholder="Precio venta"
                  value={variante.precio_venta}
                  onChange={(e) =>
                    actualizarVariante(indice, "precio_venta", e.target.value)
                  }
                />
                <input
                  type="number"
                  min="0"
                  placeholder="Costo"
                  value={variante.costo_unitario}
                  onChange={(e) =>
                    actualizarVariante(indice, "costo_unitario", e.target.value)
                  }
                />
                <input
                  type="number"
                  min="0"
                  max="100"
                  placeholder="% IVA"
                  value={variante.porcentaje_iva}
                  onChange={(e) =>
                    actualizarVariante(indice, "porcentaje_iva", e.target.value)
                  }
                />
                <input
                  type="number"
                  min="0"
                  placeholder="Stock inicial"
                  value={variante.stock_actual}
                  onChange={(e) =>
                    actualizarVariante(indice, "stock_actual", e.target.value)
                  }
                />
                <input
                  type="number"
                  min="0"
                  placeholder="Stock mínimo"
                  value={variante.stock_minimo}
                  onChange={(e) =>
                    actualizarVariante(indice, "stock_minimo", e.target.value)
                  }
                />
                {variantes.length > 1 && (
                  <button
                    type="button"
                    className="productos-admin__variante-quitar"
                    onClick={() => quitarFilaVariante(indice)}
                  >
                    <Trash2 size={14} strokeWidth={2} />
                  </button>
                )}
              </div>
            ))}
          </div>
          <button
            type="button"
            className="productos-admin__agregar-variante"
            onClick={agregarFilaVariante}
          >
            <Plus size={14} strokeWidth={2} />
            Agregar variante
          </button>

          <button
            type="button"
            className="productos-admin__guardar"
            disabled={guardando}
            onClick={guardarProducto}
          >
            {guardando ? "Guardando…" : "Guardar producto"}
          </button>
        </div>
      )}

      {cargando ? (
        <SkeletonFilas filas={4} columnas={4} />
      ) : (
        <div className="productos-admin__lista">
          {productos.map((producto) => {
            const enEdicion = edicion?.productoId === producto.id;
            return (
              <div
                key={producto.id}
                className={`productos-admin__tarjeta ${
                  !producto.activo ? "productos-admin__tarjeta--inactiva" : ""
                }`}
              >
                {enEdicion ? (
                  <>
                    <div className="productos-admin__campos-basicos productos-admin__campos-basicos--edicion">
                      <input
                        type="text"
                        value={edicion.nombre}
                        onChange={(e) =>
                          actualizarCampoEdicion("nombre", e.target.value)
                        }
                      />
                      <input
                        type="text"
                        value={edicion.descripcion}
                        placeholder="Descripción"
                        onChange={(e) =>
                          actualizarCampoEdicion("descripcion", e.target.value)
                        }
                      />
                      <select
                        value={edicion.unidad_medida}
                        onChange={(e) =>
                          actualizarCampoEdicion(
                            "unidad_medida",
                            e.target.value,
                          )
                        }
                      >
                        <option value="unidad">Unidad</option>
                        <option value="madeja">Madeja</option>
                        <option value="metro">Metro</option>
                        <option value="kg">Peso (kg / gramos en el POS)</option>
                      </select>
                      <select
                        value={edicion.categoria_id}
                        onChange={(e) =>
                          actualizarCampoEdicion("categoria_id", e.target.value)
                        }
                      >
                        <option value="">Sin categoría</option>
                        {categorias.map((c) => (
                          <option key={c.id} value={c.id}>
                            {c.nombre}
                          </option>
                        ))}
                      </select>
                      <label className="productos-admin__checkbox-activo">
                        <input
                          type="checkbox"
                          checked={edicion.activo}
                          onChange={(e) =>
                            actualizarCampoEdicion("activo", e.target.checked)
                          }
                        />
                        Producto activo
                      </label>
                    </div>

                    <div className="productos-admin__variantes">
                      {edicion.variantes.map((variante, indice) => (
                        <div
                          key={variante.id}
                          className="productos-admin__variante-fila"
                        >
                          <input
                            type="text"
                            placeholder="SKU"
                            value={variante.sku}
                            onChange={(e) =>
                              actualizarVarianteEdicion(
                                indice,
                                "sku",
                                e.target.value,
                              )
                            }
                          />
                          <input
                            type="text"
                            placeholder="Código de barras"
                            value={variante.codigo_barras}
                            onChange={(e) =>
                              actualizarVarianteEdicion(
                                indice,
                                "codigo_barras",
                                e.target.value,
                              )
                            }
                          />
                          <input
                            type="text"
                            placeholder="Color"
                            value={variante.color}
                            onChange={(e) =>
                              actualizarVarianteEdicion(
                                indice,
                                "color",
                                e.target.value,
                              )
                            }
                          />
                          <input
                            type="text"
                            placeholder="Grosor"
                            value={variante.grosor}
                            onChange={(e) =>
                              actualizarVarianteEdicion(
                                indice,
                                "grosor",
                                e.target.value,
                              )
                            }
                          />
                          <input
                            type="number"
                            min="0"
                            placeholder="Precio venta"
                            value={variante.precio_venta}
                            onChange={(e) =>
                              actualizarVarianteEdicion(
                                indice,
                                "precio_venta",
                                e.target.value,
                              )
                            }
                          />
                          <input
                            type="number"
                            min="0"
                            placeholder="Costo"
                            value={variante.costo_unitario}
                            onChange={(e) =>
                              actualizarVarianteEdicion(
                                indice,
                                "costo_unitario",
                                e.target.value,
                              )
                            }
                          />
                          <input
                            type="number"
                            min="0"
                            max="100"
                            placeholder="% IVA"
                            value={variante.porcentaje_iva}
                            onChange={(e) =>
                              actualizarVarianteEdicion(
                                indice,
                                "porcentaje_iva",
                                e.target.value,
                              )
                            }
                          />
                          <input
                            type="number"
                            min="0"
                            placeholder="Stock actual"
                            value={variante.stock_actual}
                            onChange={(e) =>
                              actualizarVarianteEdicion(
                                indice,
                                "stock_actual",
                                e.target.value,
                              )
                            }
                          />
                          <input
                            type="number"
                            min="0"
                            placeholder="Stock mínimo"
                            value={variante.stock_minimo}
                            onChange={(e) =>
                              actualizarVarianteEdicion(
                                indice,
                                "stock_minimo",
                                e.target.value,
                              )
                            }
                          />
                        </div>
                      ))}
                    </div>

                    <div className="productos-admin__acciones-edicion">
                      <button
                        type="button"
                        className="productos-admin__guardar"
                        disabled={guardandoEdicion}
                        onClick={guardarEdicion}
                      >
                        <Check size={14} strokeWidth={2} />
                        {guardandoEdicion ? "Guardando…" : "Guardar cambios"}
                      </button>
                      <button
                        type="button"
                        className="productos-admin__cancelar-edicion"
                        onClick={cancelarEdicion}
                      >
                        <X size={14} strokeWidth={2} />
                        Cancelar
                      </button>
                    </div>
                  </>
                ) : (
                  <>
                    <div className="productos-admin__tarjeta-header">
                      <div>
                        <p className="productos-admin__tarjeta-nombre">
                          {producto.nombre}
                          {!producto.activo && (
                            <span className="productos-admin__badge-inactivo">
                              Inactivo
                            </span>
                          )}
                        </p>
                        {producto.descripcion && (
                          <p className="productos-admin__tarjeta-descripcion">
                            {producto.descripcion}
                          </p>
                        )}
                      </div>
                      <div className="productos-admin__tarjeta-acciones">
                        {!producto.activo && (
                          <button
                            type="button"
                            className="productos-admin__reactivar"
                            onClick={() => reactivarProducto(producto)}
                          >
                            Reactivar
                          </button>
                        )}
                        <button
                          type="button"
                          className={`productos-admin__favorito ${
                            producto.favorito
                              ? "productos-admin__favorito--activo"
                              : ""
                          }`}
                          onClick={() => alternarFavorito(producto)}
                          title={
                            producto.favorito
                              ? "Quitar de favoritos"
                              : "Marcar como favorito"
                          }
                        >
                          <Star
                            size={16}
                            strokeWidth={2}
                            fill={producto.favorito ? "currentColor" : "none"}
                          />
                        </button>
                        <button
                          type="button"
                          className="productos-admin__editar"
                          onClick={() => iniciarEdicion(producto)}
                        >
                          <Pencil size={14} strokeWidth={2} />
                          Editar
                        </button>
                      </div>
                    </div>

                    <table className="productos-admin__tabla">
                      <thead>
                        <tr>
                          <th>Variante</th>
                          <th>SKU</th>
                          <th>Precio</th>
                          <th>Stock</th>
                        </tr>
                      </thead>
                      <tbody>
                        {producto.variantes.map((variante) => (
                          <tr key={variante.id}>
                            <td>
                              {[variante.color, variante.grosor]
                                .filter(Boolean)
                                .join(" · ") || "—"}
                            </td>
                            <td className="u-cifra">{variante.sku}</td>
                            <td className="u-cifra">
                              ${variante.precio_venta.toLocaleString("es-CO")}
                            </td>
                            <td className="u-cifra">{variante.stock_actual}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
