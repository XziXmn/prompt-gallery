/* 数据加载层:索引立即加载;全文分片按需懒加载。约定字段见 AI.md */
(function () {
  "use strict";

  const cache = {
    stats: null,
    index: null,        // Array(带 img)
    indexLite: null,    // Array(无 img,搜索/检索用,更小)
    featured: null,
    fullMap: null,      // Map(id -> item) 全量
    fullLoading: null,  // Promise
  };

  async function fetchJSON(url) {
    const resp = await fetch(url);
    if (!resp.ok) throw new Error(`加载失败 ${url}: ${resp.status}`);
    return resp.json();
  }

  async function getStats() {
    if (!cache.stats) cache.stats = fetchJSON("data/stats.json");
    return cache.stats;
  }

  async function getIndex() {
    if (!cache.index) cache.index = fetchJSON("data/prompts.index.json");
    return cache.index;
  }

  async function getFeatured() {
    if (!cache.featured) cache.featured = fetchJSON("data/featured.json");
    return cache.featured;
  }

  /** 懒加载全部全文分片(后台执行一次,之后走内存)。返回 Map(id->item)。 */
  function ensureFull() {
    if (cache.fullMap) return Promise.resolve(cache.fullMap);
    if (cache.fullLoading) return cache.fullLoading;
    cache.fullLoading = (async () => {
      const stats = await getStats();
      const n = Math.max(1, stats.fullParts || 1);
      const map = new Map();
      const jobs = [];
      for (let i = 1; i <= n; i++) {
        jobs.push(
          fetchJSON(`data/prompts.full.part${i}.json`)
            .then((part) => (part.items || []).forEach((it) => map.set(it.id, it)))
            .catch(() => {})
        );
      }
      await Promise.all(jobs);
      cache.fullMap = map;
      return map;
    })();
    return cache.fullLoading;
  }

  /** 取单条完整数据(含 prompt 正文);未加载完则临时拉对应分类切片。 */
  async function getItem(id) {
    if (cache.fullMap && cache.fullMap.has(id)) return cache.fullMap.get(id);
    const map = await ensureFull();
    if (map.has(id)) return map.get(id);
    // 兜底:从索引拿分类,再取该分类切片
    const index = await getIndex();
    const idx = index.find((e) => e.id === id);
    if (idx) {
      try {
        const group = await fetchJSON(`data/prompts.by-category/${encodeURIComponent(idx.c)}.json`);
        const hit = (group.items || []).find((it) => it.id === id);
        if (hit) return hit;
      } catch (e) { /* ignore */ }
    }
    return null;
  }

  /** 收藏页:按 id 列表批量取(index 基础信息 + 等全文后补)。 */
  async function getItemsByIds(ids) {
    const index = await getIndex();
    const byId = new Map(index.map((e) => [e.id, e]));
    return ids.filter((id) => byId.has(id)).map((id) => byId.get(id));
  }

  window.PGData = { getStats, getIndex, getFeatured, ensureFull, getItem, getItemsByIds, fetchJSON };
})();
