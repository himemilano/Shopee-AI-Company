import os
import sys
import time
import json
import csv
import base64
import requests
from datetime import datetime, timedelta, timezone

# ==========================================================
# 💸 1. 国別・実務特化型 利益＆適正価格計算シミュレーター
# ==========================================================
class ShopeePricingEngine:
    """Shopee各仕向け国（SG, MY, TW）の手数料、配送料、為替を正確に計算する"""
    def __init__(self, target_country="SG"):
        self.target_country = target_country.upper()
        
        # 実務に基づいた最新の為替レート・手数料率の設定
        if self.target_country == "SG":  # シンガポール
            self.currency = "SGD"
            self.exchange_rate = 115.5   # 1 SGD = 115.5 円
            self.commission_rate = 0.08  # 販売手数料 8.0%
            self.transaction_rate = 0.022 # 決済手数料 2.2%
            self.service_rate = 0.03     # CCB+FSSプログラム参加料 3.0%
        elif self.target_country == "MY": # マレーシア
            self.currency = "MYR"
            self.exchange_rate = 35.2    # 1 MYR = 35.2 円
            self.commission_rate = 0.08
            self.transaction_rate = 0.022
            self.service_rate = 0.04     # マレーシアはプログラム手数料がやや高め
        elif self.target_country == "TW": # 台湾
            self.currency = "TWD"
            self.exchange_rate = 4.8     # 1 TWD = 4.8 円
            self.commission_rate = 0.085 # 台湾は販売手数料が変動（最大8.5%）
            self.transaction_rate = 0.022
            self.service_rate = 0.03
        else:
            # デフォルト (SG基準)
            self.currency = "SGD"
            self.exchange_rate = 115.5
            self.commission_rate = 0.08
            self.transaction_rate = 0.022
            self.service_rate = 0.03

    def calculate(self, cost_jpy, selling_price_local, weight_g):
        """
        cost_jpy: 国内仕入価格 + 国内送料 (円)
        selling_price_local: Shopee現地での販売価格 (現地通貨)
        weight_g: 梱包を含めた商品の重量 (g)
        """
        sales_jpy = selling_price_local * self.exchange_rate
        
        # SLS (Shopee Logistics Service) 国際配送料セラー負担額の算出シミュレーション
        if self.target_country == "SG":
            # シンガポールSLS料金テーブル
            if weight_g <= 50:
                shipping_local = 1.20
            elif weight_g <= 250:
                shipping_local = 2.40
            else:
                shipping_local = 2.40 + ((weight_g - 250) // 50 + 1) * 0.20
        elif self.target_country == "TW":
            # 台湾SLS（ファミリーマート/セブンイレブン受取基準）
            shipping_local = 60.0 if weight_g <= 500 else 60.0 + ((weight_g - 500) // 500 + 1) * 30.0
        else:
            # マレーシア等デフォルト
            shipping_local = 4.50 if weight_g <= 250 else 4.50 + ((weight_g - 250) // 250 + 1) * 1.50
            
        shipping_jpy = shipping_local * self.exchange_rate
        
        # 各種販売手数料の合計
        total_fee_rate = self.commission_rate + self.transaction_rate + self.service_rate
        fees_jpy = sales_jpy * total_fee_rate
        
        # 純利益額および利益率
        net_profit_jpy = sales_jpy - cost_jpy - shipping_jpy - fees_jpy
        profit_margin = (net_profit_jpy / sales_jpy) * 100 if sales_jpy > 0 else 0
        
        return {
            "currency": self.currency,
            "sales_jpy": round(sales_jpy),
            "shipping_jpy": round(shipping_jpy),
            "fees_jpy": round(fees_jpy),
            "net_profit_jpy": round(net_profit_jpy),
            "profit_margin": round(profit_margin, 2)
        }

# ==========================================================
# 🧠 2. GEMINI POLICY AUDITOR & TRANSLATOR
# ==========================================================
class GeminiShopeeAgent:
    """Gemini API を使って規約の抵触判断、英語タイトルの最適化、画像プロンプトの設計を行う"""
    def __init__(self, api_key):
        self.api_key = api_key
        self.model_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-09-2025:generateContent"

    def ask_gemini(self, prompt, system_instruction=""):
        if not self.api_key:
            return "⚠️ API KEY MISSING"
            
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "systemInstruction": {"parts": [{"text": system_instruction}]}
        }
        url = f"{self.model_url}?key={self.api_key}"
        
        for delay in [1, 2, 4]:
            try:
                res = requests.post(url, headers=headers, json=payload, timeout=30)
                if res.status_code == 200:
                    return res.json()["candidates"][0]["content"]["parts"][0]["text"]
            except Exception as e:
                time.sleep(delay)
        return "⚠️ Gemini API Error"

    def audit_listing(self, product_name, category, description_jp):
        """Shopeeの厳しい出品規約（航空危険物、バッテリー、液体、ブランド侵害、医薬品表記等）に抵触しないか審査"""
        system_instruction = (
            "You are an expert compliance officer for Shopee Japan Cross-border division. "
            "Evaluate if the item is safe to export to Singapore, Malaysia, and Taiwan. "
            "Analyze battery types, liquid contents, copycat brands, or medical claims. "
            "Respond ONLY in valid, clean JSON with keys: 'rating' (A: Safe, B: Caution, C: Banned), "
            "'issues' (array of strings in Japanese), and 'action_plan' (Japanese recommendation)."
        )
        prompt = f"Product Name: {product_name}\nCategory: {category}\nDescription: {description_jp}"
        response = self.ask_gemini(prompt, system_instruction)
        try:
            cleaned = response.replace("```json", "").replace("```", "").strip()
            return json.loads(cleaned)
        except:
            return {
                "rating": "B",
                "issues": ["AIによる判定規格外ですが、安全のため出品前の自己チェックを推奨します。"],
                "action_plan": "リチウムイオン電池の有無、成分に危険物が無いか目視確認を行ってください。"
            }

    def generate_listing_pack(self, product_name, description_jp):
        """競合セラーに勝つための英語の最適化タイトル、現地向けの商品紹介文、Imagen用のプロンプトを生成"""
        system_instruction = (
            "You are a stellar Shopee marketing specialist. Optimize Japanese e-commerce listings for Southeast Asian buyers. "
            "Produce structured JSON with: 'optimized_title' (Max 80 chars, includes keywords, high CTR), "
            "'localized_description' (English bullet points, specs, shipping info, and key hashtags), "
            "'imagen_image_prompt' (a premium 1:1 professional catalog layout prompt for Google Imagen 4.0 to generate a clean product poster)."
        )
        prompt = f"Name: {product_name}\nDetails: {description_jp}"
        response = self.ask_gemini(prompt, system_instruction)
        try:
            cleaned = response.replace("```json", "").replace("```", "").strip()
            return json.loads(cleaned)
        except:
            return {
                "optimized_title": f"[Direct from Japan] {product_name}",
                "localized_description": f"Authentic Japanese product.\n\nDescription:\n{description_jp}\n\n- 100% Genuine\n- Shipped from Tokyo",
                "imagen_image_prompt": f"A studio lighting photo of {product_name} in clean minimalist layout, soft shadow, 8k resolution, commercial advertising design."
            }

# ==========================================================
# 🎨 3. IMAGEN 4.0 AUTOMATIC AD-BANNER GENERATOR
# ==========================================================
class ShopeeBannerGenerator:
    """GoogleのImagen 4.0モデルを利用し、Canvaでデザインしたかのような超美麗な正方形(1:1)出品画像を自動生成する"""
    def __init__(self, api_key):
        self.api_key = api_key
        self.url = f"https://generativelanguage.googleapis.com/v1beta/models/imagen-4.0-generate-001:predict?key={api_key}"

    def generate_and_save(self, prompt, output_path):
        if not self.api_key:
            print("⚠️ API Key is missing. Imagen Image generation skipped.")
            return False

        print("🎨 Imagen 4.0 エンジン起動中... 1:1 プロ仕様出品画像をレンダリングしています...")
        payload = {
            "instances": [
                {"prompt": f"{prompt}, studio-lit, clean background, premium packaging, highly detailed, centered composition, commercial product design"}
            ],
            "parameters": {
                "sampleCount": 1,
                "aspectRatio": "1:1",
                "outputMimeType": "image/png"
            }
        }
        headers = {"Content-Type": "application/json"}
        try:
            res = requests.post(self.url, headers=headers, json=payload, timeout=60)
            if res.status_code == 200:
                result = res.json()
                base64_data = result["predictions"][0]["bytesBase64Encoded"]
                image_bytes = base64.b64decode(base64_data)
                
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                with open(output_path, "wb") as f:
                    f.write(image_bytes)
                print(f"✨ 広告用アイキャッチ画像を自動保存しました: {output_path}")
                return True
            else:
                print(f"❌ Imagen生成エラー (HTTP {res.status_code}): {res.text}")
                return False
        except Exception as e:
            print(f"❌ Imagen処理プロセス例外: {e}")
            return False

# ==========================================================
# 🏁 4. AUTOMATED PATROL EXECUTION MAIN FLOW
# ==========================================================
def main():
    jst = timezone(timedelta(hours=9))
    print(f"==========================================================")
    print(f"🛍️ Shopee AI Company | 統合自動リサーチ＆高付加価値出品プログラム 起動")
    print(f"🕒 実行時刻: {datetime.now(jst).strftime('%Y-%m-%d %H:%M:%S JST')}")
    print(f"==========================================================")

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        api_key = os.getenv("API_KEY")
        
    if not api_key:
        print("❌ APIキーが環境変数に確認できません。処理を終了します。")
        return

    # エージェントおよびエンジンの初期化
    pricing_engine = ShopeePricingEngine(target_country="SG") # シンガポールをターゲットに選定
    ai_agent = GeminiShopeeAgent(api_key=api_key)
    banner_gen = ShopeeBannerGenerator(api_key=api_key)

    # 🛒 会長指示に基づくAmazon等からの調査・出品商品データ
    patrol_items = [
        {
            "id": "SP-001",
            "name": "【Amazon大人気】極上高保湿ヒアルロン酸美容液 (プレミアムリッチ仕様)",
            "category": "Health & Beauty / Skincare / Serum",
            "cost_jpy": 2400,            # 国内での仕入れ原価 + 送料
            "target_price_local": 45.0,  # 競合日本人セラーのShopee Singaporeでの販売額 (SGD)
            "weight_g": 160,             # 梱包込み重量
            "features_jp": "高純度の国産ヒアルロン酸100%配合。防腐剤フリー、無着色、無香料で敏感肌の方でも安心してお使いいただける超しっとり美容液。"
        },
        {
            "id": "SP-002",
            "name": "次世代リチウムイオン超急速充電式ヘアカッター / 電動バリカン",
            "category": "Health & Beauty / Personal Care / Grooming",
            "cost_jpy": 3500,
            "target_price_local": 65.0,
            "weight_g": 380,
            "features_jp": "コードレスで使用可能なサロン仕様電動バリカン。強力なリチウム電池搭載で最大120分稼働。刃は丸ごと水洗い可能。"
        }
    ]

    processed_listings = []

    for item in patrol_items:
        print(f"\n──────────────────────────────────────────")
        print(f"📦 調査対象: {item['name']}")
        print(f"──────────────────────────────────────────")

        # 1. 精密利益計算
        p_res = pricing_engine.calculate(
            cost_jpy=item["cost_jpy"],
            selling_price_local=item["target_price_local"],
            weight_g=item["weight_g"]
        )
        print(f"💰 利益計算結果 ({p_res['currency']}):")
        print(f"   現地販売価格: {item['target_price_local']} {p_res['currency']} (日本円売上: {p_res['sales_jpy']}円)")
        print(f"   SLS国際配送料: {p_res['shipping_jpy']}円 / 各種販売手数料: {p_res['fees_jpy']}円")
        print(f"   国内仕入原価: {item['cost_jpy']}円")
        print(f"   💵 想定純利益: {p_res['net_profit_jpy']}円 (利益率: {p_res['profit_margin']}%)")

        if p_res["net_profit_jpy"] < 400:
            print("⚠️ [薄利判定] 利益幅が少なく赤字・薄利リスクがあります。価格設定の底上げを検討してください。")

        # 2. 厳格なAIポリシー・規約審査
        print("🛡️ Shopee出品ガイドライン＆輸出入ポリシー審査中...")
        audit = ai_agent.audit_listing(
            product_name=item["name"],
            category=item["category"],
            description_jp=item["features_jp"]
        )
        print(f"   [判定ステータス]: {audit.get('rating')} 判定")
        for issue in audit.get("issues", []):
            print(f"   ❌ ポリシー懸念: {issue}")
        print(f"   💡 指導指示: {audit.get('action_plan')}")

        if audit.get("rating") == "C":
            print("🛑 [規約違反自動ロック] 航空危険物（バッテリー規制）または重大な輸入ポリシーに抵触するため、この商品は出品データベースから除外します。")
            continue

        # 3. 英語リスティング構築
        print("✍️ 現地向けセールスコピー＆英語リスティングの生成...")
        listing = ai_agent.generate_listing_pack(
            product_name=item["name"],
            description_jp=item["features_jp"]
        )
        print(f"   生成タイトル: {listing.get('optimized_title')}")

        # 4. Imagen 4.0 による広告用バナー・アイキャッチ画像の生成
        image_path = f"outputs/images/{item['id']}_main.png"
        image_success = banner_gen.generate_and_save(
            prompt=listing.get("imagen_image_prompt"),
            output_path=image_path
        )

        # 5. 一括出品データ格納
        processed_listings.append({
            "SKU_ID": item["id"],
            "Optimized_Title": listing.get("optimized_title"),
            "English_Description": listing.get("localized_description"),
            "Local_Price": item["target_price_local"],
            "Currency": p_res["currency"],
            "Estimated_Profit_JPY": p_res["net_profit_jpy"],
            "Profit_Margin_Percent": p_res["profit_margin"],
            "Compliance_Rating": audit.get("rating"),
            "Generated_Banner": image_path if image_success else "Not_Generated"
        })

    # 💾 5. Shopee Mass Upload 互換一括出品用CSVテンプレート出力
    if processed_listings:
        csv_path = "outputs/shopee_upload_template.csv"
        os.makedirs(os.path.dirname(csv_path), exist_ok=True)
        
        headers = processed_listings[0].keys()
        with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerows(processed_listings)
            
        print(f"\n💾 [データベース更新完了] 一括アップロード用CSVデータベースファイルを自動生成・上書き保存しました: {csv_path}")
    else:
        print("\n⚠️ 出品適格商品がありませんでした。CSVデータベースの保存はスキップされました。")

    print(f"\n==========================================================")
    print(f"🎉 パトロール業務完了。成果物を格納して安全に終了（退勤）します。")
    print(f"==========================================================")

if __name__ == "__main__":
    main()
