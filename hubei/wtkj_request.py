from urllib.parse import urlparse, parse_qs

import requests


def queryCouponUrl(userId):
    try:
        url = f"https://gxhs.wtkj.site/dev-api/gxhs/front/ums/queryCouponUrl"
        payload = {
            "actType": "6",
            "custId": userId,
            "userId": userId
        }
        headers = {"User-Agent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                                 'Chrome/137.0.0.0 Safari/537.36',
                   "Referer": 'https://servicewechat.com/wxe48112dad392793a/187/page-frame.html',
                   "Content-Type": 'application/json'
                   }

        response = requests.post(url, headers=headers, json=payload, verify=False)

        if response.status_code == 200:
            parse_data = response.json()

            url_data = parse_data["data"]
            parsed_url = urlparse(url_data)
            query_string = parsed_url.fragment
            query_params = parse_qs(query_string)

            sign_value = query_params.get('/unionpayOnlineHome?sign')
            if sign_value:
                return sign_value[0]  # 返回列表中的第一个值
            else:
                return None

    except Exception as e:
        print(f"接口异常, e")
        return None


if __name__ == "__main__":
    print(queryCouponUrl('r44iUPJpas'))
