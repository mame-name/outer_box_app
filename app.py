import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from calc import process_product_data

st.set_page_config(layout="wide", page_title="小袋サイズ適正化アプリ")

# UIスタイルの微調整
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stForm { border: 1px solid #ddd; padding: 20px; border-radius: 10px; background-color: white; }
    div[data-testid="stExpander"] { border: none !important; }
    </style>
    """, unsafe_allow_html=True)

def main():
    st.markdown("<h2 style='text-align: center;'>🤖 小袋サイズ適正化シミュレーター</h2>", unsafe_allow_html=True)
    st.divider()

    # 2画面分割の設定
    col_left, col_right = st.columns([1, 2], gap="large")

    # --- 左画面：設定・入力エリア ---
    with col_left:
        st.subheader("📁 データ読込 & 設定")
        uploaded_file = st.file_uploader("実績XLSM読込", type=['xlsm'])
        
        st.markdown("---")
        
        with st.form("sim_form"):
            st.markdown("#### 🔍 シミュレーション条件")
            
            # 入力行のヘルパー関数
            def input_row(label, placeholder="", is_number=False, val=0):
                c1, c2 = st.columns([1, 2])
                with c1: st.markdown(f"<div style='padding-top:8px;'>{label}</div>", unsafe_allow_html=True)
                with c2:
                    if is_number: return st.number_input(label, value=val, step=1, label_visibility="collapsed")
                    else: return st.text_input(label, placeholder=placeholder, label_visibility="collapsed")

            # ご要望の項目
            i_form = input_row("　形態", "例: 液体/粉体")
            i_pcs = input_row("　入数", is_number=True, val=0)
            i_w = input_row("　重量", "g", is_number=True, val=200)
            i_sg = input_row("　比重", "0.000")
            i_width = input_row("　巾", "折返し巾", is_number=True, val=100)
            i_length = input_row("　長さ", is_number=True, val=150)
            
            c1, c2 = st.columns([1, 2])
            with c1: st.markdown("<div style='padding-top:8px;'>　シール</div>", unsafe_allow_html=True)
            with c2: i_seal = st.selectbox("シール形式", ["ビン口", "フラット"], label_visibility="collapsed")

            c1, c2 = st.columns([1, 2])
            with c1: st.markdown("<div style='padding-top:8px;'>　充填機</div>", unsafe_allow_html=True)
            with c2: i_machine = st.selectbox("充填機選択", ["FR-1/5", "ZERO-1"], label_visibility="collapsed")
            
            submit = st.form_submit_button("計算・プロット実行", use_container_width=True)

        # 計算結果の簡易表示エリア
        sim_data = None
        if submit:
            try:
                w_v, s_v, wd_v, ln_v = float(i_w), float(i_sg or 1.0), float(i_width), float(i_length)
                adj_wd = (wd_v - 10) if "FR" in i_machine else (wd_v - 8)
                sim_area = (adj_wd * (ln_v - 24) + 40) if i_seal == "ビン口" else (adj_wd * (ln_v - 15))
                sim_vol = w_v / 1000 / s_v
                sim_height = (sim_vol / sim_area) * 1000000 * 1.9
                sim_data = {"vol": sim_vol, "height": sim_height}

                st.success(f"計算完了: 高さ {sim_height:.2f} / 体積 {sim_vol:.4f}")
            except:
                st.error("入力値を確認してください（比重など）")

    # --- 右画面：グラフ表示エリア ---
    with col_right:
        if uploaded_file:
            try:
                target_indices = [0, 1, 4, 5, 6, 9, 15, 17, 18, 25, 26, 28]
                col_names = ["製品コード", "名前", "充填機", "重量", "入数", "比重", "外装", "顧客名", "ショット", "粘度", "製品サイズ", "シール"]
                df_raw = pd.read_excel(uploaded_file, sheet_name="製品一覧", usecols=target_indices, names=col_names, skiprows=5, engine='openpyxl')
                df_final = process_product_data(df_raw)
                
                plot_df = df_final.dropna(subset=['体積', '高さ', '重量']).copy()
                plot_df = plot_df[(plot_df['体積'] > 0) & (plot_df['高さ'] > 0)]

                if not plot_df.empty:
                    fig = px.scatter(plot_df, x="体積", y="高さ", color="充填機", 
                                     hover_name="名前", 
                                     hover_data={"重量": ":.1f", "シール": True, "製品サイズ": True},
                                     color_discrete_sequence=["#DDA0DD", "#7CFC00", "#00BFFF"])

                    # 近似曲線
                    for col, n, c in [("高さ", "全体平均", "DarkSlateGrey"), ("上限高", "上限目安", "Orange"), ("下限高", "下限目安", "DeepPink")]:
                        temp_fig = px.scatter(plot_df, x="体積", y=col, trendline="ols")
                        trend = temp_fig.data[1]
                        trend.name, trend.line.color, trend.mode = n, c, 'lines'
                        fig.add_trace(trend)

                    # シミュレーション点（星印）
                    if sim_data:
                        fig.add_trace(go.Scatter(x=[sim_data["vol"]], y=[sim_data["height"]], mode='markers',
                                                 marker=dict(symbol='star', size=18, color='red', line=dict(width=2, color='black')),
                                                 name='シミュレーション結果'))

                    fig.update_layout(xaxis=dict(tickformat=".3f", range=[0, 0.04]), yaxis=dict(range=[0, 10]), height=650)
                    st.plotly_chart(fig, use_container_width=True)
                
                with st.expander("📋 抽出データ一覧を表示"):
                    st.dataframe(df_final, use_container_width=True)

            except Exception as e:
                st.error(f"読み込みエラー: {e}")
        else:
            st.info("左画面から実績ファイルをアップロードしてください。グラフがここに表示されます。")

if __name__ == "__main__":
    main()
