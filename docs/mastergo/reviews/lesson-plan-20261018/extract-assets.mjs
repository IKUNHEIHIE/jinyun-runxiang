import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
const here = path.dirname(fileURLToPath(import.meta.url));
const repo = path.resolve(here, '../../../..');
const html = fs.readFileSync(path.join(repo,'.local/android/references/lesson-plan-structure.html'),'utf8');
if (html.includes('@@SVG:')) throw Error('Unresolved source vectors');
const icons = {};
for (const match of html.matchAll(/<div data-node-id="([^"]+)"[^>]*>(?:(?!data-node-id=)[\s\S])*?(<svg[\s\S]*?<\/svg>)/g)) {
  const filename = `lesson-plan-${match[1].replace(':','-')}.svg`;
  fs.writeFileSync(path.join(repo,'user-web/public/design/icons',filename),match[2]);
  icons[match[1]] = '/design/icons/'+filename;
}
if (Object.keys(icons).length!==14) throw Error('Expected 14 source SVGs');
const manifestPath = path.join(repo,'user-web/src/mobile/design-assets.json');
const manifest = JSON.parse(fs.readFileSync(manifestPath,'utf8'));
Object.assign(manifest['layer-5-02348'].icons, icons);
manifest['layer-5-02348'].images['5:02348'] = '/design/images/5576fb521ca134e55c7ca0d481dcc303.png';
fs.writeFileSync(manifestPath,JSON.stringify(manifest,null,2)+'\n');
console.log(JSON.stringify({sourceSvgCount:Object.keys(icons).length}));
