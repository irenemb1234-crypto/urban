// ==UserScript==
// @name         LinkedIn → urban inbox
// @namespace    https://github.com/irenemb1234-crypto/urban
// @version      1.1.0
// @description  Recoge posts guardados (y del feed) de LinkedIn y los envía a inbox/linkedin_inbox.json del repo urban.
// @match        https://www.linkedin.com/*
// @grant        GM_xmlhttpRequest
// @grant        GM_getValue
// @grant        GM_setValue
// @grant        GM_registerMenuCommand
// @connect      api.github.com
// @run-at       document-idle
// ==/UserScript==

(function () {
  'use strict';

  const REPO = 'irenemb1234-crypto/urban';
  const BRANCH = 'main';
  const INBOX_PATH = 'inbox/linkedin_inbox.json';
  const MAX_ROUNDS = 60;
  const MAX_TEXT = 500; // solo lo necesario para clasificar: el repo es público
  const ACTIVITY_RE = /urn:li:(activity|ugcPost|share):(\d{15,25})/;

  GM_registerMenuCommand('Cambiar token de GitHub', () => {
    const t = prompt('Token de GitHub (fine-grained, solo repo urban, Contents: Read and write):');
    if (t) GM_setValue('gh_token', t.trim());
  });

  function getToken() {
    let t = GM_getValue('gh_token', '');
    if (!t) {
      t = (prompt('Token de GitHub (fine-grained, solo repo urban, Contents: Read and write):') || '').trim();
      if (t) GM_setValue('gh_token', t);
    }
    return t;
  }

  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  const clean = (s) => (s || '').replace(/\s+/g, ' ').replace(/…\s*(ver más|see more|more)\s*$/i, '').trim();

  function containers() {
    const found = new Map();
    const nodes = document.querySelectorAll(
      '[data-chameleon-result-urn], [data-urn], [data-id], a[href*="urn:li:activity:"], a[href*="urn:li:ugcPost:"]'
    );
    for (const n of nodes) {
      const raw = n.getAttribute('data-chameleon-result-urn') || n.getAttribute('data-urn') ||
        n.getAttribute('data-id') || n.getAttribute('href') || '';
      const m = raw.match(ACTIVITY_RE);
      if (!m) continue;
      const box = n.closest('li, div.feed-shared-update-v2, div[data-urn], div[data-id]') || n;
      // La URL debe conservar el tipo de URN: un ID de ugcPost no es un ID de activity.
      if (!found.has(m[2])) found.set(m[2], { urn: m[0], box });
    }
    return found;
  }

  function extract(id, urn, box) {
    const authorLink = box.querySelector('a[href*="/in/"], a[href*="/company/"]');
    const authorName =
      box.querySelector('.entity-result__title-text span[aria-hidden="true"], .update-components-actor__title span[aria-hidden="true"]') ||
      authorLink;
    const headline = box.querySelector('.entity-result__primary-subtitle, .update-components-actor__description span[aria-hidden="true"]');
    const textEl = box.querySelector('.entity-result__content-summary, .update-components-text, .feed-shared-inline-show-more-text');
    const time = box.querySelector('.entity-result__simple-insight-text, .update-components-actor__sub-description span[aria-hidden="true"]');
    const links = [...box.querySelectorAll('a[href]')]
      .map((a) => a.href)
      .filter((h) => !/linkedin\.com\/(in|company|feed\/hashtag|search)/.test(h) && !h.startsWith('javascript'));
    return {
      id,
      url: `https://www.linkedin.com/feed/update/${urn}`,
      autor: clean(authorName && authorName.innerText),
      titular: clean(headline && headline.innerText),
      perfil: authorLink ? authorLink.href.split('?')[0] : '',
      texto: clean(textEl ? textEl.innerText : box.innerText).slice(0, MAX_TEXT),
      enlaces: [...new Set(links)].slice(0, 10),
      publicado_hace: clean(time && time.innerText),
      origen: location.pathname.includes('saved-posts') ? 'guardados' : 'feed',
      capturado: new Date().toISOString(),
    };
  }

  async function expandAll(status) {
    let last = -1, stable = 0;
    for (let i = 0; i < MAX_ROUNDS && stable < 3; i++) {
      window.scrollTo(0, document.body.scrollHeight);
      const more = [...document.querySelectorAll('button')].find((b) =>
        /show more results|ver más resultados|mostrar más resultados|load more/i.test(b.innerText));
      if (more) more.click();
      await sleep(1800);
      const n = containers().size;
      status(`Cargando… ${n} posts`);
      stable = n === last ? stable + 1 : 0;
      last = n;
    }
    for (const b of document.querySelectorAll('button')) {
      if (/^\s*(…\s*)?(ver más|see more|more)\s*$/i.test(b.innerText)) b.click();
    }
    await sleep(500);
  }

  function gh(method, path, body) {
    return new Promise((resolve, reject) => {
      GM_xmlhttpRequest({
        method,
        url: `https://api.github.com/repos/${REPO}/contents/${path}` + (method === 'GET' ? `?ref=${BRANCH}` : ''),
        headers: {
          Authorization: `Bearer ${getToken()}`,
          Accept: 'application/vnd.github+json',
          'Content-Type': 'application/json',
        },
        data: body ? JSON.stringify(body) : undefined,
        onload: (r) => resolve({ status: r.status, json: (() => { try { return JSON.parse(r.responseText); } catch { return {}; } })() }),
        onerror: reject,
      });
    });
  }

  const b64encode = (s) => {
    const bytes = new TextEncoder().encode(s);
    let bin = '';
    for (let i = 0; i < bytes.length; i += 0x8000) bin += String.fromCharCode(...bytes.subarray(i, i + 0x8000));
    return btoa(bin);
  };
  const b64decode = (s) => new TextDecoder().decode(Uint8Array.from(atob(s.replace(/\n/g, '')), (c) => c.charCodeAt(0)));

  async function push(posts) {
    for (let attempt = 0; attempt < 3; attempt++) {
      const cur = await gh('GET', INBOX_PATH);
      if (cur.status === 401 || cur.status === 403) throw new Error('Token de GitHub no válido o sin permisos');
      const existing = cur.status === 200 ? JSON.parse(b64decode(cur.json.content)) : [];
      const known = new Set(existing.map((p) => p.id));
      const fresh = posts.filter((p) => !known.has(p.id));
      if (!fresh.length) return 0;
      const res = await gh('PUT', INBOX_PATH, {
        message: `inbox: ${fresh.length} posts de LinkedIn`,
        content: b64encode(JSON.stringify(existing.concat(fresh), null, 2) + '\n'),
        branch: BRANCH,
        ...(cur.status === 200 ? { sha: cur.json.sha } : {}),
      });
      if (res.status === 200 || res.status === 201) return fresh.length;
      if (res.status !== 409) throw new Error(`GitHub respondió ${res.status}: ${res.json.message || ''}`);
    }
    throw new Error('Conflicto al escribir en GitHub, inténtalo de nuevo');
  }

  function addButton() {
    if (document.getElementById('urban-inbox-btn')) return;
    const btn = document.createElement('button');
    btn.id = 'urban-inbox-btn';
    btn.textContent = 'Enviar a urban';
    Object.assign(btn.style, {
      position: 'fixed', bottom: '20px', right: '20px', zIndex: 99999, padding: '10px 16px',
      background: '#0a66c2', color: '#fff', border: 'none', borderRadius: '20px',
      font: '600 14px system-ui, sans-serif', cursor: 'pointer', boxShadow: '0 2px 8px rgba(0,0,0,.3)',
    });
    const status = (t) => { btn.textContent = t; };
    btn.onclick = async () => {
      if (!getToken()) return;
      btn.disabled = true;
      try {
        await expandAll(status);
        const posts = [...containers()].map(([id, { urn, box }]) => extract(id, urn, box));
        status(`Enviando ${posts.length}…`);
        const n = await push(posts);
        status(`✓ ${n} nuevos enviados (${posts.length} vistos)`);
      } catch (e) {
        status('Error: ' + e.message);
      } finally {
        btn.disabled = false;
        setTimeout(() => status('Enviar a urban'), 8000);
      }
    };
    document.body.appendChild(btn);
  }

  addButton();
  new MutationObserver(addButton).observe(document.body, { childList: true });
})();
