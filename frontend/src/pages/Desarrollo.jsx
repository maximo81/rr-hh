// CU5 (necesidades y capacitaciones) y CU10 (planes de desarrollo).
import { useEffect, useState } from "react";
import api from "../api";

export default function Desarrollo() {
  const [tab, setTab] = useState("necesidades");
  const [rows, setRows] = useState([]);
  const [emps, setEmps] = useState([]);
  const [f, setF] = useState({ empleado: "", descripcion: "", motivo: "", prioridad: "media" });
  const [msg, setMsg] = useState("");
  const canEdit = ["admin", "rrhh"].includes(localStorage.getItem("rol"));
  const set = (k) => (e) => setF({ ...f, [k]: e.target.value });

  useEffect(() => { api.get("/empleados", { params: { limit: 200 } }).then((r) => setEmps(r.data)); }, []);
  const load = () => api.get(`/${tab}`).then((r) => setRows(r.data));
  useEffect(() => { load(); setMsg(""); }, [tab]);

  async function guardar(e) {
    e.preventDefault(); setMsg("");
    try {
      if (tab === "necesidades")
        await api.post("/necesidades", { empleados_id_empleado: +f.empleado, descripcion: f.descripcion, motivo: f.motivo || null, prioridad: f.prioridad });
      else
        await api.post("/planes", { empleados_id_empleado: +f.empleado, objetivo_general: f.descripcion });
      setMsg("Guardado"); load();
    } catch (err) { setMsg(err.response?.data?.detail?.toString() || "Error"); }
  }

  return (
    <>
      <h2>Desarrollo</h2>
      <div className="tabs">
        {["necesidades", "capacitaciones", "planes"].map((t) => <button key={t} className={tab === t ? "on" : ""} onClick={() => setTab(t)}>{t[0].toUpperCase() + t.slice(1)}</button>)}
      </div>
      {canEdit && tab !== "capacitaciones" && (
        <form className="card form" onSubmit={guardar}>
          <div><label>Persona</label><select value={f.empleado} onChange={set("empleado")} required><option value="">Seleccionar…</option>
            {emps.map((e) => <option key={e.id_empleado} value={e.id_empleado}>{e.apellido}, {e.nombre}</option>)}</select></div>
          <div><label>{tab === "planes" ? "Objetivo general" : "Descripción"}</label><input value={f.descripcion} onChange={set("descripcion")} required /></div>
          {tab === "necesidades" && <>
            <div><label>Motivo</label><input value={f.motivo} onChange={set("motivo")} /></div>
            <div><label>Prioridad</label><select value={f.prioridad} onChange={set("prioridad")}><option>baja</option><option>media</option><option>alta</option></select></div></>}
          <button>Registrar</button>{msg && <span className={msg === "Guardado" ? "ok" : "err"}>{msg}</span>}
        </form>
      )}
      <div className="card">
        {tab === "necesidades" && <table><thead><tr><th>Persona</th><th>Necesidad</th><th>Motivo</th><th>Prioridad</th></tr></thead>
          <tbody>{rows.map((r) => <tr key={r.id_necesidad}><td>{r.apellido}, {r.nombre}</td><td>{r.descripcion}</td><td>{r.motivo}</td><td><span className={`badge ${r.prioridad}`}>{r.prioridad}</span></td></tr>)}</tbody></table>}
        {tab === "capacitaciones" && <table><thead><tr><th>Título</th><th>Inicio</th><th>Fin</th><th>Participantes</th></tr></thead>
          <tbody>{rows.map((r) => <tr key={r.id_capacitacion}><td>{r.titulo}</td><td>{r.fecha_inicio}</td><td>{r.fecha_fin}</td><td>{r.participantes}</td></tr>)}</tbody></table>}
        {tab === "planes" && <table><thead><tr><th>Persona</th><th>Objetivo general</th><th>Avance</th></tr></thead>
          <tbody>{rows.map((r) => <tr key={r.id_plan}><td>{r.apellido}, {r.nombre}</td><td>{r.objetivo_general}</td><td>{r.avance}%</td></tr>)}</tbody></table>}
      </div>
    </>
  );
}
