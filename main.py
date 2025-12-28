"""
EZ Key Remapper - Main entry point with system tray support.
"""
import sys
from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QAction, QMessageBox
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QColor, QFont
from PyQt5.QtCore import Qt

from installer.first_run import run_first_time_setup, check_driver_installed
from gui.main_window import MainWindow
from core.key_interceptor import get_interceptor


def create_tray_icon() -> QIcon:
    """Create a simple tray icon programmatically."""
    size = 64
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)

    # Draw background circle
    painter.setBrush(QColor(70, 130, 180))  # Steel blue
    painter.setPen(Qt.NoPen)
    painter.drawEllipse(4, 4, size - 8, size - 8)

    # Draw "K" for keyboard
    painter.setPen(QColor(255, 255, 255))
    font = QFont("Arial", 32, QFont.Bold)
    painter.setFont(font)
    painter.drawText(pixmap.rect(), Qt.AlignCenter, "K")

    painter.end()
    return QIcon(pixmap)


class Application:
    """Main application with system tray."""

    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)

        # Create main window
        self.window = MainWindow()

        # Create system tray
        self.tray_icon = QSystemTrayIcon(create_tray_icon(), self.app)
        self.tray_icon.setToolTip("EZ Key Remapper")

        # Tray menu
        tray_menu = QMenu()

        show_action = QAction("Show", self.app)
        show_action.triggered.connect(self.show_window)
        tray_menu.addAction(show_action)

        tray_menu.addSeparator()

        self.enable_action = QAction("Enabled", self.app)
        self.enable_action.setCheckable(True)
        self.enable_action.setChecked(True)
        self.enable_action.triggered.connect(self.toggle_enabled)
        tray_menu.addAction(self.enable_action)

        tray_menu.addSeparator()

        exit_action = QAction("Exit", self.app)
        exit_action.triggered.connect(self.quit)
        tray_menu.addAction(exit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.on_tray_activated)
        self.tray_icon.show()

        # Show window on start
        self.window.show()

    def show_window(self):
        """Show and bring window to front."""
        self.window.show()
        self.window.raise_()
        self.window.activateWindow()

    def toggle_enabled(self, checked: bool):
        """Toggle remapping enabled state."""
        interceptor = get_interceptor()
        interceptor.set_enabled(checked)
        self.window._enable_check.setChecked(checked)

    def on_tray_activated(self, reason):
        """Handle tray icon activation."""
        if reason == QSystemTrayIcon.DoubleClick:
            self.show_window()

    def quit(self):
        """Quit the application."""
        # Stop the interceptor
        interceptor = get_interceptor()
        interceptor.stop()

        # Hide tray icon
        self.tray_icon.hide()

        # Quit app
        self.app.quit()

    def run(self) -> int:
        """Run the application."""
        return self.app.exec_()


def main():
    # Always create QApplication first
    app = QApplication(sys.argv)

    # Check if driver is installed by trying to create context
    from core.key_interceptor import InterceptionDriver
    driver_ok = False
    try:
        test_driver = InterceptionDriver()
        test_driver.destroy()
        driver_ok = True
    except RuntimeError as e:
        driver_ok = False

    if not driver_ok:
        # Show setup dialog (skip_check=True since we already know driver isn't working)
        if not run_first_time_setup(skip_check=True):
            sys.exit(0)
        # After setup, tell user to reboot
        QMessageBox.information(
            None,
            "Reboot Required",
            "The Interception driver has been installed.\n\n"
            "Please reboot your computer, then run this app again."
        )
        sys.exit(0)

    # Driver is OK, start the main app
    main_app = Application()
    sys.exit(main_app.run())


if __name__ == "__main__":
    main()
