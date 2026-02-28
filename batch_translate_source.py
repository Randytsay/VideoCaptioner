import os
import re
import opencc

def batch_translate_source():
    converter = opencc.OpenCC('s2hk')
    pattern = re.compile(r'(\.tr\(\s*["\'])(.*?)(["\']\s*\))')
    
    app_dir = 'app'
    count = 0
    file_count = 0
    
    for root, dirs, files in os.walk(app_dir):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    def replace_func(match):
                        prefix = match.group(1)
                        original = match.group(2)
                        suffix = match.group(3)
                        translated = converter.convert(original)
                        if original != translated:
                            nonlocal count
                            count += 1
                        return f"{prefix}{translated}{suffix}"
                    
                    new_content = pattern.sub(replace_func, content)
                    
                    if content != new_content:
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(new_content)
                        file_count += 1
                        print(f"Updated: {file_path}")
                except Exception as e:
                    print(f"Error processing {file_path}: {e}")
                    
    print(f"\nTotal replacements: {count} across {file_count} files.")

if __name__ == "__main__":
    batch_translate_source()
