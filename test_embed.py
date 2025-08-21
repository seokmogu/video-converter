#!/usr/bin/env python3
from subtitle_generator import SubtitleGenerator

# 기존 파일들로 자막 삽입만 테스트
video_path = "/Users/smgu/test_code/video_converter/video_compressed.mp4"
srt_path = "/Users/smgu/test_code/video_converter/video_compressed_subtitles.srt"
output_path = "/Users/smgu/test_code/video_converter/video_with_subtitles.mp4"

print("🚀 자막 삽입 테스트 시작")
print(f"비디오: {video_path}")
print(f"자막: {srt_path}")
print(f"출력: {output_path}")

generator = SubtitleGenerator()
success = generator.embed_subtitles_to_video(video_path, srt_path, output_path)

if success:
    print("\n🎉 자막 삽입 완료!")
else:
    print("\n❌ 자막 삽입 실패")