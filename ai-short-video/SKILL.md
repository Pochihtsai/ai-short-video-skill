---
name: ai-short-video
description: 用 HyperFrames 做中文或英文的短片，直式（1080×1920，Reels、Shorts、TikTok）或橫式（1920×1080，YouTube、簡報）都可以。流程：需求→故事線→大綱→風格與配樂（用畫面確認）→旁白稿，五關都確認才製作，內含已驗證過的規則：中英文配音和逐詞時間、直式三平台安全區與橫式安全框、Mac／Windows 字型設定、字幕斷句腳本、淺色玻璃風、依內容找免費可商用配樂（Mixkit、Openverse）、混音音量。觸發詞：「做一支短片」「做影片」「直式短片」「橫式影片」「短影音」「Reels」「Shorts」「TikTok 影片」「YouTube 影片」「英文影片」「動畫影片」「解說影片」「配字幕的影片」「再做一支」「用 HyperFrames 做」。改既有 HyperFrames 專案的細節時也用這份規則。
---

# 中英文短片，直式與橫式（HyperFrames）

先讀 `/hyperframes` skill 的契約，本檔只補 HyperFrames 沒寫的規則。工作資料夾預設放在使用者桌面的「影片」資料夾，每支片一個子資料夾；使用者指定別處就照他的。

## 工具（裝好的位置）

- HyperFrames：用 `npx hyperframes`；它的 skill 都在 `~/.claude/skills/`
- FFmpeg、Node.js 22 以上、Google Chrome
- 配音用的 edge-tts（中英文都用它），裝在獨立環境裡：
  - Mac：`~/.venvs/edge-tts/bin/python`
  - Windows：`%USERPROFILE%\.venvs\edge-tts\Scripts\python.exe`
- 音效庫：`~/.claude/skills/media-use/audio/assets/sfx/`，19 個，Pixabay 授權，免標示
- 配樂：不附音樂檔，每次依內容用 `scripts/find_music.py` 到 Mixkit、Openverse 找（見「聲音」）
- 本 skill 的腳本在 `scripts/`，Mac、Windows 都能跑（Mac 用 `python3`，Windows 用 `python`）

任何一項找不到，先照本 skill 資料夾裡的 `SETUP_給Claude的設定指引.md` 補裝；那份檔案不在的話，告訴使用者缺什麼，不要自己猜著裝。

## 流程：五關確認，全部通過才製作

目的：做一支片要跑好幾分鐘、花不少額度，方向越早對齊越不會整支重做。每一關只問一件事、附上推薦和理由，讓使用者看一眼就能決定。

| 關卡 | 交給使用者 | 存檔 |
|---|---|---|
| 0. 需求 | 一次問完：語言、直式或橫式、長度（建議 15、30 或 60 秒）、用途和觀眾。已經說了的不再問 | — |
| 1. 故事線 | 三條故事線，每條三到四句：切入角度、核心比喻、結尾想讓觀眾記住什麼。推薦一條並說理由 | `01_故事線.md` |
| 2. 大綱 | 選定故事線的分幕表：每一幕幾秒、畫面大概是什麼、要傳達的重點 | `02_大綱.md` |
| 3. 風格與配樂 | 用大綱裡最有代表性的一幕，做 **2 張**不同風格的靜態畫面：一張依內容推薦，一張明顯不同的方向。同時建議配樂方向，附 2–3 首候選曲的試聽和授權說明。另外替 2–4 個關鍵動作各列 3 個動態效果（名稱、一句說明、示範連結），讓使用者點開看會動的示範再選 | `03_風格/`（圖片）、`03_配樂.md`、`03_動態.md` |
| 4. 旁白稿 | 完整旁白，標出每一幕對應哪幾句，附字數和預估秒數，再附一段約 10 秒的配音試聽 | `04_旁白稿.md`、試聽檔 |
| 5. 製作 | 配音、動畫、字幕、音樂、音效一次做完，交第一版 | `renders/` |

