# Base Prompt Template

把下面的 `{{...}}` 占位符全部替换成 Step 1 选好的维度值和文章内容，然后落盘到 `prompts/NN-cover-[slug].md`。

模板用英文写（图像模型对英文 prompt 理解更准），但**标题保留原始中文**——不要翻译。

---

```
Create a cover image following these guidelines:

## Image Specifications

- **Type**: Cover image / Hero image for WeChat Official Account article
- **Aspect Ratio**: {{aspect_ratio}}

## Core Principles

- Ample whitespace, highlight core message, avoid cluttered layouts
- Main visual centered or offset left (reserve right side for title)
- Simplified silhouettes for any characters — NO realistic human faces
- Icon-based vocabulary: simple, recognizable icons over detailed illustrations

## Five Dimensions

### Type: {{type}}
{{type_description}}

### Palette: {{palette}}
{{palette_color_values}}
{{palette_decorative_hints}}

### Rendering: {{rendering}}
{{rendering_characteristics}}

### Text: {{text_level}}
{{text_level_description}}

### Mood: {{mood}}
{{mood_adjustments}}

## Title Text (render EXACTLY this Chinese text in the image)

{{title_chinese}}

- Render in {{font_style}} Chinese typeface
- Color: deep charcoal #2A2A2A (NOT pure black)
- Size: large but not screaming — let whitespace do the work
- Layout: {{title_layout}} lines max, broken at a natural reading point
- Letter spacing: slightly loose, never cramped
- {{subtitle_instruction}}

## Composition

- One dominant focal point ({{focal_element}})
- 1-2 micro-accents max — only if they don't clutter
- {{whitespace_percentage}}+ whitespace overall
- Background: {{background_color}}
- Zero photorealism, zero shading, zero 3D textures

## Mood Application

| Aspect | Adjustment |
|--------|-----------|
| Contrast | {{contrast_adjustment}} |
| Saturation | {{saturation_adjustment}} |
| Weight | {{weight_adjustment}} |

## Language

- Use Chinese for all text elements (matching the source title's language)
- Match punctuation style to Chinese conventions

## Hard Constraints

- NO realistic human faces, NO human bodies
- NO actual code text (don't write `console.log` — only iconic symbols if needed)
- NO English text anywhere except iconic symbols where the brief explicitly calls for them
- NO watermarks, NO QR codes, NO author handles, NO logos
- {{custom_constraints}}

---

Render now: a {{aspect_ratio}} {{palette}}-palette {{rendering}} cover image with {{focal_summary}}, generous whitespace, and the Chinese title "{{title_chinese}}" set in {{font_style}} sans-serif {{title_position}}.
```

---

## 填充字段速查

| 字段 | 说明 | 例 |
|---|---|---|
| `aspect_ratio` | 画幅 | `16:9`、`2.35:1`、`1:1` |
| `type` / `type_description` | 见 dimensions.md → Type 表 | `minimal` / `single focal element, generous whitespace (60%+)` |
| `palette` / `palette_color_values` / `palette_decorative_hints` | 见 dimensions.md → Palette 表 | `macaron` / hex 码列表 / 装饰提示 |
| `rendering` / `rendering_characteristics` | 见 dimensions.md → Rendering 表 | `flat-vector` / `clean geometric shapes, crisp outlines, solid fills` |
| `text_level` / `text_level_description` | 文字密度 | `title-only` / `single headline, 85% visual area` |
| `mood` / `contrast/saturation/weight` | 情绪 | `balanced` / `standard / standard / standard` |
| `font_style` | 字体倾向 | `clean modern sans-serif`、`handwritten`、`serif`、`bold display` |
| `title_chinese` | 用户原标题 | `写代码会像发短信一样简单` |
| `title_layout` | 1-3 行 | `2` |
| `subtitle_instruction` | 是否要副标题 | `NO subtitle, NO tags, NO English translation` |
| `focal_element` | 主焦点物体 | `a single pastel chat bubble containing </>` |
| `whitespace_percentage` | 留白比例 | `60%`、`40%`、`30%` |
| `background_color` | 背景色 | `cream off-white #FAF7F2`、`pure white`、`deep navy #1A2333` |
| `custom_constraints` | 特殊禁令 | `NO keyboard illustrations`、`NO phone illustrations` |
| `focal_summary` | 焦点一句话总结 | `a single pastel chat bubble with </>` |
| `title_position` | 标题位置 | `on the right two-thirds`、`centered`、`bottom-aligned` |
