import os # 운영체제(OS)의 환경 변수 및 파일 경로를 제어하기 위한 파이썬 표준 내장 모듈을 불러옵니다.
import warnings # 프로그램 실행 중 발생하는 불필요한 내부 경고 메시지를 숨기기 위한 모듈을 불러옵니다.
import pdfplumber # PDF 파일 내의 텍스트, 표, 좌표 정보를 추출하기 위한 외부 라이브러리를 불러옵니다.
import datetime # 현재 날짜와 시간 정보를 가져와 로그 기록용 타임스탬프를 생성하기 위한 모듈을 불러옵니다.
import threading # 메인 GUI 창이 멈추지 않도록 무거운 변환 작업을 별도의 백그라운드 스레드에서 실행하기 위한 모듈입니다.
import tkinter as tk # 윈도우용 그래픽 사용자 인터페이스(GUI)를 생성하고 조작하는 파이썬 기본 라이브러리를 불러옵니다.
from tkinter import filedialog, messagebox, scrolledtext # 파일 선택창, 알림 팝업창, 스크롤 가능한 텍스트 창 위젯을 불러옵니다.
import multiprocessing # 실행 중인 시스템의 코어 확인 및 다중 프로세싱 오류 방지를 위한 모듈을 불러옵니다.

# 시스템 환경 변수 및 경고 메시지 설정
os.environ["TQDM_DISABLE"] = "1" # 터미널 화면에 진행률 상태바가 지저분하게 자동 출력되는 것을 강제로 차단합니다.
warnings.filterwarnings("ignore", category=UserWarning) # 사용자에게 보여줄 필요가 없는 내부 모듈의 경고 메시지를 무시하도록 설정합니다.

def is_inside(inner_bbox, outer_bbox, margin=5):
    # 첫 번째 좌표 영역이 두 번째 좌표 영역 안에 지정된 오차 범위 내로 완전히 포함되는지 검사하는 함수입니다.
    ix0, iy0, ix1, iy1 = inner_bbox # 내부 박스의 좌측, 상단, 우측, 하단 좌표값을 각각 분리하여 저장합니다.
    ox0, oy0, ox1, oy1 = outer_bbox # 외부 박스의 좌측, 상단, 우측, 하단 좌표값을 각각 분리하여 저장합니다.
    return (ix0 >= ox0 - margin) and (iy0 >= oy0 - margin) and \
           (ix1 <= ox1 + margin) and (iy1 <= oy1 + margin) # 내부 박스의 모든 모서리가 외부 박스 경계선 안쪽에 모두 위치하면 참(True)을 반환합니다.

def is_char_inside(char_obj, bbox):
    # PDF 상의 단일 글자 객체의 중심점 좌표를 계산하여 특정 박스 영역 안에 들어가는지 판별하는 함수입니다.
    cx = (char_obj["x0"] + char_obj["x1"]) / 2 # 글자의 좌측 좌표와 우측 좌표를 더한 후 2로 나누어 가로 중심점을 구합니다.
    cy = (char_obj["top"] + char_obj["bottom"]) / 2 # 글자의 상단 좌표와 하단 좌표를 더한 후 2로 나누어 세로 중심점을 구합니다.
    bx0, btop, bx1, bbottom = bbox # 비교할 대상 박스의 좌표 4개를 분리하여 각각의 변수에 저장합니다.
    return (bx0 <= cx <= bx1) and (btop <= cy <= bbottom) # 계산된 중심점이 박스 경계선 내부에 완벽히 포함되면 참을 반환합니다.

