import streamlit as st
import pandas as pd
from calc import process_product_data

st.set_page_config(layout="wide", page_title="小袋サイズ適正化アプリ")

# UIスタイルの調整
st.markdown("""
    <style>
    .stForm { border: 1px solid #ddd; padding: 20px; border-radius: 10px; background-color: #f9f9f9; }
    div[data-testid="stExpander"] { border: none !important; }
    </style>
    """, unsafe_allow_html=True)

def main():
    st.markdown("<h2 style='text-align: center;'>🤖 小袋サイズ適正化シミュレーター</h2>", unsafe_allow_html=True)
    st.divider()

    # 2画面分割 (1:2の比率)
    col_left, col_right = st.columns([1, 2], gap="large")

    # --- 左画面：シミュレーション入力エリア ---
    with col_left:
        st.subheader("📝 シミュレーション条件")
        
        with st.form("sim_form"):
            # 入力項目：形態、重量、入数、比重、製品サイズ
            i_form = st.selectbox("形態", ["液体", "粉体", "その他"])
            i_weight = st.number_input("重量 (g)", value=0.0, step=0.1)
            i_pcs = st.number_input("入数", value=0, step=1)
            i_sg = st.number_input("比重", value=0.000, step=0.001, format="%.3f")
            i_size = st.text_input("製品サイズ (巾*長さ)", placeholder="100*150")
            
            st.markdown("---")
            uploaded_file = st.file_uploader("実績XLSM読込", type=['xlsm'])
            
            submit = st.form_submit_button("データ更新・計算", use_container_width=True)

        if submit:
            st.info("シミュレーション値を受け付けました（※計算ロジック未実装）")

    # --- 右画面：実績データ表示エリア ---
    with col_right:
        st.subheader("📊 実績データ一覧")
        
        if uploaded_file:
            try:
                # A=0, B=1, C=2, D=3, F=5, G=6, I=8, J=9, P=15, AB=27
                target_indices = [0, 1, 2, 3, 5, 6, 8, 9, 15, 27]
                col_names = ["製品コード", "名前", "形態", "充填機", "重量", "入数", "顧客名", "比重", "製品サイズ", "シール"]
                
                df_raw = pd.read_excel(
                    uploaded_file, 
                    sheet_name="製品一覧", 
                    usecols=target_indices, 
                    names=col_names, 
                    skiprows=5, 
                    engine='openpyxl'
                )
                
                # calc.py でデータ処理
                df_final = process_product_data(df_raw)
                
                # テーブル表示
                st.dataframe(df_final, use_container_width=True, height=600)
                st.success(f"読み込み完了: {len(df_final)} 件")
                
            except Exception as e:
                st.error(f"読み込みエラー: {e}\nシート名が「製品一覧」であることを確認してください。")
        else:
            st.info("左側のフォームから実績ファイルをアップロードしてください。")

if __name__ == "__main__":main()
