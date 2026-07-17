// Formatage monétaire et dates — conventions UEMOA (FCFA, fr-FR).

export function fcfa(n: number): string {
  return Math.round(n).toLocaleString("fr-FR").replace(/ /g, " ") + " FCFA";
}

export function compact(n: number): string {
  const a = Math.abs(n);
  if (a >= 1e9) return (n / 1e9).toLocaleString("fr-FR", { maximumFractionDigits: 2 }) + " Md";
  if (a >= 1e6) return (n / 1e6).toLocaleString("fr-FR", { maximumFractionDigits: 1 }) + " M";
  if (a >= 1e3) return (n / 1e3).toLocaleString("fr-FR", { maximumFractionDigits: 0 }) + " k";
  return n.toLocaleString("fr-FR");
}

export function dateFr(iso: string): string {
  const [y, m, d] = iso.split("-");
  return `${d}/${m}/${y}`;
}

export function dateCourt(iso: string): string {
  const [, m, d] = iso.split("-");
  const mois = ["", "janv.", "févr.", "mars", "avr.", "mai", "juin", "juil.", "août", "sept.", "oct.", "nov.", "déc."];
  return `${d} ${mois[parseInt(m, 10)]}`;
}
