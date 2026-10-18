import fs from 'node:fs/promises';
import path from 'node:path';

// Package the original assets used by the implemented mobile screens.
// Full design downloads stay intact in public/ for design inspection and future pages.
const HERITAGE_ARTICLE_ASSETS = [
  '/design/images/6c315b81dd6dfeb3b254b58c6798c9b5.png',
  '/design/images/ba12a3b2e432326ea765587195b54a2d.png',
  '/design/images/5cf22302a02d1b6a59b17ba9fdd26219.png',
  '/design/images/2e521aeae97258549215ecf8a09efd08.png',
  '/design/images/1d096953210d426fc2ef3300764b80a3.webp',
];
export function androidPublicAssets() {
  let config;
  return {
    name: 'android-referenced-public-assets',
    apply: 'build',
    configResolved(resolved) { config = resolved; },
    async closeBundle() {
      const publicRoot = path.resolve(config.root, 'public');
      const outputRoot = path.resolve(config.root, config.build.outDir);
      const mobileRoot = path.resolve(config.root, 'src/mobile');
      const files = [];
      async function scan(directory) {
        for (const entry of await fs.readdir(directory, { withFileTypes: true })) {
          const file = path.join(directory, entry.name);
          if (entry.isDirectory()) await scan(file);
          else if (/\.(vue|ts|css)$/.test(entry.name)) files.push(file);
        }
      }
      await scan(mobileRoot);
      const source = (await Promise.all(files.map(file => fs.readFile(file, 'utf8')))).join('\n');
      const nodeIds = new Set([...source.matchAll(/["'](\d+:[\d/:]+)["']/g)].map(match => match[1]));
      const urls = new Set([...source.matchAll(/\/design\/[a-zA-Z0-9_./-]+\.(?:ttf|woff2?|svg|webp|png|jpe?g)/g)].map(match => match[0]));
      for (const url of HERITAGE_ARTICLE_ASSETS) urls.add(url);
      const catalog = JSON.parse(await fs.readFile(path.join(mobileRoot, 'design-assets.json'), 'utf8'));
      for (const screen of Object.values(catalog)) {
        for (const [id, url] of Object.entries({ ...screen.images, ...screen.icons })) {
          if (nodeIds.has(id) && !url.endsWith('/undefined')) urls.add(url);
        }
      }
      const packaged = [];
      for (const url of [...urls].sort()) {
        const sourceFile = path.resolve(publicRoot, '.' + url);
        const targetFile = path.resolve(outputRoot, '.' + url);
        if (!sourceFile.startsWith(publicRoot + path.sep) || !targetFile.startsWith(outputRoot + path.sep)) throw new Error('Public asset path escaped the app directory');
        await fs.mkdir(path.dirname(targetFile), { recursive: true });
        await fs.copyFile(sourceFile, targetFile);
        packaged.push({ url, bytes: (await fs.stat(sourceFile)).size });
      }
      // Retain font licenses and the small existing static fallback resources.
      for (const entry of await fs.readdir(path.join(publicRoot, 'design/fonts'))) {
        if (entry.endsWith('.txt')) await fs.copyFile(path.join(publicRoot, 'design/fonts', entry), path.join(outputRoot, 'design/fonts', entry));
      }
      await fs.cp(path.join(publicRoot, 'static'), path.join(outputRoot, 'static'), { recursive: true });
      await fs.writeFile(path.join(outputRoot, 'android-assets.json'), JSON.stringify({ assets: packaged, bytes: packaged.reduce((sum, file) => sum + file.bytes, 0) }, null, 2));
      console.log(`Android public assets: ${packaged.length} original resources, ${(packaged.reduce((sum, file) => sum + file.bytes, 0) / 1048576).toFixed(1)} MiB`);
    }
  };
}
