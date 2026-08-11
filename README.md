# 📋 MoM AI Generator

### Automated Minutes of Meeting from Meeting Audio using AI & NLP

**MoM AI Generator** is an end-to-end application that automatically converts meeting audio into structured and professional **Minutes of Meeting (MoM)**.

The system accepts meeting recordings, transcribes the conversation using **OpenAI Whisper**, processes the transcript using NLP techniques, extracts important meeting information such as **key topics, decisions, and action items**, generates a concise summary, and formats the results into downloadable **Word and Markdown documents**.

It also provides an optional **Gmail email integration** for sending the generated MoM directly to meeting participants.

---

## 🎯 Problem Statement

Preparing Minutes of Meeting manually is time-consuming and can lead to missed discussion points, decisions, and action items.

Meeting recordings often contain a large amount of information that needs to be reviewed before producing a useful summary. This project automates that process by combining **Automatic Speech Recognition (ASR)** with **Natural Language Processing (NLP)**.

The goal is to transform:

**Meeting Audio → Transcript → NLP Analysis → Summary → Structured MoM → Email / Download**

---

## 💡 Solution

MoM AI Generator provides an automated pipeline for converting meeting recordings into structured meeting documentation.

### How it works

1. 🎵 **Audio Upload**

   * Upload a meeting recording.
   * Supported formats include `.mp3`, `.wav`, `.m4a`, and `.ogg`.

2. 🎙️ **Speech-to-Text**

   * OpenAI Whisper converts the meeting audio into text.
   * The application supports Whisper models from `tiny` through `large`.
   * Language can be automatically detected or manually selected.

3. 🧹 **Transcript Preprocessing**

   * Removes unnecessary whitespace.
   * Removes common filler words such as `um`, `uh`, `hmm`, and `erm`.
   * Removes repeated words.
   * Splits long transcripts into manageable chunks.

4. 🧠 **NLP Analysis**

   * Extracts important keywords and topics.
   * Identifies potential action items using predefined NLP patterns.
   * Detects decision and agreement statements.
   * Produces structured meeting insights.

5. 📝 **Text Summarization**

   * Generates a concise summary from the processed transcript.
   * The current implementation includes a lightweight extractive summarization approach based on word frequency and sentence scoring.

6. 📋 **Minutes Generation**

   * Combines the extracted information into a professional MoM.
   * Generates both Markdown and Word (`.docx`) formats.

7. 📧 **Email Delivery**

   * The generated MoM can be sent through Gmail SMTP.
   * The `.docx` document can optionally be attached to the email.

---

## 🏗️ System Architecture

```text
                    ┌──────────────────────┐
                    │    Meeting Audio     │
                    │ mp3 / wav / m4a / ogg│
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │    OpenAI Whisper    │
                    │       ASR            │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │ Transcript Cleaning  │
                    │  & Preprocessing     │
                    └──────────┬───────────┘
                               │
              ┌────────────────┼────────────────┐
              ▼                ▼                ▼
       ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
       │ Key Topics  │  │   Decisions │  │ Action Items│
       │ Extraction  │  │  Extraction │  │  Extraction │
       └─────────────┘  └─────────────┘  └─────────────┘
              │                │                │
              └────────────────┼────────────────┘
                               ▼
                    ┌──────────────────────┐
                    │     Summarization    │
                    │  Extractive NLP      │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │    MoM Formatter     │
                    │ Markdown + DOCX      │
                    └──────────┬───────────┘
                               │
                 ┌─────────────┼─────────────┐
                 ▼             ▼             ▼
          ┌────────────┐ ┌────────────┐ ┌────────────┐
          │  Preview   │ │  Download  │ │    Gmail   │
          │    MoM     │ │ DOCX/MD/TXT│ │    Email   │
          └────────────┘ └────────────┘ └────────────┘
```

The application exposes the complete workflow through Streamlit, including separate sections for uploading/processing audio, viewing the transcript, previewing the MoM, downloading files, and sending email.

---

