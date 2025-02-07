import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

# Instagram 账号信息
USERNAME = "zhang1987wing"
PASSWORD = "woai1987instagram"

# 要下载的 Instagram 视频链接
VIDEO_URL = "https://www.instagram.com/p/DFMF3CCKJFu/?igsh=MTgzcjl2aXE5NHgyYQ=="

# 配置 Selenium WebDriver
options = webdriver.ChromeOptions()
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("--headless")  # 无头模式（可选）
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-gpu")
options.set_capability("goog:loggingPrefs", {"performance": "ALL"})  # 启用性能日志

# 启动 WebDriver
driver = webdriver.Chrome(options=options)

# 访问 Instagram 登录页面
driver.get("https://www.instagram.com/accounts/login/")
time.sleep(5)

# 登录 Instagram
driver.find_element(By.NAME, "username").send_keys(USERNAME)
driver.find_element(By.NAME, "password").send_keys(PASSWORD)
driver.find_element(By.NAME, "password").send_keys(Keys.RETURN)
time.sleep(10)

# 打开视频页面
driver.get(VIDEO_URL)
time.sleep(5)

# 获取 Chrome DevTools 网络日志
logs = driver.get_log("performance")
video_url = None

# 解析日志，提取 MP4 视频链接
for log in logs:
    message = log["message"]
    if "video/mp4" in message and "url" in message:
        start = message.find("url") + 6  # 获取 URL 开头
        end = message.find('"', start)  # 获取 URL 结尾
        video_url = message[start:end]
        break

if video_url:
    print("真实视频链接：", video_url)

    # 下载视频
    video_data = requests.get(video_url).content
    with open("instagram_video.mp4", "wb") as file:
        file.write(video_data)

    print("视频下载完成！")
else:
    print("获取视频失败")

# 关闭 WebDriver
driver.quit()


#https://fastdl.app/zh/video
#https://fastdl.app/api/convert
#{"url":"https://www.instagram.com/p/DFMF3CCKJFu/?igsh=MTgzcjl2aXE5NHgyYQ==","ts":1738930457257,"_ts":1738233115775,"_tsc":70649,"_s":"d8b9ec21c53ff3c5315265f19b5f0e2b1267febfbd7c2cc7ac72859ad4ea0935"}