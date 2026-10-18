import fs from 'node:fs/promises';

// Temporary fix for https://github.com/ionic-team/capacitor/issues/8530.
// SystemBars requests insets again onPageCommitVisible, when the document exists.
const target = new URL('../node_modules/@capacitor/android/capacitor/src/main/java/com/getcapacitor/plugin/SystemBars.java', import.meta.url);
const source = (await fs.readFile(target, 'utf8')).replace(/\r\n/g, '\n');
const original = `                    try {
                      document.documentElement.style.setProperty("--safe-area-inset-top", "%dpx");
                      document.documentElement.style.setProperty("--safe-area-inset-right", "%dpx");
                      document.documentElement.style.setProperty("--safe-area-inset-bottom", "%dpx");
                      document.documentElement.style.setProperty("--safe-area-inset-left", "%dpx");
                    } catch(e) { console.error('Error injecting safe area CSS:', e); }`;
const guarded = `                    try {
                      const root = document.documentElement;
                      if (root) {
                        root.style.setProperty("--safe-area-inset-top", "%dpx");
                        root.style.setProperty("--safe-area-inset-right", "%dpx");
                        root.style.setProperty("--safe-area-inset-bottom", "%dpx");
                        root.style.setProperty("--safe-area-inset-left", "%dpx");
                      }
                    } catch(e) { console.error('Error injecting safe area CSS:', e); }`;
if (source.includes(guarded)) {
  console.log('Capacitor safe-area startup guard already applied.');
} else {
  if (!source.includes(original) || source.indexOf(original) !== source.lastIndexOf(original))
    throw new Error('SystemBars source changed; review the temporary safe-area fix before building.');
  await fs.writeFile(target, source.replace(original, guarded), 'utf8');
  console.log('Applied Capacitor safe-area startup guard.');
}
