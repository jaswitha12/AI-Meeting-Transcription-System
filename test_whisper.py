import whisper

print("Loading Whisper model...")

model = whisper.load_model("base")

print("Whisper model loaded successfully!")

print("Starting transcription...")

result = model.transcribe("uploads/test.mp3")

transcript = result["text"]

print("\n========== TRANSCRIPT ==========")
print(transcript)
print("================================")