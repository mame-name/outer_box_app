import pandas as pd

def process_product_data(df):
    df = df.copy()

    # 1. 製品コードを6桁ゼロ埋め
    def format_code(x):
        if pd.isna(x) or x == "": return ""
        try:
            return str(int(float(x))).zfill(6)
        except:
            return str(x).zfill(6)
    df['製品コード'] = df['製品コード'].apply(format_code)

    # 2. 数値変換
    num_cols = ['重量（個）', '入数', '重量（箱）', '比重']
    for col in num_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    # 3. 体積列の作成 (重量 / 比重 * 入数)
    # 比重が0だとエラーになるため条件分岐
    def calc_volume(row):
        try:
            w = float(row['重量（個）'])
            sg = float(row['比重'])
            n = float(row['入数'])
            if sg > 0:
                return w / sg * n
            return 0
        except:
            return 0
    df['体積'] = df.apply(calc_volume, axis=1)

    # 4. 文字列クリーニング
    str_cols = ['製品名', '荷姿', '形態', '外箱', '製品サイズ']
    for col in str_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace('nan', '').str.strip()

    # 5. 製品サイズの分解 (巾*長さ)
    def split_size(size_str):
        if '*' in size_str:
            parts = size_str.split('*')
            try:
                return float(parts[0]), float(parts[1])
            except:
                return None, None
        return None, None

    df[['巾', '長さ']] = df.apply(lambda row: pd.Series(split_size(row['製品サイズ'])), axis=1)
    
    return df
