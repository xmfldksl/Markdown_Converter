# Markdown Converter v1.2

## Overview

This Python-based tool converts PDF, Excel (.xlsx, .xlsb), and PowerPoint (.pptx) documents into structured Markdown format. It is designed to preserve text hierarchies and complex table layouts, specifically focusing on handling large datasets and extracting nested tables into a readable Markdown structure.

## Key Technical Features

  * **Multi-Format Support:** Converts PDF, XLSX, XLSB, and PPTX files seamlessly.
  * **Intelligent Table Extraction:** Detects nested tables in PDFs and separates them into logical sections.
  * **Large Data Processing:** Utilizes chunking and memory-safe streaming to process large Excel files without memory overflow.
  * **Robust Text Processing:** Handles duplicate characters caused by PDF effects and accurately extracts text from PPTX shape frames.
  * **Responsive GUI:** Built with `tkinter` and `threading`, featuring real-time progress updates to ensure a non-blocking UI during heavy processing.

## For Developers (Source Code)

### Prerequisites

  * **Python 3.9** or higher
  * **Required Libraries:** `pdfplumber`, `pandas`, `openpyxl`, `pyxlsb`, `python-pptx`, `tabulate`, `tkinter`

### Installation

1.  Clone the repository:
    ```bash
    git clone [https://github.com/xmfldksl/Markdown_Converter.git](https://github.com/xmfldksl/Markdown_Converter.git)
    cd Markdown_Converter
    ```
2.  Install dependencies:
    ```bash
    pip install pdfplumber pandas openpyxl pyxlsb python-pptx tabulate
    ```

### How to Run

```bash
python md_converter_main.py
```

## For Users (Executable)

  * **Windows Only:** No Python installation is required if you download the compiled package.
  * **Download:** Visit the [Releases](https://github.com/xmfldksl/Markdown_Converter/releases) page to download the latest executable zip archive (Extract the archive and run the executable file while keeping the `_internal` directory).

## Release Notes (v1.2)

  * **Engine Modularity:** Separated core logic into `md_converter_main.py`, `md_converter_pdf.py`, `md_converter_xlsx.py`, and `md_converter_pptx.py`.
  * **Excel Integration:** Added support for standard `.xlsx` and binary `.xlsb` files using streaming and chunking methods.
  * **PowerPoint Integration:** Added support for extracting text and tables directly from `.pptx` slides.
  * **UI/UX Enhancement:** Unified UI to support multiple formats dynamically and improved progress tracking.
  * **Performance Optimization:** Distributed deployment with an `_internal` folder architecture to prevent launch delays and maximize UI responsiveness.

## Limitations

  * **OCR Not Supported:** Only text-based documents are supported. Image-based (scanned) PDFs will not be converted.
  * **Complex Layouts:** Multi-column or highly artistic document layouts may produce unexpected results.

### Author
Name: xmfldksl
Email: xmfldksl@gmail.com
GitHub: https://github.com/xmfldksl

License
This project is licensed under the MIT License - see the LICENSE file for details.

-----

# Markdown Converter v1.2

## 개요

이 프로젝트는 PDF, 엑셀(.xlsx, .xlsb), 파워포인트(.pptx) 문서를 구조화된 Markdown 형식으로 변환하는 파이썬 기반 도구입니다. 텍스트 계층 구조와 복잡한 표 레이아웃을 보존하며, 대용량 데이터 처리와 중첩된 표를 읽기 쉬운 마크다운 구조로 재구성하는 데 특화되어 있습니다.

## 주요 기술 특징

  * **다중 확장자 지원:** PDF, XLSX, XLSB, PPTX 파일을 하나의 프로그램에서 변환합니다.
  * **지능형 표 추출:** PDF 내부의 중첩된 표를 감지하고 논리적 섹션으로 분리합니다.
  * **대용량 데이터 처리:** 스트리밍 및 청크 분할 방식을 통해 메모리 초과 없이 거대한 엑셀 파일을 안전하게 변환합니다.
  * **강력한 텍스트 처리:** PDF의 글자 중복 문제를 해결하고 PPTX의 텍스트 상자 및 표 데이터를 정확하게 추출합니다.
  * **응답형 GUI:** `tkinter`와 `threading`을 사용하여 실시간 진행률을 표기하며 대용량 처리 중에도 UI가 멈추지 않습니다.

## 개발자 가이드 (소스 코드 사용)

### 사전 요구 사항

  * **Python 3.9** 이상
  * **필수 라이브러리:** `pdfplumber`, `pandas`, `openpyxl`, `pyxlsb`, `python-pptx`, `tabulate`, `tkinter`

### 설치 방법

1.  리포지토리 클론:
    ```bash
    git clone [https://github.com/xmfldksl/Markdown_Converter.git](https://github.com/xmfldksl/Markdown_Converter.git)
    cd Markdown_Converter
    ```
2.  라이브러리 설치:
    ```bash
    pip install pdfplumber pandas openpyxl pyxlsb python-pptx tabulate
    ```

### 실행 방법

```bash
python md_converter_main.py
```

## 일반 사용자 가이드 (실행 파일)

  * **Windows 전용:** 배포된 패키지 압축 파일을 사용할 경우 파이썬 설치가 필요 없습니다.
  * **다운로드:** [Releases](https://github.com/xmfldksl/Markdown_Converter/releases) 페이지에서 최신 실행 패키지 압축 파일(.zip)을 다운로드하세요 (압축 해제 후 `_internal` 폴더가 유지된 상태에서 실행 파일을 작동해야 합니다).

## v1.2 업데이트 내역

  * **엔진 모듈화:** 코드를 `md_converter_main.py`, `md_converter_pdf.py`, `md_converter_xlsx.py`, `md_converter_pptx.py`로 분할하여 확장성을 확보했습니다.
  * **엑셀 지원 추가:** `.xlsx` 및 `.xlsb` 바이너리 파일 변환 기능이 추가되었습니다.
  * **파워포인트 지원 추가:** `.pptx` 슬라이드 내부 텍스트 및 표 추출 기능이 추가되었습니다.
  * **UI/UX 개선:** 여러 확장자를 처리할 수 있도록 메인 화면이 개편되었으며 진행률 연동이 최적화되었습니다.
  * **구동 성능 최적화:** `_internal` 폴더 분리형 배포 구조를 채택하여, 실행 초기 지연 현상을 차단하고 프로그램 응답 속도를 최대화했습니다.

## 제한 사항

  * **OCR 미지원:** 텍스트 기반 문서만 지원하며, 스캔된 이미지 문서는 지원하지 않습니다.
  * **복잡한 레이아웃:** 다단 구성이나 예술적 레이아웃의 경우 서식이 어긋날 수 있습니다.

### 제작자
이름: xmfldksl
이메일: xmfldksl@gmail.com
깃허브: https://github.com/xmfldksl

라이선스
이 프로젝트는 MIT 라이선스를 따릅니다. 자세한 내용은 LICENSE 파일을 확인하세요.