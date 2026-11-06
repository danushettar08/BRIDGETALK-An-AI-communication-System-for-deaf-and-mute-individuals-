"""
BridgeTalk AI — Futuristic Live ISL Translation Page
----------------------------------------------------
Preserves the existing BridgeTalk service interfaces while providing
a premium dark/neon desktop UI inspired by modern AI products.

Core pipeline:
Camera -> MediaPipe/recognition -> English text -> Translation -> TTS
"""

from __future__ import annotations

from PySide6.QtCore import QThread, Qt, Signal, Slot
from PySide6.QtGui import QImage, QPixmap, QFont
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from services.camera_service import CameraService
from services.communication_service import CommunicationService
from services.tts_service import TTSService
from services.speech_service import SpeechService
from services.translation_service import TranslationService


# ==============================================================
# COLORS
# ==============================================================

BG = "#050712"
PANEL = "#080D1C"
PANEL_2 = "#0B1122"
BORDER = "#202B49"
BORDER_HOVER = "#38456B"
TEXT = "#F5F7FF"
MUTED = "#8D98B5"
PURPLE = "#8B5CF6"
BLUE = "#3B82F6"
CYAN = "#22D3EE"
GREEN = "#22C55E"
RED = "#EF4444"
ORANGE = "#F59E0B"


# ==============================================================
# CAMERA PREVIEW
# ==============================================================

class CameraPreview(QLabel):
    """Large responsive camera preview."""

    def __init__(self, parent=None):
        super().__init__(parent)

        self._last_image: QImage | None = None

        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumSize(420, 300)
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )
        self.setText("CAMERA READY\n\nStart the camera to begin")
        self.setStyleSheet(
            f"""
            QLabel {{
                background: #03050B;
                border: 1px solid {BORDER};
                border-radius: 18px;
                color: {MUTED};
                font-size: 15px;
                font-weight: 700;
            }}
            """
        )

    @Slot(QImage)
    def update_frame(self, image: QImage) -> None:
        if image.isNull():
            return

        self._last_image = image.copy()
        self._render()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._render()

    def _render(self) -> None:
        if self._last_image is None:
            return

        pixmap = QPixmap.fromImage(self._last_image)

        if pixmap.isNull():
            return

        scaled = pixmap.scaled(
            self.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )

        self.setPixmap(scaled)

    def clear_preview(self) -> None:
        self._last_image = None
        self.clear()
        self.setText("CAMERA READY\n\nStart the camera to begin")


# ==============================================================
# ASYNC WORKERS
# ==============================================================

class TranslationWorker(QThread):
    result_ready = Signal(object)

    def __init__(
        self,
        translation_service: TranslationService,
        text: str,
        parent=None,
    ):
        super().__init__(parent)
        self.translation_service = translation_service
        self.text = text

    def run(self) -> None:
        try:
            result = self.translation_service.translate(self.text)
            self.result_ready.emit(result)
        except Exception as exc:
            print("[Translation] Worker error:", repr(exc))
            self.result_ready.emit(None)


class SpeechWorker(QThread):
    result_ready = Signal(object)

    def __init__(
        self,
        speech_service: SpeechService,
        duration: int = 6,
        parent=None,
    ):
        super().__init__(parent)
        self.speech_service = speech_service
        self.duration = duration

    def run(self) -> None:
        try:
            result = self.speech_service.listen(duration=self.duration)
            self.result_ready.emit(result)
        except Exception as exc:
            print("[Speech] Worker error:", repr(exc))
            self.result_ready.emit(None)


# ==============================================================
# MAIN PAGE
# ==============================================================

