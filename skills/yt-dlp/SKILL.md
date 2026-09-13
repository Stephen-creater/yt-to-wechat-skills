---
name: yt-dlp
description: "用本机 yt-dlp 下载音视频、字幕或元数据；YouTube 素材归档按本技能约定。"
---

# yt-dlp

用本机 `yt-dlp` 处理音视频抓取、格式选择、字幕/封面/元数据保存和批量下载。官方项目是 `yt-dlp/yt-dlp`，一个支持大量站点的命令行音视频下载器。

## 先做判断

1. **默认行为**：用户只给了一个 YouTube 视频链接，没有明确说要什么时，默认执行”字幕 + 封面”一条龙——下载字幕转 Markdown、下载封面上传 OSS（PicGo）、封面图嵌入同一个 Markdown 文件。不需要额外确认。
2. 如果用户明确说只要视频、音频、元数据、播放列表或仅检查格式，按具体要求走，不执行默认一条龙。
3. 如果可能下载大量文件、超长直播、完整播放列表，先确认范围、目录和数量。
4. 涉及登录内容时优先用 `--cookies-from-browser` 或用户提供的 cookies 文件；不要让用户在命令里明文给账号密码。
5. 不协助绕过 DRM、付费墙、未授权访问或平台访问控制。普通登录态、公开视频、本人有权访问的内容可以处理。
6. 用户说”下载字幕”时，默认最终产物是中文命名的 Markdown 文档，直接写入 `03 素材管理/05 播客/`；`.srt/.vtt` 只作为临时中间文件，除非用户明确要原始字幕格式。
7. 用户说”下载封面 / 缩略图 / 封面图”时，默认把封面通过本机 PicGo 上传到 OSS，Markdown 中引用 OSS URL，本地不留图片；只有用户明确要求”保留本地””存本地””放到 assets”时，才落到与 Markdown 同目录的 `assets/`。
8. 实际下载前，复杂任务先用 `--simulate`、`--list-formats`、`--list-subs` 或 `--dump-json` 检查。

## 默认工作流：字幕 + 封面一条龙

用户给了 YouTube 链接、没有额外指定时，按以下顺序执行：

### 步骤 1：检查字幕可用性

```bash
yt-dlp --list-subs "URL"
```

### 步骤 2：并行下载字幕和封面

字幕下载到临时目录：

```bash
mkdir -p ".compile-runs/yt-dlp-subtitles" ".compile-runs/yt-dlp-thumbnails"
yt-dlp --skip-download --write-auto-subs --sub-langs "en-orig,en" --sub-format srt \
  -P ".compile-runs/yt-dlp-subtitles" \
  -o "%(upload_date>%Y%m%d)s 字幕 %(title).80B [%(id)s].%(ext)s" \
  "URL"
```

封面下载到临时目录：

```bash
yt-dlp --skip-download --write-thumbnail --convert-thumbnails jpg \
  -P ".compile-runs/yt-dlp-thumbnails" \
  -o "%(id)s 封面.%(ext)s" \
  "URL"
```

### 步骤 3：上传封面到 OSS

```bash
curl -s -X POST "http://127.0.0.1:36677/upload" \
  -H "Content-Type: application/json" \
  -d "{\"list\":[\"$(pwd)/.compile-runs/yt-dlp-thumbnails/VIDEO_ID 封面.jpg\"]}"
```

拿到返回的 `result[0]` 作为 `COVER_OSS_URL`。如果 PicGo 没启动或上传失败，停下报告，不继续。

### 步骤 4：生成 Markdown（字幕 + 封面合一）

```bash
python3 "99 技能/skills/yt-dlp/scripts/subtitle_to_markdown.py" \
  ".compile-runs/yt-dlp-subtitles/RAW_SUBTITLE.srt" \
  -o "03 素材管理/05 播客/YYYYMMDD-播客 中文可读主题 [VIDEO_ID].md" \
  --source "URL" \
  --title "ORIGINAL_ENGLISH_TITLE" \
  --display-title "YYYYMMDD-播客 中文可读主题 [VIDEO_ID]" \
  --video-id "VIDEO_ID" \
  --language "en-orig" \
  --subtitle-type "auto" \
  --cover-url "COVER_OSS_URL"
```

`--cover-url` 会把封面图以 `![封面](OSS_URL)` 的形式嵌入 Markdown 正文标题下方，同时写入 frontmatter 的 `cover` 字段。

### 步骤 5：清理临时文件

```bash
rm ".compile-runs/yt-dlp-thumbnails/VIDEO_ID 封面.jpg"
```

