import os
import time
import requests
from datetime import datetime, timedelta, timezone

# 🔥 知識ベース出力保管庫フォルダ
OUTPUT_DIR = "outputs/shopee_rules"
os.makedirs(OUTPUT_DIR, exist_ok=True)

jst = timezone(timedelta(hours=9))
current_date = datetime.now(jst).strftime("%Y-%m-%d")

# ==============================================================================
# 🎯 【グローバル防衛網マスターリスト】世界各国のエデュケーションハブ重要カテゴリID
# 各国で規約の整理構造（カテゴリID）が異なるため、国ごとに独立して設定できるようにしています。
# 今後、SGなどの全ページ確認用URL（例: sub_cat_id=XXXX）を入手された際は、対象国の配列に追加・変更してください。
# ==============================================================================
TARGET_CATEGORIES = {
    "TW": [
        46,   # 出品規則 / Listing Policy
        291,  # 物流設定 / Logistics
        1000, # 手續費與服務費 / Fees
        2073, # 跨境賣家規範 / Cross Border Rules
        43,   # 訂單與系統操作 / Orders
        62, 61, 60, 58, 56, 341, 55, 52,
        1219  # 化粧品・医療機器等専門ガイドライン
    ],
    "SG": [
        46,   # Listing Policy & Rules（出品禁止・制限ルール等最重要）
        291,  # Shopee Logistics Channel & SLS（配送ルート・サイズ規定）
        1000, # Seller Fees & Transaction Fees（各種手数料・決済サービス）
        43,   # Order Fulfillment & Penalty Points（注文処理・ペナルティポイント）
        62, 61, 60, 58, 56, 55, 52  # SG特有のセラープログラム・運用ルール
    ],
    "MY": [
        46,   # Listing Policies & Prohibited Items（マレーシア出品禁止ルール）
        291,  # Logistics & Shipping Channels（配送・SLS設定）
        1000, # Transaction Fees & Commissions（販売手数料・税務関連）
        43,   # Fulfillment & Penalty System（出荷遅延率・ペナルティ基準）
        62, 61, 60, 58, 56, 55, 52  # MY特有の重要マーケティング・運用カテゴリ
    ],
    "PH": [
        46, 291, 1000, 43, 62, 61, 60, 58, 56, 55, 52  # フィリピン（主要カテゴリ一網打尽）
    ],
    "TH": [
        46, 291, 1000, 43, 62, 61, 60, 58, 56, 55, 52  # タイ（タイ語マニュアル）
    ],
    "VN": [
        46, 291, 1000, 43, 62, 61, 60, 58, 56, 55, 52  # ベトナム（ベトナム語マニュアル）
    ],
    "BR": [
        46, 291, 1000, 43, 62, 61, 60, 58, 56, 55, 52  # ブラジル（ポルトガル語マニュアル）
    ],
    "JP": [
        1304, 997, 1653, 1654, 1526, 1583, 1527, 1557, 1537, 1540, 1542, 1718, 1550  # 日本越境セラー特有案内
    ]
}

# 🌐 各国のセラー教育ポータル（Seller Education Hub）の正確なドメイン
DOMAINS = {
    "TW": "seller.shopee.tw",
    "SG": "seller.shopee.sg",
    "MY": "seller.shopee.com.my",
    "PH": "seller.shopee.ph",
    "TH": "seller.shopee.co.th",
    "VN": "seller.shopee.vn",
    "BR": "seller.shopee.com.br",
    "JP": "shopee.jp"
}

# 🚩 各国の識別フラグ（国旗）
FLAGS = {
    "TW": "🇹🇼", "SG": "🇸🇬", "MY": "🇲🇾", "PH": "🇵🇭",
    "TH": "🇹🇭", "VN": "🇻🇳", "BR": "🇧🇷", "JP": "🇯🇵"
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9,ja;q=0.8"
}

def fetch_shopee_api_category(sub_cat_id, region):
    """リージョンごとのバックエンドAPIから直接記事タイトル一覧を奪取"""
    domain = DOMAINS.get(region, "shopee.jp")
    api_url = f"https://{domain}/api/v2/edu/modules?sub_cat_id={sub_cat_id}"
    
    try:
        response = requests.get(api_url, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data.get("data", {}).get("modules", [])
    except Exception as e:
        print(f"[{region} API エラー] カテゴリID {sub_cat_id}: {e}")
    return []

def fetch_shopee_article_body(post_id, region):
    """個別記事の奥底へ潜り込み、本文テキストを直接強奪する"""
    domain = DOMAINS.get(region, "shopee.jp")
    api_url = f"https://{domain}/api/v2/edu/posts/{post_id}"
    try:
        response = requests.get(api_url, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            post_data = response.json().get("data", {}).get("post", {})
            return post_data.get("content", "")
    except Exception as e:
        print(f"[{region} API 本文エラー] 記事ID {post_id}: {e}")
    return ""

def run_crawler():
    print("=== ⚖️ Shopee 法務・規約監視部門：グローバル一括ディープスキャン開始 ===")
    
    report = f"# 📰 Shopee グローバル規約知識データベース ({current_date})\n"
    report += "<!-- このファイルは全AI社員の共通知識ベースとして自動更新されます -->\n\n"
    report += "## 🎯 監視対象国: TW, SG, MY, PH, TH, VN, BR, JP\n\n"
    
    # バッククォークのエスケープ用変数（システムの干渉を100%防止）
    ticks = "```"
    
    for region, cat_ids in TARGET_CATEGORIES.items():
        flag = FLAGS.get(region, "🏳️")
        report += f"## {flag} Shopee {region} セラーエデュケーションハブ 巡回結果\n\n"
        
        for cat_id in cat_ids:
            print(f"[{region} スキャン中] カテゴリID: {cat_id} ...")
            modules = fetch_shopee_api_category(cat_id, region)
            
            articles_found = False
            for module in modules:
                for post in module.get("posts", []):
                    title = post.get("title")
                    post_id = post.get("id")
                    updated_at = post.get("updated_at", 0)
                    date_str = datetime.fromtimestamp(updated_at, jst).strftime('%Y-%m-%d') if updated_at else "不明"
                    
                    print(f"[{region}] 📄 記事本文読込中: {title[:20]}...")
                    body_content = fetch_shopee_article_body(post_id, region)
                    
                    report += f"### 📝 [{date_str}] {title} (ID: {post_id})\n"
                    report += f"- **元URL:** https://{DOMAINS[region]}/edu/article/{post_id}\n"
                    report += f"- **本文データ（生データ）:**\n"
                    
                    if body_content:
                        clean_body = body_content.replace("<p>", "").replace("</p>", "\n").replace("<br>", "\n")
                        # 知識ベースとしてのコンテキスト容量を確保するため、主要部分を切り出して蓄積
                        report += f"{ticks}text\n{clean_body[:1200]}\n{ticks}\n\n"
                    else:
                        report += "*(本文データの取得失敗、または空です)*\n\n"
                        
                    articles_found = True
                    time.sleep(0.5) # 連続アクセスのウェイト
                    
            if not articles_found:
                pass # 出力の視認性を高めるため、空のカテゴリはスキップ
            time.sleep(1)

    # 💾 共有知識ベースとして上書き保存
    report_file = os.path.join(OUTPUT_DIR, f"{current_date}_shopee_rules_raw.md")
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report)
        
    print(f"✅ グローバル全地域のディープナレッジ回収が完了しました。 -> `{report_file}`")

if __name__ == "__main__":
    run_crawler()
