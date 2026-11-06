/* 全站共享 UI:收藏/复制/Toast/灯箱/卡片渲染/画廊页逻辑 */
(function () {
  "use strict";

  const CAT_ICONS = {
    "海报排版": "🎨", "UI界面": "🖥️", "电商产品": "🛍️", "人像写真": "📷",
    "摄影写实": "📸", "插画艺术": "🖌️", "3D潮玩": "🧸", "信息图表": "📊",
    "Logo品牌": "✒️", "文字渲染": "🔤", "古风历史": "🏮", "游戏动漫": "🎮",
    "场景叙事": "🏙️", "视频模板": "🎬", "其他": "📦",
  };
  const SOURCE_NAMES = {
    canghe: "苍何画廊", suxian: "水仙", david: "Awesome",
    handbook: "实战手册", xtrend: "X热门", youmind: "YouMind",
    gptimage2: "GPTImage2", inbox: "投喂",
  };
  const PLACEHOLDER =
    "data:image/svg+xml;utf8," +
    encodeURIComponent(
      '<svg xmlns="http://www.w3.org/2000/svg" width="400" height="300"><rect width="100%" height="100%" fill="#1a2133"/><text x="50%" y="50%" fill="#5a6578" font-size="40" text-anchor="middle" dominant-baseline="middle">🖼️</text></svg>'
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

  /* ---------- 卡片渲染 ---------- */
  function cardHTML(it) {
    const title = it.tz || it.t || "";
    const cat = it.c || "其他";
    const src = SOURCE_NAMES[it.s] || it.s;
    const fav = favStore.has(it.id) ? " on" : "";
    const img = it.img
      ? `<img loading="lazy" src="${esc(imgSrc(it.img))}" alt="${esc(title)}"
           onerror="this.onerror=null;this.src='${PLACEHOLDER}'">`
      : `<div class="ph">🖼️</div>`;
    const ref = it.nr ? `<span class="chip ref">需参考图</span>` : "";
    return `<article class="card" data-id="${esc(it.id)}">
      <div class="thumb">
        <button class="fav-btn${fav}" data-fav="${esc(it.id)}" title="收藏">♥</button>
        ${img}
      </div>
      <div class="body">
        <h3 class="title" title="${esc(title)}">${esc(title)}</h3>
        <div class="meta">
          <span class="chip cat">${esc(CAT_ICONS[cat] || "")} ${esc(cat)}</span>
          ${ref}
          <span class="chip src">${esc(src)}</span>
        </div>
      </div>
    </article>`;
  }

  function bindCards(container, onItemClick) {
    container.querySelectorAll(".card").forEach((card) => {
      card.addEventListener("click", (ev) => {
        const favBtn = ev.target.closest(".fav-btn");
        if (favBtn) {
          const id = favBtn.dataset.fav;
          const on = favStore.toggle(id);
          favBtn.classList.toggle("on", on);
          toast(on ? "已收藏 ♥" : "已取消收藏");
          ev.stopPropagation();
          return;
        }
        onItemClick(card.dataset.id);
      });
    });
  }

  /* ---------- 灯箱 ---------- */
  function ensureLightbox() {
    let lb = document.querySelector(".lightbox");
    if (lb) return lb;
    lb = document.createElement("div");
    lb.className = "lightbox";
    lb.innerHTML = `
      <button class="lb-close" title="关闭">✕</button>
      <div class="box">
        <div class="lb-handle"></div>
        <div class="img-side"><img alt=""></div>
        <div class="txt-side">
          <h3></h3>
          <div class="lb-meta"></div>
          <div class="prompt-toolbar" style="display:none">
            <button class="fchip on" data-lang="orig">原文</button>
            <button class="fchip" data-lang="zh">中文对照<small style="opacity:.6">机器翻译</small></button>
          </div>
          <div class="prompt-box"></div>
          <div class="lb-actions">
            <button class="btn" data-act="copy">📋 复制当前内容</button>
            <button class="btn secondary" data-act="fav">♥ 收藏</button>
            <a class="btn secondary" data-act="src" target="_blank" rel="noreferrer" style="display:none">↗ 查看来源</a>
          </div>
        </div>
      </div>`;
    document.body.appendChild(lb);
    lb.addEventListener("click", (ev) => {
      if (ev.target === lb || ev.target.classList.contains("lb-close")) closeLightbox();
    });
    document.addEventListener("keydown", (ev) => { if (ev.key === "Escape") closeLightbox(); });
    return lb;
  }

  let currentLightboxItem = null;
  let promptLang = "orig"; // 当前灯箱显示:orig=原文 zh=中文对照

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
    // 骨架态
    lb.querySelector("h3").textContent = "加载中…";
    lb.querySelector(".prompt-box").textContent = "";
    const it = await window.PGData.getItem(id);
    if (!it) { lb.querySelector("h3").textContent = "条目不存在"; return; }
    currentLightboxItem = it;
    const title = it.titleZh || it.title || "";
    lb.querySelector("h3").textContent = title;
    lb.querySelector(".img-side img").src = imgSrc(it.image) || PLACEHOLDER;
    const meta = lb.querySelector(".lb-meta");
    meta.innerHTML = `
      <span class="chip cat">${esc(CAT_ICONS[it.category] || "")} ${esc(it.category)}</span>
      <span class="chip src">${esc(it.source && it.source.name || "")}</span>
      ${it.author ? `<span class="chip">${esc(it.author)}</span>` : ""}
      ${it.needsReference ? `<span class="chip ref">需参考图</span>` : ""}`;
    // 有中文对照时显示切换按钮
    const toolbar = lb.querySelector(".prompt-toolbar");
    toolbar.style.display = it.promptZh ? "flex" : "none";
    renderLightboxPrompt();
    const srcLink = lb.querySelector('[data-act="src"]');
    if (it.source && it.source.url) {
      srcLink.href = it.source.url;
      srcLink.style.display = "inline-flex";
    } else srcLink.style.display = "none";
    const favBtn = lb.querySelector('[data-act="fav"]');
    favBtn.textContent = favStore.has(id) ? "♥ 已收藏" : "♥ 收藏";
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
      toast(ok ? (promptLang === "zh" ? "中文对照已复制 ✓" : "提示词原文已复制 ✓") : "复制失败,请手动选择文本");
    } else if (act.dataset.act === "fav") {
      const on = favStore.toggle(currentLightboxItem.id);
      act.textContent = on ? "♥ 已收藏" : "♥ 收藏";
      toast(on ? "已收藏 ♥" : "已取消收藏");
    }
  });

  /* ---------- 画廊页 ---------- */
  const state = { cat: null, src: null, ref: false, q: "", sort: "hot", shown: 0, list: [] };
  const PAGE_SIZE = 60;

  function applyFilters(index) {
    let list = index.slice();
    const q = state.q.trim().toLowerCase();
    if (state.cat) list = list.filter((e) => e.c === state.cat);
    if (state.src) list = list.filter((e) => e.s === state.src);
    if (state.ref) list = list.filter((e) => e.nr);
    if (q) {
      const full = window.__pgFullMap;
      const fields = (e) => {
        const item = full && full.get(e.id);
        return `${e.t || ""} ${e.tz || ""} ${item ? item.prompt : ""} ${item && item.promptZh ? item.promptZh : ""}`.toLowerCase();
      };
      list = list.filter((e) => fields(e).includes(q));
    }
    if (state.sort === "hot") list.sort((a, b) => (b.h || 0) - (a.h || 0));
    else if (state.sort === "new") list.sort((a, b) => (b.d || "") .localeCompare(a.d || ""));
    else if (state.sort === "rand") list.sort(() => Math.random() - 0.5);
    return list;
  }

  async function initGallery() {
    const grid = document.getElementById("grid");
    const index = await window.PGData.getIndex();
    const stats = await window.PGData.getStats();

    // URL 参数
    const params = new URLSearchParams(location.search);
    state.cat = params.get("cat");
    state.src = params.get("src");
    state.ref = params.get("ref") === "1";
    state.q = params.get("q") || "";
    state.sort = params.get("sort") || "hot";

    renderChips(index, stats);
    syncControls();
    reflow(index);

    // 后台加载全文 → 全文搜索可用后重查一次
    window.PGData.ensureFull().then((map) => {
      window.__pgFullMap = map;
      if (state.q) reflow(index);
    });

    function renderChips(index, stats) {
      const catRow = document.getElementById("catChips");
      const cats = Object.entries(stats.categoryCounts || {}).filter(([, n]) => n > 0)
        .sort((a, b) => b[1] - a[1]);
      catRow.innerHTML =
        `<button class="fchip" data-cat="">全部<span class="n">${index.length}</span></button>` +
        cats.map(([c, n]) => `<button class="fchip" data-cat="${esc(c)}">${esc(CAT_ICONS[c] || "")} ${esc(c)}<span class="n">${n}</span></button>`).join("");
      catRow.addEventListener("click", (ev) => {
        const btn = ev.target.closest("[data-cat]");
        if (!btn) return;
        state.cat = btn.dataset.cat || null;
        state.shown = 0;
        syncControls(); reflow(index); syncUrl();
      });

      const srcRow = document.getElementById("srcChips");
      const sources = Object.entries(stats.perSource || {}).filter(([, n]) => n > 0)
        .sort((a, b) => b[1] - a[1]);
      srcRow.innerHTML =
        `<button class="fchip" data-src="">全部来源</button>` +
        sources.map(([s, n]) => `<button class="fchip" data-src="${esc(s)}">${esc(SOURCE_NAMES[s] || s)}<span class="n">${n}</span></button>`).join("");
      srcRow.addEventListener("click", (ev) => {
        const btn = ev.target.closest("[data-src]");
        if (!btn) return;
        state.src = btn.dataset.src || null;
        state.shown = 0;
        syncControls(); reflow(index); syncUrl();
      });
    }

    function syncControls() {
      document.querySelectorAll("[data-cat]").forEach((b) => b.classList.toggle("on", (b.dataset.cat || null) === state.cat));
      document.querySelectorAll("[data-src]").forEach((b) => b.classList.toggle("on", (b.dataset.src || null) === state.src));
      document.getElementById("refToggle").checked = state.ref;
      document.querySelectorAll("#sortSegmented [data-sort]").forEach((b) =>
        b.classList.toggle("on", b.dataset.sort === state.sort)
      );
      document.getElementById("searchInput").value = state.q;
    }

    function syncUrl() {
      const p = new URLSearchParams();
      if (state.cat) p.set("cat", state.cat);
      if (state.src) p.set("src", state.src);
      if (state.ref) p.set("ref", "1");
      if (state.q) p.set("q", state.q);
      if (state.sort !== "hot") p.set("sort", state.sort);
      history.replaceState(null, "", p.toString() ? `gallery.html?${p}` : "gallery.html");
    }

    function reflow(index) {
      state.list = applyFilters(index);
      state.shown = Math.min(PAGE_SIZE, state.list.length);
      grid.innerHTML = state.list.length
        ? state.list.slice(0, state.shown).map(cardHTML).join("")
        : `<div class="empty-tip" style="column-span:all">没有匹配的提示词,换个关键词试试</div>`;
      bindCards(grid, openLightbox);
      observeReveals(grid);
      document.getElementById("resultInfo").textContent =
        `共 ${state.list.length} 条${state.q ? ` · 关键词「${state.q}」` : ""}`;
      const btn = document.getElementById("loadMore");
      btn.style.display = state.shown < state.list.length ? "inline-flex" : "none";
    }

    document.getElementById("loadMore").addEventListener("click", () => {
      state.shown = Math.min(state.shown + PAGE_SIZE, state.list.length);
      grid.innerHTML = state.list.slice(0, state.shown).map(cardHTML).join("");
      bindCards(grid, openLightbox);
      observeReveals(grid);
      if (state.shown >= state.list.length) btnHide();
      function btnHide() { document.getElementById("loadMore").style.display = "none"; }
    });

    let searchTimer = null;
    document.getElementById("searchInput").addEventListener("input", (ev) => {
      clearTimeout(searchTimer);
      searchTimer = setTimeout(() => {
        state.q = ev.target.value;
        state.shown = 0;
        reflow(index); syncUrl();
      }, 220);
    });
    document.getElementById("sortSegmented").addEventListener("click", (ev) => {
      const btn = ev.target.closest("[data-sort]");
      if (!btn) return;
      state.sort = btn.dataset.sort;
      reflow(index); syncUrl();
    });
    document.getElementById("refToggle").addEventListener("change", (ev) => {
      state.ref = ev.target.checked;
      reflow(index); syncUrl();
    });
  }

  /* ---------- 收藏页 ---------- */
  async function initFavorites() {
    const grid = document.getElementById("grid");
    const ids = favStore.all();
    if (!ids.length) {
      grid.innerHTML = `<div class="empty-tip" style="column-span:all">还没有收藏,去画廊页点亮 ♥ 吧</div>`;
      document.getElementById("resultInfo").textContent = "共 0 条";
      return;
    }
    const entries = await window.PGData.getItemsByIds(ids);
    const known = new Set(entries.map((e) => e.id));
    const missing = ids.filter((id) => !known.has(id));
    grid.innerHTML = entries.map(cardHTML).join("") ||
      `<div class="empty-tip">收藏的条目已不存在(数据更新被去重合并)</div>`;
    bindCards(grid, openLightbox);
    observeReveals(grid);
    document.getElementById("resultInfo").textContent =
      `共 ${entries.length} 条` + (missing.length ? ` · ${missing.length} 条已因数据更新失效` : "");
  }

  /* ---------- 明暗主题(默认浅色;iOS 风格) ---------- */
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
  function syncThemeBtn(theme) {
    // 图标显示"点击后将切换到"的模式
    const btn = document.getElementById("themeToggle");
    if (btn) btn.textContent = theme === "light" ? "🌙" : "☀️";
  }

  /* ---------- 卡片入场动效 ---------- */
  const revealObserver = new IntersectionObserver(
    (entries) => {
      entries.forEach((en) => {
        if (en.isIntersecting) {
          en.target.classList.add("in");
          revealObserver.unobserve(en.target);
        }
      });
    },
    { rootMargin: "80px" }
  );
  function observeReveals(container) {
    container.querySelectorAll(".card:not(.in)").forEach((c) => {
      c.classList.add("reveal");
      revealObserver.observe(c);
    });
  }

  /* ---------- 页面路由 ---------- */
  document.addEventListener("DOMContentLoaded", () => {
    initTheme();
    const page = document.body.dataset.page;
    // 高亮导航
    document.querySelectorAll(".nav a").forEach((a) => {
      if (a.dataset.nav === page) a.classList.add("active");
    });
    if (page === "gallery") initGallery().catch((e) => console.error(e));
    if (page === "favorites") initFavorites().catch((e) => console.error(e));
  });

  /* 导出 */
  window.PG = { esc, cardHTML, bindCards, openLightbox, favStore, toast, copyText, CAT_ICONS, SOURCE_NAMES, imgSrc, observeReveals };
  window.PG_PLACEHOLDER = PLACEHOLDER;
})();
