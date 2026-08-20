import {
  Background,
  Controls,
  MarkerType,
  ReactFlow,
  type Edge,
  type Node,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { Breadcrumbs } from "@/components/layout/Breadcrumbs";
import { ArchitectureDiagram } from "@/components/diagrams/ArchitectureDiagram";

export function ArchitecturePage() {
  return (
    <div className="fade-in space-y-6">
      <Breadcrumbs items={[{ label: "Architecture" }]} />

      <div>
        <h1 className="text-display text-2xl font-semibold text-slate-50">
          Architecture
        </h1>
        <p className="mt-1 max-w-3xl text-sm text-slate-400">
          LLMs never perform enterprise writes. Investigator is READ-only via MCP;
          Planner proposes; Reviewer critiques; humans approve; Executor and
          Verifier are deterministic application code.
        </p>
      </div>

      <ArchitectureDiagram />

      <section className="panel p-5">
        <h2 className="text-display text-lg font-semibold">Prompt injection defense</h2>
        <p className="mt-2 text-sm text-slate-400">
          Untrusted tool output is sanitized before it re-enters the Investigator
          context. LYRA is the stored prompt-injection security scenario.
        </p>

        <div className="mt-4 h-[280px] overflow-hidden rounded-xl border border-white/8">
          <InjectionFlow />
        </div>

        <div className="mt-4 grid gap-3 md:grid-cols-2">
          <div className="rounded-xl border border-rose-500/25 bg-rose-500/8 p-4">
            <div className="text-xs uppercase tracking-wider text-rose-300">
              Security test (LYRA)
            </div>
            <div className="mt-2 text-display text-2xl font-semibold text-rose-100">
              FAIL
            </div>
            <p className="mt-2 text-sm text-rose-100/80">
              Current eval pass rate for prompt-injection / stored-injection tags is
              0%. Do not interpret this as a green security benchmark.
            </p>
          </div>
          <div className="rounded-xl border border-white/10 bg-white/3 p-4 text-sm text-slate-300">
            Interpretation depends on the recorded CaseState: systems may escalate
            or fail to complete the desired malicious workflow. Inspect LYRA cases
            in Showcase for actual stages and reviewer verdicts rather than claiming
            a pass.
          </div>
        </div>
      </section>

      <section className="panel p-5">
        <h2 className="text-display text-lg font-semibold">Evaluation methodology</h2>
        <p className="mt-2 text-sm text-slate-400">
          20 synthetic enterprise support cases covering happy path, identifier
          normalization, partial payment, currency mismatch, split payments, stale
          holds, contract overrides, multi-invoice, missing mappings, false claims,
          and stored prompt injection.
        </p>
        <div className="mt-4 h-[320px] overflow-hidden rounded-xl border border-white/8">
          <MethodologyFlow />
        </div>
      </section>
    </div>
  );
}

function InjectionFlow() {
  const nodes: Node[] = [
    { id: "u", position: { x: 20, y: 90 }, data: { label: "Untrusted tool output" }, style: nodeStyle("#f59e0b") },
    { id: "c", position: { x: 240, y: 90 }, data: { label: "after_tool_callback" }, style: nodeStyle("#8b5cf6") },
    { id: "s", position: { x: 460, y: 90 }, data: { label: "Recursive sanitizer" }, style: nodeStyle("#8b5cf6") },
    { id: "r", position: { x: 680, y: 90 }, data: { label: "Redaction / notice" }, style: nodeStyle("#22c55e") },
    { id: "i", position: { x: 900, y: 90 }, data: { label: "Investigator" }, style: nodeStyle("#8b5cf6") },
    { id: "l", position: { x: 240, y: 200 }, data: { label: 'CRM: "Ignore previous…"' }, style: nodeStyle("#ef4444") },
  ];
  const edges: Edge[] = [
    edge("u", "c"),
    edge("c", "s"),
    edge("s", "r"),
    edge("r", "i"),
    edge("l", "c"),
  ];

  return (
    <ReactFlow nodes={nodes} edges={edges} fitView proOptions={{ hideAttribution: true }} nodesDraggable={false} nodesConnectable={false}>
      <Background gap={16} color="#1e293b" />
      <Controls showInteractive={false} className="!bg-surface-850 !border-white/10" />
    </ReactFlow>
  );
}

function MethodologyFlow() {
  const nodes: Node[] = [
    { id: "m1", position: { x: 40, y: 40 }, data: { label: "Multi-Agent" }, style: nodeStyle("#8b5cf6") },
    { id: "m2", position: { x: 40, y: 120 }, data: { label: "Investigator" }, style: nodeStyle("#8b5cf6") },
    { id: "m3", position: { x: 40, y: 200 }, data: { label: "Planner" }, style: nodeStyle("#8b5cf6") },
    { id: "m4", position: { x: 40, y: 280 }, data: { label: "Reviewer" }, style: nodeStyle("#8b5cf6") },
    { id: "s1", position: { x: 320, y: 40 }, data: { label: "Single-Agent" }, style: nodeStyle("#3b82f6") },
    { id: "s2", position: { x: 320, y: 160 }, data: { label: "Investigate + plan" }, style: nodeStyle("#3b82f6") },
    { id: "n1", position: { x: 600, y: 40 }, data: { label: "No Reviewer" }, style: nodeStyle("#f59e0b") },
    { id: "n2", position: { x: 600, y: 120 }, data: { label: "Investigator" }, style: nodeStyle("#f59e0b") },
    { id: "n3", position: { x: 600, y: 200 }, data: { label: "Planner" }, style: nodeStyle("#f59e0b") },
  ];
  const edges: Edge[] = [
    edge("m1", "m2"),
    edge("m2", "m3"),
    edge("m3", "m4"),
    edge("s1", "s2"),
    edge("n1", "n2"),
    edge("n2", "n3"),
  ];

  return (
    <ReactFlow nodes={nodes} edges={edges} fitView proOptions={{ hideAttribution: true }} nodesDraggable={false} nodesConnectable={false}>
      <Background gap={16} color="#1e293b" />
      <Controls showInteractive={false} className="!bg-surface-850 !border-white/10" />
    </ReactFlow>
  );
}

function nodeStyle(color: string) {
  return {
    border: `1px solid ${color}66`,
    background: `${color}22`,
    color: "#e2e8f0",
    borderRadius: 10,
    fontSize: 12,
    padding: 8,
    width: 170,
  };
}

function edge(source: string, target: string): Edge {
  return {
    id: `${source}-${target}`,
    source,
    target,
    style: { stroke: "#64748b" },
    markerEnd: { type: MarkerType.ArrowClosed, color: "#64748b" },
  };
}
