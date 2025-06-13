import hashlib
import os

import requests


def householdAppliance_alert(plat_ssn):
    try:
        url = f"https://mkts.chinaums.com/jdhsApi/jdhs/user/category/coupon/get/unionpay_online/householdAppliance"
        payload = {
            "platSsn": f'{plat_ssn}',
            "userInfo": '68486B9EBA2ADC21DD59C4F6A303102C691C2256A4558CA0E0D162D38D14BC93BF7CD93BF9A8A48961CEC603C1628A7F1B'
                        'D3F3C7860F6772CDD098003AAF1C9970EC29E20FE5D345D0B2289E8D6196C8CAF367AC7AFC79B5DF29E9B4B10589EC45B1'
                        '993235897DD6FE155311F1C62625EB423F069015D5FFAFFB889C66151401A2CC261F4001343238B029AC5AFC2A397D6F76'
                        'D6B27B5895BB582BEFBD37CE30E19F36640F6FD17989F2FA21875B333D1834CBDD687F4BEF83DC0E950FE7323C9C050968'
                        'E8FFBD1F2A45E047DD3966DB5D098867B9E4FB1B1BE86820E86540460D92C7328613C2D45451E9198386C87E0AA46E6620'
                        'E1EC93BA343BC762217A63',
            "category": "COMPUTER"
        }
        headers = {"User-Agent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                                 'Chrome/137.0.0.0 Safari/537.36',
                   "Origin": 'https://mkts.chinaums.com',
                   "Referer": 'https://mkts.chinaums.com/hbjdhs-h5/index.html'
                   }

        response = requests.post(url, headers=headers, json=payload, verify=False)

        parse_data = response.json()
        return parse_data["respCode"]
    except Exception as e:
        print(f"接口异常, e")
        return 0


if __name__ == "__main__":
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
