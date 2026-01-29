import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from calc import process_product_data

# --- 以前のコードの定数を踏襲 ---
LINE_WIDTH = 1
MARKER_SIZE = 6
SIM_MARKER_SIZE = 15

st.set_page_config(layout="wide", page_title="小袋サイズ適正化アプリ")

# 左右独立スクロールを実現するCSS
st.markdown("""
    <style>
    [data-testid="stAppViewContainer"] { overflow: hidden; }
    .scroll-container { height: 85vh; overflow-y: auto; padding-right: 10px; }
    .stForm { border: 1px solid #ddd; padding: 20px; border-radius: 10px; background-color: #f9f9f9; }
    h1, h2 { text-align: center; }
    </style>
    """, unsafe_allow_html=True)

def main():
    st.markdown("<h1>Intelligent 熊谷さん<br>🤖 🤖 🤖 小袋サイズ確認 🤖 🤖 🤖</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: gray;'>まるで熊谷さんが考えたような精度でサイズを確認してくれるアプリです</p>", unsafe_allow_html=True)
    st.divider()

    # 画面分割 (左1: 右2)
    col_left, col_right = st.columns([1, 2], gap="large")

    # --- 左画面：操作・入力エリア ---
    with col_left:
        st.markdown('<div class="scroll-container">', unsafe_allow_html=True)
        
        # 1. ファイル読込（自動処理）
        st.subheader("📁 実績データ読込")
        uploaded_file = st.file_uploader("実績XLSMを選択", type=['xlsm'], label_visibility="collapsed")
        
        st.markdown("---")
        
        # 2. シミュレーション入力欄
        st.subheader("📝 条件設定")
        with st.form("sim_form"):
            i_nosugata = st.selectbox("荷姿", ["液体", "粉体", "その他"])
            i_weight = st.number_input("重量（個） (g)", value=0.0, step=0.1)
            i_pcs = st.number_input("入数", value=0, step=1)
            i_sg = st.number_input("比重", value=0.000, step=0.001, format="%.3f")
            i_size = st.text_input("製品サイズ (巾*長さ)", placeholder="100*150")
            
            calc_submit = st.form_submit_button("シミュレーション実行", use_container_width=True)
            
        st.markdown('</div>', unsafe_allow_html=True)

    # --- 右画面：実績データ表示エリア ---
    with col_right:
        st.markdown('<div class="scroll-container">', unsafe_allow_html=True)
        st.subheader("📊 実績データ一覧")
        
        if uploaded_file:
            try:
                # 指定インデックス（A=0, B=1, C=2, D=3, F=5, G=6, I=8, J=9, P=15, AA=26）
                target_indices = [0, 1, 2, 3, 5, 6, 8, 9, 15, 26]
                col_names = [
                    "製品コード", "製品名", "荷姿", "形態", 
                    "重量（個）", "入数", "重量（箱）", "比重", 
                    "外箱", "製品サイズ"
                ]
                
                # 自動読み込み
                df_raw = pd.read_excel(
                    uploaded_file, 
                    sheet_name="製品一覧", 
                    usecols=target_indices, 
                    names=col_names, 
                    skiprows=5, 
                    engine='openpyxl'
                )
                
                df_final = process_product_data(df_raw)
                
                # テーブル表示 (独立スクロール内)
                st.dataframe(df_final, use_container_width=True, height=800)
                st.success(f"自動読込完了: {len(df_final)} 件")
                
            except Exception as e:
                st.error(f"エラー: {e}")
        else:
            st.warning("左側のエリアからファイルをアップロードしてください。")
            
        st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
