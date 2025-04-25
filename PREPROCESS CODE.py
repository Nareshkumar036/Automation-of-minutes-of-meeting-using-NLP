import ipywidgets as widgets
from IPython.display import display, Audio, clear_output
import os
import librosa
import noisereduce as nr
import soundfile as sf
from pathlib import Path
import datetime

# Create directories if they don't exist
UPLOAD_DIR = "original_audio"
PROCESSED_DIR = "cleaned_audio"
Path(UPLOAD_DIR).mkdir(exist_ok=True)
Path(PROCESSED_DIR).mkdir(exist_ok=True)

def on_upload_change(change):
    if change['type'] == 'change' and change['name'] == 'value':
        clear_output()

        # Get uploaded file info
        file_name = next(iter(change['new'].keys()))
        file_content = change['new'][file_name]['content']

        # Save original file
        original_path = Path(UPLOAD_DIR) / file_name
        with open(original_path, 'wb') as f:
            f.write(file_content)

        # Process and save cleaned audio
        output_path = process_and_save_audio(original_path)

        # Display results
        print("🔊 Audio Processing Complete")
        print(f"📥 Original file saved to: {original_path.absolute()}")
        print(f"✨ Cleaned file saved to: {output_path.absolute()}")
        print("\n🎧 Processed Audio Preview:")
        display(Audio(filename=str(output_path)))

def process_and_save_audio(input_path, target_sr=16000):
    """Process audio and save with timestamp"""
    # Generate output filename with timestamp
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    input_stem = Path(input_path).stem
    output_filename = f"cleaned_{input_stem}_{timestamp}.wav"
    output_path = Path(PROCESSED_DIR) / output_filename

    # Load and process audio
    audio, sr = librosa.load(input_path, sr=target_sr, mono=True)

    # Noise reduction
    audio = nr.reduce_noise(
        y=audio,
        sr=sr,
        stationary=True,
        prop_decrease=0.8,
        n_fft=512,
        win_length=256,
        hop_length=128
    )

    # Save as WAV file
    sf.write(output_path, audio, sr, subtype='PCM_16')
    return output_path

# Create upload widget
uploader = widgets.FileUpload(
    accept='.wav,.mp3,.flac,.webm,.ogg',
    multiple=False,
    description='Upload Audio',
    style={'description_width': 'initial'}
)

# Display interface
print(f"🗂️ Original files will be saved in: {Path(UPLOAD_DIR).absolute()}")
print(f"✨ Cleaned files will be saved in: {Path(PROCESSED_DIR).absolute()}")
print("\n⬇️ Upload an audio file to process:")
uploader.observe(on_upload_change, names='value')
display(uploader)
