#!/usr/bin/env python3
import whisper
import openai
import json
import os
from pathlib import Path
import ffmpeg

class SubtitleGenerator:
    def __init__(self, openai_api_key=None):
        self.whisper_model = None
        if openai_api_key:
            openai.api_key = openai_api_key
        else:
            print("⚠️  OpenAI API 키가 없어 번역 기능이 제한됩니다.")
    
    def load_whisper_model(self, model_size="large"):
        """Whisper 모델 로드"""
        print(f"Whisper {model_size} 모델 로딩 중...")
        self.whisper_model = whisper.load_model(model_size)
        print("✅ Whisper 모델 로드 완료")
    
    def transcribe_japanese_audio(self, video_path):
        """일본어 음성을 텍스트로 변환 (타임스탬프 포함)"""
        if not self.whisper_model:
            self.load_whisper_model()
        
        print("🎤 일본어 음성 인식 중...")
        result = self.whisper_model.transcribe(
            video_path,
            language="ja",  # 일본어로 지정
            word_timestamps=True,
            verbose=True
        )
        
        print(f"✅ 음성 인식 완료: {len(result['segments'])}개 세그먼트")
        return result
    
    def translate_text_batch(self, texts):
        """일본어 텍스트를 한국어로 번역"""
        if not openai.api_key:
            print("⚠️  OpenAI API 키가 없어 번역을 건너뜁니다.")
            return [f"[번역 필요] {text}" for text in texts]
        
        print("🌐 일본어 → 한국어 번역 중...")
        
        # 배치로 번역 (비용 절약)
        batch_text = "\n---\n".join(texts)
        
        try:
            response = openai.chat.completions.create(
                model="gpt-4o",  # 최고 품질 번역
                messages=[
                    {
                        "role": "system",
                        "content": """당신은 전문 일본어-한국어 번역가입니다. 
                        AI/기술 관련 세미나 발표 내용을 번역합니다.
                        자연스러운 한국어로 번역하되, 기술 용어는 적절히 유지하세요.
                        각 문장은 '---'로 구분되어 있습니다."""
                    },
                    {
                        "role": "user", 
                        "content": f"다음 일본어 텍스트를 한국어로 번역해주세요:\n\n{batch_text}"
                    }
                ]
            )
            
            translated_batch = response.choices[0].message.content
            translated_texts = translated_batch.split("\n---\n")
            
            # 원본과 번역본 개수 맞추기
            if len(translated_texts) != len(texts):
                print("⚠️  번역 개수가 맞지 않습니다. 개별 번역으로 재시도...")
                return [self.translate_single_text(text) for text in texts]
            
            print(f"✅ 번역 완료: {len(translated_texts)}개 문장")
            return translated_texts
            
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
    
    def create_srt_file(self, segments, translations, output_path):
        """SRT 자막 파일 생성"""
        print("📝 SRT 자막 파일 생성 중...")
        
        with open(output_path, 'w', encoding='utf-8') as f:
            for i, (segment, translation) in enumerate(zip(segments, translations), 1):
                start_time = self.seconds_to_srt_time(segment['start'])
                end_time = self.seconds_to_srt_time(segment['end'])
                
                # 이중 자막 (일본어 + 한국어)
                subtitle_text = f"{segment['text'].strip()}\n{translation.strip()}"
                
                f.write(f"{i}\n")
                f.write(f"{start_time} --> {end_time}\n")
                f.write(f"{subtitle_text}\n\n")
        
        print(f"✅ SRT 파일 생성 완료: {output_path}")
    
    def seconds_to_srt_time(self, seconds):
        """초를 SRT 시간 형식으로 변환"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millisecs = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millisecs:03d}"
    
    def embed_subtitles_to_video(self, video_path, srt_path, output_path):
        """비디오에 자막을 하드코딩"""
        print("🎬 비디오에 자막 삽입 중...")
        
        try:
            # 경로를 문자열로 변환
            video_path = str(video_path)
            srt_path = str(srt_path)
            output_path = str(output_path)
            
            # SRT 파일 경로에서 백슬래시 이스케이프 (Windows 호환성)
            srt_path_escaped = srt_path.replace('\\', '\\\\').replace(':', '\\:')
            
            # 한글 폰트 설정
            subtitle_filter = f"subtitles='{srt_path_escaped}':force_style='FontSize=20,PrimaryColour=&Hffffff,BackColour=&H80000000,OutlineColour=&H0,BorderStyle=3'"
            
            (
                ffmpeg
                .input(video_path)
                .output(
                    output_path,
                    vf=subtitle_filter,
                    vcodec='libx264',
                    acodec='aac',
                    crf=23,  # 적당한 품질
                    preset='medium'
                )
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True)
            )
            
            print(f"✅ 자막 포함 비디오 생성 완료: {output_path}")
            return True
            
        except ffmpeg.Error as e:
            print(f"❌ 자막 삽입 실패: {e}")
            if e.stderr:
                print(f"FFmpeg 오류 세부 정보: {e.stderr.decode('utf-8')}")
            return False
        except Exception as e:
            print(f"❌ 예상치 못한 오류: {e}")
            return False
    
    def process_video(self, video_path, output_dir=None):
        """전체 프로세스 실행"""
        video_file = Path(video_path)
        if output_dir is None:
            output_dir = video_file.parent
        else:
            output_dir = Path(output_dir)
        
        print(f"🚀 비디오 자막 생성 시작: {video_file.name}")
        
        # 1. 음성 인식
        transcription = self.transcribe_japanese_audio(video_path)
        
        # 2. 번역
        japanese_texts = [segment['text'] for segment in transcription['segments']]
        korean_translations = self.translate_text_batch(japanese_texts)
        
        # 3. SRT 파일 생성
        srt_path = output_dir / f"{video_file.stem}_subtitles.srt"
        self.create_srt_file(transcription['segments'], korean_translations, srt_path)
        
        # 4. 자막 포함 비디오 생성
        output_video_path = output_dir / f"{video_file.stem}_with_subtitles.mp4"
        success = self.embed_subtitles_to_video(video_path, srt_path, output_video_path)
        
        if success:
            print(f"\n🎉 완료! 자막 포함 비디오: {output_video_path}")
            return output_video_path
        else:
            print(f"\n📄 SRT 파일만 생성됨: {srt_path}")
            return srt_path

def main():
    # OpenAI API 키 설정 (환경변수 또는 직접 입력)
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("OpenAI API 키를 입력하세요 (번역 기능 사용 시 필요):")
        api_key = input().strip() or None
    
    # 비디오 파일 경로
    video_path = "/Users/smgu/test_code/video_converter/video_compressed.mp4"
    
    # 자막 생성기 실행
    generator = SubtitleGenerator(api_key)
    result = generator.process_video(video_path)
    
    print(f"\n✅ 작업 완료: {result}")

if __name__ == "__main__":
    main()