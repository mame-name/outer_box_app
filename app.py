import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from calc import process_product_data

st.set_page_config(layout="wide", page_title="小袋サイズ適正化アプリ")

# CSS: スタイル調整
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
    with st.sidebar:
        st.subheader("📁 実績データ読込")
        uploaded_file = st.file_uploader("実績XLSMを選択", type=['xlsm'], label_visibility="collapsed")
        st.divider()

        # --- ステップ1: 形態で絞り込み ---
        st.subheader("🔍 1. 形態選択")
        
        # 形態とセレクトボックスを横並びに配置
        c1, c2 = st.columns([1, 2])
        with c1: 
            st.markdown("<div style='padding-top:8px;'>形態</div>", unsafe_allow_html=True)
        with c2:
            type_list = ["小袋", "パウチ", "BIB", "スパウト"]
            i_type = st.selectbox("形態", type_list, label_visibility="collapsed")
            
        btn_filter = st.button("形態で絞ってグラフを表示", use_container_width=True)
        
        st.divider()

        # --- ステップ2: シミュレーション入力 ---
        st.subheader("📝 2. 条件設定")
        with st.form("sim_form"):
            def input_row(label, placeholder_text=""):
                c1, c2 = st.columns([1, 2])
                with c1: st.markdown(f"<div style='padding-top:8px;'>{label}</div>", unsafe_allow_html=True)
                with c2: return st.text_input(label, value="", placeholder=placeholder_text, label_visibility="collapsed")

            # 重量、入数、比重を横並び形式で配置
            i_weight = input_row("重量（個）", "単位：kg")
            i_pcs = input_row("入数", "単位：個")
            i_sg = input_row("比重", "0.000")
            
            calc_submit = st.form_submit_button("シミュレーション結果をグラフにプロット", use_container_width=True)

    st.markdown("<h1 style='text-align: center;'>Intelligent 熊谷さん<br>🤖 🤖 🤖 外箱サイズ確認 🤖 🤖 🤖</h1>", unsafe_allow_html=True)
    st.divider()

    if uploaded_file:
        try:
            target_indices = [0, 1, 2, 3, 5, 6, 8, 9, 15, 26]
            col_names = ["製品コード", "製品名", "荷姿", "形態", "重量（個）", "入数", "重量（箱）", "比重", "外箱", "製品サイズ"]
            df_raw = pd.read_excel(uploaded_file, sheet_name="製品一覧", usecols=target_indices, names=col_names, skiprows=5, engine='openpyxl')
            
            df_processed = process_product_data(df_raw)
            
            # 除外リスト適用
            exclude_boxes = ["専用", "No,27", "HC21-3"]
            df_filtered = df_processed[
                (df_processed["形態"] == i_type) & 
                (~df_processed["外箱"].isin(exclude_boxes))
            ].copy()

            if not df_filtered.empty:
                st.subheader(f"📈 外箱分布マップ（{i_type} / ※例外箱を除く）")
                plot_data = df_filtered[df_filtered["単一体積"] > 0].copy()

                # 散布図
                fig = px.scatter(
                    plot_data, x="単一体積", y="入数", color="外箱",
                    hover_name="製品名",
                    hover_data={"製品コード":True, "単一体積":":.3f", "重量（個）":True, "比重":True, "入数":True, "外箱":True},
                    template="plotly_white", height=650,
                    labels={"単一体積": "1個あたりの体積 (重量/比重)", "入数": "入数 [個]"}
                )

                # 実線エリアチャート表現
                for box_type in plot_data["外箱"].unique():
                    group = plot_data[plot_data["外箱"] == box_type]
                    if len(group) >= 3:
                        fig.add_trace(go.Scatter(
                            x=group["単一体積"], y=group["入数"],
                            fill='toself', 
                            fillcolor='rgba(150, 150, 150, 0.15)',
                            line=dict(width=1.5, dash='solid', color='rgba(100, 100, 100, 0.4)'),
                            name=f"{box_type} の範囲", 
                            showlegend=False, 
                            hoverinfo='skip'
                        ))

                # プロット実行（ボタン押下時）
                if calc_submit and i_weight and i_sg and i_pcs:
                    try:
                        sim_unit_vol = float(i_weight) / float(i_sg)
                        sim_pcs = float(i_pcs)
                        
                        fig.add_trace(go.Scatter(
                            x=[sim_unit_vol], y=[sim_pcs],
                            mode='markers+text',
                            marker=dict(symbol='star', size=25, color='red', line=dict(width=2, color='white')),
                            text=["ターゲット"],
                            textposition="top center",
                            name='ターゲット'
                        ))
                        
                        # 範囲拡張
                        max_vol = max(plot_data["単一体積"].max(), sim_unit_vol)
                        max_pcs = max(plot_data["入数"].max(), sim_pcs)
                        fig.update_xaxes(range=[0, max_vol * 1.1])
                        fig.update_yaxes(range=[0, max_pcs * 1.1])
                    except:
                        st.sidebar.warning("数値を入力してください")

                fig.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
                st.plotly_chart(fig, use_container_width=True)

                st.divider()
                st.subheader("📊 実績データ一覧")
                st.dataframe(df_filtered, use_container_width=True, height=500)
            else:
                st.warning(f"「{i_type}」に該当するデータがありません。")
        except Exception as e:
            st.error(f"エラー: {e}")
    else:
        st.warning("サイドバーからファイルをアップロードしてください。")

if __name__ == "__main__":
    main()
