/* 首页:双栏 Hero 信息位 + 轮播 + 每日精选(换一批)+ 分类 + 最新入库 */
(function () {
  "use strict";

  const { esc, openLightbox, renderGrid, catIcon } = window.PG;
  const ico = (name, cls) => window.PG.svgWrap(window.PG.ICONS[name]).replace('class="ico-svg"', `class="${cls || "ico-svg"}"`);

  const fmt = (n) => Number(n || 0).toLocaleString("en-US");

  let carouselIndex = 0;
  let carouselItems = [];
  let carouselTimer = null;

  async function init() {
    const [index, stats, featuredIds] = await Promise.all([
      window.PGData.getIndex(),
      window.PGData.getStats(),
      window.PGData.getFeatured().catch(() => []),
    ]);

    renderHero(stats, index);
    renderCarousel(featuredIds, index);
    renderDaily(index);
    renderCategories(stats);
    renderLatest(index);
  }

  /* ---------- Hero 信息位 ---------- */
  function renderHero(stats, index) {
    const sources = Object.entries(stats.perSource || {}).filter(([, n]) => n > 0);
    const cats = Object.values(stats.categoryCounts || {}).filter((n) => n > 0).length;
    const total = document.getElementById("heroTotal");
    const srcN = document.getElementById("heroSources");
    if (total) total.textContent = fmt(index.length);
    if (srcN) srcN.textContent = sources.length;

    const hs = document.getElementById("heroStats");
    if (hs) {
      hs.innerHTML = `
        <div class="s"><div class="n">${fmt(index.length)}</div><div class="l">精选提示词</div></div>
        <div class="s"><div class="n">${cats}</div><div class="l">统一分类</div></div>
        <div class="s"><div class="n">${sources.length}</div><div class="l">来源渠道</div></div>`;
    }
    const upd = document.getElementById("hsUpdated");
    const imgs = document.getElementById("hsImages");
    const ref = document.getElementById("hsRef");
    if (upd) upd.textContent = (stats.generatedAt || "").slice(0, 16).replace("T", " ") + " UTC";
    if (imgs) imgs.textContent = fmt(stats.images || 0) + " 张";
    if (ref) ref.textContent = fmt(stats.needsReference || 0) + " 条";
  }

  /* ---------- 轮播 ---------- */
  function renderCarousel(featuredIds, index) {
    const byId = new Map(index.map((e) => [e.id, e]));
    carouselItems = featuredIds.map((id) => byId.get(id)).filter(Boolean).slice(0, 10);
    if (!carouselItems.length) carouselItems = index.filter((e) => e.img).slice(0, 10);

    const track = document.getElementById("carouselTrack");
    const dots = document.getElementById("carouselDots");
    if (!carouselItems.length) return;

    track.innerHTML = carouselItems
      .map((it) => {
        const title = it.tz || it.t || "";
        return `<div class="carousel-slide" data-id="${esc(it.id)}">
          <img src="${esc(window.PG.imgSrc(it.img))}" alt="${esc(title)}"
            onerror="this.onerror=null;this.src=window.PG_PLACEHOLDER">
          <div class="shade"></div>
          <div class="carousel-caption">
            <span class="tag">${esc(it.c)}</span>
            <h3>${esc(title)}</h3>
            <div class="src">${esc(window.PG.SOURCE_NAMES[it.s] || it.s)} · 点击查看提示词</div>
          </div>
        </div>`;
      })
      .join("");
    dots.innerHTML = carouselItems.map((_, i) => `<span data-i="${i}" class="${i === 0 ? "on" : ""}"></span>`).join("");

    // 箭头用 SVG
    document.querySelector(".carousel-arrow.prev").innerHTML = window.PG.svgWrap(window.PG.ICONS.left);
    document.querySelector(".carousel-arrow.next").innerHTML = window.PG.svgWrap(window.PG.ICONS.right);

    track.parentElement.querySelector(".prev").addEventListener("click", () => go(carouselIndex - 1, true));
    track.parentElement.querySelector(".next").addEventListener("click", () => go(carouselIndex + 1, true));
    dots.addEventListener("click", (ev) => {
      const s = ev.target.closest("[data-i]");
      if (s) go(Number(s.dataset.i), false);
    });
    track.addEventListener("click", (ev) => {
      const slide = ev.target.closest("[data-id]");
      if (slide) openLightbox(slide.dataset.id);
    });
    go(0, false);
    startAuto();
    let startX = null;
    track.addEventListener("touchstart", (ev) => { startX = ev.touches[0].clientX; }, { passive: true });
    track.addEventListener("touchend", (ev) => {
      if (startX == null) return;
      const dx = ev.changedTouches[0].clientX - startX;
      if (Math.abs(dx) > 40) go(carouselIndex + (dx < 0 ? 1 : -1), true);
      startX = null;
    }, { passive: true });
  }

  function go(i, resetTimer) {
    if (!carouselItems.length) return;
    carouselIndex = ((i % carouselItems.length) + carouselItems.length) % carouselItems.length;
    document.getElementById("carouselTrack").style.transform = `translateX(-${carouselIndex * 100}%)`;
    document.querySelectorAll("#carouselDots span").forEach((d, di) =>
      d.classList.toggle("on", di === carouselIndex)
    );
    if (resetTimer) startAuto();
  }
  function startAuto() {
    clearInterval(carouselTimer);
    carouselTimer = setInterval(() => go(carouselIndex + 1, false), 5200);
  }

  /* ---------- 每日精选:按日期确定性轮换 + 换一批 ---------- */
  function mulberry32(seed) {
    return function () {
      seed |= 0; seed = (seed + 0x6D2B79F5) | 0;
      let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }
  function hashStr(s) {
    let h = 2166136261;
    for (let i = 0; i < s.length; i++) {
      h ^= s.charCodeAt(i);
      h = Math.imul(h, 16777619);
    }
    return h >>> 0;
  }

  let dailyPool = [];

  function pickDaily(shuffled) {
    const usedCats = {};
    const picks = [];
    for (const e of shuffled) {
      const c = usedCats[e.c] || 0;
      if (c >= 2) continue;
      usedCats[e.c] = c + 1;
      picks.push(e);
      if (picks.length >= 10) break;
    }
    if (picks.length < 10) {
      picks.push(...shuffled.filter((e) => !picks.includes(e)).slice(0, 10 - picks.length));
    }
    return picks;
  }

  function renderDaily(index) {
    const badge = document.getElementById("dailyBadge");
    const grid = document.getElementById("dailyGrid");
    const today = new Date();
    const key = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, "0")}-${String(today.getDate()).padStart(2, "0")}`;
    if (badge) badge.textContent = `${key} · 每天更新`;

    dailyPool = index
      .filter((e) => e.img && (e.h || 0) > 0)
      .sort((a, b) => (b.h || 0) - (a.h || 0))
      .slice(0, 120);
    if (dailyPool.length < 10) dailyPool = index.filter((e) => e.img);

    const rng = mulberry32(hashStr("daily-" + key));
    const shuffled = dailyPool.slice();
    for (let i = shuffled.length - 1; i > 0; i--) {
      const j = Math.floor(rng() * (i + 1));
      [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
    }
    renderGrid(grid, pickDaily(shuffled), openLightbox);

    const btn = document.getElementById("dailyShuffle");
    if (btn && !btn.dataset.bound) {
      btn.dataset.bound = "1";
      btn.addEventListener("click", () => {
        if (!dailyPool.length) return;
        let next, tries = 0;
        const current = new Set([...grid.querySelectorAll(".card")].map((c) => c.dataset.id));
        do {
          const r = mulberry32((Math.random() * 2 ** 31) | 0);
          const s = dailyPool.slice();
          for (let i = s.length - 1; i > 0; i--) {
            const j = Math.floor(r() * (i + 1));
            [s[i], s[j]] = [s[j], s[i]];
          }
          next = pickDaily(s);
          tries++;
        } while (tries < 6 && next.every((e) => current.has(e.id)));
        renderGrid(grid, next, openLightbox);
        grid.scrollIntoView({ behavior: "smooth", block: "start" });
      });
    }
  }

  /* ---------- 分类导航 ---------- */
  function renderCategories(stats) {
    const grid = document.getElementById("catGrid");
    const counts = Object.entries(stats.categoryCounts || {})
      .filter(([, n]) => n > 0)
      .sort((a, b) => b[1] - a[1]);
    grid.innerHTML = counts
      .map(([cat, n]) => `
        <a class="cat-card" href="gallery.html?cat=${encodeURIComponent(cat)}">
          <span class="ico">${catIcon(cat)}</span>
          <span class="name">${esc(cat)}</span>
          <span class="count">${fmt(n)} 条</span>
        </a>`)
      .join("");
  }

  /* ---------- 最新入库 ---------- */
  function renderLatest(index) {
    const latest = index
      .filter((e) => e.img)
      .sort((a, b) => (b.d || "").localeCompare(a.d || ""))
      .slice(0, 12);
    const grid = document.getElementById("latestGrid");
    renderGrid(grid, latest, openLightbox);
  }

  document.addEventListener("DOMContentLoaded", () => init().catch((e) => console.error(e)));
})();
