import torch
from transformers import pipeline
import librosa
import numpy as np
from typing import Dict, List, Tuple, Optional
import logging
from pathlib import Path
import time

from ..core.config import settings

logger = logging.getLogger(__name__)

class TranscriptionService:
    """Advanced speech-to-text transcription service using Whisper."""
    
    def __init__(self, model_size: str = "small"):
        """
        Initialize transcription service.
        
        Args:
            model_size: Whisper model size (tiny, base, small, medium, large)
        """
        self.device = "cuda:0" if torch.cuda.is_available() else "cpu"
        self.model_size = model_size
        self.pipe = None
        self._load_model()
    
    def _load_model(self):
        """Load the Whisper model."""
        try:
            model_name = f"openai/whisper-{self.model_size}"
            logger.info(f"Loading Whisper model: {model_name} on {self.device}")
            
            self.pipe = pipeline(
                "automatic-speech-recognition",
                model=model_name,
                device=self.device,
                return_timestamps=True
            )
            logger.info("Whisper model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {str(e)}")
            raise
    
    def transcribe_audio(
        self, 
        audio_path: str, 
        language: str = "en",
        chunk_length_s: int = 30,
        return_segments: bool = True
    ) -> Dict:
        """
        Transcribe audio file to text with timestamps.
        
        Args:
            audio_path: Path to audio file
            language: Language code (en, es, fr, etc.)
            chunk_length_s: Chunk length in seconds for long audio
            return_segments: Whether to return segmented transcript
            
        Returns:
            Dictionary with transcript, segments, and metadata
        """
        start_time = time.time()
        
        try:
            logger.info(f"Starting transcription of {audio_path}")
            
            # Load and preprocess audio
            audio_array = self._preprocess_audio(audio_path)
            
            # Configure generation arguments
            generate_kwargs = {
                "language": language,
                "task": "transcribe"
            }
            
            # Transcribe with timestamps
            result = self.pipe(
                audio_array,
                chunk_length_s=chunk_length_s,
                generate_kwargs=generate_kwargs,
                return_timestamps=return_segments
            )
            
            # Process results
            transcript_data = self._process_results(result, start_time)
            
            logger.info(f"Transcription completed in {transcript_data['processing_time']:.2f}s")
            return transcript_data
            
        except Exception as e:
            logger.error(f"Transcription failed: {str(e)}")
            raise
    
    def _preprocess_audio(self, audio_path: str) -> np.ndarray:
        """Preprocess audio for optimal transcription."""
        try:
            # Load audio with optimal settings for Whisper
            audio, sr = librosa.load(
                audio_path, 
                sr=16000,  # Whisper expects 16kHz
                mono=True
            )
            
            # Normalize audio
            audio = librosa.util.normalize(audio)
            
            return audio
            
        except Exception as e:
            logger.error(f"Audio preprocessing failed: {str(e)}")
            raise
    
    def _process_results(self, result: Dict, start_time: float) -> Dict:
        """Process and format transcription results."""
        processing_time = time.time() - start_time
        
        # Extract main transcript
        full_text = result.get("text", "")
        
        # Process segments if available
        segments = []
        word_count = 0
        confidence_scores = []
        
        if "chunks" in result:
            for chunk in result["chunks"]:
                segment = {
                    "text": chunk.get("text", ""),
                    "start_time": chunk.get("timestamp", [0, 0])[0] or 0,
                    "end_time": chunk.get("timestamp", [0, 0])[1] or 0,
                }
                segments.append(segment)
                word_count += len(segment["text"].split())
        else:
            word_count = len(full_text.split())
        
        # Calculate average confidence (if available)
        avg_confidence = np.mean(confidence_scores) if confidence_scores else None
        
        return {
            "full_text": full_text.strip(),
            "segments": segments,
            "word_count": word_count,
            "processing_time": processing_time,
            "confidence_score": avg_confidence,
            "language_detected": result.get("language", "en"),
            "model_used": f"whisper-{self.model_size}"
        }
    
    def transcribe_with_speaker_timestamps(
        self, 
        audio_path: str, 
        speaker_segments: List[Dict]
    ) -> Dict:
        """
        Transcribe audio with speaker information from diarization.
        
        Args:
            audio_path: Path to audio file
            speaker_segments: Speaker diarization results
            
        Returns:
            Transcript with speaker labels
        """
        try:
            logger.info("Starting speaker-aware transcription")
            
            # Load full audio
            audio, sr = librosa.load(audio_path, sr=16000, mono=True)
            
            speaker_transcript = []
            
            for segment in speaker_segments:
                start_time = segment["start"]
                end_time = segment["end"]
                speaker_label = segment["speaker"]
                
                # Extract audio segment
                start_sample = int(start_time * sr)
                end_sample = int(end_time * sr)
                audio_segment = audio[start_sample:end_sample]
                
                if len(audio_segment) > 0:
                    # Transcribe segment
                    result = self.pipe(audio_segment)
                    text = result.get("text", "").strip()
                    
                    if text:
                        speaker_transcript.append({
                            "speaker": speaker_label,
                            "start_time": start_time,
                            "end_time": end_time,
                            "text": text
                        })
            
            # Combine into full transcript
            full_text = "\n".join([
                f"{seg['speaker']}: {seg['text']}" 
                for seg in speaker_transcript
            ])
            
            return {
                "full_text": full_text,
                "segments": speaker_transcript,
                "word_count": len(full_text.split()),
                "speaker_count": len(set(seg["speaker"] for seg in speaker_transcript))
            }
            
        except Exception as e:
            logger.error(f"Speaker-aware transcription failed: {str(e)}")
            raise
    
    def get_supported_languages(self) -> List[str]:
        """Get list of supported languages."""
        return [
            "en", "es", "fr", "de", "it", "pt", "ru", "ja", "ko", "zh",
            "ar", "hi", "nl", "pl", "tr", "sv", "da", "no", "fi"
        ]
    
    def estimate_processing_time(self, audio_duration: float) -> float:
        """Estimate processing time for given audio duration."""
        # Rough estimate: Whisper processes at ~10x real-time on CPU, ~30x on GPU
        multiplier = 0.1 if self.device == "cpu" else 0.033
        return audio_duration * multiplier