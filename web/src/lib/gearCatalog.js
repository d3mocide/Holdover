// A small starter catalog so adding gear is a tap, not typing. Names are common Oregon trout, steelhead and
// warmwater choices. Brands appear only where the product line is certain; everything is editable once added,
// and anything not listed can be typed freely. Fisheries: trout, steelhead, warmwater.

export const KINDS = [
  ['rod', 'Rods', 'Rod'], ['reel', 'Reels', 'Reel'], ['line', 'Line & leader', 'Line'], ['lure', 'Lures & bait', 'Lure'],
  ['fly', 'Flies', 'Fly'], ['terminal', 'Terminal tackle', 'Terminal'], ['net', 'Nets & tools', 'Net or tool'],
  ['wearable', 'Wearables', 'Wearable'], ['electronics', 'Electronics', 'Electronics'], ['other', 'Other', 'Other']
];
export const KIND_LABEL = Object.fromEntries(KINDS.map(([k, plural]) => [k, plural]));
export const KIND_ONE = Object.fromEntries(KINDS.map(([k, , one]) => [k, one]));
export const FISHERY_LABEL = { trout: 'Trout', steelhead: 'Steelhead', warmwater: 'Warmwater' };
// Kinds a trip's "gear used" and a catch's "caught on" can point at.
export const TRIP_KINDS = ['lure', 'fly', 'terminal'];

const T = 'trout', S = 'steelhead', W = 'warmwater';
const e = (kind, name, fisheries, brand = null, size = null) => ({ kind, name, brand, size, fisheries });

