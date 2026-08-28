import os
import re
import shutil
from pathlib import Path

import pandas as pd
from PIL import Image, ImageOps


# ================================================================
# OCR SETUP
# ================================================================

try:
    import pytesseract

    TESSERACT_PATHS = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    ]

    TESSERACT_FOUND = shutil.which(
        "tesseract"
    )

    OCR_AVAILABLE = False

    if TESSERACT_FOUND:
        pytesseract.pytesseract.tesseract_cmd = (
            TESSERACT_FOUND
        )
        OCR_AVAILABLE = True

    else:
        for path in TESSERACT_PATHS:

            if os.path.exists(path):
                pytesseract.pytesseract.tesseract_cmd = (
                    path
                )
                OCR_AVAILABLE = True
                break

except Exception:
    OCR_AVAILABLE = False


# ================================================================
# WHISPER SETUP
# ================================================================

try:
    import whisper

    WHISPER_AVAILABLE = True

except Exception:
    WHISPER_AVAILABLE = False


class MultimodalProcessor:
    """
    Handles multimodal messages.

    Supported media:
    - Images: OCR using Tesseract
    - Voice notes: transcription using Whisper

    Also supports:
    - Different media type names
    - Lookup using media_id
    - Fallback lookup using message_id
    - Different possible CSV column names
    - Existing transcript/text columns if present
    """

    def __init__(
        self,
        dataset_path=None
    ):

        if dataset_path is None:
            dataset_path = (
                Path(__file__)
                .resolve()
                .parent
                .parent
                / "dataset"
            )

        self.dataset_path = Path(
            dataset_path
        )

        self.images_df = self._load_csv(
            "images.csv"
        )

        self.voice_notes_df = self._load_csv(
            "voice_notes.csv"
        )

        self._whisper_model = None
        self._whisper_failed = False

        print(
            "Multimodal processor initialized."
        )

        print(
            f"OCR available: {OCR_AVAILABLE}"
        )

        print(
            f"Whisper available: "
            f"{WHISPER_AVAILABLE}"
        )

    # ============================================================
    # CSV LOADING
    # ============================================================

    def _load_csv(
        self,
        filename
    ):

        path = (
            self.dataset_path
            / filename
        )

        if not path.exists():

            print(
                f"WARNING: {filename} "
                f"not found at: {path}"
            )

            return pd.DataFrame()

        try:

            dataframe = pd.read_csv(
                path
            )

            print(
                f"Loaded {filename}: "
                f"{len(dataframe)} rows"
            )

            return dataframe

        except Exception as error:

            print(
                f"WARNING: Could not load "
                f"{filename}: {error}"
            )

            return pd.DataFrame()

    # ============================================================
    # VALUE CLEANING
    # ============================================================

    def _safe_string(
        self,
        value
    ):

        if value is None:
            return ""

        try:
            if pd.isna(value):
                return ""
        except Exception:
            pass

        value = str(value).strip()

        if value.lower() in [
            "nan",
            "none",
            "null",
        ]:
            return ""

        return value

    def _clean_text(
        self,
        text
    ):

        text = self._safe_string(
            text
        )

        if not text:
            return ""

        text = text.replace(
            "\n",
            " "
        )

        text = text.replace(
            "\r",
            " "
        )

        text = re.sub(
            r"\s+",
            " ",
            text
        )

        return text.strip()

    # ============================================================
    # COLUMN HELPERS
    # ============================================================

    def _find_existing_column(
        self,
        dataframe,
        possible_columns
    ):

        if dataframe is None:
            return None

        if dataframe.empty:
            return None

        normalized_columns = {
            str(column).strip().lower():
            column
            for column in dataframe.columns
        }

        for column_name in possible_columns:

            normalized_name = (
                str(column_name)
                .strip()
                .lower()
            )

            if normalized_name in normalized_columns:

                return normalized_columns[
                    normalized_name
                ]

        return None

    def _get_row_value(
        self,
        row,
        possible_columns
    ):

        if row is None:
            return ""

        normalized_row = {
            str(key).strip().lower(): value
            for key, value
            in row.items()
        }

        for column_name in possible_columns:

            normalized_name = (
                str(column_name)
                .strip()
                .lower()
            )

            if normalized_name in normalized_row:

                return self._safe_string(
                    normalized_row[
                        normalized_name
                    ]
                )

        return ""

    # ============================================================
    # MEDIA PATH RESOLUTION
    # ============================================================

    def _resolve_media_path(
        self,
        relative_path
    ):

        relative_path = self._safe_string(
            relative_path
        )

        if not relative_path:
            return None

        relative_path = relative_path.replace(
            "\\",
            "/"
        )

        raw_path = Path(
            relative_path
        )

        possible_paths = []

        # Absolute path
        if raw_path.is_absolute():

            possible_paths.append(
                raw_path
            )

        # Normal dataset-relative path
        possible_paths.append(
            self.dataset_path
            / raw_path
        )

        # Project-root-relative path
        possible_paths.append(
            self.dataset_path.parent
            / raw_path
        )

        # Media folder fallback
        possible_paths.append(
            self.dataset_path
            / "media"
            / raw_path.name
        )

        # Images fallback
        possible_paths.append(
            self.dataset_path
            / "media"
            / "images"
            / raw_path.name
        )

        # Audio fallback
        possible_paths.append(
            self.dataset_path
            / "media"
            / "audio"
            / raw_path.name
        )

        for path in possible_paths:

            try:
                if path.exists():

                    return path.resolve()

            except Exception:
                continue

        return None

    # ============================================================
    # IMAGE LOOKUP
    # ============================================================

    def _find_image_row(
        self,
        media_id="",
        message_id=""
    ):

        if self.images_df.empty:
            return None

        media_id = self._safe_string(
            media_id
        )

        message_id = self._safe_string(
            message_id
        )

        # Try image ID first
        if media_id:

            image_id_column = (
                self._find_existing_column(
                    self.images_df,
                    [
                        "image_id",
                        "media_id",
                        "id",
                    ]
                )
            )

            if image_id_column:

                matches = self.images_df[
                    self.images_df[
                        image_id_column
                    ]
                    .astype(str)
                    .str.strip()
                    == media_id
                ]

                if not matches.empty:

                    return (
                        matches.iloc[0]
                        .to_dict()
                    )

        # Fallback: message ID
        if message_id:

            message_id_column = (
                self._find_existing_column(
                    self.images_df,
                    [
                        "message_id",
                        "parent_message_id",
                        "source_message_id",
                    ]
                )
            )

            if message_id_column:

                matches = self.images_df[
                    self.images_df[
                        message_id_column
                    ]
                    .astype(str)
                    .str.strip()
                    == message_id
                ]

                if not matches.empty:

                    return (
                        matches.iloc[0]
                        .to_dict()
                    )

        return None

    def _find_image_path(
        self,
        media_id="",
        message_id=""
    ):

        row = self._find_image_row(
            media_id,
            message_id
        )

        if row is None:
            return None

        file_path = self._get_row_value(
            row,
            [
                "file_path",
                "path",
                "image_path",
                "media_path",
                "filename",
                "file_name",
            ]
        )

        return self._resolve_media_path(
            file_path
        )

    # ============================================================
    # VOICE LOOKUP
    # ============================================================

    def _find_voice_row(
        self,
        media_id="",
        message_id=""
    ):

        if self.voice_notes_df.empty:
            return None

        media_id = self._safe_string(
            media_id
        )

        message_id = self._safe_string(
            message_id
        )

        # Try voice note ID first
        if media_id:

            voice_id_column = (
                self._find_existing_column(
                    self.voice_notes_df,
                    [
                        "voice_note_id",
                        "audio_id",
                        "media_id",
                        "id",
                    ]
                )
            )

            if voice_id_column:

                matches = self.voice_notes_df[
                    self.voice_notes_df[
                        voice_id_column
                    ]
                    .astype(str)
                    .str.strip()
                    == media_id
                ]

                if not matches.empty:

                    return (
                        matches.iloc[0]
                        .to_dict()
                    )

        # Fallback: message ID
        if message_id:

            message_id_column = (
                self._find_existing_column(
                    self.voice_notes_df,
                    [
                        "message_id",
                        "parent_message_id",
                        "source_message_id",
                    ]
                )
            )

            if message_id_column:

                matches = self.voice_notes_df[
                    self.voice_notes_df[
                        message_id_column
                    ]
                    .astype(str)
                    .str.strip()
                    == message_id
                ]

                if not matches.empty:

                    return (
                        matches.iloc[0]
                        .to_dict()
                    )

        return None

    def _find_voice_path(
        self,
        media_id="",
        message_id=""
    ):

        row = self._find_voice_row(
            media_id,
            message_id
        )

        if row is None:
            return None

        file_path = self._get_row_value(
            row,
            [
                "file_path",
                "path",
                "audio_path",
                "voice_path",
                "media_path",
                "filename",
                "file_name",
            ]
        )

        return self._resolve_media_path(
            file_path
        )

    # ============================================================
    # WHISPER MODEL
    # ============================================================

    def _get_whisper_model(
        self
    ):

        if not WHISPER_AVAILABLE:
            return None

        if self._whisper_failed:
            return None

        if self._whisper_model is not None:
            return self._whisper_model

        try:

            print(
                "Loading Whisper model..."
            )

            self._whisper_model = (
                whisper.load_model(
                    "base"
                )
            )

            print(
                "Whisper model loaded."
            )

            return self._whisper_model

        except Exception as error:

            self._whisper_failed = True

            print(
                "WARNING: Whisper model "
                f"could not be loaded: {error}"
            )

            return None

    # ============================================================
    # IMAGE PROCESSING
    # ============================================================

    def process_image(
        self,
        media_id="",
        message_id=""
    ):

        result = {
            "available": False,
            "path": None,
            "format": None,
            "width": None,
            "height": None,
            "mode": None,
            "ocr_text": "",
            "error": None,
        }

        image_path = self._find_image_path(
            media_id,
            message_id
        )

        if image_path is None:

            result["error"] = (
                "Image file not found. "
                f"media_id={media_id}, "
                f"message_id={message_id}"
            )

            return result

        result["path"] = str(
            image_path
        )

        try:

            with Image.open(
                image_path
            ) as image:

                result["available"] = True

                result["format"] = (
                    image.format
                )

                result["width"] = (
                    image.width
                )

                result["height"] = (
                    image.height
                )

                result["mode"] = (
                    image.mode
                )

                if not OCR_AVAILABLE:

                    result["error"] = (
                        "OCR is unavailable. "
                        "Tesseract was not found."
                    )

                    return result

                try:

                    # Improve OCR reliability.
                    working_image = (
                        ImageOps.exif_transpose(
                            image
                        )
                    )

                    if working_image.mode != "RGB":

                        working_image = (
                            working_image.convert(
                                "RGB"
                            )
                        )

                    ocr_text = (
                        pytesseract.image_to_string(
                            working_image,
                            config="--psm 6"
                        )
                    )

                    ocr_text = (
                        self._clean_text(
                            ocr_text
                        )
                    )

                    result["ocr_text"] = (
                        ocr_text
                    )

                except Exception as error:

                    result["error"] = (
                        f"OCR failed: {error}"
                    )

        except Exception as error:

            result["error"] = str(
                error
            )

        return result

    # ============================================================
    # VOICE PROCESSING
    # ============================================================

    def process_voice(
        self,
        media_id="",
        message_id=""
    ):

        result = {
            "available": False,
            "path": None,
            "transcript": "",
            "error": None,
        }

        # --------------------------------------------------------
        # First check whether a transcript already exists in CSV
        # --------------------------------------------------------

        voice_row = self._find_voice_row(
            media_id,
            message_id
        )

        if voice_row is not None:

            existing_transcript = (
                self._get_row_value(
                    voice_row,
                    [
                        "transcript",
                        "transcription",
                        "text",
                        "voice_text",
                        "extracted_text",
                    ]
                )
            )

            if existing_transcript:

                result["available"] = True

                result["transcript"] = (
                    self._clean_text(
                        existing_transcript
                    )
                )

                return result

        # --------------------------------------------------------
        # Find audio file
        # --------------------------------------------------------

        voice_path = self._find_voice_path(
            media_id,
            message_id
        )

        if voice_path is None:

            result["error"] = (
                "Voice file not found. "
                f"media_id={media_id}, "
                f"message_id={message_id}"
            )

            return result

        result["available"] = True

        result["path"] = str(
            voice_path
        )

        model = self._get_whisper_model()

        if model is None:

            result["error"] = (
                "Whisper transcription is unavailable. "
                "Install openai-whisper and ensure "
                "FFmpeg is available."
            )

            return result

        try:

            transcription = (
                model.transcribe(
                    str(voice_path),
                    fp16=False
                )
            )

            transcript = (
                transcription.get(
                    "text",
                    ""
                )
            )

            transcript = (
                self._clean_text(
                    transcript
                )
            )

            if transcript:

                result["transcript"] = (
                    transcript
                )

            else:

                result["error"] = (
                    "Voice transcription "
                    "returned empty text."
                )

        except Exception as error:

            result["error"] = (
                "Voice transcription failed: "
                f"{error}"
            )

        return result

    # ============================================================
    # MAIN MESSAGE PROCESSOR
    # ============================================================

    def process_message(
        self,
        message
    ):

        if isinstance(
            message,
            pd.Series
        ):

            message = (
                message.to_dict()
            )

        message_id = self._safe_string(
            message.get(
                "message_id",
                ""
            )
        )

        raw_media_type = (
            self._safe_string(
                message.get(
                    "media_type",
                    ""
                )
            )
            .lower()
        )

        media_id = self._safe_string(
            message.get(
                "media_id",
                ""
            )
        )

        # --------------------------------------------------------
        # Normalize media type
        # --------------------------------------------------------

        image_types = [
            "image",
            "photo",
            "picture",
            "img",
        ]

        voice_types = [
            "voice",
            "voice_note",
            "voicenote",
            "audio",
            "audio_note",
            "voice message",
        ]

        if raw_media_type in image_types:

            media_type = "image"

        elif raw_media_type in voice_types:

            media_type = "voice"

        else:

            media_type = raw_media_type

        result = {
            "media_type": media_type,
            "media_id": media_id,
            "message_id": message_id,
            "summary": "",
            "image": None,
            "voice": None,
            "extracted_text": "",
        }

        # --------------------------------------------------------
        # IMAGE
        # --------------------------------------------------------

        if media_type == "image":

            image_info = (
                self.process_image(
                    media_id=media_id,
                    message_id=message_id
                )
            )

            result["image"] = (
                image_info
            )

            if image_info.get(
                "ocr_text"
            ):

                result[
                    "extracted_text"
                ] = (
                    image_info[
                        "ocr_text"
                    ]
                )

                result["summary"] = (
                    "Image OCR text: "
                    + image_info[
                        "ocr_text"
                    ]
                )

            elif image_info.get(
                "available"
            ):

                result["summary"] = (
                    "Image attached. "
                    "No readable text was extracted."
                )

            else:

                result["summary"] = (
                    "Image attached, but "
                    "the file could not be read."
                )

        # --------------------------------------------------------
        # VOICE
        # --------------------------------------------------------

        elif media_type == "voice":

            voice_info = (
                self.process_voice(
                    media_id=media_id,
                    message_id=message_id
                )
            )

            result["voice"] = (
                voice_info
            )

            if voice_info.get(
                "transcript"
            ):

                result[
                    "extracted_text"
                ] = (
                    voice_info[
                        "transcript"
                    ]
                )

                result["summary"] = (
                    "Voice transcript: "
                    + voice_info[
                        "transcript"
                    ]
                )

            elif voice_info.get(
                "available"
            ):

                result["summary"] = (
                    "Voice note attached, "
                    "but transcription "
                    "could not be completed."
                )

            else:

                result["summary"] = (
                    "Voice note attached, "
                    "but the audio file "
                    "could not be found."
                )

        # --------------------------------------------------------
        # NO MEDIA
        # --------------------------------------------------------

        else:

            result["summary"] = (
                "No supported media attached."
            )

        return result


