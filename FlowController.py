import ConvertInstagram
import GetInstagramVideoUrl

collected_links = GetInstagramVideoUrl.get_video_url('catt.worldd')

# 获取视频链接
print("\n收集到的链接:")
for link in collected_links:
    print(link)
    ConvertInstagram.convert_instagram_video(link)
