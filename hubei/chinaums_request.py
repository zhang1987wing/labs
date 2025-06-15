import hashlib
import os
import threading
import time

import requests
import schedule


def householdAppliance_alert(plat_ssn):
    try:
        url = f"https:/jdhsApi/jdhs/user/category/coupon/get/unionpay_online/householdAppliance"
        payload = {
            "platSsn": f'{plat_ssn}',
            "userInfo": '568099BE25B7A8A713CAABD20EB204059F8073E66BD415F9376492E93F7B9AC09F454A7B6417A27E035E0901658A1B23F234292EE054C3DB24721172F538CC91E62F8B3A587F65D5163DE8CF3A4890C34115D39AB6CE75C206DE430BC972030338FF121F2F102EB83F46AA44C16E8DE40B07BBB3FF721A2F34122462BD4812EA9832A846848F784EBF1B649C7810F097BB4C99C9680B11AB9501B89716DB6420DFFB5594A9C9AA96B1753B7CF877CF4F89544B4995FBDC5F76347DC7306732FA59CB8936B78CEF45265435A3FE0CD7927CF0724431FE0877CC4460876B31B86192C17A265E7BB6AC30FE9682C39E6A6BC20F63481AEC5E5A870F5B65961553B3',
            "category": "COMPUTER"
        }
        headers = {"User-Agent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                                 'Chrome/137.0.0.0 Safari/537.36',
                   "Origin": 'https://mkts.chinaums.com',
                   "Referer": 'https://mkts.chinaums.com/hbjdhs-h5/index.html'
                   }

        response = requests.post(url, headers=headers, json=payload, verify=False, timeout=10)

        parse_data = response.json()
        return parse_data["respCode"]
    except Exception as e:
        print(f"接口异常, e")
        return 0


def worker(thread_id):
    random_bytes_2 = os.urandom(32)
    md5_hash = hashlib.md5(random_bytes_2)
    hex_digest = md5_hash.hexdigest()

    success = True
    count = 1

    while success:
        result = householdAppliance_alert(hex_digest)
        print(f'第{count}次调用结果: {result}')

        if result == 1102:
            success = True

        count = count + 1


def main():
    # 设置线程数量
    num_threads = 5

    # 创建并启动线程
    threads = []
    for i in range(num_threads):
        t = threading.Thread(target=worker, args=(i + 1,))
        threads.append(t)
        t.start()

    # 等待所有线程完成
    for t in threads:
        t.join()


if __name__ == "__main__":
    schedule.every().day.at("09:58").do(main)

    print("等待执行指定时间任务...")
    while True:
        schedule.run_pending()
        time.sleep(1)