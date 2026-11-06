# -*- coding: utf-8 -*-
"""一键流水线:采集(按 sources.json 启用项)→ 收件箱 → 归一化 → 精选 → 切片 → 校验。

本地与 GitHub Actions 均调用本脚本。单个采集器失败不阻塞其他源,最后汇总报告。
"""
from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from common import ROOT, log, read_sources_config  # noqa: E402

STEPS_AFTER_COLLECT = [
    ("col_inbox.py", "收件箱收编"),
    ("normalize.py", "归一化去重"),
    ("make_featured.py", "首页精选"),
    ("split_parts.py", "切片输出"),
    ("validate.py", "数据校验"),
]


def run_step(script: str, label: str) -> bool:
    log(f"\n===== {label}({script}) =====")
    t0 = time.time()
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / script)],
        cwd=str(ROOT),
    )
    log(f"----- {label} {'通过' if proc.returncode == 0 else '失败'} · {time.time() - t0:.1f}s")
    return proc.returncode == 0


def main() -> int:
    cfg = read_sources_config()
    failures: list[str] = []
    log("########## 采集阶段 ##########")
    for sid, entry in (cfg.get("sources") or {}).items():
        if not entry.get("enabled", True):
            log(f"[skip] {sid} 已在 sources.json 停用")
            continue
        script = entry.get("collector") or f"col_{sid}.py"
        if not run_step(script, f"采集 {sid} · {entry.get('name', '')}"):
            failures.append(sid)

    log("\n########## 加工阶段 ##########")
    for script, label in STEPS_AFTER_COLLECT:
        if not run_step(script, label):
            failures.append(label)

    log("\n========== 流水线汇总 ==========")
    if failures:
        log(f"失败环节: {failures}(采集器失败不影响其他源与已生成数据)")
        # 校验失败才算整体失败;采集器个别失败允许继续(GitHub Actions 里用于告警)
        return 1 if any(f in ("数据校验",) for f in failures) else 0
    log("全部通过")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
