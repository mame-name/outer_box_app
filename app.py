import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from calc import process_product_data

st.set_page_config(layout="wide", page_title="小袋サイズ適正化アプリ")

# ==========================================
# グラフの表示詳細設定（ここを調整してください）
# ==========================================
SPAN_N = 5                 # 何個下の入数（実績）と結合してエリアを作るか
AREA_LINE_WIDTH = 2        # エリア外周の線幅
AREA_OPACITY = 0.3         # エリア内の塗りつぶし透明度
MARKER_SIZE = 8            # 点表示モードのサイズ
SIM_MARKER_SIZE = 18       # ターゲット（星）のサイズ
# ==========================================

# CSS: スタイル調整
st.markdown("""
    <style>
    [data-testid="stSidebar"] .stForm { border: none; padding: 0; }
    [data-testid="stSidebar"] .element-container { margin-bottom: -8px; }
    [data-testid="stSidebar"] label { font-size: 0.85rem !important; }
    .block-container { padding-top: 1.5rem !important; }
    ::placeholder { color: #aaaaaa !important; }
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
            # データ読込・クリーニング
            target_indices = [0, 1, 2, 3, 5, 6, 8, 9, 15, 26]
            col_names = ["製品コード", "製品名", "荷姿", "形態", "重量（個）", "入数", "重量（箱）", "比重", "外箱", "製品サイズ"]
            df_raw = pd.read_excel(uploaded_file, sheet_name="製品一覧", usecols=target_indices, names=col_names, skiprows=5, engine='openpyxl')
            
            df_processed = process_product_data(df_raw)
            
            exclude_boxes = ["専用", "No,27", "HC21-3"]
            df_base = df_processed[
                (df_processed["形態"] == i_type) & 
                (df_processed["外箱"].notna()) &
                (df_processed["外箱"].str.strip() != "") & 
                (~df_processed["外箱"].isin(exclude_boxes))
            ].copy()

            if not df_base.empty:
                available_boxes = sorted(df_base["外箱"].unique().tolist())
                plot_spot = st.empty()
                
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
                            # 入数ごとにxの最小・最大を抽出
                            stats = group.groupby("入数")["単一体積"].agg(['min', 'max']).reset_index()
                            stats = stats.sort_values("入数", ascending=False) # 入数が多い順
                            
                            x_path = []
                            y_path = []

                            # 右側の縁（最大体積側）を下へ辿る
                            for i in range(len(stats)):
                                curr = stats.iloc[i]
                                next_idx = i + SPAN_N if i + SPAN_N < len(stats) else len(stats) - 1
                                target_next = stats.iloc[next_idx]
                                
                                x_path.append(curr['max'])
                                y_path.append(curr['入数'])
                                # 垂直に繋いでから次の点へ（階段状）
                                x_path.append(curr['max'])
                                y_path.append(target_next['入数'])

                            # 左側の縁（最小体積側）を上へ戻る
                            for i in range(len(stats)-1, -1, -1):
                                curr = stats.iloc[i]
                                prev_idx = i - SPAN_N if i - SPAN_N >= 0 else 0
                                target_prev = stats.iloc[prev_idx]
                                
                                x_path.append(curr['min'])
                                y_path.append(curr['入数'])
                                x_path.append(curr['min'])
                                y_path.append(target_prev['入数'])

                            fig.add_trace(go.Scatter(
                                x=x_path, y=y_path,
                                fill='toself', 
                                fillcolor=color_map[box_type],
                                mode='lines',
                                line=dict(color=color_map[box_type], width=AREA_LINE_WIDTH),
                                opacity=AREA_OPACITY,
                                name=box_type,
                                hoverinfo='name'
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

                # ターゲット描画
                if i_weight and i_sg and i_pcs:
                    try:
                        sv, sp = float(i_weight)/float(i_sg), float(i_pcs)
                        fig.add_trace(go.Scatter(x=[sv], y=[sp], mode='markers',
                            marker=dict(symbol='star', size=SIM_MARKER_SIZE, color='red', line=dict(width=2, color='white')),
                            name='ターゲット'))
                    except: pass

                fig.update_layout(
                    template="plotly_white", height=600,
                    xaxis_title="1個あたりの体積 (重量/比重)",
                    yaxis_title="入数 [個]",
                    xaxis=dict(rangemode="tozero", zeroline=True, zerolinewidth=2, zerolinecolor='lightgrey'),
                    yaxis=dict(rangemode="tozero", zeroline=True, zerolinewidth=2, zerolinecolor='lightgrey'),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                
                plot_spot.plotly_chart(fig, use_container_width=True)
                st.divider()
                st.subheader("📊 実績データ一覧")
                st.dataframe(df_display, use_container_width=True, height=500)
            else:
                st.warning(f"「{i_type}」に該当するデータがありません。")
        except Exception as e:
            st.error(f"エラー: {e}")
    else:
        st.warning("サイドバーからファイルをアップロードしてください。")

if __name__ == "__main__":
    main()
