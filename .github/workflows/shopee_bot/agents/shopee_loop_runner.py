import os
import sys
import time
import subprocess
from datetime import datetime, timedelta, timezone

# 日本時間設定
jst = timezone(timedelta(hours=9))

# 🛍️ Shopeeパトロール・分析・最適化スクリプト
SCRIPTS_TO_RUN = [
    "shopee_bot/agents/price_monitor.py",           # 1. 競合商品価格・在庫の24時間監視
    "shopee_bot/agents/listings_analyzer.py",       # 2. ライバルセラーの最新出品・動向分析
    "shopee_bot/agents/auto_translator.py",         # 3. 英語・現地語の商品説明AI翻訳・要約
    "shopee_bot/agents/compliance_audit.py"         # 4. プラットフォーム利用規約・抵触チェック
]

# APIリミットセーフガード (1分間の最大リクエスト数を12回に自主規制してエラーを回避)
MAX_REQUESTS_PER_MINUTE = 12
REQUEST_INTERVAL = 60 / MAX_REQUESTS_PER_MINUTE # 5秒インターバル

def run_script_safely(script_path):
    if not os.path.exists(script_path):
        return False
        
    current_time = datetime.now(jst).strftime("%H:%M:%S")
    print(f"\n[🔄 Shopeeループ実行] {current_time} - {script_path} を開始...")
    
    start_time = time.time()
    try:
        result = subprocess.run([sys.executable, script_path], capture_output=True, text=True, timeout=300)
        
        print(result.stdout)
        if result.stderr:
            print(f"❌ エラー出力:\n{result.stderr}")
            
        elapsed = time.time() - start_time
        print(f"⏱️ 完了 (処理時間: {elapsed:.1f}秒)")
        
        time.sleep(REQUEST_INTERVAL)
        return True
    except subprocess.TimeoutExpired:
        print(f"⚠️ タイムアウト(5分超過により強制打ち切り): {script_path}")
        return False
    except Exception as e:
        print(f"❌ 実行エラー: {e}")
        return False

def main():
    print("==========================================================")
    print("🔥 Shopee AI Agent 自律常時限界ループランナー 🔥")
    print("==========================================================")
    
    loop_start_time = time.time()
    max_loop_duration = 5 * 60 * 60 + 40 * 60 # 5時間40分間、常時コンテナ内でループ監視
    
    run_count = 0
    while True:
        elapsed_total = time.time() - loop_start_time
        if elapsed_total > max_loop_duration:
            print("⏳ コンテナ上限時間に達したため、次の巡回シフトへバトンを繋ぎます。")
            break
            
        run_count += 1
        print(f"\n--- 🛍️ 第 {run_count} 回目のShopee全ストア自律パトロールループ ---")
        
        for script in SCRIPTS_TO_RUN:
            run_script_safely(script)
            
        # 次の巡回サイクルまで15秒呼吸を置く
        time.sleep(15)
        
        # 監視ログ、価格改定案、翻訳された成果物データをGitHubへ自動同期
        try:
            subprocess.run(["git", "config", "--local", "user.email", "action@github.com"], capture_output=True)
            subprocess.run(["git", "config", "--local", "user.name", "GitHub Action"], capture_output=True)
            subprocess.run(["git", "add", "."], capture_output=True)
            
            status_res = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
            if status_res.stdout.strip():
                print("📦 監視データ、価格分析シートの更新を検知！自動保存します...")
                subprocess.run(["git", "commit", "-m", "🛍️ [Shopee-Autonomy] 24時間監視から得た市場価格変動データを自動保存しました"], capture_output=True)
                subprocess.run(["git", "push"], capture_output=True)
        except Exception as e:
            print(f"⚠️ 自動コミット例外: {e}")

if __name__ == "__main__":
    main()

