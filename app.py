import streamlit as st
import pandas as pd
from calc import process_product_data

st.set_page_config(layout="wide", page_title="小袋サイズ適正化アプリ")

# CSS: サイドバー内の余白詰めとデザイン調整
st.markdown("""
    <style>
    [data-testid="stSidebar"] .stForm { border: none; padding: 0; }
    [data-testid="stSidebar"] .element-container { margin-bottom: -8px; }
    [data-testid="stSidebar"] label { font-size: 0.85rem !important; }
    .block-container { padding-top: 1.5rem !important; }
    /* 数値入力のインクリメントボタンを隠す（Chrome等） */
    input[type=number]::-webkit-inner-spin-button, 
    input[type=number]::-webkit-outer-spin-button { 
        -webkit-appearance: none; margin: 0; 
    }
    input[type=number] { -moz-appearance: textfield; }
    </style>
    """, unsafe_allow_html=True)

def main():
    # --- サイドバー：固定エリア ---
    with st.sidebar:
        st.subheader("📁 実績データ読込")
        uploaded_file = st.file_uploader("実績XLSMを選択", type=['xlsm'], label_visibility="collapsed")
        
        st.divider()
        
        st.subheader("📝 条件設定")
        with st.form("sim_form"):
            # レイアウト用ヘルパー関数
            def input_row(label, is_number=False, val="0"):
                c1, c2 = st.columns([1, 2])
                with c1: st.markdown(f"<div style='padding-top:8px;'>{label}</div>", unsafe_allow_html=True)
                with c2:
                    if is_number:
                        # text_inputにすることで +/- ボタンを強制排除
                        return st.text_input(label, value=str(val), label_visibility="collapsed")
                    else:
                        return st.text_input(label, label_visibility="collapsed")

            # 荷姿も横並びに修正
            c1, c2 = st.columns([1, 2])
            with c1: st.markdown("<div style='padding-top:8px;'>荷姿</div>", unsafe_allow_html=True)
            with c2: i_nosugata = st.selectbox("荷姿", ["液体", "粉体", "その他"], label_visibility="collapsed")

            i_weight = input_row("重量（個）", is_number=True, val="0.0")
            i_pcs = input_row("入数", is_number=True, val="0")
            i_sg = input_row("比重", is_number=True, val="0.000")
            i_size = input_row("製品サイズ") # 巾*長さ
            
            st.markdown("<div style='padding-top:10px;'></div>", unsafe_allow_html=True)
            st.form_submit_button("シミュレーション実行", use_container_width=True)

    # --- メイン画面：スクロールエリア ---
    st.markdown("<h1 style='text-align: center;'>Intelligent 熊谷さん</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: gray;'>🤖 小袋サイズ確認シミュレーター</p>", unsafe_allow_html=True)
    st.divider()

    if uploaded_file:
        try:
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
            st.dataframe(df_final, use_container_width=True, height=800)
            st.success(f"読み込み完了: {len(df_final)} 件")
            
        except Exception as e:
            st.error(f"エラー: {e}")
    else:
        st.warning("左側のサイドバーからファイルをアップロードしてください。")

if __name__ == "__main__":
    main()
