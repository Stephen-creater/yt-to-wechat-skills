import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import process from "node:process";

import {
  cleanSummaryText,
  extractSummaryFromBody,
  extractTitleFromMarkdown,
  parseFrontmatter,
  renderMarkdownDocument,
  replaceMarkdownImagesWithPlaceholders,
  resolveColorToken,
  resolveContentImages,
  serializeFrontmatter,
  stripWrappingQuotes,
} from "baoyu-md";
import { FONT_FAMILY_MAP } from "baoyu-md/src/constants.ts";

function resolveFontFamily(value: string | undefined): string | undefined {
  if (!value) return undefined;
  return FONT_FAMILY_MAP[value] ?? value;
}

interface ImageInfo {
  placeholder: string;
  localPath: string;
  originalPath: string;
}

interface ParsedResult {
  title: string;
  author: string;
  summary: string;
  htmlPath: string;
  contentImages: ImageInfo[];
}

function stripWechatIgnoreBlocks(markdown: string): string {
  return markdown.replace(
    /\n?<!--\s*wechat:ignore:start\s*-->[\s\S]*?<!--\s*wechat:ignore:end\s*-->\n?/gi,
    "\n",
  );
}

function stripCoverPreviewBeforeH1(markdown: string, coverImage?: string): string {
  const h1Match = markdown.match(/^#\s+.+$/m);
  if (!h1Match || h1Match.index === undefined) return markdown;

  const beforeH1 = markdown.slice(0, h1Match.index);
  const afterH1 = markdown.slice(h1Match.index);
  const normalizedCover = stripWrappingQuotes(coverImage ?? "").trim();

  const cleanedBeforeH1 = beforeH1.replace(
    /^!\[([^\]]*)\]\(([^)]+)\)\s*\n*/gim,
    (full, alt: string, src: string) => {
      const normalizedSrc = src.trim().replace(/^<(.+)>$/, "$1");
      const isCoverAlt = /^(公众号封面|cover image)/i.test(alt.trim());
      const isCoverImage = normalizedCover && normalizedSrc === normalizedCover;
      return isCoverAlt || isCoverImage ? "" : full;
    },
  );

  if (!cleanedBeforeH1.trim()) return afterH1.replace(/^\n+/, "");
  return cleanedBeforeH1.replace(/\s+$/, "") + "\n\n" + afterH1.replace(/^\n+/, "");
}

export async function convertMarkdown(
  markdownPath: string,
  options?: { title?: string; theme?: string; color?: string; citeStatus?: boolean; fontFamily?: string },
): Promise<ParsedResult> {
  const baseDir = path.dirname(markdownPath);
  const content = fs.readFileSync(markdownPath, "utf-8");
  const citeStatus = options?.citeStatus ?? true;

  const { frontmatter, body: rawBody } = parseFrontmatter(content);
  const ignoredBody = stripWechatIgnoreBlocks(rawBody);
  const body = stripCoverPreviewBeforeH1(
    ignoredBody,
    frontmatter.cover_image ?? frontmatter.coverImage ?? frontmatter.featureImage ?? frontmatter.cover ?? frontmatter.image,
  );

  let title = stripWrappingQuotes(options?.title ?? "")
    || stripWrappingQuotes(frontmatter.title ?? "")
    || extractTitleFromMarkdown(body);
  if (!title) {
    title = path.basename(markdownPath, path.extname(markdownPath));
  }

  const author = stripWrappingQuotes(frontmatter.author ?? "");
  const frontmatterSummary = stripWrappingQuotes(frontmatter.digest ?? "")
    || stripWrappingQuotes(frontmatter.description ?? "")
    || stripWrappingQuotes(frontmatter.summary ?? "");
  let summary = cleanSummaryText(frontmatterSummary);
  if (!summary) {
    summary = extractSummaryFromBody(body, 120);
  }

  const { images, markdown: rewrittenBody } = replaceMarkdownImagesWithPlaceholders(
    body,
    "WECHATIMGPH_",
  );
  const rewrittenMarkdown = `${serializeFrontmatter(frontmatter)}${rewrittenBody}`;

  const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), "wechat-article-images-"));
  const htmlPath = path.join(tempDir, "temp-article.html");

  console.error(
    `[md-to-wechat] Rendering markdown with theme: ${options?.theme ?? "default"}${options?.color ? `, color: ${options.color}` : ""}, citeStatus: ${citeStatus}`,
  );

  const { html } = await renderMarkdownDocument(rewrittenMarkdown, {
    citeStatus,
    defaultTitle: title,
    keepTitle: false,
    primaryColor: resolveColorToken(options?.color),
    theme: options?.theme,
    fontFamily: resolveFontFamily(options?.fontFamily),
  });
  fs.writeFileSync(htmlPath, html, "utf-8");

  const contentImages = await resolveContentImages(images, baseDir, tempDir, "md-to-wechat");

  return {
    title,
    author,
    summary,
    htmlPath,
    contentImages,
  };
}

function printUsage(): never {
  console.log(`Convert Markdown to WeChat-ready HTML with image placeholders

Usage:
  npx -y bun md-to-wechat.ts <markdown_file> [options]

Options:
  --title <title>     Override title
  --theme <name>      Theme name (default, grace, simple, modern)
  --color <name|hex>  Primary color (blue, green, vermilion, etc. or hex)
  --no-cite           Disable bottom citations for ordinary external links
  --help              Show this help

Output JSON format:
{
  "title": "Article Title",
  "htmlPath": "/tmp/wechat-article-images/temp-article.html",
  "contentImages": [
    {
      "placeholder": "WECHATIMGPH_1",
      "localPath": "/tmp/wechat-image/img.png",
      "originalPath": "imgs/image.png"
    }
  ]
}

Example:
  npx -y bun md-to-wechat.ts article.md
  npx -y bun md-to-wechat.ts article.md --theme grace
  npx -y bun md-to-wechat.ts article.md --theme modern --color blue
  npx -y bun md-to-wechat.ts article.md --no-cite
`);
  process.exit(0);
}

async function main(): Promise<void> {
  const args = process.argv.slice(2);
  if (args.length === 0 || args.includes("--help") || args.includes("-h")) {
    printUsage();
  }

  let markdownPath: string | undefined;
  let title: string | undefined;
  let theme: string | undefined;
  let color: string | undefined;
  let fontFamily: string | undefined;
  let citeStatus = true;

  for (let i = 0; i < args.length; i++) {
    const arg = args[i]!;
    if (arg === "--title" && args[i + 1]) {
      title = args[++i];
    } else if (arg === "--theme" && args[i + 1]) {
      theme = args[++i];
    } else if (arg === "--color" && args[i + 1]) {
      color = args[++i];
    } else if (arg === "--font-family" && args[i + 1]) {
      fontFamily = args[++i];
    } else if (arg === "--cite") {
      citeStatus = true;
    } else if (arg === "--no-cite") {
      citeStatus = false;
    } else if (!arg.startsWith("-")) {
      markdownPath = arg;
    }
  }

  if (!markdownPath) {
    console.error("Error: Markdown file path is required");
    process.exit(1);
  }

  if (!fs.existsSync(markdownPath)) {
    console.error(`Error: File not found: ${markdownPath}`);
    process.exit(1);
  }

  const result = await convertMarkdown(markdownPath, { title, theme, color, citeStatus, fontFamily });
  console.log(JSON.stringify(result, null, 2));
}

await main().catch((error) => {
  console.error(`Error: ${error instanceof Error ? error.message : String(error)}`);
  process.exit(1);
});
