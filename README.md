# AutoClicker

AutoClicker 是一款 Windows 桌面自動操作工具，支援滑鼠點擊、鍵盤按鍵、動作錄製與循環回放。介面分為精簡的自動操作主視窗，以及獨立的錄製與回放面板。

## 下載與啟動

前往 [GitHub Releases](https://github.com/shengpeiyap/AutoClicker/releases) 下載最新版本的 `AutoClicker.exe`，下載後雙擊即可啟動，無需另外安裝 Python。

如要從原始碼啟動，請安裝 Python 3.10 或更新版本（需包含 Tcl/Tk），在專案目錄執行：

```powershell
python main.py
```

## 自動操作

- 選擇左鍵、右鍵、中鍵，或鍵盤按鍵。
- 設定小時、分鐘、秒與毫秒間隔。
- 執行次數設為正整數時，完成該次數後停止；設為 `0` 時持續執行，直到手動停止。
- 滑鼠點擊可使用目前游標位置或指定螢幕座標。指定座標可透過「從螢幕選取…」擷取，也可直接編輯 X/Y；選取時按 Esc 取消。
- 鍵盤輸入方式可選「虛擬鍵碼」或「掃描碼」。掃描碼模式可能較適合使用實體按鍵掃描碼的應用程式。

## 錄製與回放

在主視窗開啟「錄製與回放面板…」後，可開始錄製、檢視動作清單、設定播放輪數，以及匯入或匯出 JSON 錄製檔。

錄製內容包括滑鼠移動、按下／放開、拖曳，以及鍵盤按下／放開和長按時間。回放輪數設為正整數時，完成指定輪數後停止；設為 `0` 時持續循環。

全域快捷鍵：

- `F6`：開始或停止自動操作；回放期間也可停止。
- `F7`：開始或停止錄製。
- `F8`：開始或停止錄製回放。

錄製或回放遊戲操作時，請讓目標遊戲保持前景。Windows 模擬輸入不等同真實鍵盤硬體訊號；使用 Raw Input 或過濾模擬事件的程式可能不會回應。

## 從原始碼打包

```powershell
python -m pip install -r requirements-build.txt
.
build.ps1
```

產生的可執行檔位於 `dist/AutoClicker.exe`。推送 `v*` 格式的版本標籤會觸發 GitHub Actions 在 Windows 上建置並建立 Release。

## 授權

本專案採用 MIT License，詳見 [LICENSE](LICENSE)。
