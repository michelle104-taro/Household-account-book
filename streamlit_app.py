import streamlit as st
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="我が家の家計簿", page_icon="💰")
st.title("💰 夫婦共有の家計簿")

# Googleスプレッドシートへの接続
conn = st.connection("gsheets", type=GSheetsConnection)

# フォーム画面
with st.form("kakeibo_form"):
    date = st.date_input("日付")
    category = st.selectbox("カテゴリ", ["食費", "日用品", "交際費", "固定費", "その他"])
    amount = st.number_input("金額 (円)", min_value=0, step=100)
    user = st.radio("入力者", ["夫", "妻"], horizontal=True)
    memo = st.text_input("メモ")
    
    submitted = st.form_submit_button("支出を記録する")

if submitted:
    # 既存データの取得と追加
    data = conn.read()
    new_row = {"日付": str(date), "カテゴリ": category, "金額": amount, "入力者": user, "メモ": memo}
    updated_df = data.append(new_row, ignore_index=True)
    conn.update(data=updated_df)
    st.success("支出を記録しました！")

# 履歴表示
st.subheader("📋 支出履歴")
st.dataframe(conn.read())