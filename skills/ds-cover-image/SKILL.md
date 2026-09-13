---
name: ds-cover-image
description: "在 ds 微信发布流程中生成公众号封面；也用于明确指定大圣封面工具的请求。"
version: 1.0.0
metadata:
  requires:
    skills:
      - ds-imagine
---

# ds-cover-image

把"为这篇公众号文章配一张封面图"这件事，拆成 5 个可控维度。

每次出图都走同一套模板：分析标题 → 选维度 → 写 prompt → 调 ds-imagine。维度可控，结果可复现。

## 输入

最少需要：**文章标题**。

可选：
- 正文或摘要（用于自动选维度更准）
- 显式指定的维度参数（覆盖自动选择）
- 风格预设 `--style xxx`（一次性确定配色+笔法）
- 画幅 `--aspect 16:9 | 2.35:1 | 1:1`
- 参考图 `--ref <files...>`

## 5 个维度

| 维度 | 可选值 | 默认 |
|---|---|---|
| **Type** 构图 | hero / conceptual / typography / metaphor / scene / minimal | auto |
| **Palette** 配色 | warm / elegant / cool / dark / earth / vivid / pastel / mono / retro / duotone / macaron | auto |
| **Rendering** 笔法 | flat-vector / hand-drawn / painterly / digital / pixel / chalk / screen-print | auto |
| **Text** 文字密度 | none / title-only / title-subtitle / text-rich | title-only |
| **Mood** 情绪强度 | subtle / balanced / bold | balanced |

附加：
- **Font** 字体：clean / handwritten / serif / display（默认 clean）
- **Aspect** 画幅：默认 16:9（公众号封面通用），可选 2.35:1（电影感）/ 1:1（小绿书/朋友圈卡片）

维度详解：[references/dimensions.md](references/dimensions.md)
自动选择规则：[references/auto-selection.md](references/auto-selection.md)
风格预设组合：[references/style-presets.md](references/style-presets.md)

## 工作流

```
Step 0: 检查 ds-imagine 可用（key + EXTEND.md）
Step 1: 分析标题 + 正文 → 自动选 5 维度
Step 2: 与用户确认维度（除非 --quick）
Step 3: 写完整 prompt → 落盘到 prompts/
Step 4: 调 ds-imagine 出图
Step 5: 展示结果，询问是否需要迭代
```

### Step 0: 前置检查（BLOCKING）

调用 ds-imagine 之前先确认：
- 至少一个 image API key 可用（OPENAI_API_KEY / DASHSCOPE_API_KEY / ARK_API_KEY 等）
- `~/.ds-skills/ds-imagine/EXTEND.md` 或项目级 EXTEND.md 已存在

如果 EXTEND.md 不存在，先让 ds-imagine 跑首次设置，再回到本 skill 继续。

### Step 1: 分析标题 + 选维度

读懂标题的意图：
- **主题**：技术 / 故事 / 观点 / 教程 / 产品 / 哲思 / 个人成长
- **语气**：严肃 / 轻快 / 温暖 / 锋利 / 治愈 / 反讽
- **核心视觉隐喻**：标题里有没有具体物体可视化（"短信"→ 气泡，"航海"→ 帆船，"剥洋葱"→ 洋葱）

按 [auto-selection.md](references/auto-selection.md) 的对照表自动选维度。给不出明确答案的维度，留给 Step 2 让用户选。

### Step 2: 确认维度 ⚠️

**默认必须确认**，例外：
- `--quick` 参数
- 用户明确说"直接生成""不用确认""按默认出图"

确认时用 `AskUserQuestion`，把所有可调维度合并到一次提问。展示当前自动选择 + 1-2 个备选方向（不要全 11 种都列出来）。

### Step 3: 写 prompt 文件

用 [references/base-prompt-template.md](references/base-prompt-template.md) 作为骨架，把 5 维度变量填进去。

落盘路径：**当前任务的输出目录** + `/prompts/NN-cover-[slug].md`

slug 规则：2-4 个英文词，kebab-case；同名冲突加 `-YYYYMMDD-HHMMSS` 后缀。

