#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2026 DriftGuard Contributors
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
"""
DriftGuard - Deterministic Headless Explainer Video Generator
=============================================================
Renders a broadcast-quality, deterministic 1080p MP4 video explaining
DriftGuard's architecture, the silent 200 OK problem, and developer usage.

Visual Geometry & Layout Standards:
- Strict Rule of Thirds composition along 3x3 grid (1920x1080):
  • Vertical guidelines: x = 640px (1/3) and x = 1280px (2/3)
  • Horizontal guidelines: y = 360px (1/3) and y = 720px (2/3)
- Header & Brand Zone contained strictly within y < 180px.
- Primary visual focal anchors centered on x = 640px and x = 1280px.
- Lower third metrics, supporting cards, and footers across y: 725..968.
- Dedicated subtitle band anchored at y: 880..930.
- 2.0-second cinematic logo intro and outro bumper cards.
- Outro announcement covering open source repository, documentation, and endpoints.
- Local Piper voiceover (Ryan/Lessac) with clean phonetic tunings and synchronized subtitles.
- Pure acoustic clarity: zero low-frequency hum/drone.
- Kept strictly local and untracked via .git/info/exclude.
"""

from __future__ import annotations

import argparse
import glob
import io
import math
import os
import shutil
import struct
import subprocess
import sys
import tempfile
import textwrap
import time
import wave
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from PIL import Image, ImageDraw, ImageFont

try:
    import cairosvg
    HAS_CAIROSVG = True
except ImportError:
    HAS_CAIROSVG = False

# -----------------------------------------------------------------------------
# Color Palette (Arbitrum Dark Tech Theme)
# -----------------------------------------------------------------------------
BG_COLOR: Tuple[int, int, int] = (9, 13, 22)             # Deep Slate-950
GRID_COLOR: Tuple[int, int, int] = (18, 26, 43)          # Subtle grid lines
ROT_GUIDE_COLOR: Tuple[int, int, int] = (25, 38, 62)     # Rule of Thirds gridlines
CARD_BG: Tuple[int, int, int] = (15, 23, 42)             # Slate-900 surface
CARD_BG_ELEVATED: Tuple[int, int, int] = (22, 32, 54)    # Elevated surface
CARD_BORDER: Tuple[int, int, int] = (30, 41, 59)         # Slate-800 border
CARD_BORDER_ACTIVE: Tuple[int, int, int] = (40, 160, 240)# Arbitrum Blue (#28A0F0)

CYAN: Tuple[int, int, int] = (84, 183, 245)              # #54B7F5
ARBITRUM_BLUE: Tuple[int, int, int] = (40, 160, 240)     # #28A0F0
EMERALD: Tuple[int, int, int] = (16, 185, 129)           # #10B981
AMBER: Tuple[int, int, int] = (245, 158, 11)             # #F59E0B
RED: Tuple[int, int, int] = (239, 68, 68)                # #EF4444
WHITE: Tuple[int, int, int] = (248, 250, 252)            # #F8FAFC
TEXT_MUTED: Tuple[int, int, int] = (148, 163, 184)       # #94A3B8
TEXT_DARK: Tuple[int, int, int] = (100, 116, 139)        # #64748B

CODE_COMMENT: Tuple[int, int, int] = (100, 116, 139)
CODE_PASS: Tuple[int, int, int] = (52, 211, 153)
CODE_WARN: Tuple[int, int, int] = (251, 191, 36)
CODE_FAIL: Tuple[int, int, int] = (248, 113, 113)

# -----------------------------------------------------------------------------
# Canvas Geometry & Rule of Thirds Bounds (1920x1080)
# -----------------------------------------------------------------------------
CANVAS_W: int = 1920
CANVAS_H: int = 1080
MARGIN_X: int = 80
CONTENT_W: int = CANVAS_W - 2 * MARGIN_X  # 1760px

# Rule of Thirds guidelines
ROT_X1: int = 640   # 1/3 vertical guideline
ROT_X2: int = 1280  # 2/3 vertical guideline
ROT_Y1: int = 360   # 1/3 horizontal guideline
ROT_Y2: int = 720   # 2/3 horizontal guideline (lower third baseline)

# Content bands
HEADER_MAX_Y: int = 180       # Header & Brand zone strictly y < 180
FOCAL_START_Y: int = 210      # Primary focal anchor start y
FOCAL_END_Y: int = 720        # Primary focal anchor end y (Rule of Thirds 2/3 baseline)
SUBTITLE_Y1: int = 880        # Dedicated subtitle bar top (Lower Third centered)
SUBTITLE_Y2: int = 930        # Dedicated subtitle bar bottom
SCRUBBER_Y: int = 1040        # Scrubber bar y

# -----------------------------------------------------------------------------
# Subtitle Cue Data Structure
# -----------------------------------------------------------------------------
class NarrationCue:
    """Represents a speech narration phrase and its corresponding synchronized subtitle."""
    def __init__(self, tts_text: str, subtitle_text: str, pause_after: float = 0.22) -> None:
        self.tts_text: str = tts_text
        self.subtitle_text: str = subtitle_text
        self.pause_after: float = pause_after
        self.start_time: float = 0.0
        self.end_time: float = 0.0


# -----------------------------------------------------------------------------
# Local Piper TTS Resolver & Phonetically Tuned Narrations with Subtitles
# -----------------------------------------------------------------------------
DEFAULT_PIPER_SEARCH_PATHS: List[str] = [
    "/home/masky/old factory home/headless_lab/piper/piper/piper",
    os.path.expanduser("~/old factory home/headless_lab/piper/piper/piper"),
    os.path.expanduser("~/headless_lab/piper/piper/piper"),
    os.path.expanduser("~/.local/bin/piper"),
    "/usr/local/bin/piper",
    "/usr/bin/piper",
]

DEFAULT_VOICE_DIRS: List[str] = [
    "/home/masky/old factory home/headless_lab/piper",
    os.path.expanduser("~/old factory home/headless_lab/piper"),
    os.path.expanduser("~/headless_lab/piper"),
]

SCENE_CUES: Dict[int, List[NarrationCue]] = {
    1: [
        NarrationCue(
            "Welcome to DriftGuard.",
            "Welcome to DriftGuard."
        ),
        NarrationCue(
            "DriftGuard is a deterministic Layer 7 ingress gateway and out-of-band consensus sentinel...",
            "Deterministic Layer 7 ingress gateway and out-of-band consensus sentinel..."
        ),
        NarrationCue(
            "...engineered for high-throughput EVM rollups, validator nodes, and session relayers.",
            "...engineered for EVM rollups, validator nodes, and session relayers."
        ),
        NarrationCue(
            "It decouples client JSON-RPC proxying from consensus verification, enforcing sub-130 millisecond UNIX socket draining...",
            "Decouples JSON-RPC proxying from consensus verification, enforcing < 130ms UNIX socket drain..."
        ),
        NarrationCue(
            "...operating with zero dropped TCP connections in under forty-five megabytes of memory.",
            "...operating with zero dropped TCP connections in under 45 MB of RAM."
        ),
    ],
    2: [
        NarrationCue(
            "In sub-second rollups, block tips advance every 250 milliseconds.",
            "In sub-second rollups, block tips advance every 250 milliseconds."
        ),
        NarrationCue(
            "When an upstream node stalls its ingestion feed, standard load balancers only check HTTP 200 and stay blind to blockchain desyncs.",
            "When an upstream node stalls its ingestion feed, standard load balancers only check HTTP 200 and stay blind to desyncs."
        ),
        NarrationCue(
            "Querying clients receive outdated nonces, causing newly signed transactions to immediately revert on-chain with nonce too low.",
            "Querying clients receive outdated nonces, causing transactions to immediately revert on-chain with nonce too low."
        ),
    ],
    3: [
        NarrationCue(
            "DriftGuard operates a multi-provider quorum engine sampling three independent references every 200 milliseconds.",
            "Multi-provider quorum engine sampling 3 independent references every 200ms."
        ),
        NarrationCue(
            "It verifies block height parity and cryptographic parent-hash linkage between adjacent blocks.",
            "Verifies block height parity and cryptographic parent-hash linkage between adjacent blocks."
        ),
        NarrationCue(
            "Two-thirds majority consensus isolates lagging reference outliers without draining local nodes.",
            "Two-thirds majority consensus isolates lagging reference outliers without draining local nodes."
        ),
        NarrationCue(
            "A four-state hysteresis controller manages transitions from healthy to suspect, draining only after three consecutive suspect ticks.",
            "4-state hysteresis controller transitions to suspect, draining only after K=3 suspect ticks."
        ),
        NarrationCue(
            "The minimum-healthy guardrail ensures routing is preserved if draining would leave zero active backends.",
            "Minimum-Healthy Guardrail ensures routing is preserved if draining would leave zero active backends."
        ),
    ],
    4: [
        NarrationCue(
            "Getting started and verifying consensus resilience takes under 60 seconds.",
            "Getting started and verifying consensus resilience takes under 60 seconds."
        ),
        NarrationCue(
            "Clone the repository and launch the deterministic chaos acceptance suite with make test-chaos.",
            "Clone the repository and launch the deterministic chaos acceptance suite: make test-chaos"
        ),
        NarrationCue(
            "The testbed spins up three mock EVM nodes, an HAProxy gateway, and the DriftGuard consensus controller in isolation.",
            "Spins up 3 mock EVM nodes, an HAProxy gateway, and the DriftGuard controller in isolation."
        ),
        NarrationCue(
            "Production sidecar deployments run via Docker Compose in under forty-five megabytes of RAM.",
            "Production sidecar deployments run via Docker Compose in under 45 MB of RAM."
        ),
    ],
    5: [
        NarrationCue(
            "The deterministic runner streams two to four hundred requests per second against the gateway while validating against oracle ground truth.",
            "Deterministic runner streams 200-400 req/s while validating against oracle ground truth."
        ),
        NarrationCue(
            "When an eight-block sequencer stall is injected, DriftGuard detects the lag and drains the node in 132 milliseconds.",
            "When an 8-block stall is injected, DriftGuard detects and drains the node in 132 milliseconds."
        ),
        NarrationCue(
            "Traffic reroutes to fallback with zero HTTP 5xx errors and zero dropped requests, recovering automatically after five synchronized ticks.",
            "Traffic reroutes to fallback with 0 HTTP 5xx errors, recovering after M=5 synchronized ticks."
        ),
    ],
    6: [
        NarrationCue(
            "DriftGuard deploys alongside rollup sequencers, validator clusters, and transaction relayers.",
            "Deploys alongside rollup sequencers, validator clusters, and transaction relayers."
        ),
        NarrationCue(
            "Account abstraction paymasters eliminate nonce desyncs without client SDK modifications.",
            "Account abstraction paymasters eliminate nonce desyncs without client SDK modifications."
        ),
        NarrationCue(
            "Live multi-chain reference endpoints are active across Arbitrum networks at R-P-C dot drift guard dot live.",
            "Live multi-chain reference endpoints active at rpc.driftguard.live."
        ),
    ],
    7: [
        NarrationCue(
            "DriftGuard is completely open source under the M-I-T license, with full documentation and active development on GitHub.",
            "DriftGuard is completely open source under the MIT license with full documentation on GitHub."
        ),
        NarrationCue(
            "Explore the source code, inspect our benchmarks, and start running the consensus sentinel today on GitHub.",
            "Explore the source code, inspect our benchmarks, and run the sentinel today on GitHub."
        ),
    ],
}


