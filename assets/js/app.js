/* ============================================================
   全站共享:SVG 图标 / 增量网格渲染(JS masonry)/ 灯箱 / 画廊逻辑
   ============================================================ */
(function () {
  "use strict";

  /* ================= SVG 图标系统(禁 emoji) ================= */
  const svgWrap = (inner, vb = "0 0 24 24") =>
    `<svg class="ico-svg" viewBox="${vb}" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${inner}</svg>`;

  const ICONS = {
    search: '<circle cx="11" cy="11" r="7"/><path d="M21 21l-4.3-4.3"/>',
    heart: '<path d="M12 21C7 16.5 3 13.2 3 9.3 3 6.9 4.9 5 7.3 5c1.7 0 3.2.9 4.7 2.7C13.5 5.9 15 5 16.7 5 19.1 5 21 6.9 21 9.3c0 3.9-4 7.2-9 11.7z"/>',
    copy: '<rect x="9" y="9" width="11" height="11" rx="2"/><path d="M5 15V5a2 2 0 0 1 2-2h10"/>',
    refresh: '<path d="M21 12a9 9 0 1 1-2.6-6.3"/><path d="M21 3v6h-6"/>',
    external: '<path d="M14 5h5v5M19 5l-8 8"/><path d="M19 14v4a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2h4"/>',
    sun: '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/>',
    moon: '<path d="M21 12.8A9 9 0 1 1 11.2 3 7 7 0 0 0 21 12.8z"/>',
    close: '<path d="M18 6L6 18M6 6l12 12"/>',
    left: '<path d="M15 18l-6-6 6-6"/>',
    right: '<path d="M9 6l6 6-6 6"/>',
    image: '<rect x="3" y="5" width="18" height="14" rx="2"/><circle cx="8.5" cy="10" r="1.5"/><path d="M21 15l-5-5-6 6-2-2-5 5"/>',
    sparkles: '<path d="M12 3l1.9 5.1L19 10l-5.1 1.9L12 17l-1.9-5.1L5 10l5.1-1.9z"/><path d="M19 15l.9 2.1L22 18l-2.1.9L19 21l-.9-2.1L16 18l2.1-.9z"/>',
    grid: '<rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/>',
    clock: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    radio: '<circle cx="12" cy="12" r="2"/><path d="M7.8 16.2a6 6 0 0 1 0-8.4M16.2 7.8a6 6 0 0 1 0 8.4M4.9 19.1a10 10 0 0 1 0-14.2M19.1 4.9a10 10 0 0 1 0 14.2"/>',
    send: '<path d="M22 2L11 13"/><path d="M22 2l-7 20-4-9-9-4z"/>',
    brain: '<rect x="4" y="4" width="16" height="16" rx="3"/><path d="M9 9h6M9 12h6M9 15h4"/>',
    /* 分类图标 */
    portrait: '<circle cx="12" cy="9" r="3.2"/><path d="M6.5 19c1.3-2.7 3.2-4 5.5-4s4.2 1.3 5.5 4"/><rect x="3" y="3" width="18" height="18" rx="4"/>',
    photo: '<rect x="3" y="5" width="18" height="14" rx="3"/><circle cx="8.5" cy="10" r="1.5"/><path d="M21 15l-5-5-6 6-2-2-5 5"/>',
    game: '<path d="M6 11h4M8 9v4"/><circle cx="15.5" cy="10.5" r=".6"/><circle cx="17.5" cy="13" r=".6"/><rect x="2" y="6.5" width="20" height="11" rx="5.5"/>',
    brand: '<path d="M12 19l7-7-4-4-7 7-1.5 5.5z"/><path d="M14.5 9.5l2-2a2.83 2.83 0 1 1 4 4l-2 2"/>',
    type: '<path d="M4 7V5h16v2M9 20h6M12 5v15"/>',
    chart: '<path d="M3 3v18h18"/><path d="M7 14l4-4 3 3 5-6"/>',
    shapes: '<rect x="3" y="13" width="8" height="8" rx="1.5"/><circle cx="17.5" cy="17" r="4"/><path d="M12 8.5L15.5 3 19 8.5z"/>',
    palette: '<path d="M12 21a9 9 0 1 1 9-9c0 2-1.5 3-3 3h-2a2 2 0 0 0-2 2c0 1-.8 2-2 2z"/><circle cx="7.5" cy="10.5" r=".7"/><circle cx="12" cy="7.5" r=".7"/><circle cx="16.5" cy="10.5" r=".7"/>',
    box3d: '<path d="M21 8l-9-5-9 5v8l9 5 9-5z"/><path d="M3 8l9 5 9-5M12 13v8"/>',
    poster: '<rect x="4" y="3" width="16" height="18" rx="2.5"/><path d="M8 8h8M8 12h8M8 16h5"/>',
    bag: '<path d="M6 8h12l1 12H5z"/><path d="M9 8a3 3 0 0 1 6 0"/>',
    landmark: '<path d="M3 21h18M5 21v-9M9 21v-9M15 21v-9M19 21v-9M3 10l9-6 9 6"/>',
    monitor: '<rect x="3" y="4" width="18" height="13" rx="2.5"/><path d="M8 21h8M12 17v4"/>',
    city: '<path d="M4 21V8l6-4v17M14 21V3l6 4v14M4 21h16"/><path d="M7.5 10h.01M7.5 14h.01M17 11h.01M17 15h.01"/>',
    film: '<rect x="3" y="5" width="18" height="14" rx="2.5"/><path d="M7 5v14M17 5v14M3 9h4M3 15h4M17 9h4M17 15h4"/>',
  };

  const CAT_ICON_KEYS = {
    "人像写真": "portrait", "摄影写实": "photo", "游戏动漫": "game",
    "Logo品牌": "brand", "文字渲染": "type", "信息图表": "chart",
    "其他": "shapes", "插画艺术": "palette", "3D潮玩": "box3d",
    "海报排版": "poster", "电商产品": "bag", "古风历史": "landmark",
    "UI界面": "monitor", "场景叙事": "city", "视频模板": "film",
  };
  const catIcon = (cat) => svgWrap(ICONS[CAT_ICON_KEYS[cat] || "shapes"]);

  const SOURCE_NAMES = {
    canghe: "苍何画廊", suxian: "水仙", david: "Awesome",
    handbook: "实战手册", xtrend: "X热门", youmind: "YouMind",
    gptimage2: "GPTImage2", inbox: "投喂",
  };
  const PLACEHOLDER =
    "data:image/svg+xml;utf8," +
    encodeURIComponent(
      '<svg xmlns="http://www.w3.org/2000/svg" width="400" height="300"><rect width="100%" height="100%" fill="#eceef3"/><circle cx="200" cy="128" r="42" fill="#d7dce6"/><path d="M150 200l60-55 45 40 25-22 45 37v45a15 15 0 0 1-15 15H165a15 15 0 0 1-15-15z" fill="#c3cad8"/></svg>'
    );

  const esc = (s) =>
    String(s == null ? "" : s)
      .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;").replace(/'/g, "&#39;");

  /** 图片地址:服务器部署(PG_SETTINGS.imgProxy)时走本地缓存代理 /img/?u=… */
  function imgSrc(u) {
    if (!u) return PLACEHOLDER;
    if (window.PG_SETTINGS && window.PG_SETTINGS.imgProxy) {
      return "/img/?u=" + encodeURIComponent(u);
    }
    return u;
  }

  /* ---------- 收藏(localStorage) ---------- */
  const FAV_KEY = "pg_favorites";
  const favStore = {
    all() {
      try { return JSON.parse(localStorage.getItem(FAV_KEY) || "[]"); } catch { return []; }
    },
    has(id) { return this.all().includes(id); },
    toggle(id) {
      const list = this.all();
      const i = list.indexOf(id);
      if (i >= 0) list.splice(i, 1); else list.unshift(id);
      localStorage.setItem(FAV_KEY, JSON.stringify(list.slice(0, 5000)));
      return list.includes(id);
    },
  };

  /* ---------- Toast ---------- */
  let toastTimer = null;
  function toast(msg) {
    let el = document.querySelector(".toast");
    if (!el) {
      el = document.createElement("div");
      el.className = "toast";
      document.body.appendChild(el);
    }
    el.textContent = msg;
    requestAnimationFrame(() => el.classList.add("show"));
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => el.classList.remove("show"), 1800);
  }

  async function copyText(text) {
    try {
      await navigator.clipboard.writeText(text);
      return true;
    } catch {
      const ta = document.createElement("textarea");
      ta.value = text;
      document.body.appendChild(ta);
      ta.select();
      const ok = document.execCommand("copy");
      ta.remove();
      return ok;
    }
  }

  /* ---------- 明暗主题(默认浅色;iOS 风格) ---------- */
  function syncThemeBtn(theme) {
    const btn = document.getElementById("themeToggle");
    if (btn) btn.innerHTML = theme === "light" ? svgWrap(ICONS.moon) : svgWrap(ICONS.sun);
  }
  function initTheme() {
    const saved = localStorage.getItem("pg_theme_v2");
    const theme = saved || "light";
    document.documentElement.dataset.theme = theme;
    syncThemeBtn(theme);
    const btn = document.getElementById("themeToggle");
    if (btn && !btn.dataset.bound) {
      btn.dataset.bound = "1";
      btn.addEventListener("click", () => {
        const cur = document.documentElement.dataset.theme === "light" ? "dark" : "light";
        document.documentElement.dataset.theme = cur;
        localStorage.setItem("pg_theme_v2", cur);
        syncThemeBtn(cur);
      });
    }
  }

  /* ============================================================
     卡片与网格:DOM 节点按 id 复用(杜绝图片重建闪烁)+ JS masonry
     ============================================================ */
  /** 子分类彩色胶囊(水仙式,左上角;颜色由名称哈希决定,同分类恒同色) */
  function subBadgeHTML(sub) {
    if (!sub) return "";
    let h = 0;
    for (let i = 0; i < sub.length; i++) h = (h * 31 + sub.charCodeAt(i)) >>> 0;
    return `<span class="sub-badge" style="--sb-h:${h % 360}">${esc(sub)}</span>`;
  }

  function cardEl(it) {
    const el = document.createElement("article");
    el.className = "card";
    el.dataset.id = it.id;
    const title = it.tz || it.t || "";
    const cat = it.c || "其他";
    const src = SOURCE_NAMES[it.s] || it.s || "";
    const fav = favStore.has(it.id) ? " on" : "";
    el.innerHTML = `
      <div class="thumb">
        <button class="fav-btn${fav}" data-fav="${esc(it.id)}" title="收藏">${svgWrap(ICONS.heart)}</button>
        ${subBadgeHTML(it.sub)}
        ${it.img ? '<img loading="lazy" alt="' + esc(title) + '">' : '<div class="ph">' + svgWrap(ICONS.image) + '</div>'}
      </div>
      <div class="body">
        <h3 class="title" title="${esc(title)}">${esc(title)}</h3>
        <div class="meta">
          <span class="chip cat">${esc(cat)}</span>
          ${it.nr ? '<span class="chip ref">需参考图</span>' : ''}
          <span class="chip src">${esc(src)}</span>
        </div>
      </div>`;
    const img = el.querySelector("img");
    if (img) {
      // 已知宽高比时预留空间,加载完不跳动
      if (it.ar) img.style.aspectRatio = (1 / it.ar).toFixed(4);
      img.addEventListener("load", () => img.classList.add("ok"), { once: true });
      img.addEventListener("error", () => { img.src = PLACEHOLDER; img.classList.add("ok"); }, { once: true });
      img.src = imgSrc(it.img);
    }
    return el;
  }

  const gridMaps = new WeakMap();   // container -> Map(id -> element)
  const activeGrids = new Map();    // container -> {items, onItemClick}(供 resize 重排)
  let resizeTimer = null;

  function masonryPlace(container, map, items) {
    const width = container.clientWidth || container.parentElement.clientWidth || 800;
    const minCol = 236, gap = 16;
    const cols = Math.max(2, Math.min(5, Math.floor((width + gap) / (minCol + gap))));
    // 离线构建列结构,replaceChildren 原子替换——页面高度不塌陷,滚动位置稳定
    const colEls = [];
    const colH = new Array(cols).fill(0);
    const frag = document.createDocumentFragment();
    for (let i = 0; i < cols; i++) {
      const d = document.createElement("div");
      d.className = "m-col";
      frag.appendChild(d);
      colEls.push(d);
    }
    const colW = (width - gap * (cols - 1)) / cols;
    items.forEach((it, idx) => {
      const el = map.get(it.id);
      const estH = colW * (it.ar || 1.28) + 92;   // 有真实宽高比时精确分列
      let target = 0;
      for (let i = 1; i < cols; i++) if (colH[i] < colH[target]) target = i;
      if (idx < cols) target = idx;   // 首行每列保底一张
      colEls[target].appendChild(el);
      colH[target] += estH;
    });
    container.replaceChildren(frag);
  }

  /**
   * 增量网格:按 id 复用节点(图片不重载、不闪烁),JS masonry 布局。
   */
  function renderGrid(container, items, onItemClick) {
    let map = gridMaps.get(container);
    if (!map) { map = new Map(); gridMaps.set(container, map); }

    if (!items.length) {
      container.innerHTML = "";
      map.clear();
      activeGrids.delete(container);
      container.innerHTML = '<div class="empty-tip">没有匹配的提示词,换个关键词试试</div>';
      return;
    }
    const oldTip = container.querySelector(".empty-tip");
    if (oldTip) oldTip.remove();

    const keep = new Set(items.map((i) => i.id));
    for (const [id, el] of [...map]) {
      if (!keep.has(id)) { el.remove(); map.delete(id); }
    }
    const newEls = [];
    for (const it of items) {
      let el = map.get(it.id);
      if (!el) { el = cardEl(it); map.set(it.id, el); newEls.push(el); }
    }
    masonryPlace(container, map, items);

    // 兜底:接进文档后已加载完但未标记的图(碎片树中 src 竞态),立即淡入
    container.querySelectorAll("img:not(.ok)").forEach((img) => {
      if (img.complete) {
        if (!img.naturalWidth) img.src = PLACEHOLDER;
        img.classList.add("ok");
      }
    });

    // 事件委托(每容器绑一次)
    if (!container.dataset.bound) {
      container.dataset.bound = "1";
      container.addEventListener("click", (ev) => {
        const favBtn = ev.target.closest(".fav-btn");
        if (favBtn) {
          const on = favStore.toggle(favBtn.dataset.fav);
          favBtn.classList.toggle("on", on);
          toast(on ? "已收藏" : "已取消收藏");
          ev.stopPropagation();
          return;
        }
        const card = ev.target.closest(".card");
        if (card && container.__onItem) container.__onItem(card.dataset.id);
      });
    }
    container.__onItem = onItemClick || container.__onItem;

    // 新节点入场动效
    newEls.forEach((el) => {
      el.classList.add("reveal");
      requestAnimationFrame(() => requestAnimationFrame(() => el.classList.add("in")));
    });

    activeGrids.set(container, { items, onItemClick });

    if (!resizeTimer) {
      window.addEventListener("resize", () => {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(() => {
          for (const [c, info] of activeGrids) {
            if (c.isConnected) masonryPlace(c, gridMaps.get(c), info.items);
          }
        }, 180);
      }, { passive: true, once: false });
      resizeTimer = 1;
    }
  }

  /* ---------- 灯箱(iOS Sheet) ---------- */
  function ensureLightbox() {
    let lb = document.querySelector(".lightbox");
    if (lb) return lb;
    lb = document.createElement("div");
    lb.className = "lightbox";
    lb.innerHTML = `
      <button class="lb-close" title="关闭">${svgWrap(ICONS.close)}</button>
      <div class="box">
        <div class="lb-handle"></div>
        <div class="img-side"><img alt=""></div>
        <div class="txt-side">
          <h3></h3>
          <div class="lb-meta"></div>
          <div class="prompt-toolbar" style="display:none">
            <button class="fchip on" data-lang="orig">原文</button>
            <button class="fchip" data-lang="zh">中文对照<small>机器翻译</small></button>
          </div>
          <div class="prompt-box"></div>
          <div class="lb-actions">
            <button class="btn" data-act="copy">${svgWrap(ICONS.copy)} 复制当前内容</button>
            <button class="btn secondary" data-act="fav">${svgWrap(ICONS.heart)} 收藏</button>
            <a class="btn secondary" data-act="src" target="_blank" rel="noreferrer" style="display:none">${svgWrap(ICONS.external)} 查看来源</a>
          </div>
        </div>
      </div>`;
    document.body.appendChild(lb);
    lb.addEventListener("click", (ev) => {
      if (ev.target === lb || ev.target.closest(".lb-close")) closeLightbox();
    });
    document.addEventListener("keydown", (ev) => { if (ev.key === "Escape") closeLightbox(); });
    return lb;
  }

  let currentLightboxItem = null;
  let promptLang = "orig";

  function renderLightboxPrompt() {
    const lb = document.querySelector(".lightbox");
    if (!lb || !currentLightboxItem) return;
    const it = currentLightboxItem;
    const text = promptLang === "zh" && it.promptZh ? it.promptZh : it.prompt || "";
    lb.querySelector(".prompt-box").textContent = text;
    lb.querySelectorAll(".prompt-toolbar [data-lang]").forEach((b) =>
      b.classList.toggle("on", b.dataset.lang === promptLang)
    );
  }

  async function openLightbox(id) {
    const lb = ensureLightbox();
    lb.classList.add("open");
    promptLang = "orig";
    lb.querySelector("h3").textContent = "加载中…";
    lb.querySelector(".prompt-box").textContent = "";
    const it = await window.PGData.getItem(id);
    if (!it) { lb.querySelector("h3").textContent = "条目不存在"; return; }
    currentLightboxItem = it;
    lb.querySelector("h3").textContent = it.titleZh || it.title || "";
    lb.querySelector(".img-side img").src = imgSrc(it.image) || PLACEHOLDER;
    lb.querySelector(".lb-meta").innerHTML = `
      <span class="chip cat">${esc(it.category)}</span>
      ${it.sub ? `<span class="chip">${esc(it.sub)}</span>` : ""}
      <span class="chip src">${esc((it.source && it.source.name) || "")}</span>
      ${it.author ? `<span class="chip">${esc(it.author)}</span>` : ""}
      ${it.needsReference ? '<span class="chip ref">需参考图</span>' : ""}`;
    const toolbar = lb.querySelector(".prompt-toolbar");
    toolbar.style.display = it.promptZh ? "flex" : "none";
    renderLightboxPrompt();
    const srcLink = lb.querySelector('[data-act="src"]');
    if (it.source && it.source.url) {
      srcLink.href = it.source.url;
      srcLink.style.display = "inline-flex";
    } else srcLink.style.display = "none";
    const favBtn = lb.querySelector('[data-act="fav"]');
    favBtn.innerHTML = svgWrap(ICONS.heart) + (favStore.has(id) ? " 已收藏" : " 收藏");
  }

  function closeLightbox() {
    const lb = document.querySelector(".lightbox");
    if (lb) lb.classList.remove("open");
    currentLightboxItem = null;
  }

  document.addEventListener("click", async (ev) => {
    const lb = ev.target.closest(".lightbox");
    if (!lb || !currentLightboxItem) return;
    const langBtn = ev.target.closest(".prompt-toolbar [data-lang]");
    if (langBtn) {
      promptLang = langBtn.dataset.lang;
      renderLightboxPrompt();
      return;
    }
    const act = ev.target.closest("[data-act]");
    if (!act) return;
    if (act.dataset.act === "copy") {
      const text =
        promptLang === "zh" && currentLightboxItem.promptZh
          ? currentLightboxItem.promptZh
          : currentLightboxItem.prompt || "";
      const ok = await copyText(text);
      toast(ok ? (promptLang === "zh" ? "中文对照已复制" : "提示词原文已复制") : "复制失败,请手动选择文本");
    } else if (act.dataset.act === "fav") {
      const on = favStore.toggle(currentLightboxItem.id);
      act.innerHTML = svgWrap(ICONS.heart) + (on ? " 已收藏" : " 收藏");
      toast(on ? "已收藏" : "已取消收藏");
    }
  });

  /* ============================================================
     画廊页(含子分类 tab)
     ============================================================ */
  const state = { cat: null, tag: null, src: null, ref: false, q: "", sort: "hot", shown: 0, list: [] };
  const PAGE_SIZE = 60;
  const sliceCache = new Map(); // category -> items(完整字段)

  /** 完整条目 → 卡片索引形状 */
  function toIdx(it) {
    return {
      id: it.id, t: it.title, tz: it.titleZh, c: it.category,
      sub: it.sub,
      s: (it.source && it.source.id) || "", img: it.image,
      nr: it.needsReference, d: it.createdAt, h: it.hot || 0,
    };
  }

  async function getWorkingList() {
    if (!state.cat) {
      const index = await window.PGData.getIndex();
      return { list: index, raw: null };
    }
    if (!sliceCache.has(state.cat)) {
      try {
        const data = await window.PGData.fetchJSON(
          `data/prompts.by-category/${encodeURIComponent(state.cat)}.json`
        );
        sliceCache.set(state.cat, data.items || []);
      } catch {
        sliceCache.set(state.cat, []);
      }
    }
    const rawItems = sliceCache.get(state.cat);
    return { list: rawItems.map(toIdx), raw: rawItems };
  }

  function applyFilters(list) {
    let out = list.slice();
    const q = state.q.trim().toLowerCase();
    // 注意:tag 筛选在 reflow 中基于原始条目完成(toIdx 映射体不含 tags)
    if (state.src) out = out.filter((e) => e.s === state.src);
    if (state.ref) out = out.filter((e) => e.nr);
    if (q) {
      const full = window.__pgFullMap;
      out = out.filter((e) => {
        const item = full && full.get(e.id);
        return `${e.t || ""} ${e.tz || ""} ${item ? item.prompt : ""} ${item && item.promptZh ? item.promptZh : ""}`.toLowerCase().includes(q);
      });
    }
    if (state.sort === "hot") out.sort((a, b) => (b.h || 0) - (a.h || 0));
    else if (state.sort === "new") out.sort((a, b) => (b.d || "").localeCompare(a.d || ""));
    else if (state.sort === "rand") out.sort(() => Math.random() - 0.5);
    return out;
  }

  function renderSubChips(items) {
    const row = document.getElementById("subChips");
    if (!row) return;
    if (!state.cat) { row.style.display = "none"; return; }
    row.style.display = "flex";
    // 从条目 tags 聚合出子分类(多为各源原生细分)
    const counts = {};
    for (const it of items) {
      for (const t of it.tags || []) {
        if (t && t.length <= 14) counts[t] = (counts[t] || 0) + 1;
      }
    }
    const tops = Object.entries(counts).filter(([, n]) => n >= 3).sort((a, b) => b[1] - a[1]).slice(0, 14);
    row.innerHTML =
      `<button class="fchip${state.tag ? "" : " on"}" data-tag="">全部细分</button>` +
      tops.map(([t, n]) =>
        `<button class="fchip${state.tag === t ? " on" : ""}" data-tag="${esc(t)}">${esc(t)}<span class="n">${n}</span></button>`
      ).join("");
  }

  async function initGallery() {
    const grid = document.getElementById("grid");
    const index = await window.PGData.getIndex();
    const stats = await window.PGData.getStats();

    const params = new URLSearchParams(location.search);
    state.cat = params.get("cat");
    state.src = params.get("src");
    state.ref = params.get("ref") === "1";
    state.q = params.get("q") || "";
    state.tag = params.get("tag") || null;
    state.sort = params.get("sort") || "hot";

    renderCatChips();
    renderSrcChips();
    const { raw } = await getWorkingList();
    renderSubChips(raw || []);
    syncControls();
    await reflow();

    // 后台加载全文 → 全文搜索可用
    window.PGData.ensureFull().then((map) => {
      window.__pgFullMap = map;
      if (state.q) reflow();
    });

    function renderCatChips() {
      const row = document.getElementById("catChips");
      const cats = Object.entries(stats.categoryCounts || {}).filter(([, n]) => n > 0)
        .sort((a, b) => b[1] - a[1]);
      row.innerHTML =
        `<button class="fchip${state.cat ? "" : " on"}" data-cat="">全部<span class="n">${index.length}</span></button>` +
        cats.map(([c, n]) =>
          `<button class="fchip${state.cat === c ? " on" : ""}" data-cat="${esc(c)}">${esc(c)}<span class="n">${n}</span></button>`
        ).join("");
      row.addEventListener("click", async (ev) => {
        const btn = ev.target.closest("[data-cat]");
        if (!btn) return;
        state.cat = btn.dataset.cat || null;
        state.tag = null;
        state.shown = 0;
        const { raw } = await getWorkingList();
        renderSubChips(raw || []);
        syncControls(); reflow(); syncUrl();
      });
    }

    function renderSrcChips() {
      const row = document.getElementById("srcChips");
      const sources = Object.entries(stats.perSource || {}).filter(([, n]) => n > 0)
        .sort((a, b) => b[1] - a[1]);
      row.innerHTML =
        `<button class="fchip${state.src ? "" : " on"}" data-src="">全部来源</button>` +
        sources.map(([s, n]) =>
          `<button class="fchip${state.src === s ? " on" : ""}" data-src="${esc(s)}">${esc(SOURCE_NAMES[s] || s)}<span class="n">${n}</span></button>`
        ).join("");
      row.addEventListener("click", async (ev) => {
        const btn = ev.target.closest("[data-src]");
        if (!btn) return;
        state.src = btn.dataset.src || null;
        state.shown = 0;
        syncControls(); reflow(); syncUrl();
      });
    }

    const subRow = document.getElementById("subChips");
    if (subRow) {
      subRow.addEventListener("click", (ev) => {
        const btn = ev.target.closest("[data-tag]");
        if (!btn) return;
        state.tag = btn.dataset.tag || null;
        state.shown = 0;
        syncControls(); reflow(); syncUrl();
      });
    }

    function syncControls() {
      document.querySelectorAll("[data-cat]").forEach((b) => b.classList.toggle("on", (b.dataset.cat || null) === state.cat));
      document.querySelectorAll("[data-src]").forEach((b) => b.classList.toggle("on", (b.dataset.src || null) === state.src));
      document.querySelectorAll("#subChips [data-tag]").forEach((b) => b.classList.toggle("on", (b.dataset.tag || null) === state.tag));
      document.getElementById("refToggle").checked = state.ref;
      document.querySelectorAll("#sortSegmented [data-sort]").forEach((b) => b.classList.toggle("on", b.dataset.sort === state.sort));
      document.getElementById("searchInput").value = state.q;
    }

    function syncUrl() {
      const p = new URLSearchParams();
      if (state.cat) p.set("cat", state.cat);
      if (state.tag) p.set("tag", state.tag);
      if (state.src) p.set("src", state.src);
      if (state.ref) p.set("ref", "1");
      if (state.q) p.set("q", state.q);
      if (state.sort !== "hot") p.set("sort", state.sort);
      history.replaceState(null, "", p.toString() ? `gallery.html?${p}` : "gallery.html");
    }

    async function reflow() {
      const { list, raw } = await getWorkingList();
      let work = list;
      if (state.tag && raw) {
        work = raw.filter((e) => (e.tags || []).includes(state.tag)).map(toIdx);
      }
      state.list = applyFilters(work);
      state.shown = Math.min(PAGE_SIZE, state.list.length);
      renderGrid(grid, state.list.slice(0, state.shown), openLightbox);
      document.getElementById("resultInfo").textContent =
        `共 ${state.list.length} 条${state.q ? ` · 关键词「${state.q}」` : ""}${state.tag ? ` · ${state.tag}` : ""}`;
      document.getElementById("loadMore").style.display =
        state.shown < state.list.length ? "inline-flex" : "none";
    }

    document.getElementById("loadMore").addEventListener("click", () => {
      state.shown = Math.min(state.shown + PAGE_SIZE, state.list.length);
      renderGrid(grid, state.list.slice(0, state.shown), openLightbox);
    });

    let searchTimer = null;
    document.getElementById("searchInput").addEventListener("input", (ev) => {
      clearTimeout(searchTimer);
      searchTimer = setTimeout(() => {
        state.q = ev.target.value;
        state.shown = 0;
        reflow(); syncUrl();
      }, 220);
    });
    document.getElementById("sortSegmented").addEventListener("click", (ev) => {
      const btn = ev.target.closest("[data-sort]");
      if (!btn) return;
      state.sort = btn.dataset.sort;
      reflow(); syncUrl();
    });
    document.getElementById("refToggle").addEventListener("change", (ev) => {
      state.ref = ev.target.checked;
      reflow(); syncUrl();
    });
  }

  /* ---------- 收藏页 ---------- */
  async function initFavorites() {
    const grid = document.getElementById("grid");
    const ids = favStore.all();
    if (!ids.length) {
      grid.innerHTML = '<div class="empty-tip">还没有收藏,去画廊页收藏喜欢的提示词吧</div>';
      document.getElementById("resultInfo").textContent = "共 0 条";
      return;
    }
    const entries = await window.PGData.getItemsByIds(ids);
    const known = new Set(entries.map((e) => e.id));
    const missing = ids.filter((id) => !known.has(id));
    if (!entries.length) {
      grid.innerHTML = '<div class="empty-tip">收藏的条目已不存在(数据更新被去重合并)</div>';
    } else {
      renderGrid(grid, entries, openLightbox);
    }
    document.getElementById("resultInfo").textContent =
      `共 ${entries.length} 条` + (missing.length ? ` · ${missing.length} 条已因数据更新失效` : "");
  }

  /* ---------- 页面路由 ---------- */
  document.addEventListener("DOMContentLoaded", () => {
    initTheme();
    const page = document.body.dataset.page;
    document.querySelectorAll(".nav a").forEach((a) => {
      if (a.dataset.nav === page) a.classList.add("active");
    });
    if (page === "gallery") initGallery().catch((e) => console.error(e));
    if (page === "favorites") initFavorites().catch((e) => console.error(e));
  });

  /* 导出 */
  window.PG = {
    esc, openLightbox, favStore, toast, copyText,
    CAT_ICON_KEYS, catIcon, ICONS, svgWrap, SOURCE_NAMES,
    imgSrc, renderGrid,
  };
  window.PG_PLACEHOLDER = PLACEHOLDER;
})();
