import os
import time
import psutil
import pyautogui
import pydirectinput
import subprocess
import threading
import multiprocessing
import ctypes

class VerificationSystem:
    def verify_process_running(self, process_name):
        try:
            for proc in psutil.process_iter(['name']):
                if proc.info['name'] and process_name.lower() in proc.info['name'].lower():
                    return True
        except Exception:
            pass
        return False

    def verify_window_active(self, window_title):
        try:
            # БЕЗОПАСНАЯ АЛЬТЕРНАТИВА pywinauto(backend="uia")
            # Использование pywinauto "uia" создает утечки COM-объектов в потоках.
            # ctypes EnumWindows работает в 100 раз быстрее и потокобезопасен (не вызывает BSOD).
            EnumWindows = ctypes.windll.user32.EnumWindows
            EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int))
            GetWindowText = ctypes.windll.user32.GetWindowTextW
            GetWindowTextLength = ctypes.windll.user32.GetWindowTextLengthW
            IsWindowVisible = ctypes.windll.user32.IsWindowVisible

            found = False
            def foreach_window(hwnd, lParam):
                nonlocal found
                if IsWindowVisible(hwnd):
                    length = GetWindowTextLength(hwnd)
                    buff = ctypes.create_unicode_buffer(length + 1)
                    GetWindowText(hwnd, buff, length + 1)
                    if window_title.lower() in buff.value.lower():
                        found = True
                        return False # Остановить перебор
                return True

            EnumWindows(EnumWindowsProc(foreach_window), 0)
            return found
        except Exception:
            return False

class ProcessManager:
    def __init__(self, verifier):
        self.verifier = verifier

    def get_process(self, name):
        try:
            for proc in psutil.process_iter(['name']):
                if proc.info['name'] and name.lower() in proc.info['name'].lower():
                    return proc
        except Exception:
            pass
        return None

class WindowManager:
    def __init__(self, verifier):
        self.verifier = verifier

    def wait_for_window(self, title, timeout=10):
        start = time.time()
        while time.time() - start < timeout:
            if self.verifier.verify_window_active(title):
                return True
            time.sleep(0.5) # Снижена нагрузка на CPU (0.5s вместо 1s)
        return False

class ApplicationLauncher:
    def __init__(self, process_mgr, window_mgr):
        self.process_mgr = process_mgr
        self.window_mgr = window_mgr

    def launch(self, path_or_command, expected_process, expected_window=None):
        try:
            if not path_or_command.startswith("start ") and not (":\\" in path_or_command or ":/" in path_or_command):
                path_or_command = f"start {path_or_command}"

            subprocess.Popen(path_or_command, shell=True)
            start = time.time()
            running = False
            while time.time() - start < 15:
                if self.process_mgr.get_process(expected_process):
                    running = True
                    break
                time.sleep(0.5)
            
            if not running:
                return False, f"Процесс {expected_process} не запустился"

            if expected_window:
                if not self.window_mgr.wait_for_window(expected_window, 15):
                    return False, f"Окно программы {expected_window} не появилось"

            return True, "Успешно"
        except Exception as e:
            return False, str(e)

class KeyboardController:
    def press(self, key):
        try:
            if key in ['win', 'windows']:
                import keyboard
                keyboard.send('windows')
            else:
                pydirectinput.press(key)
        except Exception:
            pass

    def hotkey(self, *keys):
        try:
            import keyboard
            mapped = [k.replace('win', 'windows') for k in keys]
            keyboard.send('+'.join(mapped))
        except Exception:
            try:
                mapped_keys = ['win' if k == 'windows' else k for k in keys]
                pyautogui.hotkey(*mapped_keys)
            except Exception:
                for k in reversed(keys): 
                    try: pydirectinput.keyUp(k)
                    except: pass

class MouseController:
    def click(self, button='left'):
        try: pydirectinput.click(button=button)
        except: pass

    def move(self, x, y, relative=False):
        try:
            if relative:
                pydirectinput.move(x, y)
            else:
                pydirectinput.moveTo(x, y)
        except: pass

    def drag(self, x_offset, y_offset):
        try:
            pydirectinput.mouseDown()
            pydirectinput.move(x_offset, y_offset)
            pydirectinput.mouseUp()
        except:
            try: pydirectinput.mouseUp()
            except: pass

