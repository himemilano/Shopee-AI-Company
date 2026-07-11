import os

def calculate_taiwan_shopee_price(amazon_cost_jpy, shipping_jpy, target_profit_jpy, exchange_rate, commission_rate, transaction_rate, service_rate, local_buffer_twd=0):
    """
    仕様書(docs/business_logic.md)に定義された数式に基づき、台湾Shopeeでの適正販売価格(NT$)を計算する。
    M&A時のAPIキー差し替えを想定し、各種手数料率は引数（環境変数）から読み込む。
    """
    # 総コスト（円）の算出
    total_cost_jpy = amazon_cost_jpy + shipping_jpy + target_profit_jpy
    
    # 手数料合計率の算出
    total_fees_rate = commission_rate + transaction_rate + service_rate
    
    if total_fees_rate >= 1.0:
        raise ValueError("手数料の合計が100%を超えています。設定を確認してください。")
        
    # 公式の適用
    # 販売価格 = コスト / [為替レート * (1 - 手数料率)] + バッファ
    denominator = exchange_rate * (1.0 - total_fees_rate)
    
    if denominator <= 0:
        return None
        
    shopee_price_twd = (total_cost_jpy / denominator) + local_buffer_twd
    
    # 台湾ドルは四捨五入して整数にするのが一般的
    return round(shopee_price_twd)

# 将来の買い手企業がAPI環境変数を書き換えるだけで動くように、OSの環境変数から取得する構造にする
if __name__ == "__main__":
    # テスト用模擬データ（今回のサンリオ鉛筆のケースを想定）
    # 実際は各APIから自動取得
    AMAZON_COST = 3500  # 例: 仕入れ原価
    SHIPPING = 800     # Paid SPS等の国内・国際合算目安
    PROFIT = 1500      # 目標利益
    
    # 環境変数（M&A譲渡対象）
    EXCHANGE_RATE = 4.6  # 1 TWD = 4.6 円想定
    COMMISSION = float(os.getenv("SHOPEE_TW_COMMISSION_RATE", 0.05)) # 5%
    TRANSACTION = float(os.getenv("SHOPEE_TW_TRANSACTION_RATE", 0.02)) # 2%
    SERVICE = float(os.getenv("SHOPEE_TW_SERVICE_RATE", 0.03)) # 3%
    
    final_price = calculate_taiwan_shopee_price(
        AMAZON_COST, SHIPPING, PROFIT, EXCHANGE_RATE, COMMISSION, TRANSACTION, SERVICE
    )
    print(f"【AIプライシング結果】台湾ストア提示価格: NT$ {final_price}")
