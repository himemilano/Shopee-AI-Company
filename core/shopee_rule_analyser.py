import os
from datetime import datetime, timedelta, timezone
# 🔥 Pydanticエラーを完全回避する、CrewAIネイティブのLLMクラスをインポート
from crewai import Agent, Crew, Process, Task, LLM

# タイムゾーンと日付の設定
jst = timezone(timedelta(hours=9))
current_date = datetime.now(jst).strftime("%Y-%m-%d")

# フォルダパス
RULES_DIR = "outputs/shopee_rules"
RAW_FILE = os.path.join(RULES_DIR, f"{current_date}_shopee_rules_raw.md")
SUMMARY_FILE = os.path.join(RULES_DIR, f"{current_date}_rules_summary.md")

# --- 🛡️ 規約解析専用のAIエージェントのLLM設定 ---
# 429エラーをいなすために最適化されたネイティブLLMモデル
rule_analyser_llm = LLM(
    model="gemini/gemini-2.5-flash",
    temperature=0.2,  # 規約解釈の誤謬を防ぐため、非常に慎重（低め）に設定
)

def load_raw_rules():
    """本日のクローラーが収集した生の規約テキストを読み込む"""
    if os.path.exists(RAW_FILE):
        with open(RAW_FILE, "r", encoding="utf-8") as f:
            return f.read()
    return "本日の生規約データが見つかりませんでした。クローラーが未実行、またはデータが空の可能性があります。"

def run_analysis():
    print("=== ⚖️ Shopee 法務・規約監視部門：AI要約分析を開始 ===")
    
    raw_context = load_raw_rules()
    if "見つかりませんでした" in raw_context:
        print(f"⚠️ {RAW_FILE} が存在しないため、解析をスキップします。")
        return

    # --- 👔 AI規約監査スペシャリスト（エージェント定義） ---
    legal_auditor = Agent(
        role="Shopee 越境EC専任 リーガル・規約監査最高責任者",
        role_description="Shopeeの最新ポリシーを秒速で解読し、越境セラーが受けるペナルティやアカウント停止リスクを徹底的に排除する専門家。",
        goal="収集された生の規約・マニュアルデータから、日本人セラーにとって致命傷になり得る変更点（知財・化粧品規制・配送料・ペナルティ）を抽出し、完璧な要約書を作成する",
        backstory="台湾・シンガポール・マレーシアの商法とShopee規約のすべてを暗記しているリーガルの鬼。難解な中国語や英語の変更点を、実務レベルのアクションプランに昇華させる能力を持つ。",
        verbose=True,
        llm=rule_analyser_llm,
        max_rpm=3,
    )

    # --- 🚀 解析タスクの定義 ---
    analysis_task = Task(
        description=f"""
【本日のShopee公式規約生データ】
{raw_context}

上記の情報源から、日本人セラーが越境EC（台湾・シンガポール・マレーシア）を運営する上で絶対に知っておくべき「規約変更」「新規制」「リスク」を分析し、綺麗で見やすい「Shopee運営法務・重要規約アップデート要約書」を作成してください。

特に関連度の高い以下のテーマを、国（TW, SG, MY）ごとに整理して出力に含めてください：
1. 💄 【化粧品・ヘルスケア】規制、成分表示、必要書類、出品ステップの変更
2. ⚠️ 【知的財産権・ブランド保護】商標侵害警告、ペナルティ強化、警告対応策
3. 🚚 【ロジスティクス】送料、サイズ規定、SLSの改定情報
4. 💰 【手数料・アカウント】決済・取引手数料の改定、各種罰点（ペナルティ）ルール

※変更がない箇所、または新規情報が抽出されなかった場合は「本日の新規更新は検知されませんでした（正常）」と明記してください。
""",
        expected_output="国ごとに整理された最新規約リスクの超詳細要約マークダウンレポート",
        agent=legal_auditor
    )

    # --- チーム結成と実行 ---
    legal_crew = Crew(
        agents=[legal_auditor],
        tasks=[analysis_task],
        process=Process.sequential,
        verbose=True,
        max_rpm=4
    )

    result = legal_crew.kickoff()

    # 💾 要約レポートの保存
    with open(SUMMARY_FILE, "w", encoding="utf-8") as f:
        f.write(str(result))
        
    print(f"💾 [法務部門] 業務完了。要約レポートが格納されました: {SUMMARY_FILE}")

if __name__ == "__main__":
    run_analysis()
