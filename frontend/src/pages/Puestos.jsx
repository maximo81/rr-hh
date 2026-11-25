// CU2: puestos de trabajo con sus requisitos (habilidades, conocimientos, especificación).
import { useEffect, useState } from "react";
import api from "../api";

export default function Puestos() {
  const [list, setList] = useState([]);
  const [det, setDet] = useState(null);
  useEffect(() => { api.get("/puestos").then((r) => setList(r.data)); }, []);
  const ver = (id) => api.get(`/puestos/${id}`).then((r) => setDet(r.data));
  return (
    <>
      <h2>Puestos de trabajo</h2>
      {det && (
        <div className="card">
          <button style={{ float: "right" }} onClick={() => setDet(null)}>Cerrar</button>
          <b>{det.codigo} · {det.titulo}</b>
          <p>{det.mision}</p>
          {det.especificaciones.map((e) => <p key={e.id_esp_puesto}><b>Categoría:</b> {e.categoria} · <b>Educación:</b> {e.especificacion_puestocol} · <b>Experiencia:</b> {e.experiencia_necesaria}</p>)}
          <p><b>Habilidades requeridas:</b> {det.habilidades.map((h) => h.descripcion).join(", ")}</p>
          <p><b>Conocimientos requeridos:</b> {det.conocimientos.map((k) => k.descripcion).join(", ")}</p>
        </div>
      )}
      <div className="card">
        <table>
          <thead><tr><th>Código</th><th>Título</th><th>Unidad</th><th>Posiciones</th><th></th></tr></thead>
          <tbody>{list.map((p) => (
            <tr key={p.id_puesto}><td>{p.codigo}</td><td>{p.titulo}</td><td>{p.departamento}</td><td>{p.posiciones}</td>
              <td><button onClick={() => ver(p.id_puesto)}>Ver</button></td></tr>
          ))}</tbody>
        </table>
      </div>
    </>
  );
}