# 비정상적인 PDF 메타데이터 좌표로 인한 에러를 막기 위한 좌표 클램핑 보호 함수
def get_safe_bbox(bbox, page_width, page_height):
    # 영역이 실제 PDF 페이지 크기를 벗어나지 않도록 좌표를 강제로 보정하는 안전 함수입니다.
    x0, top, x1, bottom = bbox # 검사할 원본 좌표를 분리하여 변수에 할당합니다.
    # 좌표가 0보다 작으면 0으로, 페이지 크기보다 크면 페이지 크기로 강제로 맞춥니다.
    x0 = max(0, min(x0, page_width)) # 좌측 X 좌표를 보정합니다.
    top = max(0, min(top, page_height)) # 상단 Y 좌표를 보정합니다.
    x1 = max(0, min(x1, page_width)) # 우측 X 좌표를 보정합니다.
    bottom = max(0, min(bottom, page_height)) # 하단 Y 좌표를 보정합니다.
    # 좌표가 꼬여서 면적이 0 이하가 되어버린 영역이라면 None을 반환하여 에러를 방지합니다.
    if x0 >= x1 or top >= bottom: # 비정상적인 면적이 발생했는지 검사합니다.
        return None # 추출을 포기하고 None을 반환하여 후속 에러를 원천 차단합니다.
    return (x0, top, x1, bottom) # 보정된 최종 좌표를 튜플 형태로 묶어서 반환합니다.

