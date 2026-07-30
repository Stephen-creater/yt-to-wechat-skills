---
name: ds-post-to-wechat
description: 大圣专用微信公众号草稿箱发布工具。支持两种产物——文章（长文，markdown/HTML/纯文本，TS 渲染主题）和小绿书（贴图号 newspic，纯文本 + 最多 20 张图）。所有微信 API 调用默认通过 SSH SOCKS5 隧道（dasheng-ecs）出口，绕开家宽 IP 漂移和 IP 白名单限制。触发条件：用户提到"发公众号""发到草稿箱""发文章""发小绿书""贴图号""post to wechat""微信公众号"。
version: 1.0.3
metadata:
  requires:
    anyBins:
      - bun
      - npx
    pythonModules:
      - requests
      - PySocks
---

# ds-post-to-wechat

物理合并自 `JimLiu/baoyu-skills` 的 `baoyu-post-to-wechat`（TS 文章发布）和大圣自维护的 `wechat-newspic-publisher`（Python 小绿书发布）。已剥离 browser 模式和 image-text browser 路径——本 skill 只走微信官方 API，通过 SSH 隧道解决 IP 白名单问题。

## 产物选择

| 类型 | 何时用 | 入口脚本 |
|------|--------|----------|
| **文章**（长文，可带封面/正文图/外链/主题渲染） | 标准公众号长文 | `scripts/ts/wechat-api.ts` |
| **小绿书**（newspic / 贴图号，纯文本 + 多图，最多 20 张） | 短帖、随感、9 宫格图文 | `scripts/py/publish.py` |

⚠️ 不支持的发布通道（已物理移除）：
- ❌ baoyu 原 `browser` 模式（Chrome CDP 操作网页编辑器）
- ❌ baoyu 原 `image-text browser` 模式（9 张图浏览器贴图）—— 已被小绿书 newspic API 覆盖且优于它

## 共享配置

| 路径 | 内容 |
|------|------|
| `.ds-skills/.env` | `WECHAT_APP_ID` + `WECHAT_APP_SECRET` |
| `.ds-skills/ds-post-to-wechat/EXTEND.md` | 偏好（默认走本地直连，无需 SSH 隧道） |

查找顺序均为：cwd 优先 → `~` 兜底。

**默认本地直连**：本机 IP 加到公众号后台的「IP 白名单」即可。如果你的家宽 IP 经常漂移，再考虑下方可选的 SSH 隧道方案。

**EXTEND.md 最小配置**（推荐学员使用）：

```yaml
default_publish_method: api             # 默认本地直连
default_theme: default                  # default / grace / simple / modern
default_color:                          # 留空 = 用 theme 默认色
default_author: 你的笔名
need_open_comment: 1                    # 默认开评论
only_fans_can_comment: 0
```

**可选：SSH 隧道**（仅当本机 IP 漂移、想统一从一台固定 IP 的服务器出口时使用）：

```yaml
default_publish_method: remote-api      # 改成 remote-api 才走隧道
remote_publish_host: <your-vps-host>    # 你的 VPS 公网 IP 或域名
remote_publish_user: <your-vps-user>
remote_publish_port: 22
remote_publish_identity_file: ~/.ssh/<your-vps-key>
remote_publish_strict_host_key_checking: accept-new
remote_publish_connect_timeout: 10
```

> 用 SSH 隧道时，要把 VPS 的出口 IP 加到公众号后台白名单，而不是本机 IP。

## 用法

### 文章

```bash
BUN=$(command -v bun || echo "npx -y bun")
SKILL="$HOME/.claude/skills/ds-post-to-wechat"  # Codex 用户改成 $HOME/.codex/skills/ds-post-to-wechat

# 默认（按 EXTEND.md 走 remote-api）
$BUN "$SKILL/scripts/ts/wechat-api.ts" article.md

# 显式带主题
$BUN "$SKILL/scripts/ts/wechat-api.ts" article.md --theme grace --color blue

# 强制本地直连（不走隧道，需本机 IP 在白名单）
# 把 EXTEND.md 的 default_publish_method 改成 api 或临时去掉 --remote
```

**入参要点**：
- 接受 `.md` / `.html` / 不存在的路径（按纯文本处理）
- Markdown 默认把外链转成文末引用（`--no-cite` 关掉）
- `news` 类型必须封面（见下方"封面约定"）
- 永远显式传 `--theme`，即使是 `default`
- 默认 `need_open_comment=1`, `only_fans_can_comment=0`

### 📌 封面约定（本工作流的硬性约定）

**所有进入公众号发布的文章必须在发布前写好 frontmatter `cover_image` 字段，指向本地图片路径或 HTTP/OSS 图片 URL。** 这样 `ds-post-to-wechat` 不用问任何问题就能拿到封面。

