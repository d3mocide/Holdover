// Wording for NOAA's flood category on a river gauge. It repeats NOAA's category and never says a river is safe.
export function floodText(f) {
  if (!f) return null;
  const stage = f.stage_ft != null ? `, stage ${f.stage_ft} ft` : '';
  let s = `NOAA flood category: ${f.label}${stage}`;
  if (f.forecast && f.forecast.category !== 'no_flooding') {
    const crest = f.forecast.stage_ft != null ? ` (${f.forecast.stage_ft} ft)` : '';
    s += `. NOAA forecast: ${f.forecast.label.toLowerCase()}${crest}`;
  }
  return s;
}
export const floodElevated = (f) => !!f && (f.elevated || (!!f.forecast && f.forecast.category !== 'no_flooding'));

/** The one-line NOAA note for a gauge card: the category, and a forecast only when it is not "no flooding". */
export function floodShort(f) {
  if (!f) return null;
  const fc = f.forecast && f.forecast.category !== 'no_flooding' ? `, forecast ${f.forecast.label.toLowerCase()}` : '';
  return `NOAA: ${f.label.toLowerCase()}${fc}`;
}
