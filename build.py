import re, os, html as htmlesc

BASE = "/Users/caesarxu/Desktop/unifydrive-weekly"
with open("/Users/caesarxu/Desktop/例会.md", "r") as f:
    content = f.read()

# In the file: lines like "# 2025\.12" (one backslash)
# use raw string without extra escaping
sections = re.split(r'\n(?=# \d{4}\\.\d)', content)
print(f"Sections: {len(sections)}")

months_map = {1:'Jan',2:'Feb',3:'Mar',4:'Apr',5:'May',6:'Jun',
              7:'Jul',8:'Aug',9:'Sep',10:'Oct',11:'Nov',12:'Dec'}

entries = []
for i, sec in enumerate(sections):
    m = re.match(r'# (\d{4})\\.(\d+)(?:\\.(\d+))?\n', sec)
    if not m:
        if i > 0:
            first = sec.split('\n')[0]
            print(f"  NO MATCH [{i}]: {first!r}")
        continue
    year = int(m.group(1))
    month = int(m.group(2))
    day = m.group(3)
    body = sec[m.end():].strip()
    
    date_str = f"{year}.{month}" if day is None else f"{year}.{month}.{day}"
    month_name = f"{months_map[month]} {year}"

    if day:
        fname = f"{year}-{month:02d}-{int(day):02d}"
    else:
        fname = f"{year}-{month:02d}"

    entries.append({
        'date': date_str, 'year': year, 'month': month,
        'month_name': month_name, 'body': body,
        'filename': fname,
    })
    print(f"  [R] {date_str} -> {fname}.html ({month_name}, {len(body)} chars)")

print(f"Parsed {len(entries)} entries total")

def md_inline(text):
    t = htmlesc.escape(text)
    t = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', t)
    t = re.sub(r'\*(.+?)\*', r'<em>\1</em>', t)
    t = re.sub(r'`([^`]+)`', r'<code>\1</code>', t)
    t = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2" target="_blank">\1</a>', t)
    t = t.replace('\\.', '.')
    return t

def md_to_html(text):
    lines = text.split('\n')
    html_parts = []
    in_list = False
    list_type = None

    for line in lines:
        stripped = line.strip()
        if not stripped:
            if in_list:
                html_parts.append('</ul>' if list_type == 'ul' else '</ol>')
                in_list = False
                list_type = None
            continue

        if stripped.startswith('### '):
            if in_list:
                html_parts.append('</ul>' if list_type == 'ul' else '</ol>')
                in_list = False
            html_parts.append(f'<h3>{md_inline(stripped[4:])}</h3>')
        elif stripped.startswith('## '):
            if in_list:
                html_parts.append('</ul>' if list_type == 'ul' else '</ol>')
                in_list = False
            html_parts.append(f'<h2>{md_inline(stripped[3:])}</h2>')
        elif stripped == '---':
            if in_list:
                html_parts.append('</ul>' if list_type == 'ul' else '</ol>')
                in_list = False
            html_parts.append('<hr>')
        elif re.match(r'^[-*]\s', stripped):
            if not in_list or list_type != 'ul':
                if in_list:
                    html_parts.append('</ul>' if list_type == 'ul' else '</ol>')
                html_parts.append('<ul>')
                in_list = True
                list_type = 'ul'
            content = re.sub(r'^[-*]\s+', '', stripped)
            html_parts.append(f'<li>{md_inline(content)}</li>')
        elif re.match(r'^\d+[\.、]\s', stripped):
            if not in_list or list_type != 'ol':
                if in_list:
                    html_parts.append('</ul>' if list_type == 'ul' else '</ol>')
                html_parts.append('<ol>')
                in_list = True
                list_type = 'ol'
            content = re.sub(r'^\d+[\.、]\s+', '', stripped)
            html_parts.append(f'<li>{md_inline(content)}</li>')
        elif stripped.startswith('> '):
            if in_list:
                html_parts.append('</ul>' if list_type == 'ul' else '</ol>')
                in_list = False
            html_parts.append(f'<blockquote>{md_inline(stripped[2:])}</blockquote>')
        elif stripped.startswith('!['):
            if in_list:
                html_parts.append('</ul>' if list_type == 'ul' else '</ol>')
                in_list = False
            m = re.match(r'!\[([^\]]*)\]\(([^)]+)\)', stripped)
            if m:
                alt, url = m.groups()
                html_parts.append(f'<p class="img-wrap"><img src="{htmlesc.escape(url)}" alt="{htmlesc.escape(alt)}" loading="lazy"></p>')
        else:
            if in_list:
                html_parts.append('</ul>' if list_type == 'ul' else '</ol>')
                in_list = False
            html_parts.append(f'<p>{md_inline(stripped)}</p>')

    if in_list:
        html_parts.append('</ul>' if list_type == 'ul' else '</ol>')

    return '\n        '.join(html_parts)

