import streamlit as st
import pandas as pd
import requests
import plotly.express as px
import plotly.graph_objects as go
from streamlit_option_menu import option_menu
from datetime import datetime

# ==========================================
# 1. ページ設定とカスタムCSS
# ==========================================
st.set_page_config(page_title="共有家計簿", page_icon="💰", layout="centered")

# スマホアプリ風にするためのカスタムCSS
st.markdown('''
<style>
    /* 全体の余白調整 */
    .block-container {
        padding-top: 1rem;
        padding-bottom: 5rem; /* 下部メニュー用余白 */
    }
    /* Streamlit標準のヘッダー/フッターを隠す */
    header {visibility: hidden;}
    footer {visibility: hidden;}
    /* ボタンを角丸にして押しやすく */
    .stButton>button {
        border-radius: 20px;
        height: 3rem;
        font-weight: bold;
    }
    /* データフレーム（表）の見た目調整 */
    .stDataFrame {
        border-radius: 10px;
        overflow: hidden;
    }
</style>
''', unsafe_allow_html=True)

# ==========================================
# 2. データ取得・保存関数 (GAS連携)
# ==========================================
try:
    GAS_URL = st.secrets["GAS_URL"]
except:
    st.error("⚠️ StreamlitのSecretsに `GAS_URL` が設定されていません。")
    st.stop()

@st.cache_data(ttl=5)
def load_data():
    try:
        response = requests.get(GAS_URL)
        data = response.json()
        df = pd.DataFrame(data)
        if not df.empty:
            df['金額'] = pd.to_numeric(df['金額'], errors='coerce').fillna(0).astype(int)
            df['日付'] = pd.to_datetime(df['日付'])
        return df
    except:
        return pd.DataFrame(columns=["日付", "カテゴリ", "金額", "入力者", "メモ"])

def save_data(date_val, category, amount, user, memo):
    payload = {
        "date": date_val.strftime("%Y/%m/%d"),
        "category": category,
        "amount": amount,
        "user": user,
        "memo": memo
    }
    try:
        requests.post(GAS_URL, json=payload)
        load_data.clear()
        return True
    except:
        return False

# データ読み込み
df = load_data()
current_month = datetime.today().replace(day=1)

# ==========================================
# 3. ナビゲーションメニュー (streamlit-option-menu)
# ==========================================
# スマホ表示を優先し、一番上にタブとして配置します
selected = option_menu(
    menu_title=None,
    options=["ホーム", "登録", "一覧", "分析"],
    icons=["house", "pencil-square", "calendar3", "bar-chart-fill"],
    menu_icon="cast",
    default_index=0,
    orientation="horizontal",
    styles={
        "container": {"padding": "0!important", "background-color": "#fafafa"},
        "icon": {"color": "#FF9D23", "font-size": "14px"}, 
        "nav-link": {"font-size": "12px", "text-align": "center", "margin":"0px", "--hover-color": "#eee"},
        "nav-link-selected": {"background-color": "#FF9D23"},
    }
)

# ==========================================
# 4. 各画面のUI実装
# ==========================================

# --- [1. ホーム画面] ---
if selected == "ホーム":
    st.subheader(f"📊 {datetime.today().month}月の支出状況")
    
    if df.empty:
        st.info("データがありません。支出を登録してください。")
    else:
        # 今月のデータに絞り込み
        df_this_month = df[(df['日付'].dt.year == current_month.year) & (df['日付'].dt.month == current_month.month)]
        
        if df_this_month.empty:
            st.info("今月の支出はまだありません。")
        else:
            total_expense = df_this_month['金額'].sum()
            st.markdown(f"<h3 style='text-align:center;'>支出合計: ¥{total_expense:,}</h3>", unsafe_allow_html=True)
            
            # トグル切り替え
            view_mode = st.radio("グラフ表示", ["カテゴリ別", "メンバー別"], horizontal=True, label_visibility="collapsed")
            
            if view_mode == "カテゴリ別":
                summary = df_this_month.groupby('カテゴリ', as_index=False)['金額'].sum()
                fig = px.pie(summary, values='金額', names='カテゴリ', hole=0.6,
                             color_discrete_sequence=px.colors.qualitative.Pastel)
            else:
                summary = df_this_month.groupby('入力者', as_index=False)['金額'].sum()
                fig = px.pie(summary, values='金額', names='入力者', hole=0.6,
                             color_discrete_sequence=px.colors.qualitative.Set2)
                
            fig.update_traces(textposition='inside', textinfo='percent+label')
            fig.update_layout(showlegend=False, margin=dict(t=10, b=10, l=10, r=10))
            st.plotly_chart(fig, use_container_width=True)

