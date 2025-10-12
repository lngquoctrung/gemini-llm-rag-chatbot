import bleach
import re

def convert_markdown_to_html(markdown):
    allowed_tags = ['b', 'strong', 'i', 'em', 'u', 'p', 'br', 'ul', 'ol', 'li', 'h1', 'h2', 'h3', 'h4', 'code', 'pre', 'span', 'div']
    allowed_attrs = {'*': ['class']}

    html = bleach.clean(markdown, tags=[], strip=True)

    def replace_code_block(match):
        code_content = match.group(1).strip()
        return f'<pre><code>{code_content}</code></pre>'

    html = re.sub(r'``````', replace_code_block, html)
    html = re.sub(r'`([^`]+)`', r'<code>\1</code>', html)
    html = re.sub(r'^#### (.*?)$', r'<h4>\1</h4>', html, flags=re.MULTILINE)
    html = re.sub(r'^### (.*?)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
    html = re.sub(r'^## (.*?)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
    html = re.sub(r'^# (.*?)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)
    html = re.sub(r'\*\*\*(.*?)\*\*\*', r'<b><i>\1</i></b>', html)
    html = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', html)
    html = re.sub(r'\*(.*?)\*', r'<i>\1</i>', html)

    processed_lines = []
    in_ordered_list = False
    in_unordered_list = False
    prev_was_list_item = False

    for line in html.split('\n'):
        stripped = line.strip()

        if not stripped or stripped.startswith('<h') or stripped.startswith('<pre>') or stripped.startswith('</pre>') or stripped.startswith('<code>'):
            if in_unordered_list and not prev_was_list_item:
                processed_lines.append('</ul>')
                in_unordered_list = False
            if in_ordered_list and not prev_was_list_item:
                processed_lines.append('</ol>')
                in_ordered_list = False
            processed_lines.append(line)
            prev_was_list_item = False
            continue

        ordered_match = re.match(r'^\d+[.)\s]\s*(.+)$', stripped)
        unordered_match = re.match(r'^[*\-]\s+(.+)$', stripped)

        if ordered_match:
            if not in_ordered_list:
                if in_unordered_list:
                    processed_lines.append('</ul>')
                    in_unordered_list = False
                processed_lines.append('<ol>')
                in_ordered_list = True
            processed_lines.append(f'<li>{ordered_match.group(1)}</li>')
            prev_was_list_item = True
        elif unordered_match:
            if not in_unordered_list:
                if in_ordered_list and not prev_was_list_item:
                    processed_lines.append('</ol>')
                    in_ordered_list = False
                processed_lines.append('<ul>')
                in_unordered_list = True
            processed_lines.append(f'<li>{unordered_match.group(1)}</li>')
            prev_was_list_item = True
        else:
            if in_unordered_list:
                processed_lines.append('</ul>')
                in_unordered_list = False
            if in_ordered_list:
                processed_lines.append('</ol>')
                in_ordered_list = False
            processed_lines.append(line)
            prev_was_list_item = False

    if in_unordered_list:
        processed_lines.append('</ul>')
    if in_ordered_list:
        processed_lines.append('</ol>')

    html = '\n'.join(processed_lines)

    blocks = []
    current_block = []

    for line in html.split('\n'):
        stripped = line.strip()
        if re.match(r'^</?(?:ol|ul|h[1-4]|pre)', stripped):
            if current_block:
                block_text = ' '.join(current_block)
                if block_text and not re.match(r'^<[^>]+>$', block_text):
                    blocks.append(f'<p>{block_text}</p>')
                current_block = []
            blocks.append(line)
        elif stripped:
            current_block.append(stripped)

    if current_block:
        block_text = ' '.join(current_block)
        if block_text and not re.match(r'^<[^>]+>$', block_text):
            blocks.append(f'<p>{block_text}</p>')

    html = ''.join(blocks)
    html = bleach.clean(html, tags=allowed_tags, attributes=allowed_attrs, strip=False)

    return html
