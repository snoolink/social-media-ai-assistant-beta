// =============================================================================
// LinkedIn Connection Bot — Browser Console Script
// Paste into DevTools Console on any LinkedIn page and press Enter.
// =============================================================================

(async () => {

// =============================================================================
// CONFIG — edit these before running
// =============================================================================
const NOTE_TEMPLATE = `Hi {name},

I saw you're hiring for data roles at {about} and wanted to reach out.

I'm a Data Engineer with 5 years of experience building scalable data pipelines across cloud and modern data stacks.

I'm currently exploring new opportunities and would love to learn more about the roles you're hiring for.

-Jay`;

// List of LinkedIn profile URLs to process.
// Alternatively, set PROFILE_URLS = null and paste your CSV data into CSV_DATA below.
const PROFILE_URLS = [
  // "https://www.linkedin.com/in/example1/",
  // "https://www.linkedin.com/in/example2/",
];

// Paste raw CSV text here if not using PROFILE_URLS.
// Must have a "profile_url" column. Optional columns: name, about, headline,
// current_position, current_company, location, connections.
// Example:
// const CSV_DATA = `profile_url,name,about,current_position,current_company
// https://www.linkedin.com/in/someone/,Jane Doe,AI startup,CTO,Acme Inc`;
const CSV_DATA = null;

const MAX_REQUESTS       = 200;   // max connections to send this run
const DELAY_MIN_MS       = 5000;  // min delay between profiles (ms)
const DELAY_MAX_MS       = 10000; // max delay between profiles (ms)
const LONG_BREAK_EVERY   = 5;     // take a longer break every N requests
const LONG_BREAK_MIN_MS  = 30000;
const LONG_BREAK_MAX_MS  = 60000;
// =============================================================================

// ---------- Utilities --------------------------------------------------------

const sleep = ms => new Promise(r => setTimeout(r, ms));
const rand  = (min, max) => Math.random() * (max - min) + min;
const delay = (min = DELAY_MIN_MS, max = DELAY_MAX_MS) => sleep(rand(min, max));

function log(msg, ...args) {
  console.log(`%c[LI-Bot] ${msg}`, 'color:#0a66c2;font-weight:bold', ...args);
}

function parseCSV(text) {
  const lines  = text.trim().split('\n');
  const headers = lines[0].split(',').map(h => h.trim().replace(/^"|"$/g, ''));
  return lines.slice(1).map(line => {
    // Handle quoted fields with commas inside
    const values = [];
    let cur = '', inQuote = false;
    for (const ch of line) {
      if (ch === '"') { inQuote = !inQuote; continue; }
      if (ch === ',' && !inQuote) { values.push(cur.trim()); cur = ''; continue; }
      cur += ch;
    }
    values.push(cur.trim());
    return Object.fromEntries(headers.map((h, i) => [h, values[i] ?? '']));
  });
}

function buildProfiles() {
  if (CSV_DATA) return parseCSV(CSV_DATA);
  return (PROFILE_URLS || []).map(url => ({ profile_url: url }));
}

function personalizeNote(template, data) {
  const fullName = data.name || 'there';
  const name     = fullName.split(' ')[0] || 'there';

  let aboutFull = data.about || '';
  if (!aboutFull) {
    if (data.current_position && data.current_company)
      aboutFull = `${data.current_position} at ${data.current_company}`;
    else if (data.headline) aboutFull = data.headline;
    else aboutFull = 'your professional journey';
  }
  const aboutWords = aboutFull.trim().split(/\s+/);
  const about = aboutWords.slice(0, 2).join(' ');

  let note = template
    .replace(/{name}/g,             name)
    .replace(/{about}/g,            about)
    .replace(/{headline}/g,         data.headline          || '')
    .replace(/{current_position}/g, data.current_position  || '')
    .replace(/{current_company}/g,  data.current_company   || '')
    .replace(/{location}/g,         data.location          || '')
    .replace(/{connections}/g,      data.connections       || '');

  if (note.length > 300) note = note.slice(0, 297) + '...';
  return note;
}

// ---------- DOM helpers ------------------------------------------------------

function isInSidebar(el) {
  let node = el;
  for (let i = 0; i < 12; i++) {
    if (!node) return false;
    if (node.tagName === 'ASIDE') return true;
    const cls = (node.className || '').toLowerCase();
    if (cls.includes('aside') || cls.includes('scaffold-layout__aside')) return true;
    node = node.parentElement;
  }
  return false;
}

function isVisible(el) {
  if (!el) return false;
  const rect = el.getBoundingClientRect();
  return rect.width > 0 && rect.height > 0 &&
    window.getComputedStyle(el).visibility !== 'hidden' &&
    window.getComputedStyle(el).display !== 'none';
}

/** Wait for a selector to appear (and optionally be visible), up to timeoutMs. */
function waitFor(selector, { root = document, timeout = 8000, visible = true } = {}) {
  return new Promise((resolve, reject) => {
    const existing = root.querySelector(selector);
    if (existing && (!visible || isVisible(existing))) return resolve(existing);

    const observer = new MutationObserver(() => {
      const el = root.querySelector(selector);
      if (el && (!visible || isVisible(el))) {
        observer.disconnect();
        resolve(el);
      }
    });
    observer.observe(root, { childList: true, subtree: true, attributes: true });
    setTimeout(() => { observer.disconnect(); reject(new Error(`Timeout waiting for: ${selector}`)); }, timeout);
  });
}

/** Click an element via a real MouseEvent (more natural than .click()). */
function realClick(el) {
  el.dispatchEvent(new MouseEvent('mousedown', { bubbles: true, cancelable: true }));
  el.dispatchEvent(new MouseEvent('mouseup',   { bubbles: true, cancelable: true }));
  el.dispatchEvent(new MouseEvent('click',     { bubbles: true, cancelable: true }));
}

/** Type into an input/textarea naturally, firing input + change events. */
function typeInto(el, text) {
  el.focus();
  el.value = '';
  // Use execCommand so React/Vue state picks up the change
  document.execCommand('selectAll', false, null);
  document.execCommand('delete',    false, null);
  document.execCommand('insertText', false, text);
  el.dispatchEvent(new Event('input',  { bubbles: true }));
  el.dispatchEvent(new Event('change', { bubbles: true }));
}

// ---------- Connect button detection -----------------------------------------

function findConnectButtonDirect() {
  // Strategy 1 & 2: co-locate with the Message button or More actions button,
  // walk up parent levels, then search within that container.
  const siblingSelectors = [
    'button[aria-label*="Message"]',
    'button[aria-label="More actions"]',
  ];

  for (const sel of siblingSelectors) {
    const siblings = [...document.querySelectorAll(sel)];
    for (const sibling of siblings) {
      if (!isVisible(sibling) || isInSidebar(sibling)) continue;
      let container = sibling.parentElement;
      for (let depth = 0; depth < 3; depth++) {
        if (!container) break;
        // Look for a button whose aria-label contains "to connect"
        const byLabel = [...container.querySelectorAll('button')].find(b =>
          (b.getAttribute('aria-label') || '').toLowerCase().includes('to connect') &&
          isVisible(b) && !isInSidebar(b)
        );
        if (byLabel) return byLabel;
        // Look for a button whose visible span text is exactly "Connect"
        const byText = [...container.querySelectorAll('button')].find(b =>
          [...b.querySelectorAll('span')].some(s => s.textContent.trim() === 'Connect') &&
          isVisible(b) && !isInSidebar(b)
        );
        if (byText) return byText;
        container = container.parentElement;
      }
    }
  }

  // Strategy 3: global aria-label scan
  const byLabel = [...document.querySelectorAll('button')].find(b =>
    (b.getAttribute('aria-label') || '').toLowerCase().includes('to connect') &&
    isVisible(b) && !isInSidebar(b)
  );
  if (byLabel) return byLabel;

  // Strategy 4: global span-text scan
  const byText = [...document.querySelectorAll('button')].find(b =>
    [...b.querySelectorAll('span')].some(s => s.textContent.trim() === 'Connect') &&
    isVisible(b) && !isInSidebar(b)
  );
  return byText || null;
}

async function findConnectButtonInMoreActions() {
  // Find the More actions trigger (not in sidebar)
  const moreBtn = [...document.querySelectorAll('button[aria-label="More actions"]')]
    .find(b => isVisible(b) && !isInSidebar(b));

  if (!moreBtn) return null;

  moreBtn.scrollIntoView({ block: 'center' });
  await sleep(400);
  realClick(moreBtn);
  await sleep(1500);

  // Items inside the dropdown are <div role="button"> inside <li> elements.
  // Match by aria-label "to connect" or span text "Connect".
  const dropdownItem =
    // role=button with "to connect" in aria-label
    [...document.querySelectorAll('[role="button"]')].find(el =>
      (el.getAttribute('aria-label') || '').toLowerCase().includes('to connect') && isVisible(el)
    ) ||
    // role=button or artdeco-dropdown__item containing a "Connect" span
    [...document.querySelectorAll('.artdeco-dropdown__item, [role="button"], li')].find(el =>
      [...el.querySelectorAll('span')].some(s => s.textContent.trim() === 'Connect') && isVisible(el)
    );

  if (dropdownItem) return dropdownItem;

  // Close the dropdown if nothing found
  document.body.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true }));
  return null;
}

