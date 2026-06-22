import os # 운영체제 환경 변수를 설정하고 제어하기 위한 파이썬 내장 모듈을 가져옵니다.
import re # cid 깨짐 문자열을 정규식으로 탐지하기 위한 내장 모듈을 가져옵니다.
import warnings # 실행 중 발생하는 내부 경고 메시지를 필터링하기 위한 내장 모듈을 가져옵니다.
import pdfplumber # PDF 문서 구조를 분석하고 데이터를 추출하기 위한 외부 라이브러리를 가져옵니다.

os.environ["TQDM_DISABLE"] = "1" # 콘솔창 진행률 상태바 출력을 강제로 비활성화합니다.
warnings.filterwarnings("ignore", category=UserWarning) # 내부 경고를 무시하도록 필터를 설정합니다.

CID_PATTERN = re.compile(r'\(cid:\d+\)') # ToUnicode 정보가 없을 때 글자 대신 추출되는 (cid:숫자) 형태를 찾기 위한 정규식을 미리 컴파일합니다.
CID_BROKEN_THRESHOLD = 0.3 # 한 페이지에서 cid가 차지하는 비율이 이 값을 넘으면 변환 불가 페이지로 판정하는 기준입니다.
UNCONVERTIBLE_MARK = "[변환 불가 페이지]" # 글꼴 정보 누락으로 변환할 수 없는 페이지를 결과물에서 대체할 표기 문구입니다.

def cid_ratio(text):
    # 주어진 텍스트에서 cid로 깨진 문자가 차지하는 비율을 계산하는 함수를 정의합니다.
    if not text: # 빈 텍스트라면.
        return 0.0 # 비율을 0으로 반환합니다.
    cid_chars = sum(len(m) for m in CID_PATTERN.findall(text)) # cid 토큰들이 차지하는 전체 글자 수를 합산합니다.
    nonspace = len(re.sub(r'\s', '', text)) # 공백을 제외한 실제 글자 수를 셉니다.
    return cid_chars / max(nonspace, 1) # cid 비율을 계산하여 반환합니다.

def is_cid_broken(text):
    # 텍스트가 cid 깨짐으로 판정될 만큼 cid 비율이 높은지 여부를 반환하는 함수를 정의합니다.
    return cid_ratio(text) >= CID_BROKEN_THRESHOLD # 기준 비율 이상이면 참을 반환합니다.

def is_inside(inner_bbox, outer_bbox, margin=5):
    # 첫 번째 좌표 영역이 두 번째 좌표 영역 안에 지정된 오차 범위 내로 포함되는지 검사하는 함수를 정의합니다.
    ix0, iy0, ix1, iy1 = inner_bbox # 내부 상자의 좌표를 변수에 저장합니다.
    ox0, oy0, ox1, oy1 = outer_bbox # 외부 상자의 좌표를 변수에 저장합니다.
    return (ix0 >= ox0 - margin) and (iy0 >= oy0 - margin) and \
           (ix1 <= ox1 + margin) and (iy1 <= oy1 + margin) # 내부에 위치하는지 논리 연산하여 반환합니다.

def is_char_inside(char_obj, bbox):
    # 단일 글자 객체의 중심점 좌표가 특정 박스 영역 내부에 존재하는지 판별하는 함수를 정의합니다.
    cx = (char_obj["x0"] + char_obj["x1"]) / 2 # 가로 중심점을 계산합니다.
    cy = (char_obj["top"] + char_obj["bottom"]) / 2 # 세로 중심점을 계산합니다.
    bx0, btop, bx1, bbottom = bbox # 대상 박스의 4개 좌표를 분리하여 할당합니다.
    return (bx0 <= cx <= bx1) and (btop <= cy <= bbottom) # 박스 경계선 내부에 들어오는지 확인하여 반환합니다.