## ✨ Features

### 🎙️ Automatic Speech Recognition

* Powered by OpenAI Whisper.
* Supports multiple Whisper model sizes:

  * `tiny`
  * `base`
  * `small`
  * `medium`
  * `large`
* Automatic language detection.
* Manual language selection.
* Timestamped transcript display.

### 🧹 NLP Transcript Processing

* Text normalization.
* Repeated-word removal.
* Filler-word removal.
* Sentence segmentation.
* Long transcript chunking.

### 🔑 Key Topic Extraction

The system identifies frequently occurring meaningful words from the transcript and uses them as key meeting topics.

### ⚡ Action Item Extraction

The NLP pipeline detects statements containing action-oriented patterns such as:

* will
* shall
* must
* should
* need to
* follow-up
* task
* deadline
* assigned to
* review
* update
* prepare
* submit

Extracted action items are included in the generated MoM.

### ✅ Decision Extraction

The system detects decision-related statements containing patterns such as:

* decided
* agreed
* confirmed
* approved
* resolved
* finalized
* consensus
* outcome

### 📝 Automatic Summarization

The current summarization module uses an **extractive NLP approach**.

Important sentences are scored using word-frequency information and the highest-scoring sentences are selected to form the summary.

This implementation is intentionally lightweight and does not require downloading a large summarization model.

### 📋 Structured MoM Generation

The generated Minutes of Meeting contains:

* Meeting Details
* Key Topics Discussed
* Attendees
* Agenda
* Meeting Summary
* Discussion Points
* Decisions Made
* Action Items
* Next Meeting

The MoM formatter generates both Markdown content and a professional `.docx` document.

### 📄 Document Export

Generated meeting minutes can be downloaded as:

* `.docx`
* `.md`
* `.txt`

The Word document contains formatted headings, tables, meeting information, action items, decisions, and other meeting sections.

### 📧 Gmail Integration

The application can send the generated MoM through Gmail SMTP.

Features include:

* Multiple recipients
* CC recipients
* HTML-formatted email
* Automatic email subject
* Optional `.docx` attachment
* Gmail App Password authentication

The email module uses Gmail's secure SMTP server on port `465`.

---

## 🛠️ Technology Stack

| Component            | Technology                                         |
| -------------------- | -------------------------------------------------- |
| Programming Language | Python                                             |
| Web Framework        | Streamlit                                          |
| Speech Recognition   | OpenAI Whisper                                     |
| NLP                  | Python / Regular Expressions / Frequency-based NLP |
| Summarization        | Custom Extractive Summarizer                       |
| ML Libraries         | PyTorch, Hugging Face Transformers                 |
| Word Generation      | python-docx                                        |
| Audio Processing     | FFmpeg, Librosa, SoundFile                         |
| Email                | Gmail SMTP                                         |
| Frontend/UI          | Streamlit + HTML/CSS                               |
| Output               | DOCX, Markdown, TXT                                |

The project's dependency configuration includes Streamlit, OpenAI Whisper, Transformers, PyTorch, SentencePiece, Accelerate, python-docx, NumPy, SciPy, SoundFile, Librosa, and tqdm.

---

## 📁 Project Structure

```text
mom-ai-generator/
│
├── app.py
│   └── Main Streamlit application
│
├── transcriber.py
│   └── Whisper speech-to-text processing
│
├── summarizer.py
│   └── Transcript cleaning, summarization,
│       topic extraction, decision extraction,
│       and action-item extraction
│
├── mom_formatter.py
│   └── Generates Markdown and DOCX Minutes of Meeting
│
├── email_sender.py
│   └── Sends MoM through Gmail SMTP
│
├── Frontend.html
│   └── Standalone frontend/UI design
│
├── requirements.txt
│   └── Python dependencies
│
└── README.md
    └── Project documentation
```

The core application separates transcription, NLP processing, document generation, and the main Streamlit application into dedicated modules.

---

## 🔄 Application Workflow