PAGE_TPL = '''<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} · UnifyDrive</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap');
  *,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
  :root{{--bg:#f5f4f0;--surface:#fff;--surface2:#efede7;--border:rgba(0,0,0,0.12);--border-light:rgba(0,0,0,0.07);--text:#15150f;--text-2:#5c5c56;--text-3:#8f8f88;--green:#0f7a3d;--green-bg:#dff2e6}}
  body{{font-family:'IBM Plex Sans',sans-serif;background:var(--bg);color:var(--text);font-size:14px;line-height:1.7;padding:0 24px 60px}}
  .page{{max-width:780px;margin:0 auto}}
  .nav{{position:sticky;top:0;z-index:100;display:flex;justify-content:space-between;align-items:center;padding:12px 20px;background:rgba(255,255,255,0.92);backdrop-filter:blur(12px);-webkit-backdrop-filter:blur(12px);border-bottom:1px solid var(--border);margin-bottom:32px;font-size:13px;font-weight:600}}
  .nav a{{text-decoration:none;color:var(--text-2);transition:color .12s}}
  .nav a:hover{{color:var(--text)}}
  .top-bar{{display:flex;justify-content:space-between;align-items:center;margin-bottom:36px;padding-bottom:16px;border-bottom:1px solid var(--border)}}
  .back-link{{font-size:12px;color:var(--text-2);text-decoration:none;display:flex;align-items:center;gap:4px;transition:color .12s}}
  .back-link:hover{{color:var(--text)}}
  .date-badge{{font-size:13px;font-weight:600;color:var(--text);background:var(--surface);border:1px solid var(--border);padding:6px 14px;border-radius:20px;font-family:'IBM Plex Mono',monospace}}
  .section-label{{font-size:11px;color:var(--text-3);text-transform:uppercase;letter-spacing:0.08em}}
  .content h1,.content h2,.content h3{{margin-top:28px;margin-bottom:8px;font-weight:600;color:var(--text)}}
  .content h1{{font-size:20px;margin-top:0}}
  .content h2{{font-size:17px;margin-top:32px;padding-bottom:6px;border-bottom:1px solid var(--border-light)}}
  .content h3{{font-size:14px;margin-top:24px;color:var(--text-2)}}
  .content p{{margin:10px 0}}
  .content ul,.content ol{{margin:8px 0;padding-left:20px}}
  .content li{{margin:4px 0;color:var(--text-2)}}
  .content code{{background:var(--surface2);padding:2px 6px;border-radius:4px;font-family:'IBM Plex Mono',monospace;font-size:13px}}
  .content blockquote{{margin:12px 0;padding:10px 16px;background:var(--surface2);border-left:3px solid var(--text-3);border-radius:0 6px 6px 0;font-size:13px;color:var(--text-2)}}
  .content hr{{border:none;border-top:1px solid var(--border);margin:24px 0}}
  .content strong{{color:var(--text);font-weight:600}}
  .content img{{max-width:100%;border-radius:8px;border:1px solid var(--border)}}
  .content .img-wrap{{margin:16px 0;text-align:center}}
  .content a{{color:var(--text)}}
  .footer{{text-align:center;margin-top:48px;padding-top:24px;border-top:1px solid var(--border);font-size:12px;color:var(--text-3)}}
  @media(max-width:540px){{body{{padding:0 16px 40px}}.content h1{{font-size:18px}}.content h2{{font-size:15px}}}}
</style>
</head>
<body>
<div class="page">
  <nav class="nav">
    <a href="reports.html">← 返回周报存档</a>
    <span style="font-size:12px;color:var(--text-3)">{date}</span>
  </nav>
  <div class="top-bar">
    <div>
      <div class="section-label">{section_label}</div>
    </div>
  </div>
  <div class="content">
        {body_html}
  </div>
  <div class="footer">
    <a style="color:inherit" href="https://github.com/theyouthforyou/unifydrive-weekly">View on GitHub</a>
  </div>
</div>
</body>
</html>'''

GH = "https://github.com/theyouthforyou/unifydrive-weekly"

report_count = 0

for e in entries:
    body_html = md_to_html(e['body'])

    out_dir = os.path.join(BASE, 'reports')
    section_label = 'Weekly / Monthly Report'
    back_link = 'reports.html'
    back_label = '周报月报'
    report_count += 1

    html_page = PAGE_TPL.format(
        title=e['date'],
        section_label=section_label,
        date=e['date'],
        back_link=back_link,
        back_label=back_label,
        body_html=body_html,
    )

    out_path = os.path.join(out_dir, f"{e['filename']}.html")
    with open(out_path, 'w') as f:
        f.write(html_page)
    print(f"  Generated: {out_path}")

print(f"\nDone! {report_count} reports generated.")
