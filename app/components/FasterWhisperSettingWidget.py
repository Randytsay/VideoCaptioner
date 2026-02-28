import os
import shutil
import subprocess
from pathlib import Path

from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QShowEvent
from PyQt5.QtWidgets import (
    QHBoxLayout,
    QHeaderView,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QGridLayout,
    QSizePolicy,
)
from qfluentwidgets import (
    BodyLabel,
    ComboBox,
    ComboBoxSettingCard,
    HyperlinkCard,
    InfoBar,
    InfoBarPosition,
    MessageBoxBase,
    ProgressBar,
    SettingCardGroup,
    SingleDirectionScrollArea,
    SubtitleLabel,
    SwitchSettingCard,
    TableItemDelegate,
    TableWidget,
    CheckBox,
)
from qfluentwidgets.components.widgets.button import HyperlinkButton, PushButton
from qfluentwidgets import FluentIcon as FIF

from app.common.config import cfg
from app.components.LineEditSettingCard import LineEditSettingCard
from app.components.SpinBoxSettingCard import DoubleSpinBoxSettingCard
from app.config import BIN_PATH, MODEL_PATH
from app.core.entities import (
    FasterWhisperModelEnum,
    TranscribeLanguageEnum,
    VadMethodEnum,
)
from app.core.utils.platform_utils import open_folder
from app.thread.file_download_thread import FileDownloadThread
from app.thread.modelscope_download_thread import ModelscopeDownloadThread

# 在文件开头添加常量定义
FASTER_WHISPER_PROGRAMS = [
    {
        "label": "GPU（cuda） + CPU 版本",
        "value": "faster-whisper-gpu.7z",
        "type": "GPU",
        "size": "1.35 GB",
        "downloadLink": "https://modelscope.cn/models/bkfengg/whisper-cpp/resolve/master/Faster-Whisper-XXL_r245.2_windows.7z",
    },
    {
        "label": "CPU版本",
        "value": "faster-whisper.exe",
        "type": "CPU",
        "size": "78.7 MB",
        "downloadLink": "https://modelscope.cn/models/bkfengg/whisper-cpp/resolve/master/whisper-faster.exe",
    },
]

FASTER_WHISPER_MODELS = [
    {
        "label": "Tiny",
        "value": "faster-whisper-tiny",
        "size": "77824",
        "downloadLink": "https://huggingface.co/Systran/faster-whisper-tiny",
        "modelScopeLink": "pengzhendong/faster-whisper-tiny",
    },
    {
        "label": "Base",
        "value": "faster-whisper-base",
        "size": "148480",
        "downloadLink": "https://huggingface.co/Systran/faster-whisper-base",
        "modelScopeLink": "pengzhendong/faster-whisper-base",
    },
    {
        "label": "Small",
        "value": "faster-whisper-small",
        "size": "495616",
        "downloadLink": "https://huggingface.co/Systran/faster-whisper-small",
        "modelScopeLink": "pengzhendong/faster-whisper-small",
    },
    {
        "label": "Medium",
        "value": "faster-whisper-medium",
        "size": "1572864",
        "downloadLink": "https://huggingface.co/Systran/faster-whisper-medium",
        "modelScopeLink": "pengzhendong/faster-whisper-medium",
    },
    {
        "label": "Large-v1",
        "value": "faster-whisper-large-v1",
        "size": "3145728",
        "downloadLink": "https://huggingface.co/Systran/faster-whisper-large-v1",
        "modelScopeLink": "pengzhendong/faster-whisper-large-v1",
    },
    {
        "label": "Large-v2",
        "value": "faster-whisper-large-v2",
        "size": "3145728",
        "downloadLink": "https://huggingface.co/Systran/faster-whisper-large-v2",
        "modelScopeLink": "pengzhendong/faster-whisper-large-v2",
    },
    {
        "label": "Large-v3",
        "value": "faster-whisper-large-v3",
        "size": "3145728",
        "downloadLink": "https://huggingface.co/Systran/faster-whisper-large-v3",
        "modelScopeLink": "pengzhendong/faster-whisper-large-v3",
    },
    {
        "label": "Large-v3-turbo",
        "value": "faster-whisper-large-v3-turbo",
        "size": "1720320",
        "downloadLink": "https://huggingface.co/Systran/faster-whisper-large-v3-turbo",
        "modelScopeLink": "pengzhendong/faster-whisper-large-v3-turbo",
    },
]


