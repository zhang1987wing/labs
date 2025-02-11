import requests

import ConvertInstagram
import GetInstagramVideoUrl
import HandleVideo

username = 'catt.worldd'

# 获取Instagram分享链接
collected_links = GetInstagramVideoUrl.get_video_url(username)
count = 1

for link in collected_links:
    print("\n收集到的Instagram分享链接:")
    print(link)

    # 从分享链接中获取mp4链接
    mp4_links = ConvertInstagram.convert_instagram_video(link)

    # 打印所有的下载链接
    for mp4_link in mp4_links:
        print(mp4_link)

        try:
            video_data = requests.get(mp4_link).content
            with open(f"{username}_{count}.mp4", "wb") as file:
                file.write(video_data)
            print("视频下载完成！")

            count = count + 1
        except Exception as e:
            print(f"下载失败: {e}")

# 视频拼接
HandleVideo.concatenate_videos(["catt.worldd_17.mp4", "catt.worldd_18.mp4", "catt.worldd_19.mp4"])