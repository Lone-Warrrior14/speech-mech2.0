import os

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
html_files = []

for dirpath, dirnames, filenames in os.walk(root):
    if 'venv' in dirnames:
        dirnames.remove('venv') # skip venv
    for filename in filenames:
        if filename.endswith('.html'):
            html_files.append(os.path.join(dirpath, filename))

output_path = os.path.join(root, 'database', 'html_list.txt')
with open(output_path, 'w', encoding='utf-8') as f:
    for path in html_files:
        f.write(path + '\n')
print(f"Found {len(html_files)} files.")