字幕原始 `.srt` 文件保留在 `.compile-runs/yt-dlp-subtitles/`，方便后续重新编译。

### 步骤 6：更新索引

写入内容 OS 后，更新 `INDEX.md` 和追加 `LOG.md`。

## 环境检查

```bash
command -v yt-dlp
yt-dlp --version
ffmpeg -version
ffprobe -version
```

`ffmpeg/ffprobe` 对合并音视频、转音频、嵌字幕、嵌封面、重封装很重要。遇到站点解析失败或 YouTube 变化，先建议更新：

```bash
yt-dlp -U
```

如果是 pip/Homebrew 安装，按安装方式更新，例如：

```bash
python -m pip install -U "yt-dlp[default]"
brew upgrade yt-dlp
```

## 通用输出模板

下载时默认给稳定文件名和目录，不把所有文件丢在当前目录：

```bash
yt-dlp -P "/path/to/output" -o "%(upload_date>%Y-%m-%d)s %(title).120B [%(id)s].%(ext)s" "URL"
```

常用字段：

```text
%(title)s
%(id)s
%(uploader)s
%(upload_date>%Y-%m-%d)s
%(playlist_index)03d
%(ext)s
```

播放列表建议加序号：

```bash
yt-dlp -P "/path/to/output" -o "%(playlist_index)03d - %(title).120B [%(id)s].%(ext)s" "PLAYLIST_URL"
```

## 检查与取元数据

查看标题、时长、URL，不下载：

```bash
yt-dlp --simulate --print "%(title)s | %(duration_string)s | %(webpage_url)s" "URL"
```

列出可下载格式：

```bash
yt-dlp -F "URL"
```

导出单条 JSON 元数据：

```bash
yt-dlp -J "URL" > info.json
```

播放列表只列条目，不深入解析每个视频：

```bash
yt-dlp --flat-playlist --print "%(playlist_index)s %(title)s %(url)s" "PLAYLIST_URL"
```

## 下载视频

下载最佳画质，自动合并音视频：

```bash
yt-dlp -P "/path/to/output" -o "%(title).120B [%(id)s].%(ext)s" "URL"
```

优先保存 mp4/H.264/AAC，兼顾兼容性：

```bash
yt-dlp -t mp4 -P "/path/to/output" -o "%(title).120B [%(id)s].%(ext)s" "URL"
```

指定最高 1080p：

```bash
yt-dlp -f "bv*[height<=1080]+ba/b[height<=1080]/b" --merge-output-format mp4 -P "/path/to/output" "URL"
```

只下载单个视频，避免 URL 同时带 playlist 时拉完整列表：

```bash
yt-dlp --no-playlist -P "/path/to/output" "URL"
```

保留 metadata、缩略图、字幕，并嵌入到文件：

```bash
yt-dlp -t mp4 --embed-metadata --embed-thumbnail --write-thumbnail --write-info-json --write-subs --sub-langs "zh.*,en.*" --embed-subs -P "/path/to/output" "URL"
```

## 提取音频

转 MP3：

```bash
yt-dlp -x --audio-format mp3 --audio-quality 0 -P "/path/to/output" -o "%(title).120B [%(id)s].%(ext)s" "URL"
```

保留更接近源站的音频格式，常用于播客/归档：

```bash
yt-dlp -f "ba/b" -x --audio-format m4a -P "/path/to/output" "URL"
```

使用内置 preset：

```bash
yt-dlp -t mp3 -P "/path/to/output" "URL"
```

## 字幕

列出字幕：

```bash
yt-dlp --list-subs "URL"
```

### 默认字幕工作流

用户只说“下载字幕”时：

1. 先运行 `yt-dlp --list-subs "URL"` 看是否有人工字幕和自动字幕。
2. 下载能稳定拿到的字幕即可：优先人工英文/原始字幕，其次自动英文/原始字幕；如果没有英文，就选列表里可用的一种字幕。不要主动请求简中自动翻译字幕。
3. 只有用户明确要求中文字幕时，才尝试一次 `zh-Hans`；如果出现 `HTTP Error 429: Too Many Requests`，立刻跳过中文，不要在同一轮反复重试。已有字幕可用就算完成。
4. 下载出的 `.srt/.vtt` 先放到 `.compile-runs/yt-dlp-subtitles/` 或其他临时目录，再转换成 Markdown。默认最终 `.md` 直接放到 `03 素材管理/05 播客/`。
5. Markdown 文件名用中文，让人一眼看懂；不要直接拿英文原版标题当文件名。一级标题 `#` 与文件名一致（去掉 `.md`）。英文原版标题写在正文信息区和 frontmatter。
6. Markdown 文件要带 frontmatter：`type: 字幕`、`title`、`source`、`created`、`status: 未处理`、`original_title`、`video_id`、`language`、`subtitle_type`。正文保留时间戳转写，方便后续编译。
7. 写入内容 OS 后，更新 `INDEX.md` 和追加 `LOG.md`。