export const CATALOG = [
  // lures and bait
  e('lure', 'Panther Martin spinner', [T, W], 'Panther Martin', '1/16 to 1/4 oz'),
  e('lure', 'Mepps Aglia spinner', [T, W], 'Mepps', '#0 to #3'),
  e('lure', 'Rooster Tail', [T, S, W], "Worden's", '1/16 to 1/4 oz'),
  e('lure', 'Blue Fox Vibrax', [T, S], 'Blue Fox', '#1 to #4'),
  e('lure', 'Kastmaster spoon', [T, W], 'Acme', '1/8 to 1/2 oz'),
  e('lure', 'Little Cleo spoon', [T], 'Acme', '1/8 to 1/2 oz'),
  e('lure', 'Dick Nite spoon', [T, S], 'Luhr Jensen', '#0 to #2'),
  e('lure', 'Krocodile spoon', [T], 'Luhr Jensen', '1/4 to 1/2 oz'),
  e('lure', 'Flatfish', [T, S], "Worden's", 'F4 to F7'),
  e('lure', 'Kwikfish', [S], 'Luhr Jensen', 'K10 to K16'),
  e('lure', 'Spin-N-Glo', [S], null, 'size 2 to 4'),
  e('lure', 'Corkie and yarn', [S], null, '8 to 12 mm'),
  e('lure', 'Rapala Original Floating', [T, W], 'Rapala', 'F05 to F09'),
  e('lure', 'Rapala Shad Rap', [T, W], 'Rapala', 'SR5 to SR7'),
  e('lure', 'Wiggle Wart', [W], 'Storm', null),
  e('lure', 'PowerBait', [T], 'Berkley', 'dough or nuggets'),
  e('lure', 'Gulp! bait', [T, S, W], 'Berkley', null),
  e('lure', 'Salmon eggs (cured)', [T, S], null, null),
  e('lure', 'Nightcrawlers', [T, W], null, null),
  e('lure', 'Marabou jig', [T, W], null, '1/32 to 1/8 oz'),
  e('lure', 'Curly-tail grub', [W], null, '2 to 4 in'),
  e('lure', 'Plastic worm (Texas rig)', [W], null, '4 to 7 in'),
  e('lure', 'Stick bait (Senko style)', [W], null, '4 to 5 in'),
  e('lure', 'Crankbait', [W], null, null),
  e('lure', 'Spinnerbait', [W], null, '1/4 to 1/2 oz'),
  e('lure', 'Beetle Spin', [W], null, '1/16 to 1/4 oz'),
  e('lure', 'Tube jig', [W], null, '3 to 4 in'),
  // flies
  e('fly', 'Woolly Bugger', [T, W], null, '#4 to #10'),
  e('fly', 'Egg-Sucking Leech', [T, S], null, '#2 to #8'),
  e('fly', 'Elk Hair Caddis', [T], null, '#12 to #18'),
  e('fly', 'Parachute Adams', [T], null, '#12 to #20'),
  e('fly', 'Pheasant Tail nymph', [T], null, '#12 to #18'),
  e('fly', "Hare's Ear nymph", [T], null, '#10 to #16'),
  e('fly', 'Prince Nymph', [T], null, '#10 to #16'),
  e('fly', 'Copper John', [T], null, '#12 to #18'),
  e('fly', 'Zebra Midge', [T], null, '#16 to #22'),
  e('fly', 'San Juan Worm', [T], null, '#10 to #14'),
  e('fly', 'Stimulator', [T], null, '#6 to #12'),
  e('fly', 'Egg pattern (Glo Bug)', [T, S], null, '8 to 12 mm'),
  e('fly', 'Green Butt Skunk', [S], null, '#2 to #8'),
  e('fly', 'Clouser Minnow', [W, T], null, '#2 to #8'),
  e('fly', 'Muddler Minnow', [T, W], null, '#4 to #10'),
  e('fly', 'Foam popper', [W], null, '#4 to #8'),
  // rods and reels
  e('rod', 'Spinning rod', [T, S, W]), e('rod', 'Ultralight spinning rod', [T, W]), e('rod', 'Baitcasting rod', [S, W]),
  e('rod', 'Fly rod', [T, S, W]), e('reel', 'Spinning reel', [T, S, W]), e('reel', 'Baitcasting reel', [S, W]),
  e('reel', 'Fly reel', [T, S, W]),
  // line
  e('line', 'Monofilament line', [T, S, W]), e('line', 'Fluorocarbon line', [T, S, W]), e('line', 'Braided line', [S, W]),
  e('line', 'Fly line (floating)', [T, S, W]), e('line', 'Fly line (sink-tip)', [S, T]), e('line', 'Tapered leader', [T, W]),
  e('line', 'Tippet', [T]),
  // terminal tackle
  e('terminal', 'Split shot', [T, W]), e('terminal', 'Barrel swivel', [T, S, W]), e('terminal', 'Snap swivel', [T, S, W]),
  e('terminal', 'Circle hook', [S, W]), e('terminal', 'Bait hook', [T, W]), e('terminal', 'Treble hook', [T, W]),
  e('terminal', 'Bobber or float', [T, W]), e('terminal', 'Slip bobber', [W]), e('terminal', 'Drift weight', [S]),
  // nets, wearables, electronics
  e('net', 'Landing net', [T, S, W]), e('net', 'Fish grip', [S, W]), e('net', 'Forceps and pliers', [T, S, W]),
  e('wearable', 'Waders', [T, S]), e('wearable', 'Wading boots', [T, S]), e('wearable', 'Wading staff', [T, S]),
  e('wearable', 'Polarized sunglasses', [T, S, W]), e('wearable', 'Rain jacket', [T, S, W]), e('wearable', 'Fishing vest or pack', [T, S, W]),
  e('electronics', 'Fish finder', [W]), e('electronics', 'Stream thermometer', [T, S])
];

/** Catalog entries matching what has been typed, best first. */
export function suggest(query, kind = null, limit = 8) {
  const q = (query || '').trim().toLowerCase();
  const pool = kind ? CATALOG.filter((c) => c.kind === kind) : CATALOG;
  if (!q) return pool.slice(0, limit);
  const scored = [];
  for (const c of pool) {
    const n = c.name.toLowerCase();
    const i = n.indexOf(q);
    if (i === 0) scored.push([0, c]); else if (i > 0) scored.push([1, c]);
    else if (n.split(/\s+/).some((w) => w.startsWith(q))) scored.push([2, c]);
  }
  return scored.sort((a, b) => a[0] - b[0] || a[1].name.localeCompare(b[1].name)).slice(0, limit).map(([, c]) => c);
}
