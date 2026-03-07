#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OCR 圖片內容提取工具
自動掃描資料夾內所有 JPG 圖片，提取文字成 JSON
"""

import os
import json
import sys
from pathlib import Path

try:
    import easyocr
except ImportError:
    print("❌ 缺少 easyocr 套件，正在安裝...")
    os.system(f"{sys.executable} -m pip install easyocr pillow -q")
    import easyocr

try:
    from PIL import Image
except ImportError:
    os.system(f"{sys.executable} -m pip install pillow -q")
    from PIL import Image


def extract_text_from_image(image_path, reader):
    """從單張圖片提取文字"""
    try:
        print(f"  ⏳ 處理: {os.path.basename(image_path)}...", end=" ", flush=True)
        # 用 Pillow 讀取圖片（支援中文檔名），再傳給 EasyOCR
        image = Image.open(image_path)
        result = reader.readtext(image, detail=0)  # detail=0 只返回文字
        text = "\n".join(result)
        print(f"✅")
        return text
    except Exception as e:
        print(f"❌ 失敗: {e}")
        return ""


def main():
    """主程式"""
    # 設定路徑
    script_dir = Path(__file__).parent
    print(f"\n📁 掃描目錄: {script_dir}\n")

    # 初始化 OCR 讀取器（繁體中文 + 英文）
    print("🤖 初始化 OCR 引擎（首次執行需要下載模型，約 200-300 MB）...")
    try:
        reader = easyocr.Reader(['ch_tra', 'en'], verbose=False, gpu=False)
    except Exception as e:
        print(f"❌ OCR 初始化失敗: {e}")
        return

    # 收集影像檔案
    image_extensions = ['.jpg', '.jpeg', '.png', '.bmp']
    image_files = []
    
    for ext in image_extensions:
        image_files.extend(sorted(script_dir.glob(f"*{ext}")))
        image_files.extend(sorted(script_dir.glob(f"*{ext.upper()}")))

    if not image_files:
        print("❌ 找不到任何圖片檔案！")
        return

    print(f"🖼️  找到 {len(image_files)} 張圖片\n")
    print("🔍 開始 OCR 提取文字...\n")

    # OCR 每張圖片
    ocr_results = {}
    for idx, image_path in enumerate(image_files, 1):
        filename = os.path.basename(image_path)
        print(f"[{idx}/{len(image_files)}]", end=" ")
        
        text = extract_text_from_image(str(image_path), reader)
        ocr_results[filename] = {
            "filename": filename,
            "text": text,
            "lines": text.split("\n") if text else []
        }

    # 輸出 JSON
    output_file = script_dir / "ocr_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(ocr_results, f, ensure_ascii=False, indent=2)

    print(f"\n\n✅ 完成！結果已保存到: {output_file}")
    print(f"   共提取 {len(ocr_results)} 張圖片的文字")
    
    # 預覽前 3 張的結果
    print("\n📋 預覽前 3 張圖片的 OCR 結果：")
    for i, (filename, data) in enumerate(list(ocr_results.items())[:3], 1):
        preview = data["text"][:100].replace("\n", " ")
        print(f"\n[{filename}]")
        print(f"  {preview}{'...' if len(data['text']) > 100 else ''}")

    print("\n" + "="*50)
    print("✨ 下一步: 執行 integrate_ocr.py 將內容整合進 HTML")
    print("="*50 + "\n")


if __name__ == "__main__":
    main()
