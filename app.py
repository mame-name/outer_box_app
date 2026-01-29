import streamlit as st
import pandas as pd
from calc import process_product_data

st.set_page_config(layout="wide", page_title="小袋サイズ適正化アプリ")

# UIスタイルの調整
st.markdown("""
    <style>
    .stForm { border: 1px solid #ddd; padding: 20px; border-radius: 10px; background-color: #f9f9f9; }
    [data-testid="stFileUploader"] { padding-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

def main():
    st.markdown("<h2 style='text-align: center;'>🤖 小袋サイズ適正化シミュレーター</h2>", unsafe_allow_html=True)
    st.divider()

    # 画面分割 (左1: 右2)
    col_left, col_right = st.columns([1, 2], gap="large")

    # --- 左画面：操作エリア ---
    with col_left:
        # 上部：ファイル取り込み（自動処理）
        st.subheader("📁 実績データ読込")
        uploaded_file = st.file_uploader("実績XLSMを選択してください", type=['xlsm'], label_visibility="collapsed")
        
        st.markdown("---")
        
        # 下部：入力フォーム
        st.subheader("📝 シミュレーション条件")
        with st.form("sim_form"):
            i_nosugata = st.selectbox("荷姿", ["液体", "粉体", "その他"])
            i_weight = st.number_input("重量（個） (g)", value=0.0, step=0.1)
            i_pcs = st.number_input("入数", value=0, step=1)
            i_sg = st.number_input("比重", value=0.000, step=0.001, format="%.3f")
            i_size = st.text_input("製品サイズ (巾*長さ)", placeholder="100*150")
            
            # フォーム内のボタンはシミュレーション計算用
            calc_submit = st.form_submit_button("シミュレーション実行", use_container_width=True)

    # --- 右画面：実績データ表示エリア ---
    with col_right:
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
                
                # 最初のような直接的な読み込み
                df_raw = pd.read_excel(
                    uploaded_file, 
                    sheet_name="製品一覧", 
                    usecols=target_indices, 
                    names=col_names, 
                    skiprows=5, 
                    engine='openpyxl'
                )
                
                # 処理実行
                df_final = process_product_data(df_raw)
                
                # テーブル表示（製品コードが文字列として正しく並ぶよう設定）
                st.dataframe(df_final, use_container_width=True, height=700)
                st.success(f"自動読込完了: {len(df_final)} 件")
                
            except Exception as e:
                st.error(f"読み込み中にエラーが発生しました: {e}")
        else:
            st.info("左側のエリアからファイルをアップロードしてください。")

if __name__ == "__main__":
    main()
