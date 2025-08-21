# Video Converter

AI 기반 비디오 자막 생성 및 화면 텍스트 번역 도구입니다. OpenAI Whisper를 사용한 음성 인식과 GPT-4를 활용한 자막 번역, 그리고 EasyOCR을 사용한 화면 텍스트 인식 및 번역 기능을 제공합니다.

## 🎯 주요 기능

- **음성 자막 생성**: OpenAI Whisper를 사용한 고품질 음성 인식
- **자막 번역**: GPT-4를 활용한 자연스러운 한국어 번역
- **화면 텍스트 인식**: EasyOCR을 사용한 화면 내 텍스트 감지
- **화면 텍스트 번역**: 감지된 텍스트의 실시간 번역 오버레이

## 🛠 설치

### 1. 저장소 클론

```bash
git clone https://github.com/seokmogu/video-converter.git
cd video-converter
```

### 2. 가상환경 생성

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 또는
venv\\Scripts\\activate  # Windows
```

### 3. 의존성 설치

```bash
pip install -r requirements.txt
```

### 4. FFmpeg 설치

- **Mac**: `brew install ffmpeg`
- **Ubuntu**: `sudo apt install ffmpeg`
- **Windows**: [FFmpeg 공식 사이트](https://ffmpeg.org/download.html)에서 다운로드

### 5. 환경 변수 설정

```bash
# .env.example을 복사해서 .env 파일 생성
cp .env.example .env

# .env 파일을 열어서 OpenAI API 키 설정
# OPENAI_API_KEY=your_actual_api_key_here
```

## 🚀 사용법

### 기본 자막 생성기

음성을 인식하여 자막을 생성하고 번역합니다.

```bash
python subtitle_generator.py
```

### 개선된 자막 생성기

더 나은 번역 품질과 자막 분할 기능을 제공합니다.

```bash
python improved_subtitle_generator.py
```

### 화면 텍스트 번역기

화면에 나타나는 텍스트를 감지하고 번역합니다.

```bash
python screen_text_translator.py
```

### 개선된 화면 텍스트 번역기

향상된 OCR 정확도와 더 나은 텍스트 감지 기능을 제공합니다.

```bash
python improved_screen_translator.py
```

### 전체 비디오 처리

음성 자막 생성과 화면 텍스트 번역을 순차적으로 실행합니다.

```bash
python process_full_video.py
```

### 통합 테스트

개선된 시스템의 통합 테스트를 실행합니다.

```bash
python test_improved_system.py
```

## 📁 파일 구조

```
video-converter/
├── README.md                          # 이 파일
├── requirements.txt                   # Python 의존성
├── .env.example                      # 환경변수 예제
├── .gitignore                        # Git 제외 파일 목록
├── subtitle_generator.py             # 기본 자막 생성기
├── improved_subtitle_generator.py    # 개선된 자막 생성기
├── screen_text_translator.py         # 기본 화면 텍스트 번역기
├── improved_screen_translator.py     # 개선된 화면 텍스트 번역기
├── process_full_video.py             # 전체 비디오 처리
├── test_improved_system.py           # 통합 테스트
├── test_screen_translation.py        # 화면 번역 테스트
└── convert_video.py                  # 비디오 변환 유틸리티
```

## ⚙️ 설정

### OpenAI API 키

1. [OpenAI 플랫폼](https://platform.openai.com/api-keys)에서 API 키를 생성합니다.
2. `.env` 파일에 키를 설정합니다:
   ```
   OPENAI_API_KEY=sk-proj-...
   ```

### 비디오 파일 준비

지원하는 비디오 형식: `.mp4`, `.mov`, `.avi`, `.mkv` 등

코드에서 `video_path` 변수를 수정하여 처리할 비디오 파일 경로를 지정합니다.

## 🔧 주요 클래스

### SubtitleGenerator

기본 자막 생성 기능을 제공합니다.

```python
from subtitle_generator import SubtitleGenerator

generator = SubtitleGenerator(api_key="your-openai-api-key")
result = generator.generate_subtitles("video.mp4")
```

### ImprovedSubtitleGenerator

향상된 자막 생성 및 번역 기능을 제공합니다.

```python
from improved_subtitle_generator import ImprovedSubtitleGenerator

generator = ImprovedSubtitleGenerator(api_key="your-openai-api-key")
result = generator.process_video_segment("video.mp4", start_time=0, end_time=60)
```

### ScreenTextTranslator

화면 텍스트 감지 및 번역 기능을 제공합니다.

```python
from screen_text_translator import ScreenTextTranslator

translator = ScreenTextTranslator(api_key="your-openai-api-key")
result = translator.process_video_with_translation("input.mp4", "output.mp4")
```

### ImprovedScreenTextTranslator

향상된 화면 텍스트 처리 기능을 제공합니다.

```python
from improved_screen_translator import ImprovedScreenTextTranslator

translator = ImprovedScreenTextTranslator(api_key="your-openai-api-key")
result = translator.process_video_segment_improved("input.mp4", "output.mp4")
```

## 🎥 처리 과정

1. **음성 자막 생성**
   - OpenAI Whisper로 음성 인식
   - GPT-4로 한국어 번역
   - SRT 파일 생성
   - 비디오에 자막 합성

2. **화면 텍스트 번역**
   - 지정된 간격으로 프레임 추출
   - EasyOCR로 텍스트 감지
   - GPT-4로 텍스트 번역
   - 번역된 텍스트를 비디오에 오버레이

## ⚠️ 주의사항

- OpenAI API 사용료가 발생할 수 있습니다.
- 긴 비디오 처리 시 상당한 시간이 소요될 수 있습니다.
- 화면 텍스트 인식 정확도는 비디오 품질에 따라 달라집니다.
- FFmpeg가 시스템에 설치되어 있어야 합니다.

## 🐛 문제 해결

### FFmpeg 오류

```bash
# Mac
brew install ffmpeg

# Ubuntu
sudo apt update
sudo apt install ffmpeg
```

### OpenAI API 오류

- API 키가 올바르게 설정되어 있는지 확인
- OpenAI 계정에 충분한 크레딧이 있는지 확인

### 메모리 부족

긴 비디오의 경우 구간별로 나누어 처리하세요:

```python
# 30분씩 구간 나누어 처리
generator.process_video_segment("video.mp4", start_time=0, end_time=1800)
generator.process_video_segment("video.mp4", start_time=1800, end_time=3600)
```

## 📝 라이선스

MIT License

## 🤝 기여하기

버그 리포트나 기능 요청은 GitHub Issues를 사용해주세요.