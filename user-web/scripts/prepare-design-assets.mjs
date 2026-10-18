import { readdir, readFile, writeFile, mkdir } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const source = path.resolve(root, "../docs/mastergo");
const assets = path.resolve(root, "public/design");
await mkdir(path.join(assets, "images"), { recursive: true });
await mkdir(path.join(assets, "icons"), { recursive: true });
await mkdir(path.join(root, "src/mobile"), { recursive: true });
const urls = new Map();
const unavailable = new Set();
const screens = {};
const walk = (node, visit) => {
  if (!node || typeof node !== "object") return;
  visit(node);
  for (const value of Object.values(node)) {
    if (Array.isArray(value)) value.forEach((item) => walk(item, visit));
    else if (value && typeof value === "object") walk(value, visit);
  }
};
for (const file of await readdir(source)) {
  if (
    !file.endsWith(".json") ||
    ["manifest.json", "layers.json"].includes(file)
  )
    continue;
  const snapshot = JSON.parse(await readFile(path.join(source, file), "utf8"));
  if (!snapshot.overview?.rootMetadata) continue;
  const slug = file.slice(0, -5);
  const imageNodes = {};
  const textNodes = {};
  const iconNodes = {};
  const styles = { ...snapshot.overview.rootMetadata.styles };
  snapshot.sections.forEach((section) =>
    Object.assign(styles, section.dsl.styles),
  );
  walk(snapshot, (node) => {
    if (node.url?.startsWith("https://image-resource.mastergo.com/")) {
      if (node.url.endsWith("/undefined")) unavailable.add(node.url);
      else
        urls.set(
          node.url,
          "/design/images/" + new URL(node.url).pathname.split("/").pop(),
        );
    }
    if (node.id && node.fill && styles[node.fill]) {
      const image = styles[node.fill].value?.find((value) => value?.url);
      if (image)
        imageNodes[node.id] =
          "/design/images/" + new URL(image.url).pathname.split("/").pop();
    }
    if (node.type === "TEXT")
      textNodes[node.id] = node.text?.map((t) => t.text).join("") ?? "";
  });
  const html = await readFile(path.join(source, slug + ".html"), "utf8");
  const regex =
    /<div data-node-id="([^"]+)"[^>]*>(<svg[\s\S]*?<\/svg>)<\/div>/g;
  for (const match of html.matchAll(regex)) {
    const filename =
      slug + "-" + match[1].replace(/[^a-zA-Z0-9-]/g, "-") + ".svg";
    await writeFile(path.join(assets, "icons", filename), match[2]);
    iconNodes[match[1]] = "/design/icons/" + filename;
  }
  screens[slug] = {
    layerId: snapshot.layerId,
    name: snapshot.overview.rootMetadata.name,
    width: snapshot.overview.rootMetadata.width,
    height: snapshot.overview.rootMetadata.height,
    images: imageNodes,
    icons: iconNodes,
    texts: textNodes,
  };
}
const pending = [...urls.entries()];
let next = 0;
const failures = [];
await Promise.all(
  Array.from({ length: 4 }, async () => {
    while (next < pending.length) {
      const [url, local] = pending[next++];
      const target = path.join(root, "public", local);
      try {
        if ((await readFile(target)).length) continue;
      } catch {}
      try {
        const response = await fetch(url, {
          signal: AbortSignal.timeout(60000),
        });
        if (!response.ok) throw new Error(String(response.status));
        await writeFile(target, Buffer.from(await response.arrayBuffer()));
      } catch (error) {
        failures.push({ url, error: String(error) });
      }
    }
  }),
);
await writeFile(
  path.join(root, "src/mobile/design-assets.json"),
  JSON.stringify(screens, null, 2),
);
await writeFile(
  path.join(source, "asset-manifest.json"),
  JSON.stringify(
    {
      images: Object.fromEntries(urls),
      unavailable: [...unavailable],
      failures,
    },
    null,
    2,
  ),
);
console.log(
  JSON.stringify({
    screens: Object.keys(screens).length,
    images: urls.size,
    icons: Object.values(screens).reduce(
      (n, s) => n + Object.keys(s.icons).length,
      0,
    ),
    failures,
  }),
);
if (failures.length) process.exitCode = 1;
