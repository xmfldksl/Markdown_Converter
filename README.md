# PDF to Markdown Converter v1.1

## Overview

This application converts PDF documents into Markdown format while preserving text structure and table layouts.
It supports detection of nested tables and automatically reorganizes them into readable Markdown output.

## Features

* Extracts text and tables from PDF files
* Detects nested tables and separates them into detailed sections
* Maintains logical reading order (top-to-bottom flow)
* Converts tables into Markdown format
* Provides a simple GUI for file selection and execution
* Displays real-time progress during conversion

## Requirements

* No additional installation is required when using the provided EXE file
* The application runs on Windows environments

## Usage

1. Launch the executable file
2. Select a PDF file to convert
3. Select a destination folder for the output
4. Click the "Convert PDF to MD" button
5. Wait until the process completes
6. The generated Markdown file will be saved automatically

## Notes

* Complex PDF layouts may produce unexpected formatting results
* Table detection is based on positional analysis and may vary depending on PDF quality
* Large PDF files may take longer to process
* **Only text-based PDFs are supported; OCR (image-based) PDFs are not supported**

## What's New in v1.1

* Removed CPU usage option (now operates in single-thread mode)
* Character deduplication: Applied `dedupe_chars(tolerance=2)` to prevent duplicate text extraction caused by effects such as shadows in PPT-based PDFs
* Duplicate keyword cleanup: Introduced `dict.fromkeys` logic to resolve repeated keyword listing in child table descriptions (assumed cause)
* Markdown table structure protection: Escaped vertical bars (`|` → `\|`) inside cell data to prevent column structure breakage
* Safe coordinate clamping: Implemented `get_safe_bbox` to prevent runtime errors caused by out-of-bound PDF coordinates
* Ghost table prevention: Added `has_content` validation to exclude empty tables with no actual text
* Non-blocking GUI threading: Used `threading` module to keep UI responsive and display real-time logs during large conversions

## Error Handling

* If an error occurs, a message will be displayed in the application window
* Ensure the selected PDF file is not corrupted
* Ensure the destination folder is accessible

## Output

* The output file is saved in Markdown (.md) format
* File names are automatically adjusted to prevent overwriting existing files


Author

Name: xmfldksl
Email: xmfldksl@gmail.com
GitHub: https://github.com/xmfldksl

License

This project is licensed under the MIT License - see the LICENSE file for details.


---

# PDF to Markdown Converter v1.1

## 개요

이 애플리케이션은 PDF 문서를 Markdown 형식으로 변환하며 텍스트 구조와 표 레이아웃을 최대한 유지합니다.
중첩된 표를 감지하여 읽기 쉬운 Markdown 형태로 재구성합니다.

## 주요 기능

* PDF 파일에서 텍스트와 표를 추출
* 중첩된 표를 감지하고 상세 섹션으로 분리
* 위에서 아래로 자연스러운 읽기 순서 유지
* 표를 Markdown 형식으로 변환
* 파일 선택 및 실행을 위한 간단한 GUI 제공
* 변환 진행 상황을 실시간으로 표시

## 요구 사항

* 제공된 EXE 파일 사용 시 추가 설치가 필요 없음
* Windows 환경에서 실행 가능

## 사용 방법

1. 실행 파일을 실행
2. 변환할 PDF 파일 선택
3. 결과를 저장할 폴더 선택
4. "Convert PDF to MD" 버튼 클릭
5. 변환 완료까지 대기
6. Markdown 파일이 자동으로 저장됨

## 참고 사항

* 복잡한 PDF 구조에서는 예상과 다른 결과가 나올 수 있음
* 표 감지는 좌표 기반 분석으로 PDF 품질에 따라 결과가 달라질 수 있음
* 대용량 PDF는 처리 시간이 길어질 수 있음
* **PDF는 반드시 텍스트 기반으로 생성되어야 하며(OCR 불가), 이미지 기반 PDF는 지원하지 않음**

## v1.1 업데이트 사항

* CPU 사용률 옵션 제거 (단일 스레드로 동작)
* 글자 중복 병합: `dedupe_chars(tolerance=2)` 적용으로 PPT 그림자 효과 등으로 인한 중복 추출 방지
* 중복 키워드 정제: `dict.fromkeys` 로직 도입으로 자식 표 안내 문구에서 동일 키워드 반복 출력 문제 해결 (추측)
* 마크다운 표 구조 보호: 셀 내부의 `|` 문자를 `\|`로 이스케이프 처리하여 열 구조 깨짐 방지
* 좌표 안전 클램핑: `get_safe_bbox` 함수 적용으로 PDF 범위를 벗어난 좌표로 인한 Runtime Error 방지
* 유령 표 출력 방지: `has_content` 검사로 내용 없는 빈 표가 출력되지 않도록 개선
* 비차단 GUI 스레딩: `threading` 모듈 적용으로 대용량 처리 중에도 UI 멈춤 없이 로그 출력

## 오류 처리

* 오류 발생 시 애플리케이션 화면에 메시지가 표시됨
* PDF 파일이 손상되지 않았는지 확인 필요
* 저장 폴더 접근 권한 확인 필요

## 출력 결과

* 결과 파일은 Markdown(.md) 형식으로 저장됨
* 기존 파일 덮어쓰기를 방지하기 위해 파일명이 자동 조정됨


제작자

이름: xmfldksl
이메일: xmfldksl@gmail.com
깃허브: https://github.com/xmfldksl

라이선스

이 프로젝트는 MIT 라이선스를 따릅니다. 자세한 내용은 LICENSE 파일을 확인하세요.
