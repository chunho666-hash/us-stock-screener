import yfinance as yf
import pandas as pd
import requests
import os

# --- 設定區：三個 Bot 的資訊 ---
# 這裡填入你提供的 Token 和 Chat ID
BOT_LIST = [
    ("8718386024:AAFF520JcpqPKkzjeFFojXDvdpXbmbxIn7I", "5116324274"),
    ("8623901579:AAG_eUeYml-9G08wE13-LaqXNRF5c7Ishpw", "7665455868"),
    ("8637220062:AAE33UjhpIgl1Lvpuf8VMACdPot9haUaWcU", "829255337")
]

def send_to_all_bots(text):
    """將訊息同步發送至所有設定好的 Telegram Bot"""
    for token, chat_id in BOT_LIST:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            "chat_id": chat_id, 
            "text": text, 
            "parse_mode": "Markdown"
        }
        try:
            requests.post(url, data=payload, timeout=15)
        except Exception as e:
            print(f"發送至 {chat_id} 失敗: {e}")

def get_tickers():
    """獲取美股主要成分股名單 (S&P 500 + Nasdaq 100)"""
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        sp5_url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
        sp500 = pd.read_html(requests.get(sp5_url, headers=headers).text)[0]['Symbol'].tolist()
        nd100_url = 'https://en.wikipedia.org/wiki/Nasdaq-100'
        nasdaq100 = pd.read_html(requests.get(nd100_url, headers=headers).text)[4]['Ticker'].tolist()
        # 移除重複並轉換格式 (例如將 BRK.B 轉為 BRK-B 以符合 yfinance)
        return [t.replace('.', '-') for t in list(set(sp500 + nasdaq100))]
    except: return []

def scan():
    tickers = get_tickers()
    buy_list = []    # 🚀 買入清單
    warn_list = []   # ⚠️ 警示清單
    drop_list = []   # 🚨 破位清單
    
    print(f"開始掃描 {len(tickers)} 隻股票...")
    
    for t in tickers:
        try:
            # 抓取 40 天數據以計算 EMA
            df = yf.download(t, period="40d", interval="1d", progress=False)
            if len(df) < 31: continue
            
            # 計算核心均線
            df['E5'] = df['Close'].ewm(span=5, adjust=False).mean()
            df['E13'] = df['Close'].ewm(span=13, adjust=False).mean()
            df['E15'] = df['Close'].ewm(span=15, adjust=False).mean()
            df['E30'] = df['Close'].ewm(span=30, adjust=False).mean()
            
            curr, prev = df.iloc[-1], df.iloc[-2]
            price = curr['Close']

            # --- 🚀 買入邏輯: 5 穿上 15 且 5,15 皆在 30 之上 ---
            if (prev['E5'] <= prev['E15'] and curr['E5'] > curr['E15']) and \
               (curr['E5'] > curr['E30'] and curr['E15'] > curr['E30']) and (price > 80):
                buy_list.append(f"🚀 *{t}* - ${price:.2f}")
                continue # 避免重複加入

            # --- ⚠️ 警示邏輯: 5 穿下 13 且 5,13 皆在 30 之上 (高位回調) ---
            if (prev['E5'] >= prev['E13'] and curr['E5'] < curr['E13']) and \
               (curr['E5'] > curr['E30'] and curr['E13'] > curr['E30']):
                warn_list.append(f"⚠️ *{t}* - ${price:.2f}")

            # --- 🚨 破位邏輯: 5 穿下 13 且 5,13 皆在 30 之下 (趨勢轉壞) ---
            elif (prev['E5'] >= prev['E13'] and curr['E5'] < curr['E13']) and \
                 (curr['E5'] < curr['E30'] and curr['E13'] < curr['E30']):
                drop_list.append(f"🚨 *{t}* - ${price:.2f}")
                
        except Exception as e:
            print(f"跳過 {t}: {e}")
            continue
    
    # 建立最終報告
    msg = "📊 **EMA 5-13/15-30 雙向選股報告**\n\n"
    
    msg += "🔥 **【買入訊號】(突破強勢)**\n"
    msg += (("\n".join(buy_list)) if buy_list else "暫無符合") + "\n\n"
    
    msg += "🟡 **【回調警示】(5穿下13 且 在30上)**\n"
    msg += (("\n".join(warn_list)) if warn_list else "暫無符合") + "\n\n"
    
    msg += "🔴 **【趨勢破位】(5穿下13 且 在30下)**\n"
    msg += (("\n".join(drop_list)) if drop_list else "暫無符合")
    
    send_to_all_bots(msg)

if __name__ == "__main__":
    scan()
