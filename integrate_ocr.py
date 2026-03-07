#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
將 OCR 結果整合進 HTML 搜尋系統
"""

import json
import re
from pathlib import Path

def load_ocr_results():
    """讀取 OCR 結果"""
    ocr_file = Path("ocr_results.json")
    if not ocr_file.exists():
        print("❌ 找不到 ocr_results.json，請先執行 ocr_images.py")
        return {}
    
    with open(ocr_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def extract_keywords(filename, text):
    """從檔名和文字提取關鍵詞和標籤"""
    keywords = []
    tags = set()
    
    # 根據檔名推測標籤
    if "行前須知" in filename:
        tags.add("圖片須知")
        tags.add("重要")
    elif "消防須知" in filename:
        tags.add("安全")
        tags.add("消防")
        tags.add("重要")
    
    # 根據文字內容推測標籤
    text_lower = text.lower()
    content_lower = text  # 繁體中文搜尋仍用原文
    
    if any(word in content_lower for word in ["禁止", "不得", "不可", "不能", "嚴禁"]):
        tags.add("禁止事項")
    
    if any(word in content_lower for word in ["時間", "時刻", "幾點", "開始", "結束"]):
        tags.add("時間")
    
    if any(word in content_lower for word in ["位置", "地點", "樓層", "區域", "堂"]):
        tags.add("位置")
    
    if any(word in content_lower for word in ["安全", "疏散", "逃生", "消防", "避難"]):
        tags.add("安全")
    
    return list(tags) if tags else ["圖片內容"]

def create_html_with_ocr(ocr_data):
    """建立包含 OCR 資料的新 HTML"""
    
    # 讀取原始 HTML
    html_file = Path("search.html")
    if not html_file.exists():
        print("❌ 找不到 search.html")
        return
    
    with open(html_file, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # 為每張圖片建立搜尋文檔
    ocr_documents = []
    doc_id = 16  # 從 ID 16 開始（前 15 個是手動內容）
    
    seen_files = set()  # 追蹤已處理的檔案（去重複）
    
    for filename, data in sorted(ocr_data.items()):
        if filename in seen_files:
            continue
        seen_files.add(filename)
        
        text = data.get("text", "").strip()
        if not text:
            continue
        
        # 清理文字
        text = text.replace('\n\n\n', '\n').replace('\n\n', '\n')
        
        # 提取標籤
        tags = extract_keywords(filename, text)
        
        # 建立文檔
        doc = {
            "id": doc_id,
            "title": filename.replace('.jpg', '').replace('.jpeg', '').replace('.png', ''),
            "source": "圖片內容",
            "tags": tags,
            "content": text[:500]  # 代碼中用前 500 字元，全文存在 fullText
        }
        
        ocr_documents.append(doc)
        doc_id += 1
    
    print(f"✅ 建立了 {len(ocr_documents)} 個圖片搜尋文檔")
    
    # 產生 JavaScript 代碼
    documents_js = "const documents = [\n"
    
    # 先加入原始文檔
    original_docs_start = html_content.find("const documents = [")
    original_docs_end = html_content.find("];", original_docs_start) + 2
    original_docs_str = html_content[original_docs_start:original_docs_end]
    
    # 提取原始文檔
    import ast
    
    # 用正規表達式提取原始文檔部分
    match = re.search(r'const documents = \[(.*?)\];', html_content, re.DOTALL)
    if not match:
        print("❌ 無法在 HTML 中找到 documents 陣列")
        return
    
    # 手動建立完整的文檔列表
    all_docs = [
        {
            "id": 1,
            "title": "上班時間與集合地點",
            "source": "集合訊息",
            "tags": ["時間", "位置", "報到"],
            "content": "【日期】3月7日\n【上班時間】14:30前完成報到\n督導於14:15開始點名\n\n【集合地點】台北大巨蛋B2層 Gate5\n台北市信義區忠孝東路四段515號"
        },
        {
            "id": 2,
            "title": "演出時間表",
            "source": "動線及進場時間",
            "tags": ["時間", "流程"],
            "content": "03月07日（六）\n預計彩排進場時間：15:00\n預計彩排開始時間：16:30\n預計進場時間：17:00\n預計開演時間：19:00\n\n【重要】觀眾詢問時間，都要加上「預計」"
        },
        {
            "id": 3,
            "title": "服裝規定與必帶物品",
            "source": "集合訊息",
            "tags": ["服裝", "必帶物品"],
            "content": "【活動服裝】\n黑色素面無logo上衣（不侷限長袖或短袖）\n黑色無破洞長褲\n一般球鞋/布鞋\n怕冷者需自備黑色素面外套\n\n【必帶物品】\n🔦 手電筒 (非常重要！)\n\n【禁止】\n- 包包無法背在身上上班，統一放在休息區\n- 室內活動無法帶帽\n- 非督導人員不可使用手機掛繩"
        },
        {
            "id": 4,
            "title": "禁止拍照、錄影、錄音",
            "source": "工作守則",
            "tags": ["禁止行為", "黑名單"],
            "content": "【違反直接黑名單】\n期間禁止拍照、錄影/音（任何現場相關人事物都是）\n\n上班期間若拿手機出來拍照、錄影，被發現會：\n1. 請你刪掉\n2. 直接下班\n3. 進入瑪思黑名單（永不錄用）\n\n包括自拍、拍證件、拍表演都禁止"
        },
        {
            "id": 5,
            "title": "禁止與藝人互動",
            "source": "工作守則及注意事項",
            "tags": ["禁止行為", "粉絲行為"],
            "content": "【禁止】\n不得與任何前來參與活動之名人、明星、藝人等做任何形式接觸及粉絲行為\n\n包括但不限於：\n- 看表演\n- 拍手\n- 隨節奏搖晃\n- 跟著唱歌\n- 收集應援物\n- 要求合照、簽名\n\n工作期間請勿跟隨音樂搖擺或有任何粉絲行為"
        },
        {
            "id": 6,
            "title": "禁止使用手機與社群發布",
            "source": "工作守則",
            "tags": ["禁止行為", "手機"],
            "content": "【禁止使用手機】\n工作期間禁止使用手機（除了現場工作聯絡之外）\n\n【禁止社群發布】\n所有關於活動的任何事件，請勿在社群（LINE/FB/IG/Threads等）上發布文字、照片或影片\n\n【禁止傳播】\n不得將相關文件/證件以任何形式傳播出去（如拍照工作證上傳）\n包括活動流程、通行工作證等"
        },
        {
            "id": 7,
            "title": "遲到與報到規定",
            "source": "工作守則及集合訊息",
            "tags": ["報到", "重要"],
            "content": "【重要】雙方雇傭關係從完成現場報到手續後開始生效\n\n【遲到認定】\n以下任何情況都算遲到：\n- 時間到了但還在停車\n- 還沒報到先去上廁所\n- 任何尚未跟督導報到的情況\n\n遲到者將從實際完成報到時間開始計薪\n且視現場缺額狀況決定是否取消工作資格"
        },
        {
            "id": 8,
            "title": "薪資與現領規定",
            "source": "工作守則",
            "tags": ["薪資", "現領"],
            "content": "【現領規則】\n此專案為下班現領（不匯款）\n\n【領薪細節】\n1. 請記得領完薪資再離開\n2. 當場確認完再離開\n3. 不要在現場討論薪資\n4. 公司只會準備千鈔\n5. 請自備零錢百鈔方便找零\n\n【計薪】\n排隊等領薪的時間已屬於「下班後」，因此並無計薪\n工作時間依照現場狀況及客戶需求調整，會依照實際時數計薪"
        },
        {
            "id": 9,
            "title": "督導聯絡電話（緊急用）",
            "source": "動線及進場時間",
            "tags": ["聯絡", "緊急"],
            "content": "⚠️ 緊急狀況請先打電話給督導，跟我們說在哪區\n\n【B1區督導】\n狗狗：0912-480515\nAngela：0922-608469\n\n【L2區督導】\nBella：0974-066271\n華：0970-238058"
        },
        {
            "id": 10,
            "title": "疏散與安全要點",
            "source": "動線及進場時間",
            "tags": ["安全", "疏散"],
            "content": "【緊急避難平台位置】（消防隊可能隨時來抽查）\nL2層：\n- 中央手扶梯左右兩側平台\n- 安全梯6號側門推開\n- 安全梯20號側門推開，第二扇門外平台\n\n【行動不便者】\n無法及時離開疏散，可至平台等待救援\n\n【一般離場】\n就近逃生梯離場（消防卡黃色框安全門）\n\n【安全梯規則】\n- A、D安全梯保持常開\n- 散場時其他安全梯須開啟\n- 散場時安全門一律只出不進"
        },
        {
            "id": 11,
            "title": "場館規定與服務點位",
            "source": "動線及進場時間",
            "tags": ["場館規定", "位置"],
            "content": "【飲食規定】\n全場館禁止飲食，瓶裝水除外\n場內僅有飲水機，買水請到外面全家\n\n【電梯使用】\n中央電梯可使用：\n- 佩戴工作證者\n- 輪椅、娃娃車使用者\n- 孕婦、行動不便者\n\n【服務點位時間】\nVIP兌換處：B1 515（全家旁邊）1200-1600\n周邊販售：B2 515（Gate 5旁邊）1200-2000\n票務櫃檯：Gate 4門外 1300-2000\n國泰兌換櫃檯：B1\n\n【吸菸室】\n場館內全面禁菸，無設置吸煙區\n請往場館外移動到忠孝東路人行道或逸仙路辦公大樓"
        },
        {
            "id": 12,
            "title": "處理觀眾問題的應對方式",
            "source": "動線及進場時間",
            "tags": ["觀眾應對", "工作"],
            "content": "【不會回答的問題】\n禮貌請觀眾稍等，再詢問督導\n公版回答：「不好意思，我跟督導確認一下，請稍等」\n\n【清潔問題】\n觀眾打翻東西需要清潔，請拍照並告知區域位置回報\n格式：xxx區xx排xx號 水打翻（群組內附照片）\n\n【觀眾拍照請求】\n上班期間若遇到觀眾要幫忙拍照\n請委婉說明正在工作，無法幫忙拍照\n\n【醫護需求】\n有觀眾身體不適、受傷，請先回報給督導"
        },
        {
            "id": 13,
            "title": "演出期間的拍照規則",
            "source": "動線及進場時間",
            "tags": ["拍照", "規定"],
            "content": "【演出開始後規則】\n僅能在Talking&VCR時段才能進入座位區\n\n【拍攝設備規定】\n演出時僅能使用手機拍攝\n其他專業攝影設備皆禁止使用\n（手機望遠鏡頭也無法）"
        },
        {
            "id": 14,
            "title": "不得隨意亂跑與崗位規定",
            "source": "動線及進場時間",
            "tags": ["工作規則"],
            "content": "【不要隨意亂跑】\n需要離開崗位，請跟督導通知你站的區域位置\n等到有人替補上再離開"
        },
        {
            "id": 15,
            "title": "稅務與勞務資料申報",
            "source": "注意事項",
            "tags": ["行政"],
            "content": "【勞務報酬資料】\n未在本公司建立勞務報酬資料電子檔者，須先完成建檔\n否則將等資料補齊才匯款\n\n【扣繳憑單】\n因應環保電子化，公司不再寄出紙本扣繳憑單\n隔年5月申報所得稅時，請自行用自然人憑證等方式登入查詢收入"
        }
    ]
    
    # 加入 OCR 文檔
    all_docs.extend(ocr_documents)
    
    # 產生 JSON 代碼
    def doc_to_js(doc):
        return f"""            {{
                id: {doc['id']},
                title: "{doc['title'].replace('"', '\\"')}",
                source: "{doc['source']}",
                tags: {json.dumps(doc['tags'], ensure_ascii=False)},
                content: `{doc['content'].replace('`', '\\`')}`
            }}"""
    
    all_docs_js = ",\n".join(doc_to_js(doc) for doc in all_docs)
    
    # 替換 HTML 中的 documents 
    new_documents_section = f"const documents = [\n{all_docs_js}\n        ];"
    
    new_html = re.sub(
        r'const documents = \[.*?\];',
        new_documents_section,
        html_content,
        flags=re.DOTALL
    )
    
    # 保存新 HTML
    with open("search.html", 'w', encoding='utf-8') as f:
        f.write(new_html)
    
    print(f"\n✅ HTML 已更新！")
    print(f"   - 原始文檔：15 個")
    print(f"   - 新增圖片文檔：{len(ocr_documents)} 個")
    print(f"   - 總共：{len(all_docs)} 個可搜尋項目")
    print(f"\n🎉 現在可以搜尋圖片內容了！")


def main():
    print("\n" + "="*50)
    print("  整合 OCR 結果到搜尋系統")
    print("="*50 + "\n")
    
    ocr_data = load_ocr_results()
    if not ocr_data:
        return
    
    create_html_with_ocr(ocr_data)
    print("\n💡 提示：重啟瀏覽器查看最新的 search.html")
    print("="*50 + "\n")


if __name__ == "__main__":
    main()
