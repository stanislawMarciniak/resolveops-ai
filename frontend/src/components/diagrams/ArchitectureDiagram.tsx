import {
  Background,
  Controls,
  Handle,
  MarkerType,
  Position,
  ReactFlow,
  type Edge,
  type Node,
  type NodeProps,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { useMemo, useState } from "react";
import { cn } from "@/utils/format";

type Kind = "llm" | "deterministic" | "external" | "human" | "boundary";

const KIND_STYLE: Record<Kind, string> = {
  llm: "border-violet-500/40 bg-violet-500/15 text-violet-100",
  deterministic: "border-sky-500/40 bg-sky-500/12 text-sky-100",
  external: "border-amber-500/40 bg-amber-500/12 text-amber-100",
  human: "border-emerald-500/40 bg-emerald-500/12 text-emerald-100",
  boundary: "border-fuchsia-500/40 bg-fuchsia-500/12 text-fuchsia-100",
};

const EXPLANATIONS: Record<string, string> = {
  operator: "Human operator investigates outcomes and gates high-risk mutations.",
  fastapi: "FastAPI orchestration surface for cases, approvals, and evaluations.",
  "case-manager": "Persists resumable CaseState and drives stage transitions.",
  investigator: "ReAct-style agent with READ-only MCP access.",
  mcp_read: "MCP tool boundary for CRM, Billing, and Policy RAG reads.",
  crm: "CRM simulator — customers, accounts, suspension status.",
  billing: "Legacy billing simulator — invoices, payments, holds.",
  policy: "Policy RAG over enterprise runbooks and contracts.",
  planner: "Produces a mutation plan but cannot call tools.",
  reviewer: "Independent self-reflection / safety critic.",
  approval: "Human-in-the-loop gate before any enterprise write.",
  executor: "Deterministic Python code. LLM never executes writes.",
  mcp_write: "WRITE MCP tools for payment matching and hold removal.",
  raw: "Read-after-write verification against live enterprise state.",
  verifier: "Checks actual enterprise state after mutations.",
  terminal: "Terminal CaseStage: RESOLVED, ESCALATED, or FAILED.",
};

function ArchNode({ data }: NodeProps) {
  const d = data as { label: string; kind: Kind; subtitle?: string };
  return (
    <div className={cn("min-w-[160px] rounded-xl border px-3 py-2 shadow-lg", KIND_STYLE[d.kind])}>
      <Handle type="target" position={Position.Top} className="!bg-slate-400" />
      <div className="text-xs font-semibold">{d.label}</div>
      {d.subtitle ? <div className="mt-0.5 text-[10px] opacity-75">{d.subtitle}</div> : null}
      <Handle type="source" position={Position.Bottom} className="!bg-slate-400" />
    </div>
  );
}

const nodeTypes = { arch: ArchNode };

export function ArchitectureDiagram() {
  const [selected, setSelected] = useState<string>("investigator");

  const { nodes, edges } = useMemo(() => {
    const defs: Array<[string, string, number, number, Kind, string?]> = [
      ["operator", "User / Operator", 420, 0, "human"],
      ["fastapi", "FastAPI", 420, 80, "deterministic"],
      ["case-manager", "Case Manager", 420, 160, "deterministic"],
      ["investigator", "Investigator", 420, 240, "llm", "READ-only ReAct"],
      ["mcp_read", "READ MCP tools", 420, 320, "boundary"],
      ["crm", "CRM", 180, 400, "external"],
      ["billing", "Billing", 420, 400, "external"],
      ["policy", "Policy RAG", 660, 400, "external"],
      ["planner", "Planner", 420, 500, "llm", "No tools"],
      ["reviewer", "Reviewer", 420, 580, "llm", "Safety critic"],
      ["approval", "Human Approval", 420, 660, "human"],
      ["executor", "Deterministic Executor", 420, 740, "deterministic"],
      ["mcp_write", "WRITE MCP tools", 420, 820, "boundary"],
      ["raw", "Read-after-write checks", 420, 900, "deterministic"],
      ["verifier", "Final Verifier", 420, 980, "deterministic"],
      ["terminal", "RESOLVED / FAILED", 420, 1060, "human"],
    ];

    const flowNodes: Node[] = defs.map(([id, label, x, y, kind, subtitle]) => ({
      id,
      type: "arch",
      position: { x, y },
      data: { label, kind, subtitle },
    }));

    const pairs: Array<[string, string]> = [
      ["operator", "fastapi"],
      ["fastapi", "case-manager"],
      ["case-manager", "investigator"],
      ["investigator", "mcp_read"],
      ["mcp_read", "crm"],
      ["mcp_read", "billing"],
      ["mcp_read", "policy"],
      ["crm", "planner"],
      ["billing", "planner"],
      ["policy", "planner"],
      ["planner", "reviewer"],
      ["reviewer", "approval"],
      ["approval", "executor"],
      ["executor", "mcp_write"],
      ["mcp_write", "raw"],
      ["raw", "verifier"],
      ["verifier", "terminal"],
    ];

    const flowEdges: Edge[] = pairs.map(([source, target]) => ({
      id: `${source}-${target}`,
      source,
      target,
      style: { stroke: "#64748b", strokeWidth: 1.4 },
      markerEnd: { type: MarkerType.ArrowClosed, color: "#64748b" },
    }));

    return { nodes: flowNodes, edges: flowEdges };
  }, []);

  return (
    <div className="grid gap-4 lg:grid-cols-[1fr_280px]">
      <div className="panel h-[720px] overflow-hidden">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          nodeTypes={nodeTypes}
          fitView
          proOptions={{ hideAttribution: true }}
          nodesDraggable={false}
          nodesConnectable={false}
          onNodeClick={(_, node) => setSelected(node.id)}
          minZoom={0.35}
          maxZoom={1.2}
        >
          <Background gap={20} size={1} color="#1e293b" />
          <Controls className="!bg-surface-850 !border-white/10" showInteractive={false} />
        </ReactFlow>
      </div>

      <div className="space-y-4">
        <div className="panel p-4">
          <div className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">
            Legend
          </div>
          <ul className="mt-3 space-y-2 text-sm">
            <li className="flex items-center gap-2"><span className="h-3 w-3 rounded bg-violet-500/60" /> Purple = LLM</li>
            <li className="flex items-center gap-2"><span className="h-3 w-3 rounded bg-sky-500/60" /> Blue = deterministic</li>
            <li className="flex items-center gap-2"><span className="h-3 w-3 rounded bg-amber-500/60" /> Amber = external</li>
            <li className="flex items-center gap-2"><span className="h-3 w-3 rounded bg-emerald-500/60" /> Green = human / security</li>
            <li className="flex items-center gap-2"><span className="h-3 w-3 rounded bg-fuchsia-500/60" /> Fuchsia = MCP boundary</li>
          </ul>
        </div>

        <div className="panel p-4">
          <div className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">
            Selected node
          </div>
          <div className="mt-2 text-display text-lg font-semibold text-slate-50">
            {selected}
          </div>
          <p className="mt-2 text-sm leading-relaxed text-slate-300">
            {EXPLANATIONS[selected] ?? "Select a node to learn more."}
          </p>
        </div>
      </div>
    </div>
  );
}
