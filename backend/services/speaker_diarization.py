import torch
import librosa
import numpy as np
from typing import Dict, List, Tuple, Optional
import logging
from pathlib import Path
import time

try:
    from pyannote.audio import Pipeline
    PYANNOTE_AVAILABLE = True
except ImportError:
    PYANNOTE_AVAILABLE = False
    logging.warning("pyannote.audio not available. Speaker diarization will use fallback method.")

from ..core.config import settings

logger = logging.getLogger(__name__)

class SpeakerDiarization:
    """Speaker identification and diarization service."""
    
    def __init__(self):
        """Initialize speaker diarization service."""
        self.pipeline = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        if PYANNOTE_AVAILABLE and settings.PYANNOTE_ACCESS_TOKEN:
            self._load_pyannote_pipeline()
        else:
            logger.info("Using fallback speaker detection method")
    
    def _load_pyannote_pipeline(self):
        """Load pyannote speaker diarization pipeline."""
        try:
            # Load pre-trained speaker diarization pipeline
            self.pipeline = Pipeline.from_pretrained(
                "pyannote/speaker-diarization-3.1",
                use_auth_token=settings.PYANNOTE_ACCESS_TOKEN
            )
            
            # Move to GPU if available
            if self.device == "cuda":
                self.pipeline.to(torch.device("cuda"))
            
            logger.info(f"Pyannote pipeline loaded successfully on {self.device}")
            
        except Exception as e:
            logger.error(f"Failed to load pyannote pipeline: {str(e)}")
            self.pipeline = None
    
    def diarize_speakers(self, audio_path: str, num_speakers: Optional[int] = None) -> Dict:
        """
        Perform speaker diarization on audio file.
        
        Args:
            audio_path: Path to audio file
            num_speakers: Expected number of speakers (optional)
            
        Returns:
            Dictionary with speaker segments and metadata
        """
        start_time = time.time()
        
        try:
            logger.info(f"Starting speaker diarization for {audio_path}")
            
            if self.pipeline:
                result = self._diarize_with_pyannote(audio_path, num_speakers)
            else:
                result = self._diarize_with_fallback(audio_path, num_speakers)
            
            # Add processing metadata
            result.update({
                "processing_time": time.time() - start_time,
                "method": "pyannote" if self.pipeline else "fallback"
            })
            
            logger.info(f"Speaker diarization completed in {result['processing_time']:.2f}s")
            return result
            
        except Exception as e:
            logger.error(f"Speaker diarization failed: {str(e)}")
            raise
    
    def _diarize_with_pyannote(self, audio_path: str, num_speakers: Optional[int] = None) -> Dict:
        """Perform diarization using pyannote.audio."""
        try:
            # Run the pipeline
            if num_speakers:
                diarization = self.pipeline(audio_path, num_speakers=num_speakers)
            else:
                diarization = self.pipeline(audio_path)
            
            # Process results
            segments = []
            speakers = set()
            
            for turn, _, speaker in diarization.itertracks(yield_label=True):
                segments.append({
                    "start": turn.start,
                    "end": turn.end,
                    "speaker": speaker,
                    "duration": turn.end - turn.start
                })
                speakers.add(speaker)
            
            # Calculate speaker statistics
            speaker_stats = self._calculate_speaker_stats(segments)
            
            return {
                "segments": segments,
                "num_speakers": len(speakers),
                "speakers": list(speakers),
                "speaker_stats": speaker_stats,
                "total_speech_time": sum(seg["duration"] for seg in segments)
            }
            
        except Exception as e:
            logger.error(f"Pyannote diarization failed: {str(e)}")
            raise
    
    def _diarize_with_fallback(self, audio_path: str, num_speakers: Optional[int] = None) -> Dict:
        """Fallback speaker diarization using simple voice activity detection."""
        try:
            logger.info("Using fallback speaker detection method")
            
            # Load audio
            audio, sr = librosa.load(audio_path, sr=16000, mono=True)
            
            # Simple voice activity detection
            frame_length = 2048
            hop_length = 512
            
            # Compute short-time energy
            energy = librosa.feature.rms(
                y=audio, 
                frame_length=frame_length, 
                hop_length=hop_length
            )[0]
            
            # Detect speech segments
            speech_segments = self._detect_speech_segments(
                energy, sr, hop_length, threshold=0.01
            )
            
            # Simple speaker assignment (alternating speakers for demonstration)
            segments = []
            current_speaker = 0
            num_speakers_estimate = num_speakers or min(3, max(1, len(speech_segments) // 5))
            
            for i, (start, end) in enumerate(speech_segments):
                # Simple heuristic: change speaker every few segments
                if i > 0 and i % 3 == 0:
                    current_speaker = (current_speaker + 1) % num_speakers_estimate
                
                segments.append({
                    "start": start,
                    "end": end,
                    "speaker": f"SPEAKER_{current_speaker:02d}",
                    "duration": end - start
                })
            
            # Calculate speaker statistics
            speakers = list(set(seg["speaker"] for seg in segments))
            speaker_stats = self._calculate_speaker_stats(segments)
            
            return {
                "segments": segments,
                "num_speakers": len(speakers),
                "speakers": speakers,
                "speaker_stats": speaker_stats,
                "total_speech_time": sum(seg["duration"] for seg in segments),
                "note": "Fallback method used - accuracy may be limited"
            }
            
        except Exception as e:
            logger.error(f"Fallback diarization failed: {str(e)}")
            raise
    
    def _detect_speech_segments(
        self, 
        energy: np.ndarray, 
        sr: int, 
        hop_length: int, 
        threshold: float = 0.01,
        min_duration: float = 0.5
    ) -> List[Tuple[float, float]]:
        """Detect speech segments using energy-based voice activity detection."""
        
        # Smooth energy signal
        from scipy import ndimage
        energy_smooth = ndimage.gaussian_filter1d(energy, sigma=2)
        
        # Threshold energy to find speech regions
        speech_frames = energy_smooth > threshold
        
        # Convert frame indices to time
        times = librosa.frames_to_time(
            np.arange(len(speech_frames)), 
            sr=sr, 
            hop_length=hop_length
        )
        
        # Find continuous speech segments
        segments = []
        in_speech = False
        start_time = 0
        
        for i, is_speech in enumerate(speech_frames):
            if is_speech and not in_speech:
                # Start of speech segment
                start_time = times[i]
                in_speech = True
            elif not is_speech and in_speech:
                # End of speech segment
                end_time = times[i]
                duration = end_time - start_time
                
                # Only keep segments longer than minimum duration
                if duration >= min_duration:
                    segments.append((start_time, end_time))
                
                in_speech = False
        
        # Handle case where speech continues to end of audio
        if in_speech:
            segments.append((start_time, times[-1]))
        
        return segments
    
    def _calculate_speaker_stats(self, segments: List[Dict]) -> Dict:
        """Calculate speaking statistics for each speaker."""
        speaker_stats = {}
        
        for segment in segments:
            speaker = segment["speaker"]
            duration = segment["duration"]
            
            if speaker not in speaker_stats:
                speaker_stats[speaker] = {
                    "total_time": 0,
                    "segment_count": 0,
                    "average_segment_length": 0
                }
            
            speaker_stats[speaker]["total_time"] += duration
            speaker_stats[speaker]["segment_count"] += 1
        
        # Calculate averages
        for speaker, stats in speaker_stats.items():
            if stats["segment_count"] > 0:
                stats["average_segment_length"] = stats["total_time"] / stats["segment_count"]
                stats["percentage"] = (stats["total_time"] / sum(
                    seg["duration"] for seg in segments
                )) * 100
        
        return speaker_stats
    
    def assign_speaker_names(
        self, 
        segments: List[Dict], 
        speaker_mapping: Dict[str, str]
    ) -> List[Dict]:
        """
        Assign human-readable names to speaker labels.
        
        Args:
            segments: List of speaker segments
            speaker_mapping: Dict mapping speaker labels to names
            
        Returns:
            Updated segments with speaker names
        """
        updated_segments = []
        
        for segment in segments:
            updated_segment = segment.copy()
            speaker_label = segment["speaker"]
            
            if speaker_label in speaker_mapping:
                updated_segment["speaker_name"] = speaker_mapping[speaker_label]
            else:
                updated_segment["speaker_name"] = speaker_label
            
            updated_segments.append(updated_segment)
        
        return updated_segments
    
    def merge_short_segments(
        self, 
        segments: List[Dict], 
        min_duration: float = 1.0
    ) -> List[Dict]:
        """
        Merge very short segments with adjacent segments from the same speaker.
        
        Args:
            segments: List of speaker segments
            min_duration: Minimum segment duration in seconds
            
        Returns:
            List of merged segments
        """
        if not segments:
            return segments
        
        merged_segments = [segments[0]]
        
        for current_segment in segments[1:]:
            last_segment = merged_segments[-1]
            
            # If current segment is very short and same speaker as previous
            if (current_segment["duration"] < min_duration and 
                current_segment["speaker"] == last_segment["speaker"]):
                
                # Merge with previous segment
                last_segment["end"] = current_segment["end"]
                last_segment["duration"] = last_segment["end"] - last_segment["start"]
            else:
                merged_segments.append(current_segment)
        
        return merged_segments
    
    def get_speaker_embeddings(self, audio_path: str, segments: List[Dict]) -> Dict:
        """
        Extract speaker embeddings for future speaker recognition.
        
        Args:
            audio_path: Path to audio file
            segments: Speaker segments
            
        Returns:
            Dictionary of speaker embeddings
        """
        try:
            if not self.pipeline:
                logger.warning("Speaker embeddings require pyannote.audio")
                return {}
            
            # Load audio
            audio, sr = librosa.load(audio_path, sr=16000, mono=True)
            
            speaker_embeddings = {}
            
            for segment in segments:
                speaker = segment["speaker"]
                start_sample = int(segment["start"] * sr)
                end_sample = int(segment["end"] * sr)
                
                # Extract audio segment
                audio_segment = audio[start_sample:end_sample]
                
                if len(audio_segment) > sr * 0.5:  # At least 0.5 seconds
                    # Extract embedding (simplified - in practice you'd use a proper embedding model)
                    # For now, just use basic spectral features as a placeholder
                    mfcc = librosa.feature.mfcc(y=audio_segment, sr=sr, n_mfcc=13)
                    embedding = np.mean(mfcc, axis=1).tolist()
                    
                    if speaker not in speaker_embeddings:
                        speaker_embeddings[speaker] = []
                    
                    speaker_embeddings[speaker].append(embedding)
            
            # Average embeddings for each speaker
            averaged_embeddings = {}
            for speaker, embeddings in speaker_embeddings.items():
                if embeddings:
                    averaged_embeddings[speaker] = np.mean(embeddings, axis=0).tolist()
            
            return averaged_embeddings
            
        except Exception as e:
            logger.error(f"Failed to extract speaker embeddings: {str(e)}")
            return {}