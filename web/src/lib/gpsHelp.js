// Browsers allow location only on secure origins (HTTPS or localhost). Say that, instead of the raw browser error.
export function gpsMessage(err, secure = typeof isSecureContext === 'boolean' ? isSecureContext : true) {
  if (!secure) return 'Location only works on a secure (HTTPS) address, and this one is plain HTTP. Pick a waterbody instead.';
  if (err?.code === 1) return 'Location was blocked. Allow it for this site, or pick a waterbody instead.';
  return `No GPS fix${err?.message ? ` (${err.message})` : ''}. Pick a waterbody instead.`;
}
