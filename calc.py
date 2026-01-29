import pandas as pd

def process_product_data(df):
    """
    全データを出力し、製品コードのゼロ埋めとサイズ分解を行う
    """
    df = df.copy()

    # 1. 製品コードを6桁の文字列として整形（先頭の0を保持）
    df['製品コード'] = df['製品コード'].apply(
        lambda x: str(int(float(x))).zfill(6) if pd.notna(x) and str(x).replace('.0','').isdigit() else str(x)
    )

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

    # 4. 製品サイズの分解処理
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
