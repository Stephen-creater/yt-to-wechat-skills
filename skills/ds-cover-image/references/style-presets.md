# 风格预设

`--style X` 等价于一次性指定一对 Palette + Rendering。如果再单独指定 `--palette` 或 `--rendering`，单独指定的值覆盖预设。

| Style 预设 | = Palette + Rendering | 适合场景 |
|---|---|---|
| `elegant` | elegant + hand-drawn | 商业评论、思想领导力，温度感 |
| `blueprint` | cool + digital | 技术架构、API、系统设计 |
| `chalkboard` | dark + chalk | 教育、教程、课堂感 |
| `dark-atmospheric` | dark + digital | 高端、电影感、剧照感技术文 |
| `editorial-infographic` | cool + digital | 数据 / 报告 / 编辑级信息图 |
| `fantasy-animation` | pastel + painterly | 童话、温柔、创意 |
| `flat-doodle` | pastel + flat-vector | 轻松、入门、可爱 |
| `intuition-machine` | retro + digital | 复古技术、80 年代 sci-fi |
| `minimal` | mono + flat-vector | 极简、纯粹、聚焦观点 |
| `nature` | earth + hand-drawn | 自然、旅行、生活笔记 |
| `notion` | mono + digital | 工具 / 效率类，极简专业 |
| `pixel-art` | vivid + pixel | 游戏、复古、致敬 |
| `playful` | pastel + hand-drawn | 教育、温柔、儿童感 |
| `retro` | retro + digital | 复古技术、致敬 80-90 年代 |
| `sketch-notes` | warm + hand-drawn | 笔记、个人成长、随性 |
| `vector-illustration` | retro + flat-vector | 复古向量插画 |
| `vintage` | retro + hand-drawn | 复古、怀旧、经典 |
| `warm` | warm + hand-drawn | 个人故事、温暖叙事 |
| `warm-flat` | warm + flat-vector | 温暖但干净的文章封面 |
| `hand-drawn-edu` | macaron + hand-drawn | 教育、教程、知识普及 |
| `watercolor` | earth + painterly | 艺术、水彩、自然抒情 |
| `poster-art` | retro + screen-print | 复古海报、丝网印刷感 |
| `mondo` | mono + screen-print | mondo 风格电影海报 |
| `art-deco` | elegant + screen-print | art deco 复古优雅海报 |
| `propaganda` | vivid + screen-print | 革命宣传画风格 |
| `cinematic` | duotone + screen-print | 电影海报、专辑封面、戏剧化 |

## 覆盖示例

```bash
# 用 blueprint 但换成手绘笔法
--style blueprint --rendering hand-drawn

# 用 elegant 但换成暖色配色
--style elegant --palette warm
```

显式 `--palette` / `--rendering` 永远覆盖预设。
