from flask import Flask, render_template, request
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
from transformers import pipeline

app = Flask(__name__)

# Function to extract video ID from URL
def get_video_id(url):
    if "watch?v=" in url:
        return url.split("watch?v=")[-1].split("&")[0]  # Remove extra params
    elif "youtu.be/" in url:
        return url.split("youtu.be/")[-1].split("?")[0]
    return None

# Function to chunk text (for long transcripts)
def chunk_text(text, max_words=500):
    words = text.split()
    return [" ".join(words[i:i+max_words]) for i in range(0, len(words), max_words)]

# Function to fetch transcript and summarize
def get_transcript_and_summary(video_id):
    try:
        # Fetch transcript (script/lyrics)
        transcript_data = YouTubeTranscriptApi.get_transcript(video_id)
        transcript = "\n".join([entry['text'] for entry in transcript_data])  # Preserve line breaks

        # Initialize summarizer
        summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

        # Split transcript into smaller parts
        chunks = chunk_text(transcript)
        summaries = [summarizer(chunk, max_length=150, min_length=50, do_sample=False)[0]['summary_text'] for chunk in chunks]

        return transcript, " ".join(summaries)  # Return full transcript + summary

    except TranscriptsDisabled:
        return "Error: Transcripts are disabled for this video.", None
    except NoTranscriptFound:
        return "Error: No transcript available for this video.", None
    except Exception as e:
        return f"Error: {str(e)}", None


# Route for homepage
@app.route("/", methods=["GET", "POST"])
def index():
    transcript_text = None  # Stores the full script
    summary_text = None  # Stores the summary

    if request.method == "POST":
        video_url = request.form["video_url"]
        video_id = get_video_id(video_url)
        if video_id:
            transcript_text, summary_text = get_transcript_and_summary(video_id)

    return render_template("index.html", transcript=transcript_text, summary=summary_text)


if __name__ == "__main__":
    app.run(debug=True)