規則：
1. **每一關都要等使用者確認才往下走**，沒確認之前不做下一關，更不能直接開始製作
2. 使用者說「後面照你的建議直接做」時，才可以略過剩下的關卡直接製作，並在製作前列出每一關採用的選擇
3. 回頭改前面的關卡時，只重做受影響的部分，例如改了某一幕的大綱，就只改那一幕的旁白，不從頭來
4. 每一關的檔案都存在影片資料夾裡，中斷後或換新對話時，先讀這些檔案接著做。第 4 關確認後、開始製作前，提醒使用者可以開新對話來製作，比較省額度（對話越長，每一步要重讀的內容越多）：在新對話說「接著做 <片名>」就好。使用者選擇留在原對話就照做
5. 使用者丟參考圖片時，第 3 關就照那個方向做，不必再另外提兩種

各關的做法：
- **需求**：沒說方向時，發到 Reels、Shorts、TikTok 用直式，發到 YouTube 或放進簡報用橫式
- **故事線、大綱**：台詞長度抓中文約每秒 4.2 個字（30 秒約 130 字），英文約每秒 3 個字（30 秒約 90 個字，依 Andrew 18 字樣本估計，第一支完整片後再校正）
- **風格圖**：在 `03_風格/<風格名>/` 各放一個只有那一幕、不配音的 `index.html`（版面照下方「語言與方向」），用 `npx hyperframes snapshot --at <秒數>` 截圖給使用者看。預設推薦 `references/design-glass.md` 的淺色玻璃風，內容不適合時改推別的。圖要用跟成品同一套工具做，使用者看到什麼，成品就長什麼樣子
- **動態效果**：目的是讓動作有名字可以溝通、選了就能照著做，又不多花額度。效果來自 Motion Prompt（MIT 授權、可商用的動態效果目錄，240 個效果，每個都有會動的示範）
  1. 從大綱挑 2–4 個關鍵動作，例如數字出現、清單依序進場、圖表長出來、換場，用 `scripts/motion_catalog.py search <英文關鍵字>` 各找 3 個候選。只把搜尋結果的名稱、一句說明、示範連結給使用者，不要把整份目錄讀進對話
  2. 使用者點連結看示範後選定，把編號和用在哪一幕寫進 `03_動態.md`
  3. 不必每個動作都挑。使用者說「動態你決定」時，由 Claude 選並寫進檔案
  4. 它管的是「怎麼動」，配色、字型、版面仍由風格圖決定
- **配樂**：照下方「聲音」的做法依內容找；使用者選好後由 Claude 下載、剪好長度，**不要叫使用者自己去網站下載**
- **旁白稿與試聽**：用 `scripts/tts_words.py` 產生試聽；換聲音之前先給試聽。台詞會送到微軟的線上服務，內容敏感時先告訴使用者
- **製作**：
  1. 配音：`scripts/tts_words.py` 同時產生 `voice.mp3` 和 `words.json`（逐詞時間）
  2. 動畫：用 `words.json` 決定每一幕的起訖時間和每個元素出現的時間點。寫法參考 `templates/`：直式看 `example_A_v3.html`，橫式看 `example_landscape_en.html`；風格照第 3 關選定的那張圖。`03_動態.md` 有選效果的，用 `scripts/motion_catalog.py get <編號>` 讀規格（不加 `--code`），照規格裡的時間點和緩動曲線用 GSAP 改寫成本片的風格；不要直接貼它的 canvas 程式碼，那段程式碼自帶深藍配色和循環節奏（2026-11-19 實測：直接貼能輸出，但和成品風格不搭；照規格改寫的版本融入得很好）。在 HTML 註解寫上 `Motion Prompt #編號 · MIT © 2026 Shohei Ohtaki`
  3. 字幕：用 `scripts/make_captions.py` 切，不要自己用 `words.json` 拼（會掉中英文之間的空格、在怪地方斷句）；再用 `scripts/captions_html.py captions.json index.html [最後一組延長到第幾秒]` 放進 `index.html`。templates 的字幕區已經有 `<!-- captions:begin -->`、`<!-- captions:end -->` 兩行標記和字幕迴圈，不要手寫字幕的 div 和 tl.set
  4. 第一版就配好音樂和音效，不交無聲版。配樂用 `scripts/prep_music.py` 剪長度、統一響度；**輸出影片前**用 `scripts/music_volume.py` 算出 `data-volume`，不要輸出後才發現太大聲再重新輸出
  5. 自檢後輸出，見下方「自檢」。音樂要標示作者時，把說明欄要貼的標示文字一起交給使用者