```yaml
---
title: "文章标题"
cover_image: ./封面/20260522-cover.jpg   # 本地相对路径（推荐）
# 或绝对路径：
# cover_image: ~/your-content-dir/公众号/封面/20260522-cover.jpg
# 或 OSS URL：
# cover_image: https://your-bucket.oss-cn-hangzhou.aliyuncs.com/path/20260523-cover.png
---
```

**约定规则**：

1. **唯一权威字段**：`cover_image`。`coverImage` / `featureImage` / `cover` / `image` 是历史兼容键，**不要在新文档里使用**，统一只写 `cover_image`。
2. **URL 和本地路径都支持**：`cover_image` 可以是本地相对路径、绝对路径或 HTTP/OSS URL；脚本会下载远程封面并上传为微信永久素材。
3. **常规文章建议本地路径，自动发布流程建议 OSS URL**：手工写稿可放 `01 内容创作/公众号/封面/`；`ds-yt-publish-wechat` 这类自动流程直接写 OSS URL，不在文章目录旁长期保存封面文件。
4. **文档可预览，发布会剥离**：Markdown 里允许在 H1 上方放一张 `![公众号封面](cover_image)` 作为写作预览图；`md-to-wechat.ts` 发布渲染前会自动剥离 H1 前的公众号封面预览，它不会进入微信正文。
5. **不要把 `cover_image` 放进正文内容区**：它只用于微信封面素材 / `thumb_media_id`。如果需要文档预览，只放在 H1 上方；不要放在 H1 下方，也不要当正文首图。
6. **不要依赖 `cover_fallback: false` 当封面方案**：它只能防止脚本误把正文首图当封面；发布前仍必须显式提供 `cover_image`。已有稿件保留该字段不影响 `cover_image` 优先级。
7. **封面查找顺序**（脚本内置，无需手动控制）：
   ```
   CLI --cover → frontmatter.cover_image → frontmatter.coverImage（兼容旧稿） → imgs/cover.png → 正文首图 → 报错
   ```

**为什么仍要求显式 `cover_image`**：微信 API `news` 类型必须先把封面上传成永久素材（拿 `thumb_media_id`）。脚本可以处理"本地路径 / OSS URL → 微信永久素材"，但不能猜哪一张正文图才是公众号封面。

### 📌 阅读原文 / 原文链接约定（可选）

文章 frontmatter 支持：

```yaml
content_source_url: https://...
# 兼容别名：
# source_url: https://...
```

发布 `news` 图文时，脚本会把它写入微信 `draft/add` 的 `content_source_url` 字段，也就是公众号后台里的“阅读原文 / 原文链接”。

用途：

1. 视频号短视频二次成文时，可把视频号短链写入这里。
2. YouTube / 外部资料二次转述时，可把原始链接写入这里。
3. 如果微信接口或后台策略不允许某类外链，发布时以微信 API 返回为准，不伪造正文卡片。

注意：`content_source_url` 不是正文内嵌卡片，也不是视频号富组件。它只负责原文链接。

### 📌 主题清单（articles only）

`default_theme` 可选值：

| 主题 | 来源 | 视觉特征 |
|---|---|---|
| `default` / `grace` / `simple` / `modern` | baoyu-md 原生 | 见 baoyu 主题文档 |
| **`dasheng`** ⭐ | 大圣专用虚拟主题（**当前默认**） | 底层用 baoyu `default`，发布前 hook 改造：H2 红色左对齐无底色 + 正文加粗变黑色 |

**`dasheng` 主题精确设计**（已定稿）：

| 元素 | 规则 |
|---|---|
| H2 (`##`) | `color: #C0392B`（深红）+ `text-align: left` + `display: block` + `font-size: 1.25em` + `font-weight: bold` + `letter-spacing: 0.05em` + `margin: 2em 8px 1em 8px` + 透明背景（无蓝底蓝条） |
| 正文加粗 `<strong>` | `color: #000`（纯黑，覆盖 baoyu 默认 primaryColor 蓝） |
| H1、正文段落、引用、列表等 | 复用 baoyu `default` 主题，不动 |
| Footer | 见下方"文末固定 footer" |

**实现位置**：`scripts/ts/wechat-api.ts` 的 `args.theme === "dasheng"` 分支，在 `publishToDraft` 前对 `htmlContent` 做两道 regex 后处理。

**色彩三层**：
- 红 `#C0392B` 仅三处：H2 标题 + Footer `—END—` + Footer CTA（视觉锚点统一）
- 黑加粗 `#000`：正文 `<strong>` + Footer 重要数据（社会证明类内容）
- 灰正文 `#3f3f3f`：默认段落

### 📌 文末固定 footer（仅文章 news 类型自动追加）

每篇文章发布前，脚本会自动把一段固定 HTML 拼到正文末尾。**用来放"—END—、个人简介、加微信"那种重复内容**，等价于微信公众号后台的「常用模板」（微信官方 `draft/add` API 不支持引用后台模板 ID，所以这里在 HTML 层模拟）。

