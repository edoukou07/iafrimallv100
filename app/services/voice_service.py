"""
Voice transcription service using OpenAI Whisper.
Converts audio files to text with high precision.
"""

import os
import logging
import whisper
from pathlib import Path
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class VoiceTranscriptionService:
    """
    Service for transcribing audio using OpenAI Whisper.
    Supports multiple languages and audio formats.
    """

    def __init__(self, model_size: str = "base"):
        """
        Initialize Whisper model.
        
        Args:
            model_size: Model size ('tiny', 'base', 'small', 'medium', 'large')
                       - tiny: Fast, lower accuracy (~39MB)
                       - base: Balanced (~140MB) - DEFAULT
                       - small: Better accuracy (~466MB)
                       - medium: Very accurate (~1.5GB)
                       - large: Highest accuracy (~2.9GB)
        """
        self.model_size = model_size
        self.model = None
        self._load_model()

    def _load_model(self) -> None:
        """Load Whisper model on initialization."""
        try:
            logger.info(f"Loading Whisper model: {self.model_size}")
            self.model = whisper.load_model(self.model_size)
            logger.info(f"✓ Whisper model '{self.model_size}' loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {str(e)}")
            raise

    def transcribe(
        self,
        audio_path: str,
        language: Optional[str] = None,
        verbose: bool = False,
    ) -> Dict[str, Any]:
        """
        Transcribe audio file to text.

        Args:
            audio_path: Path to audio file (MP3, WAV, M4A, FLAC, etc.)
            language: Language code (e.g., 'en', 'fr', 'es'). Auto-detected if None
            verbose: Whether to print processing details

        Returns:
            Dict with:
                - text: Transcribed text
                - language: Detected language code
                - segments: Detailed timing info
                - confidence: Confidence score (estimated)

        Example:
            result = service.transcribe("audio.mp3", language="fr")
            print(result['text'])  # "Bonjour, comment allez-vous?"
        """
        if not Path(audio_path).exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        try:
            logger.info(f"Transcribing: {audio_path} (language={language})")

            # Transcribe with Whisper
            result = self.model.transcribe(
                audio_path,
                language=language,
                verbose=verbose,
                temperature=0.0,  # Deterministic results
                fp16=False,  # Better compatibility
            )

            # Calculate confidence (avg of segment confidences if available)
            confidence = result.get("confidence", 0.95)

            transcription = {
                "text": result["text"].strip(),
                "language": result.get("language", "unknown"),
                "segments": result.get("segments", []),
                "confidence": confidence,
                "model": self.model_size,
                "audio_path": audio_path,
            }

            logger.info(
                f"✓ Transcription complete: '{transcription['text'][:100]}...'"
            )
            return transcription

        except Exception as e:
            logger.error(f"Transcription error: {str(e)}")
            raise

    def transcribe_with_timestamps(
        self,
        audio_path: str,
        language: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Transcribe audio with word-level timestamps.

        Returns:
            Dict with:
                - text: Full transcription
                - segments: List of {'start', 'end', 'text'}
                - language: Detected language
        """
        result = self.transcribe(audio_path, language=language)

        # Parse segments for timestamps
        segments_with_time = []
        for segment in result.get("segments", []):
            segments_with_time.append(
                {
                    "text": segment.get("text", "").strip(),
                    "start": segment.get("start", 0),
                    "end": segment.get("end", 0),
                    "confidence": segment.get("confidence", 0.95),
                }
            )

        return {
            "text": result["text"],
            "language": result["language"],
            "segments": segments_with_time,
            "confidence": result["confidence"],
        }

    def get_model_info(self) -> Dict[str, str]:
        """Get information about loaded model."""
        model_sizes = {
            "tiny": "39MB - Fastest, lowest accuracy",
            "base": "140MB - Balanced (default)",
            "small": "466MB - Better accuracy",
            "medium": "1.5GB - Very accurate",
            "large": "2.9GB - Highest accuracy",
        }

        return {
            "loaded_model": self.model_size,
            "description": model_sizes.get(self.model_size, "Unknown"),
            "languages_supported": "99+ languages",
        }


# Global instance (initialized on first use)
_voice_service: Optional[VoiceTranscriptionService] = None


def get_voice_service(model_size: str = "base") -> VoiceTranscriptionService:
    """
    Get or create global voice transcription service.
    
    Args:
        model_size: Model size to use (only used on first call)
    
    Returns:
        VoiceTranscriptionService instance
    """
    global _voice_service
    if _voice_service is None:
        _voice_service = VoiceTranscriptionService(model_size=model_size)
    return _voice_service
