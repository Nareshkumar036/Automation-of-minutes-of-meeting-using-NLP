# 📝 Automation of Minutes of Meeting using NLP

## 📌 Problem Statement

In business meetings, manually noting down key points, summarizing discussions, and preparing structured minutes is time-consuming and prone to errors. Traditional methods require human effort, leading to inconsistencies and inefficiencies. There is a need for an automated system that can accurately transcribe speech, extract relevant information, and generate well-structured minutes with minimal human intervention.

## 🎯 Solution

This project leverages **Natural Language Processing (NLP)** to automate the process of generating minutes of meetings. By using **speech-to-text conversion** and **text summarization techniques**, the system can extract key points and format them into structured meeting minutes.

### 🔹 How Our Solution Works

1. **Speech Recognition** – Converts spoken content into text using **Google Speech-to-Text API** or similar services.
2. **Text Preprocessing** – Cleans and processes raw text using **NLP techniques** like tokenization, stopword removal, and stemming.
3. **Summarization** – Extracts key discussion points using **Transformer-based models** or extractive summarization techniques.
4. **Minutes Generation** – Formats the summarized text into structured meeting minutes with sections like **Agenda, Discussion, Action Items, and Conclusions**.

---

### Dataset

1.\*\*from datasets import load\_dataset \*\*ds = load\_dataset("edinburghcstr/ami", "ihm")

2.\*\*from datasets import load\_dataset ds = load\_dataset("edinburghcstr/ami", "sdm")

## 🚀 Features

✅ **Automated Speech-to-Text Conversion** – Eliminates manual transcription.
✅ **AI-Based Summarization** – Reduces long transcripts into key points.
✅ **Structured Minutes Generation** – Organizes data into a professional format.
✅ **Export Options** – Save meeting minutes in **PDF, DOCX, or TXT** formats.

---

## 🛠️ Tech Stack

- **Programming Language:** Python
- **Speech Recognition:** Google Speech-to-Text API
- **Text Processing:** Natural Language Toolkit (NLTK), SpaCy
- **Summarization Models:** BERT, T5, or GPT-based models
- **Database:** SQLite / Firebase (if applicable)

---

## 📖 Usage

1. Open the application and start recording or upload an audio file.
2. The system converts the speech into **text**.
3. NLP processes the text and generates a **summary**.
4. The final minutes are **formatted and structured** automatically.
5. Download or export the meeting minutes.
