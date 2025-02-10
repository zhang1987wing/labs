import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

# 设置 ChromeOptions
options = webdriver.ChromeOptions()
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("--headless")  # 无头模式
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-gpu")

# 启动 WebDriver
driver = webdriver.Chrome(options=options)

# 打开目标网页
driver.get("https://fastdl.app/zh/video")
time.sleep(5)

# 找到输入框并输入数据
search_input = driver.find_element(By.ID, "search-form-input")
search_input.send_keys("https://www.instagram.com/p/DFMF3CCKJFu/?igsh=MTgzcjl2aXE5NHgyYQ==")  # 输入一个示例视频链接

# 找到下载按钮并点击
download_button = driver.find_element(By.CLASS_NAME, "search-form__button")
download_button.click()
time.sleep(5)

# 等待并处理返回的响应
time.sleep(10)  # 等待一定时间，确保请求已经完成

# 查找所有符合条件的<a>标签
download_links = driver.find_elements(By.CSS_SELECTOR, "a.button.button--filled.button__download")

# 提取href属性
href_list = [link.get_attribute("href") for link in download_links]

# 打印所有的下载链接
for href in href_list:
    print(href)

# 关闭 WebDriver
driver.quit()

# if __name__ == "__main__":
#   print()
