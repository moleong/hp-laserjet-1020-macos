# HP LaserJet 1020 for macOS

HP LaserJet 1020 在現代 macOS (Sequoia+) 上的驅動方案。

## 背景

HP LaserJet 1020 是 2005 年上市的打印機，HP 已停止提供現代 macOS 驅動。這台打印機使用專有的 **ZjStream** 協議，不是標準 PCL/PostScript，因此無法使用系統內建通用驅動。

## 推薦方案（首選）

**推薦使用 [anxkhn/hp1020-driver-mac](https://github.com/anxkhn/hp1020-driver-mac)** — 從 Apple HP Printer Drivers 5.1.1 提取的官方二進制過濾器，更穩定、安裝更簡單。

### 快速安裝

```bash
git clone https://github.com/anxkhn/hp1020-driver-mac.git
cd hp1020-driver-mac

# 安裝驅動檔案
sudo cp "HP LaserJet 1022.gz" "/Library/Printers/PPDs/Contents/Resources/"
sudo mkdir -p "/Library/Printers/hp/laserjet/hplaserjetzjs.bundle/Contents/MacOS"
sudo mkdir -p "/Library/Printers/hp/laserjet/hplaserjetzjs.bundle/Contents/Resources"
sudo cp rasterToHPZJS "/Library/Printers/hp/laserjet/hplaserjetzjs.bundle/Contents/MacOS/"
sudo cp commandToHPZJS "/Library/Printers/hp/laserjet/hplaserjetzjs.bundle/Contents/MacOS/"
sudo cp hp1020.acl "/Library/Printers/hp/laserjet/hplaserjetzjs.bundle/Contents/Resources/"
sudo chmod 755 "/Library/Printers/hp/laserjet/hplaserjetzjs.bundle/Contents/MacOS/rasterToHPZJS"
sudo chmod 755 "/Library/Printers/hp/laserjet/hplaserjetzjs.bundle/Contents/MacOS/commandToHPZJS"

# 添加印表機（替換 YOURSERIAL 為實際序號）
sudo lpadmin -p "HP_LaserJet_1020" -E \
  -v "usb://Hewlett-Packard/HP%20LaserJet%201020?serial=YOURSERIAL" \
  -P "/Library/Printers/PPDs/Contents/Resources/HP LaserJet 1022.gz" \
  -D "HP LaserJet 1020"
```

之後直接從任何應用程式打印，選 HP_LaserJet_1020 即可。

### 若參考倉庫失效

上述 4 個核心檔案（`HP LaserJet 1022.gz`、`rasterToHPZJS`、`commandToHPZJS`、`hp1020.acl`）已經安裝在你的 `/Library/Printers/` 目錄下。**即使參考倉庫消失，這些檔案仍可繼續使用**。

你也可以自行從 Apple HP Printer Drivers 5.1.1 包中提取：
1. 從 [Apple 支援網站](https://support.apple.com/zh-hk/HT201465) 或 Apple Software Update 下載 HP Printer Drivers 5.1
2. 掛載 `.dmg`，在 `/Library/Printers/hp/` 下找到對應檔案

---

## 備選方案（foo2zjs）

若你偏好開源方案，或上述方案無法運作，可使用 [OpenPrinting/foo2zjs](https://github.com/OpenPrinting/foo2zjs) + 本倉庫的網頁打印伺服器。

### 安裝

```bash
brew install ghostscript gnu-sed jbigkit
git clone --depth 1 https://github.com/OpenPrinting/foo2zjs.git
cd foo2zjs
make
sudo make install PREFIX=/usr/local

# 下載韌體
curl -L -o /tmp/sihp1020.tar.gz "https://www.quirinux.org/printers/sihp1020.tar.gz"
cd /tmp && tar zxf sihp1020.tar.gz
sudo /usr/local/bin/arm2hpdl /tmp/sihp1020.img | \
  sudo tee /usr/local/share/foo2zjs/firmware/sihp1020.dl > /dev/null
```

### 使用網頁伺服器打印

```bash
python3 hp1020-print-server.py
```

自動開啟瀏覽器到 `http://localhost:8765`，拖放 PDF 打印。

---

## 檔案說明

| 檔案 | 說明 |
|------|------|
| `hp1020-print-server.py` | 本地 HTTP 伺服器（foo2zjs 備選方案用） |

## 免責聲明

本倉庫僅為教學和硬件延壽目的。HP LaserJet 相關商標、驅動和專有技術屬於 HP Inc. 所有。參考倉庫提取的檔案來自 Apple 公開分發的 HP Printer Drivers 包。