- 做完把這次新確定的規則補進本檔

## 語言與方向

### 版面

| | 直式 1080×1920 | 橫式 1920×1080 |
|---|---|---|
| 安全範圍 | 垂直 288–1248；水平 y<840 時 120–888，y≥840 時 120–780（TikTok、Reels、Shorts 三者的交集） | 中央 80%：x 192–1728、y 108–972（CLI 的 title-safe） |
| 構圖中心線 | x=450（右下有平台按鈕列，不是 540） | x=960 |
| 標題 | top 約 312，中文 96px、英文 84px | 可以靠左（例如 left 240、top 140），中文 84px、英文 76px |
| 主畫面 | 底部停在 1100 左右 | y 約 250–800，左右兩半都要有內容（見下方「橫式構圖」） |
| 字幕 | left 120、寬 660、top 1163；中文 46px、英文 42px；底線不能超過 1248 | left 360、寬 1200、top 850；48px；底線不能超過 972 |
| 字幕每組上限 | 中文 12、英文 28 個字元 | 中文 16、英文 42 個字元 |

- 安全範圍的數字取自 HyperFrames CLI 原始碼，check 會照這些數字報 outside_safe_zone
- 直式片如果不發到短影音平台，可以改回置中
- 字幕一律一行；中文的上限用「視覺寬度」算，英文字母約半個中文字（`make_captions.py` 已處理）

### 橫式構圖

目的：橫式畫面是由左往右讀，左右的空間要拿來講事情。直式的習慣是把標題、主畫面、字幕由上往下疊成中間一欄，搬到橫式會留下左右兩大片空白（2026-11-17 使用者指出：重心過度集中在中間）。

原則：
1. 對照、前後差異、流程步驟改成左右並排，不要上下疊
2. 主畫面要用到大部分的可用寬度；只有中間一欄是直式的做法
3. 每一幕從常見的三種構圖挑一種，可以混用：
   - **左文右圖**：左邊放標題和重點句，右邊放圖
   - **左右對照**：同一個畫面裡左右擺兩種狀況，例如左邊被文件淹沒的 AI、右邊爬不動的進度和一直跳出的錯誤
   - **橫向流程**：流程或分工樹由左往右展開，例如左邊主管 agent，往右分成三個 agent，各接一張工作卡
4. 圖形可以比直式大：右邊有空間時，加上標籤、狀態、勾選等資訊，不要只是把同一張圖放大
5. 字幕照舊放底部置中，主畫面的底部要停在字幕上方

範例：`templates/example_landscape_en.html`（左右對照＋橫向流程）。用 `scripts/measure_span.py` 量的結果，主畫面寬度從舊版的可用範圍 24–54% 提高到 95%，左右兩半的內容量接近。

### Windows 中文編碼（避免亂碼）

- 本 skill 的腳本都用 UTF-8 讀寫檔案，主控台輸出也強制 UTF-8
- **不要用 `>` 把有中文的輸出存成檔案**：Windows 會改用 cp950 或 UTF-16 存檔，讀回來就變亂碼（2026-11-17 同事的字幕亂碼就是這樣來的）。要存檔的腳本都有輸出檔參數，例如 `make_captions.py` 直接寫 `captions.json`
- `script.txt`、`index.html` 這類檔案用 Claude 的寫檔工具寫（UTF-8），不要用 PowerShell 的 `echo` 或 `Out-File` 寫
- HTML 開頭要有 `<meta charset="UTF-8" />`

### 字型

- 只有 HyperFrames 內建字型可以直接寫名字
- **中文**：用同一個 `@font-face` 列出 Mac 和 Windows 的字型：
  `src: local("PingFangTC-Medium"), local("PingFang TC Medium"), local("Microsoft JhengHei");`
  （Semibold 同樣寫法，範例見 templates）。這個寫法只能在本機渲染，雲端渲染要另外放 woff2 字型檔
- **英文**：直接寫 `font-family: "Inter", sans-serif`，Inter 是 HyperFrames 內建字型，Mac、Windows、雲端渲染都一樣
- 中文台詞裡夾英文字（例如 agent）時用中文字型就好，不必另外設定
- 字級適度、粗體少用（只給關鍵字和小標）

