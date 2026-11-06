// 服务器部署覆盖:启用本地图片缓存代理(/img/?u=编码后的原图URL)
window.PG_SETTINGS = Object.assign({}, window.PG_SETTINGS, { imgProxy: true });
