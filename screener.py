import yfinance as yf
import pandas as pd
import requests
import os

# 從 GitHub Secrets 讀取
TG_TOKEN = os.getenv("TG_TOKEN")
CHAT_ID = os.getenv("TG_CHAT_ID")

def send_telegram_msg(text):
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}
    requests.post(url, data=payload)

def get_tickers():
    sp500 = pd.read_html('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')[0]['Symbol'].tolist()
    nasdaq100 = pd.read_html('https://en.wikipedia.org/wiki/Nasdaq-100')[4]['Ticker'].tolist()
    full_list = list(set(sp500 + nasdaq100))
    return [t.replace('.', '-') for t in full_list]

def scan():
    tickers = get_tickers()
    found = []
    for t in tickers:
        try:
            df = yf.download(t, period="60d", interval="1d", progress=False)
            if len(df) < 30: continue
            df['E5'] = df['Close'].ewm(span=5).mean()
            df['E13'] = df['Close'].ewm(span=13).mean()
            df['E30'] = df['Close'].ewm(span=30).mean()
            curr, prev = df.iloc[-1], df.iloc[-2]
            
            # 你的指標邏輯
            if curr['Close'] > 80 and (prev['E5'] <= prev['E13'] and curr['E5'] > curr['E13']) and (curr['E5'] > curr['E30'] and curr['E13'] > curr['E30']):
                found.append(f"🎯 *{t}* - ${curr['Close']:.2f}")
        except: continue
    
    if found:
        send_telegram_msg("🚀 **EMA 5-13-30 篩選報告**\n\n" + "\n".join(found))
    else:
        send_telegram_msg("📊 今日掃描完畢：暫無符合條件股票。")

if __name__ == "__main__":
    scan()
