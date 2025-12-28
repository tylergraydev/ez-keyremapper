"""
Key capture dialog - captures input and output keys for mapping.
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton,
    QHBoxLayout, QFrame
)
from PyQt5.QtCore import Qt, pyqtSignal, QObject
from PyQt5.QtGui import QFont
from typing import Optional, Tuple

from core.key_interceptor import KeyEvent, get_interceptor
from core.key_sender import vk_to_name


class KeyEventSignal(QObject):
    """Signal emitter for thread-safe key event handling."""
    detected = pyqtSignal(object)  # Emits KeyEvent


class CaptureDialog(QDialog):
    """
    Dialog for capturing a key mapping.

    Two-phase capture:
    1. Press the input key (on macro pad)
    2. Press the output key (desired result)
    """

    def __init__(self, target_device: Optional[int], parent=None):
        super().__init__(parent)
        self._target_device = target_device
        self._interceptor = get_interceptor()

        self._phase = 0  # 0 = waiting for input, 1 = waiting for output
        self._input_vk: Optional[int] = None
        self._output_vk: Optional[int] = None

        self._prev_callback = self._interceptor._on_key_event
        self._prev_enabled = self._interceptor._enabled

        # Signal for thread-safe UI updates
        self._signal = KeyEventSignal()
        self._signal.detected.connect(self._handle_key_event)

        self._setup_ui()

    def _setup_ui(self):
        self.setWindowTitle("Add Key Mapping")
        self.setFixedSize(400, 250)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Instruction label
        self._instruction_label = QLabel()
        self._instruction_label.setAlignment(Qt.AlignCenter)
        self._instruction_label.setWordWrap(True)
        font = QFont()
        font.setPointSize(12)
        self._instruction_label.setFont(font)
        layout.addWidget(self._instruction_label)

        # Key display frame
        key_frame = QFrame()
        key_frame.setFrameStyle(QFrame.StyledPanel)
        key_frame.setStyleSheet("""
            QFrame {
                background-color: #f0f0f0;
                border: 2px solid #ccc;
                border-radius: 8px;
            }
        """)
        key_layout = QHBoxLayout(key_frame)

        # Input key display
        input_container = QVBoxLayout()
        input_title = QLabel("Input Key")
        input_title.setAlignment(Qt.AlignCenter)
        self._input_label = QLabel("---")
        self._input_label.setAlignment(Qt.AlignCenter)
        self._input_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #333;")
        input_container.addWidget(input_title)
        input_container.addWidget(self._input_label)
        key_layout.addLayout(input_container)

        # Arrow
        arrow = QLabel("\u2192")  # Right arrow
        arrow.setAlignment(Qt.AlignCenter)
        arrow.setStyleSheet("font-size: 32px; color: #666;")
        key_layout.addWidget(arrow)

        # Output key display
        output_container = QVBoxLayout()
        output_title = QLabel("Output Key")
        output_title.setAlignment(Qt.AlignCenter)
        self._output_label = QLabel("---")
        self._output_label.setAlignment(Qt.AlignCenter)
        self._output_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #333;")
        output_container.addWidget(output_title)
        output_container.addWidget(self._output_label)
        key_layout.addLayout(output_container)

        layout.addWidget(key_frame)

        # Status label
        self._status_label = QLabel()
        self._status_label.setAlignment(Qt.AlignCenter)
        self._status_label.setStyleSheet("color: #666; font-style: italic;")
        layout.addWidget(self._status_label)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self._cancel_btn = QPushButton("Cancel")
        self._cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self._cancel_btn)

        self._confirm_btn = QPushButton("Confirm")
        self._confirm_btn.setEnabled(False)
        self._confirm_btn.clicked.connect(self.accept)
        button_layout.addWidget(self._confirm_btn)

        layout.addLayout(button_layout)

        # Start phase 1
        self._start_phase1()

    def _start_phase1(self):
        """Start phase 1: capture input key."""
        self._phase = 0
        self._instruction_label.setText(
            "Press the key on your MACRO PAD\n"
            "that you want to remap"
        )
        self._status_label.setText("Waiting for input key...")

        # Set up callback to receive key events
        self._interceptor.set_enabled(False)  # Don't remap during capture
        self._interceptor.set_key_event_callback(self._on_key_event)

    def _start_phase2(self):
        """Start phase 2: capture output key."""
        self._phase = 1
        self._instruction_label.setText(
            "Now press the DESIRED OUTPUT KEY\n"
            "(e.g., F1, F2, etc.)"
        )
        self._status_label.setText("Waiting for output key...")

    def _device_matches(self, event: KeyEvent) -> bool:
        """Check if the event came from the target device."""
        if self._target_device is None:
            return True  # No target set, accept any device

        return event.device == self._target_device

    def _on_key_event(self, event: KeyEvent):
        """Handle key events during capture (called from interceptor thread)."""
        # Only process key down events
        if event.is_key_up:
            return

        # Emit signal to handle on main thread
        self._signal.detected.emit(event)

    def _handle_key_event(self, event: KeyEvent):
        """Handle key events on the main Qt thread."""
        if self._phase == 0:
            # Phase 1: capture input key
            # Check if it's from the target device (if set)
            if self._target_device is not None and not self._device_matches(event):
                self._status_label.setText(
                    f"Wrong device! (Got device {event.device}, expected {self._target_device})"
                )
                return

            self._input_vk = event.vk_code
            self._input_label.setText(vk_to_name(event.vk_code))
            self._start_phase2()

        elif self._phase == 1:
            # Phase 2: capture output key (from any device)
            self._output_vk = event.vk_code
            self._output_label.setText(vk_to_name(event.vk_code))
            self._status_label.setText("Mapping captured! Click Confirm to add.")
            self._confirm_btn.setEnabled(True)

    def get_mapping(self) -> Optional[Tuple[int, int]]:
        """Get the captured mapping (input_vk, output_vk)."""
        if self._input_vk is not None and self._output_vk is not None:
            return (self._input_vk, self._output_vk)
        return None

    def closeEvent(self, event):
        """Restore interceptor state on close."""
        self._interceptor.set_key_event_callback(self._prev_callback)
        self._interceptor.set_enabled(self._prev_enabled)
        super().closeEvent(event)

    def reject(self):
        """Handle cancel/close."""
        self._interceptor.set_key_event_callback(self._prev_callback)
        self._interceptor.set_enabled(self._prev_enabled)
        super().reject()

    def accept(self):
        """Handle confirm."""
        self._interceptor.set_key_event_callback(self._prev_callback)
        self._interceptor.set_enabled(self._prev_enabled)
        super().accept()
