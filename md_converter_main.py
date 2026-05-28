import os # 파일 저장 및 경로 생성 등 파일 시스템 조작을 위한 파이썬 내장 모듈을 가져옵니다.
import datetime # 현재 컴퓨터 시간을 읽어와 텍스트 로그에 타임스탬프를 찍기 위한 내장 모듈을 가져옵니다.
import threading # 텍스트 변환 시 UI 창이 멈추는 것을 방지하기 위해 백그라운드 병렬 처리를 지원하는 모듈을 가져옵니다.
import multiprocessing # 윈도우 환경에서 실행 파일이 무한 증식하는 다중 프로세스 버그를 차단하기 위한 내장 모듈을 가져옵니다.
import tkinter as tk # 윈도우 화면과 버튼 등 시각적 그래픽 사용자 인터페이스(GUI)를 생성하기 위한 기본 라이브러리를 가져옵니다.
from tkinter import filedialog, messagebox, scrolledtext # 폴더 탐색창, 에러 경고창, 스크롤이 가능한 텍스트 창 컴포넌트들을 구체적으로 불러옵니다.

from md_converter_pdf import extract_sequential_content # 분리된 독립 파일 모듈에서 PDF 텍스트 추출의 핵심을 담당하는 함수를 가져옵니다.
from md_converter_xlsx import extract_excel_content # 엑셀 모듈에서 xlsx와 xlsb를 통합 처리하는 엑셀 전용 추출 함수를 가져옵니다.
from md_converter_pptx import extract_pptx_content # 파워포인트 모듈에서 슬라이드 데이터를 추출하는 함수를 새롭게 가져옵니다.

