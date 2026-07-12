import sys
import PySide6
from PySide6.QtWidgets import QApplication
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from GUI.main_window import MainWindow
from PySide6 import QtCore
from PySide6.QtCore import QMetaObject
from PySide6.QtCore import Qt


# 監視用のイベントハンドラを少しシンプルにする
class QSSHandler(FileSystemEventHandler):
    def __init__(self, target_window, qss_path):
        self.window = target_window
        self.qss_path = qss_path

    def on_modified(self, event):
        # 重要なのはここ！ Qt.QueuedConnection を使ってメインスレッドへ処理を予約します
        QMetaObject.invokeMethod(
            self.window,
            "load_stylesheet",
            Qt.ConnectionType.QueuedConnection,
            QtCore.Q_ARG(str, self.qss_path),
        )
        print("QSS 再読み込みの要求をメインスレッドに送りました。")


# 実行部
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()

    # 監視設定
    qss_path = "GUI/style.qss"
    observer = Observer()
    observer.schedule(QSSHandler(window, qss_path), path="GUI/", recursive=False)
    observer.start()

    window.show()
    sys.exit(app.exec())
