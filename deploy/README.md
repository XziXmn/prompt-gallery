# 服务器部署(Docker)

把画廊部署到一台常开的服务器(如日本 VPS):国内直连快、图片本地缓存代理、不依赖 github.io。
GitHub 仓库仍是**数据源头**(Actions 继续负责采集/翻译/去重),服务器每 30 分钟自动 pull 最新数据。

## 架构

```
GitHub Actions(采集/翻译/切片,每 6h)→ GitHub 仓库(数据源头)
                                          │  sync 容器每 30min git pull
                                          ▼
                    服务器 Docker
                      ├─ gallery:nginx 静态站点(:8088)
                      └─ /img/?u=…:图片缓存代理(白名单 + 30 天磁盘缓存 + 限流)
GitHub Pages 保留为免费备份入口
```

## 首次部署(约 5 分钟)

```bash
# 1. 服务器上克隆仓库(公开仓库,无需密钥)
git clone https://github.com/<你的用户名>/<仓库名>.git
cd <仓库名>/deploy

# 2. 一键启动(站点 + 图片代理 + 自动同步)
docker compose up -d

# 3. 验证
curl -s http://127.0.0.1:8088/stats.html -o /dev/null -w "%{http_code}\n"   # 仓库 stats.html 不存在,应 404
curl -s http://127.0.0.1:8088/index.html -o /dev/null -w "%{http_code}\n"   # 200
curl -s -o /dev/null -w "%{http_code} %{header_json}" "http://127.0.0.1:8088/img?u=https%3A%2F%2Fr2.qqsrc.com%2Fimages%2Foriginals%2F14347.jpg"
```

浏览器打开 `http://<服务器IP>:8088/` 即可看到站点(图片走本地缓存代理,
卡片右上角开发工具里能看到 `X-Cache: HIT/MISS`)。

## 它做了什么

| 组件 | 说明 |
|---|---|
| `gallery` 服务 | nginx 挂载仓库根目录为站点根;`settings.local.js` 覆盖默认配置,让全站图片走 `/img/` 代理 |
| `/img` 代理 | 域名白名单(6 个图源,见 nginx.conf 的 map,新增图源加一行)→ 30 天磁盘缓存(上限 3GB)→ 抹 Referer 防盗链 → 单 IP 30 req/s 限流防滥用 |
| `sync` 服务 | alpine/git 容器每 30 分钟 `git pull --ff-only`,数据自动更新,无需任何 GitHub 密钥 |

## 建议的后续加固

- **HTTPS**:在前面再套一层 [Caddy](https://caddyserver.com/)(自动签证书)或套 Cloudflare;
  端口 `8088` 可在 `docker-compose.yml` 里改成 `80`
- **域名**:解析 A 记录到服务器 IP 即可
- **数据快照隐私**:仓库 `data/sources/` 存有各源原始快照,若介意公开可改私有仓库
  (私有仓库的 `sync` 容器需要在 clone 时配一次 deploy key,之后 pull 不变)

## 常见问题

| 问题 | 处理 |
|---|---|
| 图片 403 | 图片 URL 不在白名单 → `nginx.conf` 的 map 里加对应域名,`docker compose restart gallery` |
| 磁盘涨太快 | 缓存上限 3GB 自动淘汰;也可 `docker compose down && docker volume rm deploy_img-cache && docker compose up -d` 清空 |
| 同步失败 | `docker logs prompt-gallery-sync` 查看;多为远端强推或网络抖动,`git pull` 手动修复一次即可 |
| 想改端口 | `docker-compose.yml` 里 `8088:80` 左边的数字 |
