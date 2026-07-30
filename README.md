# YouTube → 微信公众号 Skill 包

把一条 YouTube 链接，一路自动化成微信公众号草稿箱里的图文文章。

```
YouTube URL
  → 抓字幕（yt-dlp）
  → 中文转述摘要（yt-内容萃取）
  → 大圣风格公众号稿（ds-yt-to-wechat-content）
  → 2.35:1 封面图（ds-cover-image + ds-imagine）
  → 发到公众号草稿箱（ds-post-to-wechat）
```

跟 Claude Code 或 Codex 说一句「这个 YouTube 写成公众号：<URL>」即可。

---

## 一、包里有什么

```
yt-to-wechat-skills/
├── README.md                       ← 你正在看的文件
├── INSTALL.sh                      ← 一键安装到 Claude Code / Codex
├── skills/                         ← 7 个 skill 真源
│   ├── ds-yt-publish-wechat/       ← 顶层编排：YT → 公众号草稿一条龙
│   ├── ds-yt-to-wechat-content/    ← 核心：YT 转大圣风格公众号稿
│   ├── ds-cover-image/             ← 封面图工作流
│   ├── ds-imagine/                 ← 底层图片生成（多家 API）
│   ├── ds-post-to-wechat/          ← 微信公众号发布
│   ├── yt-内容萃取/                ← YT 字幕转中文结构化摘要
│   └── yt-dlp/                     ← YT 字幕/封面抓取
└── config-templates/               ← 配置模板（密钥都已脱敏）
    ├── .env.example
    ├── ds-post-to-wechat/
    │   ├── EXTEND.md.example
    │   └── footer.html.example
    └── ds-imagine/
        └── EXTEND.md.example
```

---

## 二、安装 skill

### 方式 A：一键脚本（推荐）

```bash
cd yt-to-wechat-skills
bash INSTALL.sh
```

脚本会问你装到 Claude Code、Codex 还是两个都装，然后把 `skills/` 下的 7 个目录用**软链接**（symlink）放到对应位置。改 SKILL.md 不用重装。

### 方式 B：手动复制

```bash
# Claude Code 用户
cp -R skills/* ~/.claude/skills/

# Codex 用户
cp -R skills/* ~/.codex/skills/
```

---

## 三、配置密钥（必做）

配置文件统一放在 `.ds-skills/` 下。两种位置任选其一：

- **项目级**（推荐）：`<你的写作项目根目录>/.ds-skills/`
- **用户级**（兜底）：`~/.ds-skills/`

两个都存在时项目级优先。

### Step 1：填密钥

```bash
# 假设你用项目级
mkdir -p ~/你的写作项目/.ds-skills/ds-post-to-wechat
mkdir -p ~/你的写作项目/.ds-skills/ds-imagine

cp config-templates/.env.example                                  ~/你的写作项目/.ds-skills/.env
cp config-templates/ds-post-to-wechat/EXTEND.md.example           ~/你的写作项目/.ds-skills/ds-post-to-wechat/EXTEND.md
cp config-templates/ds-post-to-wechat/footer.html.example         ~/你的写作项目/.ds-skills/ds-post-to-wechat/footer.html
cp config-templates/ds-imagine/EXTEND.md.example                  ~/你的写作项目/.ds-skills/ds-imagine/EXTEND.md
```

然后**打开这 4 个文件**，按文件里的注释填值：

| 文件 | 关键字段 |
|---|---|
| `.env` | `WECHAT_APP_ID`、`WECHAT_APP_SECRET`、`OPENAI_API_KEY` |
| `ds-post-to-wechat/EXTEND.md` | `default_author`（你的笔名/公众号名） |
| `ds-post-to-wechat/footer.html` | 文末签名（个人介绍 + 微信号 CTA） |
| `ds-imagine/EXTEND.md` | `save_dir`（图片保存目录） |

### Step 2：申请密钥

