import os # 운영체제 환경 변수를 설정하고 제어하기 위한 파이썬 내장 모듈을 가져옵니다.
import warnings # 실행 중 발생하는 내부 경고 메시지를 필터링하기 위한 내장 모듈을 가져옵니다.
import pdfplumber # PDF 문서 구조를 분석하고 데이터를 추출하기 위한 외부 라이브러리를 가져옵니다.

os.environ["TQDM_DISABLE"] = "1" # 시스템 환경 변수에 접근하여 콘솔창 진행률 상태바 출력을 강제로 비활성화합니다.
warnings.filterwarnings("ignore", category=UserWarning) # 사용자에게 노출할 필요가 없는 내부 경고를 무시하도록 필터를 설정합니다.

def is_inside(inner_bbox, outer_bbox, margin=5):
    # 첫 번째 좌표 영역이 두 번째 좌표 영역 안에 지정된 오차 범위 내로 포함되는지 검사하는 함수를 정의합니다.
    ix0, iy0, ix1, iy1 = inner_bbox # 내부 상자의 좌측, 상단, 우측, 하단 좌표를 각각 분리하여 변수에 저장합니다.
    ox0, oy0, ox1, oy1 = outer_bbox # 외부 상자의 좌측, 상단, 우측, 하단 좌표를 각각 분리하여 변수에 저장합니다.
    return (ix0 >= ox0 - margin) and (iy0 >= oy0 - margin) and \
           (ix1 <= ox1 + margin) and (iy1 <= oy1 + margin) # 내부 상자의 모든 모서리가 외부 상자 안쪽에 위치하는지 논리 연산하여 참 또는 거짓을 반환합니다.

def is_char_inside(char_obj, bbox):
    # 단일 글자 객체의 중심점 좌표가 특정 박스 영역 내부에 존재하는지 판별하는 함수를 정의합니다.
    cx = (char_obj["x0"] + char_obj["x1"]) / 2 # 글자의 좌측과 우측 좌표를 더하고 2로 나누어 가로 중심점을 계산합니다.
    cy = (char_obj["top"] + char_obj["bottom"]) / 2 # 글자의 상단과 하단 좌표를 더하고 2로 나누어 세로 중심점을 계산합니다.
    bx0, btop, bx1, bbottom = bbox # 대상 박스의 4개 좌표를 분리하여 할당합니다.
    return (bx0 <= cx <= bx1) and (btop <= cy <= bbottom) # 계산된 가로 및 세로 중심점이 박스 경계선 내부에 들어오는지 확인하여 반환합니다.

def get_safe_bbox(bbox, page_width, page_height):
    # 추출 영역이 실제 PDF 페이지 크기를 벗어나지 않도록 좌표를 강제로 보정하는 함수를 정의합니다.
    x0, top, x1, bottom = bbox # 원본 좌표 4개를 분리하여 저장합니다.
    x0 = max(0, min(x0, page_width)) # 좌측 X 좌표가 0보다 작으면 0으로, 너비보다 크면 너비 값으로 제한합니다.
    top = max(0, min(top, page_height)) # 상단 Y 좌표가 0보다 작으면 0으로, 높이보다 크면 높이 값으로 제한합니다.
    x1 = max(0, min(x1, page_width)) # 우측 X 좌표를 동일한 방식으로 한계값 내에 맞춥니다.
    bottom = max(0, min(bottom, page_height)) # 하단 Y 좌표를 동일한 방식으로 한계값 내에 맞춥니다.
    
    if x0 >= x1 or top >= bottom: # 보정된 좌표가 꼬여서 면적이 0 이하의 비정상적인 상태가 되었는지 검사합니다.
        return None # 비정상 영역일 경우 추출을 포기하고 None 객체를 반환합니다.
    return (x0, top, x1, bottom) # 정상적으로 보정된 최종 좌표를 튜플 형태로 묶어 반환합니다.

