// Which of the pack list's template items you already own. Matching is by gear type, fishery tag and name hints, and
// it only ever says "you have" (never "you are missing"): a template suggestion is generic, and absence of a match
// is not a fact about your tackle bag.

const has = (re) => (g) => re.test(`${g.name} ${g.brand ?? ''} ${g.model ?? ''}`);
const kind = (...ks) => (g) => ks.includes(g.kind);
const fishery = (f) => (g) => { try { return JSON.parse(g.fisheries_json || '[]').includes(f); } catch { return false; } };
const all = (...fs) => (g) => fs.every((f) => f(g));
const any = (...fs) => (g) => fs.some((f) => f(g));

// pack item id (app/packlist.py) -> which gear satisfies it
export const RULES = {
  'rod-light': all(kind('rod'), has(/spinning|ultralight/i)),
  'trout-lures': all(kind('lure', 'fly'), fishery('trout')),
  bait: any(all(kind('lure'), has(/power ?bait|eggs|nightcrawler|worm/i)), all(kind('terminal'), has(/bobber|float/i)), kind('net')),
  'rod-drift': all(kind('rod'), has(/spinning|baitcasting|drift/i)),
  'steel-lures': any(all(kind('lure', 'fly'), fishery('steelhead')), all(kind('terminal'), has(/bobber|float|drift|leader/i)), all(kind('line'), has(/leader/i))),
  'net-gaff': kind('net'),
  'rod-med': all(kind('rod'), has(/spinning|baitcasting/i)),
  'ww-lures': any(all(kind('lure', 'fly'), fishery('warmwater')), all(kind('lure'), has(/jig|worm|crank|spinnerbait|plastic/i))),
  pol: all(kind('wearable'), has(/polarized|sunglasses/i)),
  'net-ww': any(kind('net'), all(kind('net', 'other'), has(/grip/i))),
  waders: all(kind('wearable'), has(/wader|wading/i)),
  pfd: has(/life jacket|pfd|float vest/i),
  rain: all(kind('wearable'), has(/rain|jacket|shell/i)),
  sun: all(kind('wearable'), has(/sunglasses/i)),
  'first-aid': has(/pliers|clippers|forceps|first.?aid/i)
};

/** Names of active gear that covers a pack item, at most `limit` (the rest are counted in `more`). */
export function ownedFor(itemId, gear, limit = 3) {
  const rule = RULES[itemId];
  if (!rule) return { names: [], more: 0 };
  const hits = (gear || []).filter((g) => !g.deleted && (g.status ?? 'active') === 'active' && rule(g)).map((g) => g.name);
  const uniq = [...new Set(hits)].sort((a, b) => a.localeCompare(b));
  return { names: uniq.slice(0, limit), more: Math.max(0, uniq.length - limit) };
}

export const ownedText = ({ names, more }) => (names.length ? `You have: ${names.join(', ')}${more ? ` and ${more} more` : ''}` : '');