| 密钥 | 哪里申请 |
|---|---|
| `WECHAT_APP_ID` / `WECHAT_APP_SECRET` | 登录 mp.weixin.qq.com →「开发」→「基本配置」→ AppSecret 点「重置」生成（只显示一次） |
| 公众号 IP 白名单 | 同一页面：把你本机的公网 IP 加进去（不加会报 `40164 invalid ip`） |
| `OPENAI_API_KEY` | 自己有 OpenAI/Azure 账号最稳；没有的话买一个 OpenAI 兼容中转站的 key，`OPENAI_BASE_URL` 改成中转站 v1 地址 |

> **不知道本机公网 IP？** 浏览器搜「我的 IP」或终端 `curl ifconfig.me`。如果家宽 IP 经常变，看下面「可选：SSH 隧道」。

---

## 四、前置工具（系统级）

| 工具 | 用途 | 装法 |
|---|---|---|
| `yt-dlp` | 抓 YT 字幕 | `brew install yt-dlp` 或 `pip install -U yt-dlp` |
| `ffmpeg` | 字幕/媒体处理 | `brew install ffmpeg` |
| `bun` | 跑 wechat-api.ts（也可用 npx 兜底） | `brew install oven-sh/bun/bun` |
| `python3` + `requests` + `PySocks` | 跑小绿书发布 | `pip install requests PySocks` |
| **PicGo**（可选） | 把封面上传 OSS 后再发微信 | 装 PicGo 客户端，绑定你的 OSS/七牛/SM.MS |

**PicGo 不是必须**。如果不用，封面会直接从本地上传到微信永久素材库；要 OSS 中转就装它，启动后监听 `http://127.0.0.1:36677`。

---

## 五、第一次运行

打开 Claude Code 或 Codex，进入你**配好 `.ds-skills/` 的目录**，对话：

```
帮我把这个 YouTube 写成公众号草稿：
https://www.youtube.com/watch?v=XXXXXXXXXXX
```

Claude/Codex 会自动调用 `ds-yt-publish-wechat`，跑完整条流水线。

成功后，登录 mp.weixin.qq.com → 草稿箱，能看到刚发的草稿。

---

## 六、可选：SSH 隧道（家宽 IP 漂移时用）

如果你的本机 IP 经常变、不想每次去公众号后台改白名单，可以买一台便宜的 VPS 做固定出口：

1. 把 VPS 的固定公网 IP 加到公众号 IP 白名单（替代本机 IP）
2. 编辑 `.ds-skills/ds-post-to-wechat/EXTEND.md`：
   - `default_publish_method` 改成 `remote-api`
   - 取消注释并填好 `remote_publish_*` 各项
3. 第一次会用你的 SSH key 自动建隧道，所有微信 API 调用都从 VPS 出口

不需要这套就跳过——本地直连完全够用。

---

## 七、常见问题

| 现象 | 解决 |
|---|---|
| `40164 invalid ip` | 本机出口 IP 没加白名单，去 mp.weixin.qq.com 加 |
| `40001 invalid credential` | AppSecret 在公众号后台被重置了，更新 `.env` |
| `yt-dlp` 拉字幕报 `HTTP 429` | YT 限流，等几分钟重试；或换网络 |
| 封面没渲染 | 检查 `OPENAI_API_KEY` 是否有效、模型是否支持中文 |
| 发布脚本找不到密钥 | 确认 `.ds-skills/` 在 cwd 或 `~/` 下，目录名拼写无误 |
| `bun` 找不到 | 不装也行，脚本会用 `npx -y bun` 兜底，第一次慢一点 |

---

## 八、致谢

这套 skill 在以下开源项目基础上做了大圣公众号场景的定制：

- 微信发布 TS 部分：[@JimLiu/baoyu-skills](https://github.com/JimLiu/baoyu-skills) 的 `baoyu-post-to-wechat`
- 封面图 5 维度方法论：同样来自宝玉的 `baoyu-cover-image`

---

有问题随时找大圣群里问。
