import streamlit as st
import pandas as pd
from calc import process_product_data

st.set_page_config(layout="wide", page_title="小袋サイズ適正化アプリ")

# UIスタイルの調整
st.markdown("""
    <style>
    .stForm { border: 1px solid #ddd; padding: 20px; border-radius: 10px; background-color: #f9f9f9; }
    </style>
    """, unsafe_allow_html=True)

def main():
    st.markdown("<h2 style='text-align: center;'>🤖 小袋サイズ適正化シミュレーター</h2>", unsafe_allow_html=True)
    st.divider()

    # 画面分割 (左1: 右2)
    col_left, col_right = st.columns([1, 2], gap="large")

    # --- 左画面：シミュレーション入力エリア ---
    with col_left:
        st.subheader("📝 条件設定")
        
        with st.form("sim_form"):
            i_nosugata = st.selectbox("荷姿", ["液体", "粉体", "その他"])
            i_weight = st.number_input("重量（個） (g)", value=0.0, step=0.1)
            i_pcs = st.number_input("入数", value=0, step=1)
            i_sg = st.number_input("比重", value=0.000, step=0.001, format="%.3f")
            i_size = st.text_input("製品サイズ (巾*長さ)", placeholder="100*150")
            
            st.markdown("---")
            uploaded_file = st.file_uploader("実績XLSM読込 (製品一覧シート)", type=['xlsm'])
            
            submit = st.form_submit_button("データを読み込む", use_container_width=True)

    # --- 右画面：実績データ表示エリア ---
    with col_right:
        st.subheader("📊 実績データ一覧")
        
        if uploaded_file:
            try:
                # A:0, B:1, C:2, D:3, F:5, G:6, I:8, J:9, P:15, AA:26
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
                
                # calc.pyで処理（全件保持）
                df_final = process_product_data(df_raw)
                
                # テーブル表示
                st.dataframe(df_final, use_container_width=True, height=600)
                st.success(f"読み込み完了: {len(df_final)} 件の全データを表示中")
                
            except Exception as e:
                st.error(f"読み込みエラー: {e}")
        else:
            st.info("左側のフォームから実績ファイルをアップロードしてください。")

if __name__ == "__main__":
    main()
