import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path
import os

def deduplicate_txt():
    # 隱藏主視窗
    root = tk.Tk()
    root.withdraw()

    # 選擇檔案
    file_path = filedialog.askopenfilename(
        title="選擇文字檔",
        filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
    )
    
    if not file_path:
        return

    try:
        p = Path(file_path)
        # 讀取檔案，嘗試 utf-8
        try:
            with open(p, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            # 如果 utf-8 失敗，嘗試 gbk (Windows 常見)
            with open(p, 'r', encoding='gbk') as f:
                content = f.read()
        
        lines = content.splitlines()
        
        # 移除空白並去重（使用 dict.fromkeys 保持順序）
        # 只保留非空行
        unique_lines = list(dict.fromkeys(line.strip() for line in lines if line.strip()))

        # 寫回新檔案
        output_path = p.parent / f"{p.stem}_deduplicated{p.suffix}"
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(unique_lines))

        messagebox.showinfo("成功", f"處理完成！\n\n原始行數: {len(lines)}\n去重後行數: {len(unique_lines)}\n\n已儲存至：\n{output_path.name}")
        
        # 自動打開資料夾並選中檔案 (Windows)
        os.system(f'explorer /select,"{str(output_path).replace("/", "\\")}"')
    
    except Exception as e:
        messagebox.showerror("錯誤", f"處理失敗：{str(e)}")

if __name__ == "__main__":
    deduplicate_txt()
