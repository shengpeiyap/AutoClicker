"""Windows desktop auto clicker and action recorder (standard library only)."""

from __future__ import annotations

import ctypes
import json
import os
import sys
import threading
import time
import tkinter as tk
from ctypes import wintypes
from tkinter import filedialog, messagebox, ttk


def resource_path(relative_path: str) -> str:
    """Resolve a bundled asset in source mode and in a PyInstaller executable."""
    bundle_dir = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(bundle_dir, relative_path)


user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32
user32.SetWindowsHookExW.restype = ctypes.c_void_p
user32.SetWindowsHookExW.argtypes = [ctypes.c_int, ctypes.c_void_p, ctypes.c_void_p, wintypes.DWORD]
user32.CallNextHookEx.restype = ctypes.c_ssize_t
user32.CallNextHookEx.argtypes = [ctypes.c_void_p, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM]
user32.UnhookWindowsHookEx.argtypes = [ctypes.c_void_p]
user32.GetMessageW.argtypes = [ctypes.POINTER(wintypes.MSG), wintypes.HWND, wintypes.UINT, wintypes.UINT]
user32.GetMessageW.restype = wintypes.BOOL
user32.PostThreadMessageW.argtypes = [wintypes.DWORD, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
user32.SendInput.argtypes = [wintypes.UINT, ctypes.POINTER(ctypes.c_void_p), ctypes.c_int]
user32.SetCursorPos.argtypes = [ctypes.c_int, ctypes.c_int]
WH_KEYBOARD_LL = 13
WH_MOUSE_LL = 14
WM_KEYDOWN = 0x0100
WM_KEYUP = 0x0101
WM_SYSKEYDOWN = 0x0104
WM_SYSKEYUP = 0x0105
WM_MOUSEMOVE = 0x0200
WM_LBUTTONDOWN = 0x0201
WM_LBUTTONUP = 0x0202
WM_RBUTTONDOWN = 0x0204
WM_RBUTTONUP = 0x0205
WM_MBUTTONDOWN = 0x0207
WM_MBUTTONUP = 0x0208
LLKHF_INJECTED = 0x10
LLMHF_INJECTED = 0x01
INPUT_MOUSE = 0
INPUT_KEYBOARD = 1
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_SCANCODE = 0x0008
KEYEVENTF_EXTENDEDKEY = 0x0001
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010
MOUSEEVENTF_MIDDLEDOWN = 0x0020
MOUSEEVENTF_MIDDLEUP = 0x0040
VK_F6 = 0x75
VK_F7 = 0x76
VK_F8 = 0x77
VK_ESCAPE = 0x1B


class POINT(ctypes.Structure):
    _fields_ = [("x", wintypes.LONG), ("y", wintypes.LONG)]


class KBDLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [("vkCode", wintypes.DWORD), ("scanCode", wintypes.DWORD),
                ("flags", wintypes.DWORD), ("time", wintypes.DWORD),
                ("dwExtraInfo", ctypes.c_size_t)]


class MSLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [("pt", POINT), ("mouseData", wintypes.DWORD),
                ("flags", wintypes.DWORD), ("time", wintypes.DWORD),
                ("dwExtraInfo", ctypes.c_size_t)]


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [("dx", wintypes.LONG), ("dy", wintypes.LONG),
                ("mouseData", wintypes.DWORD), ("dwFlags", wintypes.DWORD),
                ("time", wintypes.DWORD), ("dwExtraInfo", ctypes.c_size_t)]


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [("wVk", wintypes.WORD), ("wScan", wintypes.WORD),
                ("dwFlags", wintypes.DWORD), ("time", wintypes.DWORD),
                ("dwExtraInfo", ctypes.c_size_t)]


class INPUTUNION(ctypes.Union):
    _fields_ = [("mi", MOUSEINPUT), ("ki", KEYBDINPUT)]


class INPUT(ctypes.Structure):
    _anonymous_ = ("u",)
    _fields_ = [("type", wintypes.DWORD), ("u", INPUTUNION)]


def send_key(vk: int, method: str = "虛擬鍵碼") -> None:
    send_key_event(vk, True, method)
    send_key_event(vk, False, method)


def send_key_event(vk: int, down: bool, method: str = "虛擬鍵碼") -> None:
    if method == "掃描碼":
        scan = int(user32.MapVirtualKeyW(vk, 4))  # MAPVK_VK_TO_VSC_EX
        if not scan:
            raise ValueError(f"無法將按鍵 {key_name(vk)} 轉換為掃描碼。")
        flags = KEYEVENTF_SCANCODE
        if scan & 0xFF00:
            flags |= KEYEVENTF_EXTENDEDKEY
        if not down:
            flags |= KEYEVENTF_KEYUP
        item = INPUT(type=INPUT_KEYBOARD, ki=KEYBDINPUT(0, scan & 0xFF, flags, 0, 0))
    else:
        flags = 0 if down else KEYEVENTF_KEYUP
        item = INPUT(type=INPUT_KEYBOARD, ki=KEYBDINPUT(vk, 0, flags, 0, 0))
    user32.SendInput(1, ctypes.cast(ctypes.byref(item), ctypes.POINTER(ctypes.c_void_p)), ctypes.sizeof(INPUT))


MOUSE_FLAGS = {
    "左鍵": (MOUSEEVENTF_LEFTDOWN, MOUSEEVENTF_LEFTUP),
    "右鍵": (MOUSEEVENTF_RIGHTDOWN, MOUSEEVENTF_RIGHTUP),
    "中鍵": (MOUSEEVENTF_MIDDLEDOWN, MOUSEEVENTF_MIDDLEUP),
}


def send_mouse_event(button: str, down: bool, x: int | None = None, y: int | None = None) -> None:
    if x is not None and y is not None:
        user32.SetCursorPos(x, y)
    flag = MOUSE_FLAGS[button][0 if down else 1]
    item = INPUT(type=INPUT_MOUSE, mi=MOUSEINPUT(0, 0, 0, flag, 0, 0))
    user32.SendInput(1, ctypes.cast(ctypes.byref(item), ctypes.POINTER(ctypes.c_void_p)), ctypes.sizeof(INPUT))


def send_click(button: str, x: int | None = None, y: int | None = None) -> None:
    if x is not None and y is not None:
        user32.SetCursorPos(x, y)
    send_mouse_event(button, True)
    send_mouse_event(button, False)


def send_mouse_move(x: int, y: int) -> None:
    user32.SetCursorPos(x, y)


def key_name(vk: int) -> str:
    scan = user32.MapVirtualKeyW(vk, 0) << 16
    buf = ctypes.create_unicode_buffer(80)
    if user32.GetKeyNameTextW(scan, buf, len(buf)):
        return buf.value
    return f"VK {vk:02X}"


def enable_dpi_awareness() -> None:
    """Keep hook coordinates and SetCursorPos coordinates in physical pixels."""
    try:
        set_context = user32.SetProcessDpiAwarenessContext
        set_context.argtypes = [ctypes.c_void_p]
        set_context.restype = wintypes.BOOL
        if set_context(ctypes.c_void_p(-4)):  # PER_MONITOR_AWARE_V2
            return
    except (AttributeError, OSError):
        pass
    try:
        shcore = ctypes.windll.shcore
        shcore.SetProcessDpiAwareness(2)  # PER_MONITOR_AWARE
        return
    except (AttributeError, OSError):
        pass
    try:
        user32.SetProcessDPIAware()
    except (AttributeError, OSError):
        pass


class HookThread(threading.Thread):
    """Owns Windows low-level hooks and forwards physical input to the UI."""
    def __init__(self, callback):
        super().__init__(daemon=True)
        self.callback = callback
        self.ready = threading.Event()
        self.error = None
        self._keyboard_proc = None
        self._mouse_proc = None
        self.thread_id = 0

    def run(self):
        self.thread_id = kernel32.GetCurrentThreadId()
        pointer = ctypes.WINFUNCTYPE(ctypes.c_ssize_t, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM)
        self.pressed_keys = set()

        def keyboard(ncode, wparam, lparam):
            if ncode >= 0 and wparam in (WM_KEYDOWN, WM_SYSKEYDOWN, WM_KEYUP, WM_SYSKEYUP):
                event = ctypes.cast(lparam, ctypes.POINTER(KBDLLHOOKSTRUCT)).contents
                if not event.flags & LLKHF_INJECTED:
                    vk = int(event.vkCode)
                    if wparam in (WM_KEYDOWN, WM_SYSKEYDOWN):
                        if vk not in self.pressed_keys:
                            self.pressed_keys.add(vk)
                            self.callback("key_down", vk, None, None)
                    elif vk in self.pressed_keys:
                        self.pressed_keys.discard(vk)
                        self.callback("key_up", vk, None, None)
            return user32.CallNextHookEx(None, ncode, wparam, lparam)

        def mouse(ncode, wparam, lparam):
            messages = {
                WM_LBUTTONDOWN: ("mouse_down", "左鍵"), WM_LBUTTONUP: ("mouse_up", "左鍵"),
                WM_RBUTTONDOWN: ("mouse_down", "右鍵"), WM_RBUTTONUP: ("mouse_up", "右鍵"),
                WM_MBUTTONDOWN: ("mouse_down", "中鍵"), WM_MBUTTONUP: ("mouse_up", "中鍵"),
                WM_MOUSEMOVE: ("mouse_move", ""),
            }
            if ncode >= 0 and wparam in messages:
                event = ctypes.cast(lparam, ctypes.POINTER(MSLLHOOKSTRUCT)).contents
                if not event.flags & LLMHF_INJECTED:
                    kind, value = messages[wparam]
                    self.callback(kind, value, int(event.pt.x), int(event.pt.y))
            return user32.CallNextHookEx(None, ncode, wparam, lparam)

        self._keyboard_proc = pointer(keyboard)
        self._mouse_proc = pointer(mouse)
        kernel32.GetModuleHandleW.restype = ctypes.c_void_p
        module = kernel32.GetModuleHandleW(None)
        k_hook = user32.SetWindowsHookExW(WH_KEYBOARD_LL, self._keyboard_proc, module, 0)
        m_hook = user32.SetWindowsHookExW(WH_MOUSE_LL, self._mouse_proc, module, 0)
        if not k_hook or not m_hook:
            self.error = ctypes.get_last_error()
            if k_hook:
                user32.UnhookWindowsHookEx(k_hook)
            if m_hook:
                user32.UnhookWindowsHookEx(m_hook)
            self.ready.set()
            return
        self.ready.set()
        msg = wintypes.MSG()
        while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))
        user32.UnhookWindowsHookEx(k_hook)
        user32.UnhookWindowsHookEx(m_hook)

    def stop(self):
        if self.thread_id:
            user32.PostThreadMessageW(self.thread_id, 0x0012, 0, 0)


