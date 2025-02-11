from moviepy import *


def concatenate_videos(video_files):

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
    final_clip.write_videofile("D:\\网赚\\待发布的视频\\final_output_video.mp4", codec="libx264", fps=24)

    # 关闭文件以释放资源
    final_clip.close()


if __name__ == "__main__":
    file_directory = f"D:\\网赚\\ins视频\\"
    concatenate_videos([file_directory + "catt.worldd_4.mp4",
                        file_directory + "catt.worldd_5.mp4",
                        file_directory + "catt.worldd_6.mp4"])
