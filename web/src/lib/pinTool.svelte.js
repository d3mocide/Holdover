// Placing a waterbody's pin from the map: the admin picks a waterbody in Settings, the map goes into tap mode, the tap is saved.
export const pin = $state({ target: null, version: 0 });
export const startPin = (wb) => { pin.target = { id: wb.id, name: wb.name, zone: wb.zone }; };
export const cancelPin = () => { pin.target = null; };
export const pinSaved = () => { pin.target = null; pin.version += 1; };
