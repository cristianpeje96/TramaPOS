import React, { useEffect, useState } from "react";
import { Plus, Truck, Pencil, Check, X } from "lucide-react";

import { proveedoresApi } from "../../../services/api";
import { SkeletonFilas } from "../../Skeleton/Skeleton";
import "./ProveedoresAdmin.scss";

export default function ProveedoresAdmin() {
  const [proveedores, setProveedores] = useState([]);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState(null);

  const [mostrarForm, setMostrarForm] = useState(false);
  const [nombre, setNombre] = useState("");
  const [nit, setNit] = useState("");
  const [telefono, setTelefono] = useState("");
  const [email, setEmail] = useState("");
  const [guardando, setGuardando] = useState(false);

  const [editandoId, setEditandoId] = useState(null);
  const [edicion, setEdicion] = useState({});

  const cargar = async () => {
    setCargando(true);
    try {
      setProveedores(await proveedoresApi.listar());
    } catch (err) {
      setError(err.message);
    } finally {
      setCargando(false);
    }
  };

  useEffect(() => {
    cargar();
  }, []);

  const crear = async () => {
    if (!nombre.trim()) return;
    setGuardando(true);
    setError(null);
    try {
      await proveedoresApi.crear({
        nombre_comercial: nombre.trim(),
        nit_o_documento: nit.trim() || null,
        telefono: telefono.trim() || null,
        email: email.trim() || null,
      });
      setNombre("");
      setNit("");
      setTelefono("");
      setEmail("");
      setMostrarForm(false);
      await cargar();
    } catch (err) {
      setError(err.message);
    } finally {
      setGuardando(false);
    }
  };

  const iniciarEdicion = (p) => {
    setEditandoId(p.id);
    setEdicion({
      nombre_comercial: p.nombre_comercial,
      nit_o_documento: p.nit_o_documento || "",
      telefono: p.telefono || "",
      email: p.email || "",
    });
  };

  const guardarEdicion = async () => {
    setGuardando(true);
    setError(null);
    try {
      await proveedoresApi.actualizar(editandoId, edicion);
      setEditandoId(null);
      await cargar();
    } catch (err) {
      setError(err.message);
    } finally {
      setGuardando(false);
    }
  };

  return (
    <div className="proveedores-admin">
      <header className="proveedores-admin__header">
        <h2 className="proveedores-admin__titulo">
          <Truck size={18} strokeWidth={2} />
          Proveedores
        </h2>
        <button type="button" onClick={() => setMostrarForm((v) => !v)}>
          <Plus size={14} strokeWidth={2} />
          {mostrarForm ? "Cancelar" : "Nuevo proveedor"}
        </button>
      </header>

      {error && <p className="proveedores-admin__error">{error}</p>}

      {mostrarForm && (
        <div className="proveedores-admin__form">
          <input
            placeholder="Nombre comercial"
            value={nombre}
            onChange={(e) => setNombre(e.target.value)}
          />
          <input
            placeholder="NIT / documento"
            value={nit}
            onChange={(e) => setNit(e.target.value)}
          />
          <input
            placeholder="Teléfono"
            value={telefono}
            onChange={(e) => setTelefono(e.target.value)}
          />
          <input
            placeholder="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
          <button type="button" disabled={guardando} onClick={crear}>
            {guardando ? "Guardando…" : "Guardar"}
          </button>
        </div>
      )}

      {cargando ? (
        <SkeletonFilas filas={3} columnas={4} />
      ) : (
        <table className="proveedores-admin__tabla">
          <thead>
            <tr>
              <th>Nombre</th>
              <th>NIT</th>
              <th>Teléfono</th>
              <th>Email</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {proveedores.map((p) =>
              editandoId === p.id ? (
                <tr key={p.id}>
                  <td>
                    <input
                      value={edicion.nombre_comercial}
                      onChange={(e) =>
                        setEdicion({
                          ...edicion,
                          nombre_comercial: e.target.value,
                        })
                      }
                    />
                  </td>
                  <td>
                    <input
                      value={edicion.nit_o_documento}
                      onChange={(e) =>
                        setEdicion({
                          ...edicion,
                          nit_o_documento: e.target.value,
                        })
                      }
                    />
                  </td>
                  <td>
                    <input
                      value={edicion.telefono}
                      onChange={(e) =>
                        setEdicion({ ...edicion, telefono: e.target.value })
                      }
                    />
                  </td>
                  <td>
                    <input
                      value={edicion.email}
                      onChange={(e) =>
                        setEdicion({ ...edicion, email: e.target.value })
                      }
                    />
                  </td>
                  <td className="proveedores-admin__acciones">
                    <button type="button" onClick={guardarEdicion}>
                      <Check size={14} strokeWidth={2} />
                    </button>
                    <button type="button" onClick={() => setEditandoId(null)}>
                      <X size={14} strokeWidth={2} />
                    </button>
                  </td>
                </tr>
              ) : (
                <tr key={p.id}>
                  <td>{p.nombre_comercial}</td>
                  <td className="u-cifra">{p.nit_o_documento || "—"}</td>
                  <td className="u-cifra">{p.telefono || "—"}</td>
                  <td>{p.email || "—"}</td>
                  <td className="proveedores-admin__acciones">
                    <button type="button" onClick={() => iniciarEdicion(p)}>
                      <Pencil size={14} strokeWidth={2} />
                    </button>
                  </td>
                </tr>
              ),
            )}
          </tbody>
        </table>
      )}
    </div>
  );
}