def purge_caches() -> None:
    """Purges all temporary cached audio, video, and image artifacts."""
    patterns = [
        "/tmp/scene*.mp4",
        "/tmp/*.png",
        "/tmp/*.wav",
        "/tmp/test_audio*",
        "/tmp/cue_*.wav",
        "/tmp/driftguard_video_*",
    ]
    for pattern in patterns:
        for p in glob.glob(pattern):
            try:
                if os.path.isdir(p):
                    shutil.rmtree(p, ignore_errors=True)
                else:
                    os.remove(p)
            except OSError:
                pass


def resolve_piper(
    custom_bin: Optional[str] = None,
    custom_model: Optional[str] = None,
    voice_name: str = "ryan"
) -> Tuple[Optional[str], Optional[str]]:
    """Resolves local Piper binary executable and ONNX voice model path."""
    bin_path: Optional[str] = None
    if custom_bin and os.path.isfile(custom_bin) and os.access(custom_bin, os.X_OK):
        bin_path = custom_bin
    else:
        for p in DEFAULT_PIPER_SEARCH_PATHS:
            if os.path.isfile(p) and os.access(p, os.X_OK):
                bin_path = p
                break
        if not bin_path:
            bin_path = shutil.which("piper")

    model_path: Optional[str] = None
    if custom_model and os.path.isfile(custom_model):
        model_path = custom_model
    else:
        target_name = f"{voice_name}.onnx"
        for vdir in DEFAULT_VOICE_DIRS:
            candidate = os.path.join(vdir, target_name)
            if os.path.isfile(candidate):
                model_path = candidate
                break

    return bin_path, model_path


def synthesize_speech_clip(
    piper_bin: str,
    model_path: str,
    text: str,
    output_wav: str,
    length_scale: float = 0.95
) -> None:
    """Synthesizes speech audio using local Piper TTS."""
    cmd = [
        piper_bin,
        "--model", model_path,
        "--length_scale", str(length_scale),
        "--sentence_silence", "0.15",
        "--output_file", output_wav,
    ]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    _, err = p.communicate(input=text.encode("utf-8"))
    if p.returncode != 0:
        raise RuntimeError(f"Piper TTS synthesis failed: {err.decode('utf-8', errors='ignore')}")


def build_scene_wav(
    output_wav: str,
    scene_dur: float,
    cue_wavs: List[Tuple[NarrationCue, str, float]],
    sample_rate: int = 44100
) -> None:
    """Combines cue audio clips into a unified scene audio file at exact timestamps."""
    total_samples = int(scene_dur * sample_rate)
    samples = [0.0] * total_samples

    for cue, wav_path, _ in cue_wavs:
        if not os.path.isfile(wav_path):
            continue
        with wave.open(wav_path, "rb") as w:
            nchannels = w.getnchannels()
            in_rate = w.getframerate()
            nframes = w.getnframes()
            raw_data = w.readframes(nframes)

        start_s = int(cue.start_time * sample_rate)
        step = in_rate / sample_rate
        n_in_samples = len(raw_data) // (2 * nchannels)

        for out_idx in range(int(n_in_samples / step)):
            target_idx = start_s + out_idx
            if target_idx >= total_samples:
                break
            in_s = int(out_idx * step)
            if in_s >= n_in_samples:
                break
            val_int = struct.unpack_from("<h", raw_data, in_s * 2 * nchannels)[0]
            samples[target_idx] += (val_int / 32768.0) * 0.95

    with wave.open(output_wav, "wb") as out_w:
        out_w.setnchannels(1)
        out_w.setsampwidth(2)
        out_w.setframerate(sample_rate)
        chunk = bytearray()
        for i in range(total_samples):
            val = int(max(-32767, min(32767, samples[i] * 32767)))
            chunk.extend(struct.pack("<h", val))
            if len(chunk) > 65536:
                out_w.writeframes(chunk)
                chunk = bytearray()
        if chunk:
            out_w.writeframes(chunk)


# -----------------------------------------------------------------------------
# Font Management
# -----------------------------------------------------------------------------
def find_font(font_names: List[str], default_size: int = 18) -> ImageFont.ImageFont:
    """Locates and loads a TrueType font, falling back to default if unavailable."""
    search_paths = [
        "/usr/share/fonts/truetype/dejavu",
        "/usr/share/fonts/truetype/liberation",
        "/usr/share/fonts/truetype",
        "/usr/local/share/fonts",
        "/Library/Fonts",
        "/System/Library/Fonts",
        "C:\\Windows\\Fonts",
    ]
    for name in font_names:
        for p in search_paths:
            path = Path(p) / name
            if path.is_file():
                try:
                    return ImageFont.truetype(str(path), default_size)
                except Exception:
                    pass
    for name in font_names:
        try:
            res = subprocess.run(["fc-match", "-f", "%{file}", name], capture_output=True, text=True)
            if res.returncode == 0 and res.stdout.strip():
                fpath = res.stdout.strip()
                if os.path.isfile(fpath):
                    return ImageFont.truetype(fpath, default_size)
        except Exception:
            pass
    return ImageFont.load_default()


class FontManager:
    """Holds initialized font handles across type hierarchy."""
    def __init__(self) -> None:
        self.hero_font = find_font(["DejaVuSans-Bold.ttf", "LiberationSans-Bold.ttf", "Arial-Bold.ttf"], 54)
        self.title_font = find_font(["DejaVuSans-Bold.ttf", "LiberationSans-Bold.ttf", "Arial-Bold.ttf"], 34)
        self.h1_font = find_font(["DejaVuSans-Bold.ttf", "LiberationSans-Bold.ttf", "Arial-Bold.ttf"], 26)
        self.h2_font = find_font(["DejaVuSans-Bold.ttf", "LiberationSans-Bold.ttf", "Arial-Bold.ttf"], 20)
        self.body_font = find_font(["DejaVuSans.ttf", "LiberationSans-Regular.ttf", "Arial.ttf"], 17)
        self.body_bold = find_font(["DejaVuSans-Bold.ttf", "LiberationSans-Bold.ttf", "Arial-Bold.ttf"], 17)
        self.small_font = find_font(["DejaVuSans.ttf", "LiberationSans-Regular.ttf", "Arial.ttf"], 14)
        self.small_bold = find_font(["DejaVuSans-Bold.ttf", "LiberationSans-Bold.ttf", "Arial-Bold.ttf"], 14)

        self.mono_title = find_font(["DejaVuSansMono-Bold.ttf", "LiberationMono-Bold.ttf", "Courier-Bold.ttf"], 18)
        self.mono_font = find_font(["DejaVuSansMono.ttf", "LiberationMono-Regular.ttf", "Courier.ttf"], 14)
        self.mono_bold = find_font(["DejaVuSansMono-Bold.ttf", "LiberationMono-Bold.ttf", "Courier-Bold.ttf"], 14)
        self.mono_small = find_font(["DejaVuSansMono.ttf", "LiberationMono-Regular.ttf", "Courier.ttf"], 13)


# -----------------------------------------------------------------------------
# Asset Loader & Procedural Glows
# -----------------------------------------------------------------------------
def load_shield_asset(project_root: Path, size: int = 240) -> Image.Image:
    """Loads DriftGuard official logo from public/ folder (icon-512.png / avatar.png)."""
    public_dir = project_root / "public"
    candidates = [
        public_dir / "icon-512.png",
        public_dir / "avatar.png",
        public_dir / "icon-192.png",
    ]
    for p in candidates:
        if p.is_file():
            try:
                img = Image.open(p).convert("RGBA")
                return img.resize((size, size), Image.Resampling.LANCZOS)
            except Exception:
                pass

    svg_path = public_dir / "favicon.svg"
    if svg_path.is_file() and HAS_CAIROSVG:
        try:
            with open(svg_path, "rb") as f:
                svg_data = f.read()
            png_bytes = cairosvg.svg2png(bytestring=svg_data, output_width=size, output_height=size)
            return Image.open(io.BytesIO(png_bytes)).convert("RGBA")
        except Exception:
            pass

    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    pts = [
        (size * 0.5, size * 0.08),
        (size * 0.9, size * 0.28),
        (size * 0.9, size * 0.72),
        (size * 0.5, size * 0.92),
        (size * 0.1, size * 0.72),
        (size * 0.1, size * 0.28),
    ]
    draw.polygon(pts, fill=(15, 23, 42, 240), outline=(40, 160, 240, 255))
    return img


def create_radial_glow(size: int = 256, color: Tuple[int, int, int] = (40, 160, 240)) -> Image.Image:
    """Generates procedural radial glow aura with cubic falloff."""
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    cx, cy = size / 2, size / 2
    r_max = size / 2
    pix = im.load()
    for y in range(size):
        for x in range(size):
            dist = math.hypot(x - cx, y - cy)
            if dist < r_max:
                factor = (1.0 - (dist / r_max)) ** 2.2
                alpha = int(255 * factor)
                pix[x, y] = (color[0], color[1], color[2], alpha)
    return im


# -----------------------------------------------------------------------------
# Drawing Helpers & UI Primitives
# -----------------------------------------------------------------------------
def ease_out(t: float) -> float:
    """Quadratic ease-out interpolation."""
    t = max(0.0, min(1.0, t))
    return 1.0 - (1.0 - t) * (1.0 - t)


def draw_badge(
    draw: ImageDraw.Draw,
    x: int,
    y: int,
    text: str,
    font: ImageFont.ImageFont,
    bg_color: Tuple[int, int, int] = CARD_BG,
    text_color: Tuple[int, int, int] = CYAN,
    border_color: Tuple[int, int, int] = CARD_BORDER,
    pad_x: int = 12,
    pad_y: int = 4
) -> Tuple[int, int]:
    """Draws rounded pill badge and returns (width, height)."""
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    w = tw + pad_x * 2
    h = th + pad_y * 2
    draw.rounded_rectangle([x, y, x + w, y + h], radius=6, fill=bg_color, outline=border_color, width=1)
    draw.text((x + pad_x, y + pad_y - bbox[1]), text, font=font, fill=text_color)
    return w, h


def draw_scene_header(
    draw: ImageDraw.Draw,
    fonts: FontManager,
    title: str = "",
    subtitle: str = "",
    tag: Optional[str] = None,
    tag_color: Tuple[int, int, int] = CYAN,
    tag_bg: Tuple[int, int, int] = CARD_BG,
    tag_border: Tuple[int, int, int] = CARD_BORDER,
    left_x: int = MARGIN_X,
    **kwargs: Any
) -> None:
    """
    Renders standardized scene header without badge bloat:
    - Title: y = 72..108 (crisp white, high-contrast)
    - Subtitle: y = 114..142 (crisp cyan)
    """
    draw.text((left_x, 72), title, font=fonts.title_font, fill=WHITE)
    draw.text((left_x, 114), subtitle, font=fonts.h2_font, fill=CYAN)



