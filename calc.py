import pandas as pd

def process_product_data(df):
    """
    指定10列のデータクリーニングを行う
    """
    df = df.copy()

    # 文字列のクリーニング（P列:製品サイズ, D列:充填機, C列:形態, AB列:シール）
    str_cols = ['製品サイズ', '充填機', '形態', 'シール', '名前', '製品コード', '顧客名']
    for col in str_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()

    # 数値の変換（F列:重量, G列:入数, J列:比重）
    num_cols = ['重量', '入数', '比重']
    for col in num_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    # 必須列「製品サイズ」が空の行を除外
    df = df[~df['製品サイズ'].isin(['nan', 'None', '', 'nan*nan'])]
    
    return df
