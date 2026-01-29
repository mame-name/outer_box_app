import streamlit as st
import pandas as pd
import plotly.express as px
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

            type_list = ["小袋", "パウチ", "BIB", "スパウト"]
            c1, c2 = st.columns([1, 2])
            with c1: st.markdown("<div style='padding-top:8px;'>形態</div>", unsafe_allow_html=True)
            with c2: 
                i_type = st.selectbox("形態", type_list, label_visibility="collapsed")

            i_weight = input_row("重量（個）", "単位：kg")
            i_pcs = input_row("入数", "単位：個")
            i_sg = input_row("比重", "0.000")
            i_size = input_row("製品サイズ", "巾*長さ")
            
            calc_submit = st.form_submit_button("シミュレーション実行", use_container_width=True)

    # --- メイン画面：スクロールエリア ---
    st.markdown("<h1 style='text-align: center;'>Intelligent 熊谷さん<br>🤖 🤖 🤖 外箱サイズ確認 🤖 🤖 🤖</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: gray;'>まるで熊谷さんが考えたような精度で箱のサイズを考えてくれるアプリです</p>", unsafe_allow_html=True)
    st.divider()

    if uploaded_file:
        try:
            target_indices = [0, 1, 2, 3, 5, 6, 8, 9, 15, 26]
            col_names = ["製品コード", "製品名", "荷姿", "形態", "重量（個）", "入数", "重量（箱）", "比重", "外箱", "製品サイズ"]
            
            df_raw = pd.read_excel(uploaded_file, sheet_name="製品一覧", usecols=target_indices, names=col_names, skiprows=5, engine='openpyxl')
            df_processed = process_product_data(df_raw)

            # 形態のみでフィルタリング
            df_processed['形態'] = df_processed['形態'].astype(str).str.strip()
            df_display = df_processed[df_processed["形態"] == i_type].copy()

            if not df_display.empty:
                # --- グラフ描画セクション ---
                st.subheader(f"📈 外箱分布マップ ({i_type})")
                
                # 数値変換と欠損値除外（横軸：重量（個）、縦軸：入数）
                df_display["重量（個）"] = pd.to_numeric(df_display["重量（個）"], errors='coerce')
                df_display["入数"] = pd.to_numeric(df_display["入数"], errors='coerce')
                plot_data = df_display.dropna(subset=["重量（個）", "入数"])

                # Scatterプロット作成
                fig = px.scatter(
                    plot_data,
                    x="重量（個）",
                    y="入数",
                    color="外箱",  # 外箱の種類で色分け
                    hover_name="製品名",
                    hover_data={
                        "製品コード": True,
                        "製品サイズ": True,
                        "重量（個）": ":.3f",
                        "入数": True,
                        "重量（箱）": ":.2f",
                        "外箱": True
                    },
                    template="plotly_white",
                    height=600,
                    labels={"重量（個）": "重量（個） [kg]", "入数": "入数 [個]"}
                )

                # プロットの見た目調整
                fig.update_traces(
                    marker=dict(size=12, opacity=0.7, line=dict(width=1, color='DarkSlateGrey'))
                )
                
                # レイアウト調整（凡例を上部に配置してグラフエリアを広く）
                fig.update_layout(
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                    margin=dict(l=0, r=0, t=50, b=0)
                )

                st.plotly_chart(fig, use_container_width=True)

                # --- 表セクション ---
                st.divider()
                st.subheader(f"📊 実績データ一覧 ({i_type})")
                st.dataframe(df_display, use_container_width=True, height=500)
                st.info(f"表示件数: {len(df_display)}件")
                
            else:
                st.warning(f"「{i_type}」に一致するデータが見つかりませんでした。")
            
        except Exception as e:
            st.error(f"エラー: {e}")
    else:
        st.warning("サイドバーからファイルをアップロードしてください。")

if __name__ == "__main__":
    main()
