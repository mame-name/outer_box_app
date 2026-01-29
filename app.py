import streamlit as st
import pandas as pd
from calc import process_product_data

st.set_page_config(layout="wide", page_title="小袋サイズ適正化アプリ")

# CSS: サイドバー内の余白詰め、プレースホルダー色調整
st.markdown("""
    <style>
    [data-testid="stSidebar"] .stForm { border: none; padding: 0; }
    [data-testid="stSidebar"] .element-container { margin-bottom: -8px; }
    [data-testid="stSidebar"] label { font-size: 0.85rem !important; }
    .block-container { padding-top: 1.5rem !important; }
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
            def input_row(label, placeholder_text=""):
                c1, c2 = st.columns([1, 2])
                with c1: st.markdown(f"<div style='padding-top:8px;'>{label}</div>", unsafe_allow_html=True)
                with c2:
                    return st.text_input(label, value="", placeholder=placeholder_text, label_visibility="collapsed")

            # 形態（リスト指定）
            type_list = ["小袋", "パウチ", "BIB", "スパウト", "BIB"]
            c1, c2 = st.columns([1, 2])
            with c1: st.markdown("<div style='padding-top:8px;'>形態</div>", unsafe_allow_html=True)
            with c2: 
                i_type = st.selectbox("形態", type_list, label_visibility="collapsed")

            # 重量欄のプレースホルダーを「単位：kg」に変更
            i_weight = input_row("重量（個）", "単位：kg")
            i_pcs = input_row("入数", "単位：個")
            i_sg = input_row("比重", "0.000")
            i_size = input_row("製品サイズ", "巾*長さ")
            
            st.markdown("<div style='padding-top:10px;'></div>", unsafe_allow_html=True)
            # ボタン押下でフィルタリング等を実行
            calc_submit = st.form_submit_button("シミュレーション実行", use_container_width=True)

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
            
            # 基本処理（0埋め、サイズ分解など）
            df_processed = process_product_data(df_raw)

            # --- フィルタリングロジックの実装 ---
            if i_type == "小袋":
                # 小袋なら、形態が「小袋」のものだけを表示
                df_display = df_processed[df_processed["形態"] == "小袋"]
            else:
                # 小袋以外なら、形態が一致し、かつ重量（個）と入数が同じ行だけ表示
                df_display = df_processed[
                    (df_processed["形態"] == i_type) & 
                    (df_processed["重量（個）"] == df_processed["入数"])
                ]

            st.subheader(f"📊 実績データ一覧 ({i_type})")
            st.dataframe(df_display, use_container_width=True, height=800)
            st.success(f"表示件数: {len(df_display)} 件 (全 {len(df_processed)} 件中)")
            
        except Exception as e:
            st.error(f"エラー: {e}")
    else:
        st.warning("左側のサイドバーからファイルをアップロードしてください。")

if __name__ == "__main__":
    main()
