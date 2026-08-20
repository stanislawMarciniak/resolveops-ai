import {
  Background,
  Controls,
  Handle,
  Position,
  ReactFlow,
  type Node,
  type Edge,
  type NodeProps,
  MarkerType,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { useMemo } from "react";
import type { CaseState } from "@/types";
import { buildPipeline, cn } from "@/utils/format";

const statusStyles = {
  completed: "border-emerald-500/40 bg-emerald-500/10 text-emerald-100",
  active: "border-amber-500/50 bg-amber-500/15 text-amber-100 ring-2 ring-amber-400/20",
  skipped: "border-slate-600/50 bg-slate-800/60 text-slate-400",
  failed: "border-rose-500/40 bg-rose-500/10 text-rose-100",
  pending: "border-white/10 bg-surface-850 text-slate-400",
  escalated: "border-amber-500/40 bg-amber-500/10 text-amber-100",
};

function AgentFlowNode({ data }: NodeProps) {
  const d = data as {
    label: string;
    detail: string;
    status: keyof typeof statusStyles;
  };

  return (
    <div
      className={cn(
        "min-w-[170px] rounded-xl border px-3 py-2.5 shadow-lg",
        statusStyles[d.status],
      )}
    >
      <Handle type="target" position={Position.Top} className="!bg-violet-400" />
      <div className="text-xs font-semibold tracking-wide">{d.label}</div>
      <div className="mt-1 text-[11px] opacity-80">{d.detail}</div>
      <Handle type="source" position={Position.Bottom} className="!bg-violet-400" />
    </div>
  );
}

const nodeTypes = { agent: AgentFlowNode };

export function CasePipeline({
  caseState,
  onSelect,
  height = 520,
}: {
  caseState: CaseState;
  onSelect?: (section: string) => void;
  height?: number;
}) {
  const pipeline = useMemo(() => buildPipeline(caseState), [caseState]);

  const { nodes, edges } = useMemo(() => {
    const flowNodes: Node[] = pipeline.map((item, index) => ({
      id: item.id,
      type: "agent",
      position: { x: 40, y: index * 78 },
      data: {
        label: item.label,
        detail: item.detail,
        status: item.status,
        section: item.section,
      },
    }));

    const flowEdges: Edge[] = pipeline.slice(0, -1).map((item, index) => ({
      id: `${item.id}-${pipeline[index + 1].id}`,
      source: item.id,
      target: pipeline[index + 1].id,
      animated: pipeline[index + 1].status === "active",
      style: { stroke: "#7c3aed", strokeWidth: 1.5 },
      markerEnd: { type: MarkerType.ArrowClosed, color: "#7c3aed" },
    }));

    return { nodes: flowNodes, edges: flowEdges };
  }, [pipeline]);

  return (
    <div className="panel overflow-hidden" style={{ height }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        fitView
        proOptions={{ hideAttribution: true }}
        nodesDraggable={false}
        nodesConnectable={false}
        elementsSelectable
        onNodeClick={(_, node) => {
          const section = (node.data as { section?: string }).section;
          if (section && onSelect) onSelect(section);
        }}
        minZoom={0.6}
        maxZoom={1.4}
      >
        <Background gap={18} size={1} color="#1e293b" />
        <Controls showInteractive={false} className="!bg-surface-850 !border-white/10 !shadow-none" />
      </ReactFlow>
    </div>
  );
}