# 在类外添加这个工具函数
def check_faster_whisper_exists() -> tuple[bool, list[str]]:
    """检查 faster-whisper 程序是否存在

    检查以下两种情况:
    1. bin目录下是否有 faster-whisper.exe
    2. bin目录下是否有 Faster-Whisper-XXL/faster-whisper-xxl.exe

    Returns:
        tuple[bool, list[str]]: (是否存在程序, 已安装的版本列表)
    """
    bin_path = Path(BIN_PATH)
    installed_versions = []

    # 检查 faster-whisper.exe(CPU版本)
    if (bin_path / "faster-whisper.exe").exists():
        installed_versions.append("CPU")

    # 检查 Faster-Whisper-XXL/faster-whisper-xxl.exe(GPU版本)
    xxl_path = bin_path / "Faster-Whisper-XXL" / "faster-whisper-xxl.exe"
    if xxl_path.exists():
        installed_versions.extend(["GPU", "CPU"])
    installed_versions = list(set(installed_versions))

    return bool(installed_versions), installed_versions


# 添加新的解压线程类
class UnzipThread(QThread):
    """7z解压线程"""

    finished = pyqtSignal()  # 解压完成信号
    error = pyqtSignal(str)  # 解压错误信号

    def __init__(self, zip_file, extract_path):
        super().__init__()
        self.zip_file = zip_file
        self.extract_path = extract_path

    def run(self):
        try:
            # 檢查 7z 是否存在
            if not shutil.which("7z"):
                raise RuntimeError(
                    "系統未偵測到 7z 執行指令，無法自動解壓程式包。\n"
                    "請先安裝 7-Zip 並加入系統環境變數，或手動將該 .7z 檔案解壓縮到同目錄下的 Faster-Whisper-XXL 資料夾中。"
                )

            subprocess.run(
                ["7z", "x", self.zip_file, f"-o{self.extract_path}", "-y"],
                check=True,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            )
            # 删除压缩包
            os.remove(self.zip_file)
            self.finished.emit()
        except subprocess.CalledProcessError as e:
            self.error.emit(f"解壓失敗 (7z 報錯): {str(e)}")
        except Exception as e:
            self.error.emit(str(e))