async function discoverConnectButton() {
  // Wait for main profile content to load
  await waitFor('main', { timeout: 10000 }).catch(() => {});
  await sleep(2000);

  return findConnectButtonDirect() || await findConnectButtonInMoreActions();
}

// ---------- Send button ------------------------------------------------------

async function clickSendButton() {
  // Primary: exact aria-label
  try {
    const btn = await waitFor('button[aria-label="Send invitation"]', { timeout: 8000 });
    realClick(btn);
    await delay(3000, 5000);
    return 'success';
  } catch (_) {}

  // Fallback: scan all visible buttons
  const sendBtn = [...document.querySelectorAll('button')].find(b => {
    if (!isVisible(b)) return false;
    const label = (b.getAttribute('aria-label') || '').trim().toLowerCase();
    const text  = b.textContent.trim().toLowerCase();
    return ['send', 'send now', 'send invitation'].includes(text) ||
           ['send', 'send now', 'send invitation'].includes(label) ||
           (text.includes('send') && !text.includes('message'));
  });

  if (sendBtn) {
    realClick(sendBtn);
    await delay(3000, 5000);
    return 'success';
  }

  return 'failed';
}

// ---------- Note handling ----------------------------------------------------

async function addNote(note) {
  // Try "Add a note" button
  const addNoteBtn = document.querySelector('button[aria-label="Add a note"]') ||
    [...document.querySelectorAll('button')].find(b =>
      b.textContent.trim().toLowerCase() === 'add a note' && isVisible(b)
    );

  if (addNoteBtn) {
    realClick(addNoteBtn);
    await sleep(rand(800, 1200));
  }

  // Find textarea
  try {
    const textarea = await waitFor('textarea', { timeout: 6000 });
    typeInto(textarea, note);
    await sleep(rand(800, 1200));
    return true;
  } catch (_) {
    return false; // proceed without note
  }
}