# --- [2. 登録画面] ---
elif selected == "登録":
    st.subheader("📝 支出の登録")
    
    with st.form("expense_form", clear_on_submit=True):
        amount = st.number_input("金額 (円)", min_value=0, step=100)
        category = st.selectbox("カテゴリ", ["食費", "日用雑貨費", "交通費", "交際費", "妊活", "固定費", "その他"])
        date_input = st.date_input("日付", value=datetime.today())
        user = st.radio("誰の支出？", ["夫", "妻", "共通"], horizontal=True)
        memo = st.text_input("詳細メモ (場所 / 用途など)")
        
        submitted = st.form_submit_button("登録する", use_container_width=True)
        
        if submitted:
            if amount > 0:
                with st.spinner("保存中..."):
                    success = save_data(date_input, category, amount, user, memo)
                if success:
                    st.success(f"¥{amount:,} ({category}) を登録しました！")
                else:
                    st.error("保存に失敗しました。")
            else:
                st.warning("金額を入力してください。")

# --- [3. 一覧画面] ---
elif selected == "一覧":
    st.subheader("📋 カレンダーと支出一覧")
    
    if df.empty:
        st.info("データがありません。")
    else:
        # 画像②のような、日付選択式のリスト
        selected_date = st.date_input("日付を選択（カレンダー）", value=datetime.today())
        
        # 選択した日付で絞り込み
        df_selected = df[df['日付'].dt.date == selected_date]
        
        st.markdown(f"**{selected_date.strftime('%Y年%m月%d日')} の支出**")
        if df_selected.empty:
            st.write("この日の支出はありません。")
        else:
            for _, row in df_selected.iterrows():
                with st.container():
                    cols = st.columns([1, 2, 1])
                    cols[0].write(f"**{row['カテゴリ']}**")
                    cols[1].caption(f"{row['入力者']} | {row['メモ']}")
                    cols[2].write(f"**¥{row['金額']:,}**")
                    st.divider()

# --- [4. 分析画面] ---
elif selected == "分析":
    st.subheader("📊 支出の推移と分析")
    
    if df.empty:
        st.info("データがありません。")
    else:
        # 画像③のようなカテゴリ絞り込み
        categories = ["全てのカテゴリ"] + list(df['カテゴリ'].unique())
        selected_cat = st.selectbox("カテゴリ絞り込み", categories)
        
        df_plot = df.copy()
        if selected_cat != "全てのカテゴリ":
            df_plot = df_plot[df_plot['カテゴリ'] == selected_cat]
        
        if not df_plot.empty:
            # 月ごとの集計
            df_plot['年月'] = df_plot['日付'].dt.strftime('%Y年%m月')
            monthly_summary = df_plot.groupby('年月', as_index=False)['金額'].sum()
            monthly_summary = monthly_summary.sort_values('年月')
            
            # 平均値（画像③の上の赤線）
            avg_amount = monthly_summary['金額'].mean()
            
            # 複合グラフ作成（棒グラフ＋平均折れ線）
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=monthly_summary['年月'], y=monthly_summary['金額'], name="支出額",
                marker_color='#FF9D23', text=monthly_summary['金額'].apply(lambda x: f"¥{x:,}"), textposition='auto'
            ))
            fig.add_trace(go.Scatter(
                x=monthly_summary['年月'], y=[avg_amount] * len(monthly_summary), mode='lines',
                name=f"平均 (¥{int(avg_amount):,})", line=dict(color='red', width=2, dash='dash')
            ))
            
            fig.update_layout(margin=dict(t=20, b=0, l=0, r=0), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
            st.plotly_chart(fig, use_container_width=True)
            
            st.divider()
            
            # 過去の月別データ（降順）
            st.markdown("##### 過去の月別データ")
            st.dataframe(monthly_summary.sort_values('年月', ascending=False).style.format({'金額': '¥{:,}'}), use_container_width=True, hide_index=True)
            
            # 年度ごとの集計
            st.markdown("##### 年間総計")
            df_plot['年'] = df_plot['日付'].dt.year.astype(str) + "年"
            yearly_summary = df_plot.groupby('年', as_index=False)['金額'].sum().sort_values('年', ascending=False)
            st.dataframe(yearly_summary.style.format({'金額': '¥{:,}'}), use_container_width=True, hide_index=True)
            
            # 全期間総計
            st.markdown(f"<h4 style='text-align:center;'>全期間総計: ¥{df_plot['金額'].sum():,}</h4>", unsafe_allow_html=True)
        else:
            st.write("該当するデータがありません。")