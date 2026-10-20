#!/usr/bin/env python3
"""Describe report length; never infer reading completion or factual accuracy."""
from __future__ import annotations

import argparse
import html
import json
import re
from pathlib import Path


REFERENCE_CHARACTERS = (1900, 2400)
REFERENCE_HAN = (850, 1250)
COUNTING_RULE = "正文按 Unicode 码点计数；body_characters 去除空白，包含英文与标点；另报含空白字符数。Markdown 链接只计可见文字，图片和 URL 不计，两个标准章节标题不计。"
LINK = re.compile(r"(?<!!)\[([^\]\n]+)\]\((?:[^()\n]|\([^()\n]*\))*\)")
IMAGE = re.compile(r"!\[[^\]\n]*\]\((?:[^()\n]|\([^()\n]*\))*\)")
SECTION = re.compile(r"^(?:一、(?:本周|上周)工作总结|二、(?:本周|下周)工作安排)[：:]?$")
HAN_RANGES = (
    (0x3400, 0x4DBF), (0x4E00, 0x9FFF), (0xF900, 0xFAFF),
    (0x20000, 0x2A6DF), (0x2A700, 0x2B73F), (0x2B740, 0x2B81F),
    (0x2B820, 0x2CEAF), (0x2CEB0, 0x2EBEF), (0x2EBF0, 0x2EE5F),
    (0x2F800, 0x2FA1F), (0x30000, 0x3134F), (0x31350, 0x323AF),
)


def visible_body(markdown: str) -> str:
    """Keep visible prose, including other headings and inline code contents.

    Remove images, URL destinations/bare URLs, Markdown formatting, reference
    definitions and the two standard report section headings. No browser or
    Markdown renderer is required; this is a deliberately small prose parser.
    """
    value = markdown.replace("\r\n", "\n").replace("\r", "\n")
    value = re.sub(r"\A\ufeff?---\n.*?\n---(?:\n|$)", "", value, flags=re.S)
    value = re.sub(r"<!--.*?-->", "", value, flags=re.S)
    reference_ids = set(re.findall(r"(?m)^\s{0,3}\[([^\]]+)\]:\s*\S+.*$", value))
    value = re.sub(r"(?m)^\s{0,3}\[[^\]]+\]:\s*\S+.*$", "", value)
    value = IMAGE.sub("", value)
    value = re.sub(r"!\[[^\]\n]*\]\[[^\]\n]*\]", "", value)
    for reference_id in reference_ids:
        value = re.sub(r"!\[" + re.escape(reference_id) + r"\]", "", value)
    value = LINK.sub(lambda match: match.group(1), value)
    value = re.sub(r"(?<!!)\[([^\]\n]+)\]\[[^\]\n]*\]", r"\1", value)
    for reference_id in reference_ids:
        value = value.replace("[" + reference_id + "]", reference_id)
    value = re.sub(r"<(?:https?|ftp)://[^>]+>", "", value)
    value = re.sub(r"</?[A-Za-z][^>]*>", "", value)

    def strip_url(match: re.Match[str]) -> str:
        url = match.group(0)
        return url[len(url.rstrip(".,;:!?。，；：！？）】")):]

    value = re.sub(r"(?:https?|ftp)://[^\s<>()]+", strip_url, value)
    lines = []
    for line in value.split("\n"):
        line = re.sub(r"^\s{0,3}#{1,6}\s+", "", line)
        line = re.sub(r"\s+#+\s*$", "", line)
        line = re.sub(r"^\s*>\s?", "", line)
        line = re.sub(r"^\s*(?:[-+*]|\d+[.)])\s+", "", line)
        if re.match(r"^\s*(`{3,}|~{3,})", line):
            continue
        line = line.replace("**", "").replace("__", "").replace("~~", "")
        line = re.sub(r"(?<!\w)[*_]([^*_\n]+)[*_](?!\w)", r"\1", line)
        line = line.replace("`", "")
        line = re.sub(r"\\([\\`*{}\[\]()#+.!_>~-])", r"\1", line)
        if SECTION.fullmatch(line.strip()):
            continue
        lines.append(line)
    return html.unescape("\n".join(lines)).strip()


def report_metrics(markdown: str) -> dict[str, object]:
    body = visible_body(markdown)
    characters = sum(not char.isspace() for char in body)
    han = sum(any(start <= ord(char) <= end for start, end in HAN_RANGES) for char in body)
    return {
        "body_characters": characters,
        "body_characters_with_whitespace": len(body),
        "whitespace_characters": sum(char.isspace() for char in body),
        "han_characters": han,
        "reference_characters": list(REFERENCE_CHARACTERS),
        "reference_han_characters": list(REFERENCE_HAN),
        "characters_in_reference_range": REFERENCE_CHARACTERS[0] <= characters <= REFERENCE_CHARACTERS[1],
        "han_in_reference_range": REFERENCE_HAN[0] <= han <= REFERENCE_HAN[1],
        "counting_rule": COUNTING_RULE,
        "notice": "参考区间仅辅助编辑，不作为通过条件，不评价论文事实、阅读状态或研究质量。",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, epilog=COUNTING_RULE)
    parser.add_argument("file", type=Path, help="UTF-8 Markdown or text report")
    parser.add_argument("--json", action="store_true", help="Print machine-readable metrics")
    args = parser.parse_args(argv)
    try:
        result = report_metrics(args.file.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError) as error:
        parser.exit(2, f"Cannot read report: {error}\n")
    if args.json:
        # ASCII-safe JSON also works in redirected Windows shells using legacy encodings.
        print(json.dumps(result, ensure_ascii=True, indent=2))
    else:
        print(f"正文字符（去空白，含英文及标点）：{result['body_characters']}")
        print(f"正文字符（含空白）：{result['body_characters_with_whitespace']}")
        print(f"中文汉字：{result['han_characters']}")
        print("参考量级：正文 1900—2400 字符；中文汉字 850—1250。")
        print(result["counting_rule"])
        print(result["notice"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
