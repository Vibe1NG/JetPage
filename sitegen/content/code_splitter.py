"""Split markdown source into alternating text and fenced-code segments."""

import re
from dataclasses import dataclass

_FENCE_RE = re.compile(
    r"^(?P<fence>`{3,}|~{3,})(?P<lang>[^\n]*)\n(?P<code>.*?)^(?P=fence)\s*$",
    re.MULTILINE | re.DOTALL,
)


@dataclass
class TextSegment:
    text: str


@dataclass
class CodeSegment:
    language: str
    code: str


def split_code_blocks(markdown: str) -> list[TextSegment | CodeSegment]:
    segments = []
    last = 0
    for m in _FENCE_RE.finditer(markdown):
        if m.start() > last:
            segments.append(TextSegment(markdown[last : m.start()]))
        segments.append(CodeSegment(language=m.group("lang").strip(), code=m.group("code")))
        last = m.end()
    if last < len(markdown):
        segments.append(TextSegment(markdown[last:]))
    return [s for s in segments if (isinstance(s, CodeSegment) or s.text.strip())]