**Prompt 文件是必需品**，不是可选。理由：
- 出图失败可复用 prompt 重试
- 换 backend 不用重新写
- 留下可追溯的生成记录

### Step 4: 出图

调 ds-imagine：

```bash
bun "<base>/99 技能/skills/ds-imagine/scripts/main.ts" \
  --promptfiles "<output-dir>/prompts/NN-cover-[slug].md" \
  --image "<output-dir>/cover.png" \
  --ar <aspect> \
  --quality 2k
```

模型优先级（处理中文标题渲染）：
1. `gpt-image-2`（OpenAI，中文字渲染最稳）
2. `seedream-4-0`（豆包，中文 OK）
3. `jimeng`（即梦，中文 OK，无 ref 支持）
4. 其他模型对中文支持差，标题容易糊或乱码，仅在没有上述 key 时降级使用

### Step 5: 展示 + 迭代

用 Read 工具把生成的 PNG 直接读出来给用户看。

附上常见迭代方向供用户挑：
- 字号 / 字体调整
- 焦点物体换位置
- 配色换方向
- 加副标题 / tag
- 换画幅

## 输出目录

默认放在：`./cover-image/<topic-slug>/`（相对当前工作目录）

结构：
```
cover-image/<topic-slug>/
├── prompts/
│   └── 01-cover-<slug>.md   # 完整 prompt 记录
├── refs/                     # 用户提供的参考图（如有）
└── cover.png                 # 最终封面
```

如果用户明确指定了输出路径，遵循指定。

## 硬性禁令

⛔ **不要用 SVG / HTML / Canvas 替代位图**。即使画面看起来像图标可以用 SVG 画，本 skill 只产 PNG。

⛔ **不要用 ImageMagick / Pillow / Canvas 改已生成图片的文字**。文字渲染不对就重生成、换变体或换 backend，不要在像素层贴新字盖旧字。

⛔ **不要发明或修改标题**。用户给的标题就是标题，不要润色、不要加副标题除非用户要求。

⛔ **不要画真实人脸**。如果画面需要人，用简笔/剪影/卡通化处理。

## 公众号场景的默认偏好

| 场景 | 推荐组合 |
|---|---|
| 技术 / AI / 工具向 | `--style blueprint` (cool + digital) 或 `--style minimal` |
| 个人故事 / 成长 / 感悟 | `--style warm` (warm + hand-drawn) 或 `--style sketch-notes` |
| 观点 / 反思 / 锋利评论 | `--style minimal` (mono + flat-vector) + Type=typography |
| 教程 / 拆解 / 知识 | `--style hand-drawn-edu` (macaron + hand-drawn) |
| 产品发布 / 大事件 | `--style cinematic` (duotone + screen-print) |

公众号默认 16:9，因为微信文章卡片预览和文中头图都用这个比例。要做小绿书/朋友圈卡才换 1:1。

## 风格预设（--style）

| 预设 | = Palette + Rendering |
|---|---|
| `elegant` | elegant + hand-drawn |
| `blueprint` | cool + digital |
| `chalkboard` | dark + chalk |
| `minimal` | mono + flat-vector |
| `notion` | mono + digital |
| `sketch-notes` | warm + hand-drawn |
| `warm-flat` | warm + flat-vector |
| `hand-drawn-edu` | macaron + hand-drawn |
| `cinematic` | duotone + screen-print |
| `vintage` | retro + hand-drawn |

完整列表：[references/style-presets.md](references/style-presets.md)

## 与其它 skill 的关系

- 出图依赖 **ds-imagine**：本 skill 只管 prompt 和工作流，不管底层 API 调用
- 与 **ljg-card** 区分：ljg-card 出"内容卡片"（多种模具：长卡、信息图、视觉笔记、漫画等），ds-cover-image 只出"文章封面图"，更聚焦
- 与 **baoyu-article-illustrator** 区分：那个是给文章中间配多张插图，本 skill 只管头图

## 致谢

本 skill 的 5 维度方法论改编自宝玉（@JimLiu）开源的 [baoyu-cover-image](https://github.com/JimLiu/baoyu-skills/tree/main/skills/baoyu-cover-image)。本地版本针对大圣公众号场景做了精简和默认值调整。
