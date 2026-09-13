---
name: ds-yt-publish-wechat
version: v0.1.3
language: zh-CN
description: "将 YouTube 内容转成公众号文章，配封面并发布到草稿箱。"
metadata:
  requires:
    skills:
      - ds-yt-to-wechat-content
      - ds-cover-image
      - ds-post-to-wechat
---

# ds-yt-publish-wechat

你是大圣的微信公众号全自动发布编排器。

本 skill 只做上层串联，不把底层能力写死在自己身上：

```text
YouTube / 转述摘要
→ ds-yt-to-wechat-content 生成公众号稿
→ ds-cover-image 生成 2.35:1 封面
→ PicGo / OSS 上传封面
→ 回填同一篇文章的 frontmatter.cover_image
→ ds-post-to-wechat 发布到草稿箱
```

目标是让用户给一个 YouTube 链接后，不再手工触发三四个 skill。

## 先读

每次执行前先读取：

```text
CLAUDE.md
INDEX.md
LOG.md 最近 100-200 行
99 技能/skills/ds-yt-to-wechat-content/SKILL.md
99 技能/skills/ds-cover-image/SKILL.md
99 技能/skills/ds-post-to-wechat/SKILL.md
```

如果输入是已有文章路径，还要读取：

```text
01 内容创作/README.md
```

## 模式

### mode: yt_to_draft（默认）

输入是 YouTube URL、YouTube 字幕 Markdown、播客转述摘要路径，或一篇已经由 `ds-yt-to-wechat-content` 生成的公众号稿。

| 输入 | 动作 |
|---|---|
| YouTube URL | 调用 `ds-yt-to-wechat-content`，由它先处理内容生成所需的萃取，再输出公众号稿 |
| `03 素材管理/05 播客/*-转述摘要*.md` | 调用 `ds-yt-to-wechat-content` 直接生成公众号稿 |
| `01 内容创作/公众号/*.md` | 跳过内容生成，从封面步骤继续 |

后续模式可以扩展为：

| 模式 | 预留用途 |
|---|---|
| `article_to_draft` | 已有公众号稿 → 生成封面 → 发布草稿 |
| `draft_only` | 已有文章且已有 `cover_image` → 只发布草稿 |

v0.1 只完整实现 `yt_to_draft`。

## 输出契约

最终只交付一篇公众号文章和一个微信草稿：

```text
01 内容创作/公众号/YYYYMMDD-播客主题.md
微信公众号草稿箱 draft
```

封面图不在 `01 内容创作/公众号` 下新建文件夹或长期保存本地文件。出图过程只允许使用 `.compile-runs/ds-yt-publish-wechat/` 作为临时工作目录；最终权威地址保留在文章 frontmatter 的 `cover_image`。

为了让大圣打开 Markdown 时能直接预览封面，文章正文区的 H1 上方可以有一行公众号封面预览图：

```markdown
![公众号封面](https://.../xxx.png)

# 公众号标题
```

这张图只服务文档预览，不服务微信正文发布。`ds-post-to-wechat` 发布前必须自动剥离 H1 前的公众号封面预览，正文里不能出现这张封面图。

回填后的文章必须满足：

```yaml
---
title: "公众号标题"
cover_title: "给 ds-cover-image 的封面标题"
cover_image: "https://.../xxx.png"
...
---

![公众号封面](https://.../xxx.png)

# 公众号标题
```

字段约定：

- `cover_title`：由 `ds-yt-to-wechat-content` 生成，作为封面出图标题输入。
- `cover_image`：唯一权威公众号封面字段，写 OSS URL；`ds-post-to-wechat` 会把它下载并上传为微信永久素材。
- H1 上方的 `![公众号封面](cover_image)` 只用于 Markdown 预览，发布前必须剥离，不计入微信正文图片。
- `cover_image` 只服务公众号封面 / `thumb_media_id`，不要在 H1 下方或正文内容区再次插入。
- 不写 `cover` / `image` / `featureImage` 等兼容字段，避免歧义。

## 工作流

### Step 0：预检

检查：

1. 输入存在且可解析。
2. PicGo 本地服务可用：

```bash
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:36677/upload
```

3. `ds-post-to-wechat` 的 `.ds-skills/.env` 和 `.ds-skills/ds-post-to-wechat/EXTEND.md` 可用。
4. `ds-imagine` 的 EXTEND.md 和至少一个 image API key 可用。

如果 PicGo、图片生成或微信发布凭证不可用，停下报告，不伪造封面、不静默降级为正文首图。

### Step 1：生成公众号稿

