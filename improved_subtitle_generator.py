#!/usr/bin/env python3
import whisper
import openai
import json
import os
from pathlib import Path
import ffmpeg
import textwrap

class ImprovedSubtitleGenerator:
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
    
    def transcribe_japanese_audio(self, video_path, start_time=None, end_time=None):
        """일본어 음성을 텍스트로 변환 (구간 지정 가능)"""
        if not self.whisper_model:
            self.load_whisper_model()
        
        # 구간 지정된 경우 해당 부분만 추출
        if start_time is not None and end_time is not None:
            print(f"🎤 일본어 음성 인식 중 ({start_time}초 ~ {end_time}초)...")
            # 임시 파일로 구간 추출
            temp_audio = "/tmp/temp_segment.wav"
            (
                ffmpeg
                .input(video_path, ss=start_time, t=end_time-start_time)
                .output(temp_audio, acodec='pcm_s16le')
                .overwrite_output()
                .run(capture_stdout=True)
            )
            
            result = self.whisper_model.transcribe(
                temp_audio,
                language="ja",
                word_timestamps=True,
                verbose=True
            )
            
            # 타임스탬프 조정 (시작 시간 추가)
            for segment in result['segments']:
                segment['start'] += start_time
                segment['end'] += start_time
            
            # 임시 파일 삭제
            if os.path.exists(temp_audio):
                os.remove(temp_audio)
        else:
            print("🎤 일본어 음성 인식 중...")
            result = self.whisper_model.transcribe(
                video_path,
                language="ja",
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
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": """당신은 전문 일본어-한국어 번역가입니다. 
                        AI/기술 관련 세미나 발표 내용을 번역합니다.
                        자연스러운 한국어로 번역하되, 기술 용어는 적절히 유지하세요.
                        각 문장은 '---'로 구분되어 있습니다.
                        간결하고 읽기 쉽게 번역하세요."""
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
                    {"role": "system", "content": "일본어를 자연스럽고 간결한 한국어로 번역하세요."},
                    {"role": "user", "content": text}
                ]
            )
            return response.choices[0].message.content
        except:
            return f"[번역 실패] {text}"
    
    def split_long_subtitle(self, text, max_chars=40):
        """긴 자막을 여러 줄로 분할"""
        if len(text) <= max_chars:
            return [text]
        
        # 단어 단위로 분할 시도
        words = text.split()
        lines = []
        current_line = ""
        
        for word in words:
            if len(current_line + " " + word) <= max_chars:
                current_line += (" " + word) if current_line else word
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        
        if current_line:
            lines.append(current_line)
        
        return lines[:3]  # 최대 3줄로 제한
    
    def create_improved_srt_file(self, segments, translations, output_path):
        """개선된 SRT 자막 파일 생성 (한국어만, 작은 폰트, 긴 자막 분할)"""
        print("📝 개선된 SRT 자막 파일 생성 중...")
        
        with open(output_path, 'w', encoding='utf-8') as f:
            subtitle_index = 1
            
            for segment, translation in zip(segments, translations):
                # 긴 자막 분할
                lines = self.split_long_subtitle(translation.strip())
                segment_duration = segment['end'] - segment['start']
                
                if len(lines) == 1:
                    # 단일 라인 자막
                    start_time = self.seconds_to_srt_time(segment['start'])
                    end_time = self.seconds_to_srt_time(segment['end'])
                    
                    f.write(f"{subtitle_index}\n")
                    f.write(f"{start_time} --> {end_time}\n")
                    f.write(f"{lines[0]}\n\n")
                    subtitle_index += 1
                
                else:
                    # 여러 라인으로 분할된 자막
                    line_duration = segment_duration / len(lines)
                    
                    for i, line in enumerate(lines):
                        line_start = segment['start'] + (i * line_duration)
                        line_end = segment['start'] + ((i + 1) * line_duration)
                        
                        start_time = self.seconds_to_srt_time(line_start)
                        end_time = self.seconds_to_srt_time(line_end)
                        
                        f.write(f"{subtitle_index}\n")
                        f.write(f"{start_time} --> {end_time}\n")
                        f.write(f"{line}\n\n")
                        subtitle_index += 1
        
        print(f"✅ 개선된 SRT 파일 생성 완료: {output_path}")
    
    def seconds_to_srt_time(self, seconds):
        """초를 SRT 시간 형식으로 변환"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millisecs = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millisecs:03d}"
    
    def embed_improved_subtitles_to_video(self, video_path, srt_path, output_path):
        """개선된 자막을 비디오에 하드코딩 (작은 폰트, 한국어만)"""
        print("🎬 개선된 자막을 비디오에 삽입 중...")
        
        try:
            # 경로를 문자열로 변환
            video_path = str(video_path)
            srt_path = str(srt_path)
            output_path = str(output_path)
            
            # SRT 파일 경로 이스케이프
            srt_path_escaped = srt_path.replace('\\', '\\\\').replace(':', '\\:')
            
            # 개선된 자막 스타일 (작은 폰트, 깔끔한 디자인)
            subtitle_filter = f"subtitles='{srt_path_escaped}':force_style='FontSize=14,PrimaryColour=&Hffffff,BackColour=&H80000000,OutlineColour=&H0,BorderStyle=3,MarginV=30'"
            
            (
                ffmpeg
                .input(video_path)
                .output(
                    output_path,
                    vf=subtitle_filter,
                    vcodec='libx264',
                    acodec='aac',
                    crf=20,  # 좋은 품질
                    preset='medium'
                )
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True)
            )
            
            print(f"✅ 개선된 자막 포함 비디오 생성 완료: {output_path}")
            return True
            
        except ffmpeg.Error as e:
            print(f"❌ 자막 삽입 실패: {e}")
            if e.stderr:
                print(f"FFmpeg 오류 세부 정보: {e.stderr.decode('utf-8')}")
            return False
        except Exception as e:
            print(f"❌ 예상치 못한 오류: {e}")
            return False
    
    def process_video_segment(self, video_path, output_dir=None, start_time=None, end_time=None):
        """비디오 구간 처리 (구간 지정 가능)"""
        video_file = Path(video_path)
        if output_dir is None:
            output_dir = video_file.parent
        else:
            output_dir = Path(output_dir)
        
        segment_info = f"_{start_time}s-{end_time}s" if start_time is not None and end_time is not None else ""
        
        print(f"🚀 개선된 비디오 자막 생성 시작: {video_file.name}{segment_info}")
        
        # 1. 음성 인식
        transcription = self.transcribe_japanese_audio(video_path, start_time, end_time)
        
        # 2. 번역
        japanese_texts = [segment['text'] for segment in transcription['segments']]
        korean_translations = self.translate_text_batch(japanese_texts)
        
        # 3. 개선된 SRT 파일 생성
        srt_path = output_dir / f"{video_file.stem}{segment_info}_improved_subtitles.srt"
        self.create_improved_srt_file(transcription['segments'], korean_translations, srt_path)
        
        # 4. 개선된 자막 포함 비디오 생성
        output_video_path = output_dir / f"{video_file.stem}{segment_info}_improved_subtitles.mp4"
        success = self.embed_improved_subtitles_to_video(video_path, srt_path, output_video_path)
        
        if success:
            print(f"\n🎉 완료! 개선된 자막 포함 비디오: {output_video_path}")
            return output_video_path
        else:
            print(f"\n📄 SRT 파일만 생성됨: {srt_path}")
            return srt_path

def main():
    # OpenAI API 키 설정 (환경변수에서 읽기)
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("⚠️ OPENAI_API_KEY 환경변수를 설정해주세요.")
        print("export OPENAI_API_KEY=your_api_key_here")
        return
    
    # 원본 비디오 파일 사용
    video_path = "/Users/smgu/test_code/video_converter/video.mov"
    
    # 중간 구간 1분 테스트 (30분~31분)
    start_time = 30 * 60  # 30분
    end_time = 31 * 60    # 31분
    
    print(f"🎯 테스트 구간: {start_time//60}분{start_time%60:02d}초 ~ {end_time//60}분{end_time%60:02d}초")
    
    # 개선된 자막 생성기 실행
    generator = ImprovedSubtitleGenerator(api_key)
    result = generator.process_video_segment(video_path, start_time=start_time, end_time=end_time)
    
    print(f"\n✅ 작업 완료: {result}")

if __name__ == "__main__":
    main()