**查找顺序**（首个命中即用）：
```
<cwd>/.ds-skills/ds-post-to-wechat/footer.html      ← 主用，已配
~/.ds-skills/ds-post-to-wechat/footer.html
<skill-root>/footer.html                            ← 兜底
```

**只对 `article_type=news` 生效**，小绿书（newspic）走 Python `publish.py`，footer 由 `<skill-root>/footer.md` 控制（纯文本格式）。

要改文末内容，直接编辑 `.ds-skills/ds-post-to-wechat/footer.html`，下次发布自动生效，无需重启或重装。

⚠️ 微信 `content` 字段总长上限 20000 字符，footer 占太长会挤压正文额度。当前 footer 约 600 字符，余量充足。

### 小绿书

```bash
PY="$HOME/.claude/skills/ds-post-to-wechat/scripts/py/publish.py"  # Codex 改成 $HOME/.codex/...

# 纯文字（自动用占位白图，发布后到后台删）
python3 "$PY" --title "20 字标题" --content "正文…"

# 多图（本地路径，自动上传永久素材）
python3 "$PY" --title "20 字标题" --content_file body.txt --image_files "1.jpg,2.jpg,3.jpg"

# 已有永久素材 media_id
python3 "$PY" --title "20 字标题" --content_file body.txt --images "ID1,ID2"
```

**入参要点**：
- 标题最多 20 字
- 正文是纯文本（newspic API 强制），段落空行分隔
- 图片最多 20 张，第一张自动当封面
- 推荐图片 1080×1440（3:4 竖版）
- 默认从 EXTEND.md 读 `default_publish_method`；显式 `--remote` 也行，`--no-remote` 强制本地

## 工作流

```
- [ ] Step 0: 判断产物类型（用户说"文章"/"长文" → 文章；说"小绿书"/"贴图"/"短帖" → newspic）
- [ ] Step 1: 检查 EXTEND.md（缺失则先引导写一份）
- [ ] Step 2: 校验 frontmatter / 标题字数 / 封面（仅文章）/ 图片清单（仅 newspic）
- [ ] Step 3: 调用对应脚本
- [ ] Step 4: 解析返回的 media_id，给出后台草稿箱链接
```

## 故障排查

| 现象 | 原因 / 处理 |
|------|------------|
| `40164 invalid ip` | 出口 IP 不在白名单。登录 mp.weixin.qq.com → 开发 → 基本配置 → IP白名单，加入本机或 VPS 的公网 IP |
| `40001 invalid credential` | AppSecret 重置后 .env 未更新 |
| `40125 invalid appid/secret` | .env 配错或被截断 |
| `SOCKS proxy on 127.0.0.1:<port> not ready` | SSH 隧道起不来。检查 key 权限、known_hosts、网络连通 |
| `ssh exited early` | 服务器拒绝连接或 key 不对，看 stderr 里 ssh 输出 |
| `45001 文件超限` | 图片单张超过 10MB |
| 标题报错 | newspic 标题 >20 字，文章标题 >64 字 |

## 子模块结构

```
ds-post-to-wechat/
├── SKILL.md                    ← 本文件
├── footer.md                   ← 小绿书默认签名（如使用）
├── placeholder.jpg             ← 小绿书 newspic 占位白图（无图时使用）
├── references/                 ← 留作扩展
└── scripts/
    ├── ts/                     ← 文章发布（bun）
    │   ├── wechat-api.ts       ← 主入口
    │   ├── wechat-http.ts      ← HTTP 客户端
    │   ├── wechat-socks-http.ts ← SOCKS5 包装
    │   ├── wechat-remote-publish.ts ← SSH 隧道管理
    │   ├── wechat-extend-config.ts  ← EXTEND.md 解析
    │   ├── wechat-image-loader.ts   ← 图片加载
    │   ├── wechat-image-processor.ts ← 图片处理（webp/jpeg/jimp）
    │   ├── md-to-wechat.ts     ← Markdown → 微信 HTML
    │   ├── package.json        ← @jsquash/webp, baoyu-md, jimp, socks
    │   └── bun.lock
    └── py/                     ← 小绿书发布（python3）
        ├── publish.py          ← 主入口
        ├── config.py           ← .env + EXTEND.md 读取
        └── format.py           ← 段落呼吸感处理（可选）
```

## 价值（保留这份说明的原因）

1. **唯一发布入口**：发任何东西到公众号都进这里，不再问"用哪个 skill"
2. **统一凭证**：一份 `.ds-skills/.env` 给两条路径用
3. **统一隧道**：家宽 IP 漂移问题一次解决，文章和小绿书都受益
4. **舍弃 browser**：避免 Chrome 自动化的脆弱性（编辑器 DOM 改版即坏）
