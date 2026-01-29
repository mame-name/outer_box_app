import pandas as pd

def process_product_data(df):
    df = df.copy()

    # 1. 製品コード 000000 形式（文字列として扱う）
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

    # 3. 単一体積（1個あたり）の計算: 重量 / 比重
    def calc_unit_volume(row):
        try:
            w = float(row['重量（個）'])
            sg = float(row['比重'])
            if sg > 0:
                return w / sg
            return 0
        except:
            return 0
    df['単一体積'] = df.apply(calc_unit_volume, axis=1)

    # 4. 文字列クリーニング
    str_cols = ['製品名', '荷姿', '形態', '外箱', '製品サイズ']
    for col in str_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace('nan', '').str.strip()

    return df
