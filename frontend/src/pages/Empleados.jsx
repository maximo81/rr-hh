// CU1 (personas) + CU7 (historial de competencias).
import { useEffect, useState } from "react";
import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import api from "../api";

const COLORS = ["#2a5bd7", "#e07b00", "#1b7a3d", "#8a2be2", "#c2185b"];

function Historial({ id, nombre, onClose }) {
  const [rows, setRows] = useState([]);
  useEffect(() => { api.get(`/empleados/${id}/historial-competencias`).then((r) => setRows(r.data)); }, [id]);
  // Pivot: una fila por fecha, una columna por competencia
  const comps = [...new Set(rows.map((r) => r.competencia))];
  const fechas = [...new Set(rows.map((r) => r.fecha))];
  const data = fechas.map((f) => Object.fromEntries([["fecha", f], ...rows.filter((r) => r.fecha === f).map((r) => [r.competencia, r.nivel])]));
  return (
    <div className="card">
      <b>Historial de competencias · {nombre}</b> <button style={{ float: "right" }} onClick={onClose}>Cerrar</button>
      {rows.length === 0 ? <p>Sin evaluaciones.</p> : (
        <div style={{ height: 260, marginTop: 10 }}>
          <ResponsiveContainer>
            <LineChart data={data}>
              <CartesianGrid stroke="#e3e7ee" /><XAxis dataKey="fecha" /><YAxis domain={[1, 5]} allowDecimals={false} /><Tooltip /><Legend />
              {comps.map((c, i) => <Line key={c} dataKey={c} stroke={COLORS[i % 5]} connectNulls strokeWidth={2} />)}
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}

export default function Empleados() {
  const [list, setList] = useState([]);
  const [q, setQ] = useState("");
  const [sel, setSel] = useState(null);
  const [form, setForm] = useState({ legajo: "", nombre: "", apellido: "", documento: "", email: "", fecha_ingreso: "" });
  const [msg, setMsg] = useState("");
  const canEdit = ["admin", "rrhh"].includes(localStorage.getItem("rol"));

  const load = () => api.get("/empleados", { params: { q } }).then((r) => setList(r.data));
  useEffect(() => { load(); }, [q]);

  async function crear(e) {
    e.preventDefault(); setMsg("");
    try {
      await api.post("/empleados", { ...form, legajo: Number(form.legajo), email: form.email || null });
      setMsg("Empleado creado"); setForm({ legajo: "", nombre: "", apellido: "", documento: "", email: "", fecha_ingreso: "" }); load();
    } catch (err) { setMsg(err.response?.data?.detail?.toString() || "Error al guardar"); }
  }
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  return (
    <>
      <h2>Empleados</h2>
      {sel && <Historial id={sel.id_empleado} nombre={`${sel.nombre} ${sel.apellido}`} onClose={() => setSel(null)} />}
      {canEdit && (
        <form className="card form" onSubmit={crear}>
          <div><label>Legajo</label><input type="number" value={form.legajo} onChange={set("legajo")} required /></div>
          <div><label>Nombre</label><input value={form.nombre} onChange={set("nombre")} required /></div>
          <div><label>Apellido</label><input value={form.apellido} onChange={set("apellido")} required /></div>
          <div><label>Documento</label><input value={form.documento} onChange={set("documento")} required /></div>
          <div><label>Email</label><input type="email" value={form.email} onChange={set("email")} /></div>
          <div><label>Fecha ingreso</label><input type="date" value={form.fecha_ingreso} onChange={set("fecha_ingreso")} required /></div>
          <button>Agregar</button>
          {msg && <span className={msg.includes("creado") ? "ok" : "err"}>{msg}</span>}
        </form>
      )}
      <div className="card">
        <input placeholder="Buscar por nombre, apellido o documento…" value={q} onChange={(e) => setQ(e.target.value)} />
        <table style={{ marginTop: 12 }}>
          <thead><tr><th>Legajo</th><th>Nombre</th><th>Puesto</th><th>Unidad</th><th>Ingreso</th><th></th></tr></thead>
          <tbody>
            {list.map((e) => (
              <tr key={e.id_empleado}>
                <td>{e.legajo}</td><td>{e.apellido}, {e.nombre}</td><td>{e.puesto}</td><td>{e.departamento}</td><td>{e.fecha_ingreso}</td>
                <td><button onClick={() => setSel(e)}>Historial</button></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}
