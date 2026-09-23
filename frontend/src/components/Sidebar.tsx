"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutGrid, Upload, FolderOpen, GitCompareArrows, FileText, Settings, Activity } from "lucide-react";

const NAV = [
  { href: "/", label: "Dashboard", icon: LayoutGrid },
  { href: "/new", label: "New Analysis", icon: Upload },
  { href: "/", label: "Projects", icon: FolderOpen, disabled: true },
  { href: "/", label: "References", icon: GitCompareArrows, disabled: true },
  { href: "/", label: "Reports", icon: FileText, disabled: true },
  { href: "/", label: "Settings", icon: Settings, disabled: true },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="hidden md:flex w-56 shrink-0 border-r border-rf-border bg-rf-bg-1 flex-col">
      <div className="h-14 flex items-center gap-2 px-4 border-b border-rf-border">
        <Activity size={16} className="text-rf-blue" strokeWidth={2.25} />
        <span className="text-[13px] font-semibold tracking-tight text-rf-text">Rawform</span>
      </div>
      <nav className="flex-1 py-3">
        {NAV.map(({ href, label, icon: Icon, disabled }, i) => {
          const active = !disabled && pathname === href && (href !== "/" || pathname === "/");
          return (
            <Link
              key={label + i}
              href={disabled ? "#" : href}
              aria-disabled={disabled}
              className={[
                "flex items-center gap-2.5 px-4 py-2 text-[13px] transition-colors",
                disabled
                  ? "text-rf-text-faint cursor-not-allowed pointer-events-none"
                  : active
                  ? "text-rf-text bg-rf-bg-2 border-l-2 border-rf-blue -ml-[2px] pl-[calc(1rem-2px+2px)]"
                  : "text-rf-text-dim hover:text-rf-text hover:bg-rf-bg-2/60",
              ].join(" ")}
            >
              <Icon size={15} strokeWidth={1.8} />
              {label}
            </Link>
          );
        })}
      </nav>
      <div className="px-4 py-3 border-t border-rf-border text-[11px] text-rf-text-faint font-data">
        v0.1.0 · local
      </div>
    </aside>
  );
}
