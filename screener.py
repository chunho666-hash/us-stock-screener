import yfinance as yf
import pandas as pd
import requests
import os
import random

TG_TOKEN = os.getenv("TG_TOKEN")
CHAT_ID = os.getenv("TG_CHAT_ID")

def send_telegram_msg(text):
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}
    requests.post(url, data=payload)

def get_tickers():
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        sp5_url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
        sp500 = pd.read_html(requests.get(sp5_url, headers=headers).text)[0]['Symbol'].tolist()
        nd100_url = 'https://en.wikipedia.org/wiki/Nasdaq-100'
        nasdaq100 = pd.read_html(requests.get(nd100_url, headers=headers).text)[4]['Ticker'].tolist()
        return [t.replace('.', '-') for t in list(set(sp500 + nasdaq100))]
    except: return []

def scan():
    tickers = get_tickers()
    found = []
    scanned_count = 0
    sample_check = [] # 用嚟做測試證明

    for t in tickers:
        try:
            df = yf.download(t, period="40d", interval="1d", progress=False)
            if len(df) < 30: continue
            
            scanned_count += 1
            # 隨機抽樣 3 隻做「工作證明」
            if len(sample_check) < 3: sample_check.append(t)

            df['E5'] = df['Close'].ewm(span=5, adjust=False).mean()
            df['E13'] = df['Close'].ewm(span=13, adjust=False).mean()
            df['E30'] = df['Close'].ewm(span=30, adjust=False).mean()
            
            curr, prev = df.iloc[-1], df.iloc[-2]
            
            # 指標判斷
            cond = (curr['Close'] > 80) and (prev['E5'] <= prev['E13'] and curr['E5'] > curr['E13']) and (curr['E5'] > curr['E30'] and curr['E13'] > curr['E30'])
            
            if cond:
                found.append(f"🎯 *{t}* - ${curr['Close']:.2f}")
        except: continue
    
    # 建立回報訊息
    report_header = f"📊 **掃描完畢 (共檢查 {scanned_count} 隻)**\n"
    if found:
        send_telegram_msg(report_header + "🚀 **符合指標目標：**\n" + "\n".join(found))
    else:
        # 如果冇符合，隨機顯示幾隻佢睇過嘅股作為證明
        proof = ", ".join(sample_check)
        send_telegram_msg(report_header + f"✅ 今日暫無符合條件股票。\n(已抽樣檢查：{proof} ... 等股票均未達標)")

if __name__ == "__main__":
    scan()
