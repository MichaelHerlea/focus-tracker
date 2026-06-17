import win32gui
import win32process
import win32api
import psutil
import ctypes
import ctypes.wintypes
import win32con
import time

from ApplicationSpecificData import ApplicationSpecificData

def get_foreground_application(hwnd) -> str:
    _, pid = win32process.GetWindowThreadProcessId(hwnd)
    try:
        exe_path = psutil.Process(pid).exe()
        langs = win32api.GetFileVersionInfo(exe_path, "\\VarFileInfo\\Translation")
        lang_codepage = f"{langs[0][0]:04x}{langs[0][1]:04x}" # type: ignore
        product_name = win32api.GetFileVersionInfo(exe_path, f"\\StringFileInfo\\{lang_codepage}\\ProductName")
        if product_name:
            return str(product_name)
        return psutil.Process(pid).name()
    except:
        return psutil.Process(pid).name()

user32 = ctypes.windll.user32

WinEventProc = ctypes.CFUNCTYPE(
    None,
    ctypes.wintypes.HANDLE,
    ctypes.wintypes.DWORD,
    ctypes.wintypes.HWND,
    ctypes.wintypes.LONG,
    ctypes.wintypes.LONG,
    ctypes.wintypes.DWORD,
    ctypes.wintypes.DWORD,
)

old_time: float = time.time()
app_instance = None

def on_foreground_change(hWinEventHook, event, hwnd, idObject, idChild, dwEventThread, dwmsEventTime):
    global old_time
    global app_instance

    if app_instance is not None:
        new_time: float = time.time()
        app_instance.total_duration += new_time - old_time
        print(app_instance.to_string())
    old_time = time.time()

    app_name = get_foreground_application(hwnd)
    app_instance = ApplicationSpecificData.get_or_create(app_name)

callback = WinEventProc(on_foreground_change)

user32.SetWinEventHook(
    win32con.EVENT_SYSTEM_FOREGROUND,
    win32con.EVENT_SYSTEM_FOREGROUND,
    0, callback, 0, 0,
    win32con.WINEVENT_OUTOFCONTEXT | win32con.WINEVENT_SKIPOWNPROCESS
)

msg = ctypes.wintypes.MSG()
while user32.GetMessageW(ctypes.byref(msg), 0, 0, 0) != 0:
    user32.TranslateMessage(ctypes.byref(msg))
    user32.DispatchMessageW(ctypes.byref(msg))