import pandas as pd

def process_product_data(df):
    """
    指定された列のクリーニングと基本加工
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
            df[col] = df[col].astype(str).str.strip()

    # 3. 製品サイズの分離 (巾*長さ)
    # AA列(製品サイズ)が "100*150" のような形式であることを想定
    size_split = df["製品サイズ"].str.split('*', n=1, expand=True)
    df["巾"] = pd.to_numeric(size_split[0], errors='coerce')
    df["長さ"] = pd.to_numeric(size_split[1], errors='coerce')

    # 無効なサイズの行を除外
    df = df[~df['製品サイズ'].isin(['nan', 'None', '', 'nan*nan'])]
    
    return df
