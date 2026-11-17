# 設定指引（給 Claude Code 看）

使用者請你照這份檔案設定做影片的環境。目標：裝好下列工具，把 ai-short-video skill 放到正確位置，最後做一支 4 秒的中文測試片給使用者看。

## 原則

- 用台灣繁體中文跟使用者說話，使用者不一定有工程背景，每一步用白話說明在做什麼。
- 開始前先告訴使用者：會檢查哪些東西、可能要裝哪些東西，大約要多久。
- **已經裝好的不要重裝**，先檢查版本。
- 需要管理員密碼或系統授權的步驟（Mac 的 Homebrew 安裝、Windows 的系統管理員視窗），請使用者自己輸入或按允許，你不要用 sudo 代打密碼。
- 每一項裝完都要驗證；失敗時說清楚卡在哪裡、需要使用者做什麼，不要跳過。
- 這是個人使用的安裝。

## 1. 判斷作業系統

Mac 用 `uname -s`，Windows 用 PowerShell 的 `$env:OS`。以下分兩欄寫。

## 2. 檢查並安裝基本工具

| 工具 | 檢查 | Mac 安裝 | Windows 安裝 |
|---|---|---|---|
| 套件管理工具 | Mac：`brew --version`；Windows：`winget --version` | 沒有 Homebrew 時，給使用者 brew.sh 首頁上的那行安裝指令，請他自己在終端機貼上執行（會要密碼） | Windows 10／11 內建 winget；沒有的話請使用者到 Microsoft Store 更新「應用程式安裝程式」 |
| Node.js 22 以上 | `node --version` | `brew install node` | `winget install OpenJS.NodeJS.LTS` |
| FFmpeg | `ffmpeg -version` | `brew install ffmpeg` | `winget install Gyan.FFmpeg` |
| Google Chrome | Mac：`ls "/Applications/Google Chrome.app"`；Windows：看 Program Files 下有沒有 Google\Chrome | `brew install --cask google-chrome` | `winget install Google.Chrome` |
| Python 3.9 以上 | Mac：`python3 --version`；Windows：`python --version` | `brew install python` | `winget install Python.Python.3.12` |

Windows 用 winget 裝完後，新開的終端機才會讀到新的 PATH；讀不到時請使用者重開 Claude Code 再繼續。

## 3. 配音環境（edge-tts）

裝在獨立環境，不汙染系統的 Python：

- Mac：
  - `python3 -m venv ~/.venvs/edge-tts`
  - `~/.venvs/edge-tts/bin/pip install edge-tts numpy pillow`
- Windows（PowerShell）：
  - `python -m venv $env:USERPROFILE\.venvs\edge-tts`
  - `& $env:USERPROFILE\.venvs\edge-tts\Scripts\pip.exe install edge-tts numpy pillow`

驗證：用 skill 裡的 `scripts/tts_words.py` 把「測試一句話。」轉成 mp3，確認檔案有產生，再給使用者聽。

## 4. HyperFrames 與 skill

1. 安裝 HyperFrames 的 skill（全域、給 Claude Code 用）：
   `npx -y skills add heygen-com/hyperframes -g -a claude-code -s '*' -y`
2. Remotion 的 skill 是選裝，先問使用者要不要：
   `npx -y skills add remotion-dev/skills -g -a claude-code -s '*' -y`
3. 把本檔所在的 `ai-short-video` 資料夾整個複製到 `~/.claude/skills/ai-short-video`（Windows 是 `%USERPROFILE%\.claude\skills\ai-short-video`）。已經有同名資料夾時，先問使用者要不要覆蓋。
4. 環境檢查：`npx -y hyperframes doctor --json`，看 FFmpeg、FFprobe、Chrome 三項是否 ok。Docker 沒開不影響本機渲染，可以忽略。

## 5. 測試片

1. 在使用者桌面建立「影片/安裝測試」資料夾，執行 `npx -y hyperframes init . --skip-skills`。
2. 把 index.html 改成 4 秒、1080×1920，畫面中間一行中文標題「安裝成功」，加一個淡入動畫；字型照 skill 的寫法用 `@font-face` 列出蘋方和微軟正黑體。
3. `npx hyperframes check --json`，要是 ok。
4. `npx hyperframes render --quality draft -o 測試.mp4`。
5. 用 ffprobe 確認 4 秒、1080×1920，抽一格畫面看中文字有沒有正確顯示（不是方塊或替代字型）。
6. 把影片給使用者看。

## 6. 回報

列出：

- 每項工具的版本
- 測試片的位置
- 沒裝或失敗的項目，以及下一步要做什麼

最後告訴使用者，之後只要說「做一支 30 秒的短片，主題是……」（可以指定中文或英文、直式或橫式）就會照 ai-short-video skill 的流程開始做；新的 skill 要開一個新的對話才會被載入。
