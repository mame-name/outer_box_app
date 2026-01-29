import streamlit as st
import pandas as pd
from calc import process_product_data

st.set_page_config(layout="wide", page_title="小袋サイズ適正化アプリ")

# CSS: サイドバー内の余白詰め、入力欄のプレースホルダー色調整、スピンボタン排除
st.markdown("""
    <style>
    [data-testid="stSidebar"] .stForm { border: none; padding: 0; }
    [data-testid="stSidebar"] .element-container { margin-bottom: -8px; }
    [data-testid="stSidebar"] label { font-size: 0.85rem !important; }
    .block-container { padding-top: 1.5rem !important; }
    
    /* プレースホルダーの文字色を少し見やすく */
    ::placeholder { color: #aaaaaa !important; }
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
            def input_row(label, placeholder_text=""):
                c1, c2 = st.columns([1, 2])
                with c1: st.markdown(f"<div style='padding-top:8px;'>{label}</div>", unsafe_allow_html=True)
                with c2:
                    # value="" にすることで初期値を空にし、placeholderを表示
                    return st.text_input(label, value="", placeholder=placeholder_text, label_visibility="collapsed")

            # 荷姿（セレクトボックス）
            c1, c2 = st.columns([1, 2])
            with c1: st.markdown("<div style='padding-top:8px;'>荷姿</div>", unsafe_allow_html=True)
            with c2: i_nosugata = st.selectbox("荷姿", ["液体", "粉体", "その他"], label_visibility="collapsed")

            # 各入力欄（初期値なし、背景にヒントを表示）
            i_weight = input_row("重量（個）", "単位：g")
            i_pcs = input_row("入数", "単位：個")
            i_sg = input_row("比重", "0.000")
            i_size = input_row("製品サイズ", "巾*長さ")
            
            st.markdown("<div style='padding-top:10px;'></div>", unsafe_allow_html=True)
            calc_submit = st.form_submit_button("シミュレーション実行", use_container_width=True)

    # --- メイン画面：スクロールエリア ---
    st.markdown("<h1 style='text-align: center;'>Intelligent 熊谷さん</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: gray;'>🤖 小袋サイズ確認シミュレーター</p>", unsafe_allow_html=True)
    st.divider()

    if uploaded_file:
        try:
            # A=0, B=1, C=2, D=3, F=5, G=6, I=8, J=9, P=15, AA=26
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
            # 右画面の表（メイン画面と一緒にスクロール）
            st.dataframe(df_final, use_container_width=True, height=800)
            st.success(f"読み込み完了: {len(df_final)} 件")
            
        except Exception as e:
            st.error(f"エラー: {e}")
    else:
        st.warning("左側のサイドバーからファイルをアップロードしてください。")

if __name__ == "__main__":
    main()
