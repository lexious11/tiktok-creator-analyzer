# TikTok Creator Analyzer

A Streamlit web app that analyzes TikTok video performance from a CSV file and turns computed metrics into AI-assisted insights using Google Gemini. The interface is primarily in Indonesian.

## Features

- Upload and validate a video CSV
- Clean numeric fields and handle invalid values
- Account overview: total views and likes, average and median views, engagement, and top-three view contribution
- Relative performance tiers: Viral, High, Normal, and Low
- Performance summary charts and per-video charts (Top 10 for readability)
- Ranked top-performing video table
- Gemini-generated findings, hypotheses, and suggested experiments, with explicit data limitations

## How it works

`CSV upload → validation and cleaning (Pandas) → analytics → Streamlit dashboard → Gemini AI insights`

Analytics are calculated in Python first. Gemini receives the resulting metrics and is instructed not to invent unavailable metrics or make unsupported causal claims. Performance labels are relative to the videos in the uploaded dataset; they are not official TikTok classifications.

## Requirements

- Python 3.13 (or a compatible Python version supported by the dependencies)
- A Gemini API key to generate AI insights

## Run locally (Windows PowerShell)

```powershell
py -3.13 -m pip install -r requirements.txt
$env:GEMINI_API_KEY="YOUR_GEMINI_API_KEY"
py -3.13 -m streamlit run app.py
```

Keep your API key private. Do not paste it into source code, screenshots, or this public repository. Set it as an environment variable in the terminal used to launch the app.

## CSV format

The CSV must contain these columns:

```text
title,views,likes,comments,shares,duration
```

The file `data/videos.csv` is a small illustrative demo dataset so the app can launch without an upload. For privacy, do not replace it with personal or private creator analytics before committing to a public repository. Upload your own CSV through the app while testing locally.

## Limitations

- The current version uses CSV input; automatic TikTok API integration is planned for a future version and is not included.
- Results describe the uploaded dataset. A small or biased sample may not represent long-term performance.
- Metrics such as retention, watch time, and completion rate are not analyzed unless those data become available.

## Tech stack

Python · Streamlit · Pandas · Google Gemini API
