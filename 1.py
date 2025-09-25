import json
import urllib.parse
import requests
import time
from datetime import datetime
import os

# 1. 要发送的 JSON 数据
data = {
    "trace": "edd5df80-df7f-4acf-8f67-68fd2f096426",
    "data": {
        "symbol_list": [
            {
                "code": "3690.HK"
            },
            {
                "code": "2015.HK"
            },
            {
                "code": "9618.HK"
            }
        ]
    }
}

# 2. 将 JSON 转为字符串并进行 URL Encode
query_str = json.dumps(data, separators=(',', ':'))  # 压缩格式，去掉空格
encoded_query = urllib.parse.quote(query_str)

# 3. 设置你的 token 和 API 地址
token = "6397d82a86c3c49e45ad58a08d4136da-c-app"  # 替换为你的实际 token
url = f"https://quote.alltick.io/quote-stock-b-api/trade-tick?token={token}&query={encoded_query}"

# 4. 全局变量
base_prices = {}  # 存储基准价格
previous_prices = {}  # 存储上一次的价格
log_file = "./stock_monitor.log"  # 日志文件名
alert_threshold = 1.5  # 预警阈值 1.5%

# 5. 写入日志文件的函数
def write_log(message):
    """写入日志到文件"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_message = f"[{timestamp}] {message}\n"
    
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(log_message)

# 6. 获取价格变化指示器的函数
def get_price_change_indicator(code, current_price):
    """获取与上一次价格比较的变化指示器"""
    if code not in previous_prices:
        # 第一次获取价格，设置为上一次价格
        previous_prices[code] = current_price
        return "(平)"  # 第一次显示为平
    
    prev_price = previous_prices[code]
    
    if current_price > prev_price:
        previous_prices[code] = current_price  # 更新上一次价格
        return "(涨)"
    elif current_price < prev_price:
        previous_prices[code] = current_price  # 更新上一次价格
        return "(跌)"
    else:
        return "(平)"

# 7. 检查价格变化的函数
def check_price_changes(stock_data):
    """检查价格变化并发出预警"""
    alerts = []
    
    for stock in stock_data:
        code = stock['code']
        current_price = float(stock['price'])
        
        # 如果是第一次获取价格，设置为基准价格
        if code not in base_prices:
            base_prices[code] = current_price
            write_log(f"设置基准价格 - {code}: {current_price}")
            continue
        
        # 计算涨跌幅
        base_price = base_prices[code]
        change_percent = ((current_price - base_price) / base_price) * 100
        
        # 检查是否超过预警阈值
        if abs(change_percent) >= alert_threshold:
            direction = "上涨" if change_percent > 0 else "下跌"
            alert_msg = f"⚠️ 预警: {code} {direction} {abs(change_percent):.2f}% (基准: {base_price}, 当前: {current_price})"
            alerts.append(alert_msg)
            write_log(alert_msg)
    
    return alerts

# 8. 发送 GET 请求的函数
def fetch_stock_data():
    headers = {
        'Accept': 'application/json'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()  # 检查 HTTP 错误

        result = [
            {
                'code': item['code'],
                'price': item['price']
            }
            for item in response.json()['data']['tick_list']
        ]

        # 打印结果，每个股票信息换行显示
        print("股票数据:")
        for stock in result:
            code = stock['code']
            current_price = float(stock['price'])
            
            # 获取价格变化指示器
            change_indicator = get_price_change_indicator(code, current_price)
            
            print(f"代码: {code}, 价格: {stock['price']} {change_indicator}")
        print("-" * 40)  # 分隔线
        
        # 写入日志
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        write_log(f"获取股票数据 - {len(result)} 只股票")
        for stock in result:
            write_log(f"  {stock['code']}: {stock['price']}")
        
        # 检查价格变化
        alerts = check_price_changes(result)
        if alerts:
            print("\n🚨 价格预警:")
            for alert in alerts:
                print(alert)
            print("-" * 40)
        
        return result

    except requests.exceptions.RequestException as e:
        error_msg = f"请求出错: {e}"
        print(error_msg)
        write_log(error_msg)
        return None

# 9. 主循环，每隔20秒调用一次
if __name__ == "__main__":
    print("开始监控股票数据，每隔20秒更新一次...")
    print(f"日志文件: {log_file}")
    print(f"预警阈值: {alert_threshold}%")
    print("按 Ctrl+C 停止程序")
    
    # 初始化日志文件
    write_log("=" * 50)
    write_log("股票监控程序启动")
    write_log(f"监控股票: {[item['code'] for item in data['data']['symbol_list']]}")
    write_log(f"预警阈值: {alert_threshold}%")
    write_log("=" * 50)
    
    try:
        while True:
            fetch_stock_data()
            time.sleep(20)  # 等待20秒
    except KeyboardInterrupt:
        print("\n程序已停止")
        write_log("程序正常停止")