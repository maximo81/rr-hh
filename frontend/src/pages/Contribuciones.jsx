// CU8 (contribuciones) y CU9 (incentivos).
import { useEffect, useState } from "react";
import api from "../api";

const VACIO = { titulo: "", fecha: "", descripcion: "", resultados: "", participantes: [] };

export default function Contribuciones() {
  const [contribs, setContribs] = useState([]);
  const [incs, setIncs] = useState([]);
  const [emps, setEmps] = useState([]);
  const [f, setF] = useState(VACIO);
  const [editId, setEditId] = useState(null);
  const [msg, setMsg] = useState("");
  const canEdit = ["admin", "rrhh", "responsable_area"].includes(localStorage.getItem("rol"));
  const set = (k) => (e) => setF({ ...f, [k]: e.target.value });
  const load = () => { api.get("/contribuciones").then((r) => setContribs(r.data)); api.get("/incentivos").then((r) => setIncs(r.data)); };
  useEffect(() => { load(); api.get("/empleados", { params: { limit: 200 } }).then((r) => setEmps(r.data)); }, []);

  const toggle = (id) => setF({ ...f, participantes: f.participantes.includes(id) ? f.participantes.filter((x) => x !== id) : [...f.participantes, id] });
  const cancelar = () => { setF(VACIO); setEditId(null); setMsg(""); };

  function modificar(c) {
    setF({ titulo: c.titulo, fecha: c.fecha || "", descripcion: c.descripcion || "", resultados: c.resultados || "", participantes: c.participantes_ids || [] });
    setEditId(c.id_contribucion); setMsg("");
    window.scrollTo(0, 0);
  }

  async function guardar(e) {
    e.preventDefault(); setMsg("");
    const body = { titulo: f.titulo, fecha: f.fecha || null, descripcion: f.descripcion || null, resultados: f.resultados || null, participantes: f.participantes };
    try {
      if (editId) await api.put(`/contribuciones/${editId}`, body);
      else await api.post("/contribuciones", body);
      setF(VACIO); setEditId(null); setMsg("Guardado"); load();
    } catch (err) { setMsg(err.response?.data?.detail?.toString() || "Error"); }
  }

  return (
    <>
      <h2>Iniciativas y contribuciones</h2>
      {canEdit && (
        <form className="card form" onSubmit={guardar}>
          <div className="seccion" style={{ gridColumn: "1 / -1" }}>{editId ? "Modificar contribución" : "Nueva contribución"}</div>
          <div><label>Título</label><input value={f.titulo} onChange={set("titulo")} maxLength={120} required /></div>
          <div><label>Fecha</label><input type="date" value={f.fecha} onChange={set("fecha")} /></div>
          <div><label>Descripción</label><input value={f.descripcion} onChange={set("descripcion")} /></div>
          <div><label>Resultados</label><input value={f.resultados} onChange={set("resultados")} /></div>
          <div style={{ gridColumn: "1 / -1" }}><label>Participantes</label>
            <div className="checks">{emps.map((e) => <label key={e.id_empleado}>
              <input type="checkbox" checked={f.participantes.includes(e.id_empleado)} onChange={() => toggle(e.id_empleado)} />{e.apellido}, {e.nombre}</label>)}</div></div>
          <div className="acciones" style={{ gridColumn: "1 / -1", justifyContent: "flex-start", alignItems: "center" }}>
            <button>Guardar</button>
            {editId && <button type="button" className="sec" onClick={cancelar}>Cancelar</button>}
            {msg && <span className={msg === "Guardado" ? "ok" : "err"}>{msg}</span>}</div>
        </form>
      )}
      <div className="card"><table>
        <thead><tr><th>Título</th><th>Fecha</th><th>Participantes</th><th>Resultados</th>{canEdit && <th></th>}</tr></thead>
        <tbody>{contribs.map((c) => <tr key={c.id_contribucion}><td>{c.titulo}</td><td>{c.fecha}</td><td>{c.participantes}</td><td>{c.resultados}</td>
          {canEdit && <td><button className="sec" onClick={() => modificar(c)}>Modificar</button></td>}</tr>)}</tbody>
      </table></div>
      <h2>Incentivos otorgados</h2>
      <div className="card"><table>
        <thead><tr><th>Persona</th><th>Tipo</th><th>Motivo</th><th>Contribución</th><th>Fecha</th></tr></thead>
        <tbody>{incs.map((i) => <tr key={i.id_incentivo}><td>{i.apellido}, {i.nombre}</td><td>{i.tipo}</td><td>{i.motivo}</td><td>{i.contribucion}</td><td>{i.fecha}</td></tr>)}</tbody>
      </table></div>
    </>
  );
}
