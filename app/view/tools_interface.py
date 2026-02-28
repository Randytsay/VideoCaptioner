"""小工具介面 - 提供去重工具與字典修正工具"""

import os
import re
from pathlib import Path

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
    QCheckBox,
)

from qfluentwidgets import (
    BodyLabel,
    CardWidget,
    InfoBar,
    InfoBarPosition,
    PushButton,
    SubtitleLabel,
    TitleLabel,
)
from qfluentwidgets import FluentIcon as FIF

from app.config import CUSTOM_DICT_PATH
from app.core.utils.text_utils import load_custom_dicts


class ToolsInterface(QWidget):
    """小工具頁面"""

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("toolsInterface")
        self.setWindowTitle(self.tr("小工具"))

        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(36, 20, 36, 20)
        main_layout.setSpacing(16)

        # 頁面標題
        title = TitleLabel(self.tr("小工具"))
        main_layout.addWidget(title)

        # ==================== 去重工具 ====================
        dedup_card = CardWidget(self)
        dedup_layout = QVBoxLayout(dedup_card)
        dedup_layout.setContentsMargins(20, 16, 20, 16)
        dedup_layout.setSpacing(10)

        dedup_title = SubtitleLabel(self.tr("📋 文字去重工具"))
        dedup_desc = BodyLabel(
            self.tr("選擇 .txt 檔案，自動去除重複行並保持原始順序。\n去重後的檔案會以「_deduplicated」後綴儲存在同目錄下。")
        )
        dedup_desc.setWordWrap(True)

        dedup_btn = PushButton(self.tr("選擇 TXT 檔案"), icon=FIF.DOCUMENT)
        dedup_btn.setFixedWidth(200)
        dedup_btn.clicked.connect(self.on_dedup_clicked)

        dedup_layout.addWidget(dedup_title)
        dedup_layout.addWidget(dedup_desc)
        dedup_layout.addWidget(dedup_btn)

        main_layout.addWidget(dedup_card)

        # ==================== 字典修正工具 ====================
        dict_card = CardWidget(self)
        dict_layout = QVBoxLayout(dict_card)
        dict_layout.setContentsMargins(20, 16, 20, 16)
        dict_layout.setSpacing(10)

        dict_title = SubtitleLabel(self.tr("📖 字典修正工具"))

        dict_path_label = BodyLabel(
            self.tr(
                "選擇 .srt 或 .txt 字幕檔案，套用自定義對照表進行修正。\n"
                f"對照表路徑：{CUSTOM_DICT_PATH}"
            )
        )
        dict_path_label.setWordWrap(True)

        btn_layout = QHBoxLayout()
        dict_btn = PushButton(self.tr("選擇字幕檔案"), icon=FIF.EDIT)
        dict_btn.setFixedWidth(200)
        dict_btn.clicked.connect(self.on_dict_correct_clicked)

        open_dict_btn = PushButton(self.tr("開啟對照表資料夾"), icon=FIF.FOLDER)
        open_dict_btn.setFixedWidth(200)
        open_dict_btn.clicked.connect(self.on_open_dict_folder)

        btn_layout.addWidget(dict_btn)
        btn_layout.addWidget(open_dict_btn)
        btn_layout.addStretch()

        self.overwrite_checkbox = QCheckBox(self.tr("直接覆蓋原檔案（否則另存為 _corrected）"))
        self.overwrite_checkbox.setChecked(False)

        dict_layout.addWidget(dict_title)
        dict_layout.addWidget(dict_path_label)
        dict_layout.addWidget(self.overwrite_checkbox)
        dict_layout.addLayout(btn_layout)

        main_layout.addWidget(dict_card)

        # 底部彈性空間
        main_layout.addStretch()

    # ==================== 去重工具邏輯 ====================
    def on_dedup_clicked(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            self.tr("選擇文字檔"),
            "",
            self.tr("文字檔案 (*.txt);;所有檔案 (*.*)"),
        )
        if not file_path:
            return

        try:
            p = Path(file_path)
            # 讀取檔案
            try:
                content = p.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                content = p.read_text(encoding="gbk")

            lines = content.splitlines()
            # 去重（保持順序），# 開頭的註解行直接保留不參與去重
            result = []
            seen = set()
            for line in lines:
                stripped = line.strip()
                if not stripped:
                    continue
                if stripped.startswith("#"):
                    result.append(stripped)
                    continue
                if stripped not in seen:
                    seen.add(stripped)
                    result.append(stripped)
            unique_lines = result

            # 寫回新檔案
            output_path = p.parent / f"{p.stem}_deduplicated{p.suffix}"
            output_path.write_text("\n".join(unique_lines), encoding="utf-8")

            InfoBar.success(
                title=self.tr("去重完成"),
                content=self.tr("原始行數：{} → 去重後：{}\n已儲存至：{}").format(
                    len(lines), len(unique_lines), output_path.name
                ),
                duration=6000,
                position=InfoBarPosition.TOP,
                parent=self,
            )

            # 打開資料夾並選中檔案
            if os.name == "nt":
                os.system(f'explorer /select,"{str(output_path).replace("/", os.sep)}"')

        except Exception as e:
            InfoBar.error(
                title=self.tr("去重失敗"),
                content=str(e),
                duration=6000,
                position=InfoBarPosition.TOP,
                parent=self,
            )

    # ==================== 字典修正工具邏輯 ====================
    def on_dict_correct_clicked(self):
        # 先檢查字典是否有內容
        mappings = load_custom_dicts(str(CUSTOM_DICT_PATH))
        if not mappings:
            InfoBar.warning(
                title=self.tr("對照表為空"),
                content=self.tr("請先在對照表資料夾中放置 .txt 對照檔案\n路徑：{}").format(
                    CUSTOM_DICT_PATH
                ),
                duration=6000,
                position=InfoBarPosition.TOP,
                parent=self,
            )
            return

        files, _ = QFileDialog.getOpenFileNames(
            self,
            self.tr("選擇字幕檔案"),
            "",
            self.tr("字幕檔案 (*.srt *.txt);;所有檔案 (*.*)"),
        )
        if not files:
            return

        # 依照鍵的長度降序排序，確保長詞優先匹配
        sorted_keys = sorted(mappings.keys(), key=len, reverse=True)
        
        processed = 0
        for file_path in files:
            try:
                p = Path(file_path)
                try:
                    content = p.read_text(encoding="utf-8")
                except UnicodeDecodeError:
                    content = p.read_text(encoding="gbk")

                # 套用置換
                for key in sorted_keys:
                    content = content.replace(key, mappings[key])

                # 儲存修正後的檔案
                if self.overwrite_checkbox.isChecked():
                    output_path = p
                else:
                    output_path = p.parent / f"{p.stem}_corrected{p.suffix}"
                    
                output_path.write_text(content, encoding="utf-8")
                processed += 1

            except Exception as e:
                InfoBar.error(
                    title=self.tr("修正失敗"),
                    content=f"{Path(file_path).name}: {e}",
                    duration=6000,
                    position=InfoBarPosition.TOP,
                    parent=self,
                )

        if processed > 0:
            InfoBar.success(
                title=self.tr("修正完成"),
                content=self.tr("已處理 {} 個檔案，套用 {} 個詞條").format(
                    processed, len(mappings)
                ),
                duration=6000,
                position=InfoBarPosition.TOP,
                parent=self,
            )

            # 打開最後一個檔案所在的資料夾
            if os.name == "nt" and files:
                last_file = Path(files[-1])
                output = last_file if self.overwrite_checkbox.isChecked() else last_file.parent / f"{last_file.stem}_corrected{last_file.suffix}"
                os.system(f'explorer /select,"{str(output).replace("/", os.sep)}"')

    def on_open_dict_folder(self):
        """開啟對照表資料夾"""
        path = str(CUSTOM_DICT_PATH)
        if os.name == "nt":
            os.startfile(path)
        else:
            import subprocess
            subprocess.Popen(["xdg-open", path])