def extract_sequential_content(pdf_path, progress_callback=None):
    # PDF 경로를 받아 텍스트와 표를 추출하고 마크다운 문자열로 반환하는 메인 추출 함수를 정의합니다.
    md_output = "" # 최종 결과물이 누적될 빈 텍스트 문자열을 초기화합니다.
    with pdfplumber.open(pdf_path) as pdf: # 전달받은 경로의 PDF 파일을 메모리에 엽니다.
        total_pages = len(pdf.pages) # 열린 PDF 문서의 전체 페이지 개수를 세어 변수에 저장합니다.
        
        for i, page in enumerate(pdf.pages): # 첫 번째 페이지부터 마지막 페이지까지 순서대로 반복문을 실행합니다.
            page = page.dedupe_chars(tolerance=2) # 2포인트 이하로 미세하게 겹치는 그림자 글자들을 하나로 병합하여 중복을 제거합니다.
            all_tables = page.find_tables() # 현재 페이지 내부에 존재하는 모든 표 객체를 탐색하여 리스트로 가져옵니다.
            all_bboxes = [t.bbox for t in all_tables] # 찾은 표 객체 리스트에서 테두리 좌표값만 별도로 뽑아내어 리스트를 만듭니다.

            child_info = {} # 표 안에 표가 들어있는 중첩 구조를 기록하기 위해 빈 딕셔너리를 생성합니다.
            for idx_a, t_a in enumerate(all_tables): # 첫 번째 비교 대상이 될 '부모 후보 표'들을 순회합니다.
                area_a = (t_a.bbox[2] - t_a.bbox[0]) * (t_a.bbox[3] - t_a.bbox[1]) # 가로 길이와 세로 길이를 곱하여 해당 표의 전체 면적을 계산합니다.
                
                for idx_b, t_b in enumerate(all_tables): # 두 번째 비교 대상이 될 '자식 후보 표'들을 순회합니다.
                    if idx_a == idx_b: continue # 두 표가 동일한 객체라면 비교할 필요가 없으므로 다음으로 넘어갑니다.
                    if is_inside(t_b.bbox, t_a.bbox): # 자식 표의 좌표가 부모 표의 좌표 안에 포함되는지 함수로 확인합니다.
                        if idx_b in child_info and area_a >= child_info[idx_b][2]: # 이미 더 작은 진짜 부모 표가 등록되어 있는지 면적을 비교합니다.
                            continue # 현재 표는 너무 큰 껍데기 표이므로 등록을 건너뜁니다.
                        
                        target_keyword = "" # 부모 표에서 추출할 제목 키워드를 저장할 빈 문자열을 만듭니다.
                        for cell in t_a.cells: # 부모 표를 구성하는 모든 개별 셀 칸들을 순회합니다.
                            if not cell: continue # 해당 칸의 데이터가 비어있다면 에러 방지를 위해 건너뜁니다.
                            
                            if is_inside(t_b.bbox, cell): # 자식 표 전체가 현재 검사 중인 단일 칸 안에 들어있는지 확인합니다.
                                safe_cell = get_safe_bbox(cell, page.width, page.height) # 해당 셀의 좌표가 페이지 밖을 벗어나지 않는지 보정합니다.
                                if safe_cell: # 셀 좌표가 정상적인 영역이라면 내부 로직을 실행합니다.
                                    cell_page = page.within_bbox(safe_cell) # PDF 페이지 전체에서 해당 셀 영역만큼만 잘라냅니다.
                                    kw_text = cell_page.filter( # 잘라낸 영역 내부의 객체들을 조건에 따라 필터링합니다.
                                        lambda obj: obj.get("object_type") != "char" or \
                                                    not is_char_inside(obj, t_b.bbox) # 자식 표 바깥에 위치한 순수 글자 객체만 남깁니다.
                                    ).extract_text() # 필터링을 통과한 글자들만 텍스트로 추출합니다.
                                    if kw_text: # 텍스트가 성공적으로 추출되었다면 조건문을 실행합니다.
                                        first_line_words = kw_text.split('\n')[0].split() # 첫 번째 줄만 분리한 뒤 공백을 기준으로 단어를 쪼개어 리스트로 만듭니다.
                                        raw_keyword = " ".join(first_line_words[:4]).strip() # 처음 4개의 단어만 공백으로 이어붙이고 양끝 여백을 제거합니다.
                                        if raw_keyword: # 키워드가 비어있지 않다면 변수에 저장합니다.
                                            target_keyword = f"'{raw_keyword}'" # 추출된 키워드 양쪽에 작은따옴표를 씌워 강조합니다.
                                break # 정확한 부모 셀을 찾았으므로 더 이상의 셀 탐색을 중지하고 반복문을 빠져나옵니다.
                        child_info[idx_b] = (idx_a, target_keyword, area_a) # 자식 표 번호를 키로 삼아 부모 번호, 키워드, 면적을 딕셔너리에 저장합니다.

            indexed_tables = list(enumerate(all_tables)) # 표 정렬 전에 원래 고유 인덱스 번호를 유지하기 위해 튜플 리스트로 변환합니다.
            sorted_tables = sorted(indexed_tables, key=lambda x: x[1].bbox[1]) # 표 객체의 상단 Y좌표를 기준으로 위에서 아래로 오름차순 정렬합니다.
            last_y = 0 # 텍스트 중복 추출을 방지하기 위해 마지막으로 읽어들인 Y좌표 위치를 0으로 초기화합니다.
            
            parent_to_children = {} # 부모 표가 가진 자식 표 리스트를 빠르게 찾기 위해 캐시용 딕셔너리를 생성합니다.
            for child_idx, data in child_info.items(): # 저장해둔 자식 표 관계 딕셔너리를 순회합니다.
                parent_idx, keyword, area = data # 튜플에 담긴 부모 번호, 키워드, 면적 정보를 각각 분리합니다.
                if parent_idx not in parent_to_children: # 부모 번호가 캐시 딕셔너리에 아직 존재하지 않는다면.
                    parent_to_children[parent_idx] = [] # 해당 부모 번호를 키로 하는 빈 리스트를 새로 만듭니다.
                parent_to_children[parent_idx].append((child_idx, all_tables[child_idx].bbox, keyword)) # 부모 리스트 안에 자식 표의 번호, 좌표, 키워드를 추가합니다.
            
            for original_idx, table_obj in sorted_tables: # 세로 위치 순서대로 정렬된 표 객체들을 하나씩 꺼내어 처리합니다.
                current_top = table_obj.bbox[1] # 현재 순회 중인 표의 상단 Y좌표를 변수에 저장합니다.
                
                if current_top > last_y: # 표의 시작 위치가 마지막 읽은 위치보다 아래에 있다면 그 사이에 일반 텍스트가 존재한다는 의미입니다.
                    safe_area = get_safe_bbox((0, last_y, page.width, current_top), page.width, page.height) # 텍스트가 있는 빈 공간 영역의 좌표를 보정합니다.
                    if safe_area: # 보정된 빈 공간 좌표가 정상이라면 텍스트 추출을 시작합니다.
                        clean_text = page.within_bbox(safe_area).filter( # 해당 빈 공간만큼 페이지를 잘라내고 필터를 적용합니다.
                            lambda o: o.get("object_type") != "char" or \
                                      not any(is_char_inside(o, b) for b in all_bboxes) # 모든 표들의 좌표와 겹치지 않는 순수 글자만 필터링합니다.
                        ).extract_text() # 표 바깥 공간의 일반 텍스트를 모두 추출합니다.
                        if clean_text and clean_text.strip(): # 추출된 텍스트가 공백이 아닌 실제 문자를 포함하고 있다면 조건문을 실행합니다.
                            md_output += clean_text.strip() + "\n\n" # 누적 결과물 문자열에 텍스트를 추가하고 두 번 줄바꿈을 넣습니다.

                if original_idx in child_info: # 현재 검사 중인 표가 부모에게 종속된 자식 표라면 단순 추출을 진행합니다.
                    table_data = table_obj.extract() # 별도의 복잡한 가공 없이 표 내부 데이터를 2차원 리스트로 모두 추출합니다.
                else: # 현재 표가 독립된 표이거나 자식을 품은 부모 표라면 상세 분석을 진행합니다.
                    my_children = parent_to_children.get(original_idx, []) # 캐시 딕셔너리에서 내 자식 표 목록을 빠르게 불러옵니다.
                    table_data = [] # 현재 표의 모든 셀 데이터를 담을 최상위 빈 리스트를 생성합니다.
                    for row in table_obj.rows: # 표를 구성하는 가로 행 객체들을 위에서부터 하나씩 순회합니다.
                        row_data = [] # 한 행의 셀 데이터들을 담을 빈 리스트를 생성합니다.
                        for cell_bbox in row.cells: # 현재 행에 포함된 개별 칸(셀)의 좌표들을 왼쪽부터 순회합니다.
                            if not cell_bbox: # 해당 칸의 좌표 정보가 존재하지 않거나 병합되어 비어있다면.
                                row_data.append("") # 행 데이터 리스트에 빈 문자열을 추가합니다.
                                continue # 아래 텍스트 추출 로직을 건너뛰고 다음 칸으로 넘어갑니다.

                            safe_cell_bbox = get_safe_bbox(cell_bbox, page.width, page.height) # 해당 셀의 추출용 좌표가 안전한지 검사하고 보정합니다.
                            if safe_cell_bbox: # 정상적으로 보정된 셀 좌표라면 추출을 시작합니다.
                                cell_page = page.within_bbox(safe_cell_bbox) # PDF 페이지 전체에서 해당 셀 크기만큼만 오려냅니다.
                                contained_children = [child for child in my_children if is_inside(child[1], cell_bbox, margin=10)] # 오려낸 셀 안에 자식 표가 들어있는지 검사하여 리스트를 만듭니다.

                                if contained_children: # 해당 셀 안에 자식 표가 하나라도 존재한다면 조건문을 실행합니다.
                                    filtered_page = cell_page.filter( # 셀 내부 객체들에 필터를 적용합니다.
                                        lambda obj: obj.get("object_type") != "char" or \
                                                    not any(is_char_inside(obj, child[1]) for child in contained_children) # 자식 표 위치와 겹치는 글자 객체는 모두 삭제합니다.
                                    )
                                    raw_text = filtered_page.extract_text() or "" # 자식 표를 제외한 부모 셀 본연의 텍스트만 추출하며 실패 시 빈 문자열을 넣습니다.
                                    
                                    kw_list = list(dict.fromkeys([child[2] for child in contained_children if child[2]])) # 셀 안에 있는 모든 자식 표들의 키워드를 순서를 유지한 채 중복 없이 리스트화합니다.
                                    kw_str = ", ".join(kw_list) # 키워드 리스트를 쉼표 기호로 이어붙여 하나의 문자열로 만듭니다.
                                    
                                    clean_text = raw_text.replace('\n', '<br>').replace('|', '\\|').strip() # 추출된 부모 텍스트의 줄바꿈을 HTML 태그로 바꾸고 파이프 기호를 이스케이프 처리합니다.
                                    if clean_text: # 정제된 부모 텍스트가 존재한다면 자식 표 안내 문구를 결합합니다.
                                        ref_str = f" [{kw_str} Details below]" if kw_str else " [Details below]" # 키워드가 있으면 키워드를 포함하여 안내 문구를 생성합니다.
                                        text = clean_text + ref_str # 부모 텍스트와 안내 문구를 합칩니다.
                                    else: # 부모 텍스트가 전혀 없이 텅 빈 상태라면.
                                        text = "" # 마크다운 출력용 텍스트를 완전히 비웁니다.
                                else: # 셀 내부에 자식 표가 없는 평범한 단일 칸이라면 일반 추출을 진행합니다.
                                    text = (cell_page.extract_text() or "").replace('\n', '<br>').replace('|', '\\|').strip() # 텍스트를 모두 추출한 뒤 줄바꿈과 파이프 기호를 치환하고 공백을 제거합니다.
                            else: # 셀 좌표가 꼬여버린 비정상적인 유령 공간이라면.
                                text = "" # 에러 방지를 위해 추출하지 않고 빈 문자열을 할당합니다.
                            row_data.append(text) # 최종 완성된 칸의 문자열 데이터를 행 리스트에 추가합니다.
                        table_data.append(row_data) # 완성된 한 줄의 행 데이터를 전체 표 리스트에 추가합니다.

                has_content = False # 투명한 테두리만 있는 유령 표를 걸러내기 위해 상태 변수를 거짓으로 초기화합니다.
                if table_data: # 추출된 표 2차원 리스트에 데이터가 하나라도 존재한다면 검사를 시작합니다.
                    check_rows = table_data[1:] if len(table_data) > 1 else table_data # 마크다운 표 제목행 밑에 실제 내용이 있는지 확인하기 위해 두 번째 줄부터 잘라냅니다.
                    for row in check_rows: # 검사 대상 행들을 하나씩 순회합니다.
                        if any(str(cell).strip() for cell in row if cell): # 행 안의 칸들 중 공백이 아닌 실제 문자가 하나라도 존재하는지 확인합니다.
                            has_content = True # 실제 문자를 발견했으므로 유효한 표로 인정하고 상태 변수를 참으로 변경합니다.
                            break # 더 이상 검사할 필요가 없으므로 반복문을 즉시 종료합니다.

                if has_content: # 유효한 내용이 있는 진짜 표로 판별되었다면 마크다운 문자열 조립을 시작합니다.
                    if original_idx in child_info: # 현재 처리 중인 표가 부모를 가진 자식 표라면 제목을 달아줍니다.
                        _, target_keyword, _ = child_info[original_idx] # 자식 정보 튜플에서 키워드 문자열만 빼옵니다.
                        if target_keyword: # 빼온 키워드가 빈 문자열이 아니라면 제목 라인을 출력합니다.
                            md_output += f"> **{target_keyword}** Details\n\n" # 인용구 마크다운 문법을 사용하여 자식 표의 제목을 누적 결과물에 추가합니다.
                    
                    for row_idx, row in enumerate(table_data): # 추출이 완료된 2차원 표 데이터를 가로행 단위로 순회합니다.
                        clean_row = [str(cv).replace('\n', '<br>').replace('|', '\\|').strip() if cv else "" for cv in row] # 행 내부의 모든 칸들에 대해 마크다운 테이블 충돌 방지 문자열 치환을 일괄 수행합니다.
                        md_output += "| " + " | ".join(clean_row) + " |\n" # 각 칸 사이에 파이프 기호를 넣어 마크다운 표의 한 줄을 완성하여 문자열에 추가합니다.
                        if row_idx == 0: # 방금 추가한 줄이 표의 첫 번째 제목 행이었다면 마크다운 구분선을 넣어야 합니다.
                            md_output += "| " + " | ".join(["---"] * len(clean_row)) + " |\n" # 칸의 개수만큼 대시 기호(---)를 생성하여 제목 아래 구분선 행을 조립해 넣습니다.
                    md_output += "\n" # 한 개의 전체 표 변환이 끝났으므로 다음 요소와의 구분을 위해 줄바꿈을 하나 추가합니다.

                last_y = max(last_y, table_obj.bbox[3]) # 표 처리가 끝났으므로 중복 추출 방지용 마지막 Y좌표를 현재 표의 맨 밑바닥 좌표로 갱신합니다.

            if last_y < page.height: # 페이지 내의 모든 표 처리가 끝났는데 하단에 남은 여백 공간이 있다면 검사합니다.
                safe_final = get_safe_bbox((0, last_y, page.width, page.height), page.width, page.height) # 표가 끝난 위치부터 페이지 맨 아래까지의 좌표를 안전하게 보정합니다.
                if safe_final: # 보정된 페이지 하단 영역 좌표가 정상이라면 텍스트 추출을 시작합니다.
                    final_text = page.within_bbox(safe_final).filter( # 페이지 맨 하단 영역만큼만 잘라내고 객체 필터를 적용합니다.
                        lambda o: o.get("object_type") != "char" or \
                                  not any(is_char_inside(o, b) for b in all_bboxes) # 모든 표 영역과 겹치는 글자 객체를 철저히 배제합니다.
                    ).extract_text() # 페이지 최하단 꼬리말 영역의 순수 일반 텍스트를 추출합니다.
                    if final_text and final_text.strip(): # 추출된 텍스트가 실제 글자를 포함하고 있다면 조건문을 실행합니다.
                        md_output += final_text.strip() + "\n\n" # 누적 결과물 문자열 맨 끝부분에 공백을 자른 텍스트와 두 번의 줄바꿈을 추가합니다.
        
            md_output += "---\n\n" # 한 페이지의 처리가 완전히 종료되었음을 알리기 위해 마크다운 수평선 구분 기호를 삽입합니다.

            if progress_callback: # UI 스레드로 퍼센트를 전송할 수 있는 콜백 함수가 인자로 들어왔는지 확인합니다.
                current_percent = int(((i + 1) / total_pages) * 100) # (현재 처리한 페이지 / 전체 페이지 수)에 100을 곱하여 정수형 백분율 값을 산출합니다.
                progress_callback(current_percent) # 산출된 퍼센트 숫자를 UI 스레드의 업데이트 함수로 전송하여 화면을 갱신시킵니다.
            
    return md_output # 모든 페이지에 대한 분석과 변환이 완료된 최종 마크다운 문자열 덩어리를 호출자에게 반환합니다.