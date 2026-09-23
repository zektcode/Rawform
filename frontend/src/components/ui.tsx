import { scoreColor } from "@/lib/format";

export function Panel({
  title,
  subtitle,
  children,
  className = "",
}: {
  title?: string;
  subtitle?: string;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={`border border-rf-border bg-rf-bg-1 ${className}`}>
      {title && (
        <div className="px-4 py-2.5 border-b border-rf-border flex items-baseline justify-between">
          <h3 className="text-[12px] font-medium text-rf-text tracking-tight">{title}</h3>
          {subtitle && <span className="text-[11px] text-rf-text-faint font-data">{subtitle}</span>}
        </div>
      )}
      <div className="p-4">{children}</div>
    </div>
  );
}

export function Stat({
  label,
  value,
  unit,
  tone = "default",
}: {
  label: string;
  value: string;
  unit?: string;
  tone?: "default" | "green" | "red" | "amber" | "blue";
}) {
  const toneClass = {
    default: "text-rf-text",
    green: "text-rf-green",
    red: "text-rf-red",
    amber: "text-rf-amber",
    blue: "text-rf-blue",
  }[tone];
  return (
    <div>
      <div className="text-[11px] text-rf-text-dim mb-1">{label}</div>
      <div className={`font-data text-[20px] leading-none ${toneClass}`}>
        {value}
        {unit && <span className="text-[12px] text-rf-text-dim ml-1">{unit}</span>}
      </div>
    </div>
  );
}

export function StatusPill({ status }: { status: string }) {
  const map: Record<string, string> = {
    pending: "text-rf-text-dim border-rf-border",
    processing: "text-rf-blue border-rf-blue-dim animate-pulse",
    complete: "text-rf-green border-rf-green-dim",
    failed: "text-rf-red border-rf-red-dim",
  };
  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2 py-0.5 border rounded-sm text-[11px] font-data uppercase tracking-wide ${
        map[status] || map.pending
      }`}
    >
      <span className="w-1.5 h-1.5 rounded-full bg-current" />
      {status}
    </span>
  );
}

export function SeverityPill({ severity }: { severity: "low" | "medium" | "high" }) {
  const map = {
    high: "text-rf-red border-rf-red-dim bg-rf-red-dim/10",
    medium: "text-rf-amber border-rf-amber/40 bg-rf-amber/10",
    low: "text-rf-blue border-rf-blue-dim bg-rf-blue-dim/10",
  };
  return (
    <span className={`px-1.5 py-0.5 border rounded-sm text-[10px] font-data uppercase tracking-wider ${map[severity]}`}>
      {severity}
    </span>
  );
}

export function ScoreBadge({ score, size = "md" }: { score: number | null; size?: "sm" | "md" | "lg" }) {
  const sizeClass = { sm: "text-[16px]", md: "text-[28px]", lg: "text-[56px]" }[size];
  return (
    <span className={`font-data ${sizeClass} ${scoreColor(score)} leading-none`}>
      {score === null ? "—" : score}
    </span>
  );
}

export function Button({
  children,
  onClick,
  variant = "primary",
  disabled,
  type = "button",
  className = "",
}: {
  children: React.ReactNode;
  onClick?: () => void;
  variant?: "primary" | "secondary" | "ghost";
  disabled?: boolean;
  type?: "button" | "submit";
  className?: string;
}) {
  const base = "px-3.5 py-2 text-[13px] font-medium rounded-sm transition-colors disabled:opacity-40 disabled:cursor-not-allowed";
  const variants = {
    primary: "bg-rf-blue text-rf-bg-0 hover:bg-rf-blue/90",
    secondary: "bg-rf-bg-2 text-rf-text border border-rf-border hover:bg-rf-bg-3",
    ghost: "text-rf-text-dim hover:text-rf-text hover:bg-rf-bg-2",
  };
  return (
    <button type={type} onClick={onClick} disabled={disabled} className={`${base} ${variants[variant]} ${className}`}>
      {children}
    </button>
  );
}

export function EmptyState({ title, subtitle }: { title: string; subtitle?: string }) {
  return (
    <div className="border border-dashed border-rf-border rounded-sm py-16 flex flex-col items-center justify-center text-center px-6">
      <div className="text-[13px] text-rf-text-dim">{title}</div>
      {subtitle && <div className="text-[12px] text-rf-text-faint mt-1 max-w-sm">{subtitle}</div>}
    </div>
  );
}
