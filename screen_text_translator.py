#!/usr/bin/env python3
import cv2
import easyocr
import openai
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import os
from pathlib import Path
import json
import time

class ScreenTextTranslator:
    def __init__(self, openai_api_key=None, source_language=None, target_language=None, ocr_languages=None):
        print("🔧 OCR 및 번역 시스템 초기화 중...")
        
        # 언어 설정 (환경변수에서 기본값 읽기)
        self.source_language = source_language or os.getenv('SOURCE_LANGUAGE', 'ja')
        self.target_language = target_language or os.getenv('TARGET_LANGUAGE', 'Korean')
        
        # OCR 언어 설정
        ocr_lang_str = ocr_languages or os.getenv('OCR_LANGUAGES', 'ja,en')
        ocr_lang_list = [lang.strip() for lang in ocr_lang_str.split(',')]
        
        # OCR 초기화
        self.ocr_reader = easyocr.Reader(ocr_lang_list)
        print(f"✅ EasyOCR 초기화 완료: {ocr_lang_list}")
        
        # OpenAI 설정
        if openai_api_key:
            openai.api_key = openai_api_key
            print("✅ OpenAI API 연결 완료")
        else:
            print("⚠️  OpenAI API 키가 없어 번역 기능이 제한됩니다.")
        
        print(f"🌐 언어 설정: {self.source_language} → {self.target_language}")
    
    def extract_frames_with_text_change(self, video_path, interval_seconds=5):
        """비디오에서 일정 간격으로 프레임을 추출"""
        print(f"🎬 비디오에서 프레임 추출 중: {interval_seconds}초 간격")
        
        cap = cv2.VideoCapture(video_path)
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps
        
        frames_data = []
        frame_interval = fps * interval_seconds
        
        for frame_num in range(0, total_frames, frame_interval):
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
            ret, frame = cap.read()
            
            if not ret:
                break
                
            timestamp = frame_num / fps
            frames_data.append({
                'frame_number': frame_num,
                'timestamp': timestamp,
                'frame': frame
            })
            
            print(f"📸 프레임 추출: {timestamp:.1f}초")
        
        cap.release()
        print(f"✅ 총 {len(frames_data)}개 프레임 추출 완료")
        return frames_data
    
    def extract_japanese_text_from_frame(self, frame):
        """프레임에서 일본어 텍스트 추출"""
        try:
            # OCR 실행
            results = self.ocr_reader.readtext(frame, detail=1)
            
            japanese_texts = []
            for (bbox, text, confidence) in results:
                # 신뢰도 70% 이상만 사용
                if confidence > 0.7:
                    # 일본어 문자가 포함된 텍스트만 필터링
                    if self.contains_japanese(text):
                        japanese_texts.append({
                            'text': text,
                            'bbox': bbox,
                            'confidence': confidence
                        })
            
            return japanese_texts
            
        except Exception as e:
            print(f"❌ OCR 오류: {e}")
            return []
    
    def contains_japanese(self, text):
        """텍스트에 일본어 문자가 포함되어 있는지 확인"""
        japanese_ranges = [
            (0x3040, 0x309F),  # 히라가나
            (0x30A0, 0x30FF),  # 가타카나  
            (0x4E00, 0x9FAF),  # 한자
        ]
        
        for char in text:
            char_code = ord(char)
            for start, end in japanese_ranges:
                if start <= char_code <= end:
                    return True
        return False
    
    def translate_texts(self, texts):
        """일본어 텍스트들을 한국어로 번역"""
        if not openai.api_key or not texts:
            return [f"[번역 필요] {text}" for text in texts]
        
        print(f"🌐 {len(texts)}개 텍스트 번역 중...")
        
        try:
            # 배치 번역
            batch_text = "\n---\n".join(texts)
            
            response = openai.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": """당신은 전문 일본어-한국어 번역가입니다.
                        화면에 표시된 슬라이드 텍스트를 번역합니다.
                        기술 용어, 회사명, 고유명사는 적절히 유지하되 자연스러운 한국어로 번역하세요.
                        각 텍스트는 '---'로 구분되어 있습니다."""
                    },
                    {
                        "role": "user",
                        "content": f"다음 일본어 텍스트들을 한국어로 번역해주세요:\n\n{batch_text}"
                    }
                ]
            )
            
            translated_batch = response.choices[0].message.content
            translations = translated_batch.split("\n---\n")
            
            # 개수 맞추기
            if len(translations) != len(texts):
                print("⚠️  번역 개수 불일치, 개별 번역으로 재시도...")
                return [self.translate_single_text(text) for text in texts]
            
            print(f"✅ 번역 완료: {len(translations)}개")
            return translations
            
        except Exception as e:
            print(f"❌ 번역 오류: {e}")
            return [f"[번역 실패] {text}" for text in texts]
    
    def translate_single_text(self, text):
        """단일 텍스트 번역"""
        try:
            response = openai.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "일본어를 자연스러운 한국어로 번역하세요."},
                    {"role": "user", "content": text}
                ]
            )
            return response.choices[0].message.content
        except:
            return f"[번역 실패] {text}"
    
    def create_overlay_frame(self, original_frame, text_data_list):
        """원본 프레임에 번역된 텍스트를 오버레이"""
        height, width = original_frame.shape[:2]
        
        # 반투명 오버레이 생성
        overlay = original_frame.copy()
        overlay_alpha = 0.7
        
        # PIL로 변환하여 한글 폰트 처리
        pil_image = Image.fromarray(cv2.cvtColor(overlay, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(pil_image)
        
        # 한글 폰트 로드 시도
        try:
            # macOS 기본 한글 폰트들 시도
            font_paths = [
                "/System/Library/Fonts/AppleSDGothicNeo.ttc",
                "/System/Library/Fonts/Helvetica.ttc",
                "/Library/Fonts/Arial Unicode MS.ttf"
            ]
            
            font = None
            for font_path in font_paths:
                if os.path.exists(font_path):
                    font = ImageFont.truetype(font_path, 20)
                    break
            
            if font is None:
                font = ImageFont.load_default()
                
        except:
            font = ImageFont.load_default()
        
        for text_data in text_data_list:
            bbox = text_data['bbox']
            korean_text = text_data['korean_text']
            
            # 바운딩 박스 좌표 계산
            x_coords = [point[0] for point in bbox]
            y_coords = [point[1] for point in bbox]
            x_min, x_max = min(x_coords), max(x_coords)
            y_min, y_max = min(y_coords), max(y_coords)
            
            # 번역 텍스트를 원본 아래쪽에 배치
            text_y = y_max + 5
            
            # 배경 사각형 그리기
            text_bbox = draw.textbbox((x_min, text_y), korean_text, font=font)
            draw.rectangle(text_bbox, fill=(0, 0, 0, 180))  # 반투명 검은 배경
            
            # 한국어 텍스트 그리기
            draw.text((x_min, text_y), korean_text, font=font, fill=(255, 255, 255))
        
        # PIL에서 OpenCV로 다시 변환
        result_frame = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
        
        return result_frame
    
    def process_video_with_translation(self, video_path, output_path, interval_seconds=5):
        """비디오 전체를 처리하여 번역 오버레이 추가"""
        print(f"🚀 화면 텍스트 번역 비디오 생성 시작: {Path(video_path).name}")
        
        # 1. 프레임 추출
        frames_data = self.extract_frames_with_text_change(video_path, interval_seconds)
        
        # 2. 각 프레임에서 텍스트 추출 및 번역
        processed_frames = []
        
        for i, frame_data in enumerate(frames_data):
            print(f"\n📝 프레임 {i+1}/{len(frames_data)} 처리 중 ({frame_data['timestamp']:.1f}초)")
            
            frame = frame_data['frame']
            
            # OCR로 일본어 텍스트 추출
            japanese_texts = self.extract_japanese_text_from_frame(frame)
            
            if japanese_texts:
                print(f"   📖 추출된 일본어 텍스트: {len(japanese_texts)}개")
                
                # 텍스트만 추출하여 번역
                texts_to_translate = [item['text'] for item in japanese_texts]
                korean_translations = self.translate_texts(texts_to_translate)
                
                # 번역 결과를 원본 데이터에 추가
                text_data_list = []
                for j, japanese_text_data in enumerate(japanese_texts):
                    text_data_list.append({
                        'bbox': japanese_text_data['bbox'],
                        'japanese_text': japanese_text_data['text'],
                        'korean_text': korean_translations[j] if j < len(korean_translations) else "[번역 실패]",
                        'confidence': japanese_text_data['confidence']
                    })
                
                # 오버레이 프레임 생성
                overlay_frame = self.create_overlay_frame(frame, text_data_list)
                
                processed_frames.append({
                    'timestamp': frame_data['timestamp'],
                    'frame': overlay_frame,
                    'has_translation': True
                })
                
                print(f"   ✅ 번역 오버레이 완료")
                
            else:
                print(f"   ⚪ 일본어 텍스트 없음")
                processed_frames.append({
                    'timestamp': frame_data['timestamp'],
                    'frame': frame,
                    'has_translation': False
                })
        
        # 3. 처리된 프레임들로 비디오 생성
        self.create_video_from_processed_frames(video_path, processed_frames, output_path)
        
        return output_path
    
    def create_video_from_processed_frames(self, original_video_path, processed_frames, output_path):
        """처리된 프레임들로 새 비디오 생성"""
        print("🎬 번역 오버레이 비디오 생성 중...")
        
        # 원본 비디오 정보 가져오기
        cap = cv2.VideoCapture(original_video_path)
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # 비디오 라이터 설정
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        # 프레임별 오버레이 맵 생성
        overlay_map = {}
        for pframe in processed_frames:
            frame_num = int(pframe['timestamp'] * fps)
            overlay_map[frame_num] = pframe
        
        # 원본 비디오를 순회하며 오버레이 적용
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        
        current_overlay = None
        for frame_num in range(total_frames):
            ret, frame = cap.read()
            if not ret:
                break
            
            # 현재 프레임에 적용할 오버레이 확인
            if frame_num in overlay_map:
                current_overlay = overlay_map[frame_num]
            
            # 오버레이 적용
            if current_overlay and current_overlay['has_translation']:
                # 5초간 오버레이 유지 (다음 오버레이까지)
                output_frame = current_overlay['frame']
            else:
                output_frame = frame
            
            out.write(output_frame)
            
            if frame_num % (fps * 10) == 0:  # 10초마다 진행상황 출력
                print(f"   📹 처리 중: {frame_num/fps:.1f}초 / {total_frames/fps:.1f}초")
        
        cap.release()
        out.release()
        
        print(f"✅ 번역 오버레이 비디오 생성 완료: {output_path}")

def main():
    # OpenAI API 키 설정
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("OpenAI API 키를 입력하세요:")
        api_key = input().strip() or None
    
    # 입력 비디오 (기존 자막 포함 비디오)
    video_path = "/Users/smgu/test_code/video_converter/video_with_subtitles.mp4"
    output_path = "/Users/smgu/test_code/video_converter/video_full_translated.mp4"
    
    # 화면 텍스트 번역기 실행
    translator = ScreenTextTranslator(api_key)
    result = translator.process_video_with_translation(
        video_path, 
        output_path, 
        interval_seconds=10  # 10초마다 화면 텍스트 확인
    )
    
    print(f"\n🎉 완전 번역 비디오 생성 완료: {result}")

if __name__ == "__main__":
    main()