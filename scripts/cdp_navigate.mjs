const hash = process.argv[2] || '#/';

async function main() {
  const pages = await fetch('http://127.0.0.1:9222/json').then(r => r.json());
  if (!pages || !pages.length) {
    console.error('No devtools pages found');
    process.exit(1);
  }
  const wsUrl = pages[0].webSocketDebuggerUrl;
  const ws = new WebSocket(wsUrl);

  ws.onopen = () => {
    ws.send(JSON.stringify({
      id: 1,
      method: 'Runtime.evaluate',
      params: { expression: `window.location.hash = '${hash}'` }
    }));
  };

  ws.onmessage = (event) => {
    console.log('CDP response:', event.data);
    setTimeout(() => process.exit(0), 300);
  };
}

main().catch(err => {
  console.error(err);
  process.exit(1);
});
