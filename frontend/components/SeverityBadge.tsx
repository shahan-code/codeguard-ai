const SEVERITY_STYLES: Record<string, string> = {
  LOW: "bg-risk-low/15 text-risk-low border-risk-low/30",
  MEDIUM: "bg-risk-medium/15 text-risk-medium border-risk-medium/30",
  HIGH: "bg-risk-high/15 text-risk-high border-risk-high/30",
  CRITICAL: "bg-risk-critical/15 text-risk-critical border-risk-critical/30",
};

export default function SeverityBadge({ severity }: { severity: string }) {
  const style = SEVERITY_STYLES[severity] || SEVERITY_STYLES.LOW;
  return (
    <span className={`inline-flex items-center rounded-sm border px-2 py-0.5 text-[11px] font-mono tracking-wide ${style}`}>
      {severity}
    </span>
  );
}
