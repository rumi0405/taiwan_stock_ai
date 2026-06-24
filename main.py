import os
import datetime
import yfinance as yf
import pandas as pd
import google.generativeai as genai

# ==================== 1. 設定區 ====================
STOCK_LIST = ["3481.TW", "2409.TW", "2327.TW", "2408.TW"]

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

def analyze_taiwan_stock(stock_id):
    print(f"正在抓取 {stock_id} 的 Yahoo 財經數據...")
    ticker = yf.Ticker(stock_id)
    df = ticker.history(period="60d")
    
    if df.empty:
        return None
        
    df['MA5'] = df['Close'].rolling(window=5).mean()
    df['MA10'] = df['Close'].rolling(window=10).mean()
    df['MA20'] = df['Close'].rolling(window=20).mean()
    df['std'] = df['Close'].rolling(window=20).std()
    df['BB_Upper'] = df['MA20'] + (df['std'] * 2)
    df['BB_Lower'] = df['MA20'] - (df['std'] * 2)
    
    today_data = df.iloc[-1]
    current_price = round(today_data['Close'], 2)
    ma5 = round(today_data['MA5'], 2)
    ma10 = round(today_data['MA10'], 2)
    ma20 = round(today_data['MA20'], 2)
    bb_upper = round(today_data['BB_Upper'], 2)
    bb_lower = round(today_data['BB_Lower'], 2)
    volume = int(today_data['Volume'])
    recent_max = round(df['High'].tail(10).max(), 2)
    recent_min = round(df['Low'].tail(10).min(), 2)

    prompt = f"""
    你是一位精通台灣股市的資深投資專家。請針對以下提供的真實盤後數據，進行深度的邏輯思考與策略分析。
    個股代號: {stock_id}
    今日收盤價: {current_price} 元
    今日成交量: {volume} 股
    均線系統: MA5={ma5}, MA10={ma10}, MA20={ma20}
    布林通道: 上軌={bb_upper}, 中軌={ma20}, 下軌={bb_lower}
    近期結構高低點 (參考值): 近期壓力參考={recent_max}, 近期支撐參考={recent_min}
    
    請嚴格依據上述數據，提供以下內容的繁體中文分析報告：
    1. 【K線型態與布林通道解讀】：分析目前價格處於布林通道的什麼位置（例如縮口突破、觸及上下軌等），以及均線排列狀態。
    2. 【實質壓力與支撐位研判】：結合布林通道與結構高低點，精確給出實質的壓力位與支撐位預測。
    3. 【籌碼與資金流向推論】：從今日量價表現與型態，推論主力目前的資金動向（吸籌震盪、高檔調節或洗盤）。
    4. 【關鍵風險提示】：列出短中期操作該個股的潛在風險，並給予明確的操作檢查清單。
    """
    model = genai.GenerativeModel('gemini-2.5-flash')
    response = model.generate_content(prompt)
    return response.text

# ==================== 主程式執行 ====================
if __name__ == "__main__":
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    final_report = f"# 🎯 {today_str} 台股 AI 盤後決策報告\n\n"
    
    for stock in STOCK_LIST:
        try:
            report = analyze_taiwan_stock(stock)
            if report:
                final_report += f"## 📈 個股分析: {stock}\n" + report + "\n\n---\n\n"
        except Exception as e:
            print(f"分析 {stock} 時發生錯誤: {e}")
            
    with open(f"report_{today_str}.md", "w", encoding="utf-8") as f:
        f.write(final_report)
    print("🎉 本地檔案生成完畢！")
