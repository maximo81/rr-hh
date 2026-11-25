// CU3 (desempeño) y CU4 (competencias): formularios + últimas evaluaciones.
import { useEffect, useState } from "react";
import api from "../api";

export default function Evaluaciones() {
  const [tab, setTab] = useState("competencias");
  const [emps, setEmps] = useState([]);
  const [comps, setComps] = useState([]);
  const [rows, setRows] = useState([]);
  const [f, setF] = useState({ empleado: "", competencia: "", nivel: 3, periodo: "2026-S2", puntaje: 7, obs: "" });
  const [msg, setMsg] = useState("");
  const set = (k) => (e) => setF({ ...f, [k]: e.target.value });

  useEffect(() => { api.get("/empleados", { params: { limit: 200 } }).then((r) => setEmps(r.data)); api.get("/competencias").then((r) => setComps(r.data)); }, []);
  const load = () => api.get(`/evaluaciones/${tab}`).then((r) => setRows(r.data));
  useEffect(() => { load(); setMsg(""); }, [tab]);

  async function guardar(e) {
    e.preventDefault(); setMsg("");
    const body = tab === "competencias"
      ? { empleados_id_empleado: +f.empleado, competencias_id_competencias: +f.competencia, nivel: +f.nivel, observaciones: f.obs || null }
      : { empleados_id_empleado: +f.empleado, periodo: f.periodo, puntaje: +f.puntaje, observaciones: f.obs || null };
    try { await api.post(`/evaluaciones/${tab}`, body); setMsg("Evaluación registrada"); load(); }
    catch (err) { setMsg(err.response?.status === 409 ? "Ya existe una evaluación para ese período" : err.response?.data?.detail?.toString() || "Error"); }
  }

  return (
    <>
      <h2>Evaluaciones</h2>
      <div className="tabs">
        <button className={tab === "competencias" ? "on" : ""} onClick={() => setTab("competencias")}>Competencias (CU4)</button>
        <button className={tab === "desempeno" ? "on" : ""} onClick={() => setTab("desempeno")}>Desempeño (CU3)</button>
      </div>
      <form className="card form" onSubmit={guardar}>
        <div><label>Persona</label>
          <select value={f.empleado} onChange={set("empleado")} required><option value="">Seleccionar…</option>
            {emps.map((e) => <option key={e.id_empleado} value={e.id_empleado}>{e.apellido}, {e.nombre}</option>)}</select></div>
        {tab === "competencias" ? (<>
          <div><label>Competencia</label>
            <select value={f.competencia} onChange={set("competencia")} required><option value="">Seleccionar…</option>
              {comps.map((c) => <option key={c.id_competencias} value={c.id_competencias}>{c.descripcion}</option>)}</select></div>
          <div><label>Nivel (1–5)</label><input type="number" min="1" max="5" value={f.nivel} onChange={set("nivel")} /></div>
        </>) : (<>
          <div><label>Período</label><input value={f.periodo} onChange={set("periodo")} required /></div>
          <div><label>Puntaje (0–10)</label><input type="number" step="0.1" min="0" max="10" value={f.puntaje} onChange={set("puntaje")} /></div>
        </>)}
        <div><label>Observaciones</label><input value={f.obs} onChange={set("obs")} /></div>
        <button>Guardar</button>
        {msg && <span className={msg.includes("registrada") ? "ok" : "err"}>{msg}</span>}
      </form>
      <div className="card">
        <table>
          <thead><tr><th>Persona</th>{tab === "competencias" ? <><th>Competencia</th><th>Nivel</th><th>Fecha</th></> : <><th>Período</th><th>Puntaje</th></>}<th>Observaciones</th></tr></thead>
          <tbody>{rows.map((r) => (
            <tr key={r.id_eval_competencia || r.id_eval_desempeno}>
              <td>{r.apellido}, {r.nombre}</td>
              {tab === "competencias" ? <><td>{r.competencia}</td><td>{r.nivel}</td><td>{r.fecha}</td></> : <><td>{r.periodo}</td><td>{r.puntaje}</td></>}
              <td>{r.observaciones}</td></tr>
          ))}</tbody>
        </table>
      </div>
    </>
  );
}
