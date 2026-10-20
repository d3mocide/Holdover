// Bounds describe download rectangles, never official fishing-zone or access boundaries.
export const ZONE_BBOX = [-123.9, 43.3, -121.5, 46.1];
export const MAX_OFFLINE_TILES = 25000;
export const ESTIMATED_TILE_BYTES = 20000;
export const hasPoint = w => Number.isFinite(w?.lat) && Number.isFinite(w?.lon);
export function areaAround(water, km = 15) {
  if (!hasPoint(water) || !(km > 0 && km <= 50)) return null;
  const dy = km / 111.195, dx = dy / Math.cos(water.lat * Math.PI / 180);
  return [water.lon - dx, water.lat - dy, water.lon + dx, water.lat + dy];
}
export function watersBounds(waters) {
  const points = waters.filter(hasPoint);
  if (!points.length) return null;
  return [Math.min(...points.map(w => w.lon)) - .1, Math.min(...points.map(w => w.lat)) - .1,
    Math.max(...points.map(w => w.lon)) + .1, Math.max(...points.map(w => w.lat)) + .1];
}
export function intersectBounds(a, b) {
  if (!a || !b || ![...a, ...b].every(Number.isFinite)) return null;
  const out = [Math.max(a[0], b[0]), Math.max(a[1], b[1]), Math.min(a[2], b[2]), Math.min(a[3], b[3])];
  return out[0] < out[2] && out[1] < out[3] ? out : null;
}
const lon2x = (lon, z) => Math.max(0, Math.min(2 ** z - 1, Math.floor(((lon + 180) / 360) * 2 ** z)));
const lat2y = (lat, z) => Math.max(0, Math.min(2 ** z - 1, Math.floor(((1 - Math.asinh(Math.tan(Math.max(-85, Math.min(85, lat)) * Math.PI / 180)) / Math.PI) / 2) * 2 ** z)));
function ranges(bbox, minZ, maxZ) {
  if (!bbox || bbox.length !== 4 || !bbox.every(Number.isFinite) || bbox[0] >= bbox[2] || bbox[1] >= bbox[3]) return [];
  if (!Number.isInteger(minZ) || !Number.isInteger(maxZ) || minZ < 0 || maxZ > 16 || minZ > maxZ) return [];
  return Array.from({ length: maxZ - minZ + 1 }, (_, i) => {
    const z = minZ + i;
    return [z, lon2x(bbox[0],z), lon2x(bbox[2],z), lat2y(bbox[3],z), lat2y(bbox[1],z)];
  });
}
export const tileCount = (bbox = ZONE_BBOX, minZ = 6, maxZ = 11) => ranges(bbox,minZ,maxZ).reduce((n,[,x0,x1,y0,y1]) => n + (x1-x0+1)*(y1-y0+1), 0);
export function tileList(bbox = ZONE_BBOX, minZ = 6, maxZ = 11) {
  if (tileCount(bbox,minZ,maxZ) > MAX_OFFLINE_TILES) throw new Error('Choose a smaller area or lower map detail (limit 25,000 tiles).');
  const out = [];
  for (const [z,x0,x1,y0,y1] of ranges(bbox,minZ,maxZ)) for (let x=x0;x<=x1;x++) for (let y=y0;y<=y1;y++) out.push([z,x,y]);
  return out;
}
export function tripDates(start, count) {
  const date = new Date(`${start}T12:00:00Z`);
  if (!Number.isFinite(date.getTime()) || date.toISOString().slice(0,10) !== start || ![1,3,7].includes(count)) return [];
  return Array.from({length:count}, (_,i) => new Date(date.getTime()+i*86400000).toISOString().slice(0,10));
}
