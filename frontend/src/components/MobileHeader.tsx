"use client";

import Link from "next/link";
import { useState } from "react";
import { usePathname } from "next/navigation";
import { Activity, Menu, X, LayoutGrid, Upload } from "lucide-react";

export default function MobileHeader() {
  const [open, setOpen] = useState(false);
  const pathname = usePathname();

  return (
    <div className="md:hidden">
      <div className="h-14 flex items-center justify-between px-4 border-b border-rf-border bg-rf-bg-1">
        <Link href="/" className="flex items-center gap-2" onClick={() => setOpen(false)}>
          <Activity size={16} className="text-rf-blue" strokeWidth={2.25} />
          <span className="text-[13px] font-semibold tracking-tight text-rf-text">Rawform</span>
        </Link>
        <button
          onClick={() => setOpen((o) => !o)}
          aria-label="Menu"
          className="w-9 h-9 flex items-center justify-center text-rf-text-dim"
        >
          {open ? <X size={18} /> : <Menu size={18} />}
        </button>
      </div>
      {open && (
        <nav className="border-b border-rf-border bg-rf-bg-1">
          <Link
            href="/"
            onClick={() => setOpen(false)}
            className={`flex items-center gap-2.5 px-4 py-3 text-[13px] border-t border-rf-border-soft ${
              pathname === "/" ? "text-rf-text bg-rf-bg-2" : "text-rf-text-dim"
            }`}
          >
            <LayoutGrid size={15} strokeWidth={1.8} /> Dashboard
          </Link>
          <Link
            href="/new"
            onClick={() => setOpen(false)}
            className={`flex items-center gap-2.5 px-4 py-3 text-[13px] border-t border-rf-border-soft ${
              pathname === "/new" ? "text-rf-text bg-rf-bg-2" : "text-rf-text-dim"
            }`}
          >
            <Upload size={15} strokeWidth={1.8} /> New Analysis
          </Link>
        </nav>
      )}
    </div>
  );
}
