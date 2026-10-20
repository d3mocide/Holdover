export const PHOTO_MAX_EDGE = 1600;
export function photoSize(width, height, edge = PHOTO_MAX_EDGE) {
  if (!(width > 0 && height > 0)) throw new Error('This photo has no readable dimensions.');
  const scale = Math.min(1, edge / Math.max(width, height));
  return { width: Math.max(1, Math.round(width * scale)), height: Math.max(1, Math.round(height * scale)) };
}

/** Browser decoding applies EXIF orientation before canvas export; exported pixels need no orientation tag. */
export async function resizePhoto(file) {
  if (!['image/jpeg', 'image/png', 'image/webp'].includes(file.type)) throw new Error('Choose a JPEG, PNG or WebP photo.');
  if (file.size > 50 * 1024 * 1024) throw new Error('Choose a photo smaller than 50 MB.');
  const url = URL.createObjectURL(file), img = new Image();
  try {
    img.src = url;
    try { await img.decode(); } catch { throw new Error('This photo could not be read. Choose another image.'); }
    const { width, height } = photoSize(img.naturalWidth, img.naturalHeight);
    const canvas = document.createElement('canvas'); canvas.width = width; canvas.height = height;
    const ctx = canvas.getContext('2d');
    if (!ctx) throw new Error('This browser could not prepare the photo.');
    ctx.drawImage(img, 0, 0, width, height);
    const type = file.type === 'image/jpeg' ? 'image/jpeg' : 'image/webp';
    const blob = await new Promise(resolve => canvas.toBlob(resolve, type, .82));
    if (!blob) throw new Error('This photo could not be resized. Try another image.');
    if (blob.size > 15 * 1024 * 1024) throw new Error('The prepared photo is still too large. Choose a smaller image.');
    return blob;
  } finally { img.src = ''; URL.revokeObjectURL(url); }
}
