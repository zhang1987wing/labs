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

    # 获取所有 a 标签
    elements = driver.find_elements(By.TAG_NAME, "a")

    # 过滤出符合 "/catt.worldd/p/" 结构的 href
    for elem in elements:
        href = elem.get_attribute("href")
        if href and href.startswith(f"https://www.instagram.com/{username}/p/"):
            post_id = href.split("/p/")[1].split("/")[0]
            collected_links.add(f"https://www.instagram.com/p/{post_id}/")

    # 关闭 WebDriver
    driver.quit()

    return collected_links

if __name__ == "__main__":
   get_video_url('catt.worldd')