class AutoClickerApp:
    def __init__(self, root):
        self.root = root
        root.title("自動點擊")
        self.app_icon_path = resource_path("mouse.ico")
        root.iconbitmap(self.app_icon_path)
        root.geometry("800x560")
        root.minsize(680, 500)
        self.running = False
        self.run_mode = None
        self.recording = False
        self.events = []
        self.started_at = 0.0
        self.pick_position = False
        self.last_move_recorded = 0.0
        self.last_move_point = None
        self.loop_count = tk.StringVar(value="0")
        self.worker = None
        self.record_window = None
        self.record_button = None
        self.play_button = None
        self.event_list = None
        self.keep_on_top = tk.BooleanVar(value=False)
        self.keyboard_mode_minimized = False
        self.record_window_was_visible = False
        self.hook = HookThread(self.on_input)
        self.hook.start()
        self.hook.ready.wait(2)
        self._build_ui()
        root.protocol("WM_DELETE_WINDOW", self.close)
        if self.hook.error:
            messagebox.showerror("輸入監聽失敗", "無法安裝鍵盤/滑鼠監聽。請重新啟動程式，或檢查 Windows 權限。")

    def _build_ui(self):
        outer = ttk.Frame(self.root, padding=14)
        outer.pack(fill="both", expand=True)
        ttk.Label(outer, text="自動點擊", font=("Microsoft JhengHei UI", 18, "bold")).pack(anchor="w")
        header = ttk.Frame(outer)
        header.pack(fill="x", pady=(2, 12))
        ttk.Label(header, text="F6 開始/停止自動操作　·　F7 錄製　·　F8 播放/停止回放", foreground="#555").pack(side="left")
        ttk.Checkbutton(header, text="主窗口保持最前", variable=self.keep_on_top,
                        command=self.apply_topmost).pack(side="right")

        click = ttk.LabelFrame(outer, text="自動操作", padding=10)
        click.pack(fill="x", pady=(0, 10))
        row = ttk.Frame(click); row.pack(fill="x", pady=3)
        self.action_row = row
        ttk.Label(row, text="操作").pack(side="left")
        self.action = tk.StringVar(value="滑鼠點擊")
        ttk.Combobox(row, textvariable=self.action, values=("滑鼠點擊", "鍵盤按鍵"), state="readonly", width=12).pack(side="left", padx=(8, 18))
        self.mouse_button_label = ttk.Label(row, text="滑鼠按鈕")
        self.mouse_button_label.pack(side="left")
        self.button = tk.StringVar(value="左鍵")
        self.button_box = ttk.Combobox(row, textvariable=self.button, values=("左鍵", "右鍵", "中鍵"), state="readonly", width=8)
        self.button_box.pack(side="left", padx=8)
        self.key_label = ttk.Label(row, text="鍵盤按鍵")
        self.key_label.pack(side="left", padx=(8, 0))
        self.key = tk.StringVar(value="空白鍵")
        self.key_box = ttk.Combobox(row, textvariable=self.key, values=("空白鍵", "Enter", "Tab", "A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z", "F1", "F2", "F3", "F4", "F5", "F8", "F9", "F10", "F11", "F12"), state="readonly", width=10)
        self.key_box.pack(side="left", padx=8)
        self.key_method_label = ttk.Label(row, text="輸入方式")
        self.key_method = tk.StringVar(value="虛擬鍵碼")
        self.key_method_box = ttk.Combobox(row, textvariable=self.key_method,
            values=("虛擬鍵碼", "掃描碼"), state="readonly", width=10)
        self.key_method_box.pack(side="left", padx=8)
        self.action.trace_add("write", lambda *_: self.update_action_controls())

        row = ttk.Frame(click); row.pack(fill="x", pady=5)
        self.interval_row = row
        ttk.Label(row, text="間隔").pack(side="left")
        self.time_vars = []
        for label, maximum in (("小時", 999), ("分鐘", 59), ("秒", 59), ("毫秒", 999)):
            var = tk.StringVar(value="0" if label != "毫秒" else "100")
            self.time_vars.append(var)
            ttk.Spinbox(row, from_=0, to=maximum, increment=1, textvariable=var, width=6).pack(side="left", padx=(8, 3))
            ttk.Label(row, text=label).pack(side="left", padx=(0, 8))
        location = ttk.Frame(click); location.pack(fill="x", pady=(0, 4))
        self.location_frame = location
        ttk.Label(location, text="點擊位置").pack(side="left")
        self.position_mode = tk.StringVar(value="目前游標位置")
        ttk.Radiobutton(location, text="目前游標位置", variable=self.position_mode, value="目前游標位置").pack(side="left", padx=(8, 10))
        ttk.Radiobutton(location, text="指定座標", variable=self.position_mode, value="指定座標").pack(side="left")
        ttk.Label(location, text="X").pack(side="left", padx=(12, 3))
        self.x_var = tk.StringVar(value="0")
        ttk.Entry(location, textvariable=self.x_var, width=9).pack(side="left")
        ttk.Label(location, text="Y").pack(side="left", padx=(8, 3))
        self.y_var = tk.StringVar(value="0")
        ttk.Entry(location, textvariable=self.y_var, width=9).pack(side="left")
        ttk.Button(location, text="從螢幕選取…", command=self.begin_pick_position).pack(side="left", padx=(10, 0))

        repeat_row = ttk.Frame(click); repeat_row.pack(fill="x", pady=(0, 4))
        ttk.Label(repeat_row, text="執行次數（0＝持續到停止）").pack(side="left")
        self.action_repeat_count = tk.StringVar(value="0")
        ttk.Spinbox(repeat_row, from_=0, to=999999, increment=1,
                    textvariable=self.action_repeat_count, width=10).pack(side="left", padx=8)

        buttons = ttk.Frame(click); buttons.pack(fill="x", pady=(8, 0))
        self.action_buttons = buttons
        self.run_button = ttk.Button(buttons, text="開始自動操作 (F6)", command=self.toggle_clicker)
        self.run_button.pack(side="left")
        ttk.Label(buttons, text="開始後按 F6 可停止。", foreground="#555").pack(side="left", padx=10)

        record_access = ttk.LabelFrame(outer, text="錄製與回放", padding=10)
        record_access.pack(fill="x", pady=(0, 10))
        ttk.Button(record_access, text="開啟錄製與回放面板…",
                   command=self.open_recording_window).pack(side="left")
        ttk.Label(record_access, text="錄製清單、播放輪數與匯入/匯出。",
                  foreground="#555").pack(side="left", padx=10)
        self.status = tk.StringVar(value="就緒。F7 可在遊戲保持前景時開始/停止錄製。")
        ttk.Label(outer, textvariable=self.status, relief="sunken", anchor="w", padding=5).pack(fill="x", pady=(10, 0))
        self.update_action_controls()

    def open_recording_window(self):
        if self.record_window is not None and self.record_window.winfo_exists():
            self.record_window.deiconify()
            self.record_window.lift()
            self.refresh_events()
            return
        window = tk.Toplevel(self.root)
        self.record_window = window
        window.title("錄製與回放")
        window.iconbitmap(self.app_icon_path)
        window.geometry("920x600")
        window.minsize(780, 500)
        window.attributes("-topmost", bool(self.keep_on_top.get()))
        window.protocol("WM_DELETE_WINDOW", self.hide_recording_window)
        outer = ttk.Frame(window, padding=12)
        outer.pack(fill="both", expand=True)
        ttk.Label(outer, text="錄製與回放", font=("Microsoft JhengHei UI", 16, "bold")).pack(anchor="w")
        ttk.Label(outer, text="F7 開始/停止錄製　·　F8 開始/停止回放；快捷鍵可在遊戲保持前景時使用。",
                  foreground="#555").pack(anchor="w", pady=(2, 10))
        toolbar = ttk.Frame(outer)
        toolbar.pack(fill="x", pady=(0, 8))
        action_bar = ttk.Frame(toolbar)
        action_bar.pack(fill="x", pady=(0, 6))
        self.record_button = ttk.Button(action_bar,
            text="停止錄製 (F7)" if self.recording else "開始錄製 (F7)", command=self.toggle_recording)
        self.record_button.pack(side="left")
        self.play_button = ttk.Button(action_bar,
            text="停止播放 (F8)" if self.run_mode == "playback" else "循環播放 (F8)",
            command=self.toggle_playback)
        self.play_button.pack(side="left", padx=6)
        ttk.Button(action_bar, text="清除", command=self.clear_recording).pack(side="left")
        ttk.Button(action_bar, text="匯入…", command=self.import_recording).pack(side="right", padx=6)
        ttk.Button(action_bar, text="匯出…", command=self.export_recording).pack(side="right")
        settings_bar = ttk.Frame(toolbar)
        settings_bar.pack(fill="x")
        ttk.Label(settings_bar, text="播放輪數（0＝持續到停止）").pack(side="left")
        ttk.Spinbox(settings_bar, from_=0, to=999999, increment=1,
                    textvariable=self.loop_count, width=8).pack(side="left", padx=(6, 18))
        ttk.Label(settings_bar, text="鍵盤回放方式").pack(side="left")
        self.record_key_method_box = ttk.Combobox(settings_bar, textvariable=self.key_method,
            values=("虛擬鍵碼", "掃描碼"), state="readonly", width=10)
        self.record_key_method_box.pack(side="left", padx=6)
        self.event_list = tk.Listbox(outer, height=18, font=("Consolas", 10), selectmode="browse")
        self.event_list.pack(fill="both", expand=True)
        self.refresh_events()

    def hide_recording_window(self):
        if self.record_window is not None and self.record_window.winfo_exists():
            self.record_window.withdraw()

    def apply_topmost(self):
        topmost = bool(self.keep_on_top.get())
        self.root.attributes("-topmost", topmost)
        if self.record_window is not None and self.record_window.winfo_exists():
            self.record_window.attributes("-topmost", topmost)

    def restore_keyboard_window(self):
        if self.keyboard_mode_minimized:
            self.keyboard_mode_minimized = False
            self.root.deiconify()
            self.root.lift()
            if (self.record_window_was_visible and self.record_window is not None
                    and self.record_window.winfo_exists()):
                self.record_window.deiconify()
                self.record_window.lift()
            self.record_window_was_visible = False

    def update_action_controls(self):
        mouse = self.action.get() == "滑鼠點擊"
        if mouse:
            self.key_label.pack_forget()
            self.key_box.pack_forget()
            self.key_method_label.pack_forget()
            self.key_method_box.pack_forget()
            self.mouse_button_label.pack(side="left")
            self.button_box.pack(side="left", padx=8, after=self.mouse_button_label)
            self.location_frame.pack(fill="x", pady=(0, 4), before=self.action_buttons)
        else:
            self.mouse_button_label.pack_forget()
            self.button_box.pack_forget()
            self.key_label.pack(side="left", padx=(8, 0))
            self.key_box.pack(side="left", padx=8, after=self.key_label)
            self.key_method_label.pack(side="left", padx=(8, 0))
            self.key_method_box.pack(side="left", padx=8, after=self.key_method_label)
            self.location_frame.pack_forget()

    def interval_seconds(self):
        h, m, s, ms = (int(v.get()) for v in self.time_vars)
        return h * 3600 + m * 60 + s + ms / 1000

    def toggle_clicker(self):
        if self.running:
            self.running = False
            self.run_mode = None
            self.run_button.configure(text="開始自動操作 (F6)")
            if self.play_button is not None and self.play_button.winfo_exists():
                self.play_button.configure(text="循環播放 (F8)")
            self.status.set("自動操作或回放已停止。")
            self.restore_keyboard_window()
            return
        try:
            interval = self.interval_seconds()
            if interval <= 0:
                raise ValueError("間隔必須大於 0 毫秒。")
            repeats = int(self.action_repeat_count.get())
            if repeats < 0:
                raise ValueError("執行次數請輸入 0 或正整數。")
            if self.position_mode.get() == "指定座標":
                x, y = int(self.x_var.get()), int(self.y_var.get())
            else:
                x = y = None
        except ValueError as exc:
            messagebox.showerror("設定錯誤", str(exc) or "時間或座標格式不正確。")
            return
        self.running = True
        self.run_mode = "clicker"
        self.run_button.configure(text="停止自動操作 (F6)")
        self.status.set("自動操作執行中。按 F6 可停止。")
        action = self.action.get()
        button = self.button.get()
        key_name_value = self.key.get()
        key_method = self.key_method.get()
        self.worker = threading.Thread(target=self.click_loop,
            args=(interval, x, y, action, button, key_name_value, repeats, key_method), daemon=True)
        if action == "鍵盤按鍵":
            # Return focus to the previously active application so simulated
            # keys cannot be typed into this tool's controls.
            self.keyboard_mode_minimized = True
            if self.record_window is not None and self.record_window.winfo_exists():
                self.record_window_was_visible = self.record_window.state() != "withdrawn"
                self.record_window.withdraw()
            self.root.iconify()
            self.root.after(150, self._start_keyboard_clicker)
        else:
            self.worker.start()

    def _start_keyboard_clicker(self):
        if self.running and self.run_mode == "clicker" and self.worker is not None:
            self.worker.start()

    def click_loop(self, interval, x, y, action, button, key_name_value, repeats, key_method):
        deadline = time.perf_counter()
        count = 0
        while self.running and (repeats == 0 or count < repeats):
            if action == "滑鼠點擊":
                send_click(button, x, y)
            else:
                mapping = {"空白鍵": 0x20, "Enter": 0x0D, "Tab": 0x09}
                vk = mapping.get(key_name_value, ord(key_name_value) if len(key_name_value) == 1 else 0x70 + int(key_name_value[1:]) - 1)
                send_key(vk, key_method)
            count += 1
            if repeats and count >= repeats:
                break
            deadline += interval
            while self.running:
                remaining = deadline - time.perf_counter()
                if remaining <= 0:
                    break
                time.sleep(min(remaining, 0.05))
        if self.run_mode == "clicker":
            self.running = False
            self.run_mode = None
            if self.keyboard_mode_minimized:
                self.root.after(0, self.restore_keyboard_window)
            self.root.after(0, lambda: self.run_button.configure(text="開始自動操作 (F6)"))
            message = (f"自動操作完成，共執行 {count} 次。" if repeats and count >= repeats
                       else "自動操作已停止。")
            self.root.after(0, lambda: self.status.set(message))

    def begin_pick_position(self):
        if self.action.get() != "滑鼠點擊":
            return
        self.pick_position = True
        self.status.set("請在螢幕上點一下目標位置；按 Esc 可取消。")

    def set_picked_position(self, x, y):
        self.x_var.set(str(x))
        self.y_var.set(str(y))
        self.position_mode.set("指定座標")
        self.status.set(f"已選取座標 ({x}, {y})；也可直接編輯 X、Y。")

    def on_input(self, kind, value, x, y):
        if kind == "key_down" and value in (VK_F6, VK_F7, VK_F8):
            command = {VK_F6: self.toggle_clicker, VK_F7: self.toggle_recording,
                       VK_F8: self.toggle_playback}[value]
            self.root.after(0, command)
            return
        if kind == "key_down" and value == VK_ESCAPE and self.pick_position:
            self.pick_position = False
            self.root.after(0, lambda: self.status.set("已取消選取座標。"))
            return
        if kind == "mouse_down" and self.pick_position:
            self.pick_position = False
            self.root.after(0, lambda: self.set_picked_position(x, y))
            return
        if not self.recording:
            return
        elapsed = time.perf_counter() - self.started_at
        if kind in ("mouse_move", "mouse_down", "mouse_up"):
            if kind == "mouse_move":
                now = time.perf_counter()
                point = (x, y)
                if now - self.last_move_recorded < 0.015 or point == self.last_move_point:
                    return
                self.last_move_recorded, self.last_move_point = now, point
            event = {"t": elapsed, "kind": kind, "x": x, "y": y}
            if kind != "mouse_move":
                event["button"] = value
        else:
            event = {"t": elapsed, "kind": kind, "vk": value, "name": key_name(value)}
        self.events.append(event)
        self.root.after(0, self.refresh_events)

    def toggle_recording(self):
        self.recording = not self.recording
        if self.recording:
            self.started_at = time.perf_counter()
            self.last_move_recorded = 0.0
            self.last_move_point = None
            if self.record_button is not None and self.record_button.winfo_exists():
                self.record_button.configure(text="停止錄製 (F7)")
            self.status.set("正在錄製鍵盤按鍵/長按及滑鼠移動/點擊/拖曳。F6/F7/F8 不會被記錄。")
        else:
            if self.record_button is not None and self.record_button.winfo_exists():
                self.record_button.configure(text="開始錄製 (F7)")
            self.status.set(f"錄製完成，共 {len(self.events)} 個動作。")

    def refresh_events(self):
        if self.event_list is None or not self.event_list.winfo_exists():
            return
        self.event_list.delete(0, tk.END)
        for event in self.events:
            stamp = f"{event['t']:8.3f}s"
            if event["kind"].startswith("key_"):
                action = "按下" if event["kind"] == "key_down" else "放開"
                desc = f"鍵盤　{action} {event['name']}"
            elif event["kind"].startswith("mouse_") and event["kind"] != "mouse_move":
                action = "按下" if event["kind"] == "mouse_down" else "放開"
                desc = f"滑鼠　{action} {event['button']}　({event['x']}, {event['y']})"
            else:
                desc = f"滑鼠移動　({event['x']}, {event['y']})"
            self.event_list.insert(tk.END, f"{stamp}  {desc}")

    def clear_recording(self):
        self.recording = False
        self.events.clear()
        if self.record_button is not None and self.record_button.winfo_exists():
            self.record_button.configure(text="開始錄製 (F7)")
        self.refresh_events()
        self.status.set("錄製已清除。")

    def play_recording(self):
        if self.running:
            return
        if not self.events:
            messagebox.showinfo("沒有錄製內容", "請先錄製一些滑鼠或鍵盤動作。")
            return
        try:
            loops = int(self.loop_count.get())
            if loops < 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("輪數錯誤", "播放輪數請輸入 0 或正整數。")
            return
        self.running = True
        self.run_mode = "playback"
        self.status.set("正在循環播放。按 F8 或 F6 可停止。")
        self.run_button.configure(text="停止播放 (F8)")
        if self.play_button is not None and self.play_button.winfo_exists():
            self.play_button.configure(text="停止播放 (F8)")
        snapshot = [dict(event) for event in self.events]
        key_method = self.key_method.get()
        self.worker = threading.Thread(target=self.play_loop, args=(snapshot, loops, key_method), daemon=True)
        self.worker.start()

    def toggle_playback(self):
        if self.running:
            if self.run_mode != "playback":
                return
            self.running = False
            self.run_mode = None
            self.status.set("正在停止回放…")
        else:
            self.play_recording()

    def play_loop(self, events, loops, key_method):
        completed = True
        loop_index = 0
        held_keys = set()
        held_buttons = set()
        while self.running and (loops == 0 or loop_index < loops):
            start = time.perf_counter()
            for event in events:
                while self.running:
                    remaining = start + event["t"] - time.perf_counter()
                    if remaining <= 0:
                        break
                    time.sleep(min(remaining, 0.02))
                if not self.running:
                    completed = False
                    break
                kind = event["kind"]
                if kind == "mouse_move":
                    send_mouse_move(event["x"], event["y"])
                elif kind in ("mouse_down", "mouse_up"):
                    down = kind == "mouse_down"
                    send_mouse_event(event["button"], down, event["x"], event["y"])
                    (held_buttons.add if down else held_buttons.discard)(event["button"])
                else:
                    down = kind == "key_down"
                    send_key_event(event["vk"], down, key_method)
                    (held_keys.add if down else held_keys.discard)(event["vk"])
            if not self.running:
                break
            loop_index += 1
        for vk in held_keys:
            send_key_event(vk, False, key_method)
        for button in held_buttons:
            send_mouse_event(button, False)
        self.running = False
        self.run_mode = None
        self.root.after(0, lambda: self.run_button.configure(text="開始自動操作 (F6)"))
        if self.play_button is not None and self.play_button.winfo_exists():
            self.root.after(0, lambda: self.play_button.configure(text="循環播放 (F8)"))
        message = (f"錄製播放完成，共 {loop_index} 輪。" if loops else
                   ("持續播放已停止。" if not completed else "錄製播放完成。"))
        self.root.after(0, lambda: self.status.set(message))

    def export_recording(self):
        path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=(("JSON 檔案", "*.json"),))
        if path:
            with open(path, "w", encoding="utf-8") as file:
                json.dump({"version": 2, "events": self.events}, file, ensure_ascii=False, indent=2)
            self.status.set(f"已匯出 {len(self.events)} 個動作。")

    def import_recording(self):
        path = filedialog.askopenfilename(filetypes=(("JSON 檔案", "*.json"),))
        if not path:
            return
        try:
            with open(path, encoding="utf-8") as file:
                data = json.load(file)
            events = data["events"]
            if not isinstance(events, list) or any(not isinstance(e, dict) for e in events):
                raise ValueError("檔案的動作資料格式不正確。")
            if any(e.get("kind") in ("key", "mouse") for e in events):
                expanded = []
                for old in events:
                    if old.get("kind") == "key":
                        base = {"t": float(old["t"]), "kind": "key_down", "vk": int(old["vk"]),
                                "name": old.get("name", key_name(int(old["vk"]))) }
                        expanded.extend((base, {**base, "kind": "key_up"}))
                    elif old.get("kind") == "mouse":
                        base = {"t": float(old["t"]), "x": int(old["x"]), "y": int(old["y"]),
                                "button": old["button"]}
                        expanded.extend(({**base, "kind": "mouse_down"}, {**base, "kind": "mouse_up"}))
                    else:
                        expanded.append(old)
                events = expanded
            for e in events:
                if not isinstance(e.get("t"), (int, float)) or e["t"] < 0:
                    raise ValueError("檔案的動作時間格式不正確。")
                if e.get("kind") not in ("key_down", "key_up", "mouse_move", "mouse_down", "mouse_up"):
                    raise ValueError("檔案含未知動作類型。")
                if e["kind"].startswith("key_") and not 0 <= int(e["vk"]) <= 255:
                    raise ValueError("檔案含無效按鍵。")
                if e["kind"].startswith("mouse_") and ("x" not in e or "y" not in e):
                    raise ValueError("檔案含無效滑鼠座標。")
                if e["kind"].startswith("mouse_"):
                    e["x"], e["y"] = int(e["x"]), int(e["y"])
                if e["kind"] in ("mouse_down", "mouse_up") and e.get("button") not in MOUSE_FLAGS:
                    raise ValueError("檔案含無效滑鼠按鍵。")
            self.events = events
            self.refresh_events()
            self.status.set(f"已匯入 {len(self.events)} 個動作。")
        except (OSError, ValueError, KeyError, TypeError, AttributeError, json.JSONDecodeError) as exc:
            messagebox.showerror("匯入失敗", str(exc))

    def close(self):
        self.running = False
        self.run_mode = None
        self.recording = False
        self.pick_position = False
        self.hook.stop()
        self.root.destroy()


if __name__ == "__main__":
    enable_dpi_awareness()
    app_root = tk.Tk()
    AutoClickerApp(app_root)
    app_root.mainloop()
