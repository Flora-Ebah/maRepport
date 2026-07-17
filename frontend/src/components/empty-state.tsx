import Link from "next/link";
import { Inbox, UploadCloud } from "lucide-react";

/** État vide : affiché tant que la donnée n'est pas importée. */
export function EmptyState({ titre, detail }: { titre: string; detail: string }) {
  return (
    <div className="bg-white py-20 px-6 flex flex-col items-center text-center">
      <div className="w-16 h-16 bg-neutral-100 flex items-center justify-center mb-5">
        <Inbox className="w-8 h-8 text-neutral-400" />
      </div>
      <h2 className="text-lg font-bold text-neutral-800">{titre}</h2>
      <p className="text-sm text-neutral-500 mt-2 max-w-md">{detail}</p>
      <Link href="/import"
        className="mt-6 h-10 px-5 bg-primary-600 text-white text-sm font-medium flex items-center gap-2 hover:bg-primary-700 transition-colors">
        <UploadCloud className="w-4 h-4" /> Importer les données
      </Link>
    </div>
  );
}
