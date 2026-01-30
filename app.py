import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from calc import process_product_data

st.set_page_config(layout="wide", page_title="外箱サイズ確認アプリ")

# ==========================================
# グラフの表示詳細設定
# ==========================================
AREA_LINE_WIDTH = 0.5      
AREA_OPACITY = 0.4         # 異なる箱同士の重なり用
MARKER_SIZE = 8            
SIM_MARKER_SIZE = 18       
# ==========================================

# CSS
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
    # 入力値を管理するセッション状態の初期化
    if "weight_val" not in st.session_state: st.session_state.weight_val = ""
    if "pcs_val" not in st.session_state: st.session_state.pcs_val = ""
    if "sg_val" not in st.session_state: st.session_state.sg_val = ""

    with st.sidebar:
        st.subheader("📁 実績データ読込")
        uploaded_file = st.file_uploader("実績XLSMを選択", type=['xlsm'], label_visibility="collapsed")

        st.subheader("📊 表示設定")
        plot_mode = st.radio("表示パターン", ["範囲で確認", "プロットで確認"], index=0)

        st.subheader("🔍 1. 形態選択")
        c1, c2 = st.columns([1, 2])
        with c1: st.markdown("<div style='padding-top:8px;'>　形態</div>", unsafe_allow_html=True)
        with c2:
            type_list = ["パウチ", "BIB", "小袋", "スパウト"]
            i_type = st.selectbox("形態", type_list, index=None, placeholder="選択してください", label_visibility="collapsed")

        st.subheader("📝 2. 条件設定")
        with st.form("sim_form"):
            def input_row(label, key, placeholder_text=""):
                c1, c2 = st.columns([1, 2])
                with c1: st.markdown(f"<div style='padding-top:8px;'>{label}</div>", unsafe_allow_html=True)
                # valueにsession_stateを入れる
                with c2: return st.text_input(label, value=st.session_state[key], placeholder=placeholder_text, label_visibility="collapsed", key=f"input_{key}")

            i_weight = input_row("　重量/個", "weight_val", "kg")
            i_pcs = input_row("　入数", "pcs_val", "個")
            i_sg = input_row("　比重", "sg_val", "0.000")
            calc_submit = st.form_submit_button("グラフにプロット", use_container_width=True, type="primary")
            
            if calc_submit:
                st.session_state.weight_val = i_weight
                st.session_state.pcs_val = i_pcs
                st.session_state.sg_val = i_sg
                st.rerun()

        # プロットボタン（フォーム）のすぐ下に配置
        if st.button("入力内容をクリア", use_container_width=True):
            # 保持用の変数と、入力欄自体のWidget keyの両方をリセット
            st.session_state.weight_val = ""
            st.session_state.pcs_val = ""
            st.session_state.sg_val = ""
            if "input_weight_val" in st.session_state: st.session_state.input_weight_val = ""
            if "input_pcs_val" in st.session_state: st.session_state.input_pcs_val = ""
            if "input_sg_val" in st.session_state: st.session_state.input_sg_val = ""
            st.rerun()

    st.markdown("<h1 style='text-align: center;'>Intelligent 熊谷さん<br>🤖 🤖 🤖 外箱サイズ確認 🤖 🤖 🤖</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: gray;'>まるで熊谷さんが考えたような精度で外箱を確認してくれるアプリです</p>", unsafe_allow_html=True)
    st.markdown("---")

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
                    if plot_mode == "範囲で確認":
                        for box_type in selected_boxes:
                            group = plot_data[plot_data["外箱"] == box_type]
                            if len(group) < 1: continue

                            stats = group.groupby("入数")["単一体積"].agg(['min', 'max']).reset_index()
                            stats = stats.sort_values("入数", ascending=False)

                            combined_x = []
                            combined_y = []

                            for i in range(len(stats)):
                                p_curr = stats.iloc[i]
                                if i + 1 < len(stats):
                                    p_target = stats.iloc[i + 1]
                                    combined_x.extend([p_curr['min'], p_curr['max'], p_target['max'], p_target['min'], p_curr['min'], None])
                                    combined_y.extend([p_curr['入数'], p_curr['入数'], p_target['入数'], p_target['入数'], p_curr['入数'], None])

                            fig.add_trace(go.Scatter(
                                x=combined_x, y=combined_y,
                                fill='toself',
                                fillcolor=color_map[box_type],
                                mode='lines',
                                line=dict(color=color_map[box_type], width=AREA_LINE_WIDTH),
                                opacity=AREA_OPACITY,
                                name=box_type,
                                hoverinfo='skip'
                            ))
                    else:
                        for box_type in selected_boxes:
                            group = plot_data[plot_data["外箱"] == box_type]
                            fig.add_trace(go.Scatter(
                                x=group["単一体積"], y=group["入数"],
                                mode='markers',
                                marker=dict(size=MARKER_SIZE, color=color_map[box_type]),
                                name=box_type,
                                text=group["製品名"],
                                hovertemplate="<b>%{text}</b><br>体積: %{x:.3f}<br>入数: %{y}<extra></extra>"
                            ))

                # ターゲット表示
                if st.session_state.weight_val and st.session_state.pcs_val and st.session_state.sg_val:
                    try:
                        sv = float(st.session_state.weight_val) / float(st.session_state.sg_val)
                        sp = float(st.session_state.pcs_val)
                        fig.add_trace(go.Scatter(
                            x=[sv], y=[sp], mode='markers',
                            marker=dict(symbol='star', size=SIM_MARKER_SIZE, color='red', line=dict(width=2, color='white')),
                            name='ターゲット'
                        ))
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
        st.info("👈 左側のパネルから「実績データベース (.xlsm)」をアップロードしてください。")

if __name__ == "__main__":
    main()