def get_safe_bbox(bbox, page):
    # 추출 영역이 실제 PDF 페이지 경계를 벗어나지 않도록 좌표를 강제로 보정하는 함수를 정의합니다.
    page_x0, page_top, page_x1, page_bottom = page.bbox # 페이지가 원점에서 시작하지 않는 경우까지 대비해 실제 페이지 경계 좌표를 가져옵니다.
    x0, top, x1, bottom = bbox # 원본 좌표 4개를 분리하여 저장합니다.
    x0 = max(page_x0, min(x0, page_x1)) # 좌측 x좌표를 페이지 좌우 경계 내로 제한합니다.
    x1 = max(page_x0, min(x1, page_x1)) # 우측 x좌표를 페이지 좌우 경계 내로 제한합니다.
    top = max(page_top, min(top, page_bottom)) # 상단 y좌표를 페이지 상하 경계 내로 제한합니다.
    bottom = max(page_top, min(bottom, page_bottom)) # 하단 y좌표를 페이지 상하 경계 내로 제한합니다.

    if x0 >= x1 or top >= bottom: # 면적이 0 이하의 비정상적인 상태가 되었는지 검사합니다.
        return None # None 객체를 반환합니다.
    return (x0, top, x1, bottom) # 최종 좌표를 튜플 형태로 묶어 반환합니다.

def build_edge_settings(page, margin=3):
    # 좌우 테두리가 투명한 표의 양쪽 끝 열 누락을 막기 위해, 수평선의 양 끝 좌표에 가상 수직선을 주입하는 표 탐지 설정을 생성하는 함수를 정의합니다.
    base_tables = page.find_tables() # 기본 설정으로 1차 표 탐지를 수행하여 표 영역 후보를 확보합니다.
    if not base_tables: # 페이지에 표가 하나도 없다면.
        return None # 보정이 불필요하므로 None을 반환합니다.

    h_edges = [e for e in page.edges if e["orientation"] == "h"] # 선과 사각형에서 추출된 모든 수평 성분을 수집합니다.
    synthetic_lines = [] # 주입할 가상 수직선들을 담을 빈 리스트를 생성합니다.
    for t in base_tables: # 탐지된 표 영역들을 하나씩 순회합니다.
        x0, top, x1, bottom = t.bbox # 표 영역의 좌표 4개를 분리하여 저장합니다.
        local_edges = [e for e in h_edges if top - margin <= e["top"] <= bottom + margin] # 해당 표의 세로 범위에 속한 수평선만 골라냅니다.
        if not local_edges: # 수평선이 전혀 없는 표라면.
            continue # 기준 좌표를 만들 수 없으므로 건너뜁니다.

        edge_x_min = min(e["x0"] for e in local_edges) # 수평선들의 좌측 최소 x좌표를 계산합니다.
        edge_x_max = max(e["x1"] for e in local_edges) # 수평선들의 우측 최대 x좌표를 계산합니다.
        for x in (edge_x_min, edge_x_max): # 좌측 끝과 우측 끝 두 위치를 각각 처리합니다.
            synthetic_lines.append({ # 표의 세로 범위만큼만 이어지는 가상 수직선 객체를 추가합니다.
                "object_type": "line", # pdfplumber가 선 객체로 인식하도록 유형을 지정합니다.
                "x0": x, "x1": x, # 수직선이므로 시작과 끝의 x좌표를 동일하게 설정합니다.
                "top": top - margin, "bottom": bottom + margin, # 표의 상단부터 하단까지 약간의 여유를 두고 연장합니다.
                "y0": page.height - (bottom + margin), # PDF 좌표계 기준의 하단 y좌표를 계산하여 기록합니다.
                "y1": page.height - (top - margin), # PDF 좌표계 기준의 상단 y좌표를 계산하여 기록합니다.
                "width": 0, # 수직선의 가로 폭은 0으로 지정합니다.
                "height": (bottom - top) + 2 * margin, # 선의 세로 길이를 계산하여 기록합니다.
            })

    if not synthetic_lines: # 주입할 가상 수직선이 하나도 만들어지지 않았다면.
        return None # 기본 탐지 방식을 그대로 사용하도록 None을 반환합니다.
    return { # 기존 괘선 탐지에 가상 수직선을 추가로 결합하는 설정 딕셔너리를 반환합니다.
        "vertical_strategy": "lines", # 수직 경계는 기존 괘선 기반 탐지를 유지합니다.
        "horizontal_strategy": "lines", # 수평 경계도 기존 괘선 기반 탐지를 유지합니다.
        "explicit_vertical_lines": synthetic_lines, # 양쪽 끝 보정용 가상 수직선 목록을 명시적으로 주입합니다.
    }