# ================================================================
# DIRECT TEST
# ================================================================

if __name__ == "__main__":

    print("=" * 70)
    print(
        "MULTIMODAL PROCESSOR TEST"
    )
    print("=" * 70)

    processor = (
        MultimodalProcessor()
    )

    print("\nIMAGE TESTS")

    image_tests = [
        "img_008",
        "img_011",
        "img_026",
    ]

    for media_id in image_tests:

        print("\n" + "-" * 70)

        print(
            f"Testing image: "
            f"{media_id}"
        )

        result = (
            processor.process_image(
                media_id=media_id
            )
        )

        print(
            "Available:",
            result["available"]
        )

        print(
            "Path:",
            result["path"]
        )

        print(
            "OCR Text:",
            result["ocr_text"]
        )

        print(
            "Error:",
            result["error"]
        )

    print("\nVOICE TESTS")

    voice_tests = [
        "vn_001",
        "vn_002",
        "vn_003",
    ]

    for media_id in voice_tests:

        print("\n" + "-" * 70)

        print(
            f"Testing voice: "
            f"{media_id}"
        )

        result = (
            processor.process_voice(
                media_id=media_id
            )
        )

        print(
            "Available:",
            result["available"]
        )

        print(
            "Path:",
            result["path"]
        )

        print(
            "Transcript:",
            result["transcript"]
        )

        print(
            "Error:",
            result["error"]
        )

    print("\n" + "=" * 70)
    print(
        "MULTIMODAL TEST COMPLETED"
    )
    print("=" * 70)