# 실시간 진행률 연동을 위해 progress_callback 매개변수를 추가
def extract_sequential_content(pdf_path, progress_callback=None):
    # PDF 경로를 입력받아 텍스트와 표를 추출하고 마크다운으로 조합하여 반환하는 핵심 함수입니다.
    md_output = "" # 생성된 문서 내용이 누적될 빈 문자열을 초기화합니다.
    with pdfplumber.open(pdf_path) as pdf: # 원본 PDF 파일을 엽니다
        total_pages = len(pdf.pages) # 전체 페이지 수를 파악하여 변수에 저장합니다
        
        for i, page in enumerate(pdf.pages): # 전체 페이지를 순서대로 반복 탐색합니다.
            page = page.dedupe_chars(tolerance=2) # 페이지 내에서 좌표가 2포인트(약 0.7밀리미터) 이하로 겹치는 중복 글자(그림자 효과 등)를 하나로 병합하여 중복 추출을 막습니다.
            all_tables = page.find_tables() # 현재 페이지에 존재하는 모든 표 객체들을 찾아옵니다
            all_bboxes = [t.bbox for t in all_tables] # 찾은 표들에서 좌표값만 뽑아내어 리스트로 만듭니다.

            child_info = {} # 표 안에 표가 중첩된 경우 관계성을 저장하기 위한 빈 딕셔너리를 생성합니다.
            for idx_a, t_a in enumerate(all_tables): # 첫 번째 비교 대상인 '부모 후보 표'를 선택합니다.
                # 부모 표의 면적을 계산하여 가장 작은 표만 부모로 인정하도록 기준 면적을 구합니다.
                area_a = (t_a.bbox[2] - t_a.bbox[0]) * (t_a.bbox[3] - t_a.bbox[1]) # 가로와 세로 길이를 곱하여 전체 면적을 산출합니다.
                
                for idx_b, t_b in enumerate(all_tables): # 두 번째 비교 대상인 '자식 후보 표'를 선택합니다.
                    if idx_a == idx_b: continue # 비교 대상이 자기 자신이라면 무시하고 다음으로 넘어갑니다.
                    if is_inside(t_b.bbox, t_a.bbox): # 자식 좌표가 부모 좌표 안에 완전히 포함된다면.
                        
                        # 새로 찾은 부모 후보 면적이 기존 부모보다 크다면 직속 부모가 아니므로 건너뜜.
                        if idx_b in child_info and area_a >= child_info[idx_b][2]: # 기존 등록된 면적과 비교합니다.
                            continue # 더 바깥쪽에 있는 표이므로 등록하지 않고 넘어갑니다.
                        
                        target_keyword = "" 
                        for cell in t_a.cells: # 부모 표의 모든 셀 좌표들을 하나씩 검사합니다.
                            # 표 안에 빈 셀 등 None 데이터가 들어올 경우의 TypeError를 방어합니다.
                            if not cell: continue # 좌표가 비어있다면 에러 방지를 위해 넘어갑니다.
                            
                            if is_inside(t_b.bbox, cell): # 자식 표 전체가 현재 특정 셀 안에 들어있는지 확인합니다.
                                safe_cell = get_safe_bbox(cell, page.width, page.height) # 셀 좌표가 안전한지 검사하고 클램핑합니다.
                                if safe_cell: # 보정된 셀 영역이 정상적이라면.
                                    cell_page = page.within_bbox(safe_cell) # 해당 셀 영역만큼만 PDF 페이지를 잘라냅니다
                                    # 잘라낸 부모 셀 안에서 글자들을 걸러냅니다.
                                    kw_text = cell_page.filter( # 객체들을 필터링합니다
                                        lambda obj: obj.get("object_type") != "char" or \
                                                    not is_char_inside(obj, t_b.bbox) # 자식 표 바깥에 있는 글자만 통과시킵니다.
                                    ).extract_text() # 조건 통과 텍스트만 추출합니다
                                    if kw_text: 
                                        first_line_words = kw_text.split('\n')[0].split() # 첫 줄을 가져와서 공백 기준으로 단어들을 분리해 리스트로 만듭니다.
                                        # 단어 리스트에서 처음 4개 요소를 가져와 양쪽에 작은따옴표 표시
                                        raw_keyword = " ".join(first_line_words[:4]).strip()
                                        if raw_keyword:
                                            target_keyword = f"'{raw_keyword}'"
                                break # 정확한 부모 셀을 찾았으므로 더 이상 검사하지 않고 강제 탈출합니다.
                        # 현재 면적값도 같이 튜플에 저장합니다.
                        child_info[idx_b] = (idx_a, target_keyword, area_a) # 자식 번호를 키로, 부모 번호, 키워드, 면적을 값으로 저장합니다.

            # 정렬 전에 원본 인덱스를 보존하기 위해 enumerate를 사용하여 튜플 리스트로 변환합니다.
            indexed_tables = list(enumerate(all_tables))
            sorted_tables = sorted(indexed_tables, key=lambda x: x[1].bbox[1]) # 표 객체들을 세로 Y좌표 기준으로 오름차순 정렬합니다.
            last_y = 0 # 중복 추출을 막기 위해 마지막 하단 Y좌표 위치를 0으로 초기화합니다.
            
            # 부모 표 인덱스를 키로, 자식 표 정보 리스트를 값으로 가지는 딕셔너리를 미리 생성하여 탐색 비용을 줄입니다.
            parent_to_children = {}
            for child_idx, data in child_info.items():
                parent_idx, keyword, area = data
                if parent_idx not in parent_to_children:
                    parent_to_children[parent_idx] = []
                parent_to_children[parent_idx].append((child_idx, all_tables[child_idx].bbox, keyword))
            
            for original_idx, table_obj in sorted_tables: # 정렬된 표를 하나씩 순서대로 꺼내어 처리합니다.
                current_top = table_obj.bbox[1] # 현재 표의 맨 위 세로 Y좌표값을 변수에 저장합니다.
                
                if current_top > last_y: # 시작 Y좌표가 마지막 좌표보다 크다면 일반 텍스트 공간이 존재한다는 의미입니다.
                    safe_area = get_safe_bbox((0, last_y, page.width, current_top), page.width, page.height) # 빈 공간 좌표를 안전하게 보정합니다.
                    if safe_area: # 보정된 빈 공간이 정상적이라면.
                        # 이 영역 내에서 특정 조건으로 필터링을 겁니다.
                        clean_text = page.within_bbox(safe_area).filter( # 페이지를 자르고 객체를 필터링합니다
                            lambda o: o.get("object_type") != "char" or \
                                      not any(is_char_inside(o, b) for b in all_bboxes) # 표 위치와 겹치지 않는 순수 글자만 남깁니다.
                        ).extract_text() # 표 밖의 순수 일반 텍스트를 추출합니다
                        if clean_text and clean_text.strip(): # 일반 텍스트 내용이 존재한다면.
                            md_output += clean_text.strip() + "\n\n" # 결과물 문자열에 더한 뒤 줄바꿈을 추가합니다.

                if original_idx in child_info: # 현재 표가 중첩된 자식 표라면.
                    table_data = table_obj.extract() # 별도 필터링 없이 내부 셀 데이터를 그대로 2차원 리스트로 추출합니다
                else: # 현재 표가 독립된 표이거나 자식을 품은 부모 표라면.
                    # 미리 생성해둔 딕셔너리에서 O(1) 시간 복잡도로 자식 표 목록을 가져옵니다.
                    my_children = parent_to_children.get(original_idx, []) 
                    table_data = [] # 행과 열 데이터를 담을 빈 2차원 리스트를 생성합니다.
                    for row in table_obj.rows: # 표의 행 객체들을 탐색합니다.
                        row_data = [] # 셀 데이터를 담을 빈 1차원 리스트를 생성합니다.
                        for cell_bbox in row.cells: # 개별 칸 영역을 탐색합니다.
                            if not cell_bbox: # 현재 칸의 좌표가 비어있다면.
                                row_data.append("") # 행 데이터에 빈 문자열만 넣습니다.
                                continue # 텍스트 추출 로직을 무시하고 다음 칸으로 넘어갑니다.

                            safe_cell_bbox = get_safe_bbox(cell_bbox, page.width, page.height) # 추출 좌표가 안전한지 검사하고 자릅니다.
                            if safe_cell_bbox: # 정상적인 유효한 칸 영역이라면.
                                cell_page = page.within_bbox(safe_cell_bbox) # 칸 영역만큼만 PDF 페이지를 오려냅니다
                                # 튜플의 인덱스 1번을 사용하여 자식 표 포함 여부를 비교합니다.
                                contained_children = [child for child in my_children if is_inside(child[1], cell_bbox, margin=10)] # 내부에 자식 표가 존재하는지 확인합니다.

                                if contained_children: # 자식 표가 하나라도 포함되어 있다면.
                                    filtered_page = cell_page.filter( # 칸 영역 내 객체들을 필터링합니다
                                        lambda obj: obj.get("object_type") != "char" or \
                                                    not any(is_char_inside(obj, child[1]) for child in contained_children) # 자식 표 위치와 겹치는 글자들은 전부 무시합니다.
                                    )
                                    raw_text = filtered_page.extract_text() or "" # 나머지 부모 텍스트만 추출하며 실패 시 빈 문자열을 넣습니다.
                                    
                                    # 중복된 키워드가 리스트에 나타나는 현상을 방지하기 위해 dict.fromkeys로 순서 유지 및 중복 제거
                                    kw_list = list(dict.fromkeys([child[2] for child in contained_children if child[2]]))
                                    kw_str = ", ".join(kw_list) # 여러 키워드를 쉼표 기호로 이어 붙입니다.
                                    
                                    # 줄바꿈 처리 및 마크다운 세로막대 이스케이프 적용 (\\| 사용)
                                    clean_text = raw_text.replace('\n', '<br>').replace('|', '\\|').strip() 
                                    # 원문이 존재할 때만 안내 문구를 붙이고, 완전히 빈 칸이면 그대로 비워둠
                                    if clean_text:
                                        ref_str = f" [{kw_str} Details below]" if kw_str else " [Details below]"
                                        text = clean_text + ref_str
                                    else:
                                        text = ""
                                else: # 자식 표가 존재하지 않는 단일 칸이라면.
                                    # 텍스트 추출 후 줄바꿈과 세로막대 이스케이프 처리 (\\| 사용)
                                    text = (cell_page.extract_text() or "").replace('\n', '<br>').replace('|', '\\|').strip() 
                            else: # 칸 좌표가 유령 영역으로 판별되었다면.
                                text = "" # 에러가 날 좌표 공간이므로 빈 텍스트 처리합니다.
                            row_data.append(text) # 정제된 문자열을 행 데이터 리스트에 추가합니다.
                        table_data.append(row_data) # 완성된 행 리스트를 표 데이터에 추가합니다.

                has_content = False # 유령 표가 아닌지 검사하기 위한 상태 변수를 초기화합니다.
                if table_data: # 추출을 완료한 리스트 구조가 하나라도 존재한다면.
                    check_rows = table_data[1:] if len(table_data) > 1 else table_data # 첫 줄을 제외한 행들을 검사 대상으로 지정합니다.
                    for row in check_rows: # 검사 대상 행들을 탐색합니다.
                        if any(str(cell).strip() for cell in row if cell): # 실제 글자가 하나라도 존재한다면.
                            has_content = True # 유효한 표라고 판별하고 상태 변수를 참으로 바꿉니다.
                            break # 더 이상 검사하지 않고 반복문을 탈출합니다.

                if has_content: # 현재 표가 진짜 내용이 존재하는 유효한 표라면.
                    if original_idx in child_info: # 부모 표에 종속된 자식 표라면.
                        # 튜플 인덱스 1번에서 타겟 키워드를 꺼내옵니다.
                        _, target_keyword, _ = child_info[original_idx] # 키워드 문자열만 빼옵니다.
                        # 추출된 키워드가 존재할 때만 자식 표의 마크다운 제목을 출력 (이미 따옴표 포함됨)
                        if target_keyword:
                            md_output += f"> **{target_keyword}** Details\n\n" 
                    
                    for row_idx, row in enumerate(table_data): # 데이터를 실제 마크다운 텍스트로 변환하기 위해 반복합니다.
                        # 모든 셀의 줄바꿈과 파이프 기호를 이스케이프 처리 (\\| 사용)
                        clean_row = [str(cv).replace('\n', '<br>').replace('|', '\\|').strip() if cv else "" for cv in row] 
                        md_output += "| " + " | ".join(clean_row) + " |\n" # 파이프 기호를 넣어 마크다운 행 구조를 완성시킵니다.
                        if row_idx == 0: # 변환한 행이 제목 행이라면.
                            md_output += "| " + " | ".join(["---"] * len(clean_row)) + " |\n" # 마크다운 가로줄 기호 행을 삽입해 줍니다.
                    md_output += "\n" # 표 처리가 끝났으므로 줄바꿈을 넣어줍니다.

                last_y = max(last_y, table_obj.bbox[3]) # 표 건너뛰기를 위해 맨 하단 좌표값을 갱신합니다.

            if last_y < page.height: # 페이지 하단에 처리되지 않은 여백이 남아있다면.
                safe_final = get_safe_bbox((0, last_y, page.width, page.height), page.width, page.height) # 남은 영역 좌표를 안전하게 보정합니다.
                if safe_final: # 보정된 영역이 정상적이라면.
                    final_text = page.within_bbox(safe_final).filter( # 잘라내고 필터링을 겁니다
                        lambda o: o.get("object_type") != "char" or \
                                  not any(is_char_inside(o, b) for b in all_bboxes) # 겹쳐 있는 글자들은 철저히 무시합니다.
                    ).extract_text() # 순수한 하단 텍스트를 추출합니다
                    if final_text and final_text.strip(): # 텍스트가 실제로 존재한다면.
                        md_output += final_text.strip() + "\n\n" # 최종 마크다운 문자열 맨 끝에 추가합니다.
        
            md_output += "---\n\n" # 페이지 처리가 끝났음을 표시하기 위해 수평선을 삽입합니다.

            # 진짜 퍼센트를 계산하여 화면으로 전송합니다.
            if progress_callback: # GUI로 쏴주는 콜백 함수가 전달되었다면.
                current_percent = int(((i + 1) / total_pages) * 100) # 백분율 수치로 환산합니다.
                progress_callback(current_percent) # 산출된 정수 숫자를 업데이트 함수로 전송합니다.
            
    return md_output # 완성된 전체 데이터를 반환합니다.