class FasterWhisperDownloadDialog(MessageBoxBase):
    """Faster Whisper 下载对话框"""

    # 添加类变量跟踪下载状态
    is_downloading = False

    def __init__(self, parent=None, setting_widget=None):
        super().__init__(parent)
        self.widget.setMinimumWidth(600)
        self.program_download_thread = None
        self.model_download_thread = None
        self._setup_ui()
        self._connect_signals()
        self.setting_widget = setting_widget

    def _setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout()
        self._setup_program_section(layout)
        layout.addSpacing(20)
        self._setup_model_section(layout)
        self._setup_progress_section(layout)

        self.viewLayout.addLayout(layout)
        self.cancelButton.setText(self.tr("關閉"))
        self.yesButton.hide()

    def _setup_program_section(self, layout):
        """设置程序下载部分UI"""
        # 标题和按钮的水平布局
        title_layout = QHBoxLayout()

        # 标题
        faster_whisper_title = SubtitleLabel(self.tr("Faster Whisper 下載"), self)
        title_layout.addWidget(faster_whisper_title)

        # 添加打开文件夹按钮
        open_folder_btn = HyperlinkButton("", self.tr("打開程序文件夾"), parent=self)
        open_folder_btn.setIcon(FIF.FOLDER)
        open_folder_btn.clicked.connect(self._open_program_folder)
        title_layout.addStretch()
        title_layout.addWidget(open_folder_btn)

        layout.addLayout(title_layout)
        layout.addSpacing(8)

        # 检查已安装的版本
        has_program, installed_versions = check_faster_whisper_exists()

        if has_program:
            # 显示已安装版本
            versions_text = " + ".join(installed_versions)
            program_status = BodyLabel(self.tr(f"已安装版本: {versions_text}"), self)
            program_status.setStyleSheet("color: green")
            layout.addWidget(program_status)

            # 添加说明标签
            if len(installed_versions) == 1:
                desc_label = BodyLabel(self.tr("您可以繼續下載其他版本:"), self)
                layout.addWidget(desc_label)
        else:
            desc_label = BodyLabel(self.tr("未下載Faster Whisper 程序"), self)
            layout.addWidget(desc_label)

        # 下载控件
        program_layout = QHBoxLayout()
        self.program_combo = ComboBox(self)
        self.program_combo.setFixedWidth(300)
        self.program_combo.hide()

        # 只显示未安装的版本
        for program in FASTER_WHISPER_PROGRAMS:
            version_type = program["type"]
            if version_type not in installed_versions:
                self.program_combo.addItem(f"{program['label']} ({program['size']})")

        # 如果还有可下载的版本，显示下载控件
        if self.program_combo.count() > 0:
            self.program_combo.show()
            self.program_download_btn = PushButton(self.tr("下載程序"), self)
            self.program_download_btn.clicked.connect(self._start_download)
            program_layout.addWidget(self.program_combo)
            program_layout.addWidget(self.program_download_btn)
            program_layout.addStretch()
            layout.addLayout(program_layout)

    def _setup_model_section(self, layout):
        """设置模型下载部分UI"""
        # 标题和按钮的水平布局
        title_layout = QHBoxLayout()

        # 标题
        model_title = SubtitleLabel(self.tr("模型下載"), self)
        title_layout.addWidget(model_title)

        # 添加打开文件夹按钮
        open_folder_btn = HyperlinkButton("", self.tr("打開模型文件夾"), parent=self)
        open_folder_btn.setIcon(FIF.FOLDER)
        open_folder_btn.clicked.connect(self._open_model_folder)
        title_layout.addStretch()
        title_layout.addWidget(open_folder_btn)

        layout.addLayout(title_layout)
        layout.addSpacing(8)

        # 模型表格
        self.model_table = self._create_model_table()
        self._populate_model_table()
        layout.addWidget(self.model_table)

    def _create_model_table(self):
        """创建模型表格"""
        table = TableWidget(self)
        table.setEditTriggers(TableWidget.NoEditTriggers)
        table.setSelectionMode(TableWidget.NoSelection)
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(
            [self.tr("模型名稱"), self.tr("大小"), self.tr("狀態"), self.tr("操作")]
        )

        # 设置表格样式
        table.setBorderVisible(True)
        table.setBorderRadius(8)
        table.setItemDelegate(TableItemDelegate(table))

        # 设置列宽
        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.Fixed)
        header.setSectionResizeMode(2, QHeaderView.Fixed)
        header.setSectionResizeMode(3, QHeaderView.Fixed)

        table.setColumnWidth(1, 100)
        table.setColumnWidth(2, 80)
        table.setColumnWidth(3, 150)

        # 设置行高
        row_height = 45
        table.verticalHeader().setDefaultSectionSize(row_height)

        # 设置表格高度
        header_height = 20
        max_visible_rows = 6
        table_height = row_height * max_visible_rows + header_height + 15
        table.setFixedHeight(table_height)

        return table

    def _setup_progress_section(self, layout):
        """设置进度显示部分UI"""
        self.progress_bar = ProgressBar(self)
        self.progress_label = BodyLabel("", self)
        self.progress_bar.hide()
        self.progress_label.hide()

        layout.addWidget(self.progress_bar)
        layout.addWidget(self.progress_label)

    def _populate_model_table(self):
        """填充模型表格数据"""
        self.model_table.setRowCount(len(FASTER_WHISPER_MODELS))
        for i, model in enumerate(FASTER_WHISPER_MODELS):
            self._add_model_row(i, model)

    def _add_model_row(self, row, model):
        """添加模型表格行"""
        # 模型名称
        name_item = QTableWidgetItem(model["label"])
        name_item.setTextAlignment(Qt.AlignCenter)  # type: ignore
        self.model_table.setItem(row, 0, name_item)

        # 大小
        size_item = QTableWidgetItem(f"{int(model['size']) / 1024:.1f} MB")
        size_item.setTextAlignment(Qt.AlignCenter)  # type: ignore
        self.model_table.setItem(row, 1, size_item)

        # 状态 - 检查model.bin文件是否存在
        model_path = os.path.join(MODEL_PATH, model["value"])
        model_bin_path = os.path.join(model_path, "model.bin")
        is_downloaded = os.path.exists(model_bin_path)

        status_item = QTableWidgetItem(
            self.tr("已下載") if is_downloaded else self.tr("未下載")
        )
        if is_downloaded:
            status_item.setForeground(Qt.green)  # type: ignore
        status_item.setTextAlignment(Qt.AlignCenter)  # type: ignore
        self.model_table.setItem(row, 2, status_item)

        # 下载按钮
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(4, 4, 4, 4)

        download_btn = HyperlinkButton(
            "",
            self.tr("重新下載") if is_downloaded else self.tr("下載"),
            parent=self,
        )
        download_btn.setIcon(FIF.DOWNLOAD)
        download_btn.clicked.connect(lambda checked, r=row: self._download_model(r))

        button_layout.addStretch()
        button_layout.addWidget(download_btn)
        button_layout.addStretch()
        self.model_table.setCellWidget(row, 3, button_container)

    def _connect_signals(self):
        """连接信号"""
        self.rejected.connect(self._on_dialog_reject)

    def _start_download(self):
        """开始下载"""
        if FasterWhisperDownloadDialog.is_downloading:
            InfoBar.warning(
                self.tr("下載進行中"),
                self.tr("請等待當前下載任務完成"),
                duration=3000,
                parent=self,
            )
            return

        FasterWhisperDownloadDialog.is_downloading = True
        # 禁用所有下载按钮
        self._set_all_download_buttons_enabled(False)

        # 获取选中的文本
        selected_text = self.program_combo.currentText()

        # 从显示文本中提取程序标签
        selected_label = selected_text.split(" (")[0]

        # 根据标签找到对应的程序配置
        program = next(
            (p for p in FASTER_WHISPER_PROGRAMS if p["label"] == selected_label), None
        )

        if not program:
            InfoBar.error(
                self.tr("下載錯誤"),
                self.tr("未找到對應的程序配置"),
                duration=3000,
                parent=self,
            )
            FasterWhisperDownloadDialog.is_downloading = False
            self._set_all_download_buttons_enabled(True)
            return

        # 确保 BIN_PATH 目录存在
        os.makedirs(BIN_PATH, exist_ok=True)

        self.progress_bar.show()
        self.progress_label.show()
        self.program_download_btn.setEnabled(False)
        self.program_combo.setEnabled(False)

        # 直接下载到bin目录
        save_path = os.path.join(BIN_PATH, program["value"])

        self.program_download_thread = FileDownloadThread(
            program["downloadLink"], save_path
        )
        self.program_download_thread.progress.connect(
            self._on_program_download_progress
        )
        self.program_download_thread.finished.connect(
            lambda: self._on_program_download_finished(save_path)
        )
        self.program_download_thread.error.connect(self._on_program_download_error)
        self.program_download_thread.start()

    def _on_program_download_progress(self, value, status_msg):
        """更新程序下载进度"""
        self.progress_bar.setValue(int(value))
        self.progress_label.setText(status_msg)

    def _on_program_download_finished(self, save_path):
        """程序下载完成处理"""
        try:
            # 检查是否是 CPU 版本的直接下载
            if save_path.endswith(".exe"):
                # 如果是exe文件,重命名为faster-whisper.exe
                os.rename(save_path, os.path.join(BIN_PATH, "faster-whisper.exe"))
                self._finish_program_installation()
            else:
                # GPU 版本需要解压
                self.progress_label.setText(self.tr("正在解壓文件..."))

                # 创建并启动解压线程
                self.unzip_thread = UnzipThread(save_path, BIN_PATH)
                self.unzip_thread.finished.connect(self._finish_program_installation)
                self.unzip_thread.error.connect(self._on_unzip_error)
                self.unzip_thread.start()
                return  # 提前返回,等待解压完成

        except Exception as e:
            InfoBar.error(self.tr("安裝失敗"), str(e), duration=3000, parent=self)
            self._cleanup_installation()

    def _on_program_download_error(self, error):
        """程序下载错误处理"""
        InfoBar.error(self.tr("下載失敗"), error, duration=3000, parent=self)
        FasterWhisperDownloadDialog.is_downloading = False
        self._set_all_download_buttons_enabled(True)
        self.program_download_btn.setEnabled(True)
        self.program_combo.setEnabled(True)
        self.progress_bar.hide()
        self.progress_label.hide()

    def _on_dialog_reject(self):
        """对话框关闭处理"""
        if self.program_download_thread and self.program_download_thread.isRunning():
            self.program_download_thread.stop()
        if self.model_download_thread and self.model_download_thread.isRunning():
            self.model_download_thread.terminate()
        FasterWhisperDownloadDialog.is_downloading = False
        self.reject()

    def closeEvent(self, event):
        """窗口关闭事件处理"""
        self._on_dialog_reject()
        super().closeEvent(event)

    def _download_model(self, row):
        """下载选中的模型"""
        if FasterWhisperDownloadDialog.is_downloading:
            InfoBar.warning(
                self.tr("下載進行中"),
                self.tr("請等待當前下載任務完成"),
                duration=3000,
                parent=self,
            )
            return

        FasterWhisperDownloadDialog.is_downloading = True
        self._set_all_download_buttons_enabled(False)

        model = FASTER_WHISPER_MODELS[row]
        self.progress_bar.show()
        self.progress_label.show()
        self.progress_label.setText(self.tr(f"正在下载 {model['label']} 模型..."))

        # 禁用当前行的下载按钮
        button_container = self.model_table.cellWidget(row, 3)
        download_btn = button_container.findChild(HyperlinkButton)
        if download_btn:
            download_btn.setEnabled(False)

        # 创建并启动下载线程，保存到类属性
        self.model_download_thread = ModelscopeDownloadThread(
            model["modelScopeLink"], os.path.join(MODEL_PATH, model["value"])
        )

        def _on_model_download_progress(value, msg):
            self.progress_bar.setValue(value)
            self.progress_label.setText(msg)

        def _on_model_download_finished():
            FasterWhisperDownloadDialog.is_downloading = False
            self._set_all_download_buttons_enabled(True)
            # 更新状态
            status_item = QTableWidgetItem(self.tr("已下載"))
            status_item.setForeground(Qt.green)  # type: ignore
            status_item.setTextAlignment(Qt.AlignCenter)  # type: ignore
            self.model_table.setItem(row, 2, status_item)

            # 更新下载按钮文本
            if download_btn:
                download_btn.setText(self.tr("重新下載"))
                download_btn.setEnabled(True)

            model = FASTER_WHISPER_MODELS[row]

            # 更新主设置对话框的模型选择
            if self.setting_widget:
                # 保存当前值并清空
                current_value = cfg.faster_whisper_model.value
                combo = self.setting_widget.model_card.comboBox
                combo.clear()

                # 找出已下载的模型
                available = []
                model_map = {
                    m["label"].lower(): m["value"] for m in FASTER_WHISPER_MODELS
                }
                for enum_val in FasterWhisperModelEnum:
                    if enum_val.value in model_map:
                        if (MODEL_PATH / model_map[enum_val.value]).exists():
                            available.append(enum_val)

                # 重建下拉框
                self.setting_widget.model_card.optionToText = {
                    e: e.value for e in available
                }
                for enum_val in available:
                    combo.addItem(enum_val.value, userData=enum_val)

                # 恢复选择
                if current_value in available:
                    combo.setCurrentText(current_value.value)
                elif combo.count() > 0:
                    combo.setCurrentIndex(0)

            InfoBar.success(
                self.tr("下載成功"),
                self.tr(f"{model['label']} 模型已下载完成"),
                duration=3000,
                parent=self,
            )
            self.progress_bar.hide()
            self.progress_label.hide()

        def _on_model_download_error(error):
            FasterWhisperDownloadDialog.is_downloading = False
            self._set_all_download_buttons_enabled(True)
            if download_btn:
                download_btn.setEnabled(True)

            InfoBar.error(self.tr("下載失敗"), str(error), duration=3000, parent=self)
            self.progress_bar.hide()
            self.progress_label.hide()

        self.model_download_thread.progress.connect(_on_model_download_progress)
        self.model_download_thread.finished.connect(_on_model_download_finished)
        self.model_download_thread.error.connect(_on_model_download_error)
        self.model_download_thread.start()

    def _set_all_download_buttons_enabled(self, enabled: bool):
        """设置所有下载按钮的启用状态"""
        # 设置程序下载按钮
        if hasattr(self, "program_download_btn"):
            self.program_download_btn.setEnabled(enabled)
            self.program_combo.setEnabled(enabled)

        # 设置所有模型下载按钮
        for row in range(self.model_table.rowCount()):
            button_container = self.model_table.cellWidget(row, 3)
            if button_container:
                download_btn = button_container.findChild(HyperlinkButton)
                if download_btn:
                    download_btn.setEnabled(enabled)

    def _open_model_folder(self):
        """打开模型文件夹"""
        if os.path.exists(MODEL_PATH):
            # 根据操作系统打开文件夹
            open_folder(str(MODEL_PATH))

    def _open_program_folder(self):
        """打开程序文件夹"""
        if os.path.exists(BIN_PATH):
            # 根据操作系统打开文件夹
            open_folder(str(BIN_PATH))

    def _finish_program_installation(self):
        """完成程序安装"""
        InfoBar.success(
            self.tr("安裝完成"),
            self.tr("Faster Whisper 程序已安裝成功"),
            duration=3000,
            parent=self,
        )
        self.accept()
        self._cleanup_installation()

    def _on_unzip_error(self, error_msg):
        """处理解压错误"""
        InfoBar.error(self.tr("安裝失敗"), error_msg, duration=3000, parent=self)
        self._cleanup_installation()

    def _cleanup_installation(self):
        """清理安装状态"""
        FasterWhisperDownloadDialog.is_downloading = False
        self._set_all_download_buttons_enabled(True)
        self.progress_bar.hide()
        self.progress_label.hide()


class FasterWhisperSettingWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self._connect_signals()

    def showEvent(self, a0: QShowEvent) -> None:
        super().showEvent(a0)
        # 检查Faster Whisper模型是否存在
        is_faster_whisper_exists, _ = check_faster_whisper_exists()
        if not is_faster_whisper_exists:
            self.show_error_info(self.tr("Faster Whisper程序不存在，請先下載程序"))
            self._show_model_manager()
        return

    def setup_ui(self):
        self.main_layout = QVBoxLayout(self)

        # 创建单向滚动区域和容器
        self.scrollArea = SingleDirectionScrollArea(orient=Qt.Vertical, parent=self)  # type: ignore
        self.scrollArea.setStyleSheet(
            "QScrollArea{background: transparent; border: none}"
        )

        self.container = QWidget(self)
        self.container.setStyleSheet("QWidget{background: transparent}")
        self.containerLayout = QVBoxLayout(self.container)

        self.setting_group = SettingCardGroup(
            self.tr("Faster Whisper 設置"), self
        )

        # 模型选择
        self.model_card = ComboBoxSettingCard(
            cfg.faster_whisper_model,
            FIF.ROBOT,
            self.tr("模型"),
            self.tr("選擇 Faster Whisper 模型"),
            [model.value for model in FasterWhisperModelEnum],
            self.setting_group,
        )

        # 检查未下载的模型并从下拉框中移除
        for i in range(self.model_card.comboBox.count() - 1, -1, -1):
            model_text = self.model_card.comboBox.itemText(i).lower()
            model_config = next(
                (
                    model
                    for model in FASTER_WHISPER_MODELS
                    if model["label"].lower() == model_text
                ),
                None,
            )
            if model_config:
                model_path = Path(MODEL_PATH) / model_config["value"]
                model_bin_path = model_path / "model.bin"
                if model_bin_path.exists():
                    continue
            self.model_card.comboBox.removeItem(i)

        # 创建管理模型卡片
        self.manage_model_card = HyperlinkCard(
            "",  # 无链接
            self.tr("管理模型"),
            FIF.DOWNLOAD,  # 使用下载图标
            self.tr("模型管理"),
            self.tr("下載或更新 Faster Whisper 模型"),
            self.setting_group,  # 添加到设置组
        )

        # 语言选择
        self.language_card = ComboBoxSettingCard(
            cfg.transcribe_language,
            FIF.LANGUAGE,
            self.tr("源語言"),
            self.tr("音視頻中説話的語言，默認根據前30秒自動識別"),
            [lang.value for lang in TranscribeLanguageEnum],
            self.setting_group,
        )
        self.language_card.comboBox.setMaxVisibleItems(6)

        # 设备选择
        self.device_card = ComboBoxSettingCard(
            cfg.faster_whisper_device,
            FIF.IOT,
            self.tr("運行設備"),
            self.tr("模型運行設備"),
            ["cuda", "cpu"],
            self.setting_group,
        )
        # _, available_devices = check_faster_whisper_exists()
        # if "GPU" not in available_devices:
        #     self.device_card.comboBox.removeItem(0)

        # VAD设置组
        self.vad_group = SettingCardGroup(self.tr("VAD設置"), self)

        # VAD过滤开关
        self.vad_filter_card = SwitchSettingCard(
            FIF.CHECKBOX,
            self.tr("VAD過濾"),
            self.tr("過濾無人聲語音片斷，減少幻覺"),
            cfg.faster_whisper_vad_filter,
            self.vad_group,
        )

        # VAD阈值
        self.vad_threshold_card = DoubleSpinBoxSettingCard(
            cfg.faster_whisper_vad_threshold,
            FIF.VOLUME,  # type: ignore
            self.tr("VAD閾值"),
            self.tr("語音概率閾值，高於此值視為語音"),
            minimum=0.00,
            maximum=1.00,
            decimals=2,
            step=0.05,
        )

        # VAD方法
        self.vad_method_card = ComboBoxSettingCard(
            cfg.faster_whisper_vad_method,
            FIF.MUSIC,
            self.tr("VAD方法"),
            self.tr("選擇VAD檢測方法"),
            [method.value for method in VadMethodEnum],
            self.vad_group,
        )

        # 其他设置组
        self.other_group = SettingCardGroup(self.tr("其他設置"), self)

        # 音频降噪
        self.ff_mdx_kim2_card = SwitchSettingCard(
            FIF.MUSIC,
            self.tr("人聲分離"),
            self.tr("處理前使用MDX-Net降噪，分離人聲和背景音樂"),
            cfg.faster_whisper_ff_mdx_kim2,
            self.other_group,
        )

        # 单词时间戳
        self.one_word_card = SwitchSettingCard(
            FIF.UNIT,
            self.tr("單字時間戳"),
            self.tr("開啓生成單字級時間戳；關閉後使用原始分段斷句"),
            cfg.faster_whisper_one_word,
            self.other_group,
        )

        # 提示词
        self.prompt_card = LineEditSettingCard(
            cfg.faster_whisper_prompt,
            FIF.CHAT,
            self.tr("提示詞"),
            self.tr("可選的提示詞,默認空"),
            "",
            self.other_group,
        )

        # 添加模型设置组的卡片
        self.setting_group.addSettingCard(self.model_card)
        self.setting_group.addSettingCard(self.manage_model_card)
        self.setting_group.addSettingCard(self.device_card)
        self.setting_group.addSettingCard(self.language_card)

        # 添加VAD设置组的卡片
        self.vad_group.addSettingCard(self.vad_filter_card)
        self.vad_group.addSettingCard(self.vad_threshold_card)
        self.vad_group.addSettingCard(self.vad_method_card)

        # 添加其他设置的卡片
        self.other_group.addSettingCard(self.ff_mdx_kim2_card)
        self.other_group.addSettingCard(self.one_word_card)
        self.other_group.addSettingCard(self.prompt_card)

        # ==================== 提示詞檔案選擇 ====================
        from app.config import WHISPER_PROMPTS_PATH

        self.prompt_title = SubtitleLabel(self.tr("提示詞檔案"), self)

        self.prompt_files_container = QWidget(self)
        self.prompt_files_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        prompt_files_layout = QVBoxLayout(self.prompt_files_container)
        prompt_files_layout.setContentsMargins(0, 4, 16, 24)
        prompt_files_layout.setSpacing(12)

        desc_label = BodyLabel(
            self.tr("勾選要在轉錄時參考的提示詞檔案（檔案位於 resource/whisper_prompts/）")
        )
        desc_label.setWordWrap(True)
        prompt_files_layout.addWidget(desc_label)

        # 掃描資料夾中的 .txt 檔案
        self.prompt_checkboxes = {}
        prompt_path = Path(WHISPER_PROMPTS_PATH)
        selected_str = cfg.selected_whisper_prompts.value or ""
        selected_set = set(s.strip() for s in selected_str.split(",") if s.strip())

        txt_files = sorted(prompt_path.glob("*.txt"))
        if txt_files:
            grid = QGridLayout()
            grid.setSpacing(16)
            for i, f in enumerate(txt_files):
                cb = CheckBox(f.stem)
                cb.setChecked(f.name in selected_set)
                cb.stateChanged.connect(self._on_prompt_file_toggled)
                self.prompt_checkboxes[f.name] = cb
                grid.addWidget(cb, i // 4, i % 4)
            prompt_files_layout.addLayout(grid)
        else:
            no_file_label = BodyLabel(self.tr("（尚無提示詞檔案）"))
            prompt_files_layout.addWidget(no_file_label)

        # 開啟資料夾按鈕
        open_prompts_btn = HyperlinkButton("", self.tr("開啟提示詞資料夾"), parent=self)
        open_prompts_btn.setIcon(FIF.FOLDER)
        open_prompts_btn.clicked.connect(lambda: open_folder(str(WHISPER_PROMPTS_PATH)))
        prompt_files_layout.addWidget(open_prompts_btn)

        # 将所有设置组添加到容器布局
        self.containerLayout.addWidget(self.prompt_title)
        self.containerLayout.addWidget(self.prompt_files_container)
        self.containerLayout.addWidget(self.setting_group)
        self.containerLayout.addWidget(self.vad_group)
        self.containerLayout.addWidget(self.other_group)
        self.containerLayout.addStretch(1)

        # 设置组件最小宽度
        self.model_card.comboBox.setMinimumWidth(200)
        self.device_card.comboBox.setMinimumWidth(200)
        self.language_card.comboBox.setMinimumWidth(200)
        self.vad_method_card.comboBox.setMinimumWidth(200)
        self.prompt_card.lineEdit.setMinimumWidth(200)

        # 设置滚动区域
        self.scrollArea.setWidget(self.container)
        self.scrollArea.setWidgetResizable(True)

        # 将滚动区域添加到主布局
        self.main_layout.addWidget(self.scrollArea)

    def _connect_signals(self):
        """连接信号"""
        self.manage_model_card.linkButton.clicked.connect(self._show_model_manager)
        self.vad_filter_card.checkedChanged.connect(self._on_vad_filter_changed)

    def _on_prompt_file_toggled(self, state):
        """提示詞檔案勾選狀態改變時，儲存到設定"""
        selected = [
            name for name, cb in self.prompt_checkboxes.items() if cb.isChecked()
        ]
        cfg.set(cfg.selected_whisper_prompts, ",".join(selected))

    def _on_vad_filter_changed(self, checked: bool):
        """VAD过滤开关状态改变时的处理"""
        self.vad_threshold_card.setEnabled(checked)
        self.vad_method_card.setEnabled(checked)

    def _show_model_manager(self):
        """显示模型管理对话框"""
        dialog = FasterWhisperDownloadDialog(self.window(), self)
        dialog.exec_()

    def show_error_info(self, error_msg):
        """显示错误信息"""
        InfoBar.error(
            title=self.tr("錯誤"),
            content=error_msg,
            parent=self.window(),
            duration=5000,
            position=InfoBarPosition.BOTTOM,
        )

    def check_faster_whisper_model(self):
        """检查选定的Faster Whisper模型是否存在

        Returns:
            bool: 如果模型存在且配置正确返回True，否则返回False
        """
        # 检查程序是否存在
        has_program, _ = check_faster_whisper_exists()
        if not has_program:
            self.show_error_info(self.tr("Faster Whisper程序不存在，請先下載程序"))
            return False

        model_value = cfg.faster_whisper_model.value.value
        # 检查模型配置是否存在
        model_config = next(
            (
                m
                for m in FASTER_WHISPER_MODELS
                if m["label"].lower() == model_value.lower()
            ),
            None,
        )
        if not model_config:
            self.show_error_info(self.tr("模型配置不存在"))
            return False

        model_path = MODEL_PATH / model_config["value"]
        model_files = model_path / "model.bin"
        # 检查模型文件是否存在
        if not model_path.exists() and not model_files.exists():
            self.show_error_info(self.tr("模型文件不存在: ") + model_value)
            return False
        return True
