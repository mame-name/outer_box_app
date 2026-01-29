import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from calc import process_product_data

st.set_page_config(layout="wide", page_title="小袋サイズ適正化アプリ")

# CSS: スタイル調整
st.markdown("""
    <style>
    [data-testid="stSidebar"] .stForm { border: none; padding: 0; }
    [data-testid="stSidebar"] label { font-size: 0.85rem !important; }
    .stCheckbox { margin-top: -15px; }
    </style>
    """, unsafe_allow_html=True)

def main():
    with st.sidebar:
        st.subheader("📁 実績データ読込")
        uploaded_file = st.file_uploader("実績XLSMを選択", type=['xlsm'], label_visibility="collapsed")
        st.divider()

        st.subheader("📊 表示設定")
        plot_mode = st.radio("表示パターン", ["実績を囲む（エリア）", "全てのプロット（点）"], index=0)
        st.divider()

        st.subheader("🔍 1. 形態選択")
        type_list = ["小袋", "パウチ", "BIB", "スパウト"]
        i_type = st.selectbox("形態", type_list, label_visibility="collapsed")
        
        st.divider()

        st.subheader("📝 2. 条件設定")
        with st.form("sim_form"):
            def input_row(label):
                c1, c2 = st.columns([1, 2])
                with c1: st.markdown(f"<div style='padding-top:8px;'>{label}</div>", unsafe_allow_html=True)
                with c2: return st.text_input(label, label_visibility="collapsed")
            i_weight = input_row("　重量/個")
            i_pcs = input_row("　入数")
            i_sg = input_row("　比重")
            st.form_submit_button("グラフにプロット", use_container_width=True)

    st.markdown("<h1 style='text-align: center;'>Intelligent 熊谷さん<br>🤖 外箱サイズ確認 🤖</h1>", unsafe_allow_html=True)

    if uploaded_file:
        try:
            target_indices = [0, 1, 2, 3, 5, 6, 8, 9, 15, 26]
            col_names = ["製品コード", "製品名", "荷姿", "形態", "重量（個）", "入数", "重量（箱）", "比重", "外箱", "製品サイズ"]
            df_raw = pd.read_excel(uploaded_file, sheet_name="製品一覧", usecols=target_indices, names=col_names, skiprows=5, engine='openpyxl')
            df_processed = process_product_data(df_raw)
            
            df_base = df_processed[
                (df_processed["形態"] == i_type) & 
                (df_processed["外箱"].notna()) & 
                (df_processed["外箱"] != "")
            ].copy()

            if not df_base.empty:
                available_boxes = sorted(df_base["外箱"].unique().tolist())
                selected_boxes = []
                check_cols = st.columns(len(available_boxes)) 
                for idx, box in enumerate(available_boxes):
                    with check_cols[idx]:
                        if st.checkbox(box, value=True, key=f"chk_{box}"):
                            selected_boxes.append(box)

                fig = go.Figure()
                colors = px.colors.qualitative.Plotly
                color_map = {box: colors[i % len(colors)] for i, box in enumerate(available_boxes)}

                plot_data = df_base[df_base["外箱"].isin(selected_boxes)].copy()

                if not plot_data.empty:
                    for box_type in selected_boxes:
                        group = plot_data[plot_data["外箱"] == box_type]
                        if len(group) < 1: continue

                        if plot_mode == "実績を囲む（エリア）":
                            # 【新ロジック】入数ごとの左右端を特定して繋ぐ
                            # 1. 入数ごとにxの最小・最大を出す
                            stats = group.groupby("入数")["単一体積"].agg(['min', 'max']).reset_index()
                            # 2. 入数(y)の昇順でソート
                            stats = stats.sort_values("入数")

                            # エリアのパスを作成
                            # 右端を「下から上」へ辿り、次に左端を「上から下」へ辿る
                            x_right = stats['max'].tolist()
                            y_right = stats['入数'].tolist()
                            x_left = stats['min'].tolist()[::-1]
                            y_left = stats['入数'].tolist()[::-1]

                            x_path = x_right + x_left
                            y_path = y_right + y_left

                            # プロットが1点しかない場合や直線すぎる場合のために少しだけ幅を持たせる
                            if len(stats) == 1: # 1つの入数しかない場合
                                x_path = [stats['min'].iloc[0]*0.95, stats['max'].iloc[0]*1.05, stats['max'].iloc[0]*1.05, stats['min'].iloc[0]*0.95]
                                y_path = [stats['入数'].iloc[0]-1, stats['入数'].iloc[0]-1, stats['入数'].iloc[0]+1, stats['入数'].iloc[0]+1]

                            fig.add_trace(go.Scatter(
                                x=x_path, y=y_path,
                                fill='toself',
                                fillcolor=color_map[box_type],
                                mode='lines',
                                line=dict(color=color_map[box_type], width=2),
                                opacity=0.3,
                                name=box_type,
                                hoverinfo='name'
                            ))
                        else:
                            # プロットモード
                            fig.add_trace(go.Scatter(
                                x=group["単一体積"], y=group["入数"],
                                mode='markers',
                                marker=dict(size=8, color=color_map[box_type]),
                                name=box_type
                            ))

                # ターゲット描画
                if i_weight and i_sg and i_pcs:
                    try:
                        sv, sp = float(i_weight)/float(i_sg), float(i_pcs)
                        fig.add_trace(go.Scatter(x=[sv], y=[sp], mode='markers',
                            marker=dict(symbol='star', size=20, color='red', line=dict(width=2, color='white')),
                            name='ターゲット'))
                    except: pass

                fig.update_layout(
                    template="plotly_white", height=600,
                    xaxis_title="1個あたりの体積 (重量/比重)", yaxis_title="入数 [個]",
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"エラー: {e}")

if __name__ == "__main__":
    main()
