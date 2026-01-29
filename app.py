import streamlit as st
import pandas as pd
from calc import process_product_data

st.set_page_config(layout="wide", page_title="小袋サイズ適正化アプリ")

# 以前のコードのスタイルを踏襲（サイドバー内の余白詰め）
st.markdown("""
    <style>
    [data-testid="stSidebar"] .stForm { border: none; padding: 0; }
    [data-testid="stSidebar"] .element-container { margin-bottom: -5px; }
    [data-testid="stSidebar"] label { font-size: 0.85rem !important; }
    .block-container { padding-top: 2rem !important; }
    </style>
    """, unsafe_allow_html=True)

def main():
    # --- サイドバー：固定（ファイル読込 & 入力欄） ---
    with st.sidebar:
        st.subheader("📁 実績データ読込")
        uploaded_file = st.file_uploader("実績XLSMを選択", type=['xlsm'], label_visibility="collapsed")
        
        st.divider()
        
        st.subheader("📝 条件設定")
        with st.form("sim_form"):
            # 入力欄のレイアウト（初期コードのスタイル）
            def input_row(label, is_number=False, val=0.0):
                c1, c2 = st.columns([1, 2])
                with c1: st.markdown(f"<div style='padding-top:8px;'>{label}</div>", unsafe_allow_html=True)
                with c2:
                    if is_number: return st.number_input(label, value=val, step=0.1, label_visibility="collapsed")
                    else: return st.text_input(label, label_visibility="collapsed")

            i_nosugata = st.selectbox("荷姿", ["液体", "粉体", "その他"])
            i_weight = input_row("重量（個）", is_number=True, val=0.0)
            i_pcs = input_row("入数", is_number=True, val=0.0) # 入数も一旦floatで対応
            i_sg = input_row("比重", is_number=True, val=0.000)
            i_size = input_row("製品サイズ") # 巾*長さ
            
            st.form_submit_button("シミュレーション実行", use_container_width=True)

    # --- メイン画面：スクロール（タイトル & 表） ---
    st.markdown("<h1 style='text-align: center;'>Intelligent 熊谷さん</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: gray;'>🤖 小袋サイズ確認シミュレーター</p>", unsafe_allow_html=True)
    st.divider()

    if uploaded_file:
        try:
            # 指定インデックス（A=0, B=1, C=2, D=3, F=5, G=6, I=8, J=9, P=15, AA=26）
            target_indices = [0, 1, 2, 3, 5, 6, 8, 9, 15, 26]
            col_names = [
                "製品コード", "製品名", "荷姿", "形態", 
                "重量（個）", "入数", "重量（箱）", "比重", 
                "外箱", "製品サイズ"
            ]
            
            df_raw = pd.read_excel(
                uploaded_file, 
                sheet_name="製品一覧", 
                usecols=target_indices, 
                names=col_names, 
                skiprows=5, 
                engine='openpyxl'
            )
            
            df_final = process_product_data(df_raw)
            
            st.subheader("📊 実績データ一覧")
            # heightを指定しない、あるいは十分大きくすることでメイン画面でスクロール
            st.dataframe(df_final, use_container_width=True)
            st.success(f"読み込み完了: {len(df_final)} 件")
            
        except Exception as e:
            st.error(f"エラー: {e}")
    else:
        st.warning("左側のサイドバーからファイルをアップロードしてください。")

if __name__ == "__main__":
    main()
