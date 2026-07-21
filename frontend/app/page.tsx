"use client";

import type { ReactNode } from "react";
import { useEffect, useRef, useState } from "react";

type ReviewFinding =
  | string
  | {
      ruleId?: string;
      severity?: string;
      path?: string;
      message?: string;
    };

type ManualReview = {
  status?: string;
  feedbackHistory?: string[];
  lastFeedback?: string | null;
  autoReviewStatus?: string;
  autoReviewFindings?: ReviewFinding[];
};

type AnalysisReview = {
  status?: string;
  feedbackHistory?: string[];
  lastFeedback?: string | null;
};

type ArtifactInfo = {
  jsonPath?: string;
  markdownPath?: string;
};

type ReviewInfo = {
  status?: string;
  findings?: ReviewFinding[];
  strengths?: unknown;
  nextActions?: unknown;
};

type GenerationProgress = {
  status?: string;
  currentStep?: string;
  summary?: string;
  updatedAt?: string;
};

type ExecutionTraceStep = {
  key?: string;
  label?: string;
  status?: string;
  summary?: string;
  preview?: unknown;
  raw?: unknown;
  completedAt?: string;
};

type ExecutionTrace = {
  steps?: ExecutionTraceStep[];
};

type DetailDesignSection = Record<string, unknown>;

type GenerationPayload = {
  basicDesignAnalytics?: Record<string, unknown>;
  analysis?: Record<string, unknown>;
  analysisReview?: AnalysisReview;
  detailDesign?: Record<string, DetailDesignSection>;
  review?: ReviewInfo;
  manualReview?: ManualReview;
  artifacts?: ArtifactInfo | null;
  pipeline?: { stages?: Array<Record<string, unknown>> };
  resourcesUsed?: Record<string, unknown>;
  generationProgress?: GenerationProgress;
  executionTrace?: ExecutionTrace;
  [key: string]: unknown;
};

type GenerationResult = GenerationPayload | string;

type CommonInputStatus = {
  status?: string;
  version?: string;
  sourceRoot?: string;
  sourceFileCount?: number;
  sourceFiles?: string[];
  promptRuntime?: {
    source?: string;
    sourceRoot?: string;
    manifestPath?: string;
    version?: string;
    fileCount?: number;
    stageNames?: string[];
    sourceFiles?: string[];
  };
};

type KnowledgeBaseProgressStep = {
  key?: string;
  label?: string;
  status?: string;
  message?: string;
  output?: Record<string, unknown> | null;
  timestamp?: string;
};

type KnowledgeBaseProgress = {
  operation?: string;
  status?: string;
  summary?: string;
  currentStep?: string | null;
  startedAt?: string | null;
  updatedAt?: string | null;
  completedAt?: string | null;
  resultPreview?: Record<string, unknown> | null;
  error?: Record<string, unknown> | null;
  steps?: KnowledgeBaseProgressStep[];
};

type KnowledgeBaseStatus = {
  status?: string;
  chunkCount?: number;
  sampleCount?: number;
  reviewedDetailDesigns?: {
    source?: string;
    seedSamples?: number;
    sampleIds?: string[];
  };
  vectorDb?: {
    provider?: string;
    available?: boolean;
    pointCount?: number;
    collection?: string;
    url?: string;
  };
  sparseIndex?: {
    provider?: string;
    chunkCount?: number;
    indexLoaded?: boolean;
    indexedChunks?: number;
  };
  progress?: KnowledgeBaseProgress;
};

type TimelineStep = {
  key: string;
  label: string;
  description: string;
  state: "done" | "current" | "upcoming";
};

function isGenerationPayload(value: GenerationResult | null): value is GenerationPayload {
  return typeof value === "object" && value !== null;
}

function tryParseJsonString(value: string): unknown {
  const trimmed = value.trim();
  if (!trimmed || (!trimmed.startsWith("{") && !trimmed.startsWith("["))) {
    return value;
  }
  try {
    return JSON.parse(trimmed);
  } catch {
    return value;
  }
}

function normalizeValue(value: unknown): unknown {
  if (typeof value === "string") return tryParseJsonString(value);
  return value;
}

