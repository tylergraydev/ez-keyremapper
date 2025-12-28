"""
Main window for EZ Key Remapper.
"""
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QPushButton, QListWidget, QListWidgetItem,
    QCheckBox, QGroupBox, QMessageBox, QFrame
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from typing import Dict, Optional, List

from core.key_interceptor import get_interceptor, KeyboardDevice
from core.key_sender import vk_to_name
from core.config import Config, save_config, load_config
from gui.capture_dialog import CaptureDialog
from gui.detect_dialog import DetectDeviceDialog


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self):
        super().__init__()
        self._keyboards: List[KeyboardDevice] = []
        self._config = load_config()
        self._interceptor = get_interceptor()

        self._setup_ui()
        self._load_devices()
        self._apply_config()

        # Start the interceptor
        self._interceptor.start()

    def _setup_ui(self):
        self.setWindowTitle("EZ Key Remapper")
        self.setMinimumSize(450, 400)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setSpacing(15)
        layout.setContentsMargins(15, 15, 15, 15)

        # Title
        title = QLabel("EZ Key Remapper")
        title.setAlignment(Qt.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)

        # Device selection group
        device_group = QGroupBox("Target Device")
        device_layout = QVBoxLayout(device_group)

        # Device combo and buttons
        device_row = QHBoxLayout()
        self._device_combo = QComboBox()
        self._device_combo.setMinimumWidth(250)
        self._device_combo.currentIndexChanged.connect(self._on_device_changed)
        device_row.addWidget(self._device_combo)

        detect_btn = QPushButton("Detect")
        detect_btn.setToolTip("Press any key on your macro pad to auto-detect it")
        detect_btn.clicked.connect(self._detect_device)
        device_row.addWidget(detect_btn)

        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self._load_devices)
        device_row.addWidget(refresh_btn)

        device_layout.addLayout(device_row)

        # Device info
        self._device_info = QLabel("")
        self._device_info.setStyleSheet("color: #666; font-size: 10px;")
        device_layout.addWidget(self._device_info)

        layout.addWidget(device_group)

        # Key mappings group
        mapping_group = QGroupBox("Key Mappings")
        mapping_layout = QVBoxLayout(mapping_group)

        self._mapping_list = QListWidget()
        self._mapping_list.setMinimumHeight(120)
        mapping_layout.addWidget(self._mapping_list)

        # Mapping buttons
        mapping_btn_layout = QHBoxLayout()
        add_btn = QPushButton("Add Mapping")
        add_btn.clicked.connect(self._add_mapping)
        mapping_btn_layout.addWidget(add_btn)

        remove_btn = QPushButton("Remove")
        remove_btn.clicked.connect(self._remove_mapping)
        mapping_btn_layout.addWidget(remove_btn)

        clear_btn = QPushButton("Clear All")
        clear_btn.clicked.connect(self._clear_mappings)
        mapping_btn_layout.addWidget(clear_btn)

        mapping_layout.addLayout(mapping_btn_layout)
        layout.addWidget(mapping_group)

        # Enable checkbox
        self._enable_check = QCheckBox("Enable Key Remapping")
        self._enable_check.setChecked(True)
        self._enable_check.stateChanged.connect(self._on_enable_changed)
        layout.addWidget(self._enable_check)

        # Status
        self._status_label = QLabel("Status: Ready")
        self._status_label.setStyleSheet(
            "padding: 10px; background-color: #e8f5e9; border-radius: 5px;"
        )
        layout.addWidget(self._status_label)

        # Hint
        hint = QLabel("Tip: Close the window to minimize to system tray")
        hint.setAlignment(Qt.AlignCenter)
        hint.setStyleSheet("color: #888; font-size: 10px;")
        layout.addWidget(hint)

    def _load_devices(self):
        """Load keyboard devices into combo box."""
        self._device_combo.clear()

        try:
            self._keyboards = self._interceptor.get_keyboards()
        except RuntimeError as e:
            QMessageBox.critical(
                self,
                "Driver Error",
                f"Failed to load Interception driver:\n\n{e}\n\n"
                "Please install the driver from:\n"
                "https://github.com/oblitum/Interception/releases"
            )
            self._keyboards = []

        self._device_combo.addItem("-- Select a device --", None)

        for kb in self._keyboards:
            self._device_combo.addItem(kb.get_display_name(), kb.device_number)

        # Try to restore previous selection
        if self._config.target_device is not None:
            for i in range(self._device_combo.count()):
                if self._device_combo.itemData(i) == self._config.target_device:
                    self._device_combo.setCurrentIndex(i)
                    break

    def _apply_config(self):
        """Apply loaded configuration."""
        # Set mappings
        self._interceptor.set_mappings(self._config.mappings)
        self._update_mapping_list()

        # Set enabled state
        self._enable_check.setChecked(self._config.enabled)
        self._interceptor.set_enabled(self._config.enabled)

        # Set target device
        if self._config.target_device is not None:
            self._interceptor.set_target_device(self._config.target_device)

    def _save_config(self):
        """Save current configuration."""
        self._config.target_device = self._device_combo.currentData()
        self._config.mappings = self._interceptor._mappings.copy()
        self._config.enabled = self._enable_check.isChecked()
        save_config(self._config)

    def _on_device_changed(self, index: int):
        """Handle device selection change."""
        device = self._device_combo.currentData()
        self._interceptor.set_target_device(device)

        # Update device info
        if device is not None:
            for kb in self._keyboards:
                if kb.device_number == device:
                    self._device_info.setText(f"Hardware: {kb.hardware_id[:50]}...")
                    break
        else:
            self._device_info.setText("")

        self._save_config()
        self._update_status()

    def _on_enable_changed(self, state: int):
        """Handle enable checkbox change."""
        enabled = state == Qt.Checked
        self._interceptor.set_enabled(enabled)
        self._save_config()
        self._update_status()

    def _update_status(self):
        """Update status label."""
        device = self._device_combo.currentData()
        enabled = self._enable_check.isChecked()
        num_mappings = len(self._interceptor._mappings)

        if not device:
            self._status_label.setText("Status: No device selected")
            self._status_label.setStyleSheet(
                "padding: 10px; background-color: #fff3e0; border-radius: 5px;"
            )
        elif not enabled:
            self._status_label.setText("Status: Disabled")
            self._status_label.setStyleSheet(
                "padding: 10px; background-color: #fce4ec; border-radius: 5px;"
            )
        elif num_mappings == 0:
            self._status_label.setText("Status: No mappings configured")
            self._status_label.setStyleSheet(
                "padding: 10px; background-color: #fff3e0; border-radius: 5px;"
            )
        else:
            self._status_label.setText(f"Status: Active ({num_mappings} mappings)")
            self._status_label.setStyleSheet(
                "padding: 10px; background-color: #e8f5e9; border-radius: 5px;"
            )

    def _detect_device(self):
        """Open dialog to detect device by pressing a key on it."""
        dialog = DetectDeviceDialog(self)
        if dialog.exec_() == DetectDeviceDialog.Accepted:
            detected_device = dialog.get_device()
            detected_hw_id = dialog.get_hardware_id()

            if detected_device is not None:
                # Find and select this device in the dropdown
                found = False
                for i in range(self._device_combo.count()):
                    if self._device_combo.itemData(i) == detected_device:
                        self._device_combo.setCurrentIndex(i)
                        found = True
                        break

                if not found:
                    # Device not in list - refresh and try again
                    self._load_devices()
                    for i in range(self._device_combo.count()):
                        if self._device_combo.itemData(i) == detected_device:
                            self._device_combo.setCurrentIndex(i)
                            found = True
                            break

                if found:
                    QMessageBox.information(
                        self,
                        "Device Detected",
                        f"Successfully detected Device {detected_device}!\n\n"
                        "This device is now selected for key remapping."
                    )
                else:
                    QMessageBox.warning(
                        self,
                        "Device Not Found",
                        f"Device {detected_device} was detected but is not in the list.\n"
                        "Try clicking Refresh."
                    )

    def _add_mapping(self):
        """Open dialog to add a new mapping."""
        device = self._device_combo.currentData()

        if device is None:
            QMessageBox.warning(
                self,
                "No Device Selected",
                "Please select a target device first."
            )
            return

        dialog = CaptureDialog(device, self)
        if dialog.exec_() == CaptureDialog.Accepted:
            mapping = dialog.get_mapping()
            if mapping:
                input_vk, output_vk = mapping
                self._interceptor.add_mapping(input_vk, output_vk)
                self._update_mapping_list()
                self._save_config()

    def _remove_mapping(self):
        """Remove selected mapping."""
        current = self._mapping_list.currentItem()
        if not current:
            return

        input_vk = current.data(Qt.UserRole)
        if input_vk is not None:
            self._interceptor.remove_mapping(input_vk)
            self._update_mapping_list()
            self._save_config()

    def _clear_mappings(self):
        """Clear all mappings."""
        if self._interceptor._mappings:
            reply = QMessageBox.question(
                self,
                "Clear Mappings",
                "Are you sure you want to remove all key mappings?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self._interceptor.clear_mappings()
                self._update_mapping_list()
                self._save_config()

    def _update_mapping_list(self):
        """Update the mapping list widget."""
        self._mapping_list.clear()
        for input_vk, output_vk in self._interceptor._mappings.items():
            item = QListWidgetItem(
                f"{vk_to_name(input_vk)}  \u2192  {vk_to_name(output_vk)}"
            )
            item.setData(Qt.UserRole, input_vk)
            self._mapping_list.addItem(item)
        self._update_status()

    def closeEvent(self, event):
        """Handle close event - minimize to tray instead."""
        event.ignore()
        self.hide()
