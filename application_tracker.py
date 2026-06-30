import win32gui
import win32process
import win32api
import psutil
import ctypes
import ctypes.wintypes
import win32con
import time
import threading

#system_processes = {"Microsoft® Windows® Operating System"}

class ApplicationTracker:
    def __init__(self):
        self.application_data = ApplicationData()

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
        with self.lock:
            app_name = self.get_foreground_application(hwnd)
            self.application_data.record_tab_switch(app_name, time.time())

    def run(self):
        self.thread_id = self.kernel32.GetCurrentThreadId()

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
        self.application_data.clear_data()
        self.thread = threading.Thread(target=self.run, daemon=True)
        self.thread.start()

    def stop(self):
        if self.thread_id is not None:
            WM_QUIT = 0x0012
            self.user32.PostThreadMessageW(self.thread_id, WM_QUIT, 0, 0)

        if self.thread is not None:
            self.thread.join(timeout=2)

class ApplicationData:
    _tab_switches = []

    def __init__(self):
        pass

    def record_tab_switch(self, name, timestamp):
        self._tab_switches.append((name, timestamp))
    
    def clear_data(self):
        self._tab_switches.clear()