import os
import datetime
import time  # 確保引入時間模組
import yfinance as yf
import pandas as pd
import google.generativeai as genai

# ==================== 1. 設定區 ====================
STOCK_LIST = ["3481.TW", "2327.TW"]

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

def analyze_taiwan_stock(stock_id):
    print(f"正在抓取 {stock_id} 的 Yahoo 財經數據...")
    ticker = yf.Ticker(stock_id)
    df = ticker.history(period="60d")
    
    if df.empty:
        print(f"❌ 無法取得 {stock_id} 的數據")
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
    你是一位精通台灣股市的資深投資專家。請針對以下提供的真實盤後數據，進行深度的邏輯思考。
    
    個股代號: {stock_id}
    今日收盤價: {current_price} 元
    今日成交量: {volume} 股
    均線系統: MA5={ma5}, MA10={ma10}, MA20={ma20}
    布林通道: 上軌={bb_upper}, 中軌={ma20}, 下軌={bb_lower}
    近期結構高低點 (參考值): 壓力={recent_max}, 支撐={recent_min}
    
    請嚴格依據上述數據，產出一份「排版極度簡潔、視覺化、適合手機快速閱讀」的繁體中文盤後報告。
    ⚠️ 排版嚴格要求：
    1. 大量使用適當的 Emoji 增加生動感（如 📈, 📉, 🔥, 💰, 🛑, 💡 等）。
    2. 廢話少說，結論先行，每一點說明請控制在 1-2 句話以內，絕對不要長篇大論。
    3. 壓力與支撐位請「務必使用 Markdown 表格」呈現，讓讀者一目了然。

    請依序提供以下四大板塊：
    ### 📊 【核心趨勢短評】
    (用最精簡的一段話，總結目前 K 線與布林通道的位階，以及均線的多空狀態)

    ### 🎯 【關鍵價位防守區】
    (請直接產出 Markdown 表格，包含「關卡屬性(如:短線壓力)」、「價位」、「觀察重點」三欄，並列出最重要的 2-3 個壓力與支撐位)

    ### 💰 【籌碼與主力動向】
    (用條列式簡述今日量價關係背後的主力意圖，如：強勢吸籌、高檔換手、刻意洗盤等)

    ### 🛑 【操作策略與風險警示】
    (給予具體的操作建議與停損/停利觀察點，條列 2-3 點即可，明確且果斷)
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
            
            print("為了防止 API 流量超限，冷卻 10 秒鐘...")
            time.sleep(10)
            
        except Exception as e:
            print(f"分析 {stock} 時發生錯誤: {e}")
            
    # 固定存成一個名字叫做 report.html 的檔案，方便寄信外掛直接讀取內文
    # 我們順便把換行改成網頁看的 HTML 換行格式 <br>
    html_content = final_report.replace("\n", "<br>")
    with open("report.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    print("🎉 本地 HTML 檔案生成完畢！")
