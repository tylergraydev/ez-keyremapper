"""
Device detection dialog - detects which keyboard device the user presses a key on.
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
)
from PyQt5.QtCore import Qt, pyqtSignal, QObject
from PyQt5.QtGui import QFont
from typing import Optional

from core.key_interceptor import KeyEvent, get_interceptor


class KeyEventSignal(QObject):
    """Signal emitter for thread-safe key event handling."""
    detected = pyqtSignal(object)  # Emits KeyEvent


class DetectDeviceDialog(QDialog):
    """
    Dialog for detecting which keyboard device the user is pressing keys on.
    Returns the device number of the detected device.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._interceptor = get_interceptor()
        self._detected_device: Optional[int] = None
        self._detected_hardware_id: Optional[str] = None

        self._prev_callback = self._interceptor._on_key_event
        self._prev_enabled = self._interceptor._enabled

        # Signal for thread-safe UI updates
        self._signal = KeyEventSignal()
        self._signal.detected.connect(self._handle_detected_key)

        self._setup_ui()
        self._start_detection()

    def _setup_ui(self):
        self.setWindowTitle("Detect Device")
        self.setFixedSize(350, 180)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Instruction
        instruction = QLabel(
            "Press any key on your MACRO PAD\n"
            "to automatically detect it"
        )
        instruction.setAlignment(Qt.AlignCenter)
        instruction.setWordWrap(True)
        font = QFont()
        font.setPointSize(12)
        instruction.setFont(font)
        layout.addWidget(instruction)

        # Status/result label
        self._status_label = QLabel("Waiting for keypress...")
        self._status_label.setAlignment(Qt.AlignCenter)
        self._status_label.setStyleSheet(
            "color: #666; font-style: italic; padding: 10px;"
            "background-color: #f5f5f5; border-radius: 5px;"
        )
        layout.addWidget(self._status_label)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self._cancel_btn = QPushButton("Cancel")
        self._cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self._cancel_btn)

        self._use_btn = QPushButton("Use This Device")
        self._use_btn.setEnabled(False)
        self._use_btn.clicked.connect(self.accept)
        self._use_btn.setStyleSheet("font-weight: bold;")
        button_layout.addWidget(self._use_btn)

        layout.addLayout(button_layout)

    def _start_detection(self):
        """Start listening for key events."""
        self._interceptor.set_enabled(False)  # Don't remap during detection
        self._interceptor.set_key_event_callback(self._on_key_event)

    def _on_key_event(self, event: KeyEvent):
        """Handle key events during detection (called from interceptor thread)."""
        # Only process key down events
        if event.is_key_up:
            return

        # Emit signal to handle on main thread
        self._signal.detected.emit(event)

    def _handle_detected_key(self, event: KeyEvent):
        """Handle detected key on the main Qt thread."""
        # Store the device info
        self._detected_device = event.device
        self._detected_hardware_id = event.hardware_id

        # Update UI
        try:
            # Extract VID/PID from hardware ID for display
            hw_upper = event.hardware_id.upper() if event.hardware_id else ""
            vid = pid = ""
            if "VID_" in hw_upper:
                try:
                    vid_start = hw_upper.index("VID_") + 4
                    vid = hw_upper[vid_start:vid_start + 4]
                except (ValueError, IndexError):
                    pass
            if "PID_" in hw_upper:
                try:
                    pid_start = hw_upper.index("PID_") + 4
                    pid = hw_upper[pid_start:pid_start + 4]
                except (ValueError, IndexError):
                    pass

            if vid and pid:
                display = f"Detected: Device {event.device}\nVID:{vid} PID:{pid}"
            else:
                display = f"Detected: Device {event.device}"

            self._status_label.setText(display)
            self._status_label.setStyleSheet(
                "color: green; font-weight: bold; padding: 10px;"
                "background-color: #e8f5e9; border-radius: 5px;"
            )
            self._use_btn.setEnabled(True)
        except Exception as e:
            print(f"[DETECT] Error updating UI: {e}", flush=True)

    def get_device(self) -> Optional[int]:
        """Get the detected device number."""
        return self._detected_device

    def get_hardware_id(self) -> Optional[str]:
        """Get the detected device hardware ID."""
        return self._detected_hardware_id

    def _restore_interceptor(self):
        """Restore interceptor to previous state."""
        self._interceptor.set_key_event_callback(self._prev_callback)
        self._interceptor.set_enabled(self._prev_enabled)

    def closeEvent(self, event):
        """Restore interceptor state on close."""
        self._restore_interceptor()
        super().closeEvent(event)

    def reject(self):
        """Handle cancel/close."""
        self._restore_interceptor()
        super().reject()

    def accept(self):
        """Handle confirm."""
        self._restore_interceptor()
        super().accept()