class PDFApp:
    def __init__(self, root):
        # 윈도우 그래픽 프로그램 초기화 생성자 함수입니다.
        self.root = root # 윈도우 창 객체를 전역 변수로 할당합니다.
        self.root.title("PDF to Markdown Converter v1.1") # 제목 표시줄 텍스트를 설정합니다.
        self.root.geometry("402x650") # 황금 비율로 설정합니다.
        self.root.resizable(False, False) # 창 크기 임의 조절 잠금을 겁니다.

        self.pdf_path = tk.StringVar() # PDF 파일 경로를 실시간으로 저장하는 전용 변수입니다.
        self.save_dir = tk.StringVar() # 마크다운 저장 폴더 경로를 실시간으로 저장하는 전용 변수입니다.
    
        tk.Label(root, text="Select PDF", font=("Arial", 10, "bold")).pack(pady=(15, 5)) # 용도를 안내하는 텍스트 라벨을 배치합니다.
        
        file_frame = tk.Frame(root) # 입력창과 버튼을 나란히 배치하기 위한 프레임을 만듭니다.
        file_frame.pack(fill=tk.X, padx=15) # 프레임을 창 가로 전체 너비에 꽉 차게 배치합니다.

        self.pdf_entry = tk.Entry(file_frame, textvariable=self.pdf_path) # 텍스트 입력창 위젯을 만듭니다.
        self.pdf_entry.pack(side=tk.LEFT, fill=tk.X, expand=True) # 남는 빈 가로 공간을 입력창이 차지하도록 확장 배치합니다.
        tk.Button(file_frame, text="...", command=self.select_pdf, width=4).pack(side=tk.RIGHT, padx=(5, 0)) # 파일 탐색기를 띄우는 버튼을 우측 정렬로 배치합니다.

        tk.Label(root, text="Select Folder to Save MD", font=("Arial", 10, "bold")).pack(pady=(15, 5)) # 용도를 안내하는 텍스트 라벨을 배치합니다.
        
        dir_frame = tk.Frame(root) # 두 번째 보조 프레임을 하단에 생성합니다.
        dir_frame.pack(fill=tk.X, padx=15) # 프레임을 가로 전체를 채우도록 설정합니다.

        self.dir_entry = tk.Entry(dir_frame, textvariable=self.save_dir) # 저장 폴더 경로 텍스트 입력창 위젯을 만듭니다.
        self.dir_entry.pack(side=tk.LEFT, fill=tk.X, expand=True) # 폴더 경로 입력창을 남는 공간을 모두 차지하도록 확장 배치합니다.
        tk.Button(dir_frame, text="...", command=self.select_dir, width=4).pack(side=tk.RIGHT, padx=(5, 0)) # 폴더 탐색기를 띄우는 버튼을 맞춥니다.

        self.start_btn = tk.Button(root, text="Convert PDF to MD", bg="#C0C0C0", fg="black", 
                                   font=("Arial", 12, "bold"), height=2, command=self.start_thread) # 실행시킬 메인 실행 버튼 위젯을 생성합니다.
        self.start_btn.pack(fill=tk.X, padx=100, pady=(20, 10)) # 실행 버튼이 중앙에 자리잡도록 길게 배치합니다.

        tk.Label(root, text="Process Log", font=("Arial", 10)).pack(pady=(5, 5)) # 스크롤 창의 제목 라벨을 배치합니다.
        
        self.log_area = scrolledtext.ScrolledText(root, state='disabled') # 읽기 전용으로 비활성화된 로깅 텍스트 영역을 만듭니다.
        self.log_area.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15)) # 하단 빈 공간 전체를 차지하도록 확장시킵니다.

    def log(self, message):
        # 백그라운드 스레드가 메인 UI 스레드로 조작을 위임하는 헬퍼 함수입니다.
        self.root.after(0, self._log_safe, message) # 스레드 이벤트 루프에 비동기 명령을 큐에 예약합니다.
        
    def _log_safe(self, message):
        # 메인 스레드에 의해서만 안전하게 실행되는 텍스트 창 출력용 내부 로직 함수입니다.
        self.log_area.configure(state='normal') # 메시지 입력을 허용하기 위해 잠금 상태를 풉니다.
        self.log_area.insert(tk.END, f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {message}\n") # 로그 맨 끝에 시간표시와 메시지를 끼워 넣습니다.
        self.log_area.see(tk.END) # 최신 로그를 따라가도록 시야를 이동시킵니다.
        self.log_area.configure(state='disabled') # 텍스트 로그 창을 다시 읽기 전용으로 잠급니다.

    def select_pdf(self):
        # 파일 선택 버튼 동작 연결 함수입니다.
        path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")]) # 파일 선택창을 띄우고 파일 전체 경로를 변수로 받아옵니다.
        if path: # 정상적으로 PDF 파일을 선택했다면.
            self.pdf_path.set(path) # 경로 문자열을 변수에 덮어씌워 텍스트가 표시되게 합니다.
            self.pdf_entry.xview_moveto(1.0) # 경로 맨 끝부분을 보이게 텍스트 커서를 자동 스크롤시킵니다.

    def select_dir(self):
        # 폴더 선택 버튼 연결 함수입니다.
        path = filedialog.askdirectory() # 윈도우 폴더 선택 전용 창을 띄우고 절대 경로 문자열을 받아옵니다.
        if path: # 경로 문자열이 무사히 존재한다면.
            self.save_dir.set(path) # 문자열을 변수에 반영하여 화면에 띄웁니다.
            self.dir_entry.xview_moveto(1.0) # 입력창 맨 오른쪽으로 이동시켜 목적지를 직관적으로 확인하게 합니다.

    def start_thread(self):
        # 메인 버튼 클릭 진입점 함수입니다.
        if not self.pdf_path.get() or not self.save_dir.get(): # 텍스트가 텅 비어있는지 검사합니다.
            messagebox.showwarning("Input Missing", "Please select both a PDF file and a save folder.") # 팝업창을 띄워 경로를 선택하라고 경고합니다.
            return # 강제 종료시킵니다.
        self.start_btn.config(state=tk.DISABLED) # 중복 연타 방지를 위해 메인 버튼을 비활성화시킵니다.
        threading.Thread(target=self.run_process, daemon=True).start() # GUI 응답 없음 방지를 위해 본 작업을 백그라운드 스레드에서 병렬로 시작시킵니다.

    def run_process(self):
        # 변환 및 저장 수행 메인 비즈니스 로직 함수입니다.
        try: # 에러가 터지더라도 강제 종료되지 않도록 예외 처리 블록으로 위험한 코드를 감쌉니다.
            # 무효한 환경변수 설정 로직을 모두 삭제했습니다.
            self.log("-" * 30) # 수평선 기호를 화면에 출력합니다.

            input_pdf = self.pdf_path.get() # PDF 전체 경로 문자열을 가져와 로컬 변수에 저장합니다.
            save_directory = self.save_dir.get() # 목적지 폴더 전체 경로 문자열을 가져와 저장합니다.
            
            original_base_name = os.path.basename(input_pdf) # 순수 파일 이름 부분만 잘라냅니다.
            name_only, _ = os.path.splitext(original_base_name) # 확장자가 빠진 이름 부분만 문자열로 추출합니다.
            ext = ".md" # 확장자 문자열 상수를 지정합니다.
            
            base_name = name_only + ext # 새로운 저장 파일명을 생성합니다.
            output_md = os.path.join(save_directory, base_name) # 저장 경로와 파일명을 안전하게 결합하여 절대 경로를 완성합니다.
            
            counter = 1 # 넘버링 번호 변수를 초기화합니다.
            while os.path.exists(output_md): # 파일 시스템에 같은 이름을 가진 파일이 존재하는지 확인합니다.
                base_name = f"{name_only} ({counter}){ext}" # 숫자를 붙여서 새로운 파일명 문자열을 만듭니다.
                output_md = os.path.join(save_directory, base_name) # 최종 저장 절대 경로를 갱신합니다.
                counter += 1 # 카운터 숫자를 증가시킵니다.
            
            # 초기 메시지 출력을 메인 UI 스레드로 안전하게 위임하는 내부 함수를 선언합니다.
            def _start_progress():
                # 텍스트를 고정하기 위한 UI 함수입니다.
                self.log_area.configure(state='normal') # 창 잠금을 해제합니다.
                self.log_area.insert(tk.END, f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Generating '{base_name}' ... ") # 문구를 입력합니다.
                self.log_area.mark_set("progress_mark", "end-1c") # 끝부분 직전에 progress_mark 투명 마커를 박아넣습니다.
                self.log_area.mark_gravity("progress_mark", tk.LEFT) # 움직이지 않게 왼쪽 고정 위치를 유지하는 중력 속성을 부여합니다.
                self.log_area.see(tk.END) # 스크롤을 맨 끝으로 내립니다.
                self.log_area.configure(state='disabled') # 잠금 처리합니다.
            self.root.after(0, _start_progress) # UI 이벤트 큐에 위임합니다.

            # 실시간 백분율 업데이트 함수 역시 UI 스레드 위임 방식으로 개편했습니다.
            def update_progress(percent):
                # 백분율 숫자를 인자로 받는 외부 콜백 함수입니다.
                def _update(p=percent): # 변수 지연 평가를 막기 위해 로컬 인자로 받습니다.
                    self.log_area.configure(state='normal') # 로그 창 잠금을 풉니다.
                    self.log_area.delete("progress_mark", tk.END) # 마커 이후 퍼센트 숫자들만 정확하게 백스페이스로 지워냅니다.
                    self.log_area.insert("progress_mark", f"{p}%") # 최신 퍼센트 숫자를 새로 적어줍니다.
                    self.log_area.see(tk.END) # 스크롤을 위치시킵니다.
                    self.log_area.configure(state='disabled') # 텍스트 창을 다시 잠급니다.
                self.root.after(0, _update) # 메인 스레드가 안전하게 화면 조작을 위임받아 실행합니다.

            # 메인 데이터 추출 시작 (백그라운드 스레드 환경)
            markdown_content = extract_sequential_content(input_pdf, progress_callback=update_progress) # 함수를 호출하여 마크다운 문자열 데이터를 반환받습니다.
            
            with open(output_md, "w", encoding="utf-8") as f: # 쓰기 모드와 UTF-8 인코딩 방식으로 최종 파일을 엽니다.
                f.write(f"# {base_name}\n") # 대제목을 적어 제목을 기록합니다.
                f.write(f"- Created at: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n") # 작업 날짜 시간을 기록합니다.
                f.write(markdown_content) # 가져온 전체 마크다운 본문을 저장합니다.

            # 파일 저장 완료 후 마지막 엔터 줄바꿈 처리를 안전하게 진행합니다.
            def _finish_progress():
                # 다음 줄로 넘어가기 위한 마무리 UI 함수입니다.
                self.log_area.configure(state='normal') # 잠금 해제합니다.
                self.log_area.insert(tk.END, "\n") # 줄바꿈 기호를 삽입합니다.
                self.log_area.configure(state='disabled') # 잠금을 복구합니다.
            self.root.after(0, _finish_progress) # 메인 스레드에 작업 종료 입력을 지시합니다.

            self.log("Done") # 에러 없이 끝났음을 문자열로 출력합니다.

        except Exception as e: # 런타임 에러가 터지면 예외 객체를 받아냅니다.
            # 예외 상황 줄바꿈 처리도 UI 스레드로 보냅니다.
            def _error_newline():
                # 가독성 확보를 위한 줄바꿈 함수입니다.
                self.log_area.configure(state='normal') # 잠금 해제합니다.
                self.log_area.insert(tk.END, "\n") # 다음 줄로 내립니다.
                self.log_area.configure(state='disabled') # 잠금을 복구합니다.
            self.root.after(0, _error_newline) # 메인 스레드에 긴급 엔터 입력을 지시합니다.
            self.log(f"Error occurred: {e}") # 영어 사유 문구를 로그 창 하단에 출력합니다.
            
            # 에러 경고 팝업창 역시 메인 스레드가 띄우도록 익명 함수로 위임합니다.
            self.root.after(0, lambda e=e: messagebox.showerror("Error", f"An error occurred during processing:\n{e}")) # 메인 스레드가 사용자 화면 중앙에 팝업창을 띄우도록 지시합니다.
        finally: # 에러 유무에 상관없이 이 구문은 최후에 무조건 실행됩니다.
            # 작업 완료 후 버튼 비활성화 상태 해제도 메인 스레드로 위임합니다.
            self.root.after(0, lambda: self.start_btn.config(state=tk.NORMAL)) # 실행 버튼 상태를 복구시킵니다.

if __name__ == "__main__": # 외부 모듈에 불려가지 않고 직접 실행되었을 때만 작동시킵니다.
    multiprocessing.freeze_support() # 윈도우 한정 다중 스레드 복제 버그를 원천 봉쇄합니다.
    root = tk.Tk() # 윈도우 인스턴스 폼 객체를 메모리에 생성합니다.
    app = PDFApp(root) # 빈 윈도우 도화지를 인자로 넘겨주어 클래스를 렌더링시킵니다.
    root.mainloop() # 메인 루프 이벤트를 대기하며 프로그램 생명 주기를 유지시킵니다.