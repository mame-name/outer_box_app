import streamlit as st
import pandas as pd
from calc import process_product_data

# ページ全体のレイアウト設定
st.set_page_config(layout="wide", page_title="小袋サイズ適正化アプリ")

# --- CSS: 独立スクロールと余白の最小化 ---
st.markdown("""
    <style>
    /* ページ全体のスクロールを禁止 */
    [data-testid="stAppViewContainer"] {
        overflow: hidden;
    }
    
    /* タイトル周りの余白削減 */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 0rem !important;
    }
    
    /* 左右独立スクロールコンテナの設定 (高さは画面に合わせて調整) */
    .scroll-column {
        height: 80vh; 
        overflow-y: auto;
        padding: 10px;
        border: 1px solid #f0f2f6;
        border-radius: 5px;
    }

    /* フォームのスタイリング */
    .stForm {
        border: 1px solid #ddd;
        padding: 15px;
        border-radius: 10px;
        background-color: #f9f9f9;
    }

    /* タイトルセクションのスタイル */
    .title-section {
        text-align: center;
        margin-bottom: -10px;
    }
    </style>
    """, unsafe_allow_html=True)

def main():
    # --- 固定タイトルエリア ---
    st.markdown('<div class="title-section">', unsafe_allow_html=True)
    st.markdown("<h3>Intelligent 熊谷さん<br>🤖 🤖 🤖 小袋サイズ確認 🤖 🤖 🤖</h3>", unsafe_allow_html=True)
    st.markdown("<p style='color: gray; font-size: 0.8rem;'>まるで熊谷さんが考えたような精度でサイズを確認してくれるアプリです</p>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    st.divider()

    # --- メインコンテンツエリア (独立スクロール) ---
    col_left, col_right = st.columns([1, 2], gap="medium")

    # 左画面: 操作・入力
    with col_left:
        st.markdown('<div class="scroll-column">', unsafe_allow_html=True)
        
        st.subheader("📁 実績データ読込")
        uploaded_file = st.file_uploader("実績XLSMを選択", type=['xlsm'], label_visibility="collapsed")
        
        st.markdown("---")
        
        st.subheader("📝 条件設定")
        with st.form("sim_form"):
            i_nosugata = st.selectbox("荷姿", ["液体", "粉体", "その他"])
            i_weight = st.number_input("重量（個） (g)", value=0.0, step=0.1)
            i_pcs = st.number_input("入数", value=0, step=1)
            i_sg = st.number_input("比重", value=0.000, step=0.001, format="%.3f")
            i_size = st.text_input("製品サイズ (巾*長さ)", placeholder="100*150")
            
            st.form_submit_button("シミュレーション実行", use_container_width=True)
        
        st.markdown('</div>', unsafe_allow_html=True)

    # 右画面: 実績データ表示
    with col_right:
        st.markdown('<div class="scroll-column">', unsafe_allow_html=True)
        st.subheader("📊 実績データ一覧")
        
        if uploaded_file:
            try:
                # A:0, B:1, C:2, D:3, F:5, G:6, I:8, J:9, P:15, AA:26
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
                
                # 表を表示
                st.dataframe(df_final, use_container_width=True, height=1000) # 十分な高さを確保
                st.success(f"自動読込完了: {len(df_final)} 件")
                
            except Exception as e:
                st.error(f"エラー: {e}")
        else:
            st.info("左側からファイルをアップロードしてください。")
            
        st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