调用 `ds-yt-to-wechat-content`，完全按它自己的 SKILL.md 执行。

完成后必须拿到一个文章路径：

```text
01 内容创作/公众号/YYYYMMDD-主题.md
```

检查文章 frontmatter 至少有：

```yaml
title: "..."
cover_title: "..."
digest: "..."
```

如果缺 `cover_title`，回到 `ds-yt-to-wechat-content` 的标题与封面标题规则补齐，不要自己临时截标题。

### Step 2：生成 2.35:1 封面

调用 `ds-cover-image`，传入：

```text
标题：frontmatter.cover_title
正文上下文：文章 title + digest + 正文主线
画幅：--aspect 2.35:1
模式：--quick / 不停下确认
```

临时输出放到：

```text
.compile-runs/ds-yt-publish-wechat/YYYYMMDD-HHMMSS-<slug>-cover.png
.compile-runs/ds-yt-publish-wechat/prompts/YYYYMMDD-HHMMSS-<slug>-prompt.md
```

文件名必须带日期时间或主题 slug，避免 PicGo / OSS 出现 `cover.png` 这类冲突名。

### Step 3：上传 OSS 并回填文章

生成封面后，立刻通过 PicGo 上传 OSS，并回填到同一篇文章：

```bash
python3 "99 技能/skills/ds-yt-publish-wechat/scripts/attach_cover_image.py" \
  "01 内容创作/公众号/YYYYMMDD-主题.md" \
  --image ".compile-runs/ds-yt-publish-wechat/YYYYMMDD-HHMMSS-<slug>-cover.png" \
  --delete-local
```

脚本会：

1. POST 本地封面到 PicGo。
2. 取返回的 OSS URL。
3. 写入 frontmatter `cover_image`。
4. 在 H1 上方写入或替换 `![公众号封面](cover_image)` 作为 Markdown 预览图。
5. 可选删除本地临时 PNG。

不要新建新的文章文档，不要把封面长期放到文章旁边的 `封面/` 或 `assets/` 目录，也不要把公众号封面图放到 H1 下方当正文首图。

### Step 4：发布到公众号草稿箱

调用 `ds-post-to-wechat` 的文章发布路径：

```bash
BUN=$(command -v bun || echo "npx -y bun")
SKILL="$HOME/.claude/skills/ds-post-to-wechat"  # Codex 用户改成 $HOME/.codex/skills/ds-post-to-wechat

$BUN "$SKILL/scripts/ts/wechat-api.ts" \
  "01 内容创作/公众号/YYYYMMDD-主题.md" \
  --theme default
```

默认走 `remote-api` 隧道，由 `ds-post-to-wechat` 的 EXTEND.md 控制。不要把正文第一张 YouTube 图当封面；必须使用 Step 3 回填的 `cover_image`。发布渲染时必须确认 H1 前的公众号封面预览已经被剥离，正文图片数量不应因为封面预览增加。

### Step 5：总报告

完成后向用户报告：

```markdown
## ds-yt-publish-wechat 结果

- 输入：{YouTube URL 或素材路径}
- 文章：{绝对路径}
- 公众号标题：{title}
- 封面标题：{cover_title}
- 封面 OSS：{cover_image}
- 草稿箱：{draft media_id 或返回链接}
- 子 skill：ds-yt-to-wechat-content / ds-cover-image / ds-post-to-wechat
- INDEX.md 已更新：是 / 否
- LOG.md 已追加：是 / 否
```

## 失败处理

| 失败位置 | 处理 |
|---|---|
| 内容生成失败 | 停止，报告 `ds-yt-to-wechat-content` 的失败原因 |
| 缺 `cover_title` | 回到内容稿补齐；不要拿公众号标题机械截短 |
| 出图失败 | 停止，保留文章稿，不发布 |
| PicGo / OSS 上传失败 | 停止，保留文章稿，不写本地封面路径，不发布 |
| `cover_image` 回填失败 | 停止，不发布 |
| 微信 API 发布失败 | 保留文章和 OSS 封面，报告 `ds-post-to-wechat` 的错误码和最小排查动作 |

## 硬性约束

- 不修改 `03 素材管理/01-11` 已有原始素材。
- 不写入 `02 选题管理`。
- 不写入 `08 一人公司学员画像`。
- 不复制底层 skill 的细节规则；执行每步前读取对应 SKILL.md 真源。
- 任何一步失败都停止后续步骤，不带病发布。
- 创建或修改文章、skill 或桥接入口后，必须更新 `INDEX.md` 并追加 `LOG.md`。
