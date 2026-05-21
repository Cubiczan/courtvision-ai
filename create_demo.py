#!/usr/bin/env python3
"""Generate CourtVision AI demo video using FFmpeg."""

import subprocess
import os

LOGO = "/home/z/my-project/courtvision-ai/logo_480.png"
OUTPUT = "/home/z/my-project/courtvision-ai/download/courtvision-demo.mp4"
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_REG = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
W, H = 1280, 720

# ── Step 1: Generate 6 individual 5-second clips as PNG sequences ──
# We use a single long base video + drawtext with enable expressions.
# To avoid comma-in-comma issues, we build a CONCAT playlist of 6 segments.

# We'll create each segment as a separate mp4, then concat.
segments = []

# (title, subtitle, extra_lines)
frames = [
    ("CourtVision AI", "AI-Powered NBA Prediction Market on Polygon",
     "Powered by AI \u2022 Built on Polygon"),
    ("NBA Playoff Analysis", "Qwen LLM + Real-Time Stats", None),
    ("Azuro Protocol Integration", "Decentralized Prediction Markets on Polygon Amoy", None),
    ("Smart Contracts", "NBAMarketFactory \u2022 CourtVisionToken \u2022 OracleProxy \u2022 RewardPool", None),
    ("AI Predictions", "Win Probability \u2022 Confidence Scores \u2022 Key Insights", None),
    ("Built for DoraHacks", "NBA Prediction Market Hackathon",
     "Polygon \u2022 Azuro Protocol \u2022 Qwen LLM"),
]

for idx, (title, subtitle, extra) in enumerate(frames):
    seg_path = f"/tmp/cv_seg_{idx}.mp4"
    segments.append(seg_path)

    # Build drawtext filters for this segment (no alpha expressions, just enable)
    draw_filters = []

    # Accent bar top
    draw_filters.append(f"drawbox=x=0:y=0:w={W}:h=4:color=0x8B5CF6@0.8:t=fill")
    # Accent bar bottom
    draw_filters.append(f"drawbox=x=0:y={H-4}:w={W}:h=4:color=0x8B5CF6@0.8:t=fill")
    # Side accent bars
    draw_filters.append(f"drawbox=x=0:y=0:w=4:h={H}:color=0x8B5CF6@0.4:t=fill")
    draw_filters.append(f"drawbox=x={W-4}:y=0:w=4:h={H}:color=0x8B5CF6@0.4:t=fill")

    # Frame counter
    draw_filters.append(
        f"drawtext=fontfile={FONT_BOLD}:text='{idx+1}/6':"
        f"fontsize=18:fontcolor=0x8B5CF6@0.6:x={W-80}:y=20"
    )

    # Decorative line above title
    title_y = 200 if idx == 5 else 240
    draw_filters.append(
        f"drawbox=x={W//2-100}:y={title_y}:w=200:h=2:color=0x8B5CF6@0.8:t=fill"
    )

    # Title
    title_size = 56 if idx in (0, 5) else 48
    draw_filters.append(
        f"drawtext=fontfile={FONT_BOLD}:text='{title}':"
        f"fontsize={title_size}:fontcolor=white:"
        f"x=(w-text_w)/2:y={title_y + 20}"
    )

    # Decorative line below title
    draw_filters.append(
        f"drawbox=x={W//2-100}:y={title_y + title_size + 35}:w=200:h=2:color=0x8B5CF6@0.8:t=fill"
    )

    # Subtitle
    sub_y = title_y + title_size + 55
    draw_filters.append(
        f"drawtext=fontfile={FONT_REG}:text='{subtitle}':"
        f"fontsize=24:fontcolor=0x8B5CF6:x=(w-text_w)/2:y={sub_y}"
    )

    # Extra line
    if extra:
        draw_filters.append(
            f"drawtext=fontfile={FONT_REG}:text='{extra}':"
            f"fontsize=18:fontcolor=0x8B5CF6@0.7:x=(w-text_w)/2:y={sub_y + 50}"
        )

    # Frame-specific decorations
    if idx == 1:  # Frame 2 - basketball accents
        for bx in [180, W - 180]:
            draw_filters.append(
                f"drawbox=x={bx-25}:y={title_y+30}:w=50:h=50:color=0xFF6B00@0.5:t=fill"
            )
    elif idx == 2:  # Frame 3 - polygon accents
        for hx in [200, W - 200]:
            draw_filters.append(
                f"drawbox=x={hx-25}:y={title_y+25}:w=50:h=50:color=0x8247E5@0.5:t=fill"
            )
    elif idx == 3:  # Frame 4 - contract boxes
        contracts = ["NBAMarketFactory", "CourtVisionToken", "OracleProxy", "RewardPool"]
        box_w, box_h = 220, 50
        start_x = (W - (4 * box_w + 3 * 20)) // 2
        for ci, cname in enumerate(contracts):
            bx = start_x + ci * (box_w + 20)
            by = sub_y + 50
            draw_filters.append(
                f"drawbox=x={bx}:y={by}:w={box_w}:h={box_h}:color=0x1a1a3a@0.8:t=fill"
            )
            draw_filters.append(
                f"drawbox=x={bx}:y={by}:w={box_w}:h=2:color=0x8B5CF6@0.8:t=fill"
            )
            draw_filters.append(
                f"drawtext=fontfile={FONT_REG}:text='{cname}':"
                f"fontsize=15:fontcolor=0x8B5CF6:x={bx+10}:y={by+15}"
            )
    elif idx == 4:  # Frame 5 - stats boxes
        stats = [("Win Probability", "87.3%"), ("Confidence", "High"), ("Key Insights", "Active")]
        stat_w, stat_h = 300, 80
        start_x = (W - (3 * stat_w + 2 * 30)) // 2
        for si, (sname, sval) in enumerate(stats):
            sx = start_x + si * (stat_w + 30)
            sy = sub_y + 50
            draw_filters.append(
                f"drawbox=x={sx}:y={sy}:w={stat_w}:h={stat_h}:color=0x1a1a3a@0.8:t=fill"
            )
            draw_filters.append(
                f"drawbox=x={sx}:y={sy}:w={stat_w}:h=3:color=0x8B5CF6@0.8:t=fill"
            )
            draw_filters.append(
                f"drawtext=fontfile={FONT_BOLD}:text='{sname}':"
                f"fontsize=20:fontcolor=white:x={sx+20}:y={sy+15}"
            )
            draw_filters.append(
                f"drawtext=fontfile={FONT_BOLD}:text='{sval}':"
                f"fontsize=28:fontcolor=0x8B5CF6:x={sx+20}:y={sy+42}"
            )

    # Join filters with commas
    filter_chain = ",".join(draw_filters)

    # FFmpeg command for this segment
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-i", LOGO,
        "-f", "lavfi", "-i", f"color=c=0x0a0a1a:s={W}x{H}:d=5:r=30",
        "-filter_complex",
        f"[1:v]{filter_chain}[bg];[bg][0:v]overlay=x=(W-overlay_w)/2:y=50",
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-pix_fmt", "yuv420p", "-r", "30", "-t", "5", "-shortest",
        seg_path
    ]

    print(f"Creating segment {idx+1}/6: {title}...")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if result.returncode != 0:
        print(f"ERROR segment {idx}:\n{result.stderr[-2000:]}")
        raise RuntimeError(f"FFmpeg segment {idx} failed: code {result.returncode}")
    print(f"  -> {os.path.getsize(seg_path):,} bytes")

# ── Step 2: Create concat file ──
concat_file = "/tmp/cv_concat.txt"
with open(concat_file, "w") as f:
    for seg in segments:
        f.write(f"file '{seg}'\n")

print(f"\nConcatenating {len(segments)} segments...")

# ── Step 3: Concatenate with crossfade using xfade ──
# For simplicity, use concat demuxer (no crossfade but clean)
cmd = [
    "ffmpeg", "-y",
    "-f", "concat", "-safe", "0", "-i", concat_file,
    "-c:v", "libx264", "-preset", "medium", "-crf", "23",
    "-pix_fmt", "yuv420p", "-r", "30",
    OUTPUT
]

result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
if result.returncode != 0:
    print(f"ERROR concat:\n{result.stderr[-2000:]}")
    raise RuntimeError(f"FFmpeg concat failed: code {result.returncode}")

# Verify
if os.path.exists(OUTPUT):
    size = os.path.getsize(OUTPUT)
    print(f"\n{'='*50}")
    print(f"  Video created successfully!")
    print(f"  Path: {OUTPUT}")
    print(f"  Size: {size:,} bytes ({size/1024/1024:.2f} MB)")
    print(f"{'='*50}")

    # Probe for duration
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", OUTPUT],
        capture_output=True, text=True
    )
    if probe.stdout.strip():
        dur = float(probe.stdout.strip())
        print(f"  Duration: {dur:.1f} seconds")
else:
    raise RuntimeError("Output file was not created!")

# Cleanup temp files
for seg in segments:
    os.remove(seg)
os.remove(concat_file)
print("  Temp files cleaned up.")
