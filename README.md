# PDF to Markdown Converter v1.1

## Overview

This Python-based tool converts PDF documents into structured Markdown format. It is designed to preserve text hierarchies and complex table layouts, specifically focusing on detecting and reorganizing nested tables into a readable Markdown structure.

## Key Technical Features

  * **Intelligent Table Extraction:** Detects nested tables and separates them into logical sections.
  * **Structural Integrity:** Maintains top-to-bottom reading order using coordinate-based analysis.
  * **Robust Text Processing:** Handles duplicate characters caused by PDF effects (e.g., shadows in PPT-generated PDFs).
  * **Responsive GUI:** Built with `tkinter` and `threading` to ensure a non-blocking UI during heavy processing.

## For Developers (Source Code)

### Prerequisites

  * **Python 3.9** or higher
  * **Required Libraries:** `PyMuPDF (fitz)`, `tkinter` (usually included with Python)

### Installation

1.  Clone the repository:
    ```bash
    git clone https://github.com/xmfldksl/PDF_to_Markdown_Converter.git
    cd PDF_to_Markdown_Converter
    ```
2.  Install dependencies:
    ```bash
    pip install pymupdf
    ```

### How to Run

```bash
python PDF_to_MD_GPT_1.1.py
```

## For Users (Executable)

  * **Windows Only:** No Python installation is required if you use the standalone `.exe` file.
  * **Download:** Visit the [Releases](https://www.google.com/search?q=https://github.com/xmfldksl/PDF_to_Markdown_Converter/releases) page to download the latest executable.

## Release Notes (v1.1)

  * **Text Deduplication:** Applied `dedupe_chars(tolerance=2)` to fix duplicate text issues.
  * **Table Security:** Escaped vertical bars (`|` → `\|`) in cells to prevent Markdown table breakage.
  * **Stability:** Implemented `get_safe_bbox` to prevent out-of-bound coordinate errors.
  * **UI/UX:** Added real-time logging and multi-threading for a smoother conversion experience.

## Limitations

  * **OCR Not Supported:** Only text-based PDFs are supported. Image-based (scanned) PDFs will not be converted.
  * **Complex Layouts:** Multi-column or highly artistic layouts may produce unexpected results.


### Author
Name: xmfldksl
Email: xmfldksl@gmail.com
GitHub: https://github.com/xmfldksl

License
This project is licensed under the MIT License - see the LICENSE file for details.

-----

# PDF to Markdown Converter v1.1

## 개요

이 프로젝트는 PDF 문서를 구조화된 Markdown 형식으로 변환하는 파이썬 기반 도구입니다. 텍스트 계층 구조와 복잡한 표 레이아웃을 보존하며, 특히 중첩된 표를 감지하여 읽기 쉬운 마크다운 구조로 재구성하는 데 특화되어 있습니다.

## 주요 기술 특징

  * **지능형 표 추출:** 중첩된 표를 감지하고 논리적 섹션으로 분리합니다.
  * **구조 유지:** 좌표 기반 분석을 통해 위에서 아래로 흐르는 읽기 순서를 유지합니다.
  * **강력한 텍스트 처리:** PPT 기반 PDF의 그림자 효과 등으로 발생하는 글자 중복 문제를 해결합니다.
  * **응답형 GUI:** `tkinter`와 `threading`을 사용하여 대용량 처리 중에도 UI가 멈추지 않습니다.

## 개발자 가이드 (소스 코드 사용)

### 사전 요구 사항

  * **Python 3.9** 이상
  * **필수 라이브러리:** `PyMuPDF (fitz)`, `tkinter`

### 설치 방법

1.  리포지토리 클론:
    ```bash
    git clone https://github.com/xmfldksl/PDF_to_Markdown_Converter.git
    cd PDF_to_Markdown_Converter
    ```
2.  라이브러리 설치:
    ```bash
    pip install pymupdf
    ```

### 실행 방법

```bash
python PDF_to_MD_GPT_1.1.py
```

## 일반 사용자 가이드 (실행 파일)

  * **Windows 전용:** 제공된 `.exe` 파일을 사용할 경우 파이썬 설치가 필요 없습니다.
  * **다운로드:** [Releases](https://www.google.com/search?q=https://github.com/xmfldksl/PDF_to_Markdown_Converter/releases) 페이지에서 최신 실행 파일을 다운로드하세요.

## v1.1 업데이트 내역

  * **글자 중복 방지:** `dedupe_chars(tolerance=2)` 적용으로 중복 추출 문제 해결
  * **표 구조 보호:** 셀 내부 `|` 문자를 `\|`로 이스케이프 처리하여 마크다운 깨짐 방지
  * **안정성 개선:** `get_safe_bbox` 도입으로 좌표 범위 초과 오류 방지
  * **UI 개선:** 실시간 로그 출력 및 멀티스레딩 적용

## 제한 사항

  * **OCR 미지원:** 텍스트 기반 PDF만 지원하며, 스캔된 이미지 PDF는 지원하지 않습니다.
  * **복잡한 레이아웃:** 다단 구성이나 예술적 레이아웃의 경우 서식이 어긋날 수 있습니다.


### 제작자
이름: xmfldksl
이메일: xmfldksl@gmail.com
깃허브: https://github.com/xmfldksl

라이선스
이 프로젝트는 MIT 라이선스를 따릅니다. 자세한 내용은 LICENSE 파일을 확인하세요.