def draw_card(
    draw: ImageDraw.Draw,
    x: int,
    y: int,
    w: int,
    h: int,
    title: str,
    subtitle: str,
    bullets: List[str],
    fonts: FontManager,
    border_color: Tuple[int, int, int] = CARD_BORDER,
    bg_color: Tuple[int, int, int] = CARD_BG,
    tag: str = "",
    tag_color: Tuple[int, int, int] = CYAN,
    wrap_width: int = 58,
    metrics: Optional[List[Tuple[str, str]]] = None
) -> None:
    """Draws a card component with title, subtitle, bullets, and bottom metric tray."""
    draw.rounded_rectangle([x, y, x + w, y + h], radius=12, fill=bg_color, outline=border_color, width=2)
    cur_y = y + 16
    if tag:
        draw_badge(draw, x + 20, cur_y, tag, fonts.small_bold, bg_color=(20, 28, 48), text_color=tag_color, border_color=border_color)
        cur_y += 32
    if title:
        draw.text((x + 20, cur_y), title, font=fonts.h1_font, fill=WHITE)
        cur_y += 30
    if subtitle:
        draw.text((x + 20, cur_y), subtitle, font=fonts.body_bold, fill=CYAN)
        cur_y += 24
        draw.line([(x + 20, cur_y), (x + w - 20, cur_y)], fill=CARD_BORDER, width=1)
        cur_y += 16
    
    max_bullet_y = y + h - (58 if metrics else 20)
    for bullet in bullets:
        if cur_y > max_bullet_y:
            break
        wrapped = textwrap.wrap(bullet, width=wrap_width)
        for line_idx, line in enumerate(wrapped):
            if cur_y > max_bullet_y:
                break
            if line_idx == 0:
                draw.text((x + 20, cur_y), "•", font=fonts.body_bold, fill=tag_color if tag else ARBITRUM_BLUE)
                draw.text((x + 38, cur_y), line, font=fonts.body_font, fill=TEXT_MUTED)
            else:
                draw.text((x + 38, cur_y), line, font=fonts.body_font, fill=TEXT_MUTED)
            cur_y += 24
        cur_y += 5

    # Bottom Metric Tray (if metrics provided)
    if metrics:
        tray_h = 36
        tray_y = y + h - tray_h - 14
        draw.rounded_rectangle([x + 18, tray_y, x + w - 18, tray_y + tray_h], radius=8, fill=(11, 16, 28), outline=CARD_BORDER, width=1)
        num_m = len(metrics)
        col_w = (w - 36) // num_m
        for m_idx, (m_label, m_val) in enumerate(metrics):
            mx = x + 18 + m_idx * col_w
            if m_idx > 0:
                draw.line([(mx, tray_y + 8), (mx, tray_y + tray_h - 8)], fill=CARD_BORDER, width=1)
            full_txt = f"{m_label}: {m_val}"
            bb = draw.textbbox((0, 0), full_txt, font=fonts.mono_small)
            tw = bb[2] - bb[0]
            tx = mx + (col_w - tw) // 2
            ty = tray_y + 10
            lbl_bb = draw.textbbox((0, 0), f"{m_label}: ", font=fonts.mono_small)
            lbl_w = lbl_bb[2] - lbl_bb[0]
            draw.text((tx, ty), f"{m_label}: ", font=fonts.mono_small, fill=TEXT_DARK)
            draw.text((tx + lbl_w, ty), m_val, font=fonts.mono_small, fill=CYAN)


