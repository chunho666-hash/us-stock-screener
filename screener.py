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
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print(f"Telegram 發送失敗: {e}")

def get_tickers():
    # 加入 User-Agent 偽裝成瀏覽器，解決 403 Forbidden 問題
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    
    try:
        # 抓取 S&P 500
        sp5_url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
        response_sp5 = requests.get(sp5_url, headers=headers)
        sp500 = pd.read_html(response_sp5.text)[0]['Symbol'].tolist()
        
        # 抓取 Nasdaq 100
        nd100_url = 'https://en.wikipedia.org/wiki/Nasdaq-100'
        response_nd100 = requests.get(nd100_url, headers=headers)
        nasdaq100 = pd.read_html(response_nd100.text)[4]['Ticker'].tolist()
        
        full_list = list(set(sp500 + nasdaq100))
        return [t.replace('.', '-') for t in full_list]
    except Exception as e:
        print(f"獲取清單失敗: {e}")
        return []

def scan():
    tickers = get_tickers()
    if not tickers:
        send_telegram_msg("⚠️ 獲取股票清單失敗，請檢查代碼。")
        return

    found = []
    print(f"開始掃描 {len(tickers)} 隻股票...")
    
    for t in tickers:
        try:
            # 獲取數據
            df = yf.download(t, period="60d", interval="1d", progress=False)
            if len(df) < 30: continue
            
            # 計算 EMA
            df['E5'] = df['Close'].ewm(span=5, adjust=False).mean()
            df['E13'] = df['Close'].ewm(span=13, adjust=False).mean()
            df['E30'] = df['Close'].ewm(span=30, adjust=False).mean()
            
            curr, prev = df.iloc[-1], df.iloc[-2]
            
            # 1. 價格 > 80
            # 2. EMA 5 穿 13 (昨日 5<=13, 今日 5>13)
            # 3. 5, 13 都在 30 之上
            price_cond = curr['Close'] > 80
            crossover = (prev['E5'] <= prev['E13']) and (curr['E5'] > curr['E13'])
            above_30 = (curr['E5'] > curr['E30']) and (curr['E13'] > curr['E30'])
            
            if price_cond and crossover and above_30:
                found.append(f"🎯 *{t}* - ${curr['Close']:.2f}")
                print(f"命中目標: {t}")
        except:
            continue
    
    if found:
        send_telegram_msg("🚀 **EMA 5-13-30 篩選報告**\n\n" + "\n".join(found))
    else:
        # 為了確認程式有在跑，可以發個訊息，或者保持安靜
        send_telegram_msg("📊 今日掃描完畢：暫無符合條件股票。")

if __name__ == "__main__":
    scan()
