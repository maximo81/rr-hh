// CU8 (contribuciones) y CU9 (incentivos).
import { useEffect, useState } from "react";
import api from "../api";

export default function Contribuciones() {
  const [contribs, setContribs] = useState([]);
  const [incs, setIncs] = useState([]);
  const load = () => { api.get("/contribuciones").then((r) => setContribs(r.data)); api.get("/incentivos").then((r) => setIncs(r.data)); };
  useEffect(load, []);
  return (
    <>
      <h2>Iniciativas y contribuciones</h2>
      <div className="card"><table>
        <thead><tr><th>Título</th><th>Fecha</th><th>Participantes</th><th>Resultados</th></tr></thead>
        <tbody>{contribs.map((c) => <tr key={c.id_contribucion}><td>{c.titulo}</td><td>{c.fecha}</td><td>{c.participantes}</td><td>{c.resultados}</td></tr>)}</tbody>
      </table></div>
      <h2>Incentivos otorgados</h2>
      <div className="card"><table>
        <thead><tr><th>Persona</th><th>Tipo</th><th>Motivo</th><th>Contribución</th><th>Fecha</th></tr></thead>
        <tbody>{incs.map((i) => <tr key={i.id_incentivo}><td>{i.apellido}, {i.nombre}</td><td>{i.tipo}</td><td>{i.motivo}</td><td>{i.contribucion}</td><td>{i.fecha}</td></tr>)}</tbody>
      </table></div>
    </>
  );
}
