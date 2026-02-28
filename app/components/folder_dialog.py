"""資料夾批次選擇對話框"""

from typing import List
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QHBoxLayout,
    QVBoxLayout,
    QListWidgetItem,
)
from qfluentwidgets import (
    MessageBoxBase,
    PushButton,
    SubtitleLabel,
    PrimaryPushButton,
    ListWidget
)


class FolderSelectionDialog(MessageBoxBase):
    """資料夾檔案選擇對話框"""

    def __init__(self, parent=None, files=None):
        super().__init__(parent)
        self.files = files or []
        self.titleLabel = SubtitleLabel("選擇要處理的檔案", self)

        # Create List Widget
        self.listWidget = ListWidget(self)

        # Add files as checkable items
        for file_path in self.files:
            item = QListWidgetItem(file_path, self.listWidget)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable) # type: ignore
            item.setCheckState(Qt.Checked) # type: ignore

        # Buttons layout
        self.select_all_btn = PushButton("全選", self)
        self.deselect_all_btn = PushButton("全取消", self)

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.select_all_btn)
        btn_layout.addWidget(self.deselect_all_btn)
        btn_layout.addStretch()

        # Add to custom layout
        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addLayout(btn_layout)
        self.viewLayout.addWidget(self.listWidget)

        # Minimum size
        self.widget.setMinimumWidth(800)
        self.widget.setMinimumHeight(500)
        self.listWidget.setMinimumHeight(400)

        # Connect signals
        self.select_all_btn.clicked.connect(self._on_select_all)
        self.deselect_all_btn.clicked.connect(self._on_deselect_all)

    def _on_select_all(self):
        for i in range(self.listWidget.count()):
            self.listWidget.item(i).setCheckState(Qt.Checked) # type: ignore

    def _on_deselect_all(self):
        for i in range(self.listWidget.count()):
            self.listWidget.item(i).setCheckState(Qt.Unchecked) # type: ignore

    def get_selected_files(self) -> List[str]:
        """返回被選中的檔案路徑列表"""
        selected = []
        for i in range(self.listWidget.count()):
            item = self.listWidget.item(i)
            if item.checkState() == Qt.Checked: # type: ignore
                selected.append(item.text())
        return selected
