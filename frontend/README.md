# ResolveOps AI Frontend

Polished operator + architecture showcase UI for ResolveOps AI.

## Stack

- React + TypeScript + Vite
- Tailwind CSS
- React Router
- Recharts
- React Flow (`@xyflow/react`)
- Lucide React

## Run

From repo root, start the backend first:

```bash
source .venv/bin/activate
PYTHONPATH=backend uvicorn app.main:app --reload --app-dir backend
```

Then:

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

`VITE_API_URL` defaults to `http://localhost:8000`.

## Build

```bash
cd frontend
npm run build
npm run preview
```

## Pages

| Route | Purpose |
| --- | --- |
| `/` | Overview / KPI dashboard |
| `/cases` | Persisted CaseState table |
| `/cases/:caseId` | Case Explorer investigation workspace |
| `/showcase` | Dataset scenario cards |
| `/showcase/:evalId` | Multi vs single vs no-reviewer comparison |
| `/evaluations` | Charts, tag heatmap, reviewer ablation |
| `/architecture` | System + security diagrams |
| `/observability` | Cost / latency / token outliers |
| `/about` | Project narrative + limitations |
