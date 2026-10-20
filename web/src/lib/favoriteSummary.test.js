import test from 'node:test';
import assert from 'node:assert/strict';
import {recentTrips,forecastStale} from './favoriteSummary.js';
test('favorites summarize only current water and live trips/catches, newest first',()=>{
  const trips=[{uuid:'old',waterbody_id:1,started_at:'2026-01-01'},{uuid:'new',waterbody_id:1,started_at:'2026-02-01'}, {uuid:'gone',waterbody_id:1,deleted:1},{uuid:'other',waterbody_id:2}];
  assert.deepEqual(recentTrips(trips,[{trip_uuid:'new',count:2},{trip_uuid:'new',count:99,deleted:1}],1).map(t=>[t.uuid,t.fish]),[['new',2],['old',0]]);
});
test('cached favorite forecasts age while offline',()=>{
  const now=Date.parse('2026-10-20T00:00:00Z');
  assert.equal(forecastStale({as_of:'2026-10-19T23:00:00Z'},now),false);
  assert.equal(forecastStale({as_of:'2026-10-19T12:00:00Z'},now),true);
  assert.equal(forecastStale({as_of:'invalid'},now),true);
});