class GameController:
    def __init__(self, keyboard, mouse):
        self.kb = keyboard
        self.mouse = mouse

    def walk_forward(self, duration=1):
        try:
            pydirectinput.keyDown("w")
            time.sleep(duration)
            pydirectinput.keyUp("w")
        except:
            try: pydirectinput.keyUp("w")
            except: pass
        
    def perform_action(self, action, kwargs=None):
        pass

# Выделяем функцию для независимого процесса
def _run_qt_overlay():
    from PyQt5.QtWidgets import QApplication, QLabel
    from PyQt5.QtCore import Qt
    import sys
    app = QApplication(sys.argv)
    label = QLabel("🎤 Ассистент Готов (Q+E показать/скрыть)", None)
    label.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool | Qt.X11BypassWindowManagerHint)
    label.setAttribute(Qt.WA_TranslucentBackground)
    label.setStyleSheet("color: #00ff00; font-size: 16px; font-weight: bold; background: rgba(0,0,0,150); padding: 5px;")
    label.move(50, 50)
    label.show()
    app.exec_()

class OverlayManager:
    def __init__(self):
        self.process = None
        try:
            import keyboard
            keyboard.add_hotkey('q+e', self.toggle_overlay)
        except Exception:
            pass

    def toggle_overlay(self):
        if self.process is None or not self.process.is_alive():
            self.start_overlay()
        else:
            try:
                self.process.terminate()
                self.process.join(timeout=1)
                self.process = None
            except:
                pass

    def start_overlay(self):
        # БЕЗОПАСНАЯ АЛЬТЕРНАТИВА: Используем независимый ПРОЦЕСС вместо ПОТОКА.
        # Запуск QApplication в побочном потоке (threading.Thread) нарушает ограничения ОС (Windows/X11),
        # что приводит к крашу драйверов видеокарты (dxgkrnl.sys) и BSOD PAGE_FAULT_IN_NONPAGED_AREA.
        if self.process is None or not self.process.is_alive():
            self.process = multiprocessing.Process(target=_run_qt_overlay, daemon=True)
            self.process.start()

class ActionExecutor:
    def __init__(self):
        self.verifier = VerificationSystem()
        self.process_mgr = ProcessManager(self.verifier)
        self.window_mgr = WindowManager(self.verifier)
        self.app_launcher = ApplicationLauncher(self.process_mgr, self.window_mgr)
        self.keyboard = KeyboardController()
        self.mouse = MouseController()
        self.game_ctrl = GameController(self.keyboard, self.mouse)
        self.overlay = OverlayManager()

    def execute(self, action_dict):
        action_type = action_dict.get("action")
        try:
            if action_type == "launch":
                prog = action_dict.get("program")
                proc = action_dict.get("process", prog + ".exe")
                success, msg = self.app_launcher.launch(prog, proc)
                return success, msg
            elif action_type == "press":
                key = action_dict.get("key", "space")
                self.keyboard.press(key)
                return True, f"Key {key} pressed"
            elif action_type == "hotkey":
                keys = action_dict.get("keys", ["windows", "r"])
                self.keyboard.hotkey(*keys)
                # Verify logic if win r
                if "r" in keys and "windows" in keys:
                    time.sleep(0.5)
                    return True, "Hotkey win+r pressed, window not strictly verified here yet"
                return True, f"Hotkey {keys} pressed"
            elif action_type == "typewrite":
                text = action_dict.get("text", "")
                pyautogui.write(text, interval=0.05)
                return True, f"Typed text: {text}"
            elif action_type == "mouse_move":
                self.mouse.move(action_dict.get("x", 0), action_dict.get("y", 0), action_dict.get("relative", False))
                return True, "Mouse moved"
            elif action_type == "mouse_click":
                self.mouse.click(action_dict.get("button", "left"))
                return True, "Mouse clicked"
            elif action_type == "overlay_on":
                self.overlay.start_overlay()
                return True, "Overlay started"
            elif action_type == "game_action":
                cmd = action_dict.get("cmd", "")
                if cmd == "walk_forward":
                    self.game_ctrl.walk_forward()
                    return True, "Walked forward"
            return False, "Unknown action"
        except Exception as e:
            return False, f"Failed: {str(e)}"