```text
1. Upload Meeting Audio
          ↓
2. Select Whisper Model
          ↓
3. Select / Detect Language
          ↓
4. Transcribe Audio
          ↓
5. Clean Transcript
          ↓
6. Extract Key Topics
          ↓
7. Extract Decisions
          ↓
8. Extract Action Items
          ↓
9. Generate Summary
          ↓
10. Build Minutes of Meeting
          ↓
11. Generate DOCX + Markdown
          ↓
12. Preview / Download / Email
```

The Streamlit application maintains transcript, summary, decisions, action items, topics, and generated MoM documents in session state during processing.

---

## 🚀 Getting Started

### Prerequisites

* Python **3.9–3.11**
* FFmpeg
* Git

FFmpeg is required for Whisper audio processing.

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/mom-ai-generator.git
cd mom-ai-generator
```

Replace `yourusername` with your GitHub username.

### 2. Create a Virtual Environment

#### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

#### Linux / macOS

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Install FFmpeg

#### Ubuntu / Debian

```bash
sudo apt update
sudo apt install ffmpeg -y
```

#### macOS

```bash
brew install ffmpeg
```

#### Windows

Download FFmpeg and add it to your system `PATH`.

### 5. Run the Application

```bash
streamlit run app.py
```

Open:

```text
http://localhost:8501
```

The original project documentation also recommends Python 3.9–3.11 and running the application through `streamlit run app.py`.

---

## ⚙️ Configuration

The application allows users to configure the Whisper model, language, summarization parameters, and meeting information from the interface.

### Whisper Models

| Model  | Speed    | Accuracy |
| ------ | -------- | -------- |
| tiny   | Fastest  | Lower    |
| base   | Fast     | Good     |
| small  | Moderate | Better   |
| medium | Slow     | High     |
| large  | Slowest  | Highest  |

`base` is a practical default for balancing processing time and transcription quality.

### Supported Languages

The current interface provides:

* Auto-detect
* English
* Tamil
* Hindi
* French
* Spanish
* German

---

## 📋 Generated MoM Example

The system produces a structured document similar to:

```text
MINUTES OF MEETING

Meeting Details
---------------
Title: Project Team Meeting
Date: 11 August 2026
Time: 10:00 AM
Venue: Virtual Meeting

Attendees
---------
- John
- Jane
- Kumar

Key Topics Discussed
--------------------
Project Planning, Budget, Development

Agenda
------
1. Project update
2. Budget discussion
3. Next steps

Meeting Summary
---------------
The team discussed the current project status,
budget requirements, and upcoming development tasks.

Discussion Points
-----------------
1. Current development progress was reviewed.
2. Budget requirements were discussed.
3. Upcoming tasks were identified.

Decisions Made
--------------
- The team agreed to proceed with the proposed plan.

Action Items
------------
1. Complete the development update
2. Review the project budget
3. Prepare the next progress report

