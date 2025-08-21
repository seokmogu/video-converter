#!/usr/bin/env python3
import sys
import os
from pathlib import Path

# 현재 디렉토리를 Python 경로에 추가
sys.path.append(str(Path(__file__).parent))

from improved_subtitle_generator import ImprovedSubtitleGenerator
from improved_screen_translator import ImprovedScreenTextTranslator

def test_improved_system():
    """개선된 시스템 통합 테스트"""
    
    # OpenAI API 키 설정 (환경변수에서 읽기)
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("⚠️ OPENAI_API_KEY 환경변수를 설정해주세요.")
        print("export OPENAI_API_KEY=your_api_key_here")
        return
    
    # 원본 비디오 사용
    video_path = "/Users/smgu/test_code/video_converter/video.mov"
    
    # 테스트 구간 (30분~31분)
    start_time = 30 * 60  # 30분
    end_time = 31 * 60    # 31분
    
    print("🚀 개선된 통합 시스템 테스트 시작")
    print(f"📹 원본 파일: {video_path}")
    print(f"⏰ 테스트 구간: {start_time//60}분{start_time%60:02d}초 ~ {end_time//60}분{end_time%60:02d}초")
    print("="*80)
    
    # 1단계: 개선된 음성 자막 생성
    print("\n🎤 1단계: 개선된 음성 자막 생성")
    subtitle_generator = ImprovedSubtitleGenerator(api_key)
    subtitle_result = subtitle_generator.process_video_segment(
        video_path, 
        start_time=start_time, 
        end_time=end_time
    )
    print(f"✅ 음성 자막 완료: {subtitle_result}")
    
    # 2단계: 개선된 화면 텍스트 번역
    print("\n📺 2단계: 개선된 화면 텍스트 번역")
    # 음성 자막이 적용된 비디오를 입력으로 사용
    if str(subtitle_result).endswith('.mp4'):
        input_for_screen = subtitle_result
    else:
        input_for_screen = video_path
    
    screen_translator = ImprovedScreenTextTranslator(api_key)
    final_result = screen_translator.process_video_segment_improved(
        input_for_screen,
        "/Users/smgu/test_code/video_converter/video_complete_improved.mp4",
        start_time=start_time,
        end_time=end_time,
        interval_seconds=10
    )
    print(f"✅ 화면 번역 완료: {final_result}")
    
    print("\n🎉 통합 테스트 완료!")
    print(f"📁 최종 결과: {final_result}")
    print("\n개선사항:")
    print("✅ 음성 자막: 한국어만, 작은 폰트, 긴 자막 분할")
    print("✅ 화면 번역: 향상된 OCR, 더 많은 텍스트 감지, 작은 폰트")
    print("✅ 원본 화질: video.mov 사용으로 더 선명한 OCR")
    print("✅ 테스트 구간: 1분만 처리로 빠른 확인")

if __name__ == "__main__":
    test_improved_system()