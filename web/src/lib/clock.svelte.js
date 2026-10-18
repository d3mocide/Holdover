// The 12/24-hour setting. Per device, in localStorage; defaults to 12-hour (AM/PM).
import { formatTime, formatClockText } from './clockFormat.js';

const KEY = 'holdover.clock';
const read = () => { try { return localStorage.getItem(KEY) === '24' ? '24' : '12'; } catch { return '12'; } };

export const clock = $state({ mode: read() });
export function setClock(mode) {
  clock.mode = mode === '24' ? '24' : '12';
  try { localStorage.setItem(KEY, clock.mode); } catch { /* the choice just will not persist */ }
}
export const hhmm = (iso) => formatTime(iso, clock.mode);
export const asOf = (iso) => (iso ? `as of ${hhmm(iso)}` : 'no data');
export const clockText = (text) => formatClockText(text, clock.mode);
