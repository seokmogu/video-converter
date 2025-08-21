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
import ffmpeg

class ImprovedScreenTextTranslator:
    def __init__(self, openai_api_key=None):
        print("🔧 개선된 OCR 및 번역 시스템 초기화 중...")
        
        # OCR 초기화 (일본어 + 영어, 더 정확한 설정)
        self.ocr_reader = easyocr.Reader(['ja', 'en'], gpu=False)
        print("✅ EasyOCR 초기화 완료")
        
        # OpenAI 설정
        if openai_api_key:
            openai.api_key = openai_api_key
            print("✅ OpenAI API 연결 완료")
        else:
            print("⚠️  OpenAI API 키가 없어 번역 기능이 제한됩니다.")
    
    def extract_frames_from_segment(self, video_path, start_time=None, end_time=None, interval_seconds=10):
        """비디오 구간에서 프레임 추출"""
        if start_time is not None and end_time is not None:
            print(f"🎬 비디오 구간에서 프레임 추출 중: {start_time}초~{end_time}초 ({interval_seconds}초 간격)")
        else:
            print(f"🎬 전체 비디오에서 프레임 추출 중: {interval_seconds}초 간격")
        
        cap = cv2.VideoCapture(video_path)
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps
        
        # 구간 설정
        if start_time is not None and end_time is not None:
            start_frame = int(start_time * fps)
            end_frame = int(end_time * fps)
        else:
            start_frame = 0
            end_frame = total_frames
            start_time = 0
            end_time = duration
        
        frames_data = []
        frame_interval = fps * interval_seconds
        
        for frame_num in range(start_frame, end_frame, frame_interval):
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
    
    def enhance_frame_for_ocr(self, frame):
        """OCR 정확도를 위한 프레임 전처리"""
        # 그레이스케일 변환
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # 해상도 업스케일링 (2배)
        height, width = gray.shape
        enhanced = cv2.resize(gray, (width*2, height*2), interpolation=cv2.INTER_CUBIC)
        
        # 노이즈 제거
        enhanced = cv2.bilateralFilter(enhanced, 9, 75, 75)
        
        # 대비 개선
        enhanced = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8)).apply(enhanced)
        
        return enhanced
    
    def extract_japanese_text_improved(self, frame):
        """개선된 일본어 텍스트 추출"""
        try:
            # 프레임 전처리
            enhanced_frame = self.enhance_frame_for_ocr(frame)
            
            # OCR 실행 (더 낮은 임계값으로 더 많은 텍스트 감지)
            results = self.ocr_reader.readtext(
                enhanced_frame, 
                detail=1,
                paragraph=False,
                width_ths=0.5,    # 더 넓은 폭 허용
                height_ths=0.5,   # 더 넓은 높이 허용
                text_threshold=0.5,  # 낮은 텍스트 임계값
                low_text=0.3      # 매우 낮은 임계값
            )
            
            japanese_texts = []
            for (bbox, text, confidence) in results:
                # 더 낮은 신뢰도도 허용 (50% 이상)
                if confidence > 0.5:
                    # 일본어 문자가 포함된 텍스트만 필터링
                    if self.contains_japanese(text):
                        # 스케일링 보정 (2배 업스케일했으므로 좌표를 반으로)
                        corrected_bbox = [[point[0]/2, point[1]/2] for point in bbox]
                        
                        japanese_texts.append({
                            'text': text.strip(),
                            'bbox': corrected_bbox,
                            'confidence': confidence
                        })
            
            return japanese_texts
            
        except Exception as e:
            print(f"❌ OCR 오류: {e}")
            return []
    
    def contains_japanese(self, text):
        """텍스트에 일본어 문자가 포함되어 있는지 확인 (개선된 감지)"""
        japanese_ranges = [
            (0x3040, 0x309F),  # 히라가나
            (0x30A0, 0x30FF),  # 가타카나  
            (0x4E00, 0x9FAF),  # 한자
            (0xFF65, 0xFF9F),  # 반각 가타카나
        ]
        
        japanese_count = 0
        total_chars = len(text.strip())
        
        if total_chars == 0:
            return False
            
        for char in text:
            char_code = ord(char)
            for start, end in japanese_ranges:
                if start <= char_code <= end:
                    japanese_count += 1
                    break
        
        # 문자의 30% 이상이 일본어면 일본어 텍스트로 간주
        return japanese_count / total_chars >= 0.3
    
    def translate_texts_improved(self, texts):
        """개선된 일본어 텍스트 번역 (더 간결하게)"""
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
                        화면에 표시된 슬라이드/UI 텍스트를 번역합니다.
                        매우 간결하고 핵심적인 한국어로 번역하세요.
                        기술 용어, 회사명, 고유명사는 적절히 유지하되 읽기 쉽게 하세요.
                        긴 문장은 핵심만 간단히 번역하세요.
                        각 텍스트는 '---'로 구분되어 있습니다."""
                    },
                    {
                        "role": "user",
                        "content": f"다음 일본어 텍스트들을 간결한 한국어로 번역해주세요:\n\n{batch_text}"
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
                    {"role": "system", "content": "일본어를 간결한 한국어로 번역하세요."},
                    {"role": "user", "content": text}
                ]
            )
            return response.choices[0].message.content
        except:
            return f"[번역 실패] {text}"
    
    def create_improved_overlay_frame(self, original_frame, text_data_list):
        """개선된 오버레이 프레임 생성 (작은 폰트, 깔끔한 디자인)"""
        height, width = original_frame.shape[:2]
        
        # PIL로 변환하여 한글 폰트 처리
        pil_image = Image.fromarray(cv2.cvtColor(original_frame, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(pil_image)
        
        # 작은 한글 폰트 로드
        try:
            font_paths = [
                "/System/Library/Fonts/AppleSDGothicNeo.ttc",
                "/System/Library/Fonts/Helvetica.ttc",
                "/Library/Fonts/Arial Unicode MS.ttf"
            ]
            
            font = None
            for font_path in font_paths:
                if os.path.exists(font_path):
                    font = ImageFont.truetype(font_path, 12)  # 작은 폰트 크기
                    break
            
            if font is None:
                font = ImageFont.load_default()
                
        except:
            font = ImageFont.load_default()
        
        for text_data in text_data_list:
            bbox = text_data['bbox']
            korean_text = text_data['korean_text']
            
            # 긴 텍스트는 줄임
            if len(korean_text) > 20:
                korean_text = korean_text[:18] + "..."
            
            # 바운딩 박스 좌표 계산
            x_coords = [point[0] for point in bbox]
            y_coords = [point[1] for point in bbox]
            x_min, x_max = min(x_coords), max(x_coords)
            y_min, y_max = min(y_coords), max(y_coords)
            
            # 번역 텍스트를 원본 바로 아래쪽에 작게 배치
            text_y = y_max + 2
            
            # 작은 배경 사각형 그리기
            text_bbox = draw.textbbox((x_min, text_y), korean_text, font=font)
            padding = 2
            bg_bbox = [
                text_bbox[0] - padding,
                text_bbox[1] - padding, 
                text_bbox[2] + padding,
                text_bbox[3] + padding
            ]
            
            # 반투명 배경
            overlay = Image.new('RGBA', pil_image.size, (0, 0, 0, 0))
            overlay_draw = ImageDraw.Draw(overlay)
            overlay_draw.rectangle(bg_bbox, fill=(0, 0, 0, 120))
            
            # 배경 합성
            pil_image = Image.alpha_composite(pil_image.convert('RGBA'), overlay).convert('RGB')
            draw = ImageDraw.Draw(pil_image)
            
            # 작은 한국어 텍스트 그리기 (흰색)
            draw.text((x_min, text_y), korean_text, font=font, fill=(255, 255, 255))
        
        # PIL에서 OpenCV로 다시 변환
        result_frame = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
        
        return result_frame
    
    def process_video_segment_improved(self, video_path, output_path, start_time=None, end_time=None, interval_seconds=10):
        """개선된 비디오 구간 처리"""
        segment_info = f"_{start_time}s-{end_time}s" if start_time is not None and end_time is not None else ""
        print(f"🚀 개선된 화면 텍스트 번역 시작: {Path(video_path).name}{segment_info}")
        
        # 1. 프레임 추출
        frames_data = self.extract_frames_from_segment(video_path, start_time, end_time, interval_seconds)
        
        # 2. 각 프레임에서 텍스트 추출 및 번역
        processed_frames = []
        
        for i, frame_data in enumerate(frames_data):
            print(f"\n📝 프레임 {i+1}/{len(frames_data)} 처리 중 ({frame_data['timestamp']:.1f}초)")
            
            frame = frame_data['frame']
            
            # 개선된 OCR로 일본어 텍스트 추출
            japanese_texts = self.extract_japanese_text_improved(frame)
            
            if japanese_texts:
                print(f"   📖 추출된 일본어 텍스트: {len(japanese_texts)}개")
                
                # 텍스트만 추출하여 번역
                texts_to_translate = [item['text'] for item in japanese_texts]
                korean_translations = self.translate_texts_improved(texts_to_translate)
                
                # 번역 결과를 원본 데이터에 추가
                text_data_list = []
                for j, japanese_text_data in enumerate(japanese_texts):
                    text_data_list.append({
                        'bbox': japanese_text_data['bbox'],
                        'japanese_text': japanese_text_data['text'],
                        'korean_text': korean_translations[j] if j < len(korean_translations) else "[번역 실패]",
                        'confidence': japanese_text_data['confidence']
                    })
                
                # 개선된 오버레이 프레임 생성
                overlay_frame = self.create_improved_overlay_frame(frame, text_data_list)
                
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
        self.create_video_from_processed_frames_improved(video_path, processed_frames, output_path, start_time, end_time)
        
        return output_path
    
    def create_video_from_processed_frames_improved(self, original_video_path, processed_frames, output_path, start_time=None, end_time=None):
        """개선된 비디오 생성"""
        print("🎬 개선된 번역 오버레이 비디오 생성 중...")
        
        # 원본 비디오 정보 가져오기
        cap = cv2.VideoCapture(original_video_path)
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        # 구간 설정
        if start_time is not None and end_time is not None:
            start_frame = int(start_time * fps)
            end_frame = int(end_time * fps)
        else:
            start_frame = 0
            end_frame = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        total_frames = end_frame - start_frame
        
        # 비디오 라이터 설정
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        # 프레임별 오버레이 맵 생성
        overlay_map = {}
        for pframe in processed_frames:
            frame_num = int(pframe['timestamp'] * fps) - start_frame
            overlay_map[frame_num] = pframe
        
        # 원본 비디오 구간을 순회하며 오버레이 적용
        cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
        
        current_overlay = None
        for frame_num in range(total_frames):
            ret, frame = cap.read()
            if not ret:
                break
            
            # 현재 프레임에 적용할 오버레이 확인
            if frame_num in overlay_map:
                current_overlay = overlay_map[frame_num]
            
            # 오버레이 적용 (10초간 유지)
            if current_overlay and current_overlay['has_translation']:
                output_frame = current_overlay['frame']
            else:
                output_frame = frame
            
            out.write(output_frame)
            
            if frame_num % (fps * 5) == 0:  # 5초마다 진행상황 출력
                progress = (frame_num / total_frames) * 100
                print(f"   📹 처리 중: {progress:.1f}%")
        
        cap.release()
        out.release()
        
        print(f"✅ 개선된 번역 오버레이 비디오 생성 완료: {output_path}")

def main():
    # OpenAI API 키 설정 (환경변수에서 읽기)
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("⚠️ OPENAI_API_KEY 환경변수를 설정해주세요.")
        print("export OPENAI_API_KEY=your_api_key_here")
        return
    
    # 원본 비디오 사용
    video_path = "/Users/smgu/test_code/video_converter/video.mov"
    output_path = "/Users/smgu/test_code/video_converter/video_improved_screen_translation.mp4"
    
    # 중간 구간 1분 테스트 (30분~31분)
    start_time = 30 * 60  # 30분
    end_time = 31 * 60    # 31분
    
    print(f"🎯 테스트 구간: {start_time//60}분{start_time%60:02d}초 ~ {end_time//60}분{end_time%60:02d}초")
    
    # 개선된 화면 텍스트 번역기 실행
    translator = ImprovedScreenTextTranslator(api_key)
    result = translator.process_video_segment_improved(
        video_path, 
        output_path, 
        start_time=start_time,
        end_time=end_time,
        interval_seconds=10  # 10초마다 화면 텍스트 확인
    )
    
    print(f"\n🎉 개선된 화면 번역 비디오 생성 완료: {result}")

if __name__ == "__main__":
    main()