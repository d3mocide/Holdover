export function recentTrips(trips, catches, id) {
  const liveCatches=catches.filter(c=>!c.deleted);
  return trips.filter(t=>!t.deleted && t.waterbody_id===id).sort((a,b)=>(b.started_at??'').localeCompare(a.started_at??'')).slice(0,3)
    .map(t=>({...t,fish:liveCatches.filter(c=>c.trip_uuid===t.uuid).reduce((n,c)=>n+(c.count??0),0)}));
}
export const forecastStale = (w,now=Date.now()) => !w || !!w.stale || !Number.isFinite(Date.parse(w.as_of)) || now-Date.parse(w.as_of)>6*3600000;
