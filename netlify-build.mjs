import { mkdir, copyFile, stat } from 'node:fs/promises';
import { join } from 'node:path';

const root = process.cwd();
const publicDir = join(root, 'public');
await mkdir(publicDir, { recursive: true });

for (const file of ['index.html', 'app.js', 'app.css']) {
  const source = join(root, file);
  const target = join(publicDir, file);
  try {
    await stat(source);
    await copyFile(source, target);
  } catch {
    // If the public copy already exists, retain it. This keeps the build
    // resilient when the repository is uploaded without empty directories.
    try { await stat(target); } catch { throw new Error(`Missing frontend asset: ${file}`); }
  }
}
console.log('Netlify frontend prepared:', publicDir);
