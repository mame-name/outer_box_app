import pandas as pd
import numpy as np

def process_product_data(df):
    """
    指定された10列をベースにデータ清掃と基本計算を行う
    """
    df = df.copy()

    # 1. 型変換（数値列）
    # F:重量, G:入数, J:比重 は数値として扱う
    num_cols = ['重量', '入数', '比重']
    for col in num_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    # 2. 型変換（文字列・クリーニング）
    # P:製品サイズ, AB:シール をクリーニング
    df['製品サイズ'] = df['製品サイズ'].astype(str).str.strip()
    df['シール'] = df['シール'].astype(str).str.strip()
    df['充填機'] = df['充填機'].astype(str).str.strip()

    # 3. サイズ未入力行の除外
    df = df[~df['製品サイズ'].isin(['nan', 'None', ''])]
    
    # 4. 巾・長さの分離 (P列: 製品サイズ "100*150" 等を想定)
    size_split = df["製品サイズ"].str.split('*', n=1, expand=True)
    df["巾"] = pd.to_numeric(size_split[0], errors='coerce')
    df["長さ"] = pd.to_numeric(size_split[1], errors='coerce')

    # 一旦、計算ロジックを入れる前の「綺麗な10列+α」の状態を返します
    return df
