import csv
import os

import requests

import ConvertInstagram
import GetInstagramVideoUrl
import HandleCsv
import HandleVideo

username = 'tgc_staff'
filename = f'{username}_video_links.csv'
collected_links = set()

if not os.path.exists(filename):
    # 获取Instagram分享链接
    collected_links = GetInstagramVideoUrl.get_video_url(username)
    HandleCsv.save_links_to_csv(collected_links, filename)

updated_rows = HandleCsv.get_updated_rows_from_csv(filename)
count = 1


try:
    for row in updated_rows:
        link = row[0]

        print("\n收集到的Instagram分享链接:")
        print(link)

        if row[1] == 'True':
            continue

        # 从分享链接中获取mp4链接
        mp4_links = ConvertInstagram.convert_instagram_video(link)

        if len(mp4_links) != 0:
            row[1] = 'True'

        # 打印所有的下载链接
        for mp4_link in mp4_links:
            print(mp4_link)

            try:
                video_data = requests.get(mp4_link).content
                with open(f"D:\\网赚\\ins视频\\{username}_{count}.mp4", "wb") as file:
                    file.write(video_data)
                print("视频下载完成！")

                count = count + 1
                row[1] = 'True'
            except Exception as e:
                print(f"下载失败: {e}")
finally:
    HandleCsv.update_csv(filename, updated_rows)

'''
# 视频拼接
file_directory = f"D:\\网赚\\ins视频\\"

video_groups = HandleVideo.video_grouping(file_directory)

for i, group in enumerate(video_groups):
    count = i + 1
    HandleVideo.concatenate_videos(group, f"D:\\网赚\\已处理视频\\final_output_video_{count}.mp4")
    print(f"第{count}组视频已处理完成")
'''
