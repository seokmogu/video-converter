#!/usr/bin/env python3
from screen_text_translator import ScreenTextTranslator
import os

# OpenAI API 키 설정 (환경변수에서 읽기)
api_key = os.getenv('OPENAI_API_KEY')
if not api_key:
    print("⚠️ OPENAI_API_KEY 환경변수를 설정해주세요.")
    print("export OPENAI_API_KEY=your_api_key_here")
    exit(1)

# 입력: 기존 음성 자막 포함 비디오
video_path = "/Users/smgu/test_code/video_converter/video_with_subtitles.mp4"
output_path = "/Users/smgu/test_code/video_converter/video_full_translated.mp4"

print("🚀 화면 텍스트 번역 시스템 시작")
print(f"입력: {video_path}")
print(f"출력: {output_path}")

# 번역기 실행 (15초 간격으로 화면 체크)
translator = ScreenTextTranslator(api_key)
result = translator.process_video_with_translation(
    video_path, 
    output_path, 
    interval_seconds=15  # 15초마다 화면 텍스트 확인
)

print(f"\n🎉 완전 번역 비디오 생성 완료!")
print(f"최종 파일: {result}")