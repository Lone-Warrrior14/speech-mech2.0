import os
import shutil

root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
list_file = os.path.join(root_dir, 'database', 'html_list.txt')
ui_dir = r'd:\SPEECH_MECH3\ui'
master_file_path = os.path.join(ui_dir, 'MASTER_BACKUP.html')

if not os.path.exists(ui_dir):
    os.makedirs(ui_dir)

with open(list_file, 'r', encoding='utf-8') as f:
    files = [line.strip() for line in f if line.strip()]

master_content = "<!-- MASTER BACKUP OF ALL HTML TEMPLATES -->\n"

for path in files:
    if os.path.exists(path):
        rel_path = os.path.relpath(path, root_dir)
        safe_name = rel_path.replace(os.sep, '__')
        
        with open(path, 'r', encoding='utf-8', errors='ignore') as src_f:
            content = src_f.read()
            
        # Add to master
        master_content += f"\n\n<!-- FILE: {rel_path} -->\n"
        master_content += f"<div id='{safe_name}' data-original-path='{rel_path}' style='display:none;'>\n"
        master_content += content
        master_content += "\n</div>\n"
        
        # Copy individual file
        dest_path = os.path.join(ui_dir, safe_name)
        with open(dest_path, 'w', encoding='utf-8') as dest_f:
            dest_f.write(content)

with open(master_file_path, 'w', encoding='utf-8') as m_f:
    m_f.write(master_content)

print(f"Backup complete. {len(files)} files processed.")
print(f"Individual backups and MASTER_BACKUP.html created in {ui_dir}")
