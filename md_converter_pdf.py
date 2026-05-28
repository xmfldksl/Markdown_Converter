import os # 운영체제 환경 변수를 설정하고 제어하기 위한 파이썬 내장 모듈을 가져옵니다.
import warnings # 실행 중 발생하는 내부 경고 메시지를 필터링하기 위한 내장 모듈을 가져옵니다.
import pdfplumber # PDF 문서 구조를 분석하고 데이터를 추출하기 위한 외부 라이브러리를 가져옵니다.

os.environ["TQDM_DISABLE"] = "1" # 콘솔창 진행률 상태바 출력을 강제로 비활성화합니다.
warnings.filterwarnings("ignore", category=UserWarning) # 내부 경고를 무시하도록 필터를 설정합니다.

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

def get_safe_bbox(bbox, page_width, page_height):
    # 추출 영역이 실제 PDF 페이지 크기를 벗어나지 않도록 좌표를 강제로 보정하는 함수를 정의합니다.
    x0, top, x1, bottom = bbox # 원본 좌표 4개를 분리하여 저장합니다.
    x0 = max(0, min(x0, page_width)) # 너비 값으로 제한합니다.
    top = max(0, min(top, page_height)) # 높이 값으로 제한합니다.
    x1 = max(0, min(x1, page_width)) # 한계값 내에 맞춥니다.
    bottom = max(0, min(bottom, page_height)) # 한계값 내에 맞춥니다.
    
    if x0 >= x1 or top >= bottom: # 면적이 0 이하의 비정상적인 상태가 되었는지 검사합니다.
        return None # None 객체를 반환합니다.
    return (x0, top, x1, bottom) # 최종 좌표를 튜플 형태로 묶어 반환합니다.

def extract_sequential_content(pdf_path, progress_callback=None):
    # PDF 경로를 받아 텍스트와 표를 추출하고 마크다운 문자열로 반환하는 메인 추출 함수를 정의합니다.
    md_output = "" # 최종 결과물이 누적될 빈 텍스트 문자열을 초기화합니다.
    with pdfplumber.open(pdf_path) as pdf: # 전달받은 경로의 PDF 파일을 메모리에 엽니다.
        total_pages = len(pdf.pages) # 전체 페이지 개수를 세어 변수에 저장합니다.
        
        for i, page in enumerate(pdf.pages): # 첫 번째 페이지부터 마지막 페이지까지 순서대로 반복문을 실행합니다.
            page = page.dedupe_chars(tolerance=2) # 중복을 제거합니다.
            all_tables = page.find_tables() # 모든 표 객체를 탐색하여 리스트로 가져옵니다.
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
                                safe_cell = get_safe_bbox(cell, page.width, page.height) # 좌표를 보정합니다.
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
            last_y = 0 # 위치를 0으로 초기화합니다.
            
            parent_to_children = {} # 캐시용 딕셔너리를 생성합니다.
            for child_idx, data in child_info.items(): # 관계 딕셔너리를 순회합니다.
                parent_idx, keyword, area = data # 정보를 각각 분리합니다.
                if parent_idx not in parent_to_children: # 존재하지 않는다면.
                    parent_to_children[parent_idx] = [] # 빈 리스트를 새로 만듭니다.
                parent_to_children[parent_idx].append((child_idx, all_tables[child_idx].bbox, keyword)) # 정보를 추가합니다.
            
            for original_idx, table_obj in sorted_tables: # 표 객체들을 하나씩 꺼내어 처리합니다.
                current_top = table_obj.bbox[1] # 상단 Y좌표를 변수에 저장합니다.
                
                if current_top > last_y: # 일반 텍스트가 존재한다면.
                    safe_area = get_safe_bbox((0, last_y, page.width, current_top), page.width, page.height) # 좌표를 보정합니다.
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

                            safe_cell_bbox = get_safe_bbox(cell_bbox, page.width, page.height) # 좌표가 안전한지 검사하고 보정합니다.
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

            if last_y < page.height: # 하단에 남은 여백 공간이 있다면 검사합니다.
                safe_final = get_safe_bbox((0, last_y, page.width, page.height), page.width, page.height) # 좌표를 안전하게 보정합니다.
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
            
    return md_output # 최종 마크다운 문자열 덩어리를 호출자에게 반환합니다.