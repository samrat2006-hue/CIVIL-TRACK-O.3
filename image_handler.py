
import re
import shutil
import subprocess
import tempfile
import uuid

from pathlib import Path

from PIL import Image, UnidentifiedImageError


# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_DIR = BASE_DIR / "uploads"

ALLOWED_IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp"
}

ALLOWED_VIDEO_EXTENSIONS = {
    ".mp4",
    ".mov",
    ".avi",
    ".mkv",
    ".webm"
}

MAX_IMAGE_SIZE = 5 * 1024 * 1024
MAX_VIDEO_SIZE = 50 * 1024 * 1024

MAX_VIDEO_DURATION = 30


# --------------------------------------------------
# INITIALIZE UPLOAD DIRECTORY
# --------------------------------------------------

def initialize_upload_directory():
    """Create the upload directory if it does not exist."""

    UPLOAD_DIR.mkdir(
        parents=True,
        exist_ok=True
    )


# --------------------------------------------------
# SAFE FILE PATH
# --------------------------------------------------

def get_safe_upload_path(file_path):
    """
    Return a file path only if it is directly inside uploads.
    """

    if not file_path:
        return None

    try:

        upload_root = UPLOAD_DIR.resolve()
        target = (BASE_DIR / file_path).resolve()

        if target.parent != upload_root:
            return None

        return target

    except (OSError, ValueError):
        return None


# --------------------------------------------------
# IMAGE VALIDATION
# --------------------------------------------------

def validate_image(uploaded_file):
    """
    Validate an uploaded photograph.

    Returns:
        (True, message) if valid
        (False, message) if invalid
    """

    if uploaded_file is None:
        return False, "No image was selected."

    extension = Path(uploaded_file.name).suffix.lower()

    if extension not in ALLOWED_IMAGE_EXTENSIONS:
        return False, (
            "Only JPG, JPEG, PNG and WEBP images are allowed."
        )

    try:

        uploaded_file.seek(0)
        file_data = uploaded_file.getvalue()

        if not file_data:
            return False, "The selected image is empty."

        if len(file_data) > MAX_IMAGE_SIZE:
            return False, "Each image must not exceed 5 MB."

        uploaded_file.seek(0)

        image = Image.open(uploaded_file)
        image.verify()

        if image.format not in ("JPEG", "PNG", "WEBP"):
            return False, "Unsupported image format."

        return True, "Image is valid."

    except (
        UnidentifiedImageError,
        OSError,
        ValueError
    ):
        return False, "The selected file is not a valid image."

    finally:
        uploaded_file.seek(0)


# --------------------------------------------------
# SAVE SINGLE IMAGE
# --------------------------------------------------

def save_image(uploaded_file):
    """
    Validate and securely save one photograph.

    Returns:
        (saved_path, message)
    """

    initialize_upload_directory()

    valid, message = validate_image(uploaded_file)

    if not valid:
        return None, message

    destination = None

    try:

        uploaded_file.seek(0)

        image = Image.open(uploaded_file)
        image.load()

        extension = Path(uploaded_file.name).suffix.lower()

        unique_name = (
            f"{uuid.uuid4().hex}{extension}"
        )

        destination = UPLOAD_DIR / unique_name

        output_format = {
            ".jpg": "JPEG",
            ".jpeg": "JPEG",
            ".png": "PNG",
            ".webp": "WEBP"
        }[extension]

        if output_format == "JPEG":

            if image.mode not in ("RGB", "L"):
                image = image.convert("RGB")

        image.save(
            destination,
            format=output_format
        )

        relative_path = str(
            Path("uploads") / unique_name
        )

        return relative_path, "Image uploaded successfully."

    except (
        OSError,
        ValueError
    ):

        if destination and destination.exists():
            destination.unlink()

        return None, "Unable to save the image. Please try again."

    finally:
        uploaded_file.seek(0)


# --------------------------------------------------
# SAVE MULTIPLE IMAGES
# --------------------------------------------------

def save_images(uploaded_files):
    """
    Validate and save multiple photographs.

    If any image fails, previously saved images from
    this upload operation are deleted.

    Returns:
        (list_of_paths, message)

        An empty list indicates failure.
    """

    if not uploaded_files:
        return [], "No photographs were selected."

    saved_paths = []

    try:

        for uploaded_file in uploaded_files:

            image_path, message = save_image(
                uploaded_file
            )

            if image_path is None:

                delete_images(saved_paths)

                return [], (
                    f"{uploaded_file.name}: {message}"
                )

            saved_paths.append(image_path)

        return saved_paths, (
            f"{len(saved_paths)} photograph(s) uploaded successfully."
        )

    except Exception:

        delete_images(saved_paths)

        return [], (
            "Unable to upload the photographs. Please try again."
        )


# --------------------------------------------------
# VIDEO DURATION DETECTION
# --------------------------------------------------

