import pandas as pd

def process_product_data(df):
    df = df.copy()

    # 1. 製品コードを6桁のゼロ埋め文字列に整形
    def format_code(x):
        if pd.isna(x) or x == "": return ""
        try:
            # 数値として認識できる場合は整数化してから6桁埋め
            return str(int(float(x))).zfill(6)
        except:
            return str(x).zfill(6)

    df['製品コード'] = df['製品コード'].apply(format_code)

    # 2. 数値変換
    num_cols = ['重量（個）', '入数', '重量（箱）', '比重']
    for col in num_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    # 3. 文字列クリーニング
    str_cols = ['製品名', '荷姿', '形態', '外箱', '製品サイズ']
    for col in str_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace('nan', '').str.strip()

    # 4. 製品サイズの分解
    df["巾"] = None
    df["長さ"] = None

    def split_size(size_str):
        if '*' in size_str:
            parts = size_str.split('*')
            try:
                return float(parts[0]), float(parts[1])
            except:
                return None, None
        return None, None

    df[['巾', '長さ']] = df.apply(
        lambda row: pd.Series(split_size(row['製品サイズ'])), axis=1
    )
    
    return df
