<div align="center">
  <img src="./legacy-docs/images/logo.png"alt="VideoCaptioner Logo" width="100">
  <p>卡卡字幕助手</p>
  <h1>VideoCaptioner</h1>
  <p>一款基於大型語言模型 (LLM) 的影片字幕處理助手，支援語音辨識、字幕斷句、優化、翻譯全流程處理</p>

[简体中文](./legacy-docs/README.md) / 正體中文 / [English](./legacy-docs/README_EN.md) / [日本語](./legacy-docs/README_JA.md)

📚 **[線上文件](https://weifeng2333.github.io/VideoCaptioner/)** | 🚀 **[快速開始](https://weifeng2333.github.io/VideoCaptioner/guide/getting-started)** | ⚙️ **[配置指南](https://weifeng2333.github.io/VideoCaptioner/config/llm)**

</div>

## 專案介紹

卡卡字幕助手（VideoCaptioner）操作簡單且無需高配置，支援 API 和本地離線兩種方式進行語音辨識，利用大型語言模型 (LLM) 進行字幕智能斷句、校正、翻譯，字幕影片全流程一鍵處理。為影片配上效果驚豔的字幕。

- 支援詞級時間戳與 VAD 語音活動檢測，辨識準確率高
- 基於 LLM 的語意理解，自動將逐字字幕重組為自然流暢的句子段落
- 結合上下文的 AI 翻譯，支援反思優化機制，譯文道地專業
- 支援批次處理影片字幕合成，提升處理效率
- 直觀的字幕編輯查看介面，支援即時預覽和快捷編輯

## 介面預覽

<div align="center">
  <img src="https://h1.appinn.me/file/1731487405884_main.png" alt="軟體介面預覽" width="90%" style="border-radius: 5px;">
</div>

![頁面預覽](https://h1.appinn.me/file/1731487410170_preview1.png)
![頁面預覽](https://h1.appinn.me/file/1731487410832_preview2.png)

## 測試

全流程處理一個 14 分鐘 1080P 的 [B 站英文 TED 影片](https://www.bilibili.com/video/BV1jT411X7Dz)，呼叫本地 Whisper 模型進行語音辨識，使用 `gpt-5-mini` 模型優化和翻譯為中文，總共消耗時間約 **4 分鐘**。

僅計算後台費用，模型優化和翻譯消耗費用不足 ￥0.01（以 OpenAI 官方價格為計算）。

具體字幕和影片合成的效果測試結果圖片，請參考 [TED 影片測試](./legacy-docs/test.md)。

## 快速開始

### Windows 用戶

#### 方式一：使用打包程式（推薦）

軟體較為輕量，打包大小不足 60MB，已整合所有必要環境，下載後可直接執行。

1. 從 [Release](https://github.com/WEIFENG2333/VideoCaptioner/releases) 頁面下載最新版本的執行檔。或者：[藍奏雲端空間下載](https://wwwm.lanzoue.com/ii14G2pdsbej)

2. 打開安裝檔進行安裝

3. LLM API 配置（用於字幕斷句、校正），可使用[本專案的中繼站](https://api.videocaptioner.cn)

4. 翻譯配置，選擇是否啟用翻譯，翻譯服務（預設使用微軟翻譯，品質一般，推薦配置自己的 API KEY 使用大模型翻譯）

5. 語音辨識配置（預設使用 B 介面網路呼叫語音辨識服務，中英以外的語言請使用本地轉錄）

### macOS 用戶

#### 一鍵安裝執行（推薦）

```bash
# 方式一：直接執行（自動安裝 uv、複製專案、安裝相關依賴）
curl -fsSL https://raw.githubusercontent.com/WEIFENG2333/VideoCaptioner/main/scripts/run.sh | bash

# 方式二：先複製專案再執行
git clone https://github.com/WEIFENG2333/VideoCaptioner.git
cd VideoCaptioner
./scripts/run.sh
```

腳本會自動：

1. 安裝 [uv](https://docs.astral.sh/uv/) 套件管理器（如果尚未安裝）
2. 複製專案到 `~/VideoCaptioner`（如果不在專案目錄中執行）
3. 安裝所有 Python 依賴
4. 啟動應用

<details>
<summary>手動安裝步驟</summary>

#### 1. 安裝 uv 套件管理器

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

#### 2. 安裝系統依賴（macOS）

```bash
brew install ffmpeg
```

#### 3. 複製並執行

```bash
git clone https://github.com/WEIFENG2333/VideoCaptioner.git
cd VideoCaptioner
uv sync          # 安裝依賴
uv run python main.py  # 執行
```

</details>

### 開發者指南

```bash
# 安裝依賴（包含開發依賴）
uv sync

# 執行應用
uv run python main.py

# 類型檢查
uv run pyright

# 程式碼檢查
uv run ruff check .
```

## 基本配置

### 1. LLM API 配置說明

LLM 大型模型是用來做字幕段句、字幕優化、以及字幕翻譯（如果有選擇 LLM 大型模型翻譯）。

| 配置項         | 說明                                                                                                                                              |
| -------------- | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| SiliconCloud   | [SiliconCloud 官網](https://cloud.siliconflow.cn/i/onCHcaDx)配置方法請參考[配置文件](https://weifeng2333.github.io/VideoCaptioner/config/llm)<br>該併發較低，建議把執行緒設定為 5 以下。 |
| DeepSeek       | [DeepSeek 官網](https://platform.deepseek.com)，建議使用 `deepseek-v3` 模型，<br>官方網站最近服務似乎不太穩定。                                 |
| OpenAI 相容介面 | 如果有其他服務商的 API，可直接在軟體中填寫。base_url 和 api_key [VideoCaptioner API](https://api.videocaptioner.cn)                                 |

註：如果使用的 API 服務商不支援高併發，請在軟體設定中將「執行緒數」調低，避免請求錯誤。

---

如果希望高併發，或者希望在軟體內使用 OpenAI 或者 Claude 等優質大型模型進行字幕校正和翻譯。

可使用本專案的✨LLM API 中繼站✨： [https://api.videocaptioner.cn](https://api.videocaptioner.cn)

其支援高併發，性價比極高，且有國內外大量模型可挑選。

註冊獲取 key 之後，設定中按照下面配置：

BaseURL: `https://api.videocaptioner.cn/v1`

API-key: `個人中心-API 令牌頁面自行獲取。`

💡 模型選擇建議 (本人在各品質層級中精選出的高性價比模型)：

- 高品質之選： `gemini-3-pro`、`claude-sonnet-4-5-20250929` (消耗比例：3)

- 較高品質之選： `gpt-5-2025-08-07`、 `claude-haiku-4-5-20251001` (消耗比例：1.2)

- 中品質之選： `gpt-5-mini`、`gemini-3-flash` (消耗比例：0.3)

本站支援超高併發，軟體中執行緒數直接拉滿即可~ 處理速度非常快~

更詳細的 API 配置教學：[中繼站配置](https://weifeng2333.github.io/VideoCaptioner/config/llm)

---

## 2. 翻譯配置

| 配置項         | 說明                                                                                                                          |
| -------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| LLM 大型模型翻譯 | 🌟 翻譯品質最好的選擇。使用 AI 大型模型進行翻譯，能更好理解上下文，翻譯更自然。需要在設定中配置 LLM API(比如 OpenAI、DeepSeek 等) |
| 微軟翻譯       | 使用微軟的翻譯服務，速度非常快                                                                                                |
| Google 翻譯       | Google 的翻譯服務，速度快，但需要能存取 Google 的網路環境                                                                              |

推薦使用 `LLM 大型模型翻譯` ，翻譯品質最好。

### 3. 語音辨識介面說明

| 介面名稱         | 支援語言                                           | 執行方式 | 說明                                                                                                              |
| ---------------- | -------------------------------------------------- | -------- | ----------------------------------------------------------------------------------------------------------------- |
| B 介面            | 僅支援中文、英文                                   | 線上     | 免費、速度較快                                                                                                    |
| J 介面            | 僅支援中文、英文                                   | 線上     | 免費、速度較快                                                                                                    |
| WhisperCpp       | 中文、日語、韓語、英文等 99 種語言，外語效果較好   | 本地     | （實際使用不穩定）需要下載轉錄模型<br>中文建議 medium 以上模型<br>英文等使用較小模型即可達到不錯效果。              |
| fasterWhisper 👍 | 中文、英文等多 99 種語言，外語效果優秀，時間軸更準確 | 本地     | （🌟推薦🌟）需要下載程式和轉錄模型<br>支援 CUDA，速度更快，轉錄準確。<br>超級準確的時間戳字幕。<br>僅支援 Windows |

### 4. 本地 Whisper 語音辨識模型

Whisper 版本有 WhisperCpp 和 fasterWhisper（推薦） 兩種，後者效果更好，都需要自行在軟體內下載模型。

| 模型        | 磁碟空間 | 記憶體佔用 | 說明                                |
| ----------- | -------- | -------- | ----------------------------------- |
| Tiny        | 75 MiB   | ~273 MB  | 轉錄很一般，僅用於測試              |
| Small       | 466 MiB  | ~852 MB  | 英文辨識效果已經不錯                |
| Medium      | 1.5 GiB  | ~2.1 GB  | 中文辨識建議至少使用此版本          |
| Large-v2 👍 | 2.9 GiB  | ~3.9 GB  | 效果好，配備允許情況下推薦使用        |
| Large-v3    | 2.9 GiB  | ~3.9 GB  | 社群回報可能會出現幻覺/字幕重複問題 |

推薦模型: `Large-v2` 穩定且品質較好。


### 5. 文稿匹配

- 在「字幕優化與翻譯」頁面，包含「文稿匹配」選項，支援以下**一種或者多種**內容，輔助校正字幕和翻譯:

| 類型       | 說明                                 | 填寫範例                                                                                                                                                |
| ---------- | ------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 術語表     | 專業術語、人名、特定詞語的修正對照表 | 機器學習->Machine Learning<br>馬斯克->Elon Musk<br>打call -> 應援<br>圖靈斑圖<br>公車悖論                                                             |
| 原字幕文稿 | 影片的原有文稿或相關內容             | 完整的演講稿、課程講義等                                                                                                                                |
| 修正要求   | 內容相關的具體修正要求               | 統一人稱代名詞、規範專業術語等<br>填寫**內容相關**的要求即可，[範例參考](https://github.com/WEIFENG2333/VideoCaptioner/issues/59#issuecomment-2495849752) |

- 如果需要文稿進行字幕優化輔助，全流程處理時，先填寫文稿資訊，再進行開始任務處理
- 注意: 使用上下文參數量不高的小型 LLM 模型時，建議控制文稿內容在 1 千字內，如果使用上下文較大的模型，則可以適當增加文稿內容。

無特殊需求，可不填寫。

### 6. Cookie 配置說明

使用 URL 下載功能時，如果遇到以下情況:

1. 下載影片網站需要登入資訊才可以下載；
2. 只能下載較低解析度的影片；
3. 網路條件較差時需要驗證；

- 請參考 [Cookie 配置說明](https://weifeng2333.github.io/VideoCaptioner/guide/cookies-config) 獲取 Cookie 資訊，並將 cookies.txt 檔案放置到軟體安裝目錄的 `AppData` 目錄下，即可正常下載高品質影片。

## 軟體流程介紹

程式簡單的處理流程如下:

```
語音辨識轉錄 -> 字幕斷句(可選) -> 字幕優化翻譯(可選) -> 字幕影片合成
```

## 軟體主要功能

軟體利用大型語言模型(LLM)在理解上下文方面的優勢，對語音辨識生成的字幕進一步處理。有效修正錯別字、統一專業術語，讓字幕內容更加準確連貫，為用戶帶來出色的觀看體驗！

#### 1. 多平台影片下載與處理

- 支援國內外主流影片平台（B 站、Youtube、小紅書、TikTok、X、西瓜視頻、抖音等）
- 自動提取影片原有字幕處理

#### 2. 專業的語音辨識引擎

- 提供多種介面線上辨識，效果媲美剪映（免費、高速）
- 支援本地 Whisper 模型（保護隱私、可離線）

#### 3. 字幕智能糾錯

- 自動優化專業術語、程式碼片段和數學公式格式
- 上下文進行斷句優化，提升閱讀體驗
- 支援文稿提示，使用原有文稿或者相關提示優化字幕斷句

#### 4. 高品質字幕翻譯

- 結合上下文的智能翻譯，確保譯文兼顧全文
- 透過 Prompt 指導大模型反思翻譯，提升翻譯品質
- 使用序列模糊匹配演算法，保證時間軸完全一致

#### 5. 字幕樣式調整

- 豐富的字幕樣式模板（科普風、新聞風、番劇風等等）
- 多種格式字幕影片（SRT、ASS、VTT、TXT）

針對新手用戶，對一些軟體內的選項說明：

#### 1. 語音轉錄頁面

- `VAD過濾`：開啟後，VAD（語音活動檢測）將過濾無人聲的語音片段，從而減少幻覺現象。建議保持預設開啟狀態。如果不懂，其他 VAD 選項建議直接保持預設即可。

- `音訊分離`：開啟後，使用 MDX-Net 進行降噪處理，能夠有效分離人聲和背景音樂，從而提升音訊品質。建議只在吵雜的影片中開啟。

#### 2. 字幕優化與翻譯頁面

- `智能斷句`：開啟後，全流程處理時生成字級時間戳，然後透過 LLM 大型模型進行斷句，從而在影片有更完美的觀看體驗。有按照句子斷句和按照語意斷句兩種模式。可根據自己的需求配置。

- `字幕校正`：開啟後，會透過 LLM 大型模型對字幕內容進行校正(如：英文單字大小寫、標點符號、錯別字、數學公式和程式碼的格式等)，提升字幕的品質。

- `反思翻譯`：開啟後，會透過 LLM 大型模型進行反思翻譯，提升翻譯的品質。相應的會增加請求的時間和消耗的 Token。(選項在 設定頁-LLM大型模型翻譯-反思翻譯 中開啟。)

- `文稿提示`：填寫後，這部分也將作為提示詞發送給大型模型，輔助字幕優化和翻譯。

#### 3. 字幕影片合成頁面

- `影片合成`：開啟後，會根據合成字幕影片；關閉將跳過影片合成的流程。

- `軟字幕`：開啟後，字幕不會燒錄到影片中，處理速度極快。但是軟字幕需要一些播放器（如 PotPlayer）支援才可以進行顯示播放。而且軟字幕的樣式不是軟體內調整的字幕樣式，而是播放器預設的白色樣式。

專案主要目錄結構說明如下：

```
VideoCaptioner/
├── app/                        # 應用原始碼目錄
│   ├── common/                 # 公用模組（配置、信號匯流排）
│   ├── components/             # UI 元件
│   ├── core/                   # 核心業務邏輯（ASR、翻譯、優化等）
│   ├── thread/                 # 非同步執行緒
│   └── view/                   # 介面視圖
├── resource/                   # 資源檔目錄
│   ├── assets/                 # 圖示、Logo 等
│   ├── bin/                    # 二進位程式（FFmpeg、Whisper 等）
│   ├── fonts/                  # 字體檔
│   ├── subtitle_style/         # 字幕樣式模板
│   └── translations/           # 多語言翻譯檔
├── work-dir/                   # 工作目錄（處理完成的影片和字幕）
├── AppData/                    # 應用程式資料目錄
│   ├── cache/                  # 快取目錄（轉錄、LLM 請求）
│   ├── models/                 # Whisper 模型檔
│   ├── logs/                   # 日誌檔
│   └── settings.json           # 使用者設定
├── scripts/                    # 安裝和執行腳本
├── main.py                     # 程式入口
└── pyproject.toml              # 專案配置和依賴
```

## 📝 說明

1. 字幕斷句的品質對觀看體驗至關重要。軟體能將逐字字幕智能重組為符合自然語言習慣的段落，並與影片畫面完美同步。

2. 在處理過程中，僅向大型語言模型發送文本內容，不包含時間軸資訊，這大大降低了處理開銷。

3. 在翻譯環節，我們採用吳恩達提出的「翻譯-反思-翻譯」方法論。這種迭代優化的方式確保了翻譯的準確性。

4. 填入 YouTube 連結時進行處理時，會自動下載影片的字幕，從而省去轉錄步驟，極大地節省操作時間。

## 🤝 貢獻指南

專案在不斷完善中，如果在使用過程遇到的 Bug，歡迎提交 [Issue](https://github.com/WEIFENG2333/VideoCaptioner/issues) 和 Pull Request 幫助改進專案。

## 📝 更新日誌

查看完整的更新歷史，請前往 [CHANGELOG.md](./CHANGELOG.md)

## 💖 支持作者

如果覺得專案對你有幫助，可以給專案點個 Star！

<details>
<summary>贊助支持</summary>
<div align="center">
  <img src="./legacy-docs/images/alipay.jpg" alt="支付寶QR Code" width="30%">
  <img src="./legacy-docs/images/wechat.jpg" alt="微信QR Code" width="30%">
</div>
</details>

## ⭐ Star History

[![Star History Chart](https://api.star-history.com/svg?repos=WEIFENG2333/VideoCaptioner&type=Date)](https://star-history.com/#WEIFENG2333/VideoCaptioner&Date)
