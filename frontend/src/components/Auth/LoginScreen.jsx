import React, { useState } from "react";
import { Lock, User } from "lucide-react";

import { useAuth } from "./AuthProvider";
import "./LoginScreen.scss";

export default function LoginScreen() {
  const { login } = useAuth();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState(null);

  const manejarSubmit = async (evento) => {
    evento.preventDefault();
    if (!username.trim() || !password) return;

    setCargando(true);
    setError(null);
    try {
      await login(username.trim(), password);
    } catch (err) {
      setError(err.message);
    } finally {
      setCargando(false);
    }
  };

  return (
    <div className="login-screen">
      <form className="login-screen__card" onSubmit={manejarSubmit}>
        <h1 className="login-screen__marca">TramaPos</h1>
        <p className="login-screen__subtitulo">Inicia sesión para continuar</p>

        <label className="login-screen__campo">
          <User size={16} strokeWidth={2} />
          <input
            type="text"
            placeholder="Usuario"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            autoFocus
          />
        </label>

        <label className="login-screen__campo">
          <Lock size={16} strokeWidth={2} />
          <input
            type="password"
            placeholder="Contraseña"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </label>

        {error && <p className="login-screen__error">{error}</p>}

        <button type="submit" disabled={cargando}>
          {cargando ? "Ingresando…" : "Ingresar"}
        </button>
      </form>
    </div>
  );
}
