import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from calc import process_product_data

st.set_page_config(layout="wide", page_title="小袋サイズ適正化アプリ")

# CSS: スタイル調整（チェックボックスを横並びにするためのスタイル含む）
st.markdown("""
    <style>
    [data-testid="stSidebar"] .stForm { border: none; padding: 0; }
    [data-testid="stSidebar"] .element-container { margin-bottom: -8px; }
    [data-testid="stSidebar"] label { font-size: 0.85rem !important; }
    .block-container { padding-top: 1.5rem !important; }
    ::placeholder { color: #aaaaaa !important; }
    /* チェックボックス群の余白調整 */
    .stCheckbox { margin-bottom: -10px; }
    </style>
    """, unsafe_allow_html=True)

def main():
    with st.sidebar:
        st.subheader("📁 実績データ読込")
        uploaded_file = st.file_uploader("実績XLSMを選択", type=['xlsm'], label_visibility="collapsed")
        st.divider()

        st.subheader("🔍 1. 形態選択")
        c1, c2 = st.columns([1, 2])
        with c1: st.markdown("<div style='padding-top:8px;'>　形態</div>", unsafe_allow_html=True)
        with c2:
            type_list = ["小袋", "パウチ", "BIB", "スパウト"]
            i_type = st.selectbox("形態", type_list, label_visibility="collapsed")
        
        st.divider()

        st.subheader("📝 2. 条件設定")
        with st.form("sim_form"):
            def input_row(label, placeholder_text=""):
                c1, c2 = st.columns([1, 2])
                with c1: st.markdown(f"<div style='padding-top:8px;'>{label}</div>", unsafe_allow_html=True)
                with c2: return st.text_input(label, value="", placeholder=placeholder_text, label_visibility="collapsed")

            i_weight = input_row("　重量/個", "単位：kg")
            i_pcs = input_row("　入数", "単位：個")
            i_sg = input_row("　比重", "0.000")
            calc_submit = st.form_submit_button("グラフにプロット", use_container_width=True)

    st.markdown("<h1 style='text-align: center;'>Intelligent 熊谷さん<br>🤖 🤖 🤖 外箱サイズ確認 🤖 🤖 🤖</h1>", unsafe_allow_html=True)
    st.divider()

    if uploaded_file:
        try:
            target_indices = [0, 1, 2, 3, 5, 6, 8, 9, 15, 26]
            col_names = ["製品コード", "製品名", "荷姿", "形態", "重量（個）", "入数", "重量（箱）", "比重", "外箱", "製品サイズ"]
            df_raw = pd.read_excel(uploaded_file, sheet_name="製品一覧", usecols=target_indices, names=col_names, skiprows=5, engine='openpyxl')
            
            df_processed = process_product_data(df_raw)
            
            # 初期フィルタ（形態と除外リスト）
            exclude_boxes = ["専用", "No,27", "HC21-3"]
            df_base = df_processed[
                (df_processed["形態"] == i_type) & 
                (~df_processed["外箱"].isin(exclude_boxes))
            ].copy()

            if not df_base.empty:
                st.subheader(f"📈 外箱分布マップ（{i_type}）")
                
                # --- 【修正】横並びチェックボックスの実装 ---
                available_boxes = sorted(df_base["外箱"].unique().tolist())
                st.write("表示する外箱を選択:")
                
                # 画面の幅に合わせてチェックボックスを配置（5列で折り返し）
                cols = st.columns(5)
                selected_boxes = []
                for idx, box in enumerate(available_boxes):
                    with cols[idx % 5]:
                        if st.checkbox(box, value=True, key=f"chk_{box}"):
                            selected_boxes.append(box)
                # ------------------------------------------

                # 選択された箱だけでフィルタリング
                df_filtered = df_base[df_base["外箱"].isin(selected_boxes)].copy()
                plot_data = df_filtered[df_filtered["単一体積"] > 0].copy()

                # グラフ作成
                fig = px.scatter(
                    plot_data, x="単一体積", y="入数", color="外箱",
                    hover_name="製品名",
                    hover_data={"製品コード":True, "単一体積":":.3f", "重量（個）":True, "比重":True, "入数":True, "外箱":True},
                    template="plotly_white", height=650,
                    labels={"単一体積": "1個あたりの体積 (重量/比重)", "入数": "入数 [個]"},
                    category_orders={"外箱": available_boxes}
                )

                # 実線エリアチャート表現
                for box_type in selected_boxes:
                    group = plot_data[plot_data["外箱"] == box_type]
                    if len(group) >= 3:
                        fig.add_trace(go.Scatter(
                            x=group["単一体積"], y=group["入数"],
                            fill='toself', 
                            fillcolor='rgba(150, 150, 150, 0.1)',
                            line=dict(width=1.5, dash='solid', color='rgba(100, 100, 100, 0.3)'),
                            name=f"{box_type} の範囲", 
                            showlegend=False, 
                            hoverinfo='skip'
                        ))

                # プロット実行
                if calc_submit and i_weight and i_sg and i_pcs:
                    try:
                        sim_unit_vol = float(i_weight) / float(i_sg)
                        sim_pcs = float(i_pcs)
                        fig.add_trace(go.Scatter(
                            x=[sim_unit_vol], y=[sim_pcs],
                            mode='markers+text',
                            marker=dict(symbol='star', size=25, color='red', line=dict(width=2, color='white')),
                            text=["ターゲット"], textposition="top center", name='ターゲット'
                        ))
                        # 範囲拡張
                        max_vol = max(plot_data["単一体積"].max() if not plot_data.empty else 0, sim_unit_vol)
                        max_pcs = max(plot_data["入数"].max() if not plot_data.empty else 0, sim_pcs)
                        fig.update_xaxes(range=[0, max_vol * 1.1])
                        fig.update_yaxes(range=[0, max_pcs * 1.1])
                    except:
                        pass

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
