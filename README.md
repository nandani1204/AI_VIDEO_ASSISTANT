# 🎙️ AI Meeting Assistant

An end-to-end Generative AI application that transforms meeting recordings into actionable insights using Speech Recognition, LLMs, and Retrieval-Augmented Generation (RAG).

The application accepts YouTube links, audio files, or video files and automatically generates transcripts, summaries, action items, key decisions, and allows users to chat with their meetings using AI.

## 🚀 Features

- Accepts YouTube URLs, audio files, and video files as input
- Transcribes English meetings using OpenAI Whisper running locally
- Transcribes Hindi and Hinglish meetings using Sarvam AI
- Generates concise meeting summaries in bullet points
- Extracts action items along with owners and deadlines
- Identifies key decisions made during meetings
- Extracts open questions and pending follow-ups
- Enables conversational querying over meeting content using RAG
- Exports generated reports as PDF or TXT files

## 🛠 Tech Stack

- Python
- OpenAI Whisper
- Sarvam AI
- LangChain LCEL
- Mistral AI
- ChromaDB
- HuggingFace Embeddings
- Streamlit
- FFmpeg
- yt-dlp

## 🧠 Architecture

Input Media/YouTube URL
↓
Speech-to-Text Pipeline
↓
Meeting Analysis using LLM
↓
Chunking + Embeddings
↓
ChromaDB Vector Store
↓
RAG-based Chat Interface
↓
PDF/TXT Report Export

## 🎯 Use Cases

- Corporate meeting analysis
- Interview transcript generation
- Lecture and webinar summarization
- Team collaboration and follow-ups
- Podcast and content analysis

## 📈 Future Enhancements

- Multi-speaker diarization
- Multi-language support
- Calendar integration
- Automatic email summary generation
- Meeting analytics dashboard