// ---------- Core send flow ---------------------------------------------------

async function sendConnectionRequest(profileUrl, note) {
  log(`Visiting: ${profileUrl}`);
  window.location.href = profileUrl;

  // Wait for navigation to complete
  await new Promise(resolve => {
    const check = setInterval(() => {
      if (document.readyState === 'complete' && window.location.href.includes(profileUrl.split('linkedin.com')[1])) {
        clearInterval(check);
        resolve();
      }
    }, 300);
    setTimeout(() => { clearInterval(check); resolve(); }, 15000);
  });

  await delay(3000, 5000);

  const connectEl = await discoverConnectButton();
  if (!connectEl) {
    log(`Connect button not found for: ${profileUrl}`);
    return 'connect_not_found';
  }

  // Check if it's an <a> with a custom-invite href
  const href = connectEl.getAttribute('href') || '';
  connectEl.scrollIntoView({ block: 'center' });
  await sleep(400);

  if (connectEl.tagName === 'A' && href.includes('/preload/custom-invite/')) {
    window.location.href = href;
    await sleep(3000);
  } else {
    realClick(connectEl);
    await sleep(rand(2000, 3000));
  }

  const currentUrl = window.location.href;
  const onInvitePage = currentUrl.includes('custom-invite') || currentUrl.includes('preload');

  if (onInvitePage) {
    // Dedicated invite page flow
    if (note) await addNote(note);
    return await clickSendButton();
  } else {
    // Modal flow — check if a dialog appeared
    const modal = document.querySelector('[role="dialog"], [aria-modal="true"]');
    if (!modal) {
      // No modal, no invite page — may have sent directly
      return 'success';
    }
    if (note) await addNote(note);
    return await clickSendButton();
  }
}

