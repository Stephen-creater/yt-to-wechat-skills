#!/usr/bin/env python3
"""
小绿书纯文本排版

核心：段落之间留空行，制造呼吸感。
去掉 Markdown 语法标记，输出干净的纯文本。

使用方法：
    python3 format.py -i article.md              # 输出到 stdout
    python3 format.py -i article.md -o output.txt # 输出到文件
"""

import sys
import os
import argparse
import re


def format_text(raw_text):
    """
    将原始文本（可能含 Markdown 语法）转换为有呼吸感的纯文本。

    处理逻辑：
    1. 去掉 Markdown 标记（标题 #、加粗 **、图片 ![]() 等）
    2. 确保每个段落之间有空行
    3. 去掉多余的连续空行（最多保留一个）
    """
    lines = raw_text.split('\n')
    result = []

    in_code_block = False

    for line in lines:
        stripped = line.strip()

        # 代码块：整块跳过（小绿书不适合放代码）
        if stripped.startswith('```'):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue

        # 空行：保留（用于段落分隔）
        if not stripped:
            result.append('')
            continue

        # 图片行：跳过（小绿书图片走 image_list，不在正文里）
        if re.match(r'!\[.*?\]\(.*?\)', stripped):
            continue

        # 分隔线：转为空行
        if stripped in ('---', '***', '___'):
            result.append('')
            continue

        # 标题：去掉 # 号，保留文字
        if stripped.startswith('#'):
            stripped = re.sub(r'^#+\s*', '', stripped)

        # 加粗：去掉 **
        stripped = re.sub(r'\*\*(.*?)\*\*', r'\1', stripped)

        # 斜体：去掉 *
        stripped = re.sub(r'\*(.*?)\*', r'\1', stripped)

        # 行内代码：去掉 `
        stripped = re.sub(r'`(.*?)`', r'\1', stripped)

        # 链接：保留文字，去掉 URL
        stripped = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', stripped)

        # 无序列表标记：去掉 - 或 * 开头，保留内容
        stripped = re.sub(r'^[-*]\s+', '', stripped)

        # 有序列表标记：保留编号
        # (1. xxx 这种保持原样，本身就是纯文本)

        # HTML 实体还原
        stripped = stripped.replace('&#x', '\\u').replace(';', '')

        result.append(stripped)

    # 合并连续空行为单个空行（呼吸感，但不过度）
    final = []
    prev_empty = False
    for line in result:
        if line == '':
            if not prev_empty:
                final.append('')
            prev_empty = True
        else:
            prev_empty = False
            final.append(line)

    # 去掉首尾空行
    while final and final[0] == '':
        final.pop(0)
    while final and final[-1] == '':
        final.pop()

    text = '\n\n'.join(
        paragraph.strip()
        for paragraph in '\n'.join(final).split('\n\n')
        if paragraph.strip()
    )

    # 追加 footer（如果存在）
    footer_path = os.path.join(os.path.dirname(__file__), '..', 'footer.md')
    if os.path.exists(footer_path):
        with open(footer_path, 'r', encoding='utf-8') as f:
            footer = f.read().strip()
        if footer:
            text = text + '\n\n' + footer

    return text


def main():
    parser = argparse.ArgumentParser(description="小绿书纯文本排版（段落呼吸感）")
    parser.add_argument("--input", "-i", required=True, help="输入文本/Markdown 文件路径")
    parser.add_argument("--output", "-o", default=None, help="输出文件路径（不指定则输出到 stdout）")

    args = parser.parse_args()

    try:
        with open(args.input, 'r', encoding='utf-8') as f:
            raw_text = f.read()

        formatted = format_text(raw_text)

        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(formatted)
            print(f"排版完成: {args.input} -> {args.output}", file=sys.stderr)
        else:
            print(formatted)

    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