def draw_terminal_window(
    draw: ImageDraw.Draw,
    x: int,
    y: int,
    w: int,
    h: int,
    title: str,
    lines: List[str],
    fonts: FontManager,
    cursor_line: int = -1,
    cursor_col: int = -1,
    metrics: Optional[List[Tuple[str, str]]] = None
) -> None:
    """Draws macOS/Linux terminal window with chrome buttons, syntax-highlighted lines, and bottom status tray."""
    draw.rounded_rectangle([x, y, x + w, y + h], radius=12, fill=(11, 16, 27), outline=CARD_BORDER, width=2)
    draw.rounded_rectangle([x, y, x + w, y + 36], radius=12, fill=(20, 28, 45))
    draw.rectangle([x, y + 24, x + w, y + 36], fill=(20, 28, 45))
    draw.line([(x, y + 36), (x + w, y + 36)], fill=CARD_BORDER, width=1)

    draw.ellipse([x + 14, y + 12, x + 26, y + 24], fill=(239, 68, 68))
    draw.ellipse([x + 34, y + 12, x + 46, y + 24], fill=(245, 158, 11))
    draw.ellipse([x + 54, y + 12, x + 66, y + 24], fill=(16, 185, 129))

    t_bbox = draw.textbbox((0, 0), title, font=fonts.small_bold)
    tw = t_bbox[2] - t_bbox[0]
    draw.text((x + (w - tw) // 2, y + 9), title, font=fonts.small_bold, fill=TEXT_MUTED)

    cur_y = y + 46
    line_h = 24
    max_line_y = y + h - (52 if metrics else 22)
    for line_idx, line in enumerate(lines):
        if cur_y > max_line_y:
            break
        cur_x = x + 18
        color = WHITE
        txt = line
        if line.startswith("$"):
            draw.text((cur_x, cur_y), "$", font=fonts.mono_bold, fill=CYAN)
            cur_x += 16
            txt = line[1:].strip()
            color = WHITE
        elif line.startswith("#"):
            color = CODE_COMMENT
        elif line.startswith("✔") or "[PASS]" in line:
            color = CODE_PASS
        elif line.startswith("⚡") or "[WARN]" in line:
            color = CODE_WARN
        elif line.startswith("✖") or "[FAIL]" in line:
            color = CODE_FAIL
        elif line.startswith("HTTP/") or "x-driftguard" in line:
            color = CYAN
        elif "x-upstream" in line:
            color = EMERALD if ("primary" in line or "fallback" in line) else WHITE

        draw.text((cur_x, cur_y), txt, font=fonts.mono_font, fill=color)

        if line_idx == cursor_line:
            bbox = draw.textbbox((0, 0), txt[:cursor_col], font=fonts.mono_font)
            cx_pos = cur_x + (bbox[2] - bbox[0]) + 2
            draw.rectangle([cx_pos, cur_y + 2, cx_pos + 8, cur_y + 16], fill=CYAN)

        cur_y += line_h

    # Bottom Status Tray (if metrics provided)
    if metrics:
        tray_h = 34
        tray_y = y + h - tray_h - 12
        draw.rounded_rectangle([x + 14, tray_y, x + w - 14, tray_y + tray_h], radius=6, fill=(15, 22, 36), outline=CARD_BORDER, width=1)
        num_m = len(metrics)
        col_w = (w - 28) // num_m
        for m_idx, (m_label, m_val) in enumerate(metrics):
            mx = x + 14 + m_idx * col_w
            if m_idx > 0:
                draw.line([(mx, tray_y + 6), (mx, tray_y + tray_h - 6)], fill=CARD_BORDER, width=1)
            full_txt = f"{m_label}: {m_val}"
            bb = draw.textbbox((0, 0), full_txt, font=fonts.mono_small)
            tw = bb[2] - bb[0]
            tx = mx + (col_w - tw) // 2
            ty = tray_y + 9
            lbl_bb = draw.textbbox((0, 0), f"{m_label}: ", font=fonts.mono_small)
            lbl_w = lbl_bb[2] - lbl_bb[0]
            draw.text((tx, ty), f"{m_label}: ", font=fonts.mono_small, fill=TEXT_DARK)
            draw.text((tx + lbl_w, ty), m_val, font=fonts.mono_small, fill=EMERALD if "0" in m_val or "PASS" in m_val or "OK" in m_val or "SYNC" in m_val else CYAN)



def draw_subtitle_pill(
    draw: ImageDraw.Draw,
    fonts: FontManager,
    text: str,
    width: int = CANVAS_W,
    height: int = CANVAS_H
) -> None:
    """
    Renders broadcast-quality floating subtitle pill anchored at y: 982..1026.
    Includes [CC] identifier badge and crisp high-contrast white typography.
    """
    if not text:
        return

    cc_txt = "CC"
    cc_bbox = draw.textbbox((0, 0), cc_txt, font=fonts.mono_small)
    cc_w = (cc_bbox[2] - cc_bbox[0]) + 16
    cc_h = (cc_bbox[3] - cc_bbox[1]) + 8

    t_bbox = draw.textbbox((0, 0), text, font=fonts.body_bold)
    tw = t_bbox[2] - t_bbox[0]
    th = t_bbox[3] - t_bbox[1]

    pill_h = 44
    pill_y = SUBTITLE_Y1
    total_w = min(width - 160, cc_w + 14 + tw + 40)
    pill_x = (width - total_w) // 2

    # Background surface
    draw.rounded_rectangle(
        [pill_x, pill_y, pill_x + total_w, pill_y + pill_h],
        radius=10,
        fill=(11, 16, 28),
        outline=(40, 160, 240),
        width=1
    )

    # CC badge
    cc_x = pill_x + 14
    cc_y = pill_y + (pill_h - cc_h) // 2
    draw.rounded_rectangle(
        [cc_x, cc_y, cc_x + cc_w, cc_y + cc_h],
        radius=4,
        fill=(18, 32, 54),
        outline=(84, 183, 245),
        width=1
    )
    draw.text((cc_x + 8, cc_y + 3), cc_txt, font=fonts.mono_small, fill=CYAN)

    # Subtitle text
    text_x = cc_x + cc_w + 14
    text_y = pill_y + (pill_h - th) // 2 - 2
    draw.text((text_x, text_y), text, font=fonts.body_bold, fill=WHITE)


# -----------------------------------------------------------------------------
# Base Scene Class
# -----------------------------------------------------------------------------
class Scene:
    """Base class for all sequence scenes."""
    def __init__(self, scene_id: int, name: str, breadcrumb: str, duration_sec: float, fps: int) -> None:
        self.scene_id: int = scene_id
        self.name: str = name
        self.breadcrumb: str = breadcrumb
        self.duration_sec: float = duration_sec
        self.fps: int = fps
        self.total_frames: int = int(duration_sec * fps)
        self.cues: List[NarrationCue] = []

    def set_duration(self, new_sec: float) -> None:
        self.duration_sec = max(2.0, new_sec)
        self.total_frames = int(self.duration_sec * self.fps)

    def get_active_subtitle(self, frame_idx: int) -> Optional[str]:
        t = frame_idx / max(1, self.fps)
        for cue in self.cues:
            if cue.start_time <= t <= (cue.end_time + 0.18):
                return cue.subtitle_text
        return None

    def render(
        self,
        frame_idx: int,
        img: Image.Image,
        draw: ImageDraw.Draw,
        fonts: FontManager,
        shield: Image.Image,
        glow: Image.Image,
        w: int,
        h: int
    ) -> None:
        raise NotImplementedError


# -----------------------------------------------------------------------------
# Intro Logo Frame: 2.0 Second Cinematic Title Bumper
# -----------------------------------------------------------------------------
class SceneIntroLogo(Scene):
    """
    2-second cinematic intro logo bumper:
    - Official DriftGuard logo (icon-512.png) with radial glow
    - Title: DRIFTGUARD
    - Subtitle: Deterministic L7 Ingress Gateway & Consensus Sentinel
    - Badge: ARBITRUM NITRO & ORBIT INFRASTRUCTURE
    - Smooth fade-in from black
    """
    def __init__(self, fps: int = 30) -> None:
        super().__init__(0, "Intro Bumper", "INTRO", 2.0, fps)

    def render(
        self,
        frame_idx: int,
        img: Image.Image,
        draw: ImageDraw.Draw,
        fonts: FontManager,
        shield: Image.Image,
        glow: Image.Image,
        w: int,
        h: int
    ) -> None:
        t = frame_idx / max(1, self.fps)
        fade = min(1.0, t / 0.45)

        cx = w // 2
        cy = 440

        # Radial glow aura
        pulse = 0.5 + 0.5 * math.sin(t * 3.5)
        glow_size = int(360 + pulse * 45)
        glow_scaled = glow.resize((glow_size, glow_size), Image.Resampling.BILINEAR)
        img.paste(glow_scaled, (cx - glow_size // 2, cy - glow_size // 2), glow_scaled)

        # Expanding pulse ring
        ring_r = int((t * 90) % 200)
        if ring_r > 20:
            draw.ellipse([cx - ring_r, cy - ring_r, cx + ring_r, cy + ring_r], outline=(40, 160, 240), width=1)

        # Official Logo
        logo_size = 220
        sh_large = shield.resize((logo_size, logo_size), Image.Resampling.LANCZOS)
        img.paste(sh_large, (cx - logo_size // 2, cy - logo_size // 2), sh_large)

        # Title
        title = "DRIFTGUARD"
        tb = draw.textbbox((0, 0), title, font=fonts.hero_font)
        draw.text((cx - (tb[2] - tb[0]) // 2, cy + 140), title, font=fonts.hero_font, fill=WHITE)

        # Subtitle
        sub = "Deterministic L7 Ingress Gateway & Consensus Sentinel"
        sb = draw.textbbox((0, 0), sub, font=fonts.h1_font)
        draw.text((cx - (sb[2] - sb[0]) // 2, cy + 205), sub, font=fonts.h1_font, fill=CYAN)

        # Badge
        badge_txt = "ARBITRUM NITRO & ORBIT INFRASTRUCTURE"
        bb = draw.textbbox((0, 0), badge_txt, font=fonts.small_bold)
        draw_badge(draw, cx - (bb[2] - bb[0]) // 2 - 14, cy + 250, badge_txt, fonts.small_bold,
                   bg_color=CARD_BG, text_color=EMERALD, border_color=EMERALD)

        # Fade in overlay from dark
        if fade < 1.0:
            overlay = Image.new("RGBA", (w, h), (BG_COLOR[0], BG_COLOR[1], BG_COLOR[2], int(255 * (1.0 - fade))))
            img.paste(overlay, (0, 0), overlay)


# -----------------------------------------------------------------------------
# Scene 1: Overview & Hero Metrics (Rule of Thirds Anchored)
# -----------------------------------------------------------------------------
class SceneIntro(Scene):
    """
    Scene 1:
    - Header & Brand Zone: y < 180px
    - Focal Anchors: Shield at x = 640px (1/3), Architecture Mission at x = 1280px (2/3)
    - Lower Third: 4 metric cards along y: 725..968 baseline
    """
    def __init__(self, fps: int = 30, duration: float = 10.5) -> None:
        super().__init__(1, "Overview", "01 OVERVIEW", duration, fps)

    def render(
        self,
        frame_idx: int,
        img: Image.Image,
        draw: ImageDraw.Draw,
        fonts: FontManager,
        shield: Image.Image,
        glow: Image.Image,
        w: int,
        h: int
    ) -> None:
        t = frame_idx / self.fps

        # 1. Header Zone (y < 160px)
        draw_scene_header(
            draw, fonts,
            title="DriftGuard Ingress Sentinel",
            subtitle="Deterministic L7 Ingress Gateway & Out-of-Band Consensus Watchdog"
        )


        # 2. Primary Focal Anchors (Rule of Thirds: y = 210..720)
        # Left Anchor: Centered at left third (x = 520, center_y = 440)
        left_cx = 520
        center_y = 440
        pulse = 0.5 + 0.5 * math.sin(t * 3.0)
        glow_size = int(270 + pulse * 45)
        glow_scaled = glow.resize((glow_size, glow_size), Image.Resampling.BILINEAR)
        img.paste(glow_scaled, (left_cx - glow_size // 2, center_y - 105 - glow_size // 2), glow_scaled)

        wave_radius = int((t * 80) % 210)
        if wave_radius > 15:
            draw.ellipse([
                (left_cx - wave_radius, center_y - 105 - wave_radius),
                (left_cx + wave_radius, center_y - 105 + wave_radius)
            ], outline=(40, 160, 240), width=1)

        sh_icon = shield.resize((175, 175), Image.Resampling.LANCZOS)
        sh_w, sh_h = sh_icon.size
        img.paste(sh_icon, (left_cx - sh_w // 2, center_y - 105 - sh_h // 2), sh_icon)

        hero_title = "DriftGuard"
        ht_box = draw.textbbox((0, 0), hero_title, font=fonts.hero_font)
        draw.text((left_cx - (ht_box[2] - ht_box[0]) // 2, center_y + 35), hero_title, font=fonts.hero_font, fill=WHITE)

        hero_sub = "Deterministic L7 Ingress Gateway"
        hs_box = draw.textbbox((0, 0), hero_sub, font=fonts.h2_font)
        draw.text((left_cx - (hs_box[2] - hs_box[0]) // 2, center_y + 105), hero_sub, font=fonts.h2_font, fill=CYAN)

        badge_txt = "SUB-MILLISECOND ROUTING  •  ZERO PACKET LOSS"
        b_box = draw.textbbox((0, 0), badge_txt, font=fonts.small_bold)
        draw_badge(draw, left_cx - (b_box[2] - b_box[0]) // 2 - 14, center_y + 155, badge_txt, fonts.small_bold,
                   bg_color=CARD_BG, text_color=EMERALD, border_color=EMERALD)

        # Right Anchor: Consensus Sentinel Mission Card (x: 980, y: 210, w: 860, h: 510)
        card_w_hero = 860
        card_h_hero = FOCAL_END_Y - FOCAL_START_Y  # 510px (Rule of Thirds 2/3 baseline at y=720)
        anchor_2_x = 980

        mission_bullets = [
            "Deterministic L7 Ingress Gateway for sub-second block velocity rollups.",
            "Decouples JSON-RPC transport from asynchronous consensus verification.",
            "Multi-provider quorum engine with cryptographic parent-hash lineage validation.",
            "4-state hysteresis controller dampening transient latency spikes and flapping.",
            "Zero-blackhole Minimum-Healthy Guardrail preserving live traffic routing.",
            "Runs as a standalone sidecar container in under 45 MB of RAM."
        ]
        mission_metrics = [
            ("SPEC", "EVM & ORBIT"),
            ("DRAIN SLA", "< 130ms"),
            ("FOOTPRINT", "< 45 MB")
        ]
        draw_card(
            draw, anchor_2_x, FOCAL_START_Y, card_w_hero, card_h_hero,
            title="Consensus Sentinel Mission",
            subtitle="Deterministic Edge Ingress Protection",
            bullets=mission_bullets,
            fonts=fonts,
            border_color=CARD_BORDER_ACTIVE,
            tag="CONSENSUS SENTINEL",
            tag_color=EMERALD,
            wrap_width=58,
            metrics=mission_metrics
        )


# -----------------------------------------------------------------------------
# Scene 2: The Core Problem: Silent 200 OK Staleness (Split Comparison)
# -----------------------------------------------------------------------------
class SceneProblem(Scene):
    """
    Scene 2:
    - Header & Brand Zone: y < 180px
    - Focal Anchors: Split comparison columns centered at x = 640px and x = 1280px
    - Lower Third: 3 production impact failure cards along y: 725..968 baseline
    """
    def __init__(self, fps: int = 30, duration: float = 11.0) -> None:
        super().__init__(2, "The Problem", "02 THE PROBLEM", duration, fps)

    def render(
        self,
        frame_idx: int,
        img: Image.Image,
        draw: ImageDraw.Draw,
        fonts: FontManager,
        shield: Image.Image,
        glow: Image.Image,
        w: int,
        h: int
    ) -> None:
        t = frame_idx / self.fps

        # 1. Header Zone (y < 160px)
        draw_scene_header(
            draw, fonts,
            title="The Silent 200 OK Staleness Trap",
            subtitle="Why Standard Layer 7 Load Balancers Fail Blockchain Workloads"
        )

        # 2. Primary Focal Anchors: Split Comparison (Rule of Thirds: y = 210..720)
        col_w = 860
        col_h = FOCAL_END_Y - FOCAL_START_Y  # 510px
        left_x = MARGIN_X
        right_x = w - MARGIN_X - col_w

        # Left Column: Standard Load Balancer
        std_bullets = [
            "Probes GET /healthz or TCP connect: receives HTTP 200 OK.",
            "Node process is alive, but blockchain consensus engine is frozen.",
            "Stuck at stale block height while canonical sequencer tip advances.",
            "Keeps routing live user and relayer transactions to desynced node.",
            "Silent failure: zero 5xx errors recorded in cloud metrics dashboards.",
            "Relayers submit stale nonces causing transaction rejection storms."
        ]
        std_metrics = [
            ("DRIFT VISIBILITY", "0% BLIND"),
            ("PROBING", "HTTP 200 OK"),
            ("FAILURE", "NONCE TOO LOW")
        ]
        draw_card(
            draw, left_x, FOCAL_START_Y, col_w, col_h,
            title="Standard Transport Load Balancer",
            subtitle="Blind L4 / L7 Transport Probing",
            bullets=std_bullets,
            fonts=fonts,
            border_color=RED,
            tag="HTTP 200 OK (BLIND ROUTING)",
            tag_color=RED,
            wrap_width=58,
            metrics=std_metrics
        )

        # Right Column: DriftGuard Out-of-Band Sentinel
        dg_bullets = [
            "Out-of-band consensus verification sampling independent references.",
            "Evaluates block numbers, tip hashes, and parent hash continuity.",
            "Detects consensus lag and isolates stale upstreams in under 130ms.",
            "Commands HAProxy via UNIX domain socket without client disconnects.",
            "Drains node cleanly without dropping in-flight TCP connections.",
            "Zero client modifications: transparent drop-in reverse proxy."
        ]
        dg_metrics = [
            ("DETECTION", "< 130ms"),
            ("ERROR RATE", "0.00%"),
            ("TCP DROPS", "0")
        ]
        draw_card(
            draw, right_x, FOCAL_START_Y, col_w, col_h,
            title="DriftGuard Consensus Sentinel",
            subtitle="Active Tip Verification & Instant Draining",
            bullets=dg_bullets,
            fonts=fonts,
            border_color=EMERALD,
            tag="CONSENSUS AWARE (DRAINED)",
            tag_color=EMERALD,
            wrap_width=58,
            metrics=dg_metrics
        )


# -----------------------------------------------------------------------------
# Scene 3: Dual-Plane Architecture & Instant Draining
# -----------------------------------------------------------------------------
class SceneArchitecture(Scene):
    """
    Scene 3:
    - Header & Brand Zone: y < 180px
    - Focal Anchors: Data Plane (HAProxy) at x = 640px, Control Plane (Sentinel) at x = 1280px
    - Lower Third: Socket Cutover SLA and Node Status Footers along y: 725..968 baseline
    """
    def __init__(self, fps: int = 30, duration: float = 13.0) -> None:
        super().__init__(3, "Architecture", "03 ARCHITECTURE", duration, fps)

    def render(
        self,
        frame_idx: int,
        img: Image.Image,
        draw: ImageDraw.Draw,
        fonts: FontManager,
        shield: Image.Image,
        glow: Image.Image,
        w: int,
        h: int
    ) -> None:
        t = frame_idx / self.fps

        # 1. Header Zone (y < 160px)
        draw_scene_header(
            draw, fonts,
            title="Multi-Provider Quorum & Hysteresis FSM",
            subtitle="Cryptographic Lineage Verification & Flap Dampening Controller"
        )

        # 2. Primary Focal Anchors: Dual Planes (Rule of Thirds: y = 210..720)
        plane_w = 820
        plane_h = FOCAL_END_Y - FOCAL_START_Y  # 510px
        left_x = MARGIN_X
        right_x = w - MARGIN_X - plane_w

        # Left Anchor: Quorum Consensus Engine
        quorum_bullets = [
            "Samples N=3 independent reference providers every 200 milliseconds.",
            "Equal height verification: block hashes must match identically.",
            "Lineage verification: block(h) parent hash must match block(h-1) tip hash.",
            "Two-thirds majority consensus: 2 matching providers isolate rogue outliers.",
            "Rogue reference jitter does not trigger false drains on healthy local nodes.",
            "Fail-Open principle: ambiguous or lost quorum freezes routing state safely."
        ]
        quorum_metrics = [
            ("QUORUM", "2/3 MAJORITY"),
            ("LINEAGE", "SHA256 LINK"),
            ("FAIL-OPEN", "FROZEN STATE")
        ]
        draw_card(
            draw, left_x, FOCAL_START_Y, plane_w, plane_h,
            title="Multi-Provider Quorum Engine",
            subtitle="N=3 Consensus & Lineage Validation",
            bullets=quorum_bullets,
            fonts=fonts,
            border_color=CYAN,
            tag="2/3 MAJORITY QUORUM",
            tag_color=CYAN,
            wrap_width=56,
            metrics=quorum_metrics
        )

        # Right Anchor: 4-State Hysteresis Controller (FSM)
        fsm_bullets = [
            "State machine lifecycle: HEALTHY -> SUSPECT -> DRAINED -> RECOVERING.",
            "First lag tick (>= 4 blocks): node marked SUSPECT without immediate drain.",
            "Drained actuation: triggered after K=3 consecutive suspect ticks.",
            "Immediate cutover: parent-hash fork divergence bypasses counters.",
            "Recovery dampening: requires M=5 consecutive synchronized ticks.",
            "Minimum-Healthy Guardrail: refuses drain if healthy backends <= 1."
        ]
        fsm_metrics = [
            ("FSM STATES", "4 DISCRETE"),
            ("DRAIN (K)", "3 TICKS"),
            ("RECOVERY (M)", "5 TICKS")
        ]
        draw_card(
            draw, right_x, FOCAL_START_Y, plane_w, plane_h,
            title="4-State Hysteresis Controller",
            subtitle="Hysteresis Dampening & Safe Actuation",
            bullets=fsm_bullets,
            fonts=fonts,
            border_color=ARBITRUM_BLUE,
            tag="FSM CONTROLLER",
            tag_color=ARBITRUM_BLUE,
            wrap_width=56,
            metrics=fsm_metrics
        )

        # Animated Connector Arrow between Planes
        arrow_y = FOCAL_START_Y + plane_h // 2
        draw.line([(left_x + plane_w, arrow_y), (right_x, arrow_y)], fill=CYAN, width=2)
        socket_tag = "UNIX DRAIN (<130ms)"
        st_box = draw.textbbox((0, 0), socket_tag, font=fonts.mono_small)
        st_w = st_box[2] - st_box[0]
        draw_badge(draw, (w - st_w) // 2 - 12, arrow_y - 28, socket_tag, fonts.mono_small,
                   bg_color=CARD_BG, text_color=CYAN, border_color=CARD_BORDER)


# -----------------------------------------------------------------------------
# Scene 4: Developer Quick Start (Terminal & Config Composition)
# -----------------------------------------------------------------------------
class SceneQuickStart(Scene):
    """
    Scene 4:
    - Header & Brand Zone: y < 180px
    - Focal Anchors: Terminal Window at x = 640px, Chains Config Window at x = 1280px
    - Lower Third: 3 deployment metric cards along y: 725..968 baseline
    """
    def __init__(self, fps: int = 30, duration: float = 11.0) -> None:
        super().__init__(4, "Quick Start", "04 QUICKSTART", duration, fps)

    def render(
        self,
        frame_idx: int,
        img: Image.Image,
        draw: ImageDraw.Draw,
        fonts: FontManager,
        shield: Image.Image,
        glow: Image.Image,
        w: int,
        h: int
    ) -> None:
        t = frame_idx / self.fps

        # 1. Header Zone (y < 160px)
        draw_scene_header(
            draw, fonts,
            title="Quick Start & Deterministic Verification",
            subtitle="60-Second Chaos Acceptance Suite & Production Topology"
        )

        # 2. Primary Focal Anchors: Dual Terminal / Code Windows (Rule of Thirds: y = 210..720)
        win_w = 860
        win_h = FOCAL_END_Y - FOCAL_START_Y  # 510px
        left_x = MARGIN_X
        right_x = w - MARGIN_X - win_w

        # Left Window: Shell Commands Terminal
        term_lines = [
            "# 1. Clone DriftGuard repository",
            "$ git clone https://github.com/maskalfreeup-glitch/driftguard.git",
            "$ cd driftguard",
            "",
            "# 2. Run deterministic chaos testbed (< 60s)",
            "$ make test-chaos",
            "✔ Starting mock reference nodes (ref-a, ref-b, ref-c)",
            "✔ Starting local target node & fallback replica",
            "✔ Starting HAProxy 2.8 gateway on port :8545",
            "✔ Generating 200-400 req/s multi-threaded load",
            "✔ Scenario 1: Baseline load -> 0 false drains [PASS]",
            "✔ Scenario 2: Outlier reference lag -> Isolated [PASS]",
            "✔ Scenario 3: Local stall -> Drained in 132.51ms [PASS]",
            "✔ Recovery verified after M=5 ticks in 259.68ms [PASS]",
            "✔ Total HTTP 5xx errors: 0 (0.00%) [PASS]"
        ]

        term_metrics = [
            ("SUITE", "CHAOS ACCEPTANCE"),
            ("LOAD", "200-400 RPS"),
            ("STATUS", "ALL PASS")
        ]
        visible_lines = min(len(term_lines), int(t * 3.2) + 2)
        draw_terminal_window(
            draw, left_x, FOCAL_START_Y, win_w, win_h,
            title="Terminal — bash (make test-chaos)",
            lines=term_lines[:visible_lines],
            fonts=fonts,
            cursor_line=visible_lines - 1,
            cursor_col=24,
            metrics=term_metrics
        )

        # Right Window: sentinel/config/chains.yaml Specification
        config_lines = [
            "# sentinel/config/chains.yaml",
            "- name: \"arbitrum-one\"",
            "  chain_id: 42161",
            "  backend: \"be_arb\"",
            "  poll_interval: 0.2",
            "  drift_threshold: 4",
            "  failure_threshold: 3",
            "  recovery_threshold: 5",
            "  nodes:",
            "    primary: \"http://nitro-node:8547\"",
            "    fallback: \"https://fallback-rpc:8547\"",
            "  references:",
            "    - \"https://ref-rpc-a:8547\"",
            "    - \"https://ref-rpc-b:8547\"",
            "    - \"https://ref-rpc-c:8547\""
        ]
        config_metrics = [
            ("CONFIG", "CHAINS.YAML"),
            ("POLL", "200ms"),
            ("THRESHOLD", "4 BLOCKS")
        ]
        draw_terminal_window(
            draw, right_x, FOCAL_START_Y, win_w, win_h,
            title="sentinel/config/chains.yaml — Topology Spec",
            lines=config_lines,
            fonts=fonts,
            metrics=config_metrics
        )


# -----------------------------------------------------------------------------
# Scene 5: Developer Verification & Live Chaos Failover Drill
# -----------------------------------------------------------------------------
class SceneLiveDrill(Scene):
    """
    Scene 5:
    - Header & Brand Zone: y < 180px
    - Focal Anchors: RPC Inspection Terminal at x = 640px, Chaos Drill Terminal at x = 1280px
    - Lower Third: 4 empirical verification status footers along y: 725..968 baseline
    """
    def __init__(self, fps: int = 30, duration: float = 10.0) -> None:
        super().__init__(5, "Failover Drill", "05 FAILOVER DRILL", duration, fps)

    def render(
        self,
        frame_idx: int,
        img: Image.Image,
        draw: ImageDraw.Draw,
        fonts: FontManager,
        shield: Image.Image,
        glow: Image.Image,
        w: int,
        h: int
    ) -> None:
        t = frame_idx / self.fps

        # 1. Header Zone (y < 160px)
        draw_scene_header(
            draw, fonts,
            title="Chaos Benchmark & Empirical SLA Results",
            subtitle="Ground-Truth Oracle Validation Under 200–400 req/s Load"
        )

        # 2. Primary Focal Anchors: Terminal & Summary Card (Rule of Thirds: y = 210..720)
        win_w = 860
        win_h = FOCAL_END_Y - FOCAL_START_Y  # 510px
        left_x = MARGIN_X
        right_x = w - MARGIN_X - win_w

        # Left Window: python3 tests/chaos/runner.py
        is_drill_active = (t >= 2.5)
        drill_lines = [
            "$ python3 tests/chaos/runner.py",
            "[*] Generating 200-400 req/s load on :8545",
            "[*] Oracle ground-truth poller active at :9090",
            "[Scenario 1] 5s baseline: 285.2 req/s -> 0 false drains [PASS]",
            "[Scenario 2] Injecting 10-block lag on Reference C",
            "  -> Quorum Engine: 2/3 majority reached; C isolated",
            "  -> Local node routing preserved [PASS]",
            "[Scenario 3] Injecting 8-block stall on Local Node",
            "  -> DRAINED transition confirmed via UNIX socket",
            "  -> Detection Latency: 132.51 ms (< 350 ms limit) [PASS]",
            "  -> Fallback actively serving in-flight client traffic",
            "  -> Tip sync restored: Recovered in 259.68 ms [PASS]",
            "  -> Total HTTP 5xx errors: 0 (0.00%) [PASS]"
        ] if is_drill_active else [
            "$ python3 tests/chaos/runner.py",
            "[*] Generating 200-400 req/s load on :8545",
            "[*] Oracle ground-truth poller active at :9090",
            "[Scenario 1] 5s baseline: 285.2 req/s -> 0 false drains [PASS]",
            "[Scenario 2] Injecting 10-block lag on Reference C...",
            "[Scenario 3] Injecting 8-block stall on Local Node..."
        ]

        drill_metrics = [
            ("DETECTION", "132.51 ms"),
            ("RECOVERY", "259.68 ms"),
            ("HTTP 5XX", "0 (0.00%)")
        ]
        draw_terminal_window(
            draw, left_x, FOCAL_START_Y, win_w, win_h,
            title="python3 tests/chaos/runner.py — Chaos Benchmark",
            lines=drill_lines,
            fonts=fonts,
            metrics=drill_metrics
        )

        # Right Card: Official Benchmark Summary Table
        summary_bullets = [
            "Detection Latency: 132.51 ms (Spec limit: < 350 ms) -> PASS",
            "Recovery Latency: 259.68 ms (M=5 consecutive ticks) -> PASS",
            "Total Stale Reads Leaked: 35 reads under active stall -> PASS",
            "False-Positive Drains: 0 during baseline and jitter -> PASS",
            "HTTP 5xx Error Rate: 0 (0.00% packet loss) -> PASS",
            "POSIX UNIX Socket Drain: atomic cutover without client reconnects."
        ]
        summary_metrics = [
            ("SLA TARGET", "< 350ms"),
            ("MEASURED", "132.51ms"),
            ("STATUS", "ALL PASS")
        ]
        draw_card(
            draw, right_x, FOCAL_START_Y, win_w, win_h,
            title="Deterministic Benchmark Summary",
            subtitle="Verified Empirical SLA Acceptance Criteria",
            bullets=summary_bullets,
            fonts=fonts,
            border_color=EMERALD,
            tag="BENCHMARK ACCEPTED",
            tag_color=EMERALD,
            wrap_width=58,
            metrics=summary_metrics
        )


# -----------------------------------------------------------------------------
# Scene 6: Deployment Targets & Production Testbed
# -----------------------------------------------------------------------------
class SceneSummary(Scene):
    """
    Scene 6:
    - Header & Brand Zone: y < 180px
    - Focal Anchors: Orbit Rollups Card at x = 640px, ERC-4337 Card at x = 1280px
    - Lower Third: Validator Cluster & Reference Endpoint Cards along y: 725..968 baseline
    """
    def __init__(self, fps: int = 30, duration: float = 8.5) -> None:
        super().__init__(6, "Ecosystem", "06 ECOSYSTEM", duration, fps)

    def render(
        self,
        frame_idx: int,
        img: Image.Image,
        draw: ImageDraw.Draw,
        fonts: FontManager,
        shield: Image.Image,
        glow: Image.Image,
        w: int,
        h: int
    ) -> None:
        t = frame_idx / self.fps

        # 1. Header Zone (y < 160px)
        draw_scene_header(
            draw, fonts,
            title="Ecosystem Deployment Targets",
            subtitle="Built for Orbit Rollup Operators, High-Throughput Relayers & Validator Clusters"
        )

        # 2. Primary Focal Anchors: Dual Target Cards (Rule of Thirds: y = 210..720)
        card_w = 860
        card_h = FOCAL_END_Y - FOCAL_START_Y  # 510px
        left_x = MARGIN_X
        right_x = w - MARGIN_X - card_w

        # Left Anchor: Orbit L3 Rollup Operators
        orbit_bullets = [
            "Deploy alongside custom Orbit chain validator nodes.",
            "Shields dApp users from sequencer micro-batch freezes.",
            "Eliminates player dropouts in high-speed gaming rollups.",
            "Automatic drain and recovery without manual intervention.",
            "Compatible with Arbitrum AnyTrust and rollup execution modes.",
            "Protects on-chain gaming state machines from consensus desync."
        ]
        orbit_metrics = [
            ("DEPLOYMENT", "SIDECAR CONTAINER"),
            ("MODE", "ANYTRUST & ROLLUP"),
            ("FAILOVER", "ZERO LOSS")
        ]
        draw_card(
            draw, left_x, FOCAL_START_Y, card_w, card_h,
            title="Orbit L3 Rollup Operators",
            subtitle="Dedicated Node Ingress Sidecar",
            bullets=orbit_bullets,
            fonts=fonts,
            border_color=ARBITRUM_BLUE,
            tag="ORBIT ROLLUPS",
            tag_color=ARBITRUM_BLUE,
            wrap_width=58,
            metrics=orbit_metrics
        )

        # Right Anchor: Session Relayers & Paymasters
        relayer_bullets = [
            "Prevents catastrophic 'nonce too low' transaction reverts.",
            "Guarantees that all signed transactions read synchronized heads.",
            "Decouples trading daemons from stale validator heads.",
            "Zero code changes required in client SDKs or paymasters.",
            "Drop-in sidecar for ERC-4337 bundlers and custom relayers.",
            "Multi-chain support: Arbitrum One, Nova, Sepolia, Orbit L3."
        ]
        relayer_metrics = [
            ("INTEGRATION", "ERC-4337 BUNDLERS"),
            ("NONCE DRIFT", "0% REVERTS"),
            ("HEAD", "CANONICAL")
        ]
        draw_card(
            draw, right_x, FOCAL_START_Y, card_w, card_h,
            title="Session Relayers & Paymasters",
            subtitle="ERC-4337 Account Abstraction",
            bullets=relayer_bullets,
            fonts=fonts,
            border_color=EMERALD,
            tag="ERC-4337 RELAYERS",
            tag_color=EMERALD,
            wrap_width=58,
            metrics=relayer_metrics
        )


# -----------------------------------------------------------------------------
# Scene 7: Open Source & Developer Resources
# -----------------------------------------------------------------------------
class SceneOutroCommunity(Scene):
    """
    Scene 7:
    - Header & Brand Zone: y < 160px
    - Rule of Thirds Anchors: Left card x: 60..920, Right card x: 1000..1860, y: 210..720 (ROT_Y2)
    - Bottom Metric Tray: Status, License, and Repository telemetry
    """
    def __init__(self, fps: int = 30, duration: float = 11.0) -> None:
        super().__init__(7, "Open Source", "07 OPEN SOURCE", duration, fps)

    def render(
        self,
        frame_idx: int,
        img: Image.Image,
        draw: ImageDraw.Draw,
        fonts: FontManager,
        shield: Image.Image,
        glow: Image.Image,
        w: int,
        h: int
    ) -> None:
        t = frame_idx / self.fps

        # 1. Header Zone (y < 160px)
        draw_scene_header(
            draw, fonts,
            title="Open Source & Developer Resources",
            subtitle="Production Ingress Gateway & Consensus Sentinel for Arbitrum Chains"
        )

        # 2. Primary Focal Anchors: Dual Target Cards (y: 210..720)
        card_w = 860
        card_h = 510
        left_x = MARGIN_X
        right_x = w - MARGIN_X - card_w

        # Left Anchor: GitHub Repository & Core Engine
        github_bullets = [
            "Public repository: github.com/maskalfreeup-glitch/driftguard",
            "Permissive MIT license: fully open for commercial and community use.",
            "Complete test suite: unit tests, chaos benchmark runner, mock RPC engines.",
            "Full source code for quorum engine, hysteresis FSM, and HAProxy templates.",
            "Comprehensive CI/CD pipelines and reproducible Docker Compose recipes.",
            "Contributions welcome: submit pull requests, issues, or RFC proposals."
        ]
        github_metrics = [
            ("REPOSITORY", "GITHUB"),
            ("LICENSE", "MIT"),
            ("TESTS", "PASSING")
        ]
        draw_card(
            draw, left_x, FOCAL_START_Y, card_w, card_h,
            title="GitHub Repository & Core Engine",
            subtitle="Open Source Consensus Sentinel",
            bullets=github_bullets,
            fonts=fonts,
            border_color=ARBITRUM_BLUE,
            tag="OPEN SOURCE REPOSITORY",
            tag_color=ARBITRUM_BLUE,
            wrap_width=58,
            metrics=github_metrics
        )

        # Right Anchor: Documentation & Reference Deployment
        docs_bullets = [
            "Official documentation portal: docs.driftguard.live",
            "Interactive quickstart guides, topology diagrams, and runbooks.",
            "Live Arbitrum One reference endpoint: rpc.driftguard.live",
            "Zero-overhead metrics exporter with pre-built Grafana dashboards.",
            "Enterprise HAProxy configuration with dynamic socket reloads.",
            "Drop-in compatibility with Arbitrum Orbit, Nova, and Nitro rollups."
        ]
        docs_metrics = [
            ("DOCS", "DOCS.DRIFTGUARD.LIVE"),
            ("RPC", "RPC.DRIFTGUARD.LIVE"),
            ("STATUS", "ACTIVE")
        ]
        draw_card(
            draw, right_x, FOCAL_START_Y, card_w, card_h,
            title="Documentation & Reference Deployment",
            subtitle="Production Endpoints & Operations Manual",
            bullets=docs_bullets,
            fonts=fonts,
            border_color=EMERALD,
            tag="DOCUMENTATION & ENDPOINTS",
            tag_color=EMERALD,
            wrap_width=58,
            metrics=docs_metrics
        )


# -----------------------------------------------------------------------------
# Outro Logo Frame: 2.0 Second Cinematic Resolve Bumper
# -----------------------------------------------------------------------------
class SceneOutroLogo(Scene):
    """
    2-second cinematic outro logo bumper:
    - Official DriftGuard logo with radial glow
    - Title: DRIFTGUARD
    - Tagline: High-Availability EVM Gateway & Consensus Sentinel
    - Community links & MIT licensing
    - Smooth fade-out to black
    """
    def __init__(self, fps: int = 30) -> None:
        super().__init__(99, "Outro Bumper", "OUTRO", 2.0, fps)

    def render(
        self,
        frame_idx: int,
        img: Image.Image,
        draw: ImageDraw.Draw,
        fonts: FontManager,
        shield: Image.Image,
        glow: Image.Image,
        w: int,
        h: int
    ) -> None:
        t = frame_idx / max(1, self.fps)
        rem_t = self.duration_sec - t
        fade = min(1.0, rem_t / 0.45)

        cx = w // 2
        cy = 400

        # Radial glow aura
        pulse = 0.5 + 0.5 * math.sin(t * 3.5)
        glow_size = int(340 + pulse * 40)
        glow_scaled = glow.resize((glow_size, glow_size), Image.Resampling.BILINEAR)
        img.paste(glow_scaled, (cx - glow_size // 2, cy - glow_size // 2), glow_scaled)

        # Official Logo
        logo_size = 200
        sh_large = shield.resize((logo_size, logo_size), Image.Resampling.LANCZOS)
        img.paste(sh_large, (cx - logo_size // 2, cy - logo_size // 2), sh_large)

        # Title
        title = "DRIFTGUARD"
        tb = draw.textbbox((0, 0), title, font=fonts.hero_font)
        draw.text((cx - (tb[2] - tb[0]) // 2, cy + 130), title, font=fonts.hero_font, fill=WHITE)

        # Tagline
        sub = "High-Availability EVM Gateway & Consensus Sentinel"
        sb = draw.textbbox((0, 0), sub, font=fonts.h1_font)
        draw.text((cx - (sb[2] - sb[0]) // 2, cy + 195), sub, font=fonts.h1_font, fill=CYAN)

        # Community Badges / Links
        link_str = "github.com/maskalfreeup-glitch/driftguard  •  docs.driftguard.live  •  rpc.driftguard.live"
        lb = draw.textbbox((0, 0), link_str, font=fonts.mono_title)
        draw_badge(draw, cx - (lb[2] - lb[0]) // 2 - 16, cy + 245, link_str, fonts.mono_title,
                   bg_color=CARD_BG, text_color=EMERALD, border_color=EMERALD, pad_x=16, pad_y=6)

        # License
        lic_txt = "SPDX-License-Identifier: MIT  •  Copyright (c) 2026 DriftGuard Contributors"
        licb = draw.textbbox((0, 0), lic_txt, font=fonts.small_bold)
        draw.text((cx - (licb[2] - licb[0]) // 2, cy + 310), lic_txt, font=fonts.small_bold, fill=TEXT_DARK)

        # Fade-out overlay
        if fade < 1.0:
            overlay = Image.new("RGBA", (w, h), (BG_COLOR[0], BG_COLOR[1], BG_COLOR[2], int(255 * (1.0 - fade))))
            img.paste(overlay, (0, 0), overlay)


# -----------------------------------------------------------------------------
# Global UI Overlay (Collision-Free Centered Header & Progress Scrubber)
# -----------------------------------------------------------------------------
def draw_global_ui(
    img: Image.Image,
    draw: ImageDraw.Draw,
    fonts: FontManager,
    shield: Image.Image,
    scenes: List[Scene],
    current_scene_idx: int,
    frame_idx: int,
    total_frames: int,
    fps: int,
    w: int,
    h: int
) -> None:
    """
    Renders top persistent header bar (y: 0..65) and bottom scrubber (y: 1040..1080).
    Guarantees mathematically centered navigation and zero collision across bands.
    """
    # Top Header Bar (y: 0..52)
    header_h = 52
    draw.rectangle([0, 0, w, header_h], fill=(11, 16, 27))
    draw.line([(0, header_h), (w, header_h)], fill=CARD_BORDER, width=1)

    # Left Brand Block: Icon + DriftGuard (clean typography, no redundant badges)
    sh_icon = shield.resize((28, 28), Image.Resampling.LANCZOS)
    img.paste(sh_icon, (MARGIN_X, 12), sh_icon)
    draw.text((MARGIN_X + 38, 15), "DriftGuard", font=fonts.h2_font, fill=WHITE)

    # Right: Minimal Scene Tracker (e.g. "01 / 07  •  OVERVIEW")
    if 0 <= current_scene_idx < len(scenes):
        sc_num = f"{current_scene_idx + 1:02d} / {len(scenes):02d}"
        sc_name = scenes[current_scene_idx].name.upper()

        num_bb = draw.textbbox((0, 0), sc_num, font=fonts.mono_small)
        num_w = num_bb[2] - num_bb[0]
        sep = "  •  "
        sep_bb = draw.textbbox((0, 0), sep, font=fonts.small_font)
        sep_w = sep_bb[2] - sep_bb[0]
        name_bb = draw.textbbox((0, 0), sc_name, font=fonts.small_bold)
        name_w = name_bb[2] - name_bb[0]

        tot_w = num_w + sep_w + name_w
        x_pos = w - MARGIN_X - tot_w

        draw.text((x_pos, 18), sc_num, font=fonts.mono_small, fill=TEXT_MUTED)
        draw.text((x_pos + num_w, 18), sep, font=fonts.small_font, fill=TEXT_DARK)
        draw.text((x_pos + num_w + sep_w, 18), sc_name, font=fonts.small_bold, fill=CYAN)

    # Bottom Progress Scrubber (y: 1040..1080)
    draw.rectangle([0, SCRUBBER_Y, w, 1080], fill=(11, 16, 27))
    draw.line([(0, SCRUBBER_Y), (w, SCRUBBER_Y)], fill=CARD_BORDER, width=1)

    progress = frame_idx / max(1, total_frames - 1)
    bar_y = 1045
    draw.rectangle([0, bar_y, w, bar_y + 3], fill=(20, 30, 48))
    scrub_w = int(w * progress)
    if scrub_w > 0:
        draw.rectangle([0, bar_y, scrub_w, bar_y + 3], fill=CYAN)
        draw.ellipse([scrub_w - 4, bar_y - 3, scrub_w + 4, bar_y + 6], fill=WHITE)

    cur_sec = int(frame_idx / fps)
    tot_sec = int(total_frames / fps)
    tc_str = f"{cur_sec // 60:02d}:{cur_sec % 60:02d} / {tot_sec // 60:02d}:{tot_sec % 60:02d}"
    tc_box = draw.textbbox((0, 0), tc_str, font=fonts.mono_small)
    tc_w = tc_box[2] - tc_box[0]
    draw.text((w - MARGIN_X - tc_w, 1055), tc_str, font=fonts.mono_small, fill=TEXT_MUTED)


# -----------------------------------------------------------------------------
# Multi-Track Audio Synthesizer (Pristine Studio Narration, No Drone Hum)
# -----------------------------------------------------------------------------
def build_composite_audio(
    output_wav_path: str,
    duration_sec: float,
    scenes: List[Scene],
    voice_clips: Dict[int, str],
    fps: int,
    sample_rate: int = 44100
) -> None:
    """Synthesizes studio audio score with pristine voiceover and subtle typing sounds."""
    total_samples = int(duration_sec * sample_rate)
    master_left = [0.0] * total_samples
    master_right = [0.0] * total_samples

    # Subtle Terminal Typing Clicks (Scenes 4 & 5)
    typing_time_ranges = []
    accum_t = 0.0
    for sc in scenes:
        if sc.scene_id in [4, 5]:
            typing_time_ranges.append((accum_t + 0.5, accum_t + sc.duration_sec - 1.0))
        accum_t += sc.duration_sec

    for (start_t, end_t) in typing_time_ranges:
        start_s = int(start_t * sample_rate)
        end_s = int(end_t * sample_rate)
        click_interval = int(0.12 * sample_rate)
        for click_pos in range(start_s, end_s, click_interval):
            click_len = int(0.012 * sample_rate)
            for j in range(click_len):
                if click_pos + j < total_samples:
                    dt = j / sample_rate
                    click_snd = math.sin(2 * math.pi * 1400 * dt) * math.exp(-dt * 550) * 0.05
                    master_left[click_pos + j] += click_snd
                    master_right[click_pos + j] += click_snd

    # Overlay Studio Voiceover Narration Clips
    accum_time = 0.0
    for sc in scenes:
        wav_file = voice_clips.get(sc.scene_id)
        if wav_file and os.path.isfile(wav_file):
            with wave.open(wav_file, "rb") as w:
                nchannels = w.getnchannels()
                in_framerate = w.getframerate()
                nframes = w.getnframes()
                raw_data = w.readframes(nframes)

                start_sample = int(accum_time * sample_rate)
                sample_count = len(raw_data) // (2 * nchannels)
                step = in_framerate / sample_rate

                for out_idx in range(int(sample_count / step)):
                    target_idx = start_sample + out_idx
                    if target_idx >= total_samples:
                        break
                    in_sample_idx = int(out_idx * step)
                    if in_sample_idx >= sample_count:
                        break
                    byte_offset = in_sample_idx * 2 * nchannels
                    val_int = struct.unpack_from("<h", raw_data, byte_offset)[0]
                    norm_val = (val_int / 32768.0) * 0.95
                    master_left[target_idx] += norm_val
                    master_right[target_idx] += norm_val

        accum_time += sc.duration_sec

    # Write Pristine WAV Output
    with wave.open(output_wav_path, "wb") as out_wav:
        out_wav.setnchannels(2)
        out_wav.setsampwidth(2)
        out_wav.setframerate(sample_rate)
        chunk = bytearray()
        for i in range(total_samples):
            l_val = int(max(-32767, min(32767, master_left[i] * 32767)))
            r_val = int(max(-32767, min(32767, master_right[i] * 32767)))
            chunk.extend(struct.pack("<hh", l_val, r_val))
            if len(chunk) > 65536:
                out_wav.writeframes(chunk)
                chunk = bytearray()
        if chunk:
            out_wav.writeframes(chunk)


# -----------------------------------------------------------------------------
# Main Deterministic Video Pipeline
# -----------------------------------------------------------------------------
def render_video(
    output_mp4: str,
    fps: int = 30,
    width: int = 1920,
    height: int = 1080,
    target_scene_idx: Optional[int] = None,
    use_tts: bool = True,
    voice_name: str = "ryan",
    custom_piper_bin: Optional[str] = None,
    custom_piper_model: Optional[str] = None,
    show_subtitles: bool = True
) -> None:
    """Executes deterministic video generation with FFmpeg."""
    project_root = Path(__file__).resolve().parent.parent

    print("=" * 72)
    print("  DriftGuard — Explainer Video Generator (Rule of Thirds 1080p)")
    print(f"  Resolution: {width}x{height} | FPS: {fps} | Engine: Python PIL + FFmpeg")
    print("=" * 72)

    purge_caches()

    fonts = FontManager()
    shield = load_shield_asset(project_root, size=160)
    glow = create_radial_glow(size=256, color=ARBITRUM_BLUE)

    core_scenes: List[Scene] = [
        SceneIntro(fps=fps),
        SceneProblem(fps=fps),
        SceneArchitecture(fps=fps),
        SceneQuickStart(fps=fps),
        SceneLiveDrill(fps=fps),
        SceneSummary(fps=fps),
        SceneOutroCommunity(fps=fps),
    ]

    intro_bumper = SceneIntroLogo(fps=fps)
    outro_bumper = SceneOutroLogo(fps=fps)

    # Attach cues to scenes
    for sc in core_scenes:
        if sc.scene_id in SCENE_CUES:
            sc.cues = SCENE_CUES[sc.scene_id]

    piper_bin, piper_model = resolve_piper(custom_piper_bin, custom_piper_model, voice_name)
    voice_clips: Dict[int, str] = {}
    temp_dir = tempfile.mkdtemp(prefix="driftguard_video_")

    if target_scene_idx is not None:
        if 1 <= target_scene_idx <= len(core_scenes):
            scenes = [core_scenes[target_scene_idx - 1]]
            print(f"[*] Rendering isolated Scene {target_scene_idx}: {scenes[0].name}")
        else:
            print(f"Error: Invalid scene index {target_scene_idx} (valid: 1..{len(core_scenes)})")
            sys.exit(1)
    else:
        scenes = [intro_bumper] + core_scenes + [outro_bumper]

    if use_tts and piper_bin and piper_model:
        print(f"[*] Local Piper TTS active:")
        print(f"    Binary: {piper_bin}")
        print(f"    Model : {piper_model}")
        print("[*] Generating speech narration clips with subtitle cues...")

        for sc in scenes:
            if not sc.cues:
                continue

            cur_t = 0.40  # 0.4s lead-in into scene
            cue_wavs: List[Tuple[NarrationCue, str, float]] = []

            for c_idx, cue in enumerate(sc.cues):
                cue_path = os.path.join(temp_dir, f"cue_{sc.scene_id}_{c_idx}.wav")
                synthesize_speech_clip(piper_bin, piper_model, cue.tts_text, cue_path, length_scale=0.95)
                with wave.open(cue_path, "rb") as w:
                    cue_dur = w.getnframes() / w.getframerate()
                cue.start_time = cur_t
                cue.end_time = cur_t + cue_dur
                cue_wavs.append((cue, cue_path, cue_dur))
                cur_t = cue.end_time + cue.pause_after

            sc.set_duration(cur_t + 0.6)  # 0.6s grace tail
            print(f"    ✔ Scene {sc.scene_id} ({sc.name}): {len(sc.cues)} cues, {cur_t:.2f}s speech -> {sc.duration_sec:.2f}s scene")

            scene_wav = os.path.join(temp_dir, f"voice_scene_{sc.scene_id}.wav")
            build_scene_wav(scene_wav, sc.duration_sec, cue_wavs)
            voice_clips[sc.scene_id] = scene_wav
    else:
        if use_tts:
            print("[!] Piper TTS not found. Falling back to ambient audio.")
        for sc in scenes:
            if sc.cues:
                cur_t = 0.40
                for cue in sc.cues:
                    cue_dur = max(1.8, len(cue.tts_text.split()) * 0.42)
                    cue.start_time = cur_t
                    cue.end_time = cur_t + cue_dur
                    cur_t = cue.end_time + cue.pause_after
                sc.set_duration(cur_t + 0.6)

    total_frames = sum(sc.total_frames for sc in scenes)
    total_duration = sum(sc.duration_sec for sc in scenes)
    print(f"[*] Total video duration: {total_duration:.1f}s ({total_frames} frames)")
    print("\n[*] Chapter Timestamps:")
    accum_t = 0.0
    for sc in scenes:
        m, s = divmod(int(accum_t), 60)
        print(f"    - {m:02d}:{s:02d} ({accum_t:.2f}s) -> Scene {sc.scene_id}: {sc.name}")
        accum_t += sc.duration_sec
    print()

    combined_wav = os.path.join(temp_dir, "master_soundtrack.wav")
    print("[*] Synthesizing audio score (hum-free, studio narration)...")
    build_composite_audio(combined_wav, total_duration, scenes, voice_clips, fps=fps)
    print(f"✔ Master soundtrack synthesized: {os.path.getsize(combined_wav) / 1024:.1f} KB")

    # Ensure target directory exists
    Path(output_mp4).parent.mkdir(parents=True, exist_ok=True)

    ffmpeg_log_path = os.path.join(temp_dir, "ffmpeg.log")
    ffmpeg_log = open(ffmpeg_log_path, "w")

    ffmpeg_cmd = [
        "ffmpeg", "-y",
        "-loglevel", "warning",
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-s", f"{width}x{height}",
        "-pix_fmt", "rgb24",
        "-r", str(fps),
        "-i", "-",
        "-i", combined_wav,
        "-c:a", "aac",
        "-b:a", "192k",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-preset", "medium",
        "-crf", "18",
        "-shortest",
        output_mp4,
    ]

    print(f"[*] Launching FFmpeg encoder -> {output_mp4}")
    proc = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=ffmpeg_log)

    start_time = time.time()
    global_frame = 0

    try:
        for sc_idx, scene in enumerate(scenes):
            scene_name = scene.name
            is_bumper = isinstance(scene, (SceneIntroLogo, SceneOutroLogo))

            for f_in_scene in range(scene.total_frames):
                img = Image.new("RGB", (width, height), BG_COLOR)
                draw = ImageDraw.Draw(img)

                # Subtle Tech Grid (80px)
                for gx in range(0, width, 80):
                    draw.line([(gx, 0), (gx, height)], fill=(13, 19, 32), width=1)
                for gy in range(0, height, 80):
                    draw.line([(0, gy), (width, gy)], fill=(13, 19, 32), width=1)

                # Subtle Rule of Thirds composition guidelines
                draw.line([(ROT_X1, 0), (ROT_X1, height)], fill=(18, 26, 44), width=1)
                draw.line([(ROT_X2, 0), (ROT_X2, height)], fill=(18, 26, 44), width=1)
                draw.line([(0, ROT_Y1), (width, ROT_Y1)], fill=(18, 26, 44), width=1)
                draw.line([(0, ROT_Y2), (width, ROT_Y2)], fill=(18, 26, 44), width=1)

                # Render Scene Content
                scene.render(f_in_scene, img, draw, fonts, shield, glow, width, height)

                # Subtitles and Global UI Overlay
                if not is_bumper:
                    if show_subtitles:
                        active_sub = scene.get_active_subtitle(f_in_scene)
                        if active_sub:
                            draw_subtitle_pill(draw, fonts, active_sub, width, height)

                    core_idx = (sc_idx - 1) if (scenes[0] == intro_bumper) else sc_idx
                    if target_scene_idx is not None:
                        core_idx = target_scene_idx - 1

                    draw_global_ui(
                        img, draw, fonts, shield, core_scenes,
                        core_idx,
                        global_frame, total_frames, fps, width, height
                    )

                proc.stdin.write(img.tobytes())
                global_frame += 1

                if global_frame % 15 == 0 or global_frame == total_frames:
                    elapsed = time.time() - start_time
                    fps_rate = global_frame / max(0.001, elapsed)
                    eta = (total_frames - global_frame) / max(0.001, fps_rate)
                    pct = int(100 * global_frame / total_frames)
                    bar = "=" * (pct // 4) + ">" + " " * (25 - (pct // 4))
                    sys.stdout.write(
                        f"\r  [{bar}] {pct:3d}% | Frame {global_frame:04d}/{total_frames} | {fps_rate:5.1f} fps | Scene: {scene_name:<14} | ETA: {eta:4.1f}s"
                    )
                    sys.stdout.flush()

    except BrokenPipeError:
        print("\nError: FFmpeg pipe broken unexpectedly.")
        ffmpeg_log.close()
        if os.path.exists(ffmpeg_log_path):
            with open(ffmpeg_log_path, "r") as f:
                print(f.read())
        sys.exit(1)
    finally:
        if proc.stdin:
            try:
                proc.stdin.close()
            except Exception:
                pass
        proc.wait()
        ffmpeg_log.close()
        shutil.rmtree(temp_dir, ignore_errors=True)

    total_time = time.time() - start_time
    print(f"\n\n✔ Video rendering complete in {total_time:.1f}s ({total_frames / total_time:.1f} avg fps)!")
    if os.path.isfile(output_mp4):
        file_size_mb = os.path.getsize(output_mp4) / (1024 * 1024)
        print(f"✔ Output file generated: {output_mp4} ({file_size_mb:.2f} MB)")
    else:
        print(f"Error: Target MP4 {output_mp4} was not created.")
        sys.exit(1)


# -----------------------------------------------------------------------------
# CLI Entrypoint conforming to professional open-source standards
# -----------------------------------------------------------------------------
def parse_args() -> argparse.Namespace:
    """Configures and parses command-line arguments."""
    parser = argparse.ArgumentParser(
        description="DriftGuard — Deterministic Headless Explainer Video Generator (1080p Rule-of-Thirds Composition)",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--output", "-o",
        default="tutorials/driftguard-explainer.mp4",
        help="Output path for the generated MP4 file",
    )
    parser.add_argument(
        "--fps",
        type=int,
        default=30,
        help="Frames per second",
    )
    parser.add_argument(
        "--width",
        type=int,
        default=1920,
        help="Video canvas width in pixels",
    )
    parser.add_argument(
        "--height",
        type=int,
        default=1080,
        help="Video canvas height in pixels",
    )
    parser.add_argument(
        "--scene",
        type=int,
        default=None,
        choices=[1, 2, 3, 4, 5, 6, 7],
        help="Render a single scene index (1 to 7) for rapid inspection",
    )
    parser.add_argument(
        "--preview",
        action="store_true",
        help="Quick draft preview mode (1280x720 at 24fps)",
    )
    parser.add_argument(
        "--no-tts",
        action="store_true",
        help="Disable local Piper TTS speech narration",
    )
    parser.add_argument(
        "--no-subtitles",
        action="store_true",
        help="Disable on-screen subtitle captions",
    )
    parser.add_argument(
        "--voice",
        default="ryan",
        choices=["ryan", "lessac", "joe"],
        help="Piper TTS voice model checkpoint",
    )
    parser.add_argument(
        "--piper-bin",
        default=None,
        help="Custom path to piper binary executable",
    )
    parser.add_argument(
        "--piper-model",
        default=None,
        help="Custom path to piper ONNX model",
    )
    parser.add_argument(
        "--clean-cache",
        action="store_true",
        help="Force delete all cached audio and video clips before rendering",
    )
    return parser.parse_args()


def main() -> None:
    """CLI main entrypoint."""
    args = parse_args()

    if args.clean_cache:
        print("[*] Purging temporary cached files...")
        purge_caches()

    width = 1280 if args.preview else args.width
    height = 720 if args.preview else args.height
    fps = 24 if args.preview else args.fps

    out_path = Path(args.output).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    render_video(
        output_mp4=str(out_path),
        fps=fps,
        width=width,
        height=height,
        target_scene_idx=args.scene,
        use_tts=(not args.no_tts),
        voice_name=args.voice,
        custom_piper_bin=args.piper_bin,
        custom_piper_model=args.piper_model,
        show_subtitles=(not args.no_subtitles),
    )


if __name__ == "__main__":
    main()
