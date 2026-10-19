export function findWaters(waters, { query = '', mode = 'rivers', zone, favorites = [] } = {}) {
  const words = query.trim().toLocaleLowerCase().split(/\s+/).filter(Boolean);
  const favs = new Set(favorites);
  return waters.filter((w) => {
    if (words.length) return words.every((word) => `${w.name} ${w.kind} ${w.zone ?? ''}`.toLocaleLowerCase().includes(word));
    if (mode === 'favorites') return favs.has(w.id);
    return w.kind === 'river' && (!zone || w.zone === zone);
  }).sort((a, b) => Number(favs.has(b.id)) - Number(favs.has(a.id)) || a.name.localeCompare(b.name));
}

export const evidenceText = (coverage) => `Evidence: ${Math.round(Math.max(0, Math.min(1, coverage ?? 0)) * 100)}%`;
