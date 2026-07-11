import os

def calculate_taiwan_shopee_price(
    amazon_cost_jpy: int,
    target_profit_jpy: int,
    exchange_rate: float,
    is_pre_order: bool = False,   # Trueで御城印帖などの予約商品（決済手数料3%）
    is_large_item: bool = False,  # Trueで譜面台などの大型商品（送料バッファ適用）
    local_buffer_twd: int = 0
) -> int:
    """
    【台湾ストア専用】通常商品・予約商品・大型商品のすべてを網羅した価格改定マスターエンジン。
    会長から提供された実例明細（1,685元 -> 1,186元）の引き算構造を完全に1つのロジックに統合。
    """
    # 1. 送料の自動分岐（通常品は710円、大型商品は実例ベースで1,050円に自動切り替え）
    base_shipping_jpy = 1050 if is_large_item else 710
    
    # 2. 実例明細から抽出した各種プラットフォーム手数料率
    rate_commission = 0.1075  # 成交手續費 (約10.75%)
    rate_service = 0.0605     # 其他服務費 (約6.05% ※免運・CCB参加費)
    rate_payoneer = 0.02      # Payoneer為替振込手数料 (2.0%)
    
    # 3. 予約商品か通常商品かで「決済手数料」を自動分岐
    rate_transaction = 0.03 if is_pre_order else 0.025  # 金流與系統處理費 (3.0% or 2.5%)
    
    # 4. 蝦皮（Shopee）内での総手数料率の合算
    total_shopee_rates = rate_commission + rate_service + rate_transaction
    
    # 5. 必要総コスト（仕入れ原価 ＋ 日本国内/国際送料 ＋ 利益）
    total_cost_jpy = amazon_cost_jpy + base_shipping_jpy + target_profit_jpy
    
    # 6. 数理逆算ロジックによる現地販売価格（TWD）の算出
    # 手取り(円) = 販売価格(TWD) * 為替 * (1 - Shopee総手数料) * (1 - Payoneer手数料)
    denominator = exchange_rate * (1.0 - total_shopee_rates) * (1.0 - rate_payoneer)
    
    if denominator <= 0:
        raise ValueError("手数料の設定、または為替レートが不正です。")
        
    shopee_price_twd = (total_cost_jpy / denominator) + local_buffer_twd
    
    # 台湾ドルの仕様に合わせて四捨五入して整数（NT$）にする
    return round(shopee_price_twd)


# --- 以下、AI社員による動作テスト用コード ---
if __name__ == "__main__":
    print("=== Shopee-AI-Company: 台湾ストア 統合エンジン起動测试 ===")
    
    # テスト条件
    COST = 3500      # 仕入れ原価
    PROFIT = 1500    # 目標粗利
    FX_RATE = 4.6    # 為替レート
    
    # パターン①：通常のガジェットや文房具など（通常決済2.5% + 通常送料710円）
    price_1 = calculate_taiwan_shopee_price(COST, PROFIT, FX_RATE, is_pre_order=False, is_large_item=False)
    print(f"① 通常商品（通常送料・通常決済）: NT$ {price_1}")
    
    # パターン②：御城印帖など（予約受注決済3.0% + 通常送料710円）
    price_2 = calculate_taiwan_shopee_price(COST, PROFIT, FX_RATE, is_pre_order=True, is_large_item=False)
    print(f"② 予約受注（決済3%・通常送料）  : NT$ {price_2}")
    
    # パターン③：譜面台など（通常決済2.5% + 大型送料1,050円自動上乗せ）
    price_3 = calculate_taiwan_shopee_price(COST, PROFIT, FX_RATE, is_pre_order=False, is_large_item=True)
    print(f"③ 大型商品（通常決済・大型送料）  : NT$ {price_3}")
    
    print("=========================================================")
