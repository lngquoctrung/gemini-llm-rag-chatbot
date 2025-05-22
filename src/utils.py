import bleach
import re

def convert_markdown_to_html(markdown):
    # Step 1: Replace **text** with <b>text</b>
    markdown = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', markdown)

    # Step 2: Convert * and numbered lists to <ul>/<ol>
    lines = markdown.split('\n')
    new_lines = []
    in_ul = False
    in_ol = False

    for line in lines:
        stripped = line.strip()

        # Check for unordered list (*)
        if stripped.startswith('*'):
            if in_ol:
                new_lines.append('</ol>')
                in_ol = False
            if not in_ul:
                new_lines.append('<ul>')
                in_ul = True
            item = stripped[1:].strip()
            new_lines.append(f'<li>{item}</li>')

        # Check for ordered list (1., 2., ...)
        elif re.match(r'^\d+\.', stripped):
            if in_ul:
                new_lines.append('</ul>')
                in_ul = False
            if not in_ol:
                new_lines.append('<ol>')
                in_ol = True
            item = re.sub(r'^\d+\.\s*', '', stripped)
            new_lines.append(f'<li>{item}</li>')

        # Normal line
        else:
            if in_ul:
                new_lines.append('</ul>')
                in_ul = False
            if in_ol:
                new_lines.append('</ol>')
                in_ol = False
            new_lines.append(line)

    # Close any open lists
    if in_ul:
        new_lines.append('</ul>')
    if in_ol:
        new_lines.append('</ol>')

    # Step 3: Clean with bleach
    final_text = '\n'.join(new_lines)
    final_text = bleach.clean(
        final_text,
        tags=['b', 'ul', 'ol', 'li'],
        attributes={},
        strip=True
    )

    return final_text