import os

# 本来の実行ファイルである shopee_loop_runner.py を正しいパスで呼び出します。
# フォルダ構成に合わせて自動判定して確実に起動させます。
if os.path.exists("shopee_bot/agents/shopee_loop_runner.py"):
    os.system("python shopee_bot/agents/shopee_loop_runner.py")
elif os.path.exists("shopee_loop_runner.py"):
    os.system("python shopee_loop_runner.py")
else:
    print("⚠️ 実行ファイルが見つかりません。")
