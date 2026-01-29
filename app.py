import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from calc import process_product_data

st.set_page_config(layout="wide", page_title="小袋サイズ適正化アプリ")

# ==========================================
# グラフの表示詳細設定
# ==========================================
SPAN_N = 3                 # 接続する入数の間隔（厚みの調整）
AREA_LINE_WIDTH = 1.5      
AREA_OPACITY = 0.25        
MARKER_SIZE = 8            
SIM_MARKER_SIZE = 20       
# ==========================================

st.markdown("""
    <style>
    [data-testid="stSidebar"] .stForm { border: none; padding: 0; }
    [data-testid="stSidebar"] .element-container { margin-bottom: -8px; }
    [data-testid="stSidebar"] label { font-size: 0.85rem !important; }
    .block-container { padding-top: 1.5rem !important; }
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
            c1, c2 = st.columns([1, 2])
            i_weight = st.sidebar.text_input("　重量/個", placeholder="kg")
            i_pcs = st.sidebar.text_input("　入数", placeholder="個")
            i_sg = st.sidebar.text_input("　比重", placeholder="0.000")
            calc_submit = st.form_submit_button("グラフにプロット", use_container_width=True)

    st.markdown("<h1 style='text-align: center;'>Intelligent 熊谷さん<br>🤖 外箱サイズ確認 🤖</h1>", unsafe_allow_html=True)

    if uploaded_file:
        try:
            target_indices = [0, 1, 2, 3, 5, 6, 8, 9, 15, 26]
            col_names = ["製品コード", "製品名", "荷姿", "形態", "重量（個）", "入数", "重量（箱）", "比重", "外箱", "製品サイズ"]
            df_raw = pd.read_excel(uploaded_file, sheet_name="製品一覧", usecols=target_indices, names=col_names, skiprows=5, engine='openpyxl')
            df_processed = process_product_data(df_raw)
            
            exclude_boxes = ["専用", "No,27", "HC21-3"]
            df_base = df_processed[
                (df_processed["形態"] == i_type) & 
                (df_processed["外箱"].notna()) &
                (df_processed.外箱.str.strip() != "") & 
                (~df_processed["外箱"].isin(exclude_boxes))
            ].copy()

            if not df_base.empty:
                available_boxes = sorted(df_base["外箱"].unique().tolist())
                selected_boxes = []
                check_cols = st.columns(len(available_boxes)) 
                for idx, box in enumerate(available_boxes):
                    with check_cols[idx]:
                        if st.checkbox(box, value=True, key=f"chk_{box}"):
                            selected_boxes.append(box)

                df_display = df_base[df_base["外箱"].isin(selected_boxes)].copy()
                plot_data = df_display[df_display["単一体積"] > 0].copy()

                fig = go.Figure()
                colors = px.colors.qualitative.Plotly
                color_map = {box: colors[i % len(colors)] for i, box in enumerate(available_boxes)}

                if not plot_data.empty:
                    for box_type in selected_boxes:
                        group = plot_data[plot_data["外箱"] == box_type]
                        if len(group) < 1: continue

                        if plot_mode == "実績を囲む（エリア）":
                            # --- 改良ロジック：累積最大・最小による包絡線 ---
                            stats = group.groupby("入数")["単一体積"].agg(['min', 'max']).reset_index()
                            stats = stats.sort_values("入数", ascending=False) # 入数大→小

                            # 階段状に繋ぐための座標生成
                            x_right, y_right = [], []
                            x_left, y_left = [], []

                            for i in range(len(stats)):
                                curr = stats.iloc[i]
                                # 右端：現在の入数での最大体積
                                x_right.append(curr['max'])
                                y_right.append(curr['入数'])
                                
                                # 指定スパン下の入数まで垂直に下ろす
                                target_idx = min(i + SPAN_N, len(stats)-1)
                                next_y = stats.iloc[target_idx]['入数']
                                x_right.append(curr['max'])
                                y_right.append(next_y)

                            for i in range(len(stats)-1, -1, -1):
                                curr = stats.iloc[i]
                                # 左端：現在の入数での最小体積
                                x_left.append(curr['min'])
                                y_left.append(curr['入数'])
                                
                                # 指定スパン上の入数まで垂直に上げる
                                target_idx = max(i - SPAN_N, 0)
                                next_y = stats.iloc[target_idx]['入数']
                                x_left.append(curr['min'])
                                y_left.append(next_y)

                            fig.add_trace(go.Scatter(
                                x=x_right + x_left,
                                y=y_right + y_left,
                                fill='toself', 
                                fillcolor=color_map[box_type],
                                mode='lines',
                                line=dict(color=color_map[box_type], width=AREA_LINE_WIDTH),
                                opacity=AREA_OPACITY,
                                name=box_type
                            ))
                        else:
                            fig.add_trace(go.Scatter(
                                x=group["単一体積"], y=group["入数"],
                                mode='markers',
                                marker=dict(size=MARKER_SIZE, color=color_map[box_type]),
                                name=box_type,
                                text=group["製品名"],
                                hovertemplate="<b>%{text}</b><br>単一体積: %{x:.3f}<br>入数: %{y}<extra></extra>"
                            ))

                # ターゲット星印
                if i_weight and i_sg and i_pcs:
                    try:
                        sv, sp = float(i_weight)/float(i_sg), float(i_pcs)
                        fig.add_trace(go.Scatter(x=[sv], y=[sp], mode='markers',
                            marker=dict(symbol='star', size=SIM_MARKER_SIZE, color='red', line=dict(width=2, color='white')),
                            name='ターゲット'))
                    except: pass

                fig.update_layout(
                    template="plotly_white", height=600,
                    xaxis_title="1個あたりの体積 (重量/比重)", yaxis_title="入数 [個]",
                    xaxis=dict(rangemode="tozero", zeroline=True),
                    yaxis=dict(rangemode="tozero", zeroline=True),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                st.plotly_chart(fig, use_container_width=True)
                st.dataframe(df_display, use_container_width=True)
        except Exception as e:
            st.error(f"エラー: {e}")

if __name__ == "__main__":
    main()
