# Journal-informed recommendations

Open **Map > Explore waters > Best bets** or **Plan > Next 7 days**, then enable **Use my journal in rankings**.
The switch is off on a fresh page load and resets when the signed-in account changes. It is shared between Map
and Plan for that page session. No new account setting, personal table, migration or service is involved.

Each Plan result, waterbody details sheet and day view has an expandable **Your journal** comparison. The day view
also shows the recorded lures/flies and setups to consider for packing. Empty or stale data is explained explicitly.

## What counts as comparable

Calculations run in the browser against the existing device journal, including unsynced entries. Public rankings
provide stored, source-timed comparison inputs; no personal history is sent to a public endpoint or an LLM.

- Same stored waterbody id; live trips only, with a valid start time in the past.
- **Rivers:** use the first fresh discharge gauge in site-number order, consistently across views. A past trip
  needs that same gauge, with flow within 20% of its latest observed value. This uses latest observations for
  future plans too; it is labelled as an observation, not a forecast or seasonal normal.
- **Other waters:** recorded forecast air temperature within 10°F of the selected day's forecast. This is an
  air-weather comparison, not a water-temperature or habitat model.
- Current and historic discharge readings must be at most three hours old relative to now or the trip's start.
  Weather source times must be at most six hours old. Future source times are refused.
- A historic conditions snapshot must have been captured within three hours of the recorded trip start.
  Backdated logs and expired offline snapshots are not guessed into a match.
- All nondeleted catch counts must be nonnegative integers. Unknown/invalid counts exclude that trip; no catch
  rows mean no recorded catches. Such trips remain in the denominator, alongside explicit zero-count entries.

Comparisons cover **all species** because existing trips do not record a target fishery. The selected fishery
still controls the public candidate waters and their public scores. The UI does not infer an unsuccessful
trip's intended species from its gear or from other trips. Trip duration, angler effort and access conditions
are not controlled for. These are transparent heuristics, not validated fishing ranges or catch probabilities.

## Optional score adjustment

With fewer than three comparable trips the adjustment is zero. Otherwise:

    adjustment = round_to_tenth(5 × (2 × trips_with_recorded_catches / comparable_trips − 1)
                                × min(comparable_trips / 10, 1))

This shrinks small samples toward no adjustment and caps the change at ±5 points. The adjusted score is clamped
to 0–100 and candidates are sorted again, preserving public order for ties. Disabling the switch restores the
public score/order exactly. No comparison data gives no reward or penalty. Public factor contributions and
evidence coverage stay labelled as public; the journal adjustment is separate and displayed to a tenth of a point.

The comparison exposes its source gauge/time or forecast/time, the number of matching trips and trips with
recorded catches, and dated trip outcomes with each captured comparison value and time. The latest 20 trips
(five in a Plan result) are displayed; the text states when more trips count in the calculation.

## Gear evidence

Active, nondeleted lures and flies are suggested only when a comparable trip has catches explicitly attributed
to that item through the existing "caught on" reference. The denominator includes comparable trips where the
item was logged as used, even if no catches were attributed to it. Deleted catches do not contribute.

Nondeleted setups show their comparable usage count and how many of those trips had recorded catches. This is
an association with the trip, not attribution of every fish to the setup. Results are ordered by trips with
recorded catches, then recorded uses and name, with at most three of each. Recorded use never establishes that
gear caused a result, and suggestions do not claim a setup's contents are currently available or suitable.

## Offline and account boundaries

Advice uses Dexie live queries over the existing journal and owner metadata. Existing writes, edits, deletions
and sync updates recompute it. Public comparison values age while the page is open; stale values disable the
comparison even offline. An offline reload works after loading the public ranking/details into the existing
service-worker cache. An older cached ranking without comparison inputs still displays public results.

An in-memory snapshot whose owner differs from the signed-in account is hidden while device clearing/pulling
finishes. Existing sign-in adoption and shared-device clearing are unchanged; see [accounts.md](accounts.md).
No personal ranking is stored in the shared API cache. No journal entries or captured conditions are rewritten.

Automated evidence and remaining physical-device/field gates are recorded in [BUILD_LOG.md](BUILD_LOG.md).
