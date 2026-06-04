import sys
from PyQt5.QtWidgets import QApplication, QLabel
from PyQt5.QtCore import Qt

def run():
    app = QApplication(sys.argv)
    label = QLabel("🎤 Ассистент Готов (Оверлей)", None)
    label.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool | Qt.X11BypassWindowManagerHint)
    label.setAttribute(Qt.WA_TranslucentBackground)
    label.setStyleSheet("color: #00ff00; font-size: 16px; font-weight: bold; background: rgba(0,0,0,150); padding: 5px;")
    label.move(50, 50)
    label.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    run()
