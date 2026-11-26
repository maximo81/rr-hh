// CU1 (personas, con asignación de puesto) + CU7 (historial de competencias).
import { useEffect, useState } from "react";
import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import api from "../api";

const COLORS = ["#2a5bd7", "#e07b00", "#1b7a3d", "#8a2be2", "#c2185b"];
const VACIO = { legajo: "", nombre: "", apellido: "", documento: "", email: "", fecha_ingreso: "", puesto: "" };

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

// Modal de confirmación: el puesto elegido no tiene vacantes y se creará una posición nueva.
function NuevaPosicion({ puesto, onConfirm, onCancel }) {
  const [loc, setLoc] = useState("");
  return (
    <div className="modal-bg">
      <div className="card modal">
        <b>Nueva posición</b>
        <p>El puesto <b>{puesto.titulo}</b> no tiene vacantes. Se creará una nueva posición para este empleado.</p>
        <div><label>Localización física (opcional)</label><input value={loc} maxLength={80} onChange={(e) => setLoc(e.target.value)} autoFocus /></div>
        <div className="acciones">
          <button className="sec" onClick={onCancel}>Cancelar</button>
          <button onClick={() => onConfirm(loc)}>Confirmar</button>
        </div>
      </div>
    </div>
  );
}

export default function Empleados() {
  const [list, setList] = useState([]);
  const [puestos, setPuestos] = useState([]);
  const [q, setQ] = useState("");
  const [sel, setSel] = useState(null);
  const [form, setForm] = useState(VACIO);
  const [editando, setEditando] = useState(null); // empleado en edición (null = alta)
  const [modal, setModal] = useState(null); // puesto sin vacantes pendiente de confirmar
  const [msg, setMsg] = useState("");
  const canEdit = ["admin", "rrhh"].includes(localStorage.getItem("rol"));

  const load = () => api.get("/empleados", { params: { q } }).then((r) => setList(r.data));
  const loadPuestos = () => api.get("/puestos").then((r) => setPuestos(r.data));
  useEffect(() => { load(); }, [q]);
  useEffect(() => { if (canEdit) loadPuestos(); }, []);

  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });
  const cambiaPuesto = () => String(editando?.id_puesto ?? "") !== form.puesto;

  function modificar(e) {
    setEditando(e); setMsg("");
    setForm({ legajo: String(e.legajo), nombre: e.nombre, apellido: e.apellido, documento: e.documento,
              email: e.email || "", fecha_ingreso: e.fecha_ingreso, puesto: e.id_puesto ? String(e.id_puesto) : "" });
    window.scrollTo(0, 0);
  }
  function cancelar() { setEditando(null); setForm(VACIO); setMsg(""); }

  function enviar(e) {
    e.preventDefault(); setMsg("");
    const puesto = puestos.find((p) => String(p.id_puesto) === form.puesto);
    if (cambiaPuesto() && puesto && puesto.vacantes === 0) setModal(puesto); // confirmar antes de crear la posición
    else guardar(null);
  }

  async function guardar(localizacion) {
    setModal(null);
    const body = { legajo: Number(form.legajo), nombre: form.nombre, apellido: form.apellido, documento: form.documento,
                   email: form.email || null, fecha_ingreso: form.fecha_ingreso };
    try {
      let id = editando?.id_empleado;
      if (editando) await api.put(`/empleados/${id}`, body);
      else id = (await api.post("/empleados", body)).data.id_empleado;
      if (cambiaPuesto())
        await api.put(`/empleados/${id}/puesto`, { puestos_id_puesto: Number(form.puesto), localizacion_fisica: localizacion || null });
      setMsg(editando ? "Empleado actualizado" : "Empleado creado");
      setEditando(null); setForm(VACIO); load(); loadPuestos();
    } catch (err) { setMsg(err.response?.data?.detail?.toString() || "Error al guardar"); }
  }

  return (
    <>
      <h2>Empleados</h2>
      {sel && <Historial id={sel.id_empleado} nombre={`${sel.nombre} ${sel.apellido}`} onClose={() => setSel(null)} />}
      {modal && <NuevaPosicion puesto={modal} onConfirm={guardar} onCancel={() => setModal(null)} />}
      {canEdit && (
        <form className="card form" onSubmit={enviar}>
          {editando && <b style={{ gridColumn: "1 / -1" }}>Modificando: {editando.apellido}, {editando.nombre}</b>}
          <div><label>Legajo</label><input type="number" value={form.legajo} onChange={set("legajo")} required /></div>
          <div><label>Nombre</label><input value={form.nombre} onChange={set("nombre")} required /></div>
          <div><label>Apellido</label><input value={form.apellido} onChange={set("apellido")} required /></div>
          <div><label>Documento</label><input value={form.documento} onChange={set("documento")} required /></div>
          <div><label>Email</label><input type="email" value={form.email} onChange={set("email")} /></div>
          <div><label>Fecha ingreso</label><input type="date" value={form.fecha_ingreso} onChange={set("fecha_ingreso")} required /></div>
          <div><label>Puesto</label>
            <select value={form.puesto} onChange={set("puesto")} required><option value="">Seleccionar…</option>
              {[["Con vacantes", puestos.filter((p) => p.vacantes > 0)], ["Sin vacantes", puestos.filter((p) => p.vacantes === 0)]]
                .filter(([, ps]) => ps.length > 0).map(([grupo, ps]) => (
                  <optgroup key={grupo} label={grupo}>
                    {ps.map((p) => <option key={p.id_puesto} value={p.id_puesto}>{p.titulo}{p.vacantes > 0 && ` (${p.vacantes} vacante${p.vacantes > 1 ? "s" : ""})`}</option>)}
                  </optgroup>))}</select></div>
          <button>{editando ? "Guardar" : "Agregar"}</button>
          {editando && <button type="button" className="sec" onClick={cancelar}>Cancelar</button>}
          {msg && <span className={/creado|actualizado/.test(msg) ? "ok" : "err"}>{msg}</span>}
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
                <td style={{ whiteSpace: "nowrap" }}>
                  <button onClick={() => setSel(e)}>Historial</button>
                  {canEdit && <> <button className="sec" onClick={() => modificar(e)}>Modificar</button></>}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}
