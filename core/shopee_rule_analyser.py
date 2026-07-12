import os
import time
import requests
from datetime import datetime, timedelta, timezone

# タイムゾーンと日付の設定
jst = timezone(timedelta(hours=9))
current_date = datetime.now(jst).strftime("%Y-%m-%d")

# フォルダパス
RULES_DIR = "outputs/shopee_rules"
RAW_FILE = os.path.join(RULES_DIR, f"{current_date}_shopee_rules_raw.md")
SUMMARY_FILE = os.path.join(RULES_DIR, f"{current_date}_rules_summary.md")

def load_raw_rules():
    """本日のクローラーが収集したグローバルの生規約データを読み込む"""
    if os.path.exists(RAW_FILE):
        with open(RAW_FILE, "r", encoding="utf-8") as f:
            return f.read()
    return "グローバルの生規約データが見つかりませんでした。"

def generate_summary_with_gemini(raw_context, api_key):
    """Gemini 2.5 Flash APIを直接叩いて安全に超高速で要約を生成する"""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    
    system_prompt = (
        "あなたはShopeeグローバルEC特化の最高リーガル監査責任者です。越境セラーのアカウント安全性・規約準拠を徹底サポートします。\n"
        "各言語（中国語、英語、タイ語、ベトナム語、ポルトガル語）で書かれたShopeeポリシーを、日本の越境セラー向けの実務アクションプランに日本語でクリアに要約してください。"
    )
    
    prompt = f"""
以下の生データから、日本人セラーが世界のShopee（台湾、シンガポール、マレーシア、フィリピン、タイ、ベトナム、ブラジル）で越境ECを運営する上で絶対に知っておくべき「新規制」「重要変更」「罰則ルール」を分析し、国ごとに整理した「Shopeeグローバル運営法務・重要規約アップデート要約書」を日本語で分かりやすく作成してください。

【本日のShopeeグローバル規約生データ】
{raw_context}

特に重要度の高い以下のテーマにフォーカスを当ててください：
1. 💄 【化粧品・ヘルスケア】各国の薬事規制、成分表示要件、必要ライセンスの変更
2. ⚠️ 【知的財産権（IPR）】商標・意匠権侵害リスク、ブランド転売に対する警告・罰点
3. 🚚 【配送・SLS】各国ロジスティクスの料金体系、重量・サイズ制限変更
4. 💰 【手数料・取引制限】決済手数料の改定、ペナルティシステム（罰点ルール）の変更

※変更が検知されなかった国については、「本日の新規更新は検知されませんでした（正常）」と記載し、ノイズを省いて読みやすくまとめてください。
"""

    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }],
        "systemInstruction": {
            "parts": [{"text": system_prompt}]
        },
        "generationConfig": {
            "temperature": 0.2
        }
    }
    
    headers = {"Content-Type": "application/json"}
    
    # 指数バックオフ（指数リトライ）でAPIの一時的な混雑や429エラーを100%回避する
    for attempt in range(5):
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            if response.status_code == 200:
                result_json = response.json()
                text = result_json["candidates"][0]["content"]["parts"][0]["text"]
                return text
            elif response.status_code == 429:
                sleep_time = 2 ** attempt
                print(f"[API警告] 429エラーを検知。{sleep_time}秒後にリトライします...")
                time.sleep(sleep_time)
            else:
                print(f"[APIエラー] ステータスコード: {response.status_code}, レスポンス: {response.text}")
                break
        except Exception as e:
            print(f"[通信例外エラー] {e}")
            time.sleep(2 ** attempt)
            
    return None

def run_analysis():
    print("=== ⚖️ Shopee 法務・規約監視部門：グローバルAI要約分析を開始 ===")
    
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("❌ エラー: GEMINI_API_KEY が環境変数に設定されていません。")
        return
        
    raw_context = load_raw_rules()
    if "見つかりませんでした" in raw_context or not raw_context.strip():
        print(f"⚠️ {RAW_FILE} が存在しない、または空のため、解析をスキップします。")
        return

    print("🤖 Gemini API への直撃解析を要請中...")
    summary = generate_summary_with_gemini(raw_context, api_key)
    
    if summary:
        with open(SUMMARY_FILE, "w", encoding="utf-8") as f:
            f.write(summary)
        print(f"💾 [法務部門] 業務完了。要約レポートが格納されました: {SUMMARY_FILE}")
    else:
        print("❌ エラー: 要約レポートの生成に失敗しました。")

if __name__ == "__main__":
    run_analysis()

