import test from 'node:test';
import assert from 'node:assert/strict';
import { photoSize, resizePhoto } from './photo.js';
test('photo dimensions stay proportional, bounded, and never enlarge small pictures', () => {
  assert.deepEqual(photoSize(4000,3000), { width:1600,height:1200 });
  assert.deepEqual(photoSize(3000,4000), { width:1200,height:1600 });
  assert.deepEqual(photoSize(400,300), { width:400,height:300 });
  assert.deepEqual(photoSize(1,5000), { width:1,height:1600 });
  assert.throws(() => photoSize(0,10));
});

test('unsupported or excessively large photos fail before decoding or storage',async()=>{
  await assert.rejects(resizePhoto({type:'image/gif',size:100}),/JPEG, PNG or WebP/);
  await assert.rejects(resizePhoto({type:'image/jpeg',size:51*1024*1024}),/smaller than 50 MB/);
});
