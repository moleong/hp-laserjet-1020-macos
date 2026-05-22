#!/usr/bin/env python3
"""
HP LaserJet 1020 本地打印伺服器
運行後在瀏覽器開啟 http://localhost:8765
支援拖放或上傳 PDF，一鍵打印
"""

import os
import subprocess
import tempfile
import shutil
import time
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse

HTML_PAGE = '''<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>HP LaserJet 1020 打印</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: #1a1a2e;
            color: #eee;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 40px 20px;
        }
        h1 { font-size: 24px; margin-bottom: 8px; color: #fff; }
        .subtitle { color: #888; font-size: 14px; margin-bottom: 30px; }
        .drop-zone {
            width: 100%;
            max-width: 500px;
            height: 200px;
            border: 2px dashed #444;
            border-radius: 16px;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            transition: all 0.3s;
            background: #16213e;
        }
        .drop-zone:hover, .drop-zone.dragover {
            border-color: #e94560;
            background: #1a2744;
        }
        .drop-zone svg {
            width: 48px;
            height: 48px;
            margin-bottom: 12px;
            fill: #e94560;
        }
        .drop-zone p { color: #aaa; font-size: 16px; }
        .drop-zone .hint { color: #666; font-size: 12px; margin-top: 6px; }
        #file-input { display: none; }
        .file-info {
            margin-top: 20px;
            padding: 16px 20px;
            background: #16213e;
            border-radius: 12px;
            width: 100%;
            max-width: 500px;
            display: none;
        }
        .file-info.active { display: block; }
        .file-name { font-weight: 600; color: #fff; margin-bottom: 4px; }
        .file-size { color: #888; font-size: 13px; }
        .btn-print {
            margin-top: 20px;
            width: 100%;
            max-width: 500px;
            padding: 16px;
            border: none;
            border-radius: 12px;
            background: #e94560;
            color: #fff;
            font-size: 18px;
            font-weight: 600;
            cursor: pointer;
            transition: background 0.3s;
            display: none;
        }
        .btn-print:hover { background: #ff6b6b; }
        .btn-print.active { display: block; }
        .btn-print:disabled {
            background: #444;
            cursor: not-allowed;
        }
        .status {
            margin-top: 20px;
            padding: 12px 20px;
            border-radius: 10px;
            width: 100%;
            max-width: 500px;
            display: none;
            font-size: 14px;
        }
        .status.active { display: block; }
        .status.success { background: #1e3a2f; color: #4ade80; }
        .status.error { background: #3a1e1e; color: #f87171; }
        .status.info { background: #1e2a3a; color: #60a5fa; }
        .spinner {
            display: inline-block;
            width: 16px;
            height: 16px;
            border: 2px solid #fff;
            border-top-color: transparent;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin-right: 8px;
            vertical-align: middle;
        }
        @keyframes spin { to { transform: rotate(360deg); } }
    </style>
</head>
<body>
    <h1>HP LaserJet 1020 打印</h1>
    <p class="subtitle">拖放 PDF 檔案或點擊上傳</p>

    <div class="drop-zone" id="dropZone">
        <svg viewBox="0 0 24 24"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6zm4 18H6V4h7v5h5v11zM12 9L9 13h2v4h2v-4h2L12 9z"/></svg>
        <p>拖放 PDF 到這裡</p>
        <p class="hint">或點擊選擇檔案</p>
    </div>
    <input type="file" id="file-input" accept=".pdf,application/pdf">

    <div class="file-info" id="fileInfo">
        <div class="file-name" id="fileName"></div>
        <div class="file-size" id="fileSize"></div>
    </div>

    <button class="btn-print" id="btnPrint">打印</button>

    <div class="status" id="status"></div>

    <script>
        const dropZone = document.getElementById('dropZone');
        const fileInput = document.getElementById('file-input');
        const fileInfo = document.getElementById('fileInfo');
        const fileName = document.getElementById('fileName');
        const fileSize = document.getElementById('fileSize');
        const btnPrint = document.getElementById('btnPrint');
        const status = document.getElementById('status');

        let currentFile = null;

        dropZone.addEventListener('click', () => fileInput.click());

        dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropZone.classList.add('dragover');
        });

        dropZone.addEventListener('dragleave', () => {
            dropZone.classList.remove('dragover');
        });

        dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropZone.classList.remove('dragover');
            const files = e.dataTransfer.files;
            if (files.length > 0) handleFile(files[0]);
        });

        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) handleFile(e.target.files[0]);
        });

        function handleFile(file) {
            if (file.type !== 'application/pdf' && !file.name.toLowerCase().endsWith('.pdf')) {
                showStatus('請上傳 PDF 檔案', 'error');
                return;
            }
            currentFile = file;
            fileName.textContent = file.name;
            fileSize.textContent = formatSize(file.size);
            fileInfo.classList.add('active');
            btnPrint.classList.add('active');
            status.classList.remove('active');
        }

        function formatSize(bytes) {
            if (bytes < 1024) return bytes + ' B';
            if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
            return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
        }

        function showStatus(msg, type) {
            status.textContent = msg;
            status.className = 'status ' + type + ' active';
        }

        btnPrint.addEventListener('click', async () => {
            if (!currentFile) return;

            btnPrint.disabled = true;
            showStatus('正在處理...', 'info');
            status.innerHTML = '<span class="spinner"></span>正在轉換並發送到印表機...';

            const formData = new FormData();
            formData.append('pdf', currentFile);

            try {
                const response = await fetch('/print', {
                    method: 'POST',
                    body: formData
                });
                const result = await response.json();

                if (result.success) {
                    showStatus('✓ ' + result.message, 'success');
                } else {
                    showStatus('✗ ' + result.message, 'error');
                }
            } catch (err) {
                showStatus('✗ 連線失敗: ' + err.message, 'error');
            }

            btnPrint.disabled = false;
        });
    </script>
</body>
</html>'''


class PrintHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(HTML_PAGE.encode('utf-8'))

    def do_POST(self):
        if self.path != '/print':
            self.send_error(404)
            return

        content_type = self.headers.get('Content-Type', '')
        if not content_type.startswith('multipart/form-data'):
            self.send_error(400)
            return

        boundary = content_type.split('boundary=')[1].strip()
        if boundary.startswith('"') and boundary.endswith('"'):
            boundary = boundary[1:-1]

        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)

        # Parse multipart form
        parts = body.split(('--' + boundary).encode())
        pdf_data = None

        for part in parts:
            if b'Content-Disposition' in part and b'filename=' in part:
                # Extract file data
                header_end = part.find(b'\r\n\r\n')
                if header_end > 0:
                    pdf_data = part[header_end + 4:]
                    # Remove trailing \r\n before boundary
                    if pdf_data.endswith(b'\r\n'):
                        pdf_data = pdf_data[:-2]
                    break

        if not pdf_data:
            self._respond(False, '未能讀取 PDF 檔案')
            return

        result = self._print_pdf(pdf_data)
        self._respond(result['success'], result['message'])

    def _print_pdf(self, pdf_data):
        tmpdir = tempfile.mkdtemp(prefix='hp1020-')
        pdf_path = os.path.join(tmpdir, 'input.pdf')
        ps_path = os.path.join(tmpdir, 'output.ps')
        zjs_path = os.path.join(tmpdir, 'output.zjs')

        try:
            # Save PDF
            with open(pdf_path, 'wb') as f:
                f.write(pdf_data)

            # PDF to PostScript
            gs_result = subprocess.run(
                ['/opt/homebrew/bin/gs', '-q', '-dNOPAUSE', '-dBATCH',
                 '-sDEVICE=ps2write', f'-sOutputFile={ps_path}', pdf_path],
                capture_output=True, timeout=30
            )
            if gs_result.returncode != 0:
                return {'success': False, 'message': 'PDF 轉換失敗'}

            # PostScript to ZjStream
            with open(zjs_path, 'wb') as zjs_file:
                wrapper_result = subprocess.run(
                    ['/usr/local/bin/foo2zjs-wrapper', '-P', '-z1', '-L0',
                     '-r1200x600', '-pletter', ps_path],
                    stdout=zjs_file, stderr=subprocess.PIPE, timeout=30
                )
            if wrapper_result.returncode != 0:
                return {'success': False, 'message': '印表機格式轉換失敗'}

            # Send to printer
            lp_result = subprocess.run(
                ['lp', '-d', 'HP_LaserJet_1020', '-o', 'raw', zjs_path],
                capture_output=True, timeout=30
            )
            if lp_result.returncode != 0:
                err = lp_result.stderr.decode('utf-8', errors='ignore')[:200]
                return {'success': False, 'message': f'發送到印表機失敗: {err}'}

            return {'success': True, 'message': '已發送到印表機'}

        except subprocess.TimeoutExpired:
            return {'success': False, 'message': '處理超時'}
        except Exception as e:
            return {'success': False, 'message': f'錯誤: {str(e)}'}
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    def _respond(self, success, message):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        import json
        self.wfile.write(json.dumps({'success': success, 'message': message}).encode())


def main():
    port = 8765
    server = HTTPServer(('127.0.0.1', port), PrintHandler)
    print(f'HP LaserJet 1020 打印伺服器已啟動')
    print(f'請在瀏覽器開啟: http://localhost:{port}')
    print('按 Ctrl+C 停止')

    # 自動開啟瀏覽器
    url = f'http://localhost:{port}'
    time.sleep(0.5)
    webbrowser.open(url)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\n已停止')


if __name__ == '__main__':
    main()
