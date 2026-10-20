import test from 'node:test';
import assert from 'node:assert/strict';
import { forecastNote } from './forecastText.js';
test('forecast distinguishes missing area from unavailable date and labels nearby provenance', () => {
  assert.equal(forecastNote(null), 'No forecast cached for this area yet');
  assert.equal(forecastNote({ day: null }), 'No forecast available for this date');
  const weather = { distance_km: 12.3, day: { short: 'Cloudy', precip_pct: 20, wind: '5 mph', wind_dir: 'W' } };
  assert.equal(forecastNote(weather), 'Area forecast · NWS point 12 km away. Cloudy, 20% rain, wind 5 mph W');
  assert.match(forecastNote({ ...weather, distance_km: 0.2 }), /<1 km away/);
  assert.equal(forecastNote({ ...weather, distance_km: 0 }), 'Cloudy, 20% rain, wind 5 mph W');
});
