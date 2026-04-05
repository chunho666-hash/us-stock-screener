import yfinance as yf
import pandas as pd
import requests
import os

# 配置多組 TG 帳號 (Token, Chat_ID)
# 格式：(Token, Chat_ID)
TG_ACCOUNTS = [
    ("8718386024:AAFF520JcpqPKkzjeFFojXDvdpXbmbxIn7I", "5116324274"),    # 原有帳號
    ("8623901579:AAG_eUeYml-9G08wE13-LaqXNRF5c7Ishpw", "7665455868"),    # 新加帳號 1
    ("8637220062:AAE33UjhpIgl1Lvpuf8VMACdPot9haUaWcU", "829255337")     # 新加帳號 2
]

def send_to_all_tg(text):
    """循環發送訊息俾所有設定咗嘅 TG 帳號"""
    for token, chat_id in TG_ACCOUNTS:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
        try:
            requests.post(url, data=payload, timeout=10)
            print(f"成功發送至 Chat ID: {chat_id}")
        except Exception as e:
            print(f"發送至 {chat_id} 失敗: {e}")

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
    if not tickers: return
    
    found = []
    scanned_count = 0
    sample_check = []

    print(f"開始掃描 {len(tickers)} 隻股票...")
    for t in tickers:
        try:
            df = yf.download(t, period="40d", interval="1d", progress=False)
            if len(df) < 30: continue
            
            scanned_count += 1
            if len(sample_check) < 3: sample_check.append(t)

            df['E5'] = df['Close'].ewm(span=5, adjust=False).mean()
            df['E13'] = df['Close'].ewm(span=13, adjust=False).mean()
            df['E30'] = df['Close'].ewm(span=30, adjust=False).mean()
            
            curr, prev = df.iloc[-1], df.iloc[-2]
            
            # 指標條件：價 > 80, 5穿13, 都在30之上
            cond = (curr['Close'] > 80) and (prev['E5'] <= prev['E13'] and curr['E5'] > curr['E13']) and (curr['E5'] > curr['E30'] and curr['E13'] > curr['E30'])
            
            if cond:
                found.append(f"🎯 *{t}* - ${curr['Close']:.2f}")
        except: continue
    
    # 建立報告
    header = f"📊 **收市掃描報告 (共檢查 {scanned_count} 隻)**\n"
    if found:
        full_msg = header + "🚀 **符合 EMA 5-13-30 交叉：**\n" + "\n".join(found)
    else:
        proof = ", ".join(sample_check)
        full_msg = header + f"✅ 今日暫無符合條件股票。\n(抽樣檢查：{proof} ... 均未達標)"
    
    # 全體推送
    send_to_all_tg(full_msg)

if __name__ == "__main__":
    scan()
