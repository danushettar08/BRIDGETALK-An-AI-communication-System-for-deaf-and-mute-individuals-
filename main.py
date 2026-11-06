"""
BridgeTalk
AI Communication System for Deaf and Mute Individuals.

Application entry point.
"""

import sys

from PySide6.QtWidgets import QApplication

from config.theme import Theme
from utils.theme_manager import ThemeManager
from ui.main_window import MainWindow


def main() -> int:
    """Start BridgeTalk."""

    application = QApplication(sys.argv)

    application.setApplicationName("BridgeTalk")
    application.setApplicationDisplayName("BridgeTalk")
    application.setApplicationVersion("1.0.0")
    application.setOrganizationName("BridgeTalk")

    # Dark theme is the default.
    ThemeManager.set_theme(
        application,
        Theme.DARK,
    )

    window = MainWindow()
    window.show()

    return application.exec()


if __name__ == "__main__":
    sys.exit(main())

