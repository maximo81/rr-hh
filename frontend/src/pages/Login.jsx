// Login: envía credenciales a /auth/login y guarda el JWT.
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../api";

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const nav = useNavigate();

  async function submit(e) {
    e.preventDefault();
    setError("");
    try {
      const { data } = await api.post("/auth/login", { email, password });
      localStorage.setItem("token", data.access_token);
      localStorage.setItem("rol", data.rol);
      localStorage.setItem("email", data.email);
      nav("/");
      window.location.reload(); // refresca el menú según el rol
    } catch (err) {
      setError(err.response?.status === 401 ? "Credenciales inválidas" : "No se pudo conectar con el servidor");
    }
  }

  return (
    <div className="login">
      <form className="card" onSubmit={submit}>
        <h2>Ingresar a RRHH</h2>
        <div><label>Email</label><input value={email} onChange={(e) => setEmail(e.target.value)} type="email" required /></div>
        <div><label>Contraseña</label><input value={password} onChange={(e) => setPassword(e.target.value)} type="password" required /></div>
        {error && <div className="err">{error}</div>}
        <button>Entrar</button>
      </form>
    </div>
  );
}
