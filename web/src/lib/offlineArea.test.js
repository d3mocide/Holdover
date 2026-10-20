import test from 'node:test';
import assert from 'node:assert/strict';
import { areaAround,watersBounds,intersectBounds,tileCount,tileList,tripDates } from './offlineArea.js';
test('trip bounds use stored pins and reject unlocated waters',()=>{
  assert.equal(areaAround({lat:null,lon:null}),null);
  const a=areaAround({lat:44,lon:-122},15);assert.ok(a[0]<-122&&a[2]>-122&&a[1]<44&&a[3]>44);
  assert.deepEqual(watersBounds([{lat:null,lon:null},{lat:44,lon:-122}]),[-122.1,43.9,-121.9,44.1]);
  assert.deepEqual(intersectBounds([-125,42,-120,47],[-124,43,-121,46]),[-124,43,-121,46]);
  assert.equal(intersectBounds([-125,42,-124,43],[-122,44,-121,45]),null);
});
test('tile enumeration is bounded, matches count and supports areas outside Willamette',()=>{
  const a=areaAround({lat:44,lon:-118},5);const tiles=tileList(a,6,12);assert.equal(tiles.length,tileCount(a,6,12));
  assert.ok(tiles.every(([z,x,y])=>z>=6&&z<=12&&x>=0&&x<2**z&&y>=0&&y<2**z));
  assert.throws(()=>tileList([-125,42,-116,47],6,16),/smaller area/);
  assert.equal(tileCount(null),0);assert.equal(tileCount([1,2,0,3]),0);
});
test('trip dates preserve exact day across month/year boundaries',()=>{
  assert.deepEqual(tripDates('2026-12-31',3),['2026-12-31','2027-01-01','2027-01-02']);
  assert.deepEqual(tripDates('bad',3),[]);assert.deepEqual(tripDates('2026-02-30',1),[]);
});
