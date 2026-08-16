import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.set_page_config(page_title="我が家の家計簿", page_icon="💰", layout="centered")
st.title("💰 夫婦共有の家計簿")

# Googleスプレッドシートへの接続設定（Secretsから自動読み込み）
conn = st.connection("gsheets", type=GSheetsConnection)

try:
    # 既存データの読み込み（ttl=0で最新データを毎回取得）
    data = conn.read(ttl=0)
    if data.empty:
        data = pd.DataFrame(columns=["日付", "カテゴリ", "金額", "入力者", "メモ"])
except Exception as e:
    st.error("データの読み込みに失敗しました。Secretsの設定を確認してください。")
    st.stop()

# 支出入力フォーム
with st.form("kakeibo_form", clear_on_submit=True):
    date = st.date_input("日付")
    category = st.selectbox("カテゴリ", ["食費", "日用品", "交際費", "固定費", "その他"])
    amount = st.number_input("金額 (円)", min_value=0, step=100)
    user = st.radio("入力者", ["夫", "妻"], horizontal=True)
    memo = st.text_input("メモ")
    
    submitted = st.form_submit_button("支出を記録する")

if submitted:
    if amount == 0:
        st.warning("金額を1文字以上（1円以上）入力してください。")
    else:
        # 新しいデータの追加
        new_row = pd.DataFrame([{
            "日付": date.strftime("%Y-%m-%d"), 
            "カテゴリ": category, 
            "金額": amount, 
            "入力者": user, 
            "メモ": memo
        }])
        
        updated_df = pd.concat([data, new_row], ignore_index=True)
        
        try:
            conn.update(data=updated_df)
            st.success("✨ 支出を記録しました！")
            st.rerun()
        except Exception as e:
            st.error(f"保存に失敗しました: {e}")

# 履歴表示（新しい順）
st.subheader("📋 支出履歴")
st.dataframe(data.iloc[::-1], use_container_width=True)