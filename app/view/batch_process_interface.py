import os

from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtGui import QColor, QDesktopServices, QFont
from PyQt5.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    Action,
    ComboBox,
    InfoBar,
    InfoBarPosition,
    ProgressBar,
    PushButton,
    RoundMenu,
    TableWidget,
)
from qfluentwidgets import (
    FluentIcon as FIF,
)

from app.common.config import cfg
from app.common.signal_bus import signalBus
from app.components.TranscriptionSettingDialog import TranscriptionSettingDialog
from app.core.constant import (
    INFOBAR_DURATION_INFO,
    INFOBAR_DURATION_SUCCESS,
    INFOBAR_DURATION_WARNING,
)
from app.core.entities import (
    BatchTaskStatus,
    BatchTaskType,
    FasterWhisperModelEnum,
    FileConflictPolicy,
    SupportedAudioFormats,
    SupportedSubtitleFormats,
    SupportedVideoFormats,
    TranscribeModelEnum,
)
from app.core.utils.platform_utils import get_available_transcribe_models
from app.components.folder_dialog import FolderSelectionDialog
from app.thread.batch_process_thread import (
    BatchProcessThread,
    BatchTask,
)


class BatchProcessInterface(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("batchProcessInterface")
        self.setWindowTitle(self.tr("批量處理"))
        self.setAcceptDrops(True)
        self.batch_thread = BatchProcessThread()

        self.init_ui()
        self.setup_connections()

    def init_ui(self):
        # 创建主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(8)

        # 顶部控制区域
        top_layout = QHBoxLayout()
        top_layout.setSpacing(8)

        # 任务类型选择
        self.task_type_combo = ComboBox()
        self.task_type_combo.addItems([str(task_type) for task_type in BatchTaskType])
        self.task_type_combo.setCurrentText(str(BatchTaskType.TRANSCRIBE))

        # 辨識模型選擇
        self.model_combo = ComboBox()
        available_models = get_available_transcribe_models()
        self.model_combo.addItems([model.value for model in available_models])
        # 同步當前全域設定的模型
        current_model_value = cfg.get(cfg.transcribe_model).value
        self.model_combo.setCurrentText(current_model_value)

        # FasterWhisper 子模型選擇 (tiny/base/small/medium/large 等)
        self.sub_model_combo = ComboBox()
        self.sub_model_combo.addItems([m.value for m in FasterWhisperModelEnum])
        current_sub_model = cfg.get(cfg.faster_whisper_model).value
        self.sub_model_combo.setCurrentText(current_sub_model)
        # 僅在 FasterWhisper 被選中時顯示
        self.sub_model_combo.setVisible(
            current_model_value == TranscribeModelEnum.FASTER_WHISPER.value
        )

        # 任务类型说明
        self.task_type_descriptions = {
            str(BatchTaskType.TRANSCRIBE): self.tr("僅進行語音識別，生成字幕文件"),
            str(BatchTaskType.SUBTITLE): self.tr("對已有字幕進行分割、優化或翻譯"),
            str(BatchTaskType.TRANS_SUB): self.tr("先轉錄再處理字幕，不合成視頻"),
            str(BatchTaskType.FULL_PROCESS): self.tr("轉錄 → 字幕處理 → 合成視頻"),
        }

        # 控制按钮
        self.add_file_btn = PushButton(self.tr("添加文件"), icon=FIF.ADD)
        self.add_folder_btn = PushButton(self.tr("添加文件夾"), icon=FIF.FOLDER)
        self.start_all_btn = PushButton(self.tr("開始處理"), icon=FIF.PLAY)
        self.clear_btn = PushButton(self.tr("清空列表"), icon=FIF.DELETE)

        # 添加到顶部布局
        top_layout.addWidget(self.task_type_combo)
        top_layout.addWidget(self.model_combo)
        top_layout.addWidget(self.sub_model_combo)
        top_layout.addWidget(self.add_file_btn)
        top_layout.addWidget(self.add_folder_btn)
        top_layout.addWidget(self.clear_btn)

        # 设置按钮
        self.setting_btn = PushButton(self.tr("轉錄設置"), icon=FIF.SETTING)
        top_layout.addWidget(self.setting_btn)

        # 檔案衝突處理策略
        self.conflict_combo = ComboBox()
        self.conflict_combo.addItems([str(p) for p in FileConflictPolicy])
        self.conflict_combo.setCurrentText(str(cfg.get(cfg.file_conflict_policy)))
        top_layout.addWidget(self.conflict_combo)

        top_layout.addStretch()
        top_layout.addWidget(self.start_all_btn)

        # 创建任务表格
        self.task_table = TableWidget()
        self.task_table.setColumnCount(3)
        self.task_table.setHorizontalHeaderLabels([self.tr("文件名"), self.tr("進度"), self.tr("狀態")])

        # 设置表格样式
        self.task_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.task_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Fixed)
        self.task_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Fixed)
        self.task_table.setColumnWidth(1, 250)  # 进度条列宽
        self.task_table.setColumnWidth(2, 160)  # 状态列宽

        # 设置行高
        self.task_table.verticalHeader().setDefaultSectionSize(40)  # 设置默认行高

        # 设置表格边框
        self.task_table.setBorderVisible(True)
        self.task_table.setBorderRadius(12)

        # 设置表格不可编辑
        self.task_table.setEditTriggers(QTableWidget.NoEditTriggers)

        # 设置表格大小策略
        self.task_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.task_table.setMinimumHeight(300)  # 设置最小高度

        # 连接双击信号
        self.task_table.doubleClicked.connect(self.on_table_double_clicked)

        # 添加到主布局
        main_layout.addLayout(top_layout)
        main_layout.addWidget(self.task_table)

        # 连接信号
        self.add_file_btn.clicked.connect(self.on_add_file_clicked)
        self.add_folder_btn.clicked.connect(self.on_add_folder_clicked)
        self.start_all_btn.clicked.connect(self.start_all_tasks)
        self.clear_btn.clicked.connect(self.clear_tasks)
        self.setting_btn.clicked.connect(self.on_setting_clicked)
        self.task_type_combo.currentTextChanged.connect(self.on_task_type_changed)
        self.model_combo.currentTextChanged.connect(self.on_model_changed)
        self.sub_model_combo.currentTextChanged.connect(self.on_sub_model_changed)
        self.conflict_combo.currentTextChanged.connect(self.on_conflict_policy_changed)

    def setup_connections(self):
        # 批处理线程信号连接
        self.batch_thread.task_progress.connect(self.update_task_progress)
        self.batch_thread.task_error.connect(self.on_task_error)
        self.batch_thread.task_completed.connect(self.on_task_completed)

        # 從設定頁同步模型變更
        signalBus.transcription_model_changed.connect(self._on_global_model_changed)

        # 表格右键菜单
        self.task_table.setContextMenuPolicy(Qt.CustomContextMenu)  # type: ignore
        self.task_table.customContextMenuRequested.connect(self.show_context_menu)

    def on_add_file_clicked(self):
        task_type = self.task_type_combo.currentText()
        file_filter = ""
        if task_type in [
            BatchTaskType.TRANSCRIBE,
            BatchTaskType.TRANS_SUB,
            BatchTaskType.FULL_PROCESS,
        ]:
            # 获取所有支持的音视频格式
            audio_formats = [f"*.{fmt.value}" for fmt in SupportedAudioFormats]
            video_formats = [f"*.{fmt.value}" for fmt in SupportedVideoFormats]
            formats = audio_formats + video_formats
            file_filter = f"{self.tr('音視頻文件')} ({' '.join(formats)})"
        elif task_type == BatchTaskType.SUBTITLE:
            # 获取所有支持的字幕格式
            subtitle_formats = [f"*.{fmt.value}" for fmt in SupportedSubtitleFormats]
            file_filter = f"{self.tr('字幕文件')} ({' '.join(subtitle_formats)})"

        files, _ = QFileDialog.getOpenFileNames(self, self.tr("選擇文件"), "", file_filter)
        if files:
            self.add_files(files)

    def on_add_folder_clicked(self):
        try:
            self._on_add_folder_clicked_impl()
        except Exception as e:
            import traceback
            traceback.print_exc()
            InfoBar.error(
                title="Error",
                content=str(e),
                duration=10000,
                position=InfoBarPosition.TOP,
                parent=self,
            )

    def _on_add_folder_clicked_impl(self):
        folder_path = QFileDialog.getExistingDirectory(self, self.tr("選擇文件夾"), "")
        if not folder_path:
            return

        task_type = BatchTaskType(self.task_type_combo.currentText())
        
        # 递归扫描文件夹
        all_files = []
        for root, _, files in os.walk(folder_path):
            for file in files:
                all_files.append(os.path.join(root, file))
                
        # 过滤有效文件
        valid_files = self.filter_files(all_files, task_type)
        valid_files.sort(key=lambda x: x.lower())

        if not valid_files:
            InfoBar.warning(
                title=self.tr("未找到文件"),
                content=self.tr("該文件夾內沒有找到與當前任務類型匹配的支持文件"),
                duration=INFOBAR_DURATION_WARNING,
                position=InfoBarPosition.TOP,
                parent=self,
            )
            return

        # 弹出选择窗口
        dialog = FolderSelectionDialog(self, valid_files)
        if dialog.exec():
            selected_files = dialog.get_selected_files()
            if selected_files:
                self.add_files(selected_files)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        files = [url.toLocalFile() for url in event.mimeData().urls()]
        self.add_files(files)

    def add_files(self, file_paths):
        task_type = BatchTaskType(self.task_type_combo.currentText())

        # 检查文件是否存在并收集不存在的文件
        non_existent_files = []
        valid_files = []
        for file_path in file_paths:
            if not os.path.exists(file_path):
                non_existent_files.append(os.path.basename(file_path))
            else:
                valid_files.append(file_path)

        # 如果有不存在的文件，显示警告
        if non_existent_files:
            InfoBar.warning(
                title=self.tr("文件不存在"),
                content=f"{self.tr('以下文件不存在：')}\n{', '.join(non_existent_files)}",
                duration=INFOBAR_DURATION_WARNING,
                position=InfoBarPosition.TOP,
                parent=self,
            )

        # 如果没有有效文件，直接返回
        if not valid_files:
            return

        # 对有效文件按文件名排序
        valid_files.sort(key=lambda x: os.path.basename(x).lower())

        # 如果表格为空，自动检测文件类型并设置任务类型
        if self.task_table.rowCount() == 0 and self.task_type_combo.currentIndex() == 0:
            first_file = valid_files[0].lower()
            is_subtitle = any(
                first_file.endswith(f".{fmt.value}") for fmt in SupportedSubtitleFormats
            )
            if is_subtitle:
                self.task_type_combo.setCurrentText(str(BatchTaskType.SUBTITLE))
                task_type = BatchTaskType.SUBTITLE
            # elif is_media:
            #     self.task_type_combo.setCurrentText(str(BatchTaskType.FULL_PROCESS))
            #     task_type = BatchTaskType.FULL_PROCESS

        # 过滤文件类型
        valid_files = self.filter_files(valid_files, task_type)

        if not valid_files:
            InfoBar.warning(
                title="无效文件",
                content="请选择正确的文件类型",
                duration=INFOBAR_DURATION_WARNING,
                position=InfoBarPosition.TOP,
                parent=self,
            )
            return

        for file_path in valid_files:
            # 检查是否已存在相同任务
            exists = False
            for row in range(self.task_table.rowCount()):
                if self.task_table.item(row, 0).toolTip() == file_path:
                    exists = True
                    InfoBar.warning(
                        title="任务已存在",
                        content="任务已存在",
                        duration=INFOBAR_DURATION_WARNING,
                        position=InfoBarPosition.TOP_RIGHT,
                        parent=self,
                    )
                    break

            if not exists:
                self.add_task_to_table(file_path)

    def filter_files(self, file_paths, task_type: BatchTaskType):
        valid_extensions = {}

        # 根据任务类型设置有效的扩展名
        if task_type in [
            BatchTaskType.TRANSCRIBE,
            BatchTaskType.TRANS_SUB,
            BatchTaskType.FULL_PROCESS,
        ]:
            valid_extensions = {f".{fmt.value}" for fmt in SupportedAudioFormats} | {
                f".{fmt.value}" for fmt in SupportedVideoFormats
            }
        elif task_type == BatchTaskType.SUBTITLE:
            valid_extensions = {f".{fmt.value}" for fmt in SupportedSubtitleFormats}

        return [
            f
            for f in file_paths
            if any(f.lower().endswith(ext) for ext in valid_extensions)
        ]

    def add_task_to_table(self, file_path):
        row = self.task_table.rowCount()
        self.task_table.insertRow(row)

        # 文件名
        file_name = QTableWidgetItem(os.path.basename(file_path))
        file_name.setToolTip(file_path)
        self.task_table.setItem(row, 0, file_name)

        # 进度条
        progress_bar = ProgressBar()
        progress_bar.setRange(0, 100)
        progress_bar.setValue(0)
        progress_bar.setFixedHeight(18)
        self.task_table.setCellWidget(row, 1, progress_bar)

        # 状态
        status = QTableWidgetItem(str(BatchTaskStatus.WAITING))
        status.setTextAlignment(Qt.AlignCenter)  # type: ignore
        status.setForeground(Qt.gray)  # type: ignore  # 设置字体颜色为灰色
        font = QFont()
        font.setBold(True)
        status.setFont(font)
        self.task_table.setItem(row, 2, status)

    def show_context_menu(self, pos):
        row = self.task_table.rowAt(pos.y())
        if row < 0:
            return

        menu = RoundMenu(parent=self)
        file_path = self.task_table.item(row, 0).toolTip()
        status = self.task_table.item(row, 2).text()

        start_action = Action(FIF.PLAY, "开始")
        start_action.triggered.connect(lambda: self.start_task(file_path))
        menu.addAction(start_action)

        cancel_action = Action(FIF.CLOSE, "取消")
        cancel_action.triggered.connect(lambda: self.cancel_task(file_path))
        menu.addAction(cancel_action)

        menu.addSeparator()
        open_folder_action = Action(FIF.FOLDER, "打开输出文件夹")
        open_folder_action.triggered.connect(lambda: self.open_output_folder(file_path))
        menu.addAction(open_folder_action)

        if status != str(BatchTaskStatus.WAITING):
            start_action.setEnabled(False)

        menu.exec_(self.task_table.viewport().mapToGlobal(pos))

    def open_output_folder(self, file_path: str):
        # 根据任务类型和文件路径确定输出文件夹
        task_type = BatchTaskType(self.task_type_combo.currentText())
        file_dir = os.path.dirname(file_path)

        if task_type == BatchTaskType.FULL_PROCESS:
            # 对于全流程任务，输出在视频同目录下
            output_dir = file_dir
        else:
            # 其他任务输出在文件同目录下
            output_dir = file_dir

        # 打开文件夹
        QDesktopServices.openUrl(QUrl.fromLocalFile(output_dir))

    def update_task_progress(self, file_path: str, progress: int, status: str):
        for row in range(self.task_table.rowCount()):
            if self.task_table.item(row, 0).toolTip() == file_path:
                # 更新进度条
                progress_bar = self.task_table.cellWidget(row, 1)
                progress_bar.setValue(progress)
                # 更新状态
                self.task_table.item(row, 2).setText(status)
                break

    def on_task_error(self, file_path: str, error: str):
        for row in range(self.task_table.rowCount()):
            if self.task_table.item(row, 0).toolTip() == file_path:
                status_item = self.task_table.item(row, 2)
                status_item.setText(str(BatchTaskStatus.FAILED))
                status_item.setToolTip(error)
                break

    def on_task_completed(self, file_path: str):
        for row in range(self.task_table.rowCount()):
            if self.task_table.item(row, 0).toolTip() == file_path:
                self.task_table.item(row, 2).setText(str(BatchTaskStatus.COMPLETED))
                self.task_table.item(row, 2).setForeground(QColor("#13A10E"))
                break

    def start_all_tasks(self):
        # 检查是否有任务
        if self.task_table.rowCount() == 0:
            InfoBar.warning(
                title="无任务",
                content="请先添加需要处理的文件",
                duration=INFOBAR_DURATION_WARNING,
                position=InfoBarPosition.TOP,
                parent=self,
            )
            return

        # 检查是否有等待处理的任务
        waiting_tasks = 0
        for row in range(self.task_table.rowCount()):
            if self.task_table.item(row, 2).text() == str(BatchTaskStatus.WAITING):
                waiting_tasks += 1

        if waiting_tasks == 0:
            InfoBar.warning(
                title="无待处理任务",
                content="所有任务已经在处理或已完成",
                duration=INFOBAR_DURATION_WARNING,
                position=InfoBarPosition.TOP,
                parent=self,
            )
            return

        # 显示开始处理的提示
        InfoBar.success(
            title=self.tr("開始處理"),
            content=f"开始处理 {waiting_tasks} 个任务",
            duration=INFOBAR_DURATION_SUCCESS,
            position=InfoBarPosition.TOP,
            parent=self,
        )
        # 开始处理任务
        for row in range(self.task_table.rowCount()):
            file_path = self.task_table.item(row, 0).toolTip()
            status = self.task_table.item(row, 2).text()
            if status == str(BatchTaskStatus.WAITING):
                task_type = BatchTaskType(self.task_type_combo.currentText())
                batch_task = BatchTask(file_path, task_type)
                self.batch_thread.add_task(batch_task)

    def start_task(self, file_path: str):
        # 显示开始处理的提示
        file_name = os.path.basename(file_path)
        InfoBar.success(
            title=self.tr("開始處理"),
            content=f"开始处理文件：{file_name}",
            duration=INFOBAR_DURATION_SUCCESS,
            position=InfoBarPosition.TOP,
            parent=self,
        )

        # 创建并添加单个任务
        task_type = BatchTaskType(self.task_type_combo.currentText())
        batch_task = BatchTask(file_path, task_type)
        self.batch_thread.add_task(batch_task)

    def cancel_task(self, file_path: str):
        self.batch_thread.stop_task(file_path)
        # 从表格中移除任务
        for row in range(self.task_table.rowCount()):
            if self.task_table.item(row, 0).toolTip() == file_path:
                self.task_table.removeRow(row)
                break

    def clear_tasks(self):
        self.batch_thread.stop_all()
        self.task_table.setRowCount(0)

    def on_task_type_changed(self, task_type: str):
        # 显示任务类型说明
        description = self.task_type_descriptions.get(task_type, "")
        if description:
            InfoBar.info(
                title=task_type,
                content=description,
                duration=INFOBAR_DURATION_INFO,
                position=InfoBarPosition.BOTTOM,
                parent=self,
            )
        # 字幕處理不需要轉錄模型，隱藏模型選擇器
        is_subtitle = task_type == str(BatchTaskType.SUBTITLE)
        self.model_combo.setVisible(not is_subtitle)
        # 子模型也要跟著隱藏
        if is_subtitle:
            self.sub_model_combo.setVisible(False)
        else:
            self.sub_model_combo.setVisible(
                self.model_combo.currentText() == TranscribeModelEnum.FASTER_WHISPER.value
            )
        # 清空当前任务列表
        self.clear_tasks()

    def on_model_changed(self, model_name: str):
        """批次頁模型選擇變更，同步到全域設定"""
        for model in TranscribeModelEnum:
            if model.value == model_name:
                cfg.set(cfg.transcribe_model, model)
                break
        # FasterWhisper 時顯示子模型選擇
        self.sub_model_combo.setVisible(
            model_name == TranscribeModelEnum.FASTER_WHISPER.value
        )

    def on_sub_model_changed(self, sub_model_name: str):
        """FasterWhisper 子模型變更，同步到全域設定"""
        for model in FasterWhisperModelEnum:
            if model.value == sub_model_name:
                cfg.set(cfg.faster_whisper_model, model)
                break

    def _on_global_model_changed(self, model_name: str):
        """從設定頁或轉錄頁同步模型變更"""
        self.model_combo.blockSignals(True)
        self.model_combo.setCurrentText(model_name)
        self.model_combo.blockSignals(False)

    def on_conflict_policy_changed(self, policy_name: str):
        """檔案衝突處理策略變更"""
        for policy in FileConflictPolicy:
            if str(policy) == policy_name:
                cfg.set(cfg.file_conflict_policy, policy)
                break

    def on_setting_clicked(self):
        """显示转录设置对话框"""
        dialog = TranscriptionSettingDialog(self.window())
        dialog.exec_()

    def closeEvent(self, event):
        self.batch_thread.stop_all()
        super().closeEvent(event)

    def on_table_double_clicked(self, index):
        """处理表格双击事件"""
        row = index.row()
        file_path = self.task_table.item(row, 0).toolTip()
        self.open_output_folder(file_path)
