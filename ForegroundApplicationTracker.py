import win32gui
import win32process
import win32api
import psutil
import ctypes
import ctypes.wintypes
import win32con
import time
from ApplicationSpecificData import ApplicationSpecificData


class ForegroundApplicationTracker:
    def __init__(self) -> None:
        self.old_time: float = time.time()
        self.app_instance = None

        self.user32 = ctypes.windll.user32

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
        if self.app_instance is not None:
            self.app_instance.total_duration += new_time - self.old_time
        self.old_time = new_time

        app_name = self.get_foreground_application(hwnd)
        self.app_instance = ApplicationSpecificData.get_or_create(app_name)

    def start(self) -> None:
        ApplicationSpecificData.clear_data()
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

    def stop(self) -> None:
        if self.app_instance is not None:
            new_time: float = time.time()
            self.app_instance.total_duration += new_time - self.old_time
            self.app_instance = None
        if self.hook:
            self.user32.UnhookWinEvent(self.hook)
            self.hook = None