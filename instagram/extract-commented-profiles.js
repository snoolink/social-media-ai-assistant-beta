(async () => {
  // ─── CONFIG ───────────────────────────────────────────────────────────────
  const SCROLL_DELAY_MS   = 1500;
  const MAX_NO_NEW_ROUNDS = 8;
  // ──────────────────────────────────────────────────────────────────────────

  const usernames = new Set();
  let noNewCount  = 0;
  const sleep = ms => new Promise(r => setTimeout(r, ms));

  /* ── Harvest using the exact Instagram username span class ── */
  function harvest() {
    let found = 0;
    // Target the specific span class Instagram uses for usernames in comments
    document.querySelectorAll('span._ap3a._aaco._aacw._aacx._aad7._aade').forEach(span => {
      const name = span.textContent.trim();
      if (name && !usernames.has(name)) {
        usernames.add(name);
        found++;
      }
    });
    return found;
  }

  /* ── Find scroll container: the div wrapping all comments ── */
  function getScrollTarget() {
    // Look for the outer comments list container — has significant scroll height
    const candidates = [...document.querySelectorAll('div')].filter(el => {
      const style = window.getComputedStyle(el);
      const oy = style.overflowY;
      return (oy === 'scroll' || oy === 'auto')
        && el.scrollHeight > el.clientHeight + 100
        && el.clientHeight > 200;
    });

    if (!candidates.length) return null;

    // The comments scroll container is typically the one with the most children
    candidates.sort((a, b) => b.children.length - a.children.length);

    // Also try to prefer the one closest to the comments DOM path
    const inner = document.querySelector('div.x5yr21d.xw2csxc.x1odjw0f.x1n2onr6');
    if (inner) {
      let el = inner.parentElement;
      while (el && el !== document.body) {
        const s = window.getComputedStyle(el);
        if ((s.overflowY === 'scroll' || s.overflowY === 'auto') && el.scrollHeight > el.clientHeight + 100) {
          return el;
        }
        el = el.parentElement;
      }
    }

    return candidates[0];
  }

  /* ── Status overlay ── */
  document.getElementById('__ig_scraper__')?.remove();
  const box = Object.assign(document.createElement('div'), {
    id: '__ig_scraper__',
    style: `position:fixed;bottom:16px;right:16px;z-index:99999;
            background:#111c;color:#fff;font:13px/1.5 monospace;
            padding:10px 14px;border-radius:8px;pointer-events:none;
            backdrop-filter:blur(6px);border:1px solid #ffffff22;max-width:300px`
  });
  document.body.appendChild(box);
  const log = msg => { box.textContent = msg; console.log('[IG Scraper]', msg); };

  await sleep(500);
  const target = getScrollTarget();

  if (!target) {
    log('❌ No scroll container found. Make sure comments panel is open.');
    return;
  }

  // Flash red border to confirm correct container
  const orig = target.style.outline;
  target.style.outline = '3px solid red';
  log(`✓ Container found — ${target.clientHeight}px tall, ${target.scrollHeight}px scrollable`);
  await sleep(1200);
  target.style.outline = orig;

  harvest();
  log(`Starting — ${usernames.size} found so far`);

  /* ── Main loop ── */
  while (noNewCount < MAX_NO_NEW_ROUNDS) {
    target.scrollTop += target.clientHeight * 0.8;
    target.dispatchEvent(new WheelEvent('wheel', { deltaY: 800, bubbles: true }));

    await sleep(SCROLL_DELAY_MS);

    const fresh = harvest();
    const atBottom = target.scrollTop + target.clientHeight >= target.scrollHeight - 30;

    if (fresh === 0) {
      noNewCount++;
      if (atBottom) { log(`Reached bottom!`); break; }
    } else {
      noNewCount = 0;
    }

    log(`${usernames.size} usernames · ${noNewCount}/${MAX_NO_NEW_ROUNDS} empty · pos: ${Math.round(target.scrollTop)}px`);
  }

  /* ── Export CSV ── */
  const csv = 'username,profile_url\n'
    + [...usernames].map(u => `${u},https://www.instagram.com/${u}/`).join('\n');
  const blob = new Blob([csv], { type: 'text/csv' });
  const a = Object.assign(document.createElement('a'), {
    href: URL.createObjectURL(blob),
    download: 'instagram_commenters.csv'
  });
  document.body.appendChild(a);
  a.click();
  a.remove();

  box.style.background = '#1a3a1a';
  log(`✅ Done! ${usernames.size} unique usernames saved.`);
  setTimeout(() => box.remove(), 6000);
  return [...usernames];
})();