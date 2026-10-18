<script>
  // Who the data comes from. Some of these are licence or courtesy requirements (OpenStreetMap's ODbL, USGS's credit
  // request); all of them are what a person deciding whether to trust a number would want to know.
  const SOURCES = [
    ['Stocking schedule and weekly Recreation Report', 'Oregon Department of Fish & Wildlife', 'https://myodfw.com', 'Stocking is by week and can change. Check ODFW for regulations.'],
    ['Algae advisories', 'Oregon Health Authority', 'https://www.oregon.gov/oha/ph/healthyenvironments/recreation/harmfulalgaeblooms/pages/blue-greenalgaeadvisories.aspx', 'Only some waters are monitored.'],
    ['Weather forecasts', 'National Weather Service', 'https://www.weather.gov', null],
    ['Streamflow and water temperature', 'U.S. Geological Survey', 'https://waterdata.usgs.gov', 'Provisional data, subject to revision.'],
    ['Reservoir levels', 'U.S. Army Corps of Engineers, Northwestern Division', 'https://www.nwd-wc.usace.army.mil/dd/common/dataquery/www/', 'Unverified data, subject to revision.'],
    ['Fire danger', 'Oregon Department of Forestry', 'https://gisapps.odf.oregon.gov/firerestrictions/PFR.html', 'Covers lands ODF protects. Check ODF for restrictions and closures.'],
    ['Wildfire perimeters', 'National Interagency Fire Center (interagency data)', 'https://data-nifc.opendata.arcgis.com', 'Perimeters can lag a new fire. A nearby fire is not by itself a closure.'],
    ['Map data', 'OpenStreetMap contributors (ODbL), tiles from Protomaps', 'https://www.openstreetmap.org/copyright', null],
    ['Map software', 'MapLibre GL JS', 'https://maplibre.org', null],
    ['Type', 'IBM Plex and Noto Sans (SIL Open Font License)', 'https://openfontlicense.org', null]
  ];
</script>

<section class="card">
  <h2 class="eyebrow">Data sources and credits</h2>
  <ul>
    {#each SOURCES as [what, who, href, note]}
      <li><span class="what">{what}</span><a {href} target="_blank" rel="noopener">{who}</a>{#if note}<span class="quiet small">{note}</span>{/if}</li>
    {/each}
  </ul>
  <p class="quiet small">Holdover is an independent project, not affiliated with these agencies. It never states regulations: always check ODFW's official pages.</p>
</section>

<style>
  h2 { margin: 0 0 8px; } ul { list-style: none; padding: 0; margin: 0 0 8px; }
  li { display: flex; flex-direction: column; gap: 1px; padding: 8px 0; border-bottom: 1px solid var(--hair); } li:last-child { border-bottom: 0; }
  .what { font-size: 12px; color: var(--text-quiet); } .small { font-size: 12.5px; margin: 0; } a { min-height: 24px; }
</style>
