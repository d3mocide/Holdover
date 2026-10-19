import { db, metaGet, metaSet } from './db.js';

// The device journal (including a draft) belongs to syncOwner, even when signed out without clearing.
export async function loadTripDraft() {
  const draft = await metaGet('tripDraft');
  if (!draft) return null;
  const owner = await metaGet('syncOwner');
  // A pre-upgrade draft belonged to the same device journal; preserve it until that journal is cleared.
  if (!Object.hasOwn(draft, 'owner_id')) return draft;
  return draft.owner_id === owner ? draft.value : null;
}

export async function saveTripDraft(value) {
  await db.transaction('rw', db.meta, async () => {
    await metaSet('tripDraft', { owner_id: await metaGet('syncOwner'), value });
  });
}

export const clearTripDraft = () => db.meta.delete('tripDraft');

export function hasDraftContent(draft) {
  return !!draft && !!(draft.wbId || draft.gps || draft.notes?.trim() || draft.method?.trim() || draft.setupUuid ||
    draft.gearSel?.length || draft.species?.some((s) => s.name?.trim() || s.count > 0));
}
