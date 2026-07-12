import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta, timezone

# 🔥 出力保管庫フォルダ
OUTPUT_DIR = "outputs/shopee_rules"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# タイムゾーン設定
jst = timezone(timedelta(hours=9))
current_date = datetime.now(jst).strftime("%Y-%m-%d")

def crawl_shopee_announcements():
    print("=== ⚖️ Shopee 法務・規約監視部門：情報収集を開始 ===")
    
    # 🎯 ターゲットURL（Shopee Taiwan 賣家大學のアナウンスページ & Shopee Japan 公式）
    targets = {
        "shopee_taiwan_edu": "https://seller.shopee.tw/edu/home",
        "shopee_japan_news": "https://shopee.jp/edu/article/" # 例としての汎用URL（実際の構造に合わせて調整可能）
    }
    
    combined_report = f"# 📰 Shopee 規約・重要事項 巡回ログ ({current_date})\n\n"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    for name, url in targets.items():
        print(f"[調査中] {name} ({url}) から最新の規約・重要トピックをスキャン中...")
        try:
            response = requests.get(url, headers=headers, timeout=15)
            response.encoding = 'utf-8'
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "html.parser")
                
                # 簡易的にテキスト、リンク、重要な告知エリアのテキストを抽出
                # ※Shopee側がJavaScript（React等）で動的描画している場合は、後々Playwright等への拡張を検討します
                page_text = soup.get_text(separator="\n", strip=True)
                
                # 抽出したデータから、手数料や配送に関するキーワードが含まれる行をフィルタリングして要約の種にする
                lines = page_text.split("\n")
                important_lines = [l for l in lines if any(k in l for k in ["手續費", "運費", "規範", "公告", "手数料", "配送", "規約", "重要"])]
                
                combined_report += f"## 🌐 ソース: {name}\n"
                combined_report += f"🔗 URL: {url}\n\n"
                combined_report += "### 📌 検知された重要キーワード・トピック\n"
                
                if important_lines:
                    for line in important_lines[:20]: # 最初の上位20件をピックアップ
                        combined_report += f"- {line}\n"
                else:
                    combined_report += "- 明示的な重要キーワードは表面上のテキストから検知されませんでした（要詳細パース）。\n"
                
                combined_report += "\n---\n\n"
            else:
                combined_report += f"## 🌐 ソース: {name}\n❌ 接続失敗 (Status Code: {response.status_code})\n\n---\n\n"
                
        except Exception as e:
            print(f"❌ {name} の取得中にエラーが発生しました: {e}")
            combined_report += f"## 🌐 ソース: {name}\n❌ エラー発生: {e}\n\n---\n\n"

    # 💾 物理ファイルとしてレポートを保存
    report_file = os.path.join(OUTPUT_DIR, f"{current_date}_shopee_rules_raw.md")
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(combined_report)
        
    print(f"✅ 巡回完了。成果物を格納しました -> `{report_file}`")

if __name__ == "__main__":
    crawl_shopee_announcements()
