# Agent Engineer Webapp

一个可运行的通用前后端交互模板，配套 mechanic 迭代工作流。

## 启动

```bash
bash run.sh          # 创建 venv、装依赖、启动 uvicorn
```

打开 http://127.0.0.1:8000 （前端）或 http://127.0.0.1:8000/docs （API）。

## 结构

```text
app.py               # FastAPI 后端（health / state / iterations）
frontend/index.html  # 单页前端（无构建步骤）
AGENTS.md            # mechanic 操作手册（agent 读它来驱动迭代）
state.json           # 迭代状态（frontier / history / budget）
evidence/            # 每 tick 的证据文件（带 hash）
tests/test_app.py    # 后端测试
```

## 用 mechanic 驱动优化

1. 复制本目录到一个新仓库；
2. 让 agent 读 `AGENTS.md` 并按循环工作：Observe → Hypothesize → Change →
   Verify → Record → Checkpoint；
3. 每 tick 是一个 commit，state.json 记录全部历史，evidence/ 存放证明。

完整工作流见 skill `agent-engineer-repo-mechanic`。
