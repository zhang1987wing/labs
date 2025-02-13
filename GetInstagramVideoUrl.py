import csv
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys


def get_video_url(username):
    # Instagram 账号信息
    login_name = "zhang1987wing"
    login_password = "woai1987instagram"

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

    try:

        # 访问 Instagram 登录页面
        driver.get("https://www.instagram.com/accounts/login/")
        time.sleep(5)

        # 登录 Instagram
        driver.find_element(By.NAME, "username").send_keys(login_name)
        driver.find_element(By.NAME, "password").send_keys(login_password)
        driver.find_element(By.NAME, "password").send_keys(Keys.RETURN)
        time.sleep(10)

        # 博主主页
        driver.get(f'https://www.instagram.com/{username}/')
        time.sleep(5)

        # 存储 href 结果
        collected_links = set()

        # 滚动页面直到加载所有帖子
        last_height = driver.execute_script("return document.body.scrollHeight")
        # 翻页次数
        page = 1

        while page < 21:
            # 获取页面中所有的视频链接
            elements = driver.find_elements(By.TAG_NAME, "a")
            for elem in elements:
                href = elem.get_attribute("href")
                if href:
                    if href.startswith(f"https://www.instagram.com/{username}/p/"):
                        post_id = href.split("/p/")[1].split("/")[0]
                        collected_links.add(f"https://www.instagram.com/p/{post_id}/")
                    elif href.startswith(f"https://www.instagram.com/{username}/reel/"):
                        post_id = href.split("/reel/")[1].split("/")[0]
                        collected_links.add(f"https://www.instagram.com/reel/{post_id}/")

            # 滚动页面到底部
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)  # 等待页面加载更多内容

            # 获取新的页面高度
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:  # 如果页面高度没有变化，说明已经加载完所有内容
                break
            last_height = new_height
            page = page + 1

        return collected_links

    finally:
        # 关闭 WebDriver
        driver.quit()


if __name__ == "__main__":
    collected_links = get_video_url('tgc_staff')
