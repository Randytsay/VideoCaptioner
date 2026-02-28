# -*- coding: utf-8 -*-
from qfluentwidgets import (
    BodyLabel,
    SwitchSettingCard,
    MessageBoxBase,
)
from qfluentwidgets import FluentIcon as FIF

from app.common.config import cfg


class TranscriptionSettingDialog(MessageBoxBase):
    """转录设置对话框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.titleLabel = BodyLabel(self.tr("轉錄設置"), self)

        # 创建输出格式选择卡片
        self.format_srt_card = SwitchSettingCard(
            FIF.DOCUMENT,
            self.tr("SRT 字幕 (.srt)"),
            self.tr("包含時間軸的標準字幕格式"),
            cfg.transcribe_format_srt,
            parent=self,
        )
        self.format_vtt_card = SwitchSettingCard(
            FIF.DOCUMENT,
            self.tr("VTT 字幕 (.vtt)"),
            self.tr("WebVTT 網頁字幕格式"),
            cfg.transcribe_format_vtt,
            parent=self,
        )
        self.format_ass_card = SwitchSettingCard(
            FIF.DOCUMENT,
            self.tr("ASS 字幕 (.ass)"),
            self.tr("包含樣式和動效的高級字幕格式"),
            cfg.transcribe_format_ass,
            parent=self,
        )
        self.format_json_card = SwitchSettingCard(
            FIF.DOCUMENT,
            self.tr("JSON 數據 (.json)"),
            self.tr("包含詳細識別數據"),
            cfg.transcribe_format_json,
            parent=self,
        )
        self.format_txt_card = SwitchSettingCard(
            FIF.DOCUMENT,
            self.tr("TXT 純文本 (.txt)"),
            self.tr("無時間軸的純文本"),
            cfg.transcribe_format_txt,
            parent=self,
        )

        # 添加到布局
        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addWidget(self.format_srt_card)
        self.viewLayout.addWidget(self.format_vtt_card)
        self.viewLayout.addWidget(self.format_ass_card)
        self.viewLayout.addWidget(self.format_json_card)
        self.viewLayout.addWidget(self.format_txt_card)
        # 设置间距
        self.viewLayout.setSpacing(10)

        # 设置窗口标题和宽度
        self.setWindowTitle(self.tr("轉錄設置"))
        self.widget.setMinimumWidth(420)

        # 只显示取消按钮
        self.yesButton.hide()
        self.cancelButton.setText(self.tr("關閉"))