function humanizeKey(value: string): string {
  return value
    .replace(/^\d+_/, "")
    .replace(/[_-]/g, " ")
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

function naturalText(value: unknown): string {
  const normalized = normalizeValue(value);
  if (normalized === null || normalized === undefined) return "";
  if (typeof normalized === "string") return normalized;
  if (typeof normalized === "number" || typeof normalized === "boolean") {
    return String(normalized);
  }
  if (Array.isArray(normalized)) {
    return normalized.map((item) => naturalText(item)).filter(Boolean).join(", ");
  }
  if (typeof normalized === "object") {
    const record = normalized as Record<string, unknown>;
    const preferred = ["title", "name", "summary", "message", "description", "path", "step", "id"];
    const direct = preferred.map((key) => record[key]).find((item) => naturalText(item));
    if (direct !== undefined) return naturalText(direct);
    return Object.entries(record)
      .map(([key, item]) => `${humanizeKey(key)}: ${naturalText(item)}`)
      .filter((item) => !item.endsWith(": "))
      .join("; ");
  }
  return String(normalized);
}

function stringifyValue(value: unknown): string {
  if (value === null || value === undefined) return "";
  if (typeof value === "string") return naturalText(value);
  if (typeof value === "number" || typeof value === "boolean") return String(value);
  if (Array.isArray(value)) {
    return value.map((item) => stringifyValue(item)).filter(Boolean).join(", ");
  }
  return naturalText(value);
}

function toList(value: unknown): string[] {
  if (value === null || value === undefined || value === "") return [];
  if (Array.isArray(value)) return value.map((item) => stringifyValue(item)).filter(Boolean);
  return [stringifyValue(value)];
}

function formatFinding(finding: ReviewFinding): string {
  if (typeof finding === "string") return finding;
  const prefix = [finding.ruleId, finding.severity].filter(Boolean).join(" / ");
  const message = finding.message ?? finding.path ?? JSON.stringify(finding);
  return prefix ? `${prefix}: ${message}` : message;
}

function titleCase(value: string): string {
  return value
    .replace(/[_-]/g, " ")
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

function appendList(markdown: string[], title: string, value: unknown) {
  const items = toList(value);
  if (!items.length) return;
  markdown.push(`### ${title}`);
  items.forEach((item) => markdown.push(`- ${item}`));
  markdown.push("");
}

function appendNaturalContent(markdown: string[], value: unknown) {
  const normalized = normalizeValue(value);
  if (normalized === null || normalized === undefined || normalized === "") {
    markdown.push("No content.");
    return;
  }
  if (Array.isArray(normalized)) {
    normalized.forEach((item) => markdown.push(`- ${naturalText(item)}`));
    return;
  }
  if (typeof normalized === "object") {
    const entries = Object.entries(normalized as Record<string, unknown>);
    entries.forEach(([key, item]) => {
      const itemValue = normalizeValue(item);
      if (Array.isArray(itemValue)) {
        markdown.push(`- ${humanizeKey(key)}: ${itemValue.map((entry) => naturalText(entry)).join(", ")}`);
      } else if (itemValue && typeof itemValue === "object") {
        markdown.push(`- ${humanizeKey(key)}: ${naturalText(itemValue)}`);
      } else {
        markdown.push(`- ${humanizeKey(key)}: ${naturalText(itemValue)}`);
      }
    });
    return;
  }
  markdown.push(naturalText(normalized));
}

function buildMarkdownPreview(payload: GenerationPayload): string {
  const markdown: string[] = ["# Detail Design Review", ""];
  const analysis = payload.analysis ?? {};
  const analytics = payload.basicDesignAnalytics ?? {};
  const inputReferences = payload.resourcesUsed?.inputReferences as
    | { referenceCount?: number; references?: Array<Record<string, unknown>> }
    | undefined;

  markdown.push("## Basic Design Analytics");
  markdown.push(stringifyValue(analytics.summary) || "No summary.");
  markdown.push("");
  appendList(markdown, "Modules", analytics.modules);
  appendList(markdown, "Screens", analytics.screens);
  appendList(markdown, "Entities", analytics.entities);
  appendList(markdown, "Business Flows", analytics.businessFlows);
  appendList(markdown, "API Candidates", analytics.apiCandidates);
  appendList(markdown, "UI Signals", analytics.uiSignals);

  if (inputReferences?.referenceCount) {
    markdown.push("## Similar Input References");
    markdown.push(`Found ${inputReferences.referenceCount} reference input example(s) from INPUT/input.`);
    markdown.push("");
    (inputReferences.references ?? []).forEach((reference) => {
      markdown.push(
        `- ${stringifyValue(reference.componentId)} ${stringifyValue(reference.name)}: ${toList(reference.sourceFiles).join(", ")}`,
      );
    });
    markdown.push("");
  }

  markdown.push("## Design Analysis");
  markdown.push(stringifyValue(analysis.summary) || "No analysis summary.");
  markdown.push("");
  if (analysis.scope) {
    markdown.push(`**Scope:** ${stringifyValue(analysis.scope)}`);
    markdown.push("");
  }
  appendList(markdown, "Risks", analysis.risks);
  appendList(markdown, "Assumptions", analysis.assumptions);
  markdown.push(`**Analysis Review:** ${payload.analysisReview?.status ?? "N/A"}`);
  markdown.push("");

  markdown.push("## Detail Design");
  if (payload.detailDesign) {
    Object.entries(payload.detailDesign).forEach(([moduleName, sections]) => {
      markdown.push(`### ${titleCase(moduleName)}`);
      if (typeof sections === "string") {
        markdown.push(sections);
        markdown.push("");
      } else {
        Object.entries(sections).forEach(([sectionName, content]) => {
          markdown.push(`#### ${humanizeKey(sectionName)}`);
          appendNaturalContent(markdown, content);
          markdown.push("");
        });
      }
    });
  } else {
    markdown.push("No detail design generated.");
    markdown.push("");
  }

  markdown.push("## Review");
  markdown.push(`**Auto Review:** ${payload.review?.status ?? "N/A"}`);
  markdown.push(`**Designer Review:** ${payload.manualReview?.status ?? "N/A"}`);
  markdown.push("");
  const findings = payload.review?.findings ?? [];
  if (findings.length) {
    markdown.push("### Checklist Findings");
    findings.forEach((finding) => markdown.push(`- ${formatFinding(finding)}`));
    markdown.push("");
  }
  appendList(markdown, "Strengths", payload.review?.strengths);
  appendList(markdown, "Next Actions", payload.review?.nextActions);

  const stages = payload.pipeline?.stages ?? [];
  if (stages.length) {
    markdown.push("## Pipeline");
    stages.forEach((stage) => {
      markdown.push(`- ${stringifyValue(stage.name)}: ${stringifyValue(stage.summary)}`);
    });
    markdown.push("");
  }

  return markdown.join("\n").trim();
}

function buildStatusTimeline(status: string): TimelineStep[] {
  const steps = [
    {
      key: "analysis",
      label: "1. Analysis",
      description: "Analyze BD/UI, retrieve KB, generate Design Analysis",
    },
    {
      key: "analysis_review",
      label: "2. Analysis Review",
      description: "User approve or request update before DD generation",
    },
    {
      key: "detail_design",
      label: "3. Detail Design",
      description: "Generate DD and run auto-review loop",
    },
    {
      key: "designer_review",
      label: "4. Designer Review",
      description: "User approve DD or request another update",
    },
    {
      key: "completed",
      label: "5. Export + KB",
      description: "Export final output and ingest approved DD into KB",
    },
  ];

  const rankByStatus: Record<string, number> = {
    pending: 0,
    analyzing: 0,
    retrieving_samples: 0,
    generating_analysis: 0,
    needs_analysis_review: 1,
    manual_updating: 2,
    generating_dd: 2,
    validating: 2,
    needs_manual_review: 3,
    completed: 4,
    failed: 0,
  };

  const currentRank = rankByStatus[status] ?? 0;

  return steps.map((step, index) => ({
    ...step,
    state:
      index < currentRank
        ? "done"
        : index === currentRank
          ? "current"
          : "upcoming",
  }));
}

function prettyJson(value: unknown): string {
  if (value === null || value === undefined) return "";
  try {
    return JSON.stringify(value, null, 2);
  } catch {
    return String(value);
  }
}

function MarkdownPreview({ markdown }: { markdown: string }) {
  const lines = markdown.split("\n");
  const elements: ReactNode[] = [];
  let codeLines: string[] = [];
  let inCodeBlock = false;

  lines.forEach((line, index) => {
    if (line.trim() === "```") {
      if (inCodeBlock) {
        elements.push(
          <pre key={`code-${index}`} className="my-3 overflow-x-auto rounded-md bg-slate-900 p-4 text-sm text-emerald-200">
            {codeLines.join("\n")}
          </pre>,
        );
        codeLines = [];
        inCodeBlock = false;
      } else {
        inCodeBlock = true;
      }
      return;
    }

    if (inCodeBlock) {
      codeLines.push(line);
      return;
    }

    if (!line.trim()) {
      elements.push(<div key={`space-${index}`} className="h-2" />);
    } else if (line.startsWith("# ")) {
      elements.push(<h1 key={index} className="text-2xl font-bold text-slate-950">{line.slice(2)}</h1>);
    } else if (line.startsWith("## ")) {
      elements.push(<h2 key={index} className="mt-5 border-b border-slate-200 pb-2 text-xl font-semibold text-slate-900">{line.slice(3)}</h2>);
    } else if (line.startsWith("### ")) {
      elements.push(<h3 key={index} className="mt-4 text-base font-semibold text-slate-800">{line.slice(4)}</h3>);
    } else if (line.startsWith("#### ")) {
      elements.push(<h4 key={index} className="mt-3 text-sm font-semibold text-slate-700">{line.slice(5)}</h4>);
    } else if (line.startsWith("- ")) {
      elements.push(<div key={index} className="ml-4 text-sm leading-6 text-slate-700">• {line.slice(2)}</div>);
    } else if (line.startsWith("**")) {
      elements.push(<p key={index} className="text-sm font-medium leading-6 text-slate-800">{line.replaceAll("**", "")}</p>);
    } else {
      elements.push(<p key={index} className="text-sm leading-6 text-slate-700">{line}</p>);
    }
  });

  if (codeLines.length) {
    elements.push(
      <pre key="code-tail" className="my-3 overflow-x-auto rounded-md bg-slate-900 p-4 text-sm text-emerald-200">
        {codeLines.join("\n")}
      </pre>,
    );
  }

  return <div className="rounded-md border border-slate-200 bg-white p-5">{elements}</div>;
}

function TracePreview({ value }: { value: unknown }) {
  const normalized = normalizeValue(value);

  if (normalized === null || normalized === undefined || normalized === "") {
    return <div className="text-sm text-slate-500">No preview.</div>;
  }

  if (typeof normalized === "string" || typeof normalized === "number" || typeof normalized === "boolean") {
    return <div className="whitespace-pre-wrap text-sm leading-6 text-slate-700">{String(normalized)}</div>;
  }

  if (Array.isArray(normalized)) {
    return (
      <div className="space-y-2">
        {normalized.map((item, index) => (
          <div key={index} className="rounded-md border border-slate-200 bg-white p-3 text-sm text-slate-700">
            {typeof item === "object" && item !== null ? (
              <pre className="overflow-x-auto whitespace-pre-wrap text-xs text-slate-700">
                {prettyJson(item)}
              </pre>
            ) : (
              naturalText(item)
            )}
          </div>
        ))}
      </div>
    );
  }

  if (typeof normalized === "object") {
    return (
      <div className="space-y-2">
        {Object.entries(normalized as Record<string, unknown>).map(([key, item]) => (
          <div key={key} className="rounded-md border border-slate-200 bg-white p-3">
            <div className="text-xs font-semibold uppercase tracking-wide text-slate-500">
              {humanizeKey(key)}
            </div>
            <div className="mt-1 whitespace-pre-wrap text-sm leading-6 text-slate-700">
              {Array.isArray(item) || (item && typeof item === "object") ? (
                <pre className="overflow-x-auto whitespace-pre-wrap text-xs text-slate-700">
                  {prettyJson(item)}
                </pre>
              ) : (
                naturalText(item)
              )}
            </div>
          </div>
        ))}
      </div>
    );
  }

  return <div className="text-sm text-slate-700">{String(normalized)}</div>;
}

export default function Home() {
  const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";

  const [designFile, setDesignFile] = useState<File | null>(null);
  const [imageFiles, setImageFiles] = useState<File[]>([]);
  const [composableFile, setComposableFile] = useState<File | null>(null);
  const [projectId, setProjectId] = useState("");
  const [jobId, setJobId] = useState("");
  const [jobStatus, setJobStatus] = useState("");
  const [analysisFeedback, setAnalysisFeedback] = useState("");
  const [designerFeedback, setDesignerFeedback] = useState("");
  const [output, setOutput] = useState<GenerationResult | null>(null);
  const [outputTab, setOutputTab] = useState<"markdown" | "json">("markdown");
  const [isLoading, setIsLoading] = useState(false);
  const [status, setStatus] = useState("");
  const [commonInputStatus, setCommonInputStatus] = useState<CommonInputStatus | null>(null);
  const [knowledgeBaseStatus, setKnowledgeBaseStatus] = useState<KnowledgeBaseStatus | null>(null);
  const [isKbActionLoading, setIsKbActionLoading] = useState(false);
  const [kbStatusMessage, setKbStatusMessage] = useState("");
  const generationPollRef = useRef<number | null>(null);
  const knowledgeBasePollRef = useRef<number | null>(null);

  useEffect(() => {
    let cancelled = false;

    const loadCommonInputStatus = async () => {
      try {
        const response = await fetch(`${baseUrl}/admin/common-input/status`);
        const data = await response.json();
        if (!cancelled) {
          setCommonInputStatus(data.data ?? null);
        }
      } catch {
        if (!cancelled) {
          setCommonInputStatus(null);
        }
      }
    };

    const loadKnowledgeBaseStatus = async () => {
      try {
        const response = await fetch(`${baseUrl}/admin/knowledge-base/status`);
        const data = await response.json();
        if (!cancelled) {
          setKnowledgeBaseStatus(data.data ?? null);
        }
      } catch {
        if (!cancelled) {
          setKnowledgeBaseStatus(null);
        }
      }
    };

    void loadCommonInputStatus();
    void loadKnowledgeBaseStatus();
    return () => {
      cancelled = true;
    };
  }, [baseUrl]);

  const responseData = async (response: Response) => {
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.detail ?? `Request failed (${response.status})`);
    }
    return payload;
  };

  const applyGenerationResponse = (nextStatus: string, nextResult: GenerationResult) => {
    setJobStatus(nextStatus);
    setOutput(nextResult);
    setOutputTab("markdown");
    if (nextStatus === "needs_analysis_review") {
      setStatus("Đã sinh Design Analysis. Chờ approve hoặc update trước khi sinh DD.");
    } else if (nextStatus === "needs_manual_review") {
      setStatus("Đã sinh xong bản nháp. Chờ Designer Review/Update.");
    } else if (nextStatus === "completed") {
      setStatus("Đã approve và export artifact.");
    } else if (nextStatus === "failed") {
      setStatus("Generate thất bại.");
    } else {
      setStatus(`Trạng thái: ${nextStatus}`);
    }
  };

  const loadKnowledgeBaseStatus = async () => {
    const response = await fetch(`${baseUrl}/admin/knowledge-base/status`);
    const data = await response.json();
    const nextStatus = (data.data ?? null) as KnowledgeBaseStatus | null;
    setKnowledgeBaseStatus(nextStatus);

    const progressStatus = nextStatus?.progress?.status;
    if (progressStatus !== "queued" && progressStatus !== "running" && knowledgeBasePollRef.current !== null) {
      window.clearInterval(knowledgeBasePollRef.current);
      knowledgeBasePollRef.current = null;
    }

    return nextStatus;
  };

  const stopGenerationPolling = () => {
    if (generationPollRef.current !== null) {
      window.clearInterval(generationPollRef.current);
      generationPollRef.current = null;
    }
  };

  const stopKnowledgeBasePolling = () => {
    if (knowledgeBasePollRef.current !== null) {
      window.clearInterval(knowledgeBasePollRef.current);
      knowledgeBasePollRef.current = null;
    }
  };

  const startKnowledgeBasePolling = () => {
    stopKnowledgeBasePolling();
    knowledgeBasePollRef.current = window.setInterval(() => {
      void loadKnowledgeBaseStatus();
    }, 5000);
  };

  useEffect(() => {
    return () => {
      stopGenerationPolling();
      stopKnowledgeBasePolling();
    };
  }, []);

  const kbProgressStatus = knowledgeBaseStatus?.progress?.status;
  const kbBusy = kbProgressStatus === "queued" || kbProgressStatus === "running";

  const pollGeneration = (nextProjectId: string, nextJobId: string) => {
    setStatus("Đang sinh Detail Design...");
    stopGenerationPolling();

    generationPollRef.current = window.setInterval(async () => {
      const statRes = await fetch(`${baseUrl}/projects/${nextProjectId}/generations/${nextJobId}`);
      const statData = await statRes.json();
      const nextStatus = statData.data.status as string;
      setJobStatus(nextStatus);

      if (["completed", "needs_analysis_review", "needs_manual_review", "failed"].includes(nextStatus)) {
        stopGenerationPolling();
        setIsLoading(false);
        applyGenerationResponse(nextStatus, statData.data.result);
      } else {
        setOutput(statData.data.result);
        setStatus(`Trạng thái: ${nextStatus}...`);
      }
    }, 3000);
  };

  const handleGenerate = async () => {
    if (!designFile) return alert("Vui lòng chọn file thiết kế Markdown (.md)");
    
    setIsLoading(true);
    setOutput(null);
    setStatus("Khởi tạo project...");

    try {
      // 1. Create Project
      const projRes = await fetch(`${baseUrl}/projects`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: "Demo Project" }),
      });
      const projData = await responseData(projRes);
      const nextProjectId = projData.data.projectId as string;
      setProjectId(nextProjectId);

      // 2. Upload the complete design input bundle
      setStatus("Đang tải Markdown, ảnh UI và Composable CSV...");
      const designInputForm = new FormData();
      designInputForm.append("design", designFile);
      imageFiles.forEach((file) => designInputForm.append("images", file));
      if (composableFile) designInputForm.append("composable", composableFile);
      const inputUploadResponse = await fetch(`${baseUrl}/projects/${nextProjectId}/documents/design-input`, {
        method: "POST",
        body: designInputForm,
      });
      await responseData(inputUploadResponse);

      // 3. Generate
      setStatus("Đang bắt đầu xử lý AI...");
      const genRes = await fetch(`${baseUrl}/projects/${nextProjectId}/generate`, { method: "POST" });
      const genData = await responseData(genRes);
      const nextJobId = genData.data.jobId as string;
      setJobId(nextJobId);

      // 4. Poll Status
      pollGeneration(nextProjectId, nextJobId);
    } catch (err: unknown) {
      setIsLoading(false);
      setStatus("Lỗi: " + (err instanceof Error ? err.message : "Unknown error"));
    }
  };

  const handleKnowledgeBaseReindex = async () => {
    setIsKbActionLoading(true);
    setKbStatusMessage("Đang gửi yêu cầu reindex knowledge base...");
    try {
      const response = await fetch(`${baseUrl}/admin/knowledge-base/reindex`, {
        method: "POST",
      });
      const data = await response.json();
      setKnowledgeBaseStatus((prev) => ({
        ...(prev ?? {}),
        progress: data.data ?? null,
      }));
      setKbStatusMessage("Đã bắt đầu reindex. UI sẽ tự cập nhật từng bước.");
      startKnowledgeBasePolling();
      await loadKnowledgeBaseStatus();
    } catch (err: unknown) {
      setKbStatusMessage("Lỗi: " + (err instanceof Error ? err.message : "Unknown error"));
    } finally {
      setIsKbActionLoading(false);
    }
  };

  const submitDesignerReview = async (action: "request_update" | "approve") => {
    if (!projectId || !jobId) return;
    if (action === "request_update" && !designerFeedback.trim()) {
      alert("Vui lòng nhập feedback trước khi yêu cầu update");
      return;
    }

    setIsLoading(true);
    setStatus(
      action === "approve"
        ? "Đang approve và export artifact..."
        : "Đang cập nhật Detail Design theo feedback...",
    );

    try {
      const response = await fetch(
        `${baseUrl}/projects/${projectId}/generations/${jobId}/designer-review`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            action,
            feedback: action === "request_update" ? designerFeedback : undefined,
          }),
        },
      );
      const data = await response.json();
      setIsLoading(false);
      if (!response.ok) {
        setStatus(data.detail ?? "Không thể xử lý designer review");
        return;
      }

      applyGenerationResponse(data.data.status, data.data.result);
      if (action === "approve") {
        setDesignerFeedback("");
      }
    } catch (err: unknown) {
      setIsLoading(false);
      setStatus("Lỗi: " + (err instanceof Error ? err.message : "Unknown error"));
    }
  };

  const submitAnalysisReview = async (action: "request_update" | "approve") => {
    if (!projectId || !jobId) return;
    if (action === "request_update" && !analysisFeedback.trim()) {
      alert("Vui lòng nhập feedback trước khi yêu cầu update analysis");
      return;
    }

    setIsLoading(true);
    setStatus(
      action === "approve"
        ? "Đang approve analysis và tiếp tục sinh Detail Design..."
        : "Đang cập nhật Design Analysis theo feedback...",
    );

    try {
      const response = await fetch(
        `${baseUrl}/projects/${projectId}/generations/${jobId}/analysis-review`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            action,
            feedback: action === "request_update" ? analysisFeedback : undefined,
          }),
        },
      );
      const data = await response.json();
      if (!response.ok) {
        setIsLoading(false);
        setStatus(data.detail ?? "Không thể xử lý analysis review");
        return;
      }

      applyGenerationResponse(data.data.status, data.data.result);
      if (action === "approve" || action === "request_update") {
        setAnalysisFeedback("");
      }
      if (action === "approve" && data.data.status === "generating_dd") {
        setStatus("Đã approve analysis. Backend đang sinh Detail Design...");
        pollGeneration(projectId, jobId);
      } else {
        setIsLoading(false);
      }
    } catch (err: unknown) {
      setIsLoading(false);
      setStatus("Lỗi: " + (err instanceof Error ? err.message : "Unknown error"));
    }
  };

  const payloadOutput = isGenerationPayload(output) ? output : null;
  const reviewFindings = payloadOutput?.review?.findings ?? [];
  const markdownPreview = payloadOutput ? buildMarkdownPreview(payloadOutput) : "";
  const feedbackHistory = payloadOutput?.manualReview?.feedbackHistory ?? [];
  const analysisFeedbackHistory = payloadOutput?.analysisReview?.feedbackHistory ?? [];
  const generationProgress = payloadOutput?.generationProgress;
  const executionTraceSteps = payloadOutput?.executionTrace?.steps ?? [];
  const statusTimeline = buildStatusTimeline(jobStatus || "pending");
  const canAnalysisReview =
    payloadOutput?.analysisReview?.status === "pending" &&
    !payloadOutput?.detailDesign &&
    !!projectId &&
    !!jobId;
  const canDesignerReview =
    payloadOutput?.manualReview?.status === "pending" &&
    !!payloadOutput?.detailDesign &&
    !!projectId &&
    !!jobId;
  const kbProgress = knowledgeBaseStatus?.progress;
  const kbSteps = kbProgress?.steps ?? [];

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-4xl mx-auto space-y-6">
        <h1 className="text-3xl font-bold text-gray-800">BD to DD Generator</h1>
        
        {/* INPUT */}
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          {commonInputStatus && (
            <div className="mb-5 rounded-lg border border-sky-200 bg-sky-50 p-4 text-sm text-sky-900">
              <div className="font-semibold">Common Input Source</div>
              <div className="mt-1">Source root: {commonInputStatus.sourceRoot ?? "N/A"}</div>
              <div>Version: {commonInputStatus.version ?? "N/A"}</div>
              <div>Loaded files: {commonInputStatus.sourceFileCount ?? 0}</div>
              <div className="mt-2 text-xs text-sky-700">
                Runtime hiện đọc templates, checklists, guidelines, skills và common components từ `INPUT/common`.
              </div>
              <div className="mt-1 text-xs text-sky-700">
                Bạn có thể đổi nội dung trong thư mục này, và lần generate tiếp theo sẽ dùng nguồn mới.
              </div>
              <div className="mt-1 text-xs text-sky-700">
                Prompt runtime source: {commonInputStatus.promptRuntime?.source === "input_common_prompts" ? "`INPUT/common/prompts`" : "backend fallback defaults"}.
              </div>
              <div className="mt-1 text-xs text-sky-700">
                Prompt manifest: {commonInputStatus.promptRuntime?.manifestPath ?? "N/A"}
              </div>
              <div className="mt-1 text-xs text-sky-700">
                Prompt version: {commonInputStatus.promptRuntime?.version ?? "N/A"} | Prompt files: {commonInputStatus.promptRuntime?.fileCount ?? 0}
              </div>
            </div>
          )}

          <div className="mb-6">
            <h2 className="text-xl font-semibold text-slate-900">1. Upload Basic Design </h2>
            <p className="mt-1 text-sm text-slate-600">
              Đưa các mẫu Basic design tại đây
            </p>
          </div>

          <div className="grid gap-4 md:grid-cols-3">
            <label className="rounded-xl border-2 border-dashed border-blue-200 bg-blue-50/60 p-4">
              <span className="block text-sm font-semibold text-blue-950">A. Design Markdown *</span>
              <span className="mt-1 block min-h-10 text-xs text-blue-800">Đề bài Basic/UI Design mô tả chức năng và màn hình.</span>
              <input
                type="file"
                accept=".md,text/markdown"
                onChange={(event) => setDesignFile(event.target.files?.[0] ?? null)}
                className="mt-4 block w-full text-xs text-slate-600 file:mr-2 file:rounded-md file:border-0 file:bg-blue-600 file:px-3 file:py-2 file:font-semibold file:text-white"
              />
              <span className="mt-3 block break-all text-xs font-medium text-blue-900">
                {designFile?.name ?? "Chưa chọn file .md"}
              </span>
            </label>

            <label className="rounded-xl border-2 border-dashed border-violet-200 bg-violet-50/60 p-4">
              <span className="block text-sm font-semibold text-violet-950">B. UI Images</span>
              <span className="mt-1 block min-h-10 text-xs text-violet-800">Một hoặc nhiều ảnh sẽ được Gemini Flash đọc và mô tả.</span>
              <input
                type="file"
                accept=".png,.jpg,.jpeg,.webp,image/png,image/jpeg,image/webp"
                multiple
                onChange={(event) => setImageFiles(Array.from(event.target.files ?? []))}
                className="mt-4 block w-full text-xs text-slate-600 file:mr-2 file:rounded-md file:border-0 file:bg-violet-600 file:px-3 file:py-2 file:font-semibold file:text-white"
              />
              <span className="mt-3 block text-xs font-medium text-violet-900">
                {imageFiles.length ? `${imageFiles.length} ảnh: ${imageFiles.map((file) => file.name).join(", ")}` : "Chưa chọn ảnh"}
              </span>
            </label>

            <label className="rounded-xl border-2 border-dashed border-emerald-200 bg-emerald-50/60 p-4">
              <span className="block text-sm font-semibold text-emerald-950">C. Composable CSV</span>
              <span className="mt-1 block min-h-10 text-xs text-emerald-800">Danh sách component/composable liên quan đến màn hình.</span>
              <input
                type="file"
                accept=".csv,text/csv"
                onChange={(event) => setComposableFile(event.target.files?.[0] ?? null)}
                className="mt-4 block w-full text-xs text-slate-600 file:mr-2 file:rounded-md file:border-0 file:bg-emerald-600 file:px-3 file:py-2 file:font-semibold file:text-white"
              />
              <span className="mt-3 block break-all text-xs font-medium text-emerald-900">
                {composableFile?.name ?? "Chưa chọn file .csv"}
              </span>
            </label>
          </div>

          <div className="mt-6 rounded-xl border border-slate-200 bg-slate-50 p-4">
            <div className="text-sm font-semibold text-slate-900">2. Hệ thống xử lý và sinh Detail Design</div>
            <div className="mt-3 grid gap-2 text-xs text-slate-700 sm:grid-cols-2 lg:grid-cols-4">
              {["Đọc Markdown + CSV", "Gemini Flash phân tích ảnh", "Phân tích BD và tìm DD mẫu trong KB", "Review Analysis → Sinh và review DD"].map((step, index) => (
                <div key={step} className="rounded-lg border border-slate-200 bg-white p-3">
                  <span className="mr-2 font-bold text-blue-700">{index + 1}</span>{step}
                </div>
              ))}
            </div>
          </div>

          <button
            onClick={handleGenerate}
            disabled={isLoading || !designFile}
            className="mt-4 w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-3 px-4 rounded-md disabled:bg-blue-300 transition-colors"
          >
            {isLoading ? "Đang xử lý bộ input..." : "Bắt đầu phân tích và sinh Detail Design"}
          </button>
          
          {status && (
            <div className="mt-3 space-y-1">
              <p className="text-sm text-gray-600 font-medium italic">{status}</p>
              {jobStatus && (
                <p className="text-xs text-gray-500">Job status: {jobStatus}</p>
              )}
            </div>
          )}
        </div>

        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
            <div>
              <h2 className="text-xl font-semibold text-gray-800">Knowledge Base Pipeline</h2>
              <p className="mt-1 text-sm text-slate-600">
                Theo dõi từng bước backend của KB như load sample, chunking, embedding, gắn metadata, upsert Qdrant và BM25.
              </p>
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => {
                  void loadKnowledgeBaseStatus();
                }}
                className="rounded-md border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
              >
                Refresh KB
              </button>
              <button
                onClick={handleKnowledgeBaseReindex}
                disabled={isKbActionLoading || kbBusy}
                className="rounded-md bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-700 disabled:bg-emerald-300"
              >
                {isKbActionLoading || kbBusy ? "KB đang chạy..." : "Reindex KB"}
              </button>
            </div>
          </div>

          {knowledgeBaseStatus && (
            <div className="mt-4 grid gap-3 md:grid-cols-4">
              <div className="rounded-md border border-slate-200 bg-slate-50 p-3 text-sm text-slate-800">
                <div className="font-semibold">Seed Samples</div>
                <div>{knowledgeBaseStatus.reviewedDetailDesigns?.seedSamples ?? 0}</div>
              </div>
              <div className="rounded-md border border-sky-200 bg-sky-50 p-3 text-sm text-sky-900">
                <div className="font-semibold">Qdrant Points</div>
                <div>{knowledgeBaseStatus.vectorDb?.pointCount ?? 0}</div>
              </div>
              <div className="rounded-md border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-900">
                <div className="font-semibold">BM25 Chunks</div>
                <div>{knowledgeBaseStatus.sparseIndex?.chunkCount ?? knowledgeBaseStatus.sparseIndex?.indexedChunks ?? 0}</div>
              </div>
              <div className="rounded-md border border-amber-200 bg-amber-50 p-3 text-sm text-amber-900">
                <div className="font-semibold">Progress</div>
                <div>{kbProgress?.status ?? "idle"}</div>
              </div>
            </div>
          )}

          {(kbStatusMessage || kbProgress) && (
            <div className="mt-4 rounded-lg border border-slate-200 bg-slate-50 p-4">
              {kbStatusMessage && (
                <div className="text-sm font-medium text-slate-700">{kbStatusMessage}</div>
              )}
              {kbProgress && (
                <div className="mt-2 space-y-1 text-sm text-slate-700">
                  <div><span className="font-semibold">Operation:</span> {kbProgress.operation ?? "N/A"}</div>
                  <div><span className="font-semibold">Current step:</span> {kbProgress.currentStep ?? "idle"}</div>
                  <div><span className="font-semibold">Summary:</span> {kbProgress.summary ?? "N/A"}</div>
                </div>
              )}
            </div>
          )}

          {kbSteps.length > 0 && (
            <div className="mt-4 space-y-3">
              {kbSteps.map((step, index) => (
                <div
                  key={`${step.key ?? "step"}-${index}`}
                  className={`rounded-lg border p-4 ${
                    step.status === "completed"
                      ? "border-emerald-200 bg-emerald-50"
                      : step.status === "failed"
                        ? "border-rose-200 bg-rose-50"
                        : "border-blue-200 bg-blue-50"
                  }`}
                >
                  <div className="flex flex-col gap-1 md:flex-row md:items-center md:justify-between">
                    <div className="text-sm font-semibold text-slate-900">
                      {step.label ?? step.key ?? `Step ${index + 1}`}
                    </div>
                    <div className="text-xs uppercase tracking-wide text-slate-600">
                      {step.status ?? "unknown"}
                    </div>
                  </div>
                  <div className="mt-1 text-sm text-slate-700">{step.message ?? "No message"}</div>
                  {step.output && (
                    <pre className="mt-3 overflow-x-auto rounded-md bg-slate-900 p-4 text-xs text-emerald-200">
                      {prettyJson(step.output)}
                    </pre>
                  )}
                </div>
              ))}
            </div>
          )}

          {kbProgress?.resultPreview && (
            <div className="mt-4 rounded-lg border border-slate-200 bg-white p-4">
              <div className="text-sm font-semibold text-slate-900">Latest KB result preview</div>
              <pre className="mt-3 overflow-x-auto rounded-md bg-slate-900 p-4 text-xs text-emerald-200">
                {prettyJson(kbProgress.resultPreview)}
              </pre>
            </div>
          )}
        </div>

        {/* OUTPUT */}
        {output && (
          <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
            <h2 className="text-xl font-semibold text-gray-800 mb-4">Kết quả (Detail Design)</h2>
            {payloadOutput && (
              <div className="mb-4 space-y-4">
                <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
                  <div className="mb-3 text-sm font-semibold text-slate-900">Workflow Timeline</div>
                  <div className="grid gap-3 md:grid-cols-5">
                    {statusTimeline.map((step) => (
                      <div
                        key={step.key}
                        className={`rounded-lg border p-3 text-sm ${
                          step.state === "done"
                            ? "border-emerald-200 bg-emerald-50 text-emerald-900"
                            : step.state === "current"
                              ? "border-blue-200 bg-blue-50 text-blue-900"
                              : "border-slate-200 bg-white text-slate-500"
                        }`}
                      >
                        <div className="font-semibold">{step.label}</div>
                        <div className="mt-1 text-xs leading-5">{step.description}</div>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="grid gap-3 md:grid-cols-3">
                  <div className="rounded-md border border-sky-200 bg-sky-50 p-3 text-sm text-sky-900">
                    <div className="font-semibold">Analysis Review</div>
                    <div>{payloadOutput.analysisReview?.status ?? "N/A"}</div>
                  </div>
                  <div className="rounded-md border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-900">
                    <div className="font-semibold">Auto Review</div>
                    <div>{payloadOutput.review?.status ?? "N/A"}</div>
                  </div>
                  <div className="rounded-md border border-amber-200 bg-amber-50 p-3 text-sm text-amber-900">
                    <div className="font-semibold">Designer Review</div>
                    <div>{payloadOutput.manualReview?.status ?? "N/A"}</div>
                  </div>
                </div>

                {generationProgress && (
                  <div className="rounded-md border border-blue-200 bg-blue-50 p-4 text-sm text-blue-900">
                    <div className="font-semibold">Generation Progress</div>
                    <div className="mt-1">Step: {generationProgress.currentStep ?? "N/A"}</div>
                    <div>Status: {generationProgress.status ?? "N/A"}</div>
                    <div>Summary: {generationProgress.summary ?? "N/A"}</div>
                  </div>
                )}

                {executionTraceSteps.length > 0 && (
                  <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
                    <div className="text-sm font-semibold text-slate-900">Pipeline Trace</div>
                    <div className="mt-1 text-sm text-slate-600">
                      Hiển thị output từng bước backend để review: phần tóm tắt dễ đọc và raw JSON để debug.
                    </div>
                    <div className="mt-4 space-y-3">
                      {executionTraceSteps.map((step, index) => (
                        <details
                          key={`${step.key ?? "trace"}-${index}`}
                          className="rounded-lg border border-slate-200 bg-white"
                        >
                          <summary className="cursor-pointer list-none p-4">
                            <div className="flex flex-col gap-2 md:flex-row md:items-start md:justify-between">
                              <div>
                                <div className="text-sm font-semibold text-slate-900">
                                  {step.label ?? step.key ?? `Step ${index + 1}`}
                                </div>
                                <div className="mt-1 text-sm text-slate-700">
                                  {step.summary ?? "No summary"}
                                </div>
                              </div>
                              <div className="text-xs uppercase tracking-wide text-slate-500">
                                {step.status ?? "unknown"}
                              </div>
                            </div>
                          </summary>
                          <div className="border-t border-slate-200 px-4 py-4">
                            <div className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                              Preview
                            </div>
                            <div className="mt-2">
                              <TracePreview value={step.preview} />
                            </div>
                            <details className="mt-4 rounded-md border border-slate-200 bg-slate-50">
                              <summary className="cursor-pointer px-4 py-3 text-sm font-medium text-slate-800">
                                Xem raw output
                              </summary>
                              <div className="border-t border-slate-200 p-4">
                                <pre className="overflow-x-auto rounded-md bg-slate-900 p-4 text-xs text-emerald-200">
                                  {prettyJson(step.raw)}
                                </pre>
                              </div>
                            </details>
                          </div>
                        </details>
                      ))}
                    </div>
                  </div>
                )}

                {analysisFeedbackHistory.length > 0 && (
                  <div className="rounded-md border border-sky-200 bg-sky-50 p-4">
                    <div className="text-sm font-semibold text-sky-900">Analysis feedback history</div>
                    <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-sky-800">
                      {analysisFeedbackHistory.map((item, index) => (
                        <li key={`${item}-${index}`}>{item}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {reviewFindings.length > 0 && (
                  <div className="rounded-md border border-gray-200 bg-gray-50 p-4">
                    <div className="text-sm font-semibold text-gray-800">Checklist findings</div>
                    <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-gray-700">
                      {reviewFindings.map((finding, index) => (
                        <li key={`${formatFinding(finding)}-${index}`}>{formatFinding(finding)}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {feedbackHistory.length > 0 && (
                  <div className="rounded-md border border-gray-200 bg-white p-4">
                    <div className="text-sm font-semibold text-gray-800">Feedback history</div>
                    <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-gray-700">
                      {feedbackHistory.map((item, index) => (
                        <li key={`${item}-${index}`}>{item}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {canAnalysisReview && (
                  <div className="rounded-md border border-sky-200 bg-sky-50 p-4">
                    <label className="block text-sm font-medium text-sky-900 mb-2">
                      Analysis Review / Update
                    </label>
                    <textarea
                      className="w-full h-28 p-4 border border-sky-300 bg-white text-black rounded-md focus:ring-blue-500 focus:border-blue-500 outline-none"
                      placeholder="Nhập feedback để hệ thống revise lại Design Analysis trước khi sinh DD..."
                      value={analysisFeedback}
                      onChange={(e) => setAnalysisFeedback(e.target.value)}
                    />
                    <div className="mt-3 flex flex-col gap-3 sm:flex-row">
                      <button
                        onClick={() => submitAnalysisReview("request_update")}
                        disabled={isLoading}
                        className="flex-1 rounded-md bg-sky-500 px-4 py-3 text-sm font-medium text-white transition-colors hover:bg-sky-600 disabled:bg-sky-300"
                      >
                        Request Analysis Update
                      </button>
                      <button
                        onClick={() => submitAnalysisReview("approve")}
                        disabled={isLoading}
                        className="flex-1 rounded-md bg-emerald-600 px-4 py-3 text-sm font-medium text-white transition-colors hover:bg-emerald-700 disabled:bg-emerald-300"
                      >
                        Approve Analysis & Generate DD
                      </button>
                    </div>
                  </div>
                )}

                {canDesignerReview && (
                  <div className="rounded-md border border-gray-200 bg-gray-50 p-4">
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Designer Review / Update
                    </label>
                    <textarea
                      className="w-full h-28 p-4 border border-gray-300 bg-white text-black rounded-md focus:ring-blue-500 focus:border-blue-500 outline-none"
                      placeholder="Nhập feedback để hệ thống revise lại Detail Design..."
                      value={designerFeedback}
                      onChange={(e) => setDesignerFeedback(e.target.value)}
                    />
                    <div className="mt-3 flex flex-col gap-3 sm:flex-row">
                      <button
                        onClick={() => submitDesignerReview("request_update")}
                        disabled={isLoading}
                        className="flex-1 rounded-md bg-amber-500 px-4 py-3 text-sm font-medium text-white transition-colors hover:bg-amber-600 disabled:bg-amber-300"
                      >
                        Request Update
                      </button>
                      <button
                        onClick={() => submitDesignerReview("approve")}
                        disabled={isLoading}
                        className="flex-1 rounded-md bg-emerald-600 px-4 py-3 text-sm font-medium text-white transition-colors hover:bg-emerald-700 disabled:bg-emerald-300"
                      >
                        Approve & Export
                      </button>
                    </div>
                  </div>
                )}

                {payloadOutput.artifacts && projectId && jobId && (
                  <div className="flex flex-col gap-3 sm:flex-row">
                    <a
                      href={`${baseUrl}/projects/${projectId}/generations/${jobId}/artifacts/jsonPath`}
                      target="_blank"
                      rel="noreferrer"
                      className="flex-1 rounded-md bg-slate-800 px-4 py-3 text-center text-sm font-medium text-white transition-colors hover:bg-slate-900"
                    >
                      Download JSON
                    </a>
                    <a
                      href={`${baseUrl}/projects/${projectId}/generations/${jobId}/artifacts/markdownPath`}
                      target="_blank"
                      rel="noreferrer"
                      className="flex-1 rounded-md bg-slate-600 px-4 py-3 text-center text-sm font-medium text-white transition-colors hover:bg-slate-700"
                    >
                      Download Markdown
                    </a>
                  </div>
                )}
              </div>
            )}
            <div className="mt-5">
              <div className="mb-3 inline-flex rounded-md border border-gray-200 bg-gray-100 p-1">
                <button
                  type="button"
                  onClick={() => setOutputTab("markdown")}
                  className={`rounded px-4 py-2 text-sm font-medium transition-colors ${
                    outputTab === "markdown"
                      ? "bg-white text-slate-950 shadow-sm"
                      : "text-slate-600 hover:text-slate-950"
                  }`}
                >
                  Markdown Preview
                </button>
                <button
                  type="button"
                  onClick={() => setOutputTab("json")}
                  className={`rounded px-4 py-2 text-sm font-medium transition-colors ${
                    outputTab === "json"
                      ? "bg-white text-slate-950 shadow-sm"
                      : "text-slate-600 hover:text-slate-950"
                  }`}
                >
                  Raw JSON
                </button>
              </div>

              {outputTab === "markdown" && payloadOutput ? (
                <MarkdownPreview markdown={markdownPreview} />
              ) : (
                <pre className="bg-gray-800 text-green-400 p-4 rounded-md overflow-x-auto text-sm shadow-inner">
                  {typeof output === "string" 
                    ? output 
                    : JSON.stringify(output, null, 2)}
                </pre>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