class MDConverterApp: 
    def __init__(self, root):
        # 그래픽 프로그램 창이 처음 생성될 때 실행되는 초기화 전용 생성자 함수입니다.
        self.root = root # 넘겨받은 메인 윈도우 인스턴스 객체를 클래스 전역에서 사용할 수 있도록 변수에 할당합니다.
        self.root.title("Markdown Converter v1.2") # 윈도우 창 좌측 상단에 표시될 프로그램의 버전 타이틀 문구를 최종 업데이트합니다.
        self.root.geometry("402x650") # 프로그램 창의 기본 가로 픽셀과 세로 픽셀 크기를 지정합니다.
        self.root.resizable(False, False) # 사용자가 마우스로 윈도우 창의 가로와 세로 크기를 임의로 늘리거나 줄일 수 없도록 잠금 처리합니다.

        self.file_path = tk.StringVar() # 원본 파일의 문자열 경로를 텍스트 위젯과 실시간으로 연동하기 위한 특수 문자열 변수를 생성합니다.
        self.save_dir = tk.StringVar() # 결과물이 저장될 폴더의 문자열 경로를 텍스트 위젯과 동기화하기 위한 특수 문자열 변수를 생성합니다.
    
        tk.Label(root, text="Select Document", font=("Arial", 10, "bold")).pack(pady=(15, 5)) # 문서 선택을 안내하는 라벨을 상단 중앙에 배치합니다.
        
        file_frame = tk.Frame(root) # 입력 텍스트 칸과 버튼을 가로로 나란히 묶어서 배치하기 위한 투명한 레이아웃 컨테이너 프레임을 생성합니다.
        file_frame.pack(fill=tk.X, padx=15) # 프레임을 창 가로축 너비 끝까지 꽉 채우도록 확장시키고 양옆 여백을 15픽셀 부여합니다.

        self.file_entry = tk.Entry(file_frame, textvariable=self.file_path) # 사용자가 경로를 직접 볼 수 있는 한 줄짜리 입력창을 투명 프레임 안에 생성하고 변수와 연결합니다.
        self.file_entry.pack(side=tk.LEFT, fill=tk.X, expand=True) # 입력창을 프레임 왼쪽에 딱 붙인 채로 남는 가로 여백을 전부 차지하도록 길게 늘립니다.
        tk.Button(file_frame, text="...", command=self.select_file, width=4).pack(side=tk.RIGHT, padx=(5, 0)) # 파일 탐색기 호출 버튼을 생성하여 프레임 우측 끝에 배치합니다.

        tk.Label(root, text="Select Folder to Save MD", font=("Arial", 10, "bold")).pack(pady=(15, 5)) # 마크다운 저장 폴더 선택 공간임을 안내하는 라벨을 중앙에 배치합니다.
        
        dir_frame = tk.Frame(root) # 두 번째 입력창과 두 번째 버튼을 묶기 위해 새로운 투명 레이아웃 컨테이너 프레임을 하단에 생성합니다.
        dir_frame.pack(fill=tk.X, padx=15) # 두 번째 프레임 역시 가로 폭 전체를 채우도록 설정하고 동일하게 양옆 여백을 부여합니다.

        self.dir_entry = tk.Entry(dir_frame, textvariable=self.save_dir) # 목적지 폴더 경로가 표시될 두 번째 한 줄 입력창을 만들고 해당 경로 변수와 실시간 연동시킵니다.
        self.dir_entry.pack(side=tk.LEFT, fill=tk.X, expand=True) # 폴더 경로 입력창도 프레임 왼쪽부터 시작하여 남는 가로 공간을 모조리 흡수하도록 늘립니다.
        tk.Button(dir_frame, text="...", command=self.select_dir, width=4).pack(side=tk.RIGHT, padx=(5, 0)) # 폴더 탐색용 점 3개 버튼을 프레임 우측에 배치하고 함수와 연결합니다.

        self.start_btn = tk.Button(root, text="Convert to MD", bg="#C0C0C0", fg="black", 
                                   font=("Arial", 12, "bold"), height=2, command=self.start_thread) # 변환 작업을 본격적으로 시작할 메인 실행 버튼 위젯을 생성합니다.
        self.start_btn.pack(fill=tk.X, padx=100, pady=(20, 10)) # 실행 버튼이 양쪽으로 100픽셀씩 여백을 가지며 화면 중앙에 자리잡도록 배치합니다.

        tk.Label(root, text="Process Log", font=("Arial", 10)).pack(pady=(5, 5)) # 하단 로그 창 위에 제목 라벨을 작게 배치합니다.
        
        self.log_area = scrolledtext.ScrolledText(root, state='disabled') # 사용자가 임의로 글자를 쓸 수 없도록 읽기 전용 상태로 묶인 스크롤 가능 텍스트 창을 만듭니다.
        self.log_area.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15)) # 텍스트 창이 프로그램 화면 하단의 남은 세로 및 가로 여백 전체를 꽉 채우도록 설정합니다.

    def log(self, message):
        # 백그라운드 스레드가 메인 UI 스레드 쪽으로 텍스트 출력을 요청하는 중간 다리 함수입니다.
        self.root.after(0, self._log_safe, message) # 비동기 큐에 화면 조작 함수를 즉시 대기열로 밀어넣습니다.
        
    def _log_safe(self, message):
        # 오직 화면을 그리는 메인 스레드에 의해서만 단독으로 안전하게 실행되는 실제 문자 출력 함수입니다.
        self.log_area.configure(state='normal') # 새로운 텍스트 문구를 삽입하기 위해 텍스트 창의 읽기 전용 잠금 상태를 일시적으로 풀어줍니다.
        self.log_area.insert(tk.END, f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {message}\n") # 로그 텍스트 영역의 맨 마지막 줄에 현재 시간 문구와 전달받은 메시지를 결합하여 적습니다.
        self.log_area.see(tk.END) # 방금 적은 최신 텍스트가 시야에 들어오도록 텍스트 창의 스크롤바를 맨 밑바닥으로 자동 이동시킵니다.
        self.log_area.configure(state='disabled') # 텍스트 영역을 다시 읽기 전용으로 단단히 잠가버립니다.

    def select_file(self):
        # 탐색기 버튼을 클릭했을 때 여러 확장자를 지원하도록 설정된 이벤트 연결 함수입니다.
        file_types = [
            ("All Supported Files", "*.pdf *.xlsx *.xlsb *.pptx"), # 모든 확장자를 한 번에 볼 수 있도록 통합 필터를 설정합니다.
            ("PDF files", "*.pdf"), 
            ("Excel files", "*.xlsx *.xlsb"), # 엑셀 필터 항목을 고를 때 두 가지 확장자가 나열되도록 속성을 유지합니다.
            ("PowerPoint files", "*.pptx") # 파워포인트 전용 필터를 유지합니다.
        ] 
        path = filedialog.askopenfilename(filetypes=file_types) # 필터를 적용하여 윈도우 파일 열기 대화창을 띄우고 선택된 절대 경로를 받아옵니다.
        if path: # 사용자가 파일을 정상적으로 골라 경로 문자열이 반환되었다면.
            self.file_path.set(path) # 화면 입력창과 연결된 변수에 경로 문자열을 덮어씌워 텍스트 위젯 화면을 갱신합니다.
            self.file_entry.xview_moveto(1.0) # 내부 텍스트 커서를 맨 오른쪽 끝으로 자동 스크롤합니다.

    def select_dir(self):
        # 두 번째 폴더 탐색기 버튼을 눌렀을 때 윈도우 폴더 지정 창을 띄우는 이벤트 연결 함수입니다.
        path = filedialog.askdirectory() # 파일이 아닌 오직 폴더만 선택할 수 있는 전용 윈도우 창을 띄워 경로를 문자열로 가져옵니다.
        if path: # 사용자가 폴더를 정상적으로 선택하여 경로 문자가 반환되었다면.
            self.save_dir.set(path) # 저장소 경로 변수에 문자열을 주입하여 화면 상의 두 번째 입력창을 즉시 갱신합니다.
            self.dir_entry.xview_moveto(1.0) # 입력창 커서를 오른쪽 맨 끝 위치로 쭉 밀어줍니다.

    def start_thread(self):
        # 메인 변환 버튼을 클릭하면 변환 프로세스의 유효성을 검사하고 백그라운드 작업을 시작하는 진입점 함수입니다.
        if not self.file_path.get() or not self.save_dir.get(): # 원본 파일 경로나 목적지 폴더 경로 중 단 하나라도 비어있는지 논리 연산으로 검사합니다.
            messagebox.showwarning("Input Missing", "Please select both a document file and a save folder.") # 경로가 비어있다면 화면 중앙에 경고 팝업창을 띄워 알립니다.
            return # 필수 정보가 없으므로 아래 코드를 더 이상 실행하지 않고 강제 종료합니다.
        self.start_btn.config(state=tk.DISABLED) # 버튼을 클릭 불가능한 상태로 만듭니다.
        threading.Thread(target=self.run_process, daemon=True).start() # 별도의 스레드를 생성하여 실행합니다.

    def run_process(self):
        # 확장자에 따라 분기하여 추출 모듈을 호출하고 디스크에 저장하는 비즈니스 로직 제어 함수입니다.
        try: # 예기치 못한 에러가 발생하여 프로그램이 폭발하는 현상을 막기 위해 예외 처리 블록으로 감쌉니다.
            self.log("-" * 30) # 마이너스 기호 30개를 그려 구분선을 만듭니다.

            input_file = self.file_path.get() # 사용자가 입력했던 원본 전체 경로를 변수에서 추출하여 가져옵니다.
            save_directory = self.save_dir.get() # 사용자가 지정했던 폴더 경로를 가져옵니다.
            
            original_base_name = os.path.basename(input_file) # 전체 경로에서 파일 이름 부분만 잘라냅니다.
            name_only, ext_original = os.path.splitext(original_base_name) # 파일 이름에서 마침표를 기준으로 확장자와 순수 이름을 분리합니다.
            ext_lower = ext_original.lower() # 모두 소문자로 변환합니다.
            ext_md = ".md" # 생성할 마크다운 파일의 확장자 상수를 선언합니다.
            
            base_name = name_only + ext_md # 새로운 저장 파일명을 조립합니다.
            output_md = os.path.join(save_directory, base_name) # 최종 절대 경로를 만듭니다.
            
            counter = 1 # 카운터 변수를 1로 초기화합니다.
            while os.path.exists(output_md): # 저장할 경로에 이미 파일이 있는지 무한 검사합니다.
                base_name = f"{name_only} ({counter}){ext_md}" # 중복 파일이 있다면 괄호와 숫자를 넣어 새로운 파일명을 빚어냅니다.
                output_md = os.path.join(save_directory, base_name) # 새로운 이름으로 경로를 갱신합니다.
                counter += 1 # 카운터를 1 올립니다.
            
            def _start_progress():
                # 마크다운 파일을 생성한다는 초기 안내 문구를 로그에 박아넣고 투명 마커를 설정하는 UI 제어 함수입니다.
                self.log_area.configure(state='normal') # 텍스트 수정을 위해 잠금을 해제합니다.
                self.log_area.insert(tk.END, f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Generating '{base_name}' ... ") # 현재 시간과 진행 문구를 삽입합니다.
                self.log_area.mark_set("progress_mark", "end-1c") # 백분율 수치를 계속 지웠다 쓰기 위해 텍스트 맨 끝에 투명한 책갈피 마커를 고정시킵니다.
                self.log_area.mark_gravity("progress_mark", tk.LEFT) # 왼쪽 중력을 부여합니다.
                self.log_area.see(tk.END) # 스크롤을 이동시킵니다.
                self.log_area.configure(state='disabled') # 잠금을 복원합니다.
            self.root.after(0, _start_progress) # UI 제어 코드를 메인 스레드 대기열로 안전하게 전달합니다.

            def update_progress(percent):
                # 추출 엔진으로부터 현재 정수 퍼센트 수치를 전달받아 화면을 실시간으로 갱신하는 콜백 함수입니다.
                def _update(p=percent): # 변수 지연 평가를 방지하기 위해 퍼센트 값을 고정합니다.
                    self.log_area.configure(state='normal') # 수정을 위해 창 잠금을 해제합니다.
                    self.log_area.delete("progress_mark", tk.END) # 투명 마커 위치부터 뒤에 적힌 옛날 백분율 숫자를 깨끗하게 지웁니다.
                    self.log_area.insert("progress_mark", f"{p}%") # 마커 위치에 % 기호와 함께 갱신된 정수 숫자를 입력합니다.
                    self.log_area.see(tk.END) # 숫자가 보이도록 스크롤을 고정합니다.
                    self.log_area.configure(state='disabled') # 창을 다시 잠급니다.
                self.root.after(0, _update) # 숫자 지우기 및 쓰기 동작을 메인 스레드로 위임합니다.

            # 파일 확장자에 따라 알맞은 추출 모듈로 연결하는 제어 블록입니다.
            if ext_lower == '.pdf':
                # PDF 모듈의 함수를 호출하여 마크다운 문자열을 반환받습니다.
                markdown_content = extract_sequential_content(input_file, progress_callback=update_progress)
            elif ext_lower in ['.xlsx', '.xlsb']:
                # 엑셀 확장자가 xlsx이거나 xlsb인 경우, 통합 엑셀 엔진 함수로 연결하여 마크다운 문자열을 반환받습니다.
                markdown_content = extract_excel_content(input_file, progress_callback=update_progress)
            elif ext_lower == '.pptx':
                # 파워포인트 모듈의 함수를 호출하여 슬라이드의 텍스트와 표를 마크다운 문자열로 반환받습니다.
                markdown_content = extract_pptx_content(input_file, progress_callback=update_progress)
            else:
                # 지정되지 않은 확장자가 들어올 경우를 대비한 방어 로직입니다.
                self.log(f"지원하지 않는 파일 형식입니다: {ext_lower}")
                return
            
            with open(output_md, "w", encoding="utf-8") as f: # 반환받은 문자열을 파일로 저장하기 위해 쓰기 모드로 디스크에 엽니다.
                f.write(f"# {base_name}\n") # 마크다운 대제목 문법으로 파일명을 작성합니다.
                f.write(f"- Created at: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n") # 변환 완료 시간 타임스탬프를 기록합니다.
                f.write(markdown_content) # 본문 전체를 디스크 파일에 한 번에 저장합니다.

            def _finish_progress():
                # 저장이 끝난 뒤 마지막 줄바꿈을 넣어주기 위한 마무리 UI 함수입니다.
                self.log_area.configure(state='normal') # 잠금을 풉니다.
                self.log_area.insert(tk.END, "\n") # 다음 줄로 넘어가는 엔터 기호를 삽입합니다.
                self.log_area.configure(state='disabled') # 다시 창을 잠급니다.
            self.root.after(0, _finish_progress) # 줄바꿈 입력을 비동기 큐로 밀어 넣습니다.

            self.log("Done") # 화면에 완료 로그를 출력합니다.

        except Exception as e: # 에러가 발생하면 예외 객체를 잡아서 이곳으로 떨어뜨립니다.
            def _error_newline():
                # 에러 출력 전 가독성을 위해 줄을 깔끔하게 넘기는 에러용 줄바꿈 UI 함수입니다.
                self.log_area.configure(state='normal') # 잠금을 해제합니다.
                self.log_area.insert(tk.END, "\n") # 줄바꿈 엔터를 입력합니다.
                self.log_area.configure(state='disabled') # 다시 잠금을 겁니다.
            self.root.after(0, _error_newline) # 메인 스레드 큐로 지시합니다.
            self.log(f"Error occurred: {e}") # 예외 객체 메시지를 영문으로 조합하여 로그 창에 찍어냅니다.
            
            self.root.after(0, lambda e=e: messagebox.showerror("Error", f"An error occurred during processing:\n{e}")) # 팝업 경고창을 메인 스레드가 띄우게끔 예약합니다.
        finally: # 최후에 무조건 한 번 실행되는 정리 구역입니다.
            self.root.after(0, lambda: self.start_btn.config(state=tk.NORMAL)) # 버튼의 비활성 상태를 풀어 다시 클릭할 수 있게 복구시킵니다.

if __name__ == "__main__":
    # 인터프리터에 의해 직접 메인 프로그램으로 실행되었을 때만 윈도우 그래픽을 활성화하는 진입점 검사입니다.
    multiprocessing.freeze_support() # pyinstaller 빌드 시 자식 프로세스 무한 증식을 방어합니다.
    root = tk.Tk() # 윈도우 인스턴스 폼 뼈대 객체를 메모리에 생성합니다.
    app = MDConverterApp(root) # 클래스 생성자에 인자로 던져주어 조립합니다.
    root.mainloop() # 무한 루프 생명 주기를 유지합니다.