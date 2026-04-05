import yfinance as yf
import pandas as pd
import requests
import os

# --- 設定區：三個 Bot 的資訊 ---
BOT_LIST = [
    ("8718386024:AAFF520JcpqPKkzjeFFojXDvdpXbmbxIn7I", "5116324274"),
    ("8623901579:AAG_eUeYml-9G08wE13-LaqXNRF5c7Ishpw", "7665455868"),
    ("8637220062:AAE33UjhpIgl1Lvpuf8VMACdPot9haUaWcU", "829255337")
]

def send_to_all_bots(text):
    for token, chat_id in BOT_LIST:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
        try:
            requests.post(url, data=payload, timeout=10)
        except: continue

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
    buy_list = []   # 🚀 連續向上貫穿
    drop_list = []  # 🚨 連續向下貫穿
    
    print(f"開始掃描 {len(tickers)} 隻股票...")
    
    for t in tickers:
        try:
            # 抓取 40 天數據計算 EMA
            df = yf.download(t, period="40d", interval="1d", progress=False)
            if len(df) < 30: continue
            
            df['E5'] = df['Close'].ewm(span=5, adjust=False).mean()
            df['E13'] = df['Close'].ewm(span=13, adjust=False).mean()
            df['E30'] = df['Close'].ewm(span=30, adjust=False).mean()
            
            curr, prev = df.iloc[-1], df.iloc[-2]
            
            # --- 🚀 邏輯 1: 連續向上貫穿 (Long) ---
            # 條件：今日 5日線 穿過 30日線，且此時 5日線 已經在 13日線 之上
            buy_cond = (curr['Close'] > 80) and \
                       (prev['E5'] <= prev['E30'] and curr['E5'] > curr['E30']) and \
                       (curr['E5'] > curr['E13'])
            
            # --- 🚨 邏輯 2: 連續向下貫穿 (Drop) ---
            # 條件：今日 5日線 跌穿 30日線，且此時 5日線 已經在 13日線 之下
            drop_cond = (prev['E5'] >= prev['E30'] and curr['E5'] < curr['E30']) and \
                        (curr['E5'] < curr['E13'])

            if buy_cond:
                buy_list.append(f"🚀 *{t}* - ${curr['Close']:.2f}")
            elif drop_cond:
                drop_list.append(f"🚨 *{t}* - ${curr['Close']:.2f}")
        except: continue
    
    # 建立合併報告
    msg = "📊 **EMA 5-13-30 連續貫穿報告**\n\n"
    
    msg += "🔥 **【向上貫穿 - 強勢起步】**\n"
    msg += (("\n".join(buy_list)) if buy_list else "暫無符合") + "\n\n"
    
    msg += "🩸 **【向下貫穿 - 趨勢轉壞】**\n"
    msg += (("\n".join(drop_list)) if drop_list else "暫無符合")
    
    send_to_all_bots(msg)

if __name__ == "__main__":
    scan()
