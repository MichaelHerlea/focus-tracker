import win32gui
import win32process
import win32api
import psutil
import ctypes
import ctypes.wintypes
import win32con
import time
import threading

system_processes = {"Microsoft® Windows® Operating System"}

class ApplicationTracker:
    def __init__(self):
        self.old_time: float = time.time()
        self.app_instance = None

        self.user32 = ctypes.windll.user32
        self.kernel32 = ctypes.windll.kernel32

        self.WinEventProc = ctypes.CFUNCTYPE(
            None,
            ctypes.wintypes.HANDLE,
            ctypes.wintypes.DWORD,
            ctypes.wintypes.HWND,
            ctypes.wintypes.LONG,
            ctypes.wintypes.LONG,
            ctypes.wintypes.DWORD,
            ctypes.wintypes.DWORD,
        )
        self.callback = self.WinEventProc(self.on_foreground_change)
        self.hook = None

        self.thread = None
        self.thread_id = None
        self.lock = threading.Lock()

    def get_foreground_application(self, hwnd) -> str:
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        try:
            exe_path = psutil.Process(pid).exe()
            langs = win32api.GetFileVersionInfo(exe_path, "\\VarFileInfo\\Translation")
            lang_codepage = f"{langs[0][0]:04x}{langs[0][1]:04x}"  # type: ignore
            product_name = win32api.GetFileVersionInfo(
                exe_path, f"\\StringFileInfo\\{lang_codepage}\\ProductName"
            )
            if product_name:
                return str(product_name)
            return psutil.Process(pid).name()
        except Exception:
            return psutil.Process(pid).name()

    def on_foreground_change(self, hWinEventHook, event, hwnd, idObject, idChild, dwEventThread, dwmsEventTime):
        new_time: float = time.time()
        with self.lock:
            if self.app_instance is not None:
                self.app_instance.total_duration += new_time - self.old_time
            self.old_time = new_time

            app_name = self.get_foreground_application(hwnd)
            if app_name not in system_processes:
                self.app_instance = ApplicationData.get_or_create(app_name)
            else:
                self.app_instance = None

    def run(self):
        self._thread_id = self.kernel32.GetCurrentThreadId()

        self.hook = self.user32.SetWinEventHook(
            win32con.EVENT_SYSTEM_FOREGROUND,
            win32con.EVENT_SYSTEM_FOREGROUND,
            0, self.callback, 0, 0,
            win32con.WINEVENT_OUTOFCONTEXT | win32con.WINEVENT_SKIPOWNPROCESS
        )

        msg = ctypes.wintypes.MSG()
        while self.user32.GetMessageW(ctypes.byref(msg), 0, 0, 0) != 0:
            self.user32.TranslateMessage(ctypes.byref(msg))
            self.user32.DispatchMessageW(ctypes.byref(msg))

        if self.hook:
            self.user32.UnhookWinEvent(self.hook)
            self.hook = None

    def start(self):
        ApplicationData.clear_data()
        self._thread = threading.Thread(target=self.run, daemon=True)
        self._thread.start()

    def stop(self):
        with self.lock:
            if self.app_instance is not None:
                new_time: float = time.time()
                self.app_instance.total_duration += new_time - self.old_time
                self.app_instance = None

        if self._thread_id is not None:
            WM_QUIT = 0x0012
            self.user32.PostThreadMessageW(self._thread_id, WM_QUIT, 0, 0)

        if self._thread is not None:
            self._thread.join(timeout=2)

class ApplicationData:
    _instances: dict = {}

    def __init__(self, name, total_duration) -> None:
        self.name = name
        self.total_duration = total_duration

    def to_string(self) -> str:
        return f"The user has spent {self.total_duration:.0f} seconds on {self.name}"

    @classmethod
    def get_or_create(cls, name: str):
        if name not in cls._instances:
            cls._instances[name] = cls(name, 0)
        return cls._instances[name]
    
    @classmethod
    def clear_data(cls):
        cls._instances = {}

    @classmethod
    # for debugging
    def get_all_instances_to_string(cls):
        tempStr = ""
        for instance in cls._instances.values():
            tempStr += f"{instance.to_string()}\n"
        return tempStr.rstrip()
    
    @classmethod
    def get_chart_data(cls):
        return_value: dict = {}
        for name, obj in cls._instances.items():
            return_value[name] = obj.total_duration
        return return_value