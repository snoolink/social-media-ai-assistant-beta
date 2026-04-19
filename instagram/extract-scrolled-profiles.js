(function () {
  const DURATION_MS = 60_000; // 1 minute window
  const usernames = new Set();
  let running = true;

  /* ── Harvest usernames using Instagram's exact span class ── */
  function harvest() {
    document.querySelectorAll('span._ap3a._aaco._aacw._aacx._aad7._aade').forEach(span => {
      const name = span.textContent.trim();
      if (name) usernames.add(name);
    });
  }

  /* ── Status overlay ── */
  document.getElementById('__ig_scraper__')?.remove();
  const box = Object.assign(document.createElement('div'), {
    id: '__ig_scraper__',
    style: `
      position: fixed;
      bottom: 16px;
      right: 16px;
      z-index: 99999;
      background: #111c;
      color: #fff;
      font: 13px/1.6 monospace;
      padding: 12px 16px;
      border-radius: 10px;
      pointer-events: none;
      backdrop-filter: blur(8px);
      border: 1px solid #ffffff33;
      min-width: 220px;
      box-shadow: 0 4px 20px rgba(0,0,0,0.4);
    `
  });
  document.body.appendChild(box);

  /* ── Timer & harvest loop ── */
  const startTime = Date.now();
  const interval = setInterval(() => {
    if (!running) return;

    harvest();

    const elapsed = Date.now() - startTime;
    const remaining = Math.max(0, DURATION_MS - elapsed);
    const secs = Math.ceil(remaining / 1000);

    if (remaining <= 0) {
      clearInterval(interval);
      running = false;
      harvest(); // final harvest
      finish();
      return;
    }

    // Progress bar
    const pct = Math.round(((DURATION_MS - remaining) / DURATION_MS) * 100);
    const filled = Math.round(pct / 5); // 20 chars wide
    const bar = '█'.repeat(filled) + '░'.repeat(20 - filled);

    box.innerHTML = `
      <div style="color:#aaa;font-size:11px;margin-bottom:4px">📋 IG Comment Scraper</div>
      <div style="color:#4fc3f7">Scroll through comments now!</div>
      <div style="margin:6px 0;color:#fff">${bar} ${pct}%</div>
      <div>⏱ <b style="color:#ffeb3b">${secs}s</b> remaining</div>
      <div>👥 <b style="color:#a5d6a7">${usernames.size}</b> usernames collected</div>
    `;
  }, 500);

  /* ── Also harvest on scroll events ── */
  document.addEventListener('scroll', harvest, true);

  /* ── Finish: export CSV ── */
  function finish() {
    document.removeEventListener('scroll', harvest, true);

    if (usernames.size === 0) {
      box.innerHTML = `<div style="color:#ef9a9a">❌ No usernames found.<br>Make sure comments were visible.</div>`;
      setTimeout(() => box.remove(), 5000);
      return;
    }

    // Build CSV
    const csv = 'username,profile_url\n'
      + [...usernames]
          .sort()
          .map(u => `${u},https://www.instagram.com/${u}/`)
          .join('\n');

    const blob = new Blob([csv], { type: 'text/csv' });
    const url  = URL.createObjectURL(blob);
    const a    = Object.assign(document.createElement('a'), {
      href:     url,
      download: `ig_commenters_${new Date().toISOString().slice(0,10)}.csv`
    });
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);

    // Final status
    box.style.background = '#1a3a1acc';
    box.style.border = '1px solid #4caf5066';
    box.innerHTML = `
      <div style="color:#aaa;font-size:11px;margin-bottom:4px">📋 IG Comment Scraper</div>
      <div style="color:#a5d6a7">✅ Done! CSV downloaded.</div>
      <div style="margin-top:4px">👥 <b style="color:#fff">${usernames.size}</b> unique usernames saved</div>
    `;
    setTimeout(() => box.remove(), 6000);

    // Also log to console
    console.log(`[IG Scraper] ${usernames.size} usernames collected:`);
    console.log([...usernames].sort().join('\n'));
  }
})();