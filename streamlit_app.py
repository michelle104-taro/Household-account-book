import streamlit as st
import pandas as pd

# ページ設定
st.set_page_config(page_title="我が家の家計簿", page_icon="💰", layout="centered")
st.title("💰 夫婦共有の家計簿")

# ==========================================
# 1. Googleフォームのリンクを設置（ここで入力してもらう）
# ==========================================
st.markdown("### ✍️ 支出の入力はこちら")
# ※ ここに後で作成したGoogleフォームのURLを入れてね！
form_url = "https://forms.google.com/..." 
st.markdown(f"[＞＞ 支出入力フォームを開く]({form_url})")

st.divider()

# ==========================================
# 2. スプレッドシートの読み込み（Secrets不要！）
# ==========================================
st.markdown("### 📋 最新の支出履歴")

# 教えてくれたスプレッドシートのIDを使って、CSVダウンロード用のURLに変換
# なぜそうなるのか？： pandasが直接読み込めるのは画面ではなくCSVデータだからだよ！
SHEET_ID = "1-HoWSwmqq53N3xiyPty_O5JzX_o-dLzL2EElwMqSnMY"
csv_url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

try:
    # データを読み込む
    df = pd.read_csv(csv_url)
    
    # データが空じゃない場合、表として表示
    if not df.empty:
        # 最新の入力が上に来るように逆順にする
        st.dataframe(df.iloc[::-1], use_container_width=True)
    else:
        st.info("まだデータがありません。")

except Exception as e:
    st.error("スプレッドシートの読み込みに失敗しました。")
    st.error("スプレッドシートの共有設定が「リンクを知っている全員（閲覧者）」になっているか確認してね！")