Next Meeting
------------
To be scheduled
```

---

## 📧 Email Configuration

The email functionality uses a **Gmail App Password**, not the regular Gmail account password.

You will need:

```text
Gmail Address
Gmail App Password
Recipient Email Address
Optional CC Addresses
```

The application can send the generated MoM as an HTML email and optionally attach the generated `.docx` document.

### ⚠️ Security Recommendation

Do **not** hard-code your Gmail credentials inside the source code.

Use environment variables or Streamlit secrets instead.

Example:

```text
GMAIL_ADDRESS=your-email@gmail.com
GMAIL_APP_PASSWORD=your-app-password
```

Never commit passwords, API keys, or credentials to GitHub.

---

## 📊 Current NLP Approach

The current implementation uses a lightweight NLP pipeline rather than relying entirely on large language models.

### Transcript Cleaning

The system:

* Normalizes whitespace
* Removes repeated words
* Removes filler expressions
* Cleans the transcript before analysis

### Key Topic Extraction

Important words are ranked according to their frequency after removing common stop words.

### Action Item Detection

Action items are detected using predefined regular-expression patterns related to tasks, deadlines, assignments, and follow-ups.

### Decision Detection

Decision statements are identified using patterns related to agreements, approvals, confirmations, and finalized outcomes.

### Extractive Summarization

The summarizer:

1. Splits the transcript into sentences.
2. Calculates word frequencies.
3. Scores sentences according to meaningful-word frequency.
4. Gives an additional weight to early sentences.
5. Selects the highest-scoring sentences.
6. Reconstructs them in their original order.

## These mechanisms are implemented directly in `summarizer.py`.

## 🖥️ User Interface

The Streamlit application provides dedicated sections for:

* 🎵 Upload & Process
* 📝 Transcript
* 📋 MoM Preview
* ⬇️ Download
* 📧 Send Email

The transcript interface also supports plain-text and timestamped transcript views and displays extracted key topics, decisions, and action items.

A separate `Frontend.html` file provides a custom visual interface concept for the MoM AI product, including the upload, transcript, preview, and email sections.

---

## 📦 Output Formats

| Format  | Purpose                            |
| ------- | ---------------------------------- |
| `.docx` | Professional meeting documentation |
| `.md`   | Markdown-based MoM                 |
| `.txt`  | Plain transcript                   |
| Gmail   | Share MoM with participants        |

---

## 🔐 Privacy

The core transcription and NLP processing can run locally using downloaded Whisper/model resources.

Meeting audio and generated content should still be handled carefully, especially when using email integration or deploying the application publicly.

For production deployments, configure appropriate authentication, secret management, file handling, and access controls.

---

## 🌐 Deployment

Possible deployment approaches include:

### Streamlit Community Cloud

Suitable for lightweight deployments, although memory limitations may require using the `tiny` or `base` Whisper model.

### Hugging Face Spaces

Can be used for hosting the Streamlit application and ML dependencies.

### Docker

The project can also be containerized with Python and FFmpeg.

Example:

```dockerfile
FROM python:3.10-slim

RUN apt-get update && apt-get install -y ffmpeg

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

The project documentation already defines deployment approaches for Streamlit Cloud, Hugging Face Spaces, Colab, ngrok, and Docker.

---

## 🔮 Future Enhancements

Potential improvements include:

* [ ] Speaker diarization
* [ ] Identify which participant said each statement
* [ ] Real-time meeting transcription
* [ ] Improved multilingual support
* [ ] LLM-based contextual summarization
* [ ] Automatic action-item owner detection
* [ ] Automatic deadline extraction
* [ ] Calendar integration
* [ ] Meeting history database
* [ ] User authentication
* [ ] Cloud storage integration
* [ ] Improved evaluation using AMI Meeting Corpus
* [ ] REST API for integration with other applications

---

## 🎓 Academic / Final Year Project

This project is suitable as a:

* B.E. / B.Tech final-year project
* M.E. / M.Tech project
* NLP project
* Artificial Intelligence project
* Speech Processing project
* Machine Learning project
* Research prototype

### Project Domain

**Artificial Intelligence + Natural Language Processing + Speech Recognition**

### Main Research Areas

* Automatic Speech Recognition
* Text preprocessing
* Extractive summarization
* Information extraction
* Meeting analytics
* Document generation
* AI-assisted productivity

---

## 📚 References

1. Radford et al. — *Robust Speech Recognition via Large-Scale Weak Supervision* (Whisper)
2. Lewis et al. — *BART: Denoising Sequence-to-Sequence Pre-training*
3. Devlin et al. — *BERT: Pre-training of Deep Bidirectional Transformers*

---

## ❤️ Acknowledgement

Built using:

**OpenAI Whisper + Python NLP + Streamlit + PyTorch + python-docx**

---

## ⭐ Project Summary

> **MoM AI Generator transforms meeting recordings into professional Minutes of Meeting automatically — from speech recognition and NLP analysis to structured documents and email delivery.**

**Audio → Whisper → NLP → Summary → MoM → DOCX/Markdown → Email**
