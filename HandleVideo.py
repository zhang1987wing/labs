import os

from moviepy import *


def concatenate_videos(video_files, output_file):
    clips = []

    # 将所有视频文件加载到 clips 列表中
    for video_file in video_files:
        clip = VideoFileClip(video_file)
        clips.append(clip)

    # 给每个视频添加转场效果（例如渐隐渐现）
    transition_duration = 1  # 转场持续时间（秒）

    # 为每个视频添加转场效果
    clips_with_transitions = []
    for i, clip in enumerate(clips):
        if i > 0:  # 对每个视频之间添加转场效果（渐隐渐现）
            clip = clip.with_effects([vfx.FadeIn(transition_duration), vfx.FadeOut(transition_duration)])
        clips_with_transitions.append(clip)

    # 拼接视频
    final_clip = concatenate_videoclips(clips_with_transitions, method="compose")

    # 保存拼接后的视频
    final_clip.write_videofile(output_file, codec="libx264", fps=24)

    # 关闭文件以释放资源
    final_clip.close()


def video_grouping(video_folder, group_size):
    # 获取所有视频文件
    video_files = sorted(
        [os.path.join(video_folder, f) for f in os.listdir(video_folder) if f.endswith((".mp4", ".avi", ".mov"))],
        key=lambda x: int(x.split('_')[-1].split('.')[0])
        # Extract the number from the filename and convert it to an integer
    )

    video_groups = []

    # 每 3 个为一组处理
    for i in range(0, len(video_files), group_size):
        group = video_files[i:i + group_size]  # 取 group_size 个视频
        if len(group) < group_size:  # 避免最后不足 group_size 个的情况
            break

        video_groups.append(group)

    return video_groups


if __name__ == "__main__":
    file_directory = f"D:\\网赚\\ins视频\\dddddo0lllll"

    video_groups = video_grouping(file_directory, 2)

    for i, group in enumerate(video_groups):
        count = i + 1
        concatenate_videos(group, f"D:\\网赚\\已处理视频\\dddddo0lllll\\final_output_video_{count}.mp4")
        print(f"第{count}组视频已处理完成")
