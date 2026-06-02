import os
import time
import psutil
import pyautogui
import pydirectinput
import subprocess
from pywinauto import Application, Desktop
import threading
import speech_recognition as sr

class VerificationSystem:
    def verify_process_running(self, process_name):
        for proc in psutil.process_iter(['name']):
            if process_name.lower() in proc.info['name'].lower():
                return True
        return False

    def verify_window_active(self, window_title):
        try:
            # We can use pygetwindow or pywinauto
            from pywinauto import Desktop
            windows = Desktop(backend="uia").windows()
            for w in windows:
                if window_title.lower() in w.window_text().lower() and w.is_active():
                    return True
            return False
        except Exception:
            return False

class ProcessManager:
    def __init__(self, verifier):
        self.verifier = verifier

    def get_process(self, name):
        for proc in psutil.process_iter(['name']):
            if name.lower() in proc.info['name'].lower():
                return proc
        return None

class WindowManager:
    def __init__(self, verifier):
        self.verifier = verifier

    def wait_for_window(self, title, timeout=10):
        start = time.time()
        while time.time() - start < timeout:
            if self.verifier.verify_window_active(title):
                return True
            time.sleep(1)
        return False

class ApplicationLauncher:
    def __init__(self, process_mgr, window_mgr):
        self.process_mgr = process_mgr
        self.window_mgr = window_mgr

    def launch(self, path_or_command, expected_process, expected_window=None):
        try:
            # Try running
            subprocess.Popen(path_or_command, shell=True)
            # Wait for process
            start = time.time()
            running = False
            while time.time() - start < 15:
                if self.process_mgr.get_process(expected_process):
                    running = True
                    break
                time.sleep(1)
            
            if not running:
                return False, "Процесс не запустился"

            if expected_window:
                if not self.window_mgr.wait_for_window(expected_window, 20):
                    return False, "Окно программы не появилось"

            return True, "Успешно"
        except Exception as e:
            return False, str(e)

class KeyboardController:
    def press(self, key):
        pydirectinput.press(key)

    def hotkey(self, *keys):
        # pydirectinput doesn't have a direct hotkey, pyautogui does but might not work in games.
        # usually we do keyDown then keyUp.
        for k in keys: pydirectinput.keyDown(k)
        for k in reversed(keys): pydirectinput.keyUp(k)

class MouseController:
    def click(self, button='left'):
        pydirectinput.click(button=button)

    def move(self, x, y, relative=False):
        if relative:
            pydirectinput.move(x, y)
        else:
            pydirectinput.moveTo(x, y)

    def drag(self, x_offset, y_offset):
        pydirectinput.mouseDown()
        pydirectinput.move(x_offset, y_offset)
        pydirectinput.mouseUp()

class GameController:
    def __init__(self, keyboard, mouse):
        self.kb = keyboard
        self.mouse = mouse

    def walk_forward(self, duration=1):
        pydirectinput.keyDown("w")
        time.sleep(duration)
        pydirectinput.keyUp("w")
        
    def perform_action(self, action, kwargs=None):
        pass # Handle game specific actions

class OverlayManager:
    def __init__(self):
        self.running = False
        self.overlay_thread = None

    def start_overlay(self):
        # A simple PyQt overlay in a separate thread
        if not self.running:
            self.running = True
            def run_qt():
                from PyQt5.QtWidgets import QApplication, QLabel
                from PyQt5.QtCore import Qt
                import sys
                
                # Check if app exists
                app = QApplication.instance()
                if not app:
                    app = QApplication(sys.argv)
                
                label = QLabel("🎤 Ассистент Готов (Q+E показать/скрыть)", None)
                label.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool | Qt.X11BypassWindowManagerHint)
                label.setAttribute(Qt.WA_TranslucentBackground)
                label.setStyleSheet("color: #00ff00; font-size: 16px; font-weight: bold; background: rgba(0,0,0,150); padding: 5px;")
                label.move(50, 50)
                label.show()
                app.exec_()

            self.overlay_thread = threading.Thread(target=run_qt, daemon=True)
            self.overlay_thread.start()

class VoiceManager:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.is_listening = False

    def start_listening(self, callback):
        self.is_listening = True
        def listen_loop():
            with sr.Microphone() as source:
                self.recognizer.adjust_for_ambient_noise(source)
                while self.is_listening:
                    try:
                        audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=5)
                        text = self.recognizer.recognize_google(audio, language="ru-RU")
                        if text:
                            callback(text)
                    except sr.WaitTimeoutError:
                        continue
                    except Exception as e:
                        pass
        t = threading.Thread(target=listen_loop, daemon=True)
        t.start()

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
        self.voice = VoiceManager()

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
