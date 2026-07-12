import os
import time
import requests
from datetime import datetime, timedelta, timezone

# 🔥 知識ベース出力保管庫フォルダ
OUTPUT_DIR = "outputs/shopee_rules"
os.makedirs(OUTPUT_DIR, exist_ok=True)

jst = timezone(timedelta(hours=9))
current_date = datetime.now(jst).strftime("%Y-%m-%d")

TARGET_CATEGORIES = {
    "TW": [46, 291, 1000, 2073, 43, 62, 61, 60, 58, 56, 341, 55, 52, 1219],
    "SG": [46, 291, 1000, 43, 62, 61, 60, 58, 56, 55, 52],
    "MY": [46, 291, 1000, 43, 62, 61, 60, 58, 56, 55, 52],
    "JP": [1304, 997, 1653, 1654, 1526, 1583, 1527, 1557, 1537, 1540, 1542, 1718, 1550]
}

DOMAINS = {
    "TW": "seller.shopee.tw",
    "SG": "seller.shopee.sg",
    "MY": "seller.shopee.com.my",
    "JP": "shopee.jp"
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9,ja;q=0.8"
}

def fetch_shopee_api_category(sub_cat_id, region):
    """目次(記事一覧)を引っこ抜く"""
    domain = DOMAINS.get(region, "shopee.jp")
    api_url = f"https://{domain}/api/v2/edu/modules?sub_cat_id={sub_cat_id}"
    try:
        response = requests.get(api_url, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            return response.json().get("data", {}).get("modules", [])
    except Exception as e:
        print(f"[{region} API 目次エラー] カテゴリ {sub_cat_id}: {e}")
    return []

def fetch_shopee_article_body(post_id, region):
    """【新設】個別記事の奥底へ潜り込み、本文テキストを直接強奪する"""
    domain = DOMAINS.get(region, "shopee.jp")
    api_url = f"https://{domain}/api/v2/edu/posts/{post_id}"
    try:
        response = requests.get(api_url, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            post_data = response.json().get("data", {}).get("post", {})
            # 本文（HTML/JSON混在）から極力プレーンなテキスト、または要約用のコンテンツを抽出
            return post_data.get("content", "")
    except Exception as e:
        print(f"[{region} API 本文エラー] 記事ID {post_id}: {e}")
    return ""

def run_crawler():
    print("=== ⚖️ Shopee 法務・規約監視部門：ディープナレッジスキャン開始 ===")
    
    report = f"# 📰 Shopee 3カ国横断・規約知識データベース ({current_date})\n"
    report += "\n\n"
    
    for region, cat_ids in TARGET_CATEGORIES.items():
        flag = '🇹🇼' if region=='TW' else '🇸🇬' if region=='SG' else '🇲🇾' if region=='MY' else '🇯🇵'
        report += f"## {flag} Shopee {region} ナレッジベース\n\n"
        
        for cat_id in cat_ids:
            modules = fetch_shopee_api_category(cat_id, region)
            base_url = f"https://{DOMAINS[region]}/edu/category?sub_cat_id={cat_id}"
            
            articles_found = False
            for module in modules:
                for post in module.get("posts", []):
                    title = post.get("title")
                    post_id = post.get("id")
                    updated_at = post.get("updated_at", 0)
                    date_str = datetime.fromtimestamp(updated_at, jst).strftime('%Y-%m-%d') if updated_at else "不明"
                    
                    print(f"[{region}] 📄 記事読込中: {title[:20]}...")
                    # 🎯 深層探索：個別記事の本文を引っこ抜く
                    body_content = fetch_shopee_article_body(post_id, region)
                    
                    report += f"### 📝 [{date_str}] {title} (ID: {post_id})\n"
                    report += f"- **元URL:** https://{DOMAINS[region]}/edu/article/{post_id}\n"
                    report += f"- **本文データ（生データ）:**\n"
                    
                    if body_content:
                        # 軽く不要なHTMLタグを削ぎ落として読みやすく整形
                        clean_body = body_content.replace("<p>", "").replace("</p>", "\n").replace("", "\n")
                        # 長すぎる場合は最初の1000文字程度を知識ベースに格納（必要に応じて調整）
                        report += f"
http://googleusercontent.com/immersive_entry_chip/0

---

## 🎯 次のステップ：AI（LLM）への知識共有の仕掛け

このコードをプッシュすれば、次回の巡回から「目次＋具体的な規約の本文（化粧品・知財ルールなど）」がすべて1つのマークダウンファイルにガッツリ蓄積されるようになります。

これが完了したら、次は**「この蓄積されたルールブックをLLM（AI社員）に毎朝読み込ませて、『前回からの変更点』や『化粧品・ブランド転売における即死リスク』だけをピンポイントに弾き出す要約エージェント」**の頭脳をここにドッキングさせましょう。

まずはこのコードに書き換えてコミット・プッシュをお願いします。完了したら、AIの「知能」部分の実装へ進みましょう！
