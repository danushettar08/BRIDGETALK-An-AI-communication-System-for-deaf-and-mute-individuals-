"""
BridgeTalk Camera Hardware Test.

This file tests only the webcam.

It does NOT load:
- Sanket
- MediaPipe
- Gesture recognition
- PySide6
- Any BridgeTalk UI

Purpose:
Confirm that OpenCV can open and continuously read
frames from the camera.
"""

from __future__ import annotations

import cv2


def open_camera(index: int):
    """
    Try opening a camera using Windows DirectShow first,
    then fall back to the default OpenCV backend.
    """

    print()
    print("=" * 60)
    print(f"Trying camera index: {index}")
    print("=" * 60)

    # ----------------------------------------------------------
    # DirectShow
    # ----------------------------------------------------------

    print("[Camera] Trying DirectShow...")

    camera = cv2.VideoCapture(
        index,
        cv2.CAP_DSHOW,
    )

    if camera.isOpened():

        print(
            f"[Camera] DirectShow opened camera {index}"
        )

        return camera

    camera.release()

    # ----------------------------------------------------------
    # Default backend
    # ----------------------------------------------------------

    print("[Camera] DirectShow failed.")
    print("[Camera] Trying default OpenCV backend...")

    camera = cv2.VideoCapture(
        index
    )

    if camera.isOpened():

        print(
            f"[Camera] Default backend opened camera {index}"
        )

        return camera

    camera.release()

    print(
        f"[Camera] Could NOT open camera {index}"
    )

    return None


def configure_camera(camera) -> None:
    """Configure a reasonable camera resolution."""

    camera.set(
        cv2.CAP_PROP_FRAME_WIDTH,
        640,
    )

    camera.set(
        cv2.CAP_PROP_FRAME_HEIGHT,
        480,
    )

    camera.set(
        cv2.CAP_PROP_FPS,
        30,
    )

    camera.set(
        cv2.CAP_PROP_BUFFERSIZE,
        1,
    )

    width = int(
        camera.get(
            cv2.CAP_PROP_FRAME_WIDTH
        )
    )

    height = int(
        camera.get(
            cv2.CAP_PROP_FRAME_HEIGHT
        )
    )

    fps = camera.get(
        cv2.CAP_PROP_FPS
    )

    print()
    print("[Camera] Configuration")
    print("-" * 40)
    print(f"Width  : {width}")
    print(f"Height : {height}")
    print(f"FPS    : {fps}")
    print("-" * 40)


def main() -> None:
    """Run the camera hardware test."""

    print()
    print("=" * 60)
    print("BRIDGETALK CAMERA HARDWARE TEST")
    print("=" * 60)

    camera = None
    opened_index = None

    # ----------------------------------------------------------
    # Try camera indexes 0-4
    # ----------------------------------------------------------

    for index in range(5):

        camera = open_camera(index)

        if camera is not None:

            opened_index = index

            break

    # ----------------------------------------------------------
    # No camera found
    # ----------------------------------------------------------

    if camera is None:

        print()
        print("=" * 60)
        print("RESULT: NO CAMERA COULD BE OPENED")
        print("=" * 60)
        print()
        print("OpenCV could not open camera indexes 0-4.")
        print()
        print("Check:")
        print("1. Windows Camera permission")
        print("2. Whether another application is using the camera")
        print("3. Whether the webcam is physically available")
        print("4. Windows Camera application")
        print()

        return

    # ----------------------------------------------------------
    # Configure
    # ----------------------------------------------------------

    configure_camera(
        camera
    )

    # ----------------------------------------------------------
    # Create preview window
    # ----------------------------------------------------------

    window_name = (
        "BridgeTalk Camera Test"
    )

    cv2.namedWindow(
        window_name,
        cv2.WINDOW_NORMAL,
    )

    cv2.resizeWindow(
        window_name,
        800,
        600,
    )

    print()
    print("=" * 60)
    print(
        f"CAMERA {opened_index} SUCCESSFULLY OPENED"
    )
    print("=" * 60)
    print()
    print("Camera preview should now appear.")
    print()
    print("Press Q to quit.")
    print()

    frame_count = 0

    # ----------------------------------------------------------
    # Camera loop
    # ----------------------------------------------------------

    try:

        while True:

            success, frame = camera.read()

            # --------------------------------------------------
            # Failed frame
            # --------------------------------------------------

            if not success:

                print(
                    "[Camera] Failed to read frame."
                )

                key = cv2.waitKey(10) & 0xFF

                if key == ord("q"):

                    break

                continue

            frame_count += 1

            # --------------------------------------------------
            # Add diagnostic information
            # --------------------------------------------------

            cv2.putText(
                frame,
                f"Camera Index: {opened_index}",
                (20, 35),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 255, 0),
                2,
                cv2.LINE_AA,
            )

            cv2.putText(
                frame,
                f"Frames: {frame_count}",
                (20, 70),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2,
                cv2.LINE_AA,
            )

            cv2.putText(
                frame,
                "Press Q to close",
                (20, 105),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 255),
                2,
                cv2.LINE_AA,
            )

            # --------------------------------------------------
            # Display
            # --------------------------------------------------

            cv2.imshow(
                window_name,
                frame,
            )

            # --------------------------------------------------
            # Keyboard
            # --------------------------------------------------

            key = cv2.waitKey(1) & 0xFF

            if key == ord("q"):

                break

    except KeyboardInterrupt:

        print()
        print(
            "[Camera] Test interrupted."
        )

    except Exception as exc:

        print()
        print(
            "[Camera] Runtime error:"
        )
        print(
            repr(exc)
        )

    finally:

        # ------------------------------------------------------
        # Cleanup
        # ------------------------------------------------------

        print()
        print(
            "[Camera] Releasing camera..."
        )

        camera.release()

        cv2.destroyAllWindows()

        print(
            "[Camera] Camera released."
        )

        print()
        print("=" * 60)
        print("CAMERA TEST FINISHED")
        print("=" * 60)


if __name__ == "__main__":
    main()