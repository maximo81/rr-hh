// CU5 (necesidades y capacitaciones) y CU10 (planes de desarrollo).
import { useEffect, useState } from "react";
import api from "../api";

export default function Desarrollo() {
  const [tab, setTab] = useState("necesidades");
  const [rows, setRows] = useState([]);
  const [emps, setEmps] = useState([]);
  const [caps, setCaps] = useState([]);
  const vacio = { empleado: "", descripcion: "", motivo: "", prioridad: "media", capacitacion: "", titulo: "", inicio: "", fin: "" };
  const [f, setF] = useState(vacio);
  const [msg, setMsg] = useState("");
  const canEdit = ["admin", "rrhh"].includes(localStorage.getItem("rol"));
  const set = (k) => (e) => setF({ ...f, [k]: e.target.value });

  const loadCaps = () => api.get("/capacitaciones").then((r) => setCaps(r.data));
  useEffect(() => { api.get("/empleados", { params: { limit: 200 } }).then((r) => setEmps(r.data)); loadCaps(); }, []);

  // Selecting an existing training shows its dates; "nueva" lets the user enter title and dates.
  function elegirCapacitacion(e) {
    const v = e.target.value;
    const c = caps.find((x) => String(x.id_capacitacion) === v);
    setF({ ...f, capacitacion: v, titulo: "", inicio: c?.fecha_inicio || "", fin: c?.fecha_fin || "" });
  }
  const load = () => api.get(`/${tab}`).then((r) => setRows(r.data));
  useEffect(() => { load(); setMsg(""); }, [tab]);

  async function guardar(e) {
    e.preventDefault(); setMsg("");
    try {
      if (tab === "necesidades")
        await api.post("/necesidades", {
          empleados_id_empleado: +f.empleado, descripcion: f.descripcion, motivo: f.motivo || null, prioridad: f.prioridad,
          capacitacion_id: f.capacitacion && f.capacitacion !== "nueva" ? +f.capacitacion : null,
          capacitacion_titulo: f.capacitacion === "nueva" ? f.titulo : null,
          fecha_inicio: f.capacitacion === "nueva" ? f.inicio || null : null,
          fecha_fin: f.capacitacion === "nueva" ? f.fin || null : null,
        });
      else
        await api.post("/planes", { empleados_id_empleado: +f.empleado, objetivo_general: f.descripcion });
      setMsg("Guardado"); setF(vacio); load(); loadCaps();
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
            <div><label>Prioridad</label><select value={f.prioridad} onChange={set("prioridad")}><option>baja</option><option>media</option><option>alta</option></select></div>
            <div><label>Capacitación: Título</label><select value={f.capacitacion} onChange={elegirCapacitacion}>
              <option value="">Sin capacitación</option>
              {caps.map((c) => <option key={c.id_capacitacion} value={c.id_capacitacion}>{c.titulo}</option>)}
              <option value="nueva">+ Nueva capacitación…</option></select></div>
            {f.capacitacion === "nueva" && <div><label>Título de la nueva capacitación</label><input value={f.titulo} onChange={set("titulo")} maxLength={120} required /></div>}
            {f.capacitacion && <>
              <div><label>Fecha Inicio</label><input type="date" value={f.inicio} onChange={set("inicio")} disabled={f.capacitacion !== "nueva"} /></div>
              <div><label>Fecha Fin</label><input type="date" value={f.fin} onChange={set("fin")} min={f.inicio || undefined} disabled={f.capacitacion !== "nueva"} /></div></>}</>}
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