### 配音

- **中文**：`zh-TW-HsiaoChenNeural`（曉臻），語速 +10%；另一個女聲是 `zh-TW-HsiaoYuNeural`（曉雨）。男聲 `zh-TW-YunJheNeural` 在 edge-tts 上會失敗
- **英文**：`en-US-AndrewNeural`（男聲），語速 +0%。也試過能用的：`en-US-AvaNeural`（女聲，稍慢）、`en-US-EmmaNeural`（女聲，稍快）
- 指令：`python -I scripts/tts_words.py script.txt voice.mp3 words.json <聲音> <語速>`

### 字幕斷句（`scripts/make_captions.py`）

- 用法：`python -I scripts/make_captions.py script.txt words.json <zh|en> <v|h> captions.json [總秒數]`（直接寫檔，不要用 `>` 轉存）
- 句號、冒號、分號一定斷開；一句裡優先在逗號處分組，分成最少組，而且最長那組盡量短
- 逗號之間的一段本身就太長時，才在詞與詞之間平均切，不會留下單獨一個字
- 字幕文字取台詞原文：中文逗號換成空格、句尾標點拿掉；英文保留句中逗號

### 風格

- 預設推薦 `references/design-glass.md`（淺色玻璃風），直式、橫式都適用；在第 3 關用兩張風格圖和使用者確認，使用者指定別的風格就照他的

## GSAP 與 check 的坑

- 不能對 `letterSpacing` 做動畫，check 會報錯；改用位移加淡入
- 被 GSAP 動到的元素不能另外寫 CSS transform
- 重複動畫要寫有限次數的 repeat，不能寫 `repeat:-1`
- 每個音效 `<audio>` 都要寫 `data-duration`（長度看 sfx 資料夾裡的 manifest.json），否則會被當成一路播到片尾
- 用 `npx hyperframes check --json 2>&1 | python3 scripts/check_summary.py` 看結果（Windows 把 `python3` 換成 `python`），要做到 ok，而且沒有 outside_safe_zone
- 已知誤判：白字疊在 SVG 圖形上時，contrast 檢查會拿背後的底色來算。看截圖確認讀得清楚就可以不改
- 背景柔光故意超出畫面時會出現 container_overflow 警告，可以忽略

## 聲音

- **配音**：聲音和語速見上方「語言與方向」。Mac 內建的 `say` 聲音被評為太機械，不建議用
- **音樂：依內容挑，由 Claude 自己找、自己下載**
  1. 從大綱判斷情緒和節奏，換成英文關鍵字。常見對應：
     - 輕快解說、工作技巧：upbeat、corporate、happy
     - 溫暖故事、人物：warm、acoustic、piano
     - 科技、產品介紹：electronic、tech、ambient
     - 正式報告、成果：cinematic、inspiring
     - 輕鬆生活：chill、lofi
  2. 用 `scripts/find_music.py` 搜尋，長度至少要蓋過整支片（例如 30 秒片找 35 秒以上）：
     - `python -I scripts/find_music.py mixkit <標籤> <最短秒數>`：Mixkit，免費可商用、不用標示作者（不能把原始音檔再散布出去）
     - `python -I scripts/find_music.py openverse "<關鍵字>" <最短秒數>`：Openverse，彙整多個創用 CC 音樂庫，會附上要貼的標示文字
     - 想要古典樂時，到 Wikimedia Commons 找公共領域或 CC 授權的錄音（可以用 API 查授權：`action=query&prop=imageinfo&iiprop=url|size|extmetadata`）
     - 這幾個都找不到合適的，可以自己上網找別的免費可商用來源，但要確認授權，而且 Claude 能直接下載
  3. 在第 3 關挑 2–3 首給使用者：推薦理由、來源、授權、要不要標示作者，並剪一段 15 秒左右的試聽檔
  4. 使用者選好後下載到 `assets/bgm/source/`，用 `python -I scripts/prep_music.py <原曲> assets/bgm/bgm.mp3 <影片秒數> [起點秒數]` 剪成影片長度
