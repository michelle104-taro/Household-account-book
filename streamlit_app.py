import streamlit as st
import pandas as pd
import requests
import plotly.express as px
from datetime import datetime

# ページ設定（スマホを意識したレイアウト）
st.set_page_config(page_title="共有家計簿", page_icon="💰", layout="centered")

# SecretsからGASのURLを取得
try:
    GAS_URL = st.secrets["GAS_URL"]
except:
    st.error("⚠️ StreamlitのSecretsに `GAS_URL` が設定されていません。")
    st.stop()

# スプレッドシートからデータを取得する関数
@st.cache_data(ttl=3) # 3秒間キャッシュ
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

# スプレッドシートにデータを送信する関数
def save_data(date, category, amount, user, memo):
    payload = {
        "date": date.strftime("%Y/%m/%d"),
        "category": category,
        "amount": amount,
        "user": user,
        "memo": memo
    }
    requests.post(GAS_URL, json=payload)
    load_data.clear() # データを最新に更新

# ====== UI設計 ======
st.title("💰 夫婦の共有家計簿")

# アプリ風にタブで画面切り替え
tab1, tab2, tab3 = st.tabs(["📝 入力する", "📋 支出一覧", "📊 グラフ・予算"])

# --- タブ1：入力画面 ---
with tab1:
    with st.form("input_form", clear_on_submit=True):
        st.subheader("支出の記録")
        amount = st.number_input("金額 (円)", min_value=0, step=100)
        
        st.markdown("##### どんな支出？")
        category = st.selectbox("カテゴリ", ["食費", "日用雑貨費", "交通費", "交際費", "妊活", "固定費", "その他"])
        date = st.date_input("日付", value=datetime.today())
        memo = st.text_input("詳細メモ (場所 / 用途など)")
        
        st.markdown("##### 誰の支出？")
        user = st.radio("", ["夫", "妻", "共通"], horizontal=True, label_visibility="collapsed")
        
        submitted = st.form_submit_button("作成", use_container_width=True)
        
        if submitted:
            if amount > 0:
                with st.spinner("保存中..."):
                    save_data(date, category, amount, user, memo)
                st.success("支出を記録しました！")
            else:
                st.warning("金額を入力してください。")

# --- タブ2：一覧画面 ---
with tab2:
    st.subheader("支出一覧")
    df = load_data()
    if df.empty:
        st.info("まだデータがありません。")
    else:
        # 日付の新しい順に並び替え
        df_sorted = df.sort_values('日付', ascending=False)
        
        for index, row in df_sorted.iterrows():
            with st.container():
                cols = st.columns([1, 2, 1])
                cols[0].write(f"**{row['カテゴリ']}**")
                cols[1].caption(f"{row['日付'].strftime('%m/%d')} | {row['メモ']}")
                cols[2].write(f"**¥{row['金額']:,}**")
                st.divider()

# --- タブ3：グラフ画面 ---
with tab3:
    st.subheader("支出の割合")
    df = load_data()
    if df.empty:
        st.info("データがありません。")
    else:
        # 合計金額の計算
        total = df['金額'].sum()
        st.markdown(f"<h3 style='text-align: center;'>支出合計: ¥{total:,}</h3>", unsafe_allow_html=True)
        
        # ドーナツグラフの作成 (Plotly)
        summary = df.groupby('カテゴリ', as_index=False)['金額'].sum()
        fig = px.pie(summary, values='金額', names='カテゴリ', hole=0.5, 
                     color_discrete_sequence=px.colors.qualitative.Pastel)
        fig.update_traces(textposition='inside', textinfo='percent+label')
        fig.update_layout(showlegend=False, margin=dict(t=0, b=0, l=0, r=0))
        st.plotly_chart(fig, use_container_width=True)