import pandas as pd

def process_product_data(df):
    """
    全データを出力し、製品サイズが有効な場合のみ巾・長さを抽出する
    """
    df = df.copy()

    # 1. 数値変換 (重量(個), 入数, 重量(箱), 比重)
    num_cols = ['重量（個）', '入数', '重量（箱）', '比重']
    for col in num_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    # 2. 文字列クリーニング
    str_cols = ['製品コード', '製品名', '荷姿', '形態', '外箱', '製品サイズ']
    for col in str_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace('nan', '').str.strip()

    # 3. 製品サイズの処理 (絞り込みはせず、可能なものだけ分解)
    # デフォルト値を設定
    df["巾"] = None
    df["長さ"] = None

    def split_size(size_str):
        if '*' in size_str:
            parts = size_str.split('*')
            try:
                # 数値として抽出を試みる
                w = float(parts[0])
                l = float(parts[1])
                return w, l
            except:
                return None, None
        return None, None

    # 分解処理を適用
    df[['巾', '長さ']] = df.apply(
        lambda row: pd.Series(split_size(row['製品サイズ'])), axis=1
    )
    
    return df