- **授權**：
  - 可以用：公共領域、CC0、CC BY（要標示作者）、Mixkit 免費音樂授權
  - CC BY-SA 可以用，但「相同方式分享」的條款會延伸到整支影片，要先告訴使用者
  - 不可以用：不可商用（NC）、禁止改作（ND，剪進影片就算改作）
  - 古典樂的曲子沒有版權，但**錄音另外有版權**，要看錄音本身的授權；公共領域的老錄音常是單聲道、低位元率，音質差
  - 下載前要看曲目頁面的標籤和說明，確認是不是改編版（曾經遇過標題是莫札特、其實是電吉他重金屬改編）
- **混音**：
  - 用 loudnorm 正規化到 -20 LUFS，結尾 2 秒淡出（`prep_music.py` 會做）
  - `data-volume` 每首都要算，不要套固定值：`python -I scripts/music_volume.py assets/voice.mp3 words.json assets/bgm/bgm.mp3`。2026-11-18 升降桌片的 Digital Clouds 算出 0.21，舊的固定值 0.45 會讓空檔的音樂只比配音低約 9 dB
  - 目標是配音空檔的音樂比配音低 14–19 dB；低到 -40 dB 就幾乎聽不到了
  - 輸出後用 `python -I scripts/audio_levels.py <影片> words.json <空檔起點:長度>...` 複查。要給 words.json：沒給時配音段固定量 5–7 秒，這兩秒裡有停頓就會量得太小聲（升降桌片少算約 3 dB，誤以為音樂太大聲而多重新輸出一次）。挑空檔要避開音效的時間點
- **音效**：初稿就配上。從音效庫複製到專案的 `assets/sfx/`，音量 0.3–0.5，在換場、元素出現、強調的地方用，一支 30 秒的片 4–8 個就夠

## 自檢

1. 跑 check（上面的指令）
2. `npx hyperframes snapshot --at <各幕關鍵秒數>`，用 Read 看 contact sheet：文字有沒有擠、重疊、超出畫面，有沒有壓到字幕
3. 輸出：`npx hyperframes render --quality delivery -o renders/<名稱>_vN.mp4`，一支 30 秒的片大約要 3 分鐘
4. **從成品驗收**：用 `scripts/frame_sheet.py` 抽 8 格看（依片長平均取格，直式、橫式都能用），用 ffprobe 確認長度、解析度（1080×1920 或 1920×1080）、有音軌，再跑 `scripts/audio_levels.py`（記得給 words.json）
5. **版面有沒有用到這個方向的空間**：每一幕挑一個畫面都進場後的秒數，跑 `<edge-tts 環境的 python> -I scripts/measure_span.py renders/<檔名>.mp4 <秒數>...`（要用裝了 numpy、pillow 的 edge-tts 環境）。橫式的主畫面寬度要到可用範圍的 70% 以上，而且左右兩半都有內容；不到就回頭照「橫式構圖」重排。數字只是提醒，最後仍要看畫面。背景是滿版格線或紋理時（例如藍圖線稿風），整個畫面都會被算成有內容，量出來一律 125%，這時不用這個腳本，直接看畫面判斷
6. 回報時要寫出沒有驗證到的部分。例如音效只量了音量、沒有實際聽，就要明說

## 省成本

- 一次要做多支片時，每一支交給一個分身（fork），主線只負責整理規格、統一驗收和傳檔
- 主線對話越長，每一步都要重讀越多快取；閒置超過 1 小時後快取會過期，再呼叫一次要整段重寫
- 只要產生音檔時，可以請使用者自己在終端機跑 edge-tts，不必經過 Claude
- 動態效果用 `motion_catalog.py` 只查需要的幾行：一次搜尋約 1 KB、一個效果的規格約 1.5 KB；整份目錄約 60 KB，不要整份讀進來

## 驗證狀態

- 中文直式：做過三支 30 秒的完整片
- 中文橫式：2026-11-18 做過一支 45 秒的完整片（3D 升降桌安裝教學）
- 英文直式、英文橫式：只用 7–9 秒的測試片驗證過版面、字型、配音和字幕，還沒做過完整長度的片。第一次做完整片時，把新發現的規則補進本檔
- 橫式構圖：2026-11-17 改成左右對照與橫向流程後，中英文兩支測試片重新輸出驗證過（check 通過、主畫面寬度佔可用範圍 95%）