class GesturePage(QWidget):
    """Premium BridgeTalk live ISL translation dashboard."""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.camera_service = CameraService()
        self.communication_service = CommunicationService()
        self.tts_service = TTSService()
        self.speech_service = SpeechService()
        self.translation_service = TranslationService("English")

        self.speech_worker = None
        self.translation_worker = None

        self.current_speech_text = ""
        self.current_translation = ""
        self.current_word = ""

        self._tts_voices = []

        self._build_ui()

    # ==========================================================
    # STYLE HELPERS
    # ==========================================================

    def _panel_style(self, accent=PURPLE) -> str:
        return f"""
        QFrame#Panel {{
            background: qlineargradient(
                x1:0, y1:0, x2:1, y2:1,
                stop:0 {PANEL},
                stop:1 {PANEL_2}
            );
            border: 1px solid {BORDER};
            border-radius: 18px;
        }}

        QFrame#Panel:hover {{
            border: 1px solid {accent};
        }}
        """

    def _button_style(self, accent=PURPLE) -> str:
        return f"""
        QPushButton {{
            background: qlineargradient(
                x1:0, y1:0, x2:1, y2:0,
                stop:0 {accent},
                stop:1 {BLUE}
            );
            color: white;
            border: none;
            border-radius: 10px;
            padding: 10px 18px;
            font-size: 13px;
            font-weight: 800;
        }}

        QPushButton:hover {{
            background: qlineargradient(
                x1:0, y1:0, x2:1, y2:0,
                stop:0 #A78BFA,
                stop:1 #60A5FA
            );
        }}

        QPushButton:pressed {{
            padding-top: 11px;
        }}

        QPushButton:disabled {{
            background: #151B2E;
            color: #58627C;
        }}
        """

    def _ghost_button_style(self) -> str:
        return f"""
        QPushButton {{
            background: #0A1020;
            color: {TEXT};
            border: 1px solid {BORDER};
            border-radius: 10px;
            padding: 9px 15px;
            font-size: 12px;
            font-weight: 700;
        }}

        QPushButton:hover {{
            border: 1px solid {PURPLE};
            background: #11172B;
        }}
        """

    def _danger_button_style(self) -> str:
        return f"""
        QPushButton {{
            background: #160B13;
            color: #FCA5A5;
            border: 1px solid #5B2330;
            border-radius: 10px;
            padding: 9px 15px;
            font-size: 12px;
            font-weight: 700;
        }}

        QPushButton:hover {{
            background: #2A0D18;
            border: 1px solid {RED};
        }}
        """

    def _title(self, text: str, size=16, color=TEXT) -> QLabel:
        label = QLabel(text)
        label.setStyleSheet(
            f"color: {color}; font-size: {size}px; font-weight: 850;"
        )
        return label

    def _muted(self, text: str, size=12) -> QLabel:
        label = QLabel(text)
        label.setStyleSheet(
            f"color: {MUTED}; font-size: {size}px;"
        )
        return label

    def _pill(self, text: str, color=GREEN) -> QLabel:
        label = QLabel(text)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet(
            f"""
            QLabel {{
                background: #071A17;
                color: {color};
                border: 1px solid {color};
                border-radius: 10px;
                padding: 7px 11px;
                font-size: 11px;
                font-weight: 850;
            }}
            """
        )
        return label

    def _panel(self, title: str, subtitle: str = "", accent=PURPLE):
        panel = QFrame()
        panel.setObjectName("Panel")
        panel.setStyleSheet(self._panel_style(accent))

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(10)

        header = QHBoxLayout()
        header.setSpacing(10)

        title_label = self._title(title, 14, accent)
        header.addWidget(title_label)
        header.addStretch()

        if subtitle:
            header.addWidget(self._muted(subtitle, 10))

        layout.addLayout(header)

        return panel, layout

    # ==========================================================
    # BUILD UI
    # ==========================================================

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        scroll.setStyleSheet(
            f"""
            QScrollArea {{
                background: {BG};
                border: none;
            }}

            QScrollBar:vertical {{
                width: 8px;
                background: {BG};
            }}

            QScrollBar::handle:vertical {{
                background: #283454;
                border-radius: 4px;
                min-height: 45px;
            }}
            """
        )

        content = QWidget()
        content.setStyleSheet(f"background: {BG};")

        main = QVBoxLayout(content)
        main.setContentsMargins(26, 22, 26, 26)
        main.setSpacing(16)

        scroll.setWidget(content)
        root.addWidget(scroll)

        # ------------------------------------------------------
        # TOP HEADER
        # ------------------------------------------------------

        header = QHBoxLayout()
        header.setSpacing(14)

        heading_box = QVBoxLayout()
        heading_box.setSpacing(2)

        heading = QLabel("Live ISL Translation")
        heading.setStyleSheet(
            f"""
            QLabel {{
                color: {TEXT};
                font-size: 28px;
                font-weight: 900;
            }}
            """
        )

        subheading = QLabel(
            "Real-time Indian Sign Language recognition and translation"
        )
        subheading.setStyleSheet(
            f"color: {MUTED}; font-size: 13px;"
        )

        heading_box.addWidget(heading)
        heading_box.addWidget(subheading)
        header.addLayout(heading_box)
        header.addStretch()

        self.live_pill = self._pill("● OFFLINE", RED)
        header.addWidget(self.live_pill)

        self.hands_pill = self._pill("♧ 0 HANDS", CYAN)
        self.hands_pill.setStyleSheet(
            f"""
            QLabel {{
                background: #08131C;
                color: {CYAN};
                border: 1px solid #174A5A;
                border-radius: 10px;
                padding: 7px 11px;
                font-size: 11px;
                font-weight: 850;
            }}
            """
        )
        header.addWidget(self.hands_pill)

        fps_pill = self._pill("●‰ 45 FPS", BLUE)
        fps_pill.setStyleSheet(
            f"""
            QLabel {{
                background: #09111F;
                color: {BLUE};
                border: 1px solid #234D86;
                border-radius: 10px;
                padding: 7px 11px;
                font-size: 11px;
                font-weight: 850;
            }}
            """
        )
        header.addWidget(fps_pill)

        model_pill = self._pill("MODEL: LSTM", PURPLE)
        model_pill.setStyleSheet(
            f"""
            QLabel {{
                background: #120B20;
                color: #C4B5FD;
                border: 1px solid #4C2B77;
                border-radius: 10px;
                padding: 7px 11px;
                font-size: 11px;
                font-weight: 850;
            }}
            """
        )
        header.addWidget(model_pill)

        main.addLayout(header)

        # ------------------------------------------------------
        # HERO ROW
        # ------------------------------------------------------

        hero = QGridLayout()
        hero.setHorizontalSpacing(16)
        hero.setVerticalSpacing(16)

        # Camera panel
        camera_panel, camera_layout = self._panel(
            "▣  LIVE SIGN CAPTURE",
            accent=PURPLE,
        )

        camera_header = camera_layout.itemAt(0).layout()

        self.start_button = QPushButton("START CAMERA")
        self.start_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )
        self.start_button.setMinimumHeight(38)
        self.start_button.setStyleSheet(
            self._button_style(PURPLE)
        )
        self.start_button.clicked.connect(self.toggle_camera)
        camera_header.addWidget(self.start_button)

        self.camera_preview = CameraPreview()
        camera_layout.addWidget(self.camera_preview, 1)

        camera_bottom = QHBoxLayout()
        camera_bottom.setSpacing(8)

        self.camera_status_chip = self._pill(
            "● CAMERA READY",
            MUTED,
        )
        camera_bottom.addWidget(self.camera_status_chip)

        self.hand_tracking_chip = self._pill(
            "HAND TRACKING STANDBY",
            MUTED,
        )
        camera_bottom.addWidget(self.hand_tracking_chip)

        self.hand_side_chip = self._pill(
            "NO HAND",
            MUTED,
        )
        camera_bottom.addWidget(self.hand_side_chip)

        camera_layout.addLayout(camera_bottom)

        # Recognition panel
        recognition_panel, recognition_layout = self._panel(
            "✦  AI RECOGNITION",
            "LIVE MODEL OUTPUT",
            PURPLE,
        )

        # Signal line / status
        self.signal_label = QLabel(
            "────────────────────────────────────────"
        )
        self.signal_label.setStyleSheet(
            f"color: #473D7A; font-size: 10px;"
        )
        recognition_layout.addWidget(self.signal_label)

        recog_label = self._muted("RECOGNIZED SIGN", 10)
        recognition_layout.addWidget(recog_label)

        self.gesture_result = QLabel("READY")
        self.gesture_result.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )
        self.gesture_result.setMinimumHeight(85)
        self.gesture_result.setStyleSheet(
            f"""
            QLabel {{
                color: #A78BFA;
                font-size: 32px;
                font-weight: 950;
                letter-spacing: 1px;
                background: transparent;
            }}
            """
        )
        recognition_layout.addWidget(self.gesture_result)

        self.confidence_value = QLabel("0.0%")
        self.confidence_value.setStyleSheet(
            f"""
            QLabel {{
                color: {GREEN};
                font-size: 30px;
                font-weight: 900;
            }}
            """
        )

        confidence_header = QHBoxLayout()
        confidence_header.addWidget(
            self._muted("CONFIDENCE SCORE", 10)
        )
        confidence_header.addStretch()
        confidence_header.addWidget(self.confidence_value)
        recognition_layout.addLayout(confidence_header)

        self.confidence_bar = QProgressBar()
        self.confidence_bar.setRange(0, 100)
        self.confidence_bar.setValue(0)
        self.confidence_bar.setTextVisible(False)
        self.confidence_bar.setFixedHeight(8)
        self.confidence_bar.setStyleSheet(
            f"""
            QProgressBar {{
                background: #151C31;
                border: none;
                border-radius: 4px;
            }}

            QProgressBar::chunk {{
                border-radius: 4px;
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 {PURPLE},
                    stop:0.55 {BLUE},
                    stop:1 {CYAN}
                );
            }}
            """
        )
        recognition_layout.addWidget(self.confidence_bar)

        self.confidence_status = QLabel("● Waiting for a sign")
        self.confidence_status.setStyleSheet(
            f"color: {MUTED}; font-size: 11px; font-weight: 700;"
        )
        recognition_layout.addWidget(self.confidence_status)

        recognition_layout.addStretch()

        # Detected hand row
        detected = QHBoxLayout()
        detected.setSpacing(8)

        self.detected_hands_chip = self._pill(
            "♧ 0 HANDS DETECTED",
            PURPLE,
        )
        detected.addWidget(self.detected_hands_chip)

        self.left_chip = self._pill(
            "LEFT: —",
            GREEN,
        )
        detected.addWidget(self.left_chip)

        self.right_chip = self._pill(
            "RIGHT: —",
            BLUE,
        )
        detected.addWidget(self.right_chip)

        recognition_layout.addLayout(detected)

        hero.addWidget(camera_panel, 0, 0)
        hero.addWidget(recognition_panel, 0, 1)

        hero.setColumnStretch(0, 3)
        hero.setColumnStretch(1, 2)

        main.addLayout(hero)

        # ------------------------------------------------------
        # LOWER ROW
        # ------------------------------------------------------

        lower = QGridLayout()
        lower.setHorizontalSpacing(16)
        lower.setVerticalSpacing(16)

        # Communication
        communication_panel, communication_layout = self._panel(
            "▱  COMMUNICATION",
            "LIVE SENTENCE",
            PURPLE,
        )

        current_row = QHBoxLayout()
        current_row.addWidget(
            self._muted("CURRENT SENTENCE", 10)
        )
        current_row.addStretch()

        self.word_count_label = QLabel("WORD COUNT 0")
        self.word_count_label.setStyleSheet(
            f"""
            color: {MUTED};
            font-size: 10px;
            font-weight: 800;
            """
        )
        current_row.addWidget(self.word_count_label)
        communication_layout.addLayout(current_row)

        self.sentence_label = QLabel(
            "Your communication sentence will appear here..."
        )
        self.sentence_label.setWordWrap(True)
        self.sentence_label.setAlignment(
            Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft
        )
        self.sentence_label.setMinimumHeight(94)
        self.sentence_label.setStyleSheet(
            f"""
            QLabel {{
                background: #050914;
                border: 1px solid {BORDER};
                border-radius: 12px;
                color: {TEXT};
                font-size: 17px;
                font-weight: 650;
                padding: 14px;
            }}
            """
        )
        communication_layout.addWidget(self.sentence_label)

        communication_buttons = QHBoxLayout()
        communication_buttons.setSpacing(8)

        self.add_word_button = QPushButton("+  ADD WORD")
        self.add_word_button.setEnabled(False)
        self.add_word_button.setStyleSheet(
            self._button_style(PURPLE)
        )
        self.add_word_button.clicked.connect(
            self.add_current_word
        )
        communication_buttons.addWidget(
            self.add_word_button
        )

        self.backspace_button = QPushButton("⌫  BACKSPACE")
        self.backspace_button.setStyleSheet(
            self._ghost_button_style()
        )
        self.backspace_button.clicked.connect(
            self.remove_last_word
        )
        communication_buttons.addWidget(
            self.backspace_button
        )

        self.clear_button = QPushButton("CLEAR")
        self.clear_button.setStyleSheet(
            self._danger_button_style()
        )
        self.clear_button.clicked.connect(
            self.clear_sentence
        )
        communication_buttons.addWidget(
            self.clear_button
        )

        communication_layout.addLayout(communication_buttons)

        # Translation
        translation_panel, translation_layout = self._panel(
            "⇄  TRANSLATION",
            "LANGUAGE CONVERSION",
            GREEN,
        )

        language_row = QHBoxLayout()
        language_row.setSpacing(8)

        self.target_language_combo = QComboBox()
        self.target_language_combo.setMinimumHeight(38)
        self.target_language_combo.addItems(
            list(TranslationService.LANGUAGES.keys())
        )
        self.target_language_combo.setCurrentText("English")
        self.target_language_combo.currentTextChanged.connect(
            self._translation_language_changed
        )
        language_row.addWidget(self.target_language_combo, 1)

        swap = QLabel("⇄")
        swap.setAlignment(Qt.AlignmentFlag.AlignCenter)
        swap.setStyleSheet(
            f"""
            color: {CYAN};
            background: #07131A;
            border: 1px solid #17404D;
            border-radius: 9px;
            font-size: 17px;
            font-weight: 900;
            padding: 7px;
            """
        )
        language_row.addWidget(swap)

        self.translation_from = QLabel("English")
        self.translation_from.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )
        self.translation_from.setStyleSheet(
            f"""
            color: {TEXT};
            background: #0A1020;
            border: 1px solid {BORDER};
            border-radius: 9px;
            padding: 9px;
            font-weight: 700;
            """
        )
        language_row.insertWidget(0, self.translation_from, 1)

        translation_layout.addLayout(language_row)

        translation_layout.addWidget(
            self._muted("TRANSLATED TEXT", 10)
        )

        self.translation_result_label = QLabel(
            "Translated text will appear here..."
        )
        self.translation_result_label.setWordWrap(True)
        self.translation_result_label.setMinimumHeight(82)
        self.translation_result_label.setStyleSheet(
            f"""
            QLabel {{
                background: #06130F;
                border: 1px solid #174B38;
                border-radius: 12px;
                color: #4ADE80;
                font-size: 20px;
                font-weight: 800;
                padding: 12px;
            }}
            """
        )
        translation_layout.addWidget(
            self.translation_result_label
        )

        translation_buttons = QHBoxLayout()
        translation_buttons.setSpacing(8)

        self.translate_button = QPushButton("⇄  TRANSLATE")
        self.translate_button.setEnabled(False)
        self.translate_button.setStyleSheet(
            self._button_style(GREEN)
        )
        self.translate_button.clicked.connect(
            self.translate_sentence
        )
        translation_buttons.addWidget(
            self.translate_button
        )

        self.speak_translation_button = QPushButton(
            "🔊  SPEAK"
        )
        self.speak_translation_button.setEnabled(False)
        self.speak_translation_button.setStyleSheet(
            self._ghost_button_style()
        )
        self.speak_translation_button.clicked.connect(
            self.speak_translation
        )
        translation_buttons.addWidget(
            self.speak_translation_button
        )

        translation_layout.addLayout(
            translation_buttons
        )

        # Voice panel
        voice_panel, voice_layout = self._panel(
            "â™©  VOICE",
            "SPEECH INPUT / OUTPUT",
            CYAN,
        )

        voice_layout.addWidget(
            self._muted("SPEECH TO TEXT", 10)
        )

        speech_row = QHBoxLayout()
        speech_row.setSpacing(8)

        self.speech_result_label = QLabel(
            "Click listen to speak..."
        )
        self.speech_result_label.setWordWrap(True)
        self.speech_result_label.setMinimumHeight(58)
        self.speech_result_label.setStyleSheet(
            f"""
            QLabel {{
                background: #050914;
                border: 1px solid {BORDER};
                border-radius: 10px;
                color: {MUTED};
                padding: 10px;
            }}
            """
        )
        speech_row.addWidget(
            self.speech_result_label,
            1,
        )

        self.listen_button = QPushButton("●")
        self.listen_button.setToolTip("Start speech recognition")
        self.listen_button.setFixedSize(54, 54)
        self.listen_button.setStyleSheet(
            self._button_style(PURPLE)
        )
        self.listen_button.clicked.connect(
            self.start_speech_recognition
        )
        speech_row.addWidget(
            self.listen_button
        )

        voice_layout.addLayout(speech_row)

        self.add_speech_button = QPushButton(
            "+ ADD SPEECH TO SENTENCE"
        )
        self.add_speech_button.setEnabled(False)
        self.add_speech_button.setStyleSheet(
            self._ghost_button_style()
        )
        self.add_speech_button.clicked.connect(
            self.add_speech_to_sentence
        )
        voice_layout.addWidget(
            self.add_speech_button
        )

        voice_layout.addWidget(
            self._muted("TEXT TO SPEECH", 10)
        )

        self.voice_combo = QComboBox()
        self.voice_combo.setMinimumHeight(36)
        voice_layout.addWidget(self.voice_combo)

        voice_buttons = QHBoxLayout()
        voice_buttons.setSpacing(8)

        self.test_voice_button = QPushButton("TEST VOICE")
        self.test_voice_button.setStyleSheet(
            self._ghost_button_style()
        )
        self.test_voice_button.clicked.connect(
            self.test_selected_voice
        )
        voice_buttons.addWidget(
            self.test_voice_button
        )

        self.voice_speak_button = QPushButton("🔊 SPEAK")
        self.voice_speak_button.setEnabled(False)
        self.voice_speak_button.setStyleSheet(
            self._button_style(BLUE)
        )
        self.voice_speak_button.clicked.connect(
            self.speak_sentence
        )
        voice_buttons.addWidget(
            self.voice_speak_button
        )

        voice_layout.addLayout(voice_buttons)

        lower.addWidget(communication_panel, 0, 0)
        lower.addWidget(translation_panel, 0, 1)
        lower.addWidget(voice_panel, 0, 2)

        lower.setColumnStretch(0, 3)
        lower.setColumnStretch(1, 3)
        lower.setColumnStretch(2, 2)

        main.addLayout(lower)

        # ------------------------------------------------------
        # FOOTER STATUS
        # ------------------------------------------------------

        footer = QFrame()
        footer.setStyleSheet(
            f"""
            QFrame {{
                background: #070B16;
                border: 1px solid {BORDER};
                border-radius: 12px;
            }}
            """
        )

        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(14, 8, 14, 8)

        self.tracking_status = QLabel(
            "● Ready to detect signs..."
        )
        self.tracking_status.setStyleSheet(
            f"color: {GREEN}; font-size: 11px; font-weight: 750;"
        )
        footer_layout.addWidget(self.tracking_status)

        footer_layout.addStretch()

        footer_layout.addWidget(
            self._muted("BridgeTalk AI  •  v1.0.0", 10)
        )

        footer_layout.addStretch()

        performance = QLabel(
            "● High Performance Mode   ●‰ GPU Ready"
        )
        performance.setStyleSheet(
            f"color: {CYAN}; font-size: 10px; font-weight: 750;"
        )
        footer_layout.addWidget(performance)

        main.addWidget(footer)

        # ------------------------------------------------------
        # Hidden compatibility combo
        # ------------------------------------------------------

        self.camera_combo = QComboBox(self)
        self.camera_combo.hide()

        self._load_tts_voices()
        self.voice_combo.currentIndexChanged.connect(
            self._voice_changed
        )

        self._load_cameras()

    # ==========================================================
    # COPY
    # ==========================================================

    def copy_sentence(self) -> None:
        sentence = (
            self.communication_service.get_sentence().strip()
        )

        if not sentence:
            return

        clipboard = QApplication.clipboard()
        if clipboard is not None:
            clipboard.setText(sentence)

        self.tracking_status.setText(
            "● Sentence copied"
        )

    # ==========================================================
    # CAMERAS
    # ==========================================================

    def _load_cameras(self) -> None:
        self.camera_combo.clear()

        cameras = self.camera_service.available_cameras()

        if not cameras:
            self.camera_combo.addItem(
                "No camera detected",
                -1,
            )
            self.start_button.setEnabled(False)
            return

        for index in cameras:
            self.camera_combo.addItem(
                f"Camera {index + 1}",
                index,
            )

    def toggle_camera(self) -> None:
        if self.camera_service.is_running():
            self.stop_camera()
        else:
            self.start_camera()

    def start_camera(self) -> None:
        camera_index = self.camera_combo.currentData()

        if camera_index is None or camera_index < 0:
            return

        self.camera_service.start(int(camera_index))

        thread = self.camera_service.thread

        if thread is None:
            return

        # Avoid duplicate signal connections where possible.
        try:
            thread.frame_ready.connect(
                self.camera_preview.update_frame
            )
            thread.hand_count_changed.connect(
                self.update_hand_count
            )
            thread.handedness_changed.connect(
                self.update_handedness
            )
            thread.gesture_changed.connect(
                self.update_gesture
            )
            thread.gesture_text_changed.connect(
                self.update_communication_text
            )
            thread.camera_started.connect(
                self._camera_started
            )
            thread.camera_stopped.connect(
                self._camera_stopped
            )
            thread.camera_error.connect(
                self._camera_error
            )
            thread.tracking_error.connect(
                self._tracking_error
            )
        except Exception as exc:
            print("[BridgeTalk] Signal connection error:", exc)

    def stop_camera(self) -> None:
        self.camera_service.stop()
        self.camera_preview.clear_preview()

        self.start_button.setText("START CAMERA")
        self.live_pill.setText("● OFFLINE")
        self.live_pill.setStyleSheet(
            f"""
            QLabel {{
                background: #1A0A10;
                color: {RED};
                border: 1px solid #5B2330;
                border-radius: 10px;
                padding: 7px 11px;
                font-size: 11px;
                font-weight: 850;
            }}
            """
        )

        self.camera_status_chip.setText("● CAMERA READY")
        self.hand_tracking_chip.setText("HAND TRACKING STANDBY")
        self.hand_side_chip.setText("NO HAND")

        self.tracking_status.setText(
            "● Ready to detect signs..."
        )

        self.update_hand_count(0)
        self.update_handedness("No hand detected")
        self.gesture_result.setText("READY")
        self.confidence_value.setText("0.0%")
        self.confidence_bar.setValue(0)
        self.confidence_status.setText(
            "● Waiting for a sign"
        )
        self.gesture_result.setText(
            "Waiting for a gesture..."
        )

    # ==========================================================
    # HAND COUNT
    # ==========================================================

    @Slot(int)
    def update_hand_count(self, count: int) -> None:
        self.hand_count_value = count

        self.hands_pill.setText(
            f"♧ {count} HANDS"
        )
        self.detected_hands_chip.setText(
            f"♧ {count} HANDS DETECTED"
        )

        if count == 0:
            color = MUTED
        else:
            color = PURPLE

        self.detected_hands_chip.setStyleSheet(
            f"""
            QLabel {{
                background: #100B1D;
                color: {color};
                border: 1px solid {color};
                border-radius: 10px;
                padding: 7px 11px;
                font-size: 11px;
                font-weight: 850;
            }}
            """
        )

    # ==========================================================
    # HANDEDNESS
    # ==========================================================

    @Slot(str)
    def update_handedness(self, value: str) -> None:
        self.hand_side_chip.setText(
            value.upper()
        )

        lowered = value.lower()

        if "left" in lowered:
            self.left_chip.setText("LEFT: DETECTED")
        else:
            self.left_chip.setText("LEFT: —")

        if "right" in lowered:
            self.right_chip.setText("RIGHT: DETECTED")
        else:
            self.right_chip.setText("RIGHT: —")

    # ==========================================================
    # GESTURE
    # ==========================================================

    @Slot(str, float)
    def update_gesture(
        self,
        gesture: str,
        score: float,
    ) -> None:
        if not gesture or gesture == "None":
            self.gesture_result.setText("READY")
            self.confidence_value.setText("0.0%")
            self.confidence_bar.setValue(0)
            self.confidence_status.setText(
                "● Waiting for a sign"
            )
            return

        gesture_names = {
            "Open_Palm": "OPEN PALM",
            "Closed_Fist": "CLOSED FIST",
            "Pointing_Up": "POINTING UP",
            "Thumb_Up": "THUMBS UP",
            "Thumb_Down": "THUMBS DOWN",
            "Victory": "VICTORY",
            "ILoveYou": "I LOVE YOU",
        }

        display_name = gesture_names.get(
            gesture,
            gesture.replace("_", " ").upper(),
        )

        confidence = max(
            0.0,
            min(1.0, float(score)),
        ) * 100.0

        self.gesture_result.setText(display_name)
        self.confidence_value.setText(
            f"{confidence:.1f}%"
        )
        self.confidence_bar.setValue(
            int(confidence)
        )

        if confidence >= 80:
            status = "● High confidence"
            color = GREEN
        elif confidence >= 50:
            status = "● Medium confidence"
            color = ORANGE
        else:
            status = "● Low confidence"
            color = RED

        self.confidence_status.setText(status)
        self.confidence_status.setStyleSheet(
            f"color: {color}; font-size: 11px; font-weight: 750;"
        )

        self.tracking_status.setText(
            "● Gesture recognized"
        )

    # ==========================================================
    # CURRENT WORD
    # ==========================================================

    @Slot(str)
    def update_communication_text(
        self,
        text: str,
    ) -> None:
        self.current_word = text.strip()

        if not self.current_word:
            self.gesture_result.setText(
                "Waiting for a gesture..."
            )
            self.add_word_button.setEnabled(False)
            return

        self.gesture_result.setText(
            self.current_word
        )
        self.add_word_button.setEnabled(True)

        # Keep the large recognition panel synchronized.
        self.gesture_result.setText(
            self.current_word.upper()
        )

    # ==========================================================
    # ADD WORD
    # ==========================================================

    def add_current_word(self) -> None:
        if not self.current_word:
            return

        sentence = (
            self.communication_service.add_if_new(
                self.current_word
            )
        )

        self._update_sentence(sentence)

    # ==========================================================
    # SENTENCE
    # ==========================================================

    def remove_last_word(self) -> None:
        sentence = (
            self.communication_service.remove_last()
        )
        self._update_sentence(sentence)

    def clear_sentence(self) -> None:
        sentence = (
            self.communication_service.clear()
        )
        self._update_sentence(sentence)

    def _update_sentence(
        self,
        sentence: str,
    ) -> None:
        sentence = sentence or ""

        if not sentence.strip():
            self.sentence_label.setText(
                "Your communication sentence will appear here..."
            )
            self.word_count_label.setText(
                "WORD COUNT 0"
            )

            self.voice_speak_button.setEnabled(False)
            self.voice_speak_button.setEnabled(False)
            self.translate_button.setEnabled(False)
            self.speak_translation_button.setEnabled(False)

            return

        self.sentence_label.setText(sentence)

        word_count = len(sentence.split())
        self.word_count_label.setText(
            f"WORD COUNT {word_count}"
        )

        self.voice_speak_button.setEnabled(True)
        self.voice_speak_button.setEnabled(True)
        self.translate_button.setEnabled(True)

    # ==========================================================
    # SPEAK SENTENCE
    # ==========================================================

    def speak_sentence(self) -> None:
        sentence = (
            self.communication_service.get_sentence().strip()
        )

        if not sentence:
            return

        print("[BridgeTalk] Speaking:", sentence)

        success = self.tts_service.speak(sentence)

        if success:
            self.tracking_status.setText(
                "● Speaking sentence..."
            )

    # ==========================================================
    # SPEECH INPUT
    # ==========================================================

    def start_speech_recognition(self) -> None:
        if (
            self.speech_worker is not None
            and self.speech_worker.isRunning()
        ):
            return

        self.current_speech_text = ""
        self.add_speech_button.setEnabled(False)
        self.listen_button.setEnabled(False)
        self.listen_button.setText("...")
        self.speech_result_label.setText(
            "Listening... speak clearly for a few seconds."
        )
        self.tracking_status.setText(
            "● Listening..."
        )

        self.speech_worker = SpeechWorker(
            self.speech_service,
            duration=6,
            parent=self,
        )

        self.speech_worker.result_ready.connect(
            self._speech_result_ready
        )
        self.speech_worker.finished.connect(
            self._speech_finished
        )
        self.speech_worker.start()

    @Slot(object)
    def _speech_result_ready(self, result) -> None:
        if result:
            self.current_speech_text = str(result).strip()
            self.speech_result_label.setText(
                self.current_speech_text
            )
            self.add_speech_button.setEnabled(True)
            self.tracking_status.setText(
                "● Speech recognized"
            )
        else:
            self.current_speech_text = ""
            self.speech_result_label.setText(
                "Speech could not be understood. Please try again."
            )
            self.add_speech_button.setEnabled(False)
            self.tracking_status.setText(
                "● Speech not recognized"
            )

    @Slot()
    def _speech_finished(self) -> None:
        self.listen_button.setEnabled(True)
        self.listen_button.setText("●")

        if not self.current_speech_text:
            self.tracking_status.setText(
                "● Ready to detect signs..."
            )

    def add_speech_to_sentence(self) -> None:
        text = self.current_speech_text.strip()

        if not text:
            return

        sentence = (
            self.communication_service.add_if_new(text)
        )

        self._update_sentence(sentence)
        self.add_speech_button.setEnabled(False)
        self.tracking_status.setText(
            "● Speech added"
        )

    # ==========================================================
    # TRANSLATION
    # ==========================================================

    def _translation_language_changed(
        self,
        language: str,
    ) -> None:
        try:
            self.translation_service.set_target_language(
                language
            )

            self.current_translation = ""
            self.translation_result_label.setText(
                "Translated text will appear here..."
            )
            self.speak_translation_button.setEnabled(False)

            sentence = (
                self.communication_service.get_sentence().strip()
            )

            self.translate_button.setEnabled(
                bool(sentence)
            )

            self.tracking_status.setText(
                f"● Target: {language}"
            )

        except Exception as exc:
            print(
                "[Translation] Language error:",
                repr(exc),
            )

    def translate_sentence(self) -> None:
        sentence = (
            self.communication_service.get_sentence().strip()
        )

        if not sentence:
            self.translation_result_label.setText(
                "Add a sentence before translating."
            )
            return

        self.translate_button.setEnabled(False)
        self.speak_translation_button.setEnabled(False)

        language = (
            self.translation_service.get_target_language()
        )

        self.translation_result_label.setText(
            f"Translating to {language}..."
        )
        self.tracking_status.setText(
            "● Translating..."
        )

        self.translation_worker = TranslationWorker(
            self.translation_service,
            sentence,
            parent=self,
        )

        self.translation_worker.result_ready.connect(
            self._translation_result_ready
        )
        self.translation_worker.finished.connect(
            self._translation_finished
        )
        self.translation_worker.start()

    @Slot(object)
    def _translation_result_ready(self, result) -> None:
        if result:
            self.current_translation = str(result).strip()
            self.translation_result_label.setText(
                self.current_translation
            )
            self.speak_translation_button.setEnabled(True)
            self.tracking_status.setText(
                "● Translation ready"
            )
        else:
            self.current_translation = ""
            self.translation_result_label.setText(
                "Translation failed. Check your internet connection."
            )
            self.speak_translation_button.setEnabled(False)
            self.tracking_status.setText(
                "● Translation failed"
            )

    @Slot()
    def _translation_finished(self) -> None:
        sentence = (
            self.communication_service.get_sentence().strip()
        )
        self.translate_button.setEnabled(
            bool(sentence)
        )

    def speak_translation(self) -> None:
        text = self.current_translation.strip()

        if not text:
            return

        print(
            "[BridgeTalk] Speaking translation:",
            text,
        )

        success = self.tts_service.speak(text)

        if success:
            self.tracking_status.setText(
                "● Speaking translation..."
            )

    # ==========================================================
    # TTS
    # ==========================================================

    def _load_tts_voices(self) -> None:
        self.voice_combo.clear()

        try:
            self._tts_voices = self.tts_service.get_voices()
        except Exception as exc:
            print("[TTS] Could not load voices:", exc)
            self._tts_voices = []

        if not self._tts_voices:
            self.voice_combo.addItem(
                "No voices detected"
            )
            self.test_voice_button.setEnabled(False)
            return

        self.test_voice_button.setEnabled(True)

        for voice in self._tts_voices:
            self.voice_combo.addItem(
                voice["name"],
                voice["index"],
            )

        selected_position = 0

        for position, voice in enumerate(
            self._tts_voices
        ):
            if "zira" in voice["name"].lower():
                selected_position = position
                break

        self.voice_combo.setCurrentIndex(
            selected_position
        )

        voice_index = self.voice_combo.itemData(
            selected_position
        )

        if voice_index is not None:
            self.tts_service.set_voice(
                int(voice_index)
            )

    def _voice_changed(self, index: int) -> None:
        if index < 0:
            return

        voice_index = self.voice_combo.itemData(index)

        if voice_index is None:
            return

        if self.tts_service.set_voice(int(voice_index)):
            self.tracking_status.setText(
                f"● Voice: {self.voice_combo.currentText()}"
            )

    def test_selected_voice(self) -> None:
        index = self.voice_combo.currentIndex()

        if index < 0:
            return

        voice_index = self.voice_combo.itemData(index)

        if voice_index is None:
            return

        if self.tts_service.set_voice(int(voice_index)):
            self.tts_service.test_voice(int(voice_index))

    # ==========================================================
    # CAMERA SIGNALS
    # ==========================================================

    @Slot()
    def _camera_started(self) -> None:
        self.start_button.setText("STOP CAMERA")

        self.live_pill.setText("● LIVE")
        self.live_pill.setStyleSheet(
            f"""
            QLabel {{
                background: #071A17;
                color: {GREEN};
                border: 1px solid {GREEN};
                border-radius: 10px;
                padding: 7px 11px;
                font-size: 11px;
                font-weight: 850;
            }}
            """
        )

        self.camera_status_chip.setText(
            "● CAMERA LIVE"
        )
        self.hand_tracking_chip.setText(
            "HAND TRACKING ACTIVE"
        )
        self.tracking_status.setText(
            "● Ready to detect signs..."
        )

    @Slot()
    def _camera_stopped(self) -> None:
        self.start_button.setText(
            "START CAMERA"
        )
        self.live_pill.setText(
            "● OFFLINE"
        )
        self.camera_status_chip.setText(
            "● CAMERA READY"
        )
        self.hand_tracking_chip.setText(
            "HAND TRACKING STANDBY"
        )
        self.tracking_status.setText(
            "● Ready to detect signs..."
        )

    @Slot(str)
    def _camera_error(self, message: str) -> None:
        self.live_pill.setText(
            "● CAMERA ERROR"
        )
        self.camera_status_chip.setText(
            "● CAMERA ERROR"
        )
        self.tracking_status.setText(
            "● Camera error"
        )
        print(f"Camera error:\n{message}")

    @Slot(str)
    def _tracking_error(self, message: str) -> None:
        self.hand_tracking_chip.setText(
            "TRACKING ERROR"
        )
        self.tracking_status.setText(
            "● Tracking error"
        )
        print(f"MediaPipe error:\n{message}")

    # ==========================================================
    # CLEANUP
    # ==========================================================

    def close_camera(self) -> None:
        try:
            self.camera_service.stop()
        except Exception:
            pass

        try:
            self.tts_service.close()
        except Exception:
            pass

    def closeEvent(self, event) -> None:
        self.close_camera()
        super().closeEvent(event)