import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

// Auxiliary structural rendering only; this is not a MasterGo canvas export.
const here = path.dirname(fileURLToPath(import.meta.url));
const repo = path.resolve(here, '../../../..');
const overview = JSON.parse(fs.readFileSync(path.join(here, 'overview.json'), 'utf8'));
const sections = Array.from({ length: overview.totalSections }, (_, i) =>
  JSON.parse(fs.readFileSync(path.join(here, `section-${String(i).padStart(2, '0')}.json`), 'utf8')));
const styles = Object.assign({}, overview.rootMetadata.styles, ...sections.map(s => s.dsl.styles));
const escape = value => String(value ?? '').replace(/[&<>"']/g, c =>
  ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]);
const px = value => typeof value === 'number' ? `${value}px` : value;
const css = value => Object.entries(value).filter(([, v]) => v != null && !String(v).includes('NaN'))
  .map(([k, v]) => `${k}:${v}`).join(';');
const values = ref => styles[ref]?.value ?? [];
const localImage = url => `http://127.0.0.1:5174/design/images/${url.split('/').pop()}`;
const tokenName = id => `--mg-${id.replace(/[^a-z0-9]/gi, '-')}`;
const tokens = Object.entries(styles).flatMap(([id, style]) => {
  if (!id.startsWith('paint_')) return [];
  const color = style.value.find(v => typeof v === 'string');
  return color ? [`${tokenName(id)}:${color}`] : [];
}).join(';');
const audit = { sections: sections.length, nodes: 0, svgPlaceholders: 0, missingVectors: [], unusualOffsets: [] };

function node(n, root = false) {
  audit.nodes++;
  const l = n.layoutStyle ?? {};
  const position = { position: 'absolute', left: px(root ? 0 : l.relativeX ?? 0),
    top: px(root ? 0 : l.relativeY ?? 0), width: px(l.width), height: px(l.height), opacity:n.opacity,
    'border-radius': n.borderRadius, overflow: n.clipsContent ? 'hidden' : undefined };
  if (l.relativeX === null || l.relativeY === null || Math.abs(l.relativeY ?? 0) > 1000)
    audit.unusualOffsets.push({ id: n.id, layout: l });
  const paint = values(n.fill);
  const background = n._color ?? paint.find(v => typeof v === 'string');
  let content = '';
  if (n.type !== 'TEXT') {
    const images = paint.filter(v => v?.url);
    const fillCss = { position: 'absolute', inset: '0', 'border-radius': 'inherit',
      background: background && `var(${tokenName(n.fill)}, ${background})`,
      'background-image': images.length ? [background?.includes('gradient(') ? background : null, ...images.map(v => `url('${localImage(v.url)}')`)].filter(Boolean).join(',') : undefined,
      'background-size': 'cover', 'background-position': 'center', };
    if (n.strokeColor) {
      fillCss.border = `${n.strokeWidth ?? '1px'} solid ${values(n.strokeColor).find(v => typeof v === 'string')}`;
      fillCss['border-width'] = n.strokeWidth ?? '1px';
      fillCss.border = undefined;
      fillCss['border-style'] = 'solid';
      fillCss['border-color'] = values(n.strokeColor).find(v => typeof v === 'string');
    }
    for (const effect of values(n.effect)) {
      const colon = effect.indexOf(':');
      if (colon < 0) continue;
      const key = effect.slice(0, colon), value = effect.slice(colon + 1).replace(/;$/, '').trim();
      fillCss[key] = fillCss[key] ? `${fillCss[key]},${value}` : value;
    }
    if (background || images.length || n.strokeColor || n.effect)
      content += `<div aria-hidden="true" style="${escape(css(fillCss))}"></div>`;
  }
  if (n.svgShortKey) {
    audit.svgPlaceholders++;
    content += `@@SVG:${n.svgShortKey}@@`;
  } else if (n.type === 'PATH') {
    audit.missingVectors.push(n.id);
  }
  if (n.type === 'TEXT') {
    const font = styles[n.text?.[0]?.font]?.value ?? {};
    Object.assign(position, { color: background, 'font-family': `'${font.family}',serif`,
      'font-size': px(font.size), 'font-weight': font.weight,
      'line-height': px(Number(font.lineHeight)), 'letter-spacing': font.letterSpacing === 'auto' ? 'normal' : font.letterSpacing,
      'text-align': n.textAlign, 'white-space': n.textMode === 'single-line' ? 'pre' : 'pre-wrap' });
    // Text boxes encode the vertical title/rotated English through their aspect ratios.
    content += (n.text ?? []).map(t => escape(t.text)).join('');
  }
  content += (n.children ?? []).map(child => node(child)).join('');
  return `<div data-node-id="${escape(n.id)}" data-name="${escape(n.name)}" style="${escape(css(position))}">${content}</div>`;
}

const containers = [...overview.splitContainers].reverse().sort((a,b)=>b.width*b.height-a.width*a.height).map(c => {
  const paint=values(c.fill), color=c.background ?? paint.find(v=>typeof v==='string');
  return `<div data-node-id="${escape(c.id)}" style="${escape(css({ position:'absolute',left:px(c.x),top:px(c.y),width:px(c.width),height:px(c.height),background:color,
    'background-image':paint.filter(v=>v?.url).map(v=>`url('${localImage(v.url)}')`).join(',')||undefined,'background-size':'cover','background-position':'center','border-radius':c.borderRadius }))}"></div>`;
}).join('');
const body = sections.map((s, i) => {
  const b = overview.sections[i];
  return `<section data-section="${i}" style="${escape(css({ position: 'absolute', left: px(b.x), top: px(b.y), width: px(b.width), height: px(b.height) }))}">${s.dsl.nodes.map(n => node(n, true)).join('')}</section>`;
}).join('');
const html = `<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>${escape(overview.rootMetadata.name)}</title><style>/* Tokens copied from the MasterGo section styles. */:root{${tokens}}*{box-sizing:border-box}html,body{margin:0}section{margin:0}svg{display:block;width:100%;height:100%}@font-face{font-family:'Ma Shan Zheng';src:url('http://127.0.0.1:5174/design/fonts/MaShanZheng.ttf');font-weight:400}@font-face{font-family:'Noto Serif SC';src:url('http://127.0.0.1:5174/design/fonts/NotoSerifSC.ttf');font-weight:100 900}</style></head><body><main data-design-root="5:01925" style="position:relative;width:373px;min-height:1394px;background:#FFFFFF;overflow:hidden">${containers}${body}</main></body></html>`;
const output = path.join(repo, '.local/android/references');
fs.mkdirSync(output, { recursive: true });
fs.writeFileSync(path.join(output, 'home-before-svg.html'), html);
fs.writeFileSync(path.join(output, 'home-structure-audit.json'), JSON.stringify(audit, null, 2));
console.log(JSON.stringify(audit));
