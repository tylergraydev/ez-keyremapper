"""
Key capture dialog - captures input and output keys for mapping.
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton,
    QHBoxLayout, QFrame, QCheckBox
)
from PyQt5.QtCore import Qt, pyqtSignal, QObject
from PyQt5.QtGui import QFont
from typing import Optional, Tuple, List, Union

from core.key_interceptor import KeyEvent, get_interceptor
from core.key_sender import vk_to_name, VK_CODES


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
        self._output_keys: List[int] = []  # Support multiple output keys (combo)

        self._prev_callback = self._interceptor._on_key_event
        self._prev_enabled = self._interceptor._enabled

        # Signal for thread-safe UI updates
        self._signal = KeyEventSignal()
        self._signal.detected.connect(self._handle_key_event)

        self._setup_ui()

    def _setup_ui(self):
        self.setWindowTitle("Add Key Mapping")
        self.setFixedSize(500, 380)
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
        output_title = QLabel("Output Key(s)")
        output_title.setAlignment(Qt.AlignCenter)
        self._output_label = QLabel("---")
        self._output_label.setAlignment(Qt.AlignCenter)
        self._output_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #333;")
        self._output_label.setWordWrap(True)
        output_container.addWidget(output_title)
        output_container.addWidget(self._output_label)
        key_layout.addLayout(output_container)

        layout.addWidget(key_frame)

        # Special keys section (for keys that are hard to press)
        special_label = QLabel("Or select a special key:")
        special_label.setAlignment(Qt.AlignCenter)
        special_label.setStyleSheet("color: #666; font-size: 10px; margin-top: 5px;")
        layout.addWidget(special_label)

        special_layout = QHBoxLayout()
        special_layout.addStretch()

        # Volume keys
        self._vol_up_btn = QPushButton("Vol Up")
        self._vol_up_btn.clicked.connect(lambda: self._add_special_key(VK_CODES['VOLUME_UP']))
        self._vol_up_btn.setEnabled(False)
        special_layout.addWidget(self._vol_up_btn)

        self._vol_down_btn = QPushButton("Vol Down")
        self._vol_down_btn.clicked.connect(lambda: self._add_special_key(VK_CODES['VOLUME_DOWN']))
        self._vol_down_btn.setEnabled(False)
        special_layout.addWidget(self._vol_down_btn)

        self._mute_btn = QPushButton("Mute")
        self._mute_btn.clicked.connect(lambda: self._add_special_key(VK_CODES['VOLUME_MUTE']))
        self._mute_btn.setEnabled(False)
        special_layout.addWidget(self._mute_btn)

        # Media keys
        self._play_btn = QPushButton("Play/Pause")
        self._play_btn.clicked.connect(lambda: self._add_special_key(VK_CODES['MEDIA_PLAY_PAUSE']))
        self._play_btn.setEnabled(False)
        special_layout.addWidget(self._play_btn)

        self._next_btn = QPushButton("Next")
        self._next_btn.clicked.connect(lambda: self._add_special_key(VK_CODES['MEDIA_NEXT']))
        self._next_btn.setEnabled(False)
        special_layout.addWidget(self._next_btn)

        self._prev_btn = QPushButton("Prev")
        self._prev_btn.clicked.connect(lambda: self._add_special_key(VK_CODES['MEDIA_PREV']))
        self._prev_btn.setEnabled(False)
        special_layout.addWidget(self._prev_btn)

        special_layout.addStretch()
        layout.addLayout(special_layout)

        # Add more keys button (for combos)
        combo_layout = QHBoxLayout()
        combo_layout.addStretch()
        self._add_key_btn = QPushButton("+ Add Another Key (Combo)")
        self._add_key_btn.setEnabled(False)
        self._add_key_btn.clicked.connect(self._add_more_keys)
        self._add_key_btn.setToolTip("Add more keys to create a combo like Ctrl+Shift+V")
        combo_layout.addWidget(self._add_key_btn)

        self._clear_output_btn = QPushButton("Clear Output")
        self._clear_output_btn.setEnabled(False)
        self._clear_output_btn.clicked.connect(self._clear_output)
        combo_layout.addWidget(self._clear_output_btn)
        combo_layout.addStretch()
        layout.addLayout(combo_layout)

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
        """Start phase 2: capture output key(s)."""
        self._phase = 1
        self._output_keys = []
        self._instruction_label.setText(
            "Now press the DESIRED OUTPUT KEY\n"
            "(or use buttons below for special keys)"
        )
        self._status_label.setText("Waiting for output key...")
        # Enable special key buttons
        self._set_special_buttons_enabled(True)

    def _set_special_buttons_enabled(self, enabled: bool):
        """Enable or disable all special key buttons."""
        self._vol_up_btn.setEnabled(enabled)
        self._vol_down_btn.setEnabled(enabled)
        self._mute_btn.setEnabled(enabled)
        self._play_btn.setEnabled(enabled)
        self._next_btn.setEnabled(enabled)
        self._prev_btn.setEnabled(enabled)

    def _add_special_key(self, vk_code: int):
        """Add a special key (from button click) to the output."""
        if self._phase != 1:
            return

        # Don't add duplicate keys
        if vk_code not in self._output_keys:
            self._output_keys.append(vk_code)

        self._output_label.setText(self._format_output_keys())
        self._add_key_btn.setEnabled(True)
        self._clear_output_btn.setEnabled(True)
        self._confirm_btn.setEnabled(True)

        if len(self._output_keys) == 1:
            self._status_label.setText(
                "Mapping captured! Click Confirm, or add more keys for a combo."
            )
        else:
            self._status_label.setText(
                f"Combo: {len(self._output_keys)} keys. Add more or Confirm."
            )

    def _add_more_keys(self):
        """Switch back to waiting for another output key."""
        self._phase = 1
        self._instruction_label.setText(
            "Press ANOTHER KEY to add to combo\n"
            f"Current: {self._format_output_keys()}"
        )
        self._status_label.setText("Waiting for next key...")
        self._add_key_btn.setEnabled(False)
        self._confirm_btn.setEnabled(False)
        self._set_special_buttons_enabled(True)

    def _clear_output(self):
        """Clear all output keys and restart phase 2."""
        self._output_keys = []
        self._output_label.setText("---")
        self._add_key_btn.setEnabled(False)
        self._clear_output_btn.setEnabled(False)
        self._confirm_btn.setEnabled(False)
        self._start_phase2()

    def _format_output_keys(self) -> str:
        """Format output keys for display."""
        if not self._output_keys:
            return "---"
        return " + ".join(vk_to_name(vk) for vk in self._output_keys)

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
            # Phase 2: capture output key(s) (from any device)
            # Don't add duplicate keys
            if event.vk_code not in self._output_keys:
                self._output_keys.append(event.vk_code)

            self._output_label.setText(self._format_output_keys())
            self._add_key_btn.setEnabled(True)
            self._clear_output_btn.setEnabled(True)
            self._confirm_btn.setEnabled(True)

            if len(self._output_keys) == 1:
                self._status_label.setText(
                    "Mapping captured! Click Confirm, or add more keys for a combo."
                )
            else:
                self._status_label.setText(
                    f"Combo: {len(self._output_keys)} keys. Add more or Confirm."
                )

    def get_mapping(self) -> Optional[Tuple[int, Union[int, List[int]]]]:
        """Get the captured mapping (input_vk, output_vk or [vk1, vk2, ...])."""
        if self._input_vk is not None and self._output_keys:
            # Return single int if only one key, list if combo
            if len(self._output_keys) == 1:
                return (self._input_vk, self._output_keys[0])
            else:
                return (self._input_vk, self._output_keys.copy())
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