// ---------- Results storage --------------------------------------------------

const STORAGE_KEY = 'li_bot_results';

function loadResults() {
  try { return JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}'); } catch { return {}; }
}

function saveResult(profileUrl, status, note) {
  const results = loadResults();
  results[profileUrl] = {
    status,
    note,
    date: new Date().toISOString(),
  };
  localStorage.setItem(STORAGE_KEY, JSON.stringify(results));
}

function printSummary(results) {
  const all = Object.values(results);
  const success        = all.filter(r => r.status === 'success').length;
  const notFound       = all.filter(r => r.status === 'connect_not_found').length;
  const failed         = all.filter(r => r.status === 'failed').length;
  log(`SUMMARY — Success: ${success} | Not found: ${notFound} | Failed: ${failed} | Total: ${all.length}`);
  console.table(
    Object.fromEntries(Object.entries(results).map(([url, v]) => [url, { status: v.status, date: v.date }]))
  );
}

// Export results as CSV — call window.liBotExportCSV() in the console anytime.
window.liBotExportCSV = function () {
  const results = loadResults();
  const rows = [['profile_url', 'status', 'date', 'note']];
  for (const [url, v] of Object.entries(results)) {
    rows.push([url, v.status, v.date, (v.note || '').replace(/"/g, '""')]);
  }
  const csv  = rows.map(r => r.map(c => `"${c}"`).join(',')).join('\n');
  const blob = new Blob([csv], { type: 'text/csv' });
  const a    = Object.assign(document.createElement('a'), { href: URL.createObjectURL(blob), download: 'li_bot_results.csv' });
  a.click();
  log('CSV exported!');
};

// ---------- Main loop --------------------------------------------------------

async function run() {
  const profiles    = buildProfiles();
  const results     = loadResults();

  if (!profiles.length) {
    log('No profiles to process. Set PROFILE_URLS or CSV_DATA at the top of the script.');
    return;
  }

  // Skip already-processed profiles
  const unprocessed = profiles.filter(p => !results[p.profile_url]);
  log(`Total: ${profiles.length} | Already done: ${profiles.length - unprocessed.length} | Remaining: ${unprocessed.length}`);

  if (!unprocessed.length) {
    log('All profiles already processed!');
    printSummary(results);
    return;
  }

  let sent = 0;

  for (const profile of unprocessed) {
    if (sent >= MAX_REQUESTS) break;

    const url  = profile.profile_url;
    const note = personalizeNote(NOTE_TEMPLATE, profile);

    console.log(`\n${'='.repeat(60)}`);
    log(`Profile ${sent + 1}/${Math.min(MAX_REQUESTS, unprocessed.length)} — ${url}`);
    log(`Note preview:\n${note}`);

    const result = await sendConnectionRequest(url, note);
    log(`Result: ${result}`);

    saveResult(url, result, note);
    sent++;

    // Longer break every N requests
    if (sent % LONG_BREAK_EVERY === 0 && sent < unprocessed.length) {
      const breakMs = rand(LONG_BREAK_MIN_MS, LONG_BREAK_MAX_MS);
      log(`Taking a longer break (${Math.round(breakMs / 1000)}s)...`);
      await sleep(breakMs);
    } else if (sent < unprocessed.length) {
      await delay(DELAY_MIN_MS, DELAY_MAX_MS);
    }
  }

  const finalResults = loadResults();
  console.log(`\n${'='.repeat(60)}`);
  printSummary(finalResults);
  log('Done! Call window.liBotExportCSV() to download results as CSV.');
}

run().catch(err => console.error('[LI-Bot] Fatal error:', err));

})();