默认下载可用英文/原始自动字幕并转成播客素材 Markdown：

```bash
mkdir -p ".compile-runs/yt-dlp-subtitles"
yt-dlp --skip-download --write-auto-subs --sub-langs "en-orig,en" --sub-format srt \
  -P ".compile-runs/yt-dlp-subtitles" \
  -o "%(upload_date>%Y%m%d)s 字幕 %(title).80B [%(id)s].%(ext)s" \
  "URL"

python3 "99 技能/skills/yt-dlp/scripts/subtitle_to_markdown.py" \
  ".compile-runs/yt-dlp-subtitles/RAW_SUBTITLE.srt" \
  -o "03 素材管理/05 播客/YYYYMMDD-播客 中文可读主题 [VIDEO_ID].md" \
  --source "URL" \
  --title "ORIGINAL_ENGLISH_TITLE" \
  --display-title "YYYYMMDD-播客 中文可读主题 [VIDEO_ID]" \
  --video-id "VIDEO_ID" \
  --language "en-orig" \
  --subtitle-type "auto"
```

用户明确要求中文字幕时，最多试一次：

```bash
yt-dlp --skip-download --write-auto-subs --sub-langs "zh-Hans" --sub-format srt \
  --sleep-requests 3 --force-ipv4 \
  -P ".compile-runs/yt-dlp-subtitles" \
  -o "%(upload_date>%Y%m%d)s 字幕 %(title).80B [%(id)s].%(ext)s" \
  "URL"
```

如果简中失败但已有其他字幕成功，对话里只需说明“简中自动翻译触发限流，已保留可用字幕 Markdown”，不要把任务判为失败。

### 原始字幕格式

只有用户明确要 `.srt/.vtt` 时，才把原始字幕作为最终产物。

下载人工字幕，不下载视频：

```bash
yt-dlp --skip-download --write-subs --sub-langs "zh.*,en.*" --sub-format "srt/vtt/best" -P "/path/to/output" "URL"
```

下载自动字幕：

```bash
yt-dlp --skip-download --write-auto-subs --sub-langs "zh.*,en.*" --sub-format "srt/vtt/best" -P "/path/to/output" "URL"
```

把字幕嵌入 mp4/mkv：

```bash
yt-dlp --write-subs --sub-langs "zh.*,en.*" --embed-subs -P "/path/to/output" "URL"
```

## 封面 / 缩略图

### 默认封面工作流：上传 OSS，本地不留图

用户说“下载封面 / 缩略图 / 封面图”时，默认走 PicGo / OSS：

1. 用 `yt-dlp --skip-download --write-thumbnail --convert-thumbnails jpg` 把封面下载到临时目录（如 `.compile-runs/yt-dlp-thumbnails/`），不要直接落到 `03 素材管理/` 之下。
2. 临时文件名加 `video_id` 或日期前缀，避免 OSS 对象名冲突（不要直接用 `cover.jpg`、`thumbnail.jpg` 这种通用名）。
3. 把临时图片 POST 到本机 PicGo（默认监听 `http://127.0.0.1:36677/upload`），拿回 OSS URL。
4. 在 Markdown 中用 OSS URL 引用封面，不要写本地相对路径或 YouTube 原始 URL。
5. 上传成功后立即删除临时图片，本地不留封面文件。
6. PicGo 没启动或上传失败时，停下报告，不要静默回退到本地存图。

下载封面到临时目录：

```bash
mkdir -p ".compile-runs/yt-dlp-thumbnails"
yt-dlp --skip-download --write-thumbnail --convert-thumbnails jpg \
  -P ".compile-runs/yt-dlp-thumbnails" \
  -o "%(id)s 封面.%(ext)s" \
  "URL"
```

通过 PicGo 上传到 OSS：

```bash
curl -s -X POST "http://127.0.0.1:36677/upload" \
  -H "Content-Type: application/json" \
  -d "{\"list\":[\"$(pwd)/.compile-runs/yt-dlp-thumbnails/VIDEO_ID 封面.jpg\"]}"
```

PicGo 必须用绝对路径。返回结构示例：

```json
{"success": true, "result": ["https://oss.example.com/yt-dlp-thumbnails/VIDEO_ID-封面.jpg"]}
```

取 `result[0]` 作为 OSS URL 写入 Markdown：

```markdown
![封面](https://oss.example.com/yt-dlp-thumbnails/VIDEO_ID-封面.jpg)
```

上传成功后清理临时文件：

```bash
rm ".compile-runs/yt-dlp-thumbnails/VIDEO_ID 封面.jpg"
```

PicGo 检查与排障：

```bash
curl -s -o /dev/null -w "%{http_code}\n" -X POST "http://127.0.0.1:36677/upload" \
  -H "Content-Type: application/json" -d '{"list":[]}'
```

200 但 `success:false` 通常是路径错误或图床配置问题；连接失败说明 PicGo 客户端没启动，先打开 PicGo 再重试。

### 保留本地封面（仅在用户明确要求时）

只有用户说“保留本地”“存本地”“放到 assets”时，才把封面落到与 Markdown 同目录的 `assets/` 子目录：

```bash
yt-dlp --skip-download --write-thumbnail --convert-thumbnails jpg \
  -P "03 素材管理/05 播客/assets" \
  -o "VIDEO_ID 封面.%(ext)s" \
  "URL"
```

Markdown 中用相对路径引用：`![封面](assets/VIDEO_ID%20封面.jpg)`。

## 播放列表与批量

下载播放列表的指定条目：

```bash
yt-dlp -I "1:10,15,20" -P "/path/to/output" -o "%(playlist_index)03d - %(title).120B [%(id)s].%(ext)s" "PLAYLIST_URL"
```

从 URL 文件批量下载：

```bash
yt-dlp -a urls.txt -P "/path/to/output" --download-archive archive.txt -i
```

`--download-archive archive.txt` 会记录已下载条目，适合反复同步频道或播放列表。

## 登录态、限速与稳定性

从浏览器读取 cookies：

```bash
yt-dlp --cookies-from-browser chrome "URL"
yt-dlp --cookies-from-browser safari "URL"
```

使用 cookies 文件：

```bash
yt-dlp --cookies "/path/to/cookies.txt" "URL"
```

网络不稳时：

```bash
yt-dlp -R 20 --fragment-retries 20 --retry-sleep "fragment:exp=1:20" -N 4 -P "/path/to/output" "URL"
```

需要温和访问时：

```bash
yt-dlp --sleep-requests 1 --sleep-interval 5 --max-sleep-interval 20 -P "/path/to/output" "URL"
```

断点续传通常默认开启；如果遇到残留 `.part` 文件，优先重跑原命令。

## 片段、章节与直播

下载指定时间段：

```bash
yt-dlp --download-sections "*00:01:30-00:03:00" -P "/path/to/output" "URL"
```

按章节切分：

```bash
yt-dlp --split-chapters -P "/path/to/output" "URL"
```

直播从头下载仅在部分站点可用，先说明实验性：

```bash
yt-dlp --live-from-start -P "/path/to/output" "LIVE_URL"
```

等待预约直播开播：

```bash
yt-dlp --wait-for-video 60-300 -P "/path/to/output" "LIVE_URL"
```

## 常见排障

- 先跑 `yt-dlp -v "URL"`，保存完整错误信息。
- 格式不可用：跑 `yt-dlp -F "URL"`，再用 `-f` 选择存在的格式。
- 合并失败：确认 `ffmpeg -version` 可用，必要时加 `--ffmpeg-location "/path/to/ffmpeg"`。
- 站点解析失败：更新 `yt-dlp`，或尝试 `--cookies-from-browser`。
- 文件名异常：加 `--restrict-filenames` 或调整 `-o` 模板。
- 播放列表误下载：加 `--no-playlist`。
- 只想测试命令：加 `--simulate`。

## 汇报给用户

执行后简要说明：

- 保存到了哪个目录。
- 下载/导出的文件数量和类型。
- 使用了哪些关键选项，例如格式、字幕语言、cookies、archive。
- 下载字幕时，说明最终 Markdown 文件路径在 `03 素材管理/05 播客/`；如果用户要求中文且触发 429，说明已跳过中文并保留可用字幕。
- 下载封面时，默认报告 PicGo 返回的 OSS URL，并说明临时本地文件已清理；如用户明确要求保留本地，说明本地保留路径。如果 PicGo 不可用导致失败，明确说原因，不要悄悄落到本地。
- 如果失败，给出下一步最小排查命令。