def get_video_duration(video_path):
    """
    Read video duration using FFprobe or imageio-ffmpeg.

    Returns:
        (duration_seconds, error_message)

    Duration is None if it cannot be verified.
    """

    ffprobe_path = shutil.which("ffprobe")

    if ffprobe_path:

        try:

            result = subprocess.run(
                [
                    ffprobe_path,
                    "-v",
                    "error",
                    "-show_entries",
                    "format=duration",
                    "-of",
                    "default=noprint_wrappers=1:nokey=1",
                    str(video_path)
                ],
                capture_output=True,
                text=True,
                timeout=20
            )

            if result.returncode == 0:

                duration = float(result.stdout.strip())

                if duration > 0:
                    return duration, None

        except (
            ValueError,
            OSError,
            subprocess.TimeoutExpired
        ):
            pass

    # Fallback to the bundled FFmpeg executable.
    try:

        import imageio_ffmpeg

        ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()

        result = subprocess.run(
            [
                ffmpeg_path,
                "-hide_banner",
                "-i",
                str(video_path)
            ],
            capture_output=True,
            text=True,
            timeout=30
        )

        output = (
            result.stderr
            + "\n"
            + result.stdout
        )

        match = re.search(
            r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)",
            output
        )

        if match:

            hours = int(match.group(1))
            minutes = int(match.group(2))
            seconds = float(match.group(3))

            duration = (
                hours * 3600
                + minutes * 60
                + seconds
            )

            if duration > 0:
                return duration, None

        return None, "Unable to determine the video duration."

    except ImportError:

        return None, (
            "Video validation requires FFprobe or imageio-ffmpeg. "
            "Please install imageio-ffmpeg."
        )

    except (
        OSError,
        subprocess.TimeoutExpired
    ):

        return None, (
            "Unable to inspect this video file."
        )


# --------------------------------------------------
# VIDEO VALIDATION
# --------------------------------------------------

def validate_video(uploaded_file):
    """
    Validate video extension, size and duration.

    Maximum permitted duration: 30 seconds.
    """

    if uploaded_file is None:
        return False, "No video was selected."

    extension = Path(uploaded_file.name).suffix.lower()

    if extension not in ALLOWED_VIDEO_EXTENSIONS:
        return False, (
            "Supported formats: MP4, MOV, AVI, MKV and WEBM."
        )

    try:

        uploaded_file.seek(0)
        file_data = uploaded_file.getvalue()

        if not file_data:
            return False, "The selected video is empty."

        if len(file_data) > MAX_VIDEO_SIZE:
            return False, "Video size must not exceed 50 MB."

        initialize_upload_directory()

        temporary_path = None

        try:

            with tempfile.NamedTemporaryFile(
                delete=False,
                suffix=extension,
                dir=UPLOAD_DIR
            ) as temporary_file:

                temporary_file.write(file_data)

                temporary_path = Path(
                    temporary_file.name
                )

            duration, error = get_video_duration(
                temporary_path
            )

            if duration is None:
                return False, error

            if duration > MAX_VIDEO_DURATION:
                return False, (
                    "Video duration must not exceed 30 seconds."
                )

            return True, "Video is valid."

        finally:

            if temporary_path and temporary_path.exists():
                temporary_path.unlink()

    except OSError:
        return False, "Unable to validate the selected video."

    finally:
        uploaded_file.seek(0)


# --------------------------------------------------
# SAVE VIDEO
# --------------------------------------------------

def save_video(uploaded_file):
    """
    Validate and save a video.

    Returns:
        (saved_path, message)
    """

    initialize_upload_directory()

    valid, message = validate_video(
        uploaded_file
    )

    if not valid:
        return None, message

    destination = None

    try:

        extension = Path(
            uploaded_file.name
        ).suffix.lower()

        unique_name = (
            f"{uuid.uuid4().hex}{extension}"
        )

        destination = UPLOAD_DIR / unique_name

        uploaded_file.seek(0)

        with open(destination, "wb") as video_file:

            video_file.write(
                uploaded_file.getvalue()
            )

        relative_path = str(
            Path("uploads") / unique_name
        )

        return relative_path, "Video uploaded successfully."

    except OSError:

        if destination and destination.exists():
            destination.unlink()

        return None, "Unable to save the video. Please try again."

    finally:
        uploaded_file.seek(0)


# --------------------------------------------------
# DELETE SINGLE MEDIA FILE
# --------------------------------------------------

def delete_media(file_path):
    """
    Delete a media file only if it is directly
    inside the CivicTrack uploads directory.
    """

    target = get_safe_upload_path(file_path)

    if target is None:
        return False

    try:

        if target.is_file():
            target.unlink()
            return True

        return False

    except OSError:
        return False


# --------------------------------------------------
# DELETE MULTIPLE IMAGES
# --------------------------------------------------

def delete_images(image_paths):
    """
    Delete multiple uploaded photographs.
    """

    if not image_paths:
        return

    for image_path in image_paths:
        delete_media(image_path)


# --------------------------------------------------
# BACKWARD-COMPATIBLE DELETE IMAGE
# --------------------------------------------------

def delete_image(image_path):
    """
    Preserve compatibility with older project functions.
    """

    return delete_media(image_path)


# --------------------------------------------------
# GET IMAGE PATH
# --------------------------------------------------

def get_image_path(image_path):
    """
    Return an absolute image path if it exists
    inside the uploads directory.
    """

    target = get_safe_upload_path(image_path)

    if target and target.is_file():
        return str(target)

    return None


# --------------------------------------------------
# GET VIDEO PATH
# --------------------------------------------------

def get_video_path(video_path):
    """
    Return an absolute video path if it exists
    inside the uploads directory.
    """

    target = get_safe_upload_path(video_path)

    if target and target.is_file():
        return str(target)

    return None


# --------------------------------------------------
# TESTING
# --------------------------------------------------

if __name__ == "__main__":

    initialize_upload_directory()

    print("CivicTrack Media Handler")
    print("-" * 40)

    print("Upload directory:", UPLOAD_DIR)

    print(
        "Image formats:",
        ", ".join(sorted(ALLOWED_IMAGE_EXTENSIONS))
    )

    print(
        "Video formats:",
        ", ".join(sorted(ALLOWED_VIDEO_EXTENSIONS))
    )

    print("Maximum image size: 5 MB per image")
    print("Maximum video size: 50 MB")
    print("Maximum video duration: 30 seconds")

    print("\nMedia handler initialized successfully.")
