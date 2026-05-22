# HP LaserJet 1020 for macOS

HP LaserJet 1020 在現代 macOS (Sequoia+) 上的開源驅動方案。

## 背景

HP LaserJet 1020 是 2005 年上市的打印機，HP 已停止提供現代 macOS 驅動。這台打印機使用專有的 **ZjStream** 協議，不是標準 PCL/PostScript，因此無法使用系統內建通用驅動。

本方案使用開源 [foo2zjs](https://github.com/OpenPrinting/foo2zjs) 驅動 + 本地網頁打印伺服器，讓這台老打印機繼續在 macOS 上工作。

## 功能

- 網頁介面拖放/上傳 PDF，一鍵打印
- 自動 PDF → PostScript → ZjStream 轉換
- 啟動時自動開啟瀏覽器

## 系統要求

- macOS 12+ (Monterey/Sequoia)
- [Homebrew](https://brew.sh)
- Python 3

## 安裝

### 1. 安裝依賴

```bash
brew install ghostscript gnu-sed jbigkit
```

### 2. 編譯並安裝 foo2zjs 驅動

```bash
git clone --depth 1 https://github.com/OpenPrinting/foo2zjs.git
cd foo2zjs
make
sudo make install PREFIX=/usr/local
```

### 3. 下載並轉換韌體

```bash
curl -L -o /tmp/sihp1020.tar.gz "https://www.quirinux.org/printers/sihp1020.tar.gz"
cd /tmp && tar zxf sihp1020.tar.gz
sudo /usr/local/bin/arm2hpdl /tmp/sihp1020.img | \
  sudo tee /usr/local/share/foo2zjs/firmware/sihp1020.dl > /dev/null
```

### 4. 安裝韌體自動載入守護進程

```bash
# 修改路徑後重新編譯 osx-hplj-hotplug
cd foo2zjs/osx-hotplug
perl -pi -e 's|/usr/share/foo2zjs|/usr/local/share/foo2zjs|g' osx-hplj-hotplug.m
make clean && make
sudo cp osx-hplj-hotplug /usr/local/bin/
sudo /usr/local/bin/osx-hplj-hotplug -D1 &
```

每次開機或插拔 USB 後，印表機燈會閃爍約 5 秒表示韌體載入成功。

## 使用方法

### 啟動打印伺服器

```bash
python3 hp1020-print-server.py
```

伺服器會自動在預設瀏覽器開啟 `http://localhost:8765`。

### 打印

1. 在應用程式中「列印為 PDF」存到桌面
2. 在網頁介面拖放 PDF 檔案
3. 按「打印」按鈕

## CUPS 過濾器問題

macOS Sequoia 的 CUPS 沙箱阻止了自定義過濾器的執行。因此本方案採用網頁伺服器端轉換 + `lp -o raw` 的方式繞過 CUPS 過濾器鏈。

## 檔案說明

| 檔案 | 說明 |
|------|------|
| `hp1020-print-server.py` | 本地 HTTP 伺服器，提供網頁介面 + PDF 轉換打印 |

## 授權

foo2zjs 為 GPL-2.0+ 授權。本倉庫僅包含包裝腳本和說明文件。

## 參考

- [OpenPrinting/foo2zjs](https://github.com/OpenPrinting/foo2zjs)
- [foo2zjs 官方文檔](http://foo2zjs.rkkda.com/)
