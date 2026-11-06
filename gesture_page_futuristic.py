"""BridgeTalk Gesture-to-Text Page.

Features:
    - Live camera
    - 21 orange hand landmarks
    - Hand count
    - Left / Right hand
    - Current gesture
    - Confidence
    - Gesture â†’ Text
    - Add word to communication
    - Backspace
    - Clear sentence
    - Text â†’ Speech
    - Speech â†’ Text
"""

from __future__ import annotations

from PySide6.QtCore import QThread, Qt, Signal, Slot
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from services.camera_service import CameraService
from services.communication_service import (
    CommunicationService,
)
from services.tts_service import TTSService
from services.speech_service import SpeechService
from services.translation_service import TranslationService


class CameraPreview(QLabel):
    """Live camera preview."""

    def __init__(
        self,
        parent=None,
    ):
        super().__init__(parent)

        self.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        # Futuristic live-preview default size.
        self.setFixedSize(
            590,
            355,
        )

        self.setSizePolicy(
            QSizePolicy.Policy.Fixed,
            QSizePolicy.Policy.Fixed,
        )

        self.setText(
            "Camera Ready\n\n"
            "Press Start Camera"
        )

        self.setStyleSheet(
            """
            QLabel {
                background-color: #050A14;
                border: 1px solid #263449;
                border-radius: 16px;
                color: #64748B;
                font-size: 13px;
                font-weight: 600;
            }
            """
        )

    @Slot(QImage)
    def update_frame(
        self,
        image: QImage,
    ) -> None:
        """Display camera frame."""

        pixmap = QPixmap.fromImage(
            image
        )

        if pixmap.isNull():
            return

        scaled = pixmap.scaled(
            self.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )

        self.setPixmap(
            scaled
        )

    def clear_preview(self) -> None:
        """Clear preview."""

        self.clear()

        self.setText(
            "Camera Ready\n\n"
            "Press Start Camera"
        )



class TranslationWorker(QThread):
    """Run network translation without freezing the UI."""

    result_ready = Signal(object)

    def __init__(
        self,
        translation_service: TranslationService,
        text: str,
        parent=None,
    ):
        super().__init__(parent)

        self.translation_service = (
            translation_service
        )

        self.text = text

    def run(self) -> None:
        """Translate the supplied text."""

        try:

            result = (
                self.translation_service.translate(
                    self.text
                )
            )

            self.result_ready.emit(
                result
            )

        except Exception as exc:

            print(
                "[Translation] Worker error:",
                repr(exc),
            )

            self.result_ready.emit(
                None
            )


class SpeechWorker(QThread):
    """Run speech recognition without freezing the UI."""

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
        """Record and recognize speech."""

        try:
            result = self.speech_service.listen(
                duration=self.duration
            )

            self.result_ready.emit(
                result
            )

        except Exception as exc:

            print(
                "[Speech] Worker error:",
                repr(exc),
            )

            self.result_ready.emit(
                None
            )


