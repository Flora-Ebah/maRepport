"use client";

import { useState, useRef } from "react";
import Link from "next/link";
import {
  UploadCloud, FileSpreadsheet, FileText, CheckCircle2, AlertTriangle,
  Loader2, ArrowRight, RotateCcw, X,
} from "lucide-react";
import { Shell } from "@/components/shell";
import { API } from "@/lib/auth";

type Result = { fichier: string; type: string; libelle: string; detail: string; ok: boolean };

const ICON = (name: string) =>
  /\.pdf$/i.test(name) ? <FileText className="w-5 h-5 text-primary-600 shrink-0" />
    : <FileSpreadsheet className="w-5 h-5 text-primary-600 shrink-0" />;

export default function Page() {
  const [files, setFiles] = useState<File[]>([]);
  const [busy, setBusy] = useState(false);
  const [results, setResults] = useState<Result[] | null>(null);
  const [err, setErr] = useState("");
  const [drag, setDrag] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  function add(list: FileList | null) {
    setErr(""); setResults(null);
    if (!list) return;
    const ok = [...list].filter((f) => /\.(xlsx|xls|pdf)$/i.test(f.name));
    const bad = [...list].length - ok.length;
    if (bad) setErr("Seuls les fichiers .xlsx et .pdf sont acceptés (les autres ont été ignorés).");
    // dédoublonnage par nom, max 3 utiles mais on autorise plus
    setFiles((prev) => {
      const names = new Set(prev.map((f) => f.name));
      return [...prev, ...ok.filter((f) => !names.has(f.name))];
    });
  }

  function remove(name: string) {
    setFiles((prev) => prev.filter((f) => f.name !== name));
  }

  async function upload() {
    if (!files.length) return;
    setBusy(true); setErr(""); setResults(null);
    try {
      const fd = new FormData();
      files.forEach((f) => fd.append("files", f));
      const r = await fetch(`${API}/api/import`, { method: "POST", body: fd });
      if (!r.ok) { const e = await r.json().catch(() => ({})); throw new Error(e.detail || "Échec de l'import."); }
      const data = await r.json();
      setResults(data.resultats);
      window.dispatchEvent(new Event("ma2e:imported")); // active la navbar
    } catch (e: unknown) {
      setErr(e instanceof Error ? e.message : "Échec de l'import.");
    } finally { setBusy(false); }
  }

  return (
    <Shell
      title="Import de données"
      subtitle="Déposez vos fichiers — un seul bouton traite les trois automatiquement"
      right={
        <Link href="/" className="text-sm text-primary-600 hover:text-primary-700 flex items-center gap-1">
          Tableaux de bord <ArrowRight className="w-4 h-4" />
        </Link>
      }
    >
      <div className="max-w-3xl mx-auto">
        {!results ? (
          <div className="card-pad-lg">
            {/* Zone de dépôt unique */}
            <div
              onDragOver={(e) => { e.preventDefault(); setDrag(true); }}
              onDragLeave={() => setDrag(false)}
              onDrop={(e) => { e.preventDefault(); setDrag(false); add(e.dataTransfer.files); }}
              onClick={() => inputRef.current?.click()}
              className={`flex flex-col items-center justify-center text-center py-14 px-6 cursor-pointer transition-colors ${drag ? "bg-primary-100" : "bg-neutral-100 hover:bg-primary-50"}`}
            >
              <div className="w-14 h-14 bg-primary-600 flex items-center justify-center mb-4">
                <UploadCloud className="w-7 h-7 text-white" />
              </div>
              <div className="font-semibold text-neutral-800">Glissez vos fichiers ici (jusqu'à 3)</div>
              <div className="text-sm text-neutral-500 mt-1">POINT RETRAIT · POINT SIVE · BALANCE — .xlsx et .pdf</div>
              <div className="text-xs text-neutral-400 mt-2">Le système reconnaît automatiquement chaque fichier.</div>
              <input ref={inputRef} type="file" accept=".xlsx,.xls,.pdf" multiple className="hidden"
                onChange={(e) => add(e.target.files)} />
            </div>

            {/* Fichiers sélectionnés */}
            {files.length > 0 && (
              <div className="mt-4 space-y-px bg-neutral-200">
                {files.map((f) => (
                  <div key={f.name} className="bg-white px-4 py-2.5 flex items-center gap-3">
                    {ICON(f.name)}
                    <div className="flex-1 min-w-0">
                      <div className="text-sm font-medium truncate">{f.name}</div>
                      <div className="text-xs text-neutral-500">{(f.size / 1024 / 1024).toFixed(1)} Mo</div>
                    </div>
                    <button onClick={() => remove(f.name)} className="text-neutral-400 hover:text-danger p-1">
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                ))}
              </div>
            )}

            {err && (
              <div className="mt-4 bg-warning-light text-warning-dark text-sm px-4 py-3 flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 shrink-0" /> {err}
              </div>
            )}

            {/* Bouton unique */}
            <button onClick={upload} disabled={busy || !files.length}
              className="mt-5 w-full h-12 bg-primary-600 text-white font-medium flex items-center justify-center gap-2 hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors">
              {busy ? <Loader2 className="w-5 h-5 animate-spin" /> : <UploadCloud className="w-5 h-5" />}
              {busy ? "Traitement en cours…" : `Importer${files.length ? ` (${files.length})` : ""}`}
            </button>
          </div>
        ) : (
          /* Résultats */
          <div className="card-pad-lg">
            <div className="section-title"><CheckCircle2 className="w-3.5 h-3.5" /> Résultat de l'import</div>
            <div className="space-y-px bg-neutral-200">
              {results.map((r, i) => (
                <div key={i} className={`px-4 py-3 flex items-center gap-3 ${r.ok ? "bg-white" : "bg-danger-light"}`}>
                  {r.ok ? <CheckCircle2 className="w-5 h-5 text-success shrink-0" /> : <AlertTriangle className="w-5 h-5 text-danger-dark shrink-0" />}
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-medium">{r.libelle} <span className="text-neutral-400">· {r.fichier}</span></div>
                    <div className="text-xs text-neutral-500">{r.detail}</div>
                  </div>
                </div>
              ))}
            </div>
            <div className="mt-5 flex gap-px bg-neutral-200">
              <Link href="/" className="flex-1 bg-primary-600 text-white px-4 py-3 flex items-center justify-center gap-2 text-sm font-medium hover:bg-primary-700">
                Explorer les tableaux de bord <ArrowRight className="w-4 h-4" />
              </Link>
              <button onClick={() => { setResults(null); setFiles([]); }}
                className="bg-white px-4 py-3 flex items-center gap-2 text-sm text-neutral-600 hover:bg-neutral-50">
                <RotateCcw className="w-4 h-4" /> Importer d'autres fichiers
              </button>
            </div>
          </div>
        )}

        <div className="mt-px bg-info-light px-4 py-3 flex items-start gap-3">
          <UploadCloud className="w-4 h-4 text-info-dark shrink-0 mt-0.5" />
          <div className="text-xs text-neutral-700">
            <span className="font-semibold text-info-dark">Un seul bouton, détection automatique.</span> Déposez le point de trésorerie,
            le suivi SIVE et la balance ; le système identifie chaque fichier, le traite, détecte les anomalies et active les écrans correspondants.
          </div>
        </div>
      </div>
    </Shell>
  );
}
