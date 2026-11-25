// CU6: indicadores agregados del capital humano.
import { useEffect, useState } from "react";
import { Bar, BarChart, CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import api from "../api";

const C1 = "#2a5bd7", C2 = "#e07b00";

function Kpi({ l, v }) {
  return <div className="card kpi"><div className="v">{v ?? "—"}</div><div className="l">{l}</div></div>;
}

function Chart({ title, children }) {
  return (
    <div className="card">
      <b>{title}</b>
      <div style={{ height: 260, marginTop: 10 }}><ResponsiveContainer>{children}</ResponsiveContainer></div>
    </div>
  );
}

export default function Dashboard() {
  const [d, setD] = useState(null);
  const [err, setErr] = useState("");
  useEffect(() => { api.get("/dashboard/kpis").then((r) => setD(r.data)).catch(() => setErr("No se pudieron cargar los indicadores")); }, []);
  if (err) return <div className="err">{err}</div>;
  if (!d) return <div>Cargando…</div>;
  const t = d.totales;
  return (
    <>
      <h2>Evolución del capital humano</h2>
      <div className="grid">
        <Kpi l="Empleados" v={t.empleados} />
        <Kpi l="Evaluaciones realizadas" v={t.evaluaciones} />
        <Kpi l="Nivel promedio de competencias (1–5)" v={t.nivel_promedio} />
        <Kpi l="Necesidades de desarrollo" v={t.necesidades} />
        <Kpi l="Capacitaciones" v={t.capacitaciones} />
        <Kpi l="Contribuciones" v={t.contribuciones} />
      </div>
      <div className="charts">
        <Chart title="Nivel promedio de competencias por mes">
          <LineChart data={d.evolucion_competencias}>
            <CartesianGrid stroke="#e3e7ee" /><XAxis dataKey="mes" /><YAxis domain={[1, 5]} /><Tooltip />
            <Line type="monotone" dataKey="nivel" name="Nivel" stroke={C1} strokeWidth={2} />
          </LineChart>
        </Chart>
        <Chart title="Necesidades de desarrollo por prioridad">
          <BarChart data={d.necesidades_por_prioridad}>
            <CartesianGrid stroke="#e3e7ee" /><XAxis dataKey="prioridad" /><YAxis allowDecimals={false} /><Tooltip />
            <Bar dataKey="total" name="Necesidades" fill={C2} />
          </BarChart>
        </Chart>
        <Chart title="Empleados por unidad">
          <BarChart data={d.empleados_por_departamento} layout="vertical" margin={{ left: 120 }}>
            <CartesianGrid stroke="#e3e7ee" /><XAxis type="number" allowDecimals={false} /><YAxis type="category" dataKey="departamento" width={150} tick={{ fontSize: 11 }} /><Tooltip />
            <Bar dataKey="total" name="Empleados" fill={C1} />
          </BarChart>
        </Chart>
        <Chart title="Nivel promedio por competencia">
          <BarChart data={d.nivel_por_competencia} layout="vertical" margin={{ left: 120 }}>
            <CartesianGrid stroke="#e3e7ee" /><XAxis type="number" domain={[0, 5]} /><YAxis type="category" dataKey="competencia" width={150} tick={{ fontSize: 11 }} /><Tooltip />
            <Bar dataKey="nivel" name="Nivel" fill={C1} />
          </BarChart>
        </Chart>
      </div>
    </>
  );
}
