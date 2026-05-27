import os # 파일 저장 및 경로 생성 등 파일 시스템 조작을 위한 파이썬 내장 모듈을 가져옵니다.
import datetime # 현재 컴퓨터 시간을 읽어와 텍스트 로그에 타임스탬프를 찍기 위한 내장 모듈을 가져옵니다.
import threading # 텍스트 변환 시 UI 창이 멈추는 것을 방지하기 위해 백그라운드 병렬 처리를 지원하는 모듈을 가져옵니다.
import multiprocessing # 윈도우 환경에서 실행 파일이 무한 증식하는 다중 프로세스 버그를 차단하기 위한 내장 모듈을 가져옵니다.
import tkinter as tk # 윈도우 화면과 버튼 등 시각적 그래픽 사용자 인터페이스(GUI)를 생성하기 위한 기본 라이브러리를 가져옵니다.
from tkinter import filedialog, messagebox, scrolledtext # 폴더 탐색창, 에러 경고창, 스크롤이 가능한 텍스트 창 컴포넌트들을 구체적으로 불러옵니다.

from md_converter_pdf import extract_sequential_content # 분리된 독립 파일 모듈에서 PDF 텍스트 추출의 핵심을 담당하는 함수를 메인 메모리로 가져옵니다.

class PDFApp:
    def __init__(self, root):
        # 그래픽 프로그램 창이 처음 생성될 때 실행되는 초기화 전용 생성자 함수입니다.
        self.root = root # 넘겨받은 메인 윈도우 인스턴스 객체를 클래스 전역에서 사용할 수 있도록 변수에 할당합니다.
        self.root.title("PDF to Markdown Converter v1.1") # 윈도우 창 좌측 상단에 표시될 프로그램의 타이틀 문구를 설정합니다.
        self.root.geometry("402x650") # 프로그램 창의 기본 가로 픽셀과 세로 픽셀 크기를 황금 비율로 고정 지정합니다.
        self.root.resizable(False, False) # 사용자가 마우스로 윈도우 창의 가로와 세로 크기를 임의로 늘리거나 줄일 수 없도록 잠금 처리합니다.

        self.pdf_path = tk.StringVar() # PDF 원본 파일의 문자열 경로를 텍스트 위젯과 실시간으로 연동하기 위한 특수 문자열 변수를 생성합니다.
        self.save_dir = tk.StringVar() # 결과물이 저장될 폴더의 문자열 경로를 텍스트 위젯과 동기화하기 위한 특수 문자열 변수를 생성합니다.
    
        tk.Label(root, text="Select PDF", font=("Arial", 10, "bold")).pack(pady=(15, 5)) # 화면 최상단에 PDF 파일 선택 공간임을 알리는 굵은 폰트의 라벨을 중앙 정렬로 배치합니다.
        
        file_frame = tk.Frame(root) # 입력 텍스트 칸과 돋보기 버튼을 가로로 나란히 묶어서 배치하기 위한 투명한 레이아웃 컨테이너 프레임을 생성합니다.
        file_frame.pack(fill=tk.X, padx=15) # 프레임을 창 가로축 너비 끝까지 꽉 채우도록 확장시키고 양옆 여백을 15픽셀 부여합니다.

        self.pdf_entry = tk.Entry(file_frame, textvariable=self.pdf_path) # 사용자가 경로를 직접 볼 수 있는 한 줄짜리 입력창을 투명 프레임 안에 생성하고 변수와 연결합니다.
        self.pdf_entry.pack(side=tk.LEFT, fill=tk.X, expand=True) # 입력창을 프레임 왼쪽에 딱 붙인 채로 남는 가로 여백을 전부 차지하도록 길게 늘립니다.
        tk.Button(file_frame, text="...", command=self.select_pdf, width=4).pack(side=tk.RIGHT, padx=(5, 0)) # 점 3개가 적힌 파일 탐색기 호출 버튼을 생성하여 프레임 우측 끝에 배치합니다.

        tk.Label(root, text="Select Folder to Save MD", font=("Arial", 10, "bold")).pack(pady=(15, 5)) # 중간 지점에 마크다운 저장 폴더 선택 공간임을 안내하는 굵은 글씨 라벨을 중앙에 배치합니다.
        
        dir_frame = tk.Frame(root) # 두 번째 입력창과 두 번째 버튼을 묶기 위해 새로운 투명 레이아웃 컨테이너 프레임을 하단에 생성합니다.
        dir_frame.pack(fill=tk.X, padx=15) # 두 번째 프레임 역시 가로 폭 전체를 채우도록 설정하고 동일하게 양옆 여백을 부여합니다.

        self.dir_entry = tk.Entry(dir_frame, textvariable=self.save_dir) # 목적지 폴더 경로가 표시될 두 번째 한 줄 입력창을 만들고 해당 경로 변수와 실시간 연동시킵니다.
        self.dir_entry.pack(side=tk.LEFT, fill=tk.X, expand=True) # 폴더 경로 입력창도 프레임 왼쪽부터 시작하여 남는 가로 공간을 모조리 흡수하도록 늘립니다.
        tk.Button(dir_frame, text="...", command=self.select_dir, width=4).pack(side=tk.RIGHT, padx=(5, 0)) # 폴더 탐색용 점 3개 버튼을 프레임 우측에 배치하고 함수와 연결합니다.

        self.start_btn = tk.Button(root, text="Convert PDF to MD", bg="#C0C0C0", fg="black", 
                                   font=("Arial", 12, "bold"), height=2, command=self.start_thread) # 변환 작업을 본격적으로 시작할 크고 눈에 띄는 메인 실행 버튼 위젯을 생성합니다.
        self.start_btn.pack(fill=tk.X, padx=100, pady=(20, 10)) # 실행 버튼이 양쪽으로 100픽셀씩 여백을 가지며 화면 중앙에 큼직하게 자리잡도록 배치합니다.

        tk.Label(root, text="Process Log", font=("Arial", 10)).pack(pady=(5, 5)) # 하단 로그 창 위에 이 구역이 작업 진행 상황을 보여주는 곳이라는 제목 라벨을 작게 배치합니다.
        
        self.log_area = scrolledtext.ScrolledText(root, state='disabled') # 사용자가 임의로 글자를 지우거나 쓸 수 없도록 읽기 전용 상태로 묶인 스크롤 가능 텍스트 창을 만듭니다.
        self.log_area.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15)) # 텍스트 창이 프로그램 화면 하단의 남은 세로 및 가로 여백 전체를 꽉 채우도록 설정합니다.

    def log(self, message):
        # 무거운 변환 작업을 수행하는 백그라운드 스레드가 메인 UI 스레드 쪽으로 텍스트 출력을 요청하는 중간 다리 함수입니다.
        self.root.after(0, self._log_safe, message) # 스레드 충돌로 인한 튕김 현상을 막기 위해 비동기 큐에 화면 조작 함수를 즉시 대기열로 밀어넣습니다.
        
    def _log_safe(self, message):
        # 비동기 큐에서 호출되어 오직 화면을 그리는 메인 스레드에 의해서만 단독으로 안전하게 실행되는 실제 문자 출력 함수입니다.
        self.log_area.configure(state='normal') # 새로운 텍스트 문구를 삽입하기 위해 텍스트 창의 읽기 전용 잠금 상태를 일시적으로 풀어줍니다.
        self.log_area.insert(tk.END, f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {message}\n") # 로그 텍스트 영역의 맨 마지막 줄에 현재 시간 문구와 전달받은 메시지를 결합하여 적습니다.
        self.log_area.see(tk.END) # 방금 적은 최신 텍스트가 시야에 들어오도록 텍스트 창의 스크롤바를 맨 밑바닥으로 자동 이동시킵니다.
        self.log_area.configure(state='disabled') # 사용자가 글자를 조작하지 못하게 텍스트 영역을 다시 읽기 전용으로 단단히 잠가버립니다.

    def select_pdf(self):
        # 첫 번째 파일 탐색기 버튼을 클릭했을 때 운영체제 창을 띄우는 이벤트 연결 함수입니다.
        path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")]) # 윈도우 파일 열기 대화창을 띄우고 확장자가 PDF인 파일만 표시하도록 필터를 설정하여 선택된 절대 경로를 받아옵니다.
        if path: # 사용자가 취소를 누르지 않고 파일을 정상적으로 골라 경로 문자열이 반환되었다면.
            self.pdf_path.set(path) # 화면 입력창과 연결된 변수에 경로 문자열을 덮어씌워 텍스트 위젯 화면을 갱신합니다.
            self.pdf_entry.xview_moveto(1.0) # 긴 경로 때문에 파일 이름이 안 보일 수 있으므로 입력창 내부 텍스트 커서를 맨 오른쪽 끝으로 자동 스크롤합니다.

    def select_dir(self):
        # 두 번째 폴더 탐색기 버튼을 눌렀을 때 윈도우 폴더 지정 창을 띄우는 이벤트 연결 함수입니다.
        path = filedialog.askdirectory() # 파일이 아닌 오직 폴더(디렉토리)만 선택할 수 있는 전용 윈도우 창을 띄워 경로를 문자열로 가져옵니다.
        if path: # 사용자가 폴더를 정상적으로 선택하여 경로 문자가 반환되었다면.
            self.save_dir.set(path) # 저장소 경로 변수에 문자열을 주입하여 화면 상의 두 번째 입력창을 즉시 갱신합니다.
            self.dir_entry.xview_moveto(1.0) # 사용자가 어느 폴더인지 식별하기 쉽게 입력창 커서를 오른쪽 맨 끝 위치로 쭉 밀어줍니다.

    def start_thread(self):
        # Convert 메인 버튼을 클릭하면 변환 프로세스의 유효성을 검사하고 백그라운드 작업을 시작하는 진입점 함수입니다.
        if not self.pdf_path.get() or not self.save_dir.get(): # 원본 파일 경로나 목적지 폴더 경로 중 단 하나라도 비어있는지 논리 연산으로 검사합니다.
            messagebox.showwarning("Input Missing", "Please select both a PDF file and a save folder.") # 경로가 비어있다면 화면 중앙에 노란색 경고 아이콘 팝업창을 띄워 알립니다.
            return # 필수 정보가 없으므로 아래 코드를 더 이상 실행하지 않고 클릭 이벤트를 강제 종료합니다.
        self.start_btn.config(state=tk.DISABLED) # 작업이 진행되는 동안 사용자가 실수로 버튼을 연타하여 이중으로 변환되는 것을 막기 위해 버튼을 클릭 불가능한 잿빛으로 만듭니다.
        threading.Thread(target=self.run_process, daemon=True).start() # GUI 화면이 멈추고 응답 없음 상태가 되는 것을 막기 위해, 별도의 일꾼(스레드)을 백그라운드에 생성하여 메인 비즈니스 로직을 던져주고 즉시 시작시킵니다.

    def run_process(self):
        # 메인 UI 흐름과 분리되어 별개의 일꾼(스레드)이 묵묵히 텍스트 추출과 파일 저장을 수행하는 비즈니스 로직 핵심 함수입니다.
        try: # 변환 도중 예기치 못한 에러가 발생하여 프로그램이 폭발하고 종료되는 현상을 막기 위해 거대한 예외 처리 블록으로 감쌉니다.
            self.log("-" * 30) # 본격적인 새로운 작업이 시작되었음을 로그 창에 알리기 위해 마이너스 기호 30개를 그려 구분선을 만듭니다.

            input_pdf = self.pdf_path.get() # 사용자가 입력했던 PDF 원본 전체 경로를 변수에서 추출하여 로컬 메모리로 복사해 옵니다.
            save_directory = self.save_dir.get() # 사용자가 지정했던 폴더 경로 역시 변수에서 빼내어 로컬로 가져옵니다.
            
            original_base_name = os.path.basename(input_pdf) # C:/test/sample.pdf 와 같은 전체 경로에서 순수하게 sample.pdf 라는 이름 부분만 잘라냅니다.
            name_only, _ = os.path.splitext(original_base_name) # sample.pdf 라는 이름에서 확장자인 .pdf 를 분리하여 버리고 순수 문자열 'sample' 만 추출합니다.
            ext = ".md" # 생성할 마크다운 파일의 확장자 문자열 상수를 선언합니다.
            
            base_name = name_only + ext # 순수 이름 문자열과 마크다운 확장자를 더하여 'sample.md' 라는 새로운 저장 파일명을 조립합니다.
            output_md = os.path.join(save_directory, base_name) # 목적지 폴더 절대 경로와 조립된 파일명을 운영체제에 맞게 안전하게 결합하여 최종 목적지 풀 경로를 만듭니다.
            
            counter = 1 # 동일한 이름의 파일이 이미 있을 경우 번호를 매기기 위해 카운터 변수를 1로 초기화합니다.
            while os.path.exists(output_md): # 파일 시스템의 목적지에 동일한 전체 경로를 가진 파일이 이미 존재하는지 무한 반복문으로 계속 검사합니다.
                base_name = f"{name_only} ({counter}){ext}" # 겹치는 파일이 있다면 이름 뒤에 (1), (2) 처럼 숫자를 끼워 넣어 새로운 이름을 문자열 포매팅으로 빚어냅니다.
                output_md = os.path.join(save_directory, base_name) # 숫자가 결합된 새로운 이름과 폴더 경로를 다시 묶어 최종 확인용 경로를 갱신합니다.
                counter += 1 # 반복문을 다시 돌 때마다 다음 숫자를 확인하기 위해 카운터를 1씩 증가시킵니다.
            
            def _start_progress():
                # 마크다운 파일을 생성한다는 초기 안내 문구를 로그에 박아넣는 보조 UI 제어 함수입니다.
                self.log_area.configure(state='normal') # 텍스트 수정을 위해 텍스트 창 보호 잠금을 해제합니다.
                self.log_area.insert(tk.END, f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Generating '{base_name}' ... ") # 현재 시간표시와 함께 파일명 생성 시작 문구를 삽입합니다.
                self.log_area.mark_set("progress_mark", "end-1c") # 백분율 수치를 계속 지웠다 쓰기 위해, 현재 삽입된 텍스트의 맨 끝부분 직전에 투명한 보이지 않는 책갈피 마커를 박아 넣습니다.
                self.log_area.mark_gravity("progress_mark", tk.LEFT) # 투명 마커가 새로운 텍스트가 들어오더라도 오른쪽으로 밀리지 않고 왼쪽 위치를 단단히 고수하도록 중력을 설정합니다.
                self.log_area.see(tk.END) # 글씨를 쓴 곳으로 스크롤을 끝까지 내립니다.
                self.log_area.configure(state='disabled') # 잠금을 복원합니다.
            self.root.after(0, _start_progress) # UI 제어 코드가 백그라운드 스레드에서 직접 렌더링되지 않고 메인 스레드 대기열로 안전하게 전달되도록 지시합니다.

            def update_progress(percent):
                # 추출 엔진으로부터 현재 몇 퍼센트를 변환했는지 숫자값을 전달받아 화면을 실시간으로 새로고침하는 외부 호출용 콜백 함수입니다.
                def _update(p=percent): # 람다 함수의 지연 평가 버그를 방지하기 위해 퍼센트 값을 내부 스코프 인자로 고정시켜 받습니다.
                    self.log_area.configure(state='normal') # 숫자 수정을 위해 창 잠금을 해제합니다.
                    self.log_area.delete("progress_mark", tk.END) # 아까 박아두었던 투명 마커 위치부터 현재 텍스트 맨 끝부분 사이에 있는 옛날 백분율 숫자를 백스페이스로 깨끗하게 지워버립니다.
                    self.log_area.insert("progress_mark", f"{p}%") # 투명 마커 위치에 새롭게 갱신된 백분율 퍼센트 숫자를 입력합니다.
                    self.log_area.see(tk.END) # 실시간으로 변화하는 숫자가 시야에 보이도록 스크롤을 고정합니다.
                    self.log_area.configure(state='disabled') # 창을 다시 읽기 전용으로 잠급니다.
                self.root.after(0, _update) # 숫자 지우기 및 쓰기 동작 전체를 안전한 메인 스레드 위임 큐에 집어넣습니다.

            markdown_content = extract_sequential_content(input_pdf, progress_callback=update_progress) # 분리된 독립 모듈의 핵심 추출 함수를 호출하고, 실시간 퍼센트를 보낼 콜백 함수를 연결하여 최종 문자열을 반환받습니다.
            
            with open(output_md, "w", encoding="utf-8") as f: # 반환받은 방대한 문자열을 디스크에 저장하기 위해 쓰기 모드와 UTF-8 인코딩을 적용하여 파일을 메모리에 엽니다.
                f.write(f"# {base_name}\n") # 파일 맨 첫 줄에 마크다운 대제목 문법(H1)을 사용하여 현재 생성된 파일명을 큼직하게 씁니다.
                f.write(f"- Created at: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n") # 두 번째 줄에 변환 작업이 완료된 현재 날짜와 시간 정보 타임스탬프를 리스트 형태로 기록합니다.
                f.write(markdown_content) # 메인 추출 엔진이 반환한 수천 수만 줄의 변환된 전체 마크다운 본문을 해당 파일에 모두 쏟아부어 저장합니다.

            def _finish_progress():
                # 100% 변환이 완전히 끝나고 디스크 저장까지 끝난 뒤 마지막 줄바꿈을 넣어주기 위한 마무리 UI 제어 함수입니다.
                self.log_area.configure(state='normal') # 잠금을 풉니다.
                self.log_area.insert(tk.END, "\n") # 백분율 수치 뒤에 다음 줄로 넘어가는 엔터 기호 문자열을 삽입하여 줄 정렬을 맞춥니다.
                self.log_area.configure(state='disabled') # 다시 창을 잠급니다.
            self.root.after(0, _finish_progress) # 줄바꿈 입력 역시 메인 스레드의 비동기 큐로 안전하게 밀어 넣습니다.

            self.log("Done") # 모든 과정이 튕김이나 에러 없이 끝났으므로 화면에 완료 문구를 띄웁니다.

        except Exception as e: # 만약 위의 모든 과정 중 단 하나라도 치명적인 에러가 발생했다면 프로그램이 강제 종료되지 않고 이곳으로 예외 객체가 떨어집니다.
            def _error_newline():
                # 로그 창에 에러가 출력되기 전 가독성을 위해 줄을 깔끔하게 넘기는 에러용 줄바꿈 UI 함수입니다.
                self.log_area.configure(state='normal') # 잠금을 해제합니다.
                self.log_area.insert(tk.END, "\n") # 줄바꿈 엔터를 입력합니다.
                self.log_area.configure(state='disabled') # 다시 잠금을 겁니다.
            self.root.after(0, _error_newline) # 메인 스레드 큐로 줄바꿈을 지시합니다.
            self.log(f"Error occurred: {e}") # 무슨 이유로 에러가 났는지 예외 객체 메시지를 영문으로 조합하여 로그 창에 텍스트로 찍어냅니다.
            
            self.root.after(0, lambda e=e: messagebox.showerror("Error", f"An error occurred during processing:\n{e}")) # 로그 창 외에도 사용자가 눈치챌 수 있도록 빨간색 X자 팝업 경고창을 메인 스레드가 띄우게끔 람다 함수로 큐에 예약합니다.
        finally: # 변환이 성공적으로 끝났든, 중간에 폭발하여 에러가 났든, 이 블록 내부의 코드는 가장 마지막에 무조건 한 번 실행됩니다.
            self.root.after(0, lambda: self.start_btn.config(state=tk.NORMAL)) # 잠가두었던 메인 변환 버튼의 잿빛 비활성 상태를 원래대로 클릭할 수 있게 복구시킵니다.

if __name__ == "__main__":
    # 현재 파일이 다른 모듈에 의해 import 당한 것이 아니라 파이썬 인터프리터에 의해 직접 메인 프로그램으로 실행되었을 때만 작동하는 진입점 검사입니다.
    multiprocessing.freeze_support() # 윈도우 환경에서 PyInstaller로 EXE 파일 빌드 시 자식 프로세스가 무한으로 켜지는 다중 스레드 버그를 방어하는 마개 코드를 선언합니다.
    root = tk.Tk() # 그래픽 요소를 그릴 수 있는 텅 빈 윈도우 인스턴스 폼 뼈대 객체를 메모리에 생성합니다.
    app = PDFApp(root) # 방금 만든 텅 빈 윈도우 뼈대를 화면 클래스 생성자에 인자로 던져주어 버튼과 입력창 등 각종 UI 위젯들이 조립되어 화면에 렌더링되게 만듭니다.
    root.mainloop() # 메인 윈도우 창이 화면에 나타난 직후 바로 꺼지지 않고 마우스 클릭 등 이벤트를 지속적으로 대기하도록 무한 루프 생명 주기를 유지시킵니다.