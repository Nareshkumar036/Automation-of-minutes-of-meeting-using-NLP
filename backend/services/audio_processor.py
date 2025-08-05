import librosa
import noisereduce as nr
import soundfile as sf
import numpy as np
from pathlib import Path
from typing import Tuple, Optional
import logging

from ..core.config import settings

logger = logging.getLogger(__name__)

class AudioProcessor:
    """Audio preprocessing and optimization service."""
    
    def __init__(self, target_sr: int = None):
        self.target_sr = target_sr or settings.DEFAULT_SAMPLE_RATE
    
    def process_audio_file(self, input_path: str, output_path: str = None) -> Tuple[str, dict]:
        """
        Process audio file with noise reduction and optimization.
        
        Args:
            input_path: Path to input audio file
            output_path: Optional output path, auto-generated if None
            
        Returns:
            Tuple of (output_path, metadata)
        """
        try:
            # Load audio
            audio, sr = librosa.load(input_path, sr=self.target_sr, mono=True)
            logger.info(f"Loaded audio: {len(audio)/sr:.2f}s at {sr}Hz")
            
            # Get metadata before processing
            original_duration = len(audio) / sr
            
            # Apply noise reduction
            audio_cleaned = self._reduce_noise(audio, sr)
            
            # Normalize audio
            audio_normalized = self._normalize_audio(audio_cleaned)
            
            # Trim silence
            audio_trimmed, (start_trim, end_trim) = self._trim_silence(audio_normalized)
            
            # Generate output path if not provided
            if output_path is None:
                input_path_obj = Path(input_path)
                output_path = str(input_path_obj.parent / f"processed_{input_path_obj.name}")
            
            # Save processed audio
            sf.write(output_path, audio_trimmed, sr, subtype='PCM_16')
            
            # Prepare metadata
            metadata = {
                "original_duration": original_duration,
                "processed_duration": len(audio_trimmed) / sr,
                "sample_rate": sr,
                "trim_start": start_trim,
                "trim_end": end_trim,
                "channels": 1,
                "format": "wav"
            }
            
            logger.info(f"Audio processed successfully: {output_path}")
            return output_path, metadata
            
        except Exception as e:
            logger.error(f"Error processing audio: {str(e)}")
            raise
    
    def _reduce_noise(self, audio: np.ndarray, sr: int) -> np.ndarray:
        """Apply noise reduction to audio."""
        try:
            return nr.reduce_noise(
                y=audio,
                sr=sr,
                stationary=True,
                prop_decrease=0.8,
                n_fft=512,
                win_length=256,
                hop_length=128
            )
        except Exception as e:
            logger.warning(f"Noise reduction failed: {str(e)}, returning original audio")
            return audio
    
    def _normalize_audio(self, audio: np.ndarray) -> np.ndarray:
        """Normalize audio amplitude."""
        return librosa.util.normalize(audio)
    
    def _trim_silence(self, audio: np.ndarray, top_db: int = 20) -> Tuple[np.ndarray, Tuple[int, int]]:
        """Trim silence from beginning and end of audio."""
        try:
            audio_trimmed, index = librosa.effects.trim(audio, top_db=top_db)
            return audio_trimmed, (index[0], len(audio) - index[1])
        except Exception as e:
            logger.warning(f"Silence trimming failed: {str(e)}, returning original audio")
            return audio, (0, 0)
    
    def get_audio_info(self, file_path: str) -> dict:
        """Get metadata about audio file without loading full content."""
        try:
            # Load just a small sample to get info
            audio, sr = librosa.load(file_path, sr=None, duration=0.1)
            
            # Get file size
            file_size = Path(file_path).stat().st_size
            
            # Calculate full duration
            total_frames = librosa.get_duration(filename=file_path)
            
            return {
                "duration": total_frames,
                "sample_rate": sr,
                "file_size": file_size,
                "format": Path(file_path).suffix.lower(),
                "estimated_words": int(total_frames * 150 / 60)  # Rough estimate: 150 words/minute
            }
        except Exception as e:
            logger.error(f"Error getting audio info: {str(e)}")
            return {}
    
    def convert_to_wav(self, input_path: str, output_path: str = None) -> str:
        """Convert audio file to WAV format."""
        try:
            # Load and resave as WAV
            audio, sr = librosa.load(input_path, sr=self.target_sr, mono=True)
            
            if output_path is None:
                input_path_obj = Path(input_path)
                output_path = str(input_path_obj.parent / f"{input_path_obj.stem}.wav")
            
            sf.write(output_path, audio, sr, subtype='PCM_16')
            logger.info(f"Converted to WAV: {output_path}")
            
            return output_path
        except Exception as e:
            logger.error(f"Error converting to WAV: {str(e)}")
            raise