class GesturePage(QWidget):
    """BridgeTalk Gesture-to-Text page."""

    def __init__(
        self,
        parent=None,
    ):
        super().__init__(parent)

        # ======================================================
        # SERVICES
        # ======================================================

        self.camera_service = (
            CameraService()
        )

        self.communication_service = (
            CommunicationService()
        )

        self.tts_service = (
            TTSService()
        )

        self.speech_service = (
            SpeechService()
        )

        self.translation_service = (
            TranslationService("English")
        )

        self.speech_worker = None
        self.current_speech_text = ""
        self.current_translation = ""

        self._tts_voices = []
        # ======================================================
        # CURRENT WORD
        # ======================================================

        self.current_word = ""

        self._build_ui()

    # ==========================================================
    # BUILD UI
    # ==========================================================

    def _build_ui(self) -> None:
        """Build the futuristic BridgeTalk live translation experience."""

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        scroll.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        scroll.setStyleSheet("""
            QScrollArea {
                background: #050812;
                border: none;
            }
            QScrollBar:vertical {
                width: 8px;
                background: #050812;
                border: none;
            }
            QScrollBar::handle:vertical {
                background: #24314A;
                border-radius: 4px;
                min-height: 48px;
            }
            QScrollBar::handle:vertical:hover {
                background: #3B82F6;
            }
        """)

        content = QWidget()
        content.setStyleSheet("background: #050812;")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(28, 24, 28, 34)
        layout.setSpacing(18)
        scroll.setWidget(content)
        outer.addWidget(scroll)

        # ----------------------------------------------------------
        # DESIGN SYSTEM
        # ----------------------------------------------------------

        title_style = """
            QLabel {
                color: #F8FAFC;
                font-size: 28px;
                font-weight: 800;
                background: transparent;
            }
        """

        subtitle_style = """
            QLabel {
                color: #71809A;
                font-size: 12px;
                font-weight: 600;
                background: transparent;
            }
        """

        section_style = """
            QLabel {
                color: #E8EEF9;
                font-size: 11px;
                font-weight: 800;
                letter-spacing: 1px;
                background: transparent;
            }
        """

        card_style = """
            QFrame {
                background: #0A1020;
                border: 1px solid #18243A;
                border-radius: 22px;
            }
        """

        inner_style = """
            QFrame {
                background: #080E1B;
                border: 1px solid #18243A;
                border-radius: 16px;
            }
        """

        primary_style = """
            QPushButton {
                background: #2563EB;
                color: #FFFFFF;
                border: 1px solid #3B82F6;
                border-radius: 11px;
                padding: 11px 18px;
                font-size: 12px;
                font-weight: 800;
            }
            QPushButton:hover {
                background: #3B82F6;
            }
            QPushButton:pressed {
                background: #1D4ED8;
            }
            QPushButton:disabled {
                background: #111A2B;
                border-color: #1A263B;
                color: #526079;
            }
        """

        secondary_style = """
            QPushButton {
                background: #0D1628;
                color: #C9D5E8;
                border: 1px solid #233552;
                border-radius: 11px;
                padding: 10px 16px;
                font-size: 12px;
                font-weight: 750;
            }
            QPushButton:hover {
                background: #13213A;
                border-color: #31527F;
                color: #FFFFFF;
            }
            QPushButton:disabled {
                color: #526079;
                background: #0A1020;
            }
        """

        success_style = """
            QPushButton {
                background: #0B2B27;
                color: #5EEAD4;
                border: 1px solid #115E59;
                border-radius: 11px;
                padding: 10px 16px;
                font-size: 12px;
                font-weight: 800;
            }
            QPushButton:hover {
                background: #0E3A35;
            }
        """

        danger_style = """
            QPushButton {
                background: #2A1118;
                color: #FB7185;
                border: 1px solid #5F1D2B;
                border-radius: 11px;
                padding: 10px 16px;
                font-size: 12px;
                font-weight: 800;
            }
            QPushButton:hover {
                background: #3B151F;
            }
        """

        # ==========================================================
        # HERO HEADER
        # ==========================================================

        header = QFrame()
        header.setStyleSheet("""
            QFrame {
                background: #070D1A;
                border: 1px solid #17243A;
                border-radius: 24px;
            }
        """)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(24, 20, 24, 20)
        header_layout.setSpacing(18)

        title_column = QVBoxLayout()
        title_column.setSpacing(4)

        eyebrow = QLabel("BRIDGETALK  /  LIVE TRANSLATION")
        eyebrow.setStyleSheet("""
            QLabel {
                color: #60A5FA;
                font-size: 10px;
                font-weight: 900;
                letter-spacing: 2px;
                background: transparent;
            }
        """)
        title_column.addWidget(eyebrow)

        title = QLabel("Sign language, understood.")
        title.setStyleSheet(title_style)
        title_column.addWidget(title)

        subtitle = QLabel(
            "Real-time Indian Sign Language recognition, translation and voice output."
        )
        subtitle.setStyleSheet(subtitle_style)
        title_column.addWidget(subtitle)

        header_layout.addLayout(title_column)
        header_layout.addStretch()

        self.status_label = QLabel("●  CAMERA OFFLINE")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setMinimumWidth(145)
        self.status_label.setStyleSheet("""
            QLabel {
                color: #FB7185;
                background: #180D15;
                border: 1px solid #4A1D2B;
                border-radius: 18px;
                padding: 9px 14px;
                font-size: 10px;
                font-weight: 900;
            }
        """)
        header_layout.addWidget(self.status_label)

        self.start_button = QPushButton("START CAMERA")
        self.start_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.start_button.setMinimumHeight(42)
        self.start_button.setStyleSheet(primary_style)
        self.start_button.clicked.connect(self.toggle_camera)
        header_layout.addWidget(self.start_button)

        layout.addWidget(header)

        # ==========================================================
        # LIVE TRANSLATION HERO
        # ==========================================================

        live_card = QFrame()
        live_card.setStyleSheet(card_style)
        live_layout = QVBoxLayout(live_card)
        live_layout.setContentsMargins(18, 18, 18, 18)
        live_layout.setSpacing(14)

        live_header = QHBoxLayout()
        live_label = QLabel("LIVE SIGN CAPTURE")
        live_label.setStyleSheet(section_style)
        live_header.addWidget(live_label)
        live_header.addStretch()

        self.tracking_status = QLabel("● SYSTEM READY")
        self.tracking_status.setStyleSheet("""
            QLabel {
                color: #64748B;
                background: #0C1424;
                border: 1px solid #1B2A43;
                border-radius: 13px;
                padding: 6px 10px;
                font-size: 9px;
                font-weight: 900;
            }
        """)
        live_header.addWidget(self.tracking_status)
        live_layout.addLayout(live_header)

        hero_row = QHBoxLayout()
        hero_row.setSpacing(16)

        # Camera
        camera_panel = QFrame()
        camera_panel.setStyleSheet("""
            QFrame {
                background: #030712;
                border: 1px solid #1E3557;
                border-radius: 20px;
            }
        """)
        camera_panel_layout = QVBoxLayout(camera_panel)
        camera_panel_layout.setContentsMargins(8, 8, 8, 8)
        camera_panel_layout.setSpacing(6)

        self.camera_preview = CameraPreview()
        self.camera_preview.setFixedSize(590, 355)
        self.camera_preview.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )
        camera_panel_layout.addWidget(
            self.camera_preview,
            alignment=Qt.AlignmentFlag.AlignCenter,
        )

        camera_meta = QHBoxLayout()
        camera_meta.setContentsMargins(8, 2, 8, 4)

        camera_meta_left = QLabel("MEDIAPIPE HAND LANDMARKS")
        camera_meta_left.setStyleSheet("""
            QLabel {
                color: #52627A;
                font-size: 9px;
                font-weight: 900;
                letter-spacing: 1px;
                background: transparent;
            }
        """)
        camera_meta.addWidget(camera_meta_left)
        camera_meta.addStretch()

        camera_meta_right = QLabel("21 POINTS / HAND")
        camera_meta_right.setStyleSheet("""
            QLabel {
                color: #60A5FA;
                font-size: 9px;
                font-weight: 900;
                background: transparent;
            }
        """)
        camera_meta.addWidget(camera_meta_right)
        camera_panel_layout.addLayout(camera_meta)

        hero_row.addWidget(camera_panel, 3)

        # Recognition panel
        recognition_panel = QFrame()
        recognition_panel.setStyleSheet("""
            QFrame {
                background: #07101F;
                border: 1px solid #1A2C49;
                border-radius: 20px;
            }
        """)
        recognition_layout = QVBoxLayout(recognition_panel)
        recognition_layout.setContentsMargins(22, 22, 22, 22)
        recognition_layout.setSpacing(13)

        ai_label = QLabel("AI RECOGNITION")
        ai_label.setStyleSheet("""
            QLabel {
                color: #60A5FA;
                font-size: 10px;
                font-weight: 900;
                letter-spacing: 2px;
                background: transparent;
            }
        """)
        recognition_layout.addWidget(ai_label)

        self.gesture_result = QLabel("WAITING")
        self.gesture_result.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )
        self.gesture_result.setWordWrap(True)
        self.gesture_result.setMinimumHeight(100)
        self.gesture_result.setStyleSheet("""
            QLabel {
                color: #F8FAFC;
                font-size: 30px;
                font-weight: 900;
                background: transparent;
            }
        """)
        recognition_layout.addWidget(self.gesture_result)

        confidence_caption = QLabel("CONFIDENCE")
        confidence_caption.setStyleSheet("""
            QLabel {
                color: #65748C;
                font-size: 9px;
                font-weight: 900;
                letter-spacing: 1px;
                background: transparent;
            }
        """)
        recognition_layout.addWidget(confidence_caption)

        self.confidence_label = QLabel("0%")
        self.confidence_label.setStyleSheet("""
            QLabel {
                color: #38BDF8;
                font-size: 22px;
                font-weight: 900;
                background: transparent;
            }
        """)
        recognition_layout.addWidget(self.confidence_label)

        self.confidence_bar = QFrame()
        self.confidence_bar.setFixedHeight(6)
        self.confidence_bar.setStyleSheet("""
            QFrame {
                background: #162238;
                border-radius: 3px;
                border: none;
            }
        """)
        bar_layout = QHBoxLayout(self.confidence_bar)
        bar_layout.setContentsMargins(0, 0, 0, 0)
        bar_layout.setSpacing(0)

        self.confidence_fill = QFrame()
        self.confidence_fill.setFixedHeight(6)
        self.confidence_fill.setStyleSheet("""
            QFrame {
                background: #38BDF8;
                border-radius: 3px;
                border: none;
            }
        """)
        bar_layout.addWidget(self.confidence_fill)
        bar_layout.addStretch()
        recognition_layout.addWidget(self.confidence_bar)

        recognition_layout.addStretch()

        # Tracking mini stats
        stats = QHBoxLayout()
        stats.setSpacing(8)

        def stat_box(title_text, value_widget):
            box = QFrame()
            box.setStyleSheet(inner_style)
            box_layout = QVBoxLayout(box)
            box_layout.setContentsMargins(10, 9, 10, 9)
            box_layout.setSpacing(2)

            caption = QLabel(title_text)
            caption.setAlignment(Qt.AlignmentFlag.AlignCenter)
            caption.setStyleSheet("""
                QLabel {
                    color: #53637C;
                    font-size: 8px;
                    font-weight: 900;
                    background: transparent;
                }
            """)
            box_layout.addWidget(caption)

            value_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
            value_widget.setStyleSheet("""
                QLabel {
                    color: #DCE7F7;
                    font-size: 14px;
                    font-weight: 900;
                    background: transparent;
                }
            """)
            box_layout.addWidget(value_widget)
            return box

        self.hand_count = QLabel("0")
        stats.addWidget(stat_box("HANDS", self.hand_count))

        self.hand_side = QLabel("—")
        stats.addWidget(stat_box("SIDE", self.hand_side))

        recognition_layout.addLayout(stats)

        self.add_word_button = QPushButton("+  ADD TO MESSAGE")
        self.add_word_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_word_button.setMinimumHeight(42)
        self.add_word_button.setEnabled(False)
        self.add_word_button.setStyleSheet(success_style)
        self.add_word_button.clicked.connect(self.add_current_word)
        recognition_layout.addWidget(self.add_word_button)

        hero_row.addWidget(recognition_panel, 2)
        live_layout.addLayout(hero_row)

        layout.addWidget(live_card)

        # ==========================================================
        # COMMUNICATION / OUTPUT
        # ==========================================================

        output_row = QHBoxLayout()
        output_row.setSpacing(16)

        # Current recognized word
        message_card = QFrame()
        message_card.setStyleSheet(card_style)
        message_layout = QVBoxLayout(message_card)
        message_layout.setContentsMargins(20, 18, 20, 18)
        message_layout.setSpacing(10)

        msg_header = QHBoxLayout()
        msg_title = QLabel("RECOGNIZED MESSAGE")
        msg_title.setStyleSheet(section_style)
        msg_header.addWidget(msg_title)
        msg_header.addStretch()

        self.communication_text = QLabel("Waiting for a sign...")
        self.communication_text.setStyleSheet("""
            QLabel {
                color: #F8FAFC;
                font-size: 22px;
                font-weight: 850;
                background: transparent;
            }
        """)
        self.communication_text.setMinimumHeight(54)
        self.communication_text.setWordWrap(True)
        message_layout.addWidget(self.communication_text)

        message_hint = QLabel("Detected text from the current sign")
        message_hint.setStyleSheet(subtitle_style)
        message_layout.addWidget(message_hint)

        output_row.addWidget(message_card, 1)

        # Sentence
        sentence_card = QFrame()
        sentence_card.setStyleSheet(card_style)
        sentence_layout = QVBoxLayout(sentence_card)
        sentence_layout.setContentsMargins(20, 18, 20, 18)
        sentence_layout.setSpacing(10)

        sentence_header = QHBoxLayout()
        sentence_title = QLabel("COMMUNICATION")
        sentence_title.setStyleSheet(section_style)
        sentence_header.addWidget(sentence_title)
        sentence_header.addStretch()

        self.backspace_button = QPushButton("BACKSPACE")
        self.backspace_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.backspace_button.setStyleSheet(secondary_style)
        sentence_header.addWidget(self.backspace_button)
        self.backspace_button.clicked.connect(self.remove_last_word)

        sentence_layout.addLayout(sentence_header)

        self.sentence_label = QLabel("Your sentence will appear here...")
        self.sentence_label.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )
        self.sentence_label.setWordWrap(True)
        self.sentence_label.setMinimumHeight(68)
        self.sentence_label.setStyleSheet("""
            QLabel {
                background: #070E1B;
                border: 1px solid #1A2B46;
                border-radius: 14px;
                color: #C8D5E8;
                font-size: 14px;
                font-weight: 650;
                padding: 13px;
            }
        """)
        sentence_layout.addWidget(self.sentence_label)

        sentence_buttons = QHBoxLayout()
        sentence_buttons.setSpacing(8)

        self.clear_button = QPushButton("CLEAR")
        self.clear_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.clear_button.setStyleSheet(danger_style)
        self.clear_button.clicked.connect(self.clear_sentence)
        sentence_buttons.addWidget(self.clear_button)

        self.copy_button = QPushButton("COPY")
        self.copy_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.copy_button.setStyleSheet(secondary_style)
        self.copy_button.clicked.connect(self.copy_sentence)
        sentence_buttons.addWidget(self.copy_button)

        self.speak_button = QPushButton("SPEAK")
        self.speak_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.speak_button.setStyleSheet(success_style)
        self.speak_button.setEnabled(False)
        self.speak_button.clicked.connect(self.speak_sentence)
        sentence_buttons.addWidget(self.speak_button)

        sentence_layout.addLayout(sentence_buttons)
        output_row.addWidget(sentence_card, 1)

        layout.addLayout(output_row)

        # ==========================================================
        # TRANSLATION
        # ==========================================================

        translation_card = QFrame()
        translation_card.setStyleSheet("""
            QFrame {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 1,
                    stop: 0 #0A1221,
                    stop: 1 #0B172A
                );
                border: 1px solid #1C3B61;
                border-radius: 22px;
            }
        """)
        translation_layout = QVBoxLayout(translation_card)
        translation_layout.setContentsMargins(20, 18, 20, 18)
        translation_layout.setSpacing(12)

        translation_header = QHBoxLayout()
        translation_title = QLabel("TRANSLATION")
        translation_title.setStyleSheet(section_style)
        translation_header.addWidget(translation_title)
        translation_header.addStretch()

        target_title = QLabel("TARGET LANGUAGE")
        target_title.setStyleSheet("""
            QLabel {
                color: #61728B;
                font-size: 9px;
                font-weight: 900;
                background: transparent;
            }
        """)
        translation_header.addWidget(target_title)

        self.target_language_combo = QComboBox()
        self.target_language_combo.setMinimumHeight(38)
        self.target_language_combo.setMinimumWidth(150)
        self.target_language_combo.setCursor(Qt.CursorShape.PointingHandCursor)
        self.target_language_combo.addItems(
            list(TranslationService.LANGUAGES.keys())
        )
        self.target_language_combo.setCurrentText("English")
        self.target_language_combo.currentTextChanged.connect(
            self._translation_language_changed
        )
        self.target_language_combo.setStyleSheet("""
            QComboBox {
                background: #08101E;
                color: #D9E5F5;
                border: 1px solid #263D5C;
                border-radius: 10px;
                padding: 7px 12px;
                font-size: 11px;
                font-weight: 750;
            }
            QComboBox:hover {
                border-color: #3B82F6;
            }
            QComboBox QAbstractItemView {
                background: #0B1424;
                color: #E2E8F0;
                selection-background-color: #1D4ED8;
                border: 1px solid #263D5C;
            }
        """)
        translation_header.addWidget(self.target_language_combo)

        translation_layout.addLayout(translation_header)

        translation_body = QHBoxLayout()
        translation_body.setSpacing(14)

        self.translation_result_label = QLabel(
            "Translated text will appear here..."
        )
        self.translation_result_label.setWordWrap(True)
        self.translation_result_label.setMinimumHeight(58)
        self.translation_result_label.setStyleSheet("""
            QLabel {
                color: #E8F1FF;
                background: #07101D;
                border: 1px solid #203A5D;
                border-radius: 14px;
                padding: 12px 15px;
                font-size: 17px;
                font-weight: 750;
            }
        """)
        translation_body.addWidget(self.translation_result_label, 1)

        translation_buttons = QVBoxLayout()
        translation_buttons.setSpacing(8)

        self.translate_button = QPushButton("TRANSLATE")
        self.translate_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.translate_button.setMinimumHeight(40)
        self.translate_button.setStyleSheet(primary_style)
        self.translate_button.setEnabled(False)
        self.translate_button.clicked.connect(self.translate_sentence)
        translation_buttons.addWidget(self.translate_button)

        self.speak_translation_button = QPushButton("SPEAK OUTPUT")
        self.speak_translation_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.speak_translation_button.setMinimumHeight(40)
        self.speak_translation_button.setStyleSheet(success_style)
        self.speak_translation_button.setEnabled(False)
        self.speak_translation_button.clicked.connect(self.speak_translation)
        translation_buttons.addWidget(self.speak_translation_button)

        translation_body.addLayout(translation_buttons)
        translation_layout.addLayout(translation_body)

        layout.addWidget(translation_card)

        # ==========================================================
        # SPEECH INPUT / VOICE
        # ==========================================================

        tools_row = QHBoxLayout()
        tools_row.setSpacing(16)

        speech_card = QFrame()
        speech_card.setStyleSheet(card_style)
        speech_layout = QVBoxLayout(speech_card)
        speech_layout.setContentsMargins(20, 18, 20, 18)
        speech_layout.setSpacing(9)

        speech_title = QLabel("VOICE INPUT")
        speech_title.setStyleSheet(section_style)
        speech_layout.addWidget(speech_title)

        self.speech_result_label = QLabel(
            "Speak naturally and BridgeTalk will convert speech to text."
        )
        self.speech_result_label.setWordWrap(True)
        self.speech_result_label.setMinimumHeight(48)
        self.speech_result_label.setStyleSheet("""
            QLabel {
                color: #94A3B8;
                background: #070E1B;
                border: 1px solid #192A44;
                border-radius: 12px;
                padding: 10px;
                font-size: 12px;
                font-weight: 600;
            }
        """)
        speech_layout.addWidget(self.speech_result_label)

        speech_buttons = QHBoxLayout()
        speech_buttons.setSpacing(8)

        self.listen_button = QPushButton("START LISTENING")
        self.listen_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.listen_button.setMinimumHeight(38)
        self.listen_button.setStyleSheet(primary_style)
        self.listen_button.clicked.connect(self.start_speech_recognition)
        speech_buttons.addWidget(self.listen_button)

        self.add_speech_button = QPushButton("+ ADD SPEECH")
        self.add_speech_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_speech_button.setMinimumHeight(38)
        self.add_speech_button.setStyleSheet(secondary_style)
        self.add_speech_button.setEnabled(False)
        self.add_speech_button.clicked.connect(self.add_speech_to_sentence)
        speech_buttons.addWidget(self.add_speech_button)

        speech_layout.addLayout(speech_buttons)
        tools_row.addWidget(speech_card, 1)

        voice_card = QFrame()
        voice_card.setStyleSheet(card_style)
        voice_layout = QVBoxLayout(voice_card)
        voice_layout.setContentsMargins(20, 18, 20, 18)
        voice_layout.setSpacing(9)

        voice_title = QLabel("VOICE OUTPUT")
        voice_title.setStyleSheet(section_style)
        voice_layout.addWidget(voice_title)

        self.voice_combo = QComboBox()
        self.voice_combo.setMinimumHeight(38)
        self.voice_combo.setCursor(Qt.CursorShape.PointingHandCursor)
        self.voice_combo.setStyleSheet("""
            QComboBox {
                background: #070E1B;
                color: #D9E5F5;
                border: 1px solid #263D5C;
                border-radius: 10px;
                padding: 7px 12px;
                font-size: 11px;
                font-weight: 700;
            }
            QComboBox QAbstractItemView {
                background: #0B1424;
                color: #E2E8F0;
                selection-background-color: #1D4ED8;
            }
        """)
        voice_layout.addWidget(self.voice_combo)

        voice_buttons = QHBoxLayout()
        voice_buttons.setSpacing(8)

        self.test_voice_button = QPushButton("TEST VOICE")
        self.test_voice_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.test_voice_button.setMinimumHeight(38)
        self.test_voice_button.setStyleSheet(secondary_style)
        self.test_voice_button.clicked.connect(self.test_selected_voice)
        voice_buttons.addWidget(self.test_voice_button)

        self.voice_speak_button = QPushButton("SPEAK SENTENCE")
        self.voice_speak_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.voice_speak_button.setMinimumHeight(38)
        self.voice_speak_button.setStyleSheet(success_style)
        self.voice_speak_button.setEnabled(False)
        self.voice_speak_button.clicked.connect(self.speak_sentence)
        voice_buttons.addWidget(self.voice_speak_button)

        voice_layout.addLayout(voice_buttons)
        tools_row.addWidget(voice_card, 1)

        layout.addLayout(tools_row)

        # ----------------------------------------------------------
        # Internal compatibility: existing camera-start logic uses
        # camera_combo.currentData(). Keep it hidden.
        # ----------------------------------------------------------

        self.camera_combo = QComboBox(self)
        self.camera_combo.hide()

        # Load cameras and voices using the existing services.
        self._load_tts_voices()
        self.voice_combo.currentIndexChanged.connect(
            self._voice_changed
        )
        self._load_cameras()

        # Initial recognition state.
        self.confidence_label.setText("0%")
        self.confidence_fill.setFixedWidth(0)

    # ==========================================================
    # COPY SENTENCE
    # ==========================================================

    def copy_sentence(self) -> None:
        """Copy the current communication sentence."""

        sentence = (
            self.communication_service
            .get_sentence()
            .strip()
        )

        if not sentence:
            return

        clipboard = QApplication.clipboard()

        if clipboard is not None:
            clipboard.setText(sentence)

        self.tracking_status.setText(
            "●  SENTENCE COPIED"
        )

    # ==========================================================
    # LOAD CAMERAS
    # ==========================================================

    def _load_cameras(self) -> None:
        """Load available cameras for the camera service.

        The redesigned UI does not display a camera selector,
        but the existing camera-start logic still uses
        ``camera_combo.currentData()``. Keep a hidden combo box
        internally so the camera service remains compatible.
        """

        if not hasattr(self, "camera_combo"):
            self.camera_combo = QComboBox(self)
            self.camera_combo.hide()

        self.camera_combo.clear()

        cameras = (
            self.camera_service.available_cameras()
        )

        if not cameras:

            self.camera_combo.addItem(
                "No camera detected",
                -1,
            )

            self.start_button.setEnabled(
                False
            )

            return

        for index in cameras:

            self.camera_combo.addItem(
                f"Camera {index + 1}",
                index,
            )

    # ==========================================================
    # CAMERA TOGGLE
    # ==========================================================

    def toggle_camera(
        self,
    ) -> None:

        if self.camera_service.is_running():

            self.stop_camera()

        else:

            self.start_camera()

    # ==========================================================
    # START CAMERA
    # ==========================================================

    def start_camera(
        self,
    ) -> None:

        camera_index = (
            self.camera_combo.currentData()
        )

        if camera_index is None:
            return

        if camera_index < 0:
            return

        self.camera_service.start(
            int(camera_index)
        )

        thread = (
            self.camera_service.thread
        )

        if thread is None:
            return

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

    # ==========================================================
    # STOP CAMERA
    # ==========================================================

    def stop_camera(
        self,
    ) -> None:

        self.camera_service.stop()

        self.camera_preview.clear_preview()

        self.start_button.setText(
            "Start Camera"
        )

        self.status_label.setText(
            "â— Camera Offline"
        )

        self.tracking_status.setText(
            "●  SYSTEM READY"
        )

        self.hand_count.setText(
            "0"
        )

        self.hand_side.setText(
            "Waiting..."
        )

        self.gesture_result.setText(
            "WAITING"
        )

        if hasattr(self, "confidence_label"):
            self.confidence_label.setText("0%")

        if hasattr(self, "confidence_fill"):
            self.confidence_fill.setFixedWidth(0)

        self.communication_text.setText(
            "Waiting for a gesture..."
        )

    # ==========================================================
    # HAND COUNT
    # ==========================================================

    @Slot(int)
    def update_hand_count(
        self,
        count: int,
    ) -> None:

        self.hand_count.setText(
            str(count)
        )

    # ==========================================================
    # HANDEDNESS
    # ==========================================================

    @Slot(str)
    def update_handedness(
        self,
        value: str,
    ) -> None:

        self.hand_side.setText(
            value
        )

    # ==========================================================
    # GESTURE
    # ==========================================================

    @Slot(str, float)
    def update_gesture(
        self,
        gesture: str,
        score: float,
    ) -> None:

        if (
            not gesture
            or gesture == "None"
        ):

            self.gesture_result.setText(
                "WAITING"
            )

            if hasattr(self, "confidence_label"):
                self.confidence_label.setText("0%")

            if hasattr(self, "confidence_fill"):
                self.confidence_fill.setFixedWidth(0)

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
            gesture
            .replace(
                "_",
                " ",
            )
            .upper(),
        )

        confidence = (
            max(
                0.0,
                min(
                    1.0,
                    score,
                ),
            )
            * 100
        )

        self.gesture_result.setText(
            display_name
        )

        if hasattr(self, "confidence_label"):
            self.confidence_label.setText(
                f"{confidence:.0f}%"
            )

        if hasattr(self, "confidence_fill"):
            fill_width = int(
                max(0.0, min(100.0, confidence))
                * 2.0
            )
            self.confidence_fill.setFixedWidth(fill_width)

        self.tracking_status.setText(
            "●  GESTURE RECOGNIZED"
        )

    # ==========================================================
    # CURRENT WORD
    # ==========================================================

    @Slot(str)
    def update_communication_text(
        self,
        text: str,
    ) -> None:

        self.current_word = (
            text.strip()
        )

        if not self.current_word:

            self.communication_text.setText(
                "Waiting for a gesture..."
            )

            self.add_word_button.setEnabled(
                False
            )

            return

        self.communication_text.setText(
            self.current_word
        )

        self.add_word_button.setEnabled(
            True
        )

    # ==========================================================
    # ADD WORD
    # ==========================================================

    def add_current_word(
        self,
    ) -> None:

        if not self.current_word:
            return

        sentence = (
            self.communication_service.add_if_new(
                self.current_word
            )
        )

        self._update_sentence(
            sentence
        )

    # ==========================================================
    # REMOVE LAST WORD
    # ==========================================================

    def remove_last_word(
        self,
    ) -> None:

        sentence = (
            self.communication_service.remove_last()
        )

        self._update_sentence(
            sentence
        )

    # ==========================================================
    # CLEAR SENTENCE
    # ==========================================================

    def clear_sentence(
        self,
    ) -> None:

        sentence = (
            self.communication_service.clear()
        )

        self._update_sentence(
            sentence
        )

    # ==========================================================
    # UPDATE SENTENCE
    # ==========================================================

    def _update_sentence(
        self,
        sentence: str,
    ) -> None:

        if not sentence:

            self.sentence_label.setText(
                "Your sentence will appear here..."
            )

            self.speak_button.setEnabled(
                False
            )

            if hasattr(self, "voice_speak_button"):
                self.voice_speak_button.setEnabled(
                    False
                )

            if hasattr(self, "translate_button"):
                self.translate_button.setEnabled(
                    False
                )

            if hasattr(self, "speak_translation_button"):
                self.speak_translation_button.setEnabled(
                    False
                )

        else:

            self.sentence_label.setText(
                sentence
            )

            self.speak_button.setEnabled(
                True
            )

            if hasattr(self, "voice_speak_button"):
                self.voice_speak_button.setEnabled(
                    True
                )

            if hasattr(self, "translate_button"):
                self.translate_button.setEnabled(
                    True
                )

    # ==========================================================
    # SPEAK SENTENCE
    # ==========================================================

    def speak_sentence(
        self,
    ) -> None:
        """Speak the complete communication sentence."""

        sentence = (
            self.communication_service
            .get_sentence()
            .strip()
        )

        if not sentence:
            return

        print(
            "[BridgeTalk] Speaking:",
            sentence,
        )

        success = (
            self.tts_service.speak(
                sentence
            )
        )

        if success:

            self.tracking_status.setText(
                "â— Speaking..."
            )

    # ==========================================================
    # START SPEECH RECOGNITION
    # ==========================================================

    def start_speech_recognition(
        self,
    ) -> None:
        """Start speech recognition in a background thread."""

        if (
            self.speech_worker is not None
            and self.speech_worker.isRunning()
        ):
            return

        self.current_speech_text = ""

        self.add_speech_button.setEnabled(
            False
        )

        self.listen_button.setEnabled(
            False
        )

        self.listen_button.setText(
            "ðŸŽ¤  Listening..."
        )

        self.speech_result_label.setText(
            "Listening... Speak clearly for a few seconds."
        )

        self.tracking_status.setText(
            "â— Listening..."
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

    # ==========================================================
    # SPEECH RESULT
    # ==========================================================

    @Slot(object)
    def _speech_result_ready(
        self,
        result,
    ) -> None:
        """Receive recognized speech from the worker."""

        if result:

            self.current_speech_text = (
                str(result).strip()
            )

            self.speech_result_label.setText(
                self.current_speech_text
            )

            self.add_speech_button.setEnabled(
                True
            )

            self.tracking_status.setText(
                "â— Speech Recognized"
            )

        else:

            self.current_speech_text = ""

            self.speech_result_label.setText(
                "Speech could not be understood. "
                "Please try again."
            )

            self.add_speech_button.setEnabled(
                False
            )

            self.tracking_status.setText(
                "â— Speech Not Recognized"
            )

    # ==========================================================
    # SPEECH FINISHED
    # ==========================================================

    @Slot()
    def _speech_finished(
        self,
    ) -> None:
        """Reset the listening button."""

        self.listen_button.setEnabled(
            True
        )

        self.listen_button.setText(
            "ðŸŽ¤  Start Listening"
        )

        if not self.current_speech_text:

            self.tracking_status.setText(
                "â— Ready"
            )

    # ==========================================================
    # ADD SPEECH TO SENTENCE
    # ==========================================================

    def add_speech_to_sentence(
        self,
    ) -> None:
        """Add recognized speech to the communication sentence."""

        text = (
            self.current_speech_text
            .strip()
        )

        if not text:
            return

        sentence = (
            self.communication_service.add_if_new(
                text
            )
        )

        self._update_sentence(
            sentence
        )

        self.speech_result_label.setText(
            text
        )

        self.add_speech_button.setEnabled(
            False
        )

        self.tracking_status.setText(
            "â— Speech Added"
        )

    # ==========================================================
    # TRANSLATION LANGUAGE CHANGED
    # ==========================================================

    def _translation_language_changed(
        self,
        language: str,
    ) -> None:
        """Change the target translation language."""

        try:
            self.translation_service.set_target_language(
                language
            )

            self.current_translation = ""

            self.translation_result_label.setText(
                "Translated text will appear here..."
            )

            self.speak_translation_button.setEnabled(
                False
            )

            sentence = (
                self.communication_service
                .get_sentence()
                .strip()
            )

            self.translate_button.setEnabled(
                bool(sentence)
            )

            self.tracking_status.setText(
                f"â— Target: {language}"
            )

        except Exception as exc:

            print(
                "[Translation] Language error:",
                repr(exc),
            )

    # ==========================================================
    # TRANSLATE SENTENCE
    # ==========================================================

    def translate_sentence(
        self,
    ) -> None:
        """Translate the current communication sentence."""

        sentence = (
            self.communication_service
            .get_sentence()
            .strip()
        )

        if not sentence:
            self.translation_result_label.setText(
                "Add a sentence before translating."
            )
            return

        language = (
            self.translation_service
            .get_target_language()
        )

        self.translate_button.setEnabled(
            False
        )

        self.speak_translation_button.setEnabled(
            False
        )

        self.translation_result_label.setText(
            f"Translating to {language}..."
        )

        self.tracking_status.setText(
            "â— Translating..."
        )

        # Translation is network-based and can take time.
        # Keep the UI responsive by doing it in a small worker.
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

    # ==========================================================
    # TRANSLATION RESULT
    # ==========================================================

    @Slot(object)
    def _translation_result_ready(
        self,
        result,
    ) -> None:
        """Display the translated sentence."""

        if result:

            self.current_translation = (
                str(result).strip()
            )

            self.translation_result_label.setText(
                self.current_translation
            )

            self.speak_translation_button.setEnabled(
                True
            )

            self.tracking_status.setText(
                "â— Translation Ready"
            )

        else:

            self.current_translation = ""

            self.translation_result_label.setText(
                "Translation failed. "
                "Check your internet connection "
                "and try again."
            )

            self.speak_translation_button.setEnabled(
                False
            )

            self.tracking_status.setText(
                "â— Translation Failed"
            )

    # ==========================================================
    # TRANSLATION FINISHED
    # ==========================================================

    @Slot()
    def _translation_finished(
        self,
    ) -> None:
        """Re-enable translation controls."""

        sentence = (
            self.communication_service
            .get_sentence()
            .strip()
        )

        self.translate_button.setEnabled(
            bool(sentence)
        )

    # ==========================================================
    # SPEAK TRANSLATION
    # ==========================================================

    def speak_translation(
        self,
    ) -> None:
        """Speak the currently translated sentence."""

        text = (
            self.current_translation
            .strip()
        )

        if not text:
            return

        print(
            "[BridgeTalk] Speaking translation:",
            text,
        )

        success = (
            self.tts_service.speak(
                text
            )
        )

        if success:

            self.tracking_status.setText(
                "â— Speaking Translation..."
            )

    # ==========================================================
    # LOAD TTS VOICES
    # ==========================================================

    def _load_tts_voices(self) -> None:
        """Load installed Windows SAPI5 voices."""

        self.voice_combo.clear()

        try:
            self._tts_voices = (
                self.tts_service.get_voices()
            )
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

        # Prefer Microsoft Zira when available.
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

    # ==========================================================
    # VOICE CHANGED
    # ==========================================================

    def _voice_changed(
        self,
        index: int,
    ) -> None:
        """Change the active speech voice."""

        if index < 0:
            return

        voice_index = self.voice_combo.itemData(
            index
        )

        if voice_index is None:
            return

        if self.tts_service.set_voice(
            int(voice_index)
        ):
            self.tracking_status.setText(
                f"â— Voice: {self.voice_combo.currentText()}"
            )

    # ==========================================================
    # TEST SELECTED VOICE
    # ==========================================================

    def test_selected_voice(
        self,
    ) -> None:
        """Test the selected Windows voice."""

        index = self.voice_combo.currentIndex()

        if index < 0:
            return

        voice_index = self.voice_combo.itemData(
            index
        )

        if voice_index is None:
            return

        if self.tts_service.set_voice(
            int(voice_index)
        ):
            self.tts_service.test_voice(
                int(voice_index)
            )

    # ==========================================================
    # CAMERA STARTED
    # ==========================================================

    @Slot()
    def _camera_started(
        self,
    ) -> None:

        self.start_button.setText(
            "Stop Camera"
        )

        self.status_label.setText(
            "●  CAMERA LIVE"
        )

        self.status_label.setStyleSheet(
            """
            QLabel {
                color: #22C55E;
                font-weight: 700;
            }
            """
        )

        self.tracking_status.setText(
            "●  MEDIAPIPE ACTIVE"
        )

    # ==========================================================
    # CAMERA STOPPED
    # ==========================================================

    @Slot()
    def _camera_stopped(
        self,
    ) -> None:

        self.start_button.setText(
            "Start Camera"
        )

        self.tracking_status.setText(
            "●  SYSTEM READY"
        )

    # ==========================================================
    # CAMERA ERROR
    # ==========================================================

    @Slot(str)
    def _camera_error(
        self,
        message: str,
    ) -> None:

        self.status_label.setText(
            "●  CAMERA ERROR"
        )

        print(
            f"Camera error:\n{message}"
        )

    # ==========================================================
    # TRACKING ERROR
    # ==========================================================

    @Slot(str)
    def _tracking_error(
        self,
        message: str,
    ) -> None:

        self.tracking_status.setText(
            "●  TRACKING ERROR"
        )

        print(
            f"MediaPipe error:\n{message}"
        )

    # ==========================================================
    # CLOSE
    # ==========================================================

    def close_camera(
        self,
    ) -> None:

        self.camera_service.stop()

        try:
            self.tts_service.close()
        except Exception:
            pass