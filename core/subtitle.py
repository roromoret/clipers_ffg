import random
from faster_whisper import WhisperModel


def _format_time_ass(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    cs = int((seconds % 1) * 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def generate_ass(video_path: str, ass_path: str):
    model = WhisperModel("tiny", device="cpu", compute_type="int8")
    segments, _ = model.transcribe(video_path, word_timestamps=False)

    colors = ["&H0000FFFF", "&H0014FF39", "&H00FFFF00", "&H00FF00FF", "&H00FFFFFF"]
    chosen_color = random.choice(colors)

    with open(ass_path, "w", encoding="utf-8") as f:
        f.write("[Script Info]\nScriptType: v4.00+\nPlayResX: 1080\nPlayResY: 1920\n\n")
        f.write("[V4+ Styles]\n")
        f.write(
            "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n")
        f.write(
            f"Style: Default,Impact,90,{chosen_color},&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,3,0,2,10,10,50,1\n\n")
        f.write("[Events]\n")
        f.write("Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")

        for segment in segments:
            text = segment.text.strip().upper()
            start = _format_time_ass(segment.start)
            end = _format_time_ass(segment.end)
            f.write(f"Dialogue: 0,{start},{end},Default,,0,0,0,,{text}\n")


def generate_title_ass(text: str, ass_path: str):
    colors = ["&H0000FFFF", "&H0014FF39", "&H00FFFF00", "&H00FF00FF", "&H00FFFFFF"]
    chosen_color = random.choice(colors)

    with open(ass_path, "w", encoding="utf-8") as f:
        f.write("[Script Info]\nScriptType: v4.00+\nPlayResX: 1080\nPlayResY: 1920\n\n")
        f.write("[V4+ Styles]\n")
        f.write(
            "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n")
        # Alignment 8 (Centre Haut) et MarginV 250 (Écarte de 250px du haut de l'écran)
        f.write(
            f"Style: Title,Impact,110,{chosen_color},&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,4,0,8,10,10,250,1\n\n")
        f.write("[Events]\n")
        f.write("Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")
        f.write(f"Dialogue: 0,0:00:00.00,9:59:59.99,Title,,0,0,0,,{text.upper()}\n")