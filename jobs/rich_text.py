from html import escape
from html.parser import HTMLParser
import re


ALLOWED_TAGS = {
    'p',
    'div',
    'br',
    'strong',
    'b',
    'em',
    'i',
    'u',
    'ul',
    'ol',
    'li',
}
BLOCKED_TAGS = {'script', 'style', 'iframe', 'object', 'embed'}
VOID_TAGS = {'br'}


class _RichTextSanitizer(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.blocked_depth = 0
        self.open_counts = {}

    def _is_blocked(self):
        return self.blocked_depth > 0

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if tag in BLOCKED_TAGS:
            self.blocked_depth += 1
            return
        if self._is_blocked():
            return
        if tag not in ALLOWED_TAGS:
            return
        if tag in VOID_TAGS:
            self.parts.append('<br>')
            return
        self.parts.append(f'<{tag}>')
        self.open_counts[tag] = self.open_counts.get(tag, 0) + 1

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag in BLOCKED_TAGS and self.blocked_depth > 0:
            self.blocked_depth -= 1
            return
        if self._is_blocked() or tag not in ALLOWED_TAGS or tag in VOID_TAGS:
            return
        if self.open_counts.get(tag, 0) > 0:
            self.parts.append(f'</{tag}>')
            self.open_counts[tag] -= 1

    def handle_data(self, data):
        if not self._is_blocked():
            self.parts.append(escape(data))

    def handle_entityref(self, name):
        if not self._is_blocked():
            self.parts.append(f'&{name};')

    def handle_charref(self, name):
        if not self._is_blocked():
            self.parts.append(f'&#{name};')


def _normalize_text_only(value):
    escaped = escape(value)
    return escaped.replace('\r\n', '\n').replace('\r', '\n').replace('\n', '<br>')


def sanitize_rich_text(value):
    if not value:
        return ''

    raw_value = str(value).strip()
    if not raw_value:
        return ''

    if '<' not in raw_value and '>' not in raw_value:
        return _normalize_text_only(raw_value)

    parser = _RichTextSanitizer()
    parser.feed(raw_value)
    parser.close()
    cleaned = ''.join(parser.parts).strip()

    # Avoid excessive empty lines from pasted content.
    cleaned = re.sub(r'(?:<br>\s*){3,}', '<br><br>', cleaned)
    return cleaned
