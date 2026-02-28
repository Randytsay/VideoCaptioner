"""OpenCC 簡繁轉換器"""

import opencc
import time
from typing import Dict, List, Optional, Callable
from app.core.entities import SubtitleProcessData
from app.core.translate.base import BaseTranslator
from app.core.translate.types import TargetLanguage
from app.core.utils.logger import setup_logger

logger = setup_logger("opencc_translator")


class OpenCCTranslator(BaseTranslator):
    """OpenCC 簡繁轉換器 (離線)"""

    def __init__(
        self,
        thread_num: int = 1,
        batch_num: int = 50,  # OpenCC is fast, so batch size can be larger
        target_language: Optional[TargetLanguage] = None,
        timeout: int = 10,
        update_callback: Optional[Callable] = None,
    ):
        super().__init__(
            thread_num, batch_num, target_language, timeout, update_callback
        )
        self.converter = None
        self._init_converter()

    def _init_converter(self):
        """初始化 OpenCC 轉換器"""
        try:
            # s2t: 簡體到繁體 (默認)
            # t2s: 繁體到簡體
            config = "s2t.json"
            if self.target_language == TargetLanguage.SIMPLIFIED_CHINESE:
                config = "t2s.json"
            elif self.target_language == TargetLanguage.TRADITIONAL_CHINESE:
                # 預設：簡體到繁體 (台灣正體)
                config = "s2twp.json" # s2twp: Simplified to Traditional (Taiwan Standard) with phrases

            self.converter = opencc.OpenCC(config)
            logger.info(f"OpenCC 轉換器初始化成功 (設定檔: {config})")
        except Exception as e:
            logger.error(f"OpenCC 轉換器初始化失敗: {str(e)}")

    def _do_translate(self, texts: List[str]) -> List[str]:
        """執行轉換"""
        if not self.converter:
            logger.warning("OpenCC 轉換器未初始化，返回原文")
            return texts
            
        try:
            return [self.converter.convert(text) for text in texts]
        except Exception as e:
            logger.error(f"OpenCC 轉換失敗: {str(e)}")
            return texts

    def process_batch(self, batch_data: List[SubtitleProcessData]) -> None:
        """處理單個批次的資料"""
        if not batch_data:
            return
            
        texts = [data.original_text for data in batch_data]
        
        try:
            converted_texts = self._do_translate(texts)
            
            for index, data in enumerate(batch_data):
                if index < len(converted_texts):
                    data.translated_text = converted_texts[index]
                else:
                    data.translated_text = data.original_text
                    
        except Exception as e:
            logger.error(f"OpenCC 批次處理失敗: {str(e)}")
            for data in batch_data:
                data.translated_text = data.original_text
    
    def test_connection(self) -> bool:
        """測試轉換器是否可用"""
        try:
            if not self.converter:
                self._init_converter()
            if self.converter:
                self.converter.convert("测试")
                return True
        except Exception as e:
            logger.error(f"OpenCC 測試失敗: {str(e)}")
        return False