def format_page_ranges(pages):
    # 깨진 페이지 번호 리스트를 받아 연속 구간으로 압축한 문자열로 만드는 함수를 정의합니다.
    if not pages: # 깨진 페이지가 하나도 없다면.
        return "" # 빈 문자열을 반환합니다.
    ordered = sorted(set(pages)) # 중복을 없애고 오름차순으로 정렬합니다.
    ranges = [] # 압축된 구간들을 담을 리스트를 생성합니다.
    start = prev = ordered[0] # 첫 페이지를 구간 시작과 직전 값으로 초기화합니다.
    for p in ordered[1:]: # 두 번째 페이지부터 순회합니다.
        if p == prev + 1: # 직전 페이지와 연속된다면.
            prev = p # 구간 끝을 현재 페이지로 확장합니다.
        else: # 연속이 끊겼다면.
            ranges.append((start, prev)) # 지금까지의 구간을 저장합니다.
            start = prev = p # 새 구간을 현재 페이지로 시작합니다.
    ranges.append((start, prev)) # 마지막 구간을 저장합니다.
    return ", ".join(f"{a}-{b}" if a != b else f"{a}" for a, b in ranges) # 각 구간을 'a-b' 또는 단일 'a' 형태로 이어 붙여 반환합니다.

def extract_sequential_content(pdf_path, progress_callback=None, log_callback=None):
    # PDF 경로를 받아 텍스트와 표를 추출하고 마크다운 문자열로 반환하는 메인 추출 함수를 정의합니다.
    md_output = "" # 최종 결과물이 누적될 빈 텍스트 문자열을 초기화합니다.
    broken_pages = [] # cid 깨짐으로 변환 불가 처리된 페이지 번호를 모아둘 리스트를 생성합니다.
    with pdfplumber.open(pdf_path) as pdf: # 전달받은 경로의 PDF 파일을 메모리에 엽니다.
        total_pages = len(pdf.pages) # 전체 페이지 개수를 세어 변수에 저장합니다.
        
        for i, page in enumerate(pdf.pages): # 첫 번째 페이지부터 마지막 페이지까지 순서대로 반복문을 실행합니다.
            page = page.dedupe_chars(tolerance=2) # 중복을 제거합니다.

            page_text = page.extract_text() or "" # 페이지 전체 텍스트를 먼저 추출해 cid 깨짐 여부를 판정할 근거로 삼습니다.
            if is_cid_broken(page_text): # 페이지 대부분이 글꼴 정보 누락으로 cid 깨짐 상태라면.
                broken_pages.append(i + 1) # 사용자 안내용으로 1부터 시작하는 페이지 번호를 기록합니다.
                md_output += UNCONVERTIBLE_MARK + "\n\n" # 표와 텍스트 추출을 건너뛰고 변환 불가 페이지 표기 한 줄로 대체합니다.
                md_output += "---\n\n" # 페이지 구분용 수평선을 삽입합니다.
                if progress_callback: # 콜백 함수가 있다면.
                    progress_callback(int(((i + 1) / total_pages) * 100)) # 진행률을 갱신합니다.
                continue # 이 페이지의 나머지 처리를 모두 건너뛰고 다음 페이지로 넘어갑니다.

            edge_settings = build_edge_settings(page) # 투명 테두리 보정용 표 탐지 설정을 생성합니다.
            all_tables = page.find_tables(edge_settings) if edge_settings else page.find_tables() # 보정 설정이 있다면 적용하고, 없다면 기본 방식으로 모든 표 객체를 탐색합니다.
            all_bboxes = [t.bbox for t in all_tables] # 테두리 좌표값만 별도로 뽑아내어 리스트를 만듭니다.

            child_info = {} # 빈 딕셔너리를 생성합니다.
            for idx_a, t_a in enumerate(all_tables): # '부모 후보 표'들을 순회합니다.
                area_a = (t_a.bbox[2] - t_a.bbox[0]) * (t_a.bbox[3] - t_a.bbox[1]) # 전체 면적을 계산합니다.
                
                for idx_b, t_b in enumerate(all_tables): # '자식 후보 표'들을 순회합니다.
                    if idx_a == idx_b: continue # 동일한 객체라면 건너뜁니다.
                    if is_inside(t_b.bbox, t_a.bbox): # 부모 표의 좌표 안에 포함되는지 확인합니다.
                        if idx_b in child_info and area_a >= child_info[idx_b][2]: # 면적을 비교합니다.
                            continue # 등록을 건너뜁니다.
                        
                        target_keyword = "" # 빈 문자열을 만듭니다.
                        for cell in t_a.cells: # 개별 칸들을 순회합니다.
                            if not cell: continue # 비어있다면 건너뜁니다.
                            
                            if is_inside(t_b.bbox, cell): # 특정 셀 안에 들어있는지 확인합니다.
                                safe_cell = get_safe_bbox(cell, page) # 좌표를 보정합니다.
                                if safe_cell: # 정상적인 영역이라면 내부 로직을 실행합니다.
                                    cell_page = page.within_bbox(safe_cell) # 셀 영역만큼만 잘라냅니다.
                                    kw_text = cell_page.filter( # 객체들을 조건에 따라 필터링합니다.
                                        lambda obj: obj.get("object_type") != "char" or \
                                                    not is_char_inside(obj, t_b.bbox) # 바깥에 위치한 순수 글자 객체만 남깁니다.
                                    ).extract_text() # 글자들만 텍스트로 추출합니다.
                                    if kw_text: # 성공적으로 추출되었다면 조건문을 실행합니다.
                                        first_line_words = kw_text.split('\n')[0].split() # 단어를 쪼개어 리스트로 만듭니다.
                                        raw_keyword = " ".join(first_line_words[:4]).strip() # 처음 4개의 단어만 공백으로 이어붙입니다.
                                        if raw_keyword: # 비어있지 않다면 변수에 저장합니다.
                                            target_keyword = f"'{raw_keyword}'" # 양쪽에 작은따옴표를 씌웁니다.
                                break # 반복문을 빠져나옵니다.
                        child_info[idx_b] = (idx_a, target_keyword, area_a) # 딕셔너리에 저장합니다.

            indexed_tables = list(enumerate(all_tables)) # 튜플 리스트로 변환합니다.
            sorted_tables = sorted(indexed_tables, key=lambda x: x[1].bbox[1]) # 오름차순 정렬합니다.
            last_y = page.bbox[1] # 페이지가 원점에서 시작하지 않을 수 있으므로 실제 상단 좌표로 초기화합니다.
            
            parent_to_children = {} # 캐시용 딕셔너리를 생성합니다.
            for child_idx, data in child_info.items(): # 관계 딕셔너리를 순회합니다.
                parent_idx, keyword, area = data # 정보를 각각 분리합니다.
                if parent_idx not in parent_to_children: # 존재하지 않는다면.
                    parent_to_children[parent_idx] = [] # 빈 리스트를 새로 만듭니다.
                parent_to_children[parent_idx].append((child_idx, all_tables[child_idx].bbox, keyword)) # 정보를 추가합니다.
            
            for original_idx, table_obj in sorted_tables: # 표 객체들을 하나씩 꺼내어 처리합니다.
                current_top = table_obj.bbox[1] # 상단 Y좌표를 변수에 저장합니다.
                
                if current_top > last_y: # 일반 텍스트가 존재한다면.
                    safe_area = get_safe_bbox((page.bbox[0], last_y, page.bbox[2], current_top), page) # 좌표를 보정합니다.
                    if safe_area: # 정상이라면 텍스트 추출을 시작합니다.
                        clean_text = page.within_bbox(safe_area).filter( # 필터를 적용합니다.
                            lambda o: o.get("object_type") != "char" or \
                                      not any(is_char_inside(o, b) for b in all_bboxes) # 순수 글자만 필터링합니다.
                        ).extract_text() # 일반 텍스트를 모두 추출합니다.
                        if clean_text and clean_text.strip(): # 문자를 포함하고 있다면 조건문을 실행합니다.
                            md_output += clean_text.strip() + "\n\n" # 결과물 문자열에 텍스트를 추가합니다.

                if original_idx in child_info: # 자식 표라면 단순 추출을 진행합니다.
                    table_data = table_obj.extract() # 2차원 리스트로 모두 추출합니다.
                else: # 독립된 표이거나 부모 표라면 상세 분석을 진행합니다.
                    my_children = parent_to_children.get(original_idx, []) # 자식 표 목록을 불러옵니다.
                    table_data = [] # 빈 리스트를 생성합니다.
                    for row in table_obj.rows: # 행 객체들을 순회합니다.
                        row_data = [] # 빈 리스트를 생성합니다.
                        for cell_bbox in row.cells: # 개별 칸의 좌표들을 순회합니다.
                            if not cell_bbox: # 비어있다면.
                                row_data.append("") # 빈 문자열을 추가합니다.
                                continue # 다음 칸으로 넘어갑니다.

                            safe_cell_bbox = get_safe_bbox(cell_bbox, page) # 좌표가 안전한지 검사하고 보정합니다.
                            if safe_cell_bbox: # 정상적으로 보정된 셀 좌표라면 추출을 시작합니다.
                                cell_page = page.within_bbox(safe_cell_bbox) # 해당 셀 크기만큼만 오려냅니다.
                                contained_children = [child for child in my_children if is_inside(child[1], cell_bbox, margin=10)] # 자식 표가 들어있는지 검사합니다.

                                if contained_children: # 자식 표가 존재한다면 조건문을 실행합니다.
                                    filtered_page = cell_page.filter( # 필터를 적용합니다.
                                        lambda obj: obj.get("object_type") != "char" or \
                                                    not any(is_char_inside(obj, child[1]) for child in contained_children) # 글자 객체는 모두 삭제합니다.
                                    )
                                    raw_text = filtered_page.extract_text() or "" # 부모 셀 본연의 텍스트만 추출합니다.
                                    
                                    kw_list = list(dict.fromkeys([child[2] for child in contained_children if child[2]])) # 중복 없이 리스트화합니다.
                                    kw_str = ", ".join(kw_list) # 하나의 문자열로 만듭니다.
                                    
                                    clean_text = raw_text.replace('\n', '<br>').replace('|', '\\|').strip() # 파이프 기호를 이스케이프 처리합니다.
                                    if clean_text: # 부모 텍스트가 존재한다면 자식 표 안내 문구를 결합합니다.
                                        ref_str = f" [{kw_str} Details below]" if kw_str else " [Details below]" 
                                        text = clean_text + ref_str # 안내 문구를 합칩니다.
                                    else: # 텅 빈 상태라면.
                                        text = "" # 텍스트를 완전히 비웁니다.
                                else: # 평범한 단일 칸이라면 일반 추출을 진행합니다.
                                    text = (cell_page.extract_text() or "").replace('\n', '<br>').replace('|', '\\|').strip() # 치환하고 공백을 제거합니다.
                            else: # 비정상적인 유령 공간이라면.
                                text = "" # 빈 문자열을 할당합니다.
                            row_data.append(text) # 행 리스트에 추가합니다.
                        table_data.append(row_data) # 전체 표 리스트에 추가합니다.

                has_content = False # 상태 변수를 거짓으로 초기화합니다.
                if table_data: # 데이터가 존재한다면 검사를 시작합니다.
                    check_rows = table_data[1:] if len(table_data) > 1 else table_data # 두 번째 줄부터 잘라냅니다.
                    for row in check_rows: # 검사 대상 행들을 하나씩 순회합니다.
                        if any(str(cell).strip() for cell in row if cell): # 실제 문자가 존재하는지 확인합니다.
                            has_content = True # 상태 변수를 참으로 변경합니다.
                            break # 반복문을 즉시 종료합니다.

                if has_content: # 진짜 표로 판별되었다면 마크다운 문자열 조립을 시작합니다.
                    if original_idx in child_info: # 부모를 가진 자식 표라면 제목을 달아줍니다.
                        _, target_keyword, _ = child_info[original_idx] # 키워드 문자열만 빼옵니다.
                        if target_keyword: # 빈 문자열이 아니라면 제목 라인을 출력합니다.
                            md_output += f"> **{target_keyword}** Details\n\n" # 제목을 누적 결과물에 추가합니다.

                    for row_idx, row in enumerate(table_data): # 가로행 단위로 순회합니다.
                        clean_row = [str(cv).replace('\n', '<br>').replace('|', '\\|').strip() if cv else "" for cv in row] # 문자열 치환을 일괄 수행합니다.
                        md_output += "| " + " | ".join(clean_row) + " |\n" # 마크다운 표의 한 줄을 완성하여 문자열에 추가합니다.
                        if row_idx == 0: # 첫 번째 제목 행이었다면 구분선을 넣어야 합니다.
                            md_output += "| " + " | ".join(["---"] * len(clean_row)) + " |\n" # 구분선 행을 조립해 넣습니다.
                    md_output += "\n" # 줄바꿈을 하나 추가합니다.

                last_y = max(last_y, table_obj.bbox[3]) # 마지막 Y좌표를 현재 표의 맨 밑바닥 좌표로 갱신합니다.

            if last_y < page.bbox[3]: # 하단에 남은 여백 공간이 있다면 검사합니다.
                safe_final = get_safe_bbox((page.bbox[0], last_y, page.bbox[2], page.bbox[3]), page) # 좌표를 안전하게 보정합니다.
                if safe_final: # 정상이라면 텍스트 추출을 시작합니다.
                    final_text = page.within_bbox(safe_final).filter( # 객체 필터를 적용합니다.
                        lambda o: o.get("object_type") != "char" or \
                                  not any(is_char_inside(o, b) for b in all_bboxes) # 글자 객체를 철저히 배제합니다.
                    ).extract_text() # 순수한 하단 텍스트를 추출합니다.
                    if final_text and final_text.strip(): # 실제 글자를 포함하고 있다면 조건문을 실행합니다.
                        md_output += final_text.strip() + "\n\n" # 본문 끝에 추가합니다.
        
            md_output += "---\n\n" # 마크다운 수평선 구분 기호를 삽입합니다.

            if progress_callback: # 콜백 함수가 인자로 들어왔는지 확인합니다.
                current_percent = int(((i + 1) / total_pages) * 100) # 퍼센트를 산출합니다.
                progress_callback(current_percent) # 정수 형태로 값을 전송합니다.
            
    if log_callback and broken_pages: # 로그 콜백이 있고 변환 불가 페이지가 하나라도 있었다면.
        summary = f"변환 불가 {len(broken_pages)}페이지: {format_page_ranges(broken_pages)}" # 깨진 페이지 수와 구간 요약 문구를 만듭니다.
        log_callback(summary) # 변환이 끝난 뒤 요약을 한 번 전달합니다.

    return md_output # 최종 마크다운 문자열 덩어리를 호출자에게 반환합니다.