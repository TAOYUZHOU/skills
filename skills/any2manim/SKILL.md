---
name: any2manim
description: >-
  Run and drive the local Any2Manim app to turn a plain-language teaching
  idea (any subject) into a rendered Manim teaching-animation video, then
  converse to revise, generate narration/subtitles, and export. Use when the
  user wants 教学动画 / 讲解视频 / 把某个知识点讲成动画 / 一句话生成动画 /
  分镜动画 / Manim 视频 / text-to-manim / math explainer video, or wants to
  install, start, debug, or script Any2Manim. Not for static charts or decks.
---

# Any2Manim

老师用一句自然语言描述 → AI 先产出**结构化教学分镜**、再写 [Manim](https://www.manim.community/)（ManimCE 0.20）代码、自动渲染出预览 → 对话式定向修改 → AI 配音 + 字幕 → 导出 MP4/GIF/封面。

- 代码位于本技能目录下 [`app/`](app/)（完整应用，非单文件脚本）。上游：[buBailai/Any2Manim](https://github.com/buBailai/Any2Manim)（MIT）。
- 形态：FastAPI 后端 + 纯 HTML/CSS/JS 前端，无前端构建步骤；默认端口 `8848`。
- 数据全部本地落盘（`app/data/`，SQLite + 文件），BYO-Key（自带模型 Key），未配 Key 时进入**演示模式**离线出片。

## 何时用 / 不用

用：把讲解思路变成课堂投屏/备课用的教学动画；跑通或排障 Any2Manim；用 HTTP API 批量/脚本化生成教学视频。

不用：静态图表、PPT/网页 deck（用 `public-html-report` / `pptx`）、纯数学推导不要求出片（直接答即可）。

## 快速开始

```bash
# 1) 建 venv 并装依赖（首次会在 app/ 下建 .venv，并预取 static-ffmpeg）
skills/any2manim/scripts/setup.sh

# 2) 启动服务（默认 http://127.0.0.1:8848；A2M_HOST/A2M_PORT 可覆盖）
skills/any2manim/scripts/run.sh
```

然后浏览器打开 <http://127.0.0.1:8848>。配 Key：右上角 ⚙️ 设置里选厂商填 Key（内置 DeepSeek / 豆包·火山方舟 / 通义千问 / 智谱 GLM / 硅基流动 / Cherry / Kimi / OpenAI / Ollama / 自定义 OpenAI 兼容）。**不填 Key 也能用**：演示模式用内置范例离线出片。

- 环境要求：Python 3.10+（开发于 3.14）。
- `ffmpeg` 由 `static-ffmpeg`（pip 自带，含字幕烧录用 libass）解决，首次会下载一次（~30MB）。
- 含 LaTeX 公式的动画需本机有 TeX 环境（TinyTeX / TeX Live）。检测不到会**自动降级**用 `Text` 写公式，数理题不会彻底失败。
- 也保留上游入口 `app/start.sh`（绑 `0.0.0.0` 供局域网访问，要求 `.venv` 已存在）。

## 用 HTTP API 驱动（agent 自动化）

Base URL 默认 `http://127.0.0.1:8848`。生成是**异步队列 + SSE**：提交后订阅事件流拿进度与产物 URL。

| 动作 | 方法 & 路径 | 说明 |
|---|---|---|
| 列 / 建项目 | `GET /api/projects?archived=false` · `POST /api/projects` | body `{title, subject}`；返回项目（含 `id`） |
| 查项目全量 | `GET /api/projects/{pid}` | `{project, versions, messages}`；`versions[].preview_path/thumb_path` 相对 `data/` |
| 提交生成/修改 | `POST /api/projects/{pid}/message` | body `{prompt, shot_index?}`；`shot_index`（从1起）把改动**限定到某一镜**；返回 `queue_position` |
| 订阅进度 | `GET /api/projects/{pid}/events`（SSE） | 事件见下表 |
| 取某版本 | `GET /api/projects/{pid}/version/{seq}` | 取 `code` / `storyboard` / `narration` / `status` |
| 分镜章节 | `GET /api/projects/{pid}/version/{seq}/chapters` | `[{idx,label,start,end}]` + 真实时长 |
| 导出 | `POST /api/projects/{pid}/export` | body `{seq, formats, quality, voiceover, voice, rate, subtitle, cover_time}` |
| 回退版本 | `POST /api/projects/{pid}/revert` | body `{seq}`（仅 `status=="ok"` 可回退） |
| 归档 | `POST /api/projects/{pid}/archive` | body `{archived}`；归档后只读 |
| 素材 | `POST /api/projects/{pid}/assets`（multipart `file`）· `GET` · `DELETE …/{aid}` | 图片 png/jpg/webp/gif 或 svg |
| 解说稿 | `POST …/version/{seq}/narration`（`{text}`）· `POST …/narration/generate` · `POST …/narration/audio` | 保存 / AI 生成 / 试听合成 |
| 配置 | `GET|POST /api/config` · `POST /api/config/test` | 保存各厂商 Key/地址/模型；`test` 做连通性自检 |
| 元数据 | `GET /api/providers` · `GET /api/examples` · `GET /api/voices` · `GET /api/changelog` | 厂商预设 / 分学科示例 / 音色 / 版本日志 |

导出参数：`formats ⊆ {mp4,gif,cover}`；`quality ∈ {l,m,h,k}` = 480p/720p/1080p/4K；`subtitle ∈ {none,burn,srt}`；`cover_time` = 封面取第几秒。产物经 `/media/<相对 data/ 路径>` 访问。

**SSE 事件类型**（`data:` JSON，含 `type`；多数带 `seq`）：
`version_start`(demo) · `rendering`(stage=`thumb`|`preview`) · `thumb_ready`(thumb_url) · `preview_ready`(preview_url, attempts, demo, best_effort) · `fallback_render` · `no_change`(error) · `failed`(error, env_missing, code) · `exporting` · `voicing` · `voice_warn`(warn) · `export_ready`(products) · `export_failed`(error)。

### 端到端最小流程

```bash
BASE=http://127.0.0.1:8848
# 1) 建项目
PID=$(curl -s -X POST $BASE/api/projects -H 'content-type: application/json' \
  -d '{"title":"自由落体","subject":"物理"}' | python3 -c 'import sys,json;print(json.load(sys.stdin)["id"])')
# 2) 后台订阅 SSE（拿进度/产物 URL）
curl -N "$BASE/api/projects/$PID/events" &
# 3) 提交生成
curl -s -X POST "$BASE/api/projects/$PID/message" -H 'content-type: application/json' \
  -d '{"prompt":"画一个自由落体的小球，旁边同步画出速度-时间图像"}'
# 4) 等 preview_ready 后取当前版本号，再导出 1080p + 配音 + 烧录字幕
SEQ=$(curl -s "$BASE/api/projects/$PID" | python3 -c 'import sys,json;print(json.load(sys.stdin)["versions"][-1]["seq"])')
curl -s -X POST "$BASE/api/projects/$PID/export" -H 'content-type: application/json' \
  -d "{\"seq\":$SEQ,\"formats\":[\"mp4\",\"cover\"],\"quality\":\"h\",\"voiceover\":true,\"subtitle\":\"burn\"}"
```

## 关键机制（决定怎么用）

- **教学优先管线**：不是「一句话直接出码」，而是先出结构化教学镜头计划（先直觉后符号、公式拆项），再翻译成动画并做「能教」质检。
- **自愈渲染循环**：渲染报错自动把错误喂回模型修复，有界重试（`HEAL_MAX_ATTEMPTS=4` / `HEAL_MAX_SECONDS=300` / 同错 3 次停），保住最后一个可渲版本；`fallback_render` 表示校验没全过但兜底渲出了。
- **定向编辑**：改动只产生最小代码 diff；传 `shot_index` 可把修改限定到某一镜。若没定位到改处 → 事件 `no_change`、旧版保留（不会整片重做）。
- **个人版单 worker 串行**（`A2M_WORKERS=1`）：渲染排队执行，别并发提交多个生成。
- **存储哲学**：代码/缩略图/元数据长期留，视频昂贵按需重渲；`versions[].preview_path` 是低清预览（临时），高清成片在 `app/data/projects/<id>/exports/`。

## 坑与注意

- **端口占用**：默认 8848；被占则 `A2M_PORT=8850 scripts/run.sh`。
- **首次渲染慢**：首次会下载 static-ffmpeg 并可能触发 Manim/TeX 缓存构建，属正常。
- **公式与路径**：LaTeX 对中文/全角路径敏感；若在含中文的路径下渲染公式失败，会降级用 `Text`（不再报错但观感差）。要真公式请装 TinyTeX/TeX Live。
- **配音需联网**：edge-tts 合成需联网（大陆网络可能要被代理/拦截），失败只发 `voice_warn` 不中断导出（视频仍产出，仅无配音）。
- **演示模式**：`GET /api/config` 的 `demo:true` 说明当前未配有效 Key，走的离线范例，不调大模型。
- **数据不随代码走**：`app/data/` 与 `.venv/` 已被 `.gitignore` 忽略，不会提交进本仓库；换机器需重跑 `scripts/setup.sh` 并在页面重配 Key（或从 `app/data/config.json` 迁移）。

## 目录

- [`app/`](app/) — 应用本体（`backend/` FastAPI + `frontend/` 纯前端 + `tools/` + `requirements.txt` + `start.sh`）
- [`app/backend/prompts/`](app/backend/prompts/) — 注入提示词（Manim API 速查 / 公式设计规则 / 镜头语法 / 教学原则）
- [`app/CHANGELOG.md`](app/CHANGELOG.md) — 版本号与更新日志的唯一来源（页面动态读取）
- [`scripts/setup.sh`](scripts/setup.sh) · [`scripts/run.sh`](scripts/run.sh) — 本技能加的便捷封装
- [`app/README.md`](app/README.md) · [`app/LICENSE`](app/LICENSE) — 上游文档与 MIT 许可

> 升级上游：直接重新克隆 [buBailai/Any2Manim](https://github.com/buBailai/Any2Manim) 覆盖 `app/`（保留 `app/data/` 与 `.venv/`）。
