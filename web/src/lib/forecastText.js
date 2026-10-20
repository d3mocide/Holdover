/** Location provenance and empty states for stored NWS forecasts. */
export function forecastNote(weather) {
  if (!weather) return 'No forecast cached for this area yet';
  if (!weather.day) return 'No forecast available for this date';
  const w = weather.day;
  const location = weather.distance_km > 0 ? `Area forecast · NWS point ${weather.distance_km < 1 ? '<1' : Math.round(weather.distance_km)} km away. ` : '';
  return `${location}${w.short ?? ''}${w.precip_pct != null ? `, ${w.precip_pct}% rain` : ''}, wind ${w.wind ?? 'unknown'} ${w.wind_dir ?? ''}`.trim();
}
