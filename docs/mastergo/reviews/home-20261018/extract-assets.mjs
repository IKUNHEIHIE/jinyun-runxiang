import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
const repo = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../../../..');
const html = fs.readFileSync(path.join(repo, '.local/android/references/home-structure.html'), 'utf8');
if (html.includes('@@SVG:')) throw Error('Unresolved source SVGs');
const icons = {};
for (const m of html.matchAll(/<div data-node-id="([^"]+)"[^>]*>(?:(?!data-node-id=)[\s\S])*?(<svg[\s\S]*?<\/svg>)/g)) {
  const name = `home-${m[1].replace(':', '-')}.svg`;
  fs.writeFileSync(path.join(repo, 'user-web/public/design/icons', name), m[2]);
  icons[m[1]] = '/design/icons/' + name;
}
if (Object.keys(icons).length !== 26) throw Error('Expected 26 source vectors');
const file = path.join(repo, 'user-web/src/mobile/design-assets.json');
const assets = JSON.parse(fs.readFileSync(file, 'utf8'));
Object.assign(assets.home.icons, icons);
fs.writeFileSync(file, JSON.stringify(assets, null, 2) + '\n');
console.log('Extracted 26 source vectors without rewriting their paths.');
