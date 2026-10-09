#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2026 DriftGuard Contributors
"""
DriftGuard - Client Acquisition Positioning Video Generator (YouTube Episode 1)
================================================================================
Renders a broadcast-quality, deterministic 1080p MP4 positioning video
combining deep systems engineering education with high-ticket B2B retainer CTAs.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
import wave
from pathlib import Path
from typing import Dict, List, Optional

from PIL import Image, ImageDraw

# Import core infrastructure from base generator
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    import scripts.generate_explainer_video as gev
except ImportError:
    import generate_explainer_video as gev

# Override / customize Narration cues specifically for Client Acquisition & Teaching
ACQUISITION_CUES: Dict[int, List[gev.NarrationCue]] = {
    1: [
        gev.NarrationCue(
            "Welcome to DriftGuard.",
            "Welcome to DriftGuard."
        ),
        gev.NarrationCue(
            "DriftGuard is an ultra-low-footprint Layer 7 ingress gateway and out-of-band consensus sentinel...",
            "Ultra-low-footprint Layer 7 ingress gateway and consensus sentinel..."
        ),
        gev.NarrationCue(
            "...engineered to solve the silent 200 OK problem for Arbitrum Orbit chains, game servers, and paymasters.",
            "...engineered to solve the Silent 200 OK problem for Orbit chains, games, and paymasters."
        ),
        gev.NarrationCue(
            "It enforces sub-130 millisecond UNIX socket draining with zero dropped TCP connections...",
            "Enforces sub-130ms UNIX socket draining with zero dropped TCP connections..."
        ),
        gev.NarrationCue(
            "...running in under forty-five megabytes of memory.",
            "...running in under 45 MB of RAM."
        ),
    ],
    2: [
        gev.NarrationCue(
            "In Arbitrum Nitro rollups, micro-batches settle every 250 milliseconds.",
            "In Arbitrum Nitro rollups, micro-batches settle every 250 milliseconds."
        ),
        gev.NarrationCue(
            "When an upstream sequencer stalls, standard load balancers return HTTP 200 while lagging blocks behind canonical head.",
            "When an upstream stalls, cloud balancers return HTTP 200 while lagging blocks behind head."
        ),
        gev.NarrationCue(
            "Relayers submit stale nonces, causing severe on-chain transaction reverts and broken onboarding.",
            "Relayers submit stale nonces, causing severe on-chain reverts and broken onboarding."
        ),
    ],
    3: [
        gev.NarrationCue(
            "DriftGuard decouples Layer 7 proxying from consensus checking.",
            "DriftGuard decouples Layer 7 proxying from consensus checking."
        ),
        gev.NarrationCue(
            "The HAProxy data plane forwards client requests with sub-millisecond latency...",
            "The HAProxy data plane forwards client requests with sub-millisecond latency..."
        ),
        gev.NarrationCue(
            "...while the asynchronous Python sentinel queries canonical anchors every 200 milliseconds out-of-band.",
            "...while the asynchronous Python sentinel queries canonical anchors every 200ms out-of-band."
        ),
        gev.NarrationCue(
            "On drift, Sentinel drains the node via a UNIX domain socket in under 130 milliseconds.",
            "On drift, Sentinel drains the node via a UNIX domain socket in under 130ms."
        ),
    ],
    4: [
        gev.NarrationCue(
            "Getting started takes under 60 seconds with our open-source Docker sidecar.",
            "Getting started takes under 60 seconds with our open-source Docker sidecar."
        ),
        gev.NarrationCue(
            "Clone the repository, copy the example environment file to configure your RPC upstreams...",
            "Clone the repo, copy .env.example to configure your RPC upstreams..."
        ),
        gev.NarrationCue(
            "...and launch the stack with docker compose up.",
            "...and launch the stack with: docker compose up -d"
        ),
        gev.NarrationCue(
            "The entire three-container deployment uses less than 120 megabytes of memory.",
            "The entire three-container deployment uses less than 120 MB of RAM."
        ),
    ],
    5: [
        gev.NarrationCue(
            "Verify live edge routing by curling port eighty-five forty-five to inspect custom gateway telemetry headers.",
            "Verify live edge routing by curling port :8545 to inspect custom telemetry headers."
        ),
        gev.NarrationCue(
            "Then run the test failover script to inject synthetic drift.",
            "Then run the test failover script to inject synthetic drift."
        ),
        gev.NarrationCue(
            "HAProxy instantly drains the primary node to maintenance mode, and fallback serves requests with zero errors.",
            "HAProxy instantly drains the primary node, and fallback serves requests with zero errors."
        ),
    ],
    6: [
        gev.NarrationCue(
            "For Orbit rollups, Web3 gaming studios, and E-R-C forty-three thirty-seven paymasters, downtime breaks user onboarding.",
            "For Orbit rollups, gaming studios, and ERC-4337 paymasters, downtime breaks onboarding."
        ),
        gev.NarrationCue(
            "Through our DriftGuard Enterprise Retainer, our systems team manages your active-active ingress gateway with guaranteed 99.99% availability.",
            "Through our Enterprise Retainer, our team manages your active-active ingress with 99.99% availability."
        ),
        gev.NarrationCue(
            "We provide sub-15 minute Sev-1 incident escalation and bi-weekly synthetic chaos injection drills.",
            "We provide sub-15 minute Sev-1 incident escalation and bi-weekly synthetic chaos drills."
        ),
    ],
    7: [
        gev.NarrationCue(
            "You can run our open source sidecar for free under the M-I-T license, or bring DriftGuard on retainer for 24/7 on-call engineering.",
            "Run our open-source sidecar for free, or bring DriftGuard on retainer for 24/7 on-call support."
        ),
        gev.NarrationCue(
            "Book a Free 48-Hour R-P-C Resilience and Staleness Audit at drift guard dot live slash audit, or explore the code on GitHub.",
            "Book a Free 48-Hour RPC Resilience Audit at driftguard.live/audit, or explore the code on GitHub."
        ),
    ],
}


class SceneClientAcquisitionSummary(gev.Scene):
    """
    Scene 6: Enterprise Retainers & SLA Guarantees
    """
    def __init__(self, fps: int = 30, duration: float = 12.0) -> None:
        super().__init__(6, "Enterprise Retainers", "06 ENTERPRISE RETAINERS", duration, fps)

    def render(
        self,
        frame_idx: int,
        img: Image.Image,
        draw: ImageDraw.Draw,
        fonts: gev.FontManager,
        shield: Image.Image,
        glow: Image.Image,
        w: int,
        h: int
    ) -> None:
        gev.draw_scene_header(
            draw, fonts,
            title="Commercial B2B Retainers & SLA Guarantees",
            subtitle="Managed Ingress Orchestration, 24/7 On-Call Support & <15 Min Sev-1 Escalation"
        )

        card_w = 860
        card_h = gev.FOCAL_END_Y - gev.FOCAL_START_Y
        left_x = gev.MARGIN_X
        right_x = w - gev.MARGIN_X - card_w

        # Left Anchor: Enterprise Retainer Tiers
        retainer_bullets = [
            "Tier 1 ($2,500/mo): 3 chain backends, 24/7 automated alerts, monthly audits.",
            "Tier 2 ($5,000/mo): Dedicated HA cluster, <15 min Sev-1 SLA, bi-weekly chaos drills.",
            "Tier 3 ($8,500/mo): Active-active multi-region gateway, 99.99% availability guarantee.",
            "Custom consensus anchor calibration against your private validator nodes.",
            "Dedicated on-call systems engineers for Orbit L3s, Game Studios & Paymasters.",
            "Automated incident embeds dispatched to client Discord, Telegram & PagerDuty."
        ]
        retainer_metrics = [
            ("RETAINER TIERS", "$2.5k - $8.5k/MO"),
            ("SEV-1 SLA", "< 15 MIN"),
            ("AVAILABILITY", "99.99% SLA")
        ]
        gev.draw_card(
            draw, left_x, gev.FOCAL_START_Y, card_w, card_h,
            title="Managed Enterprise Retainers",
            subtitle="Dedicated Infrastructure Operations",
            bullets=retainer_bullets,
            fonts=fonts,
            border_color=gev.EMERALD,
            tag="COMMERCIAL RETAINERS",
            tag_color=gev.EMERALD,
            wrap_width=58,
            metrics=retainer_metrics
        )

        # Right Anchor: Free 48-Hour RPC Resilience Audit
        audit_bullets = [
            "Continuous 48-hour latency jitter & block propagation analysis.",
            "Identification of single points of failure in existing upstream RPC pools.",
            "Evaluation of paymaster nonce flapping & transaction revert vulnerabilities.",
            "Comprehensive written Resilience Scorecard delivered at zero cost.",
            "Monitored failover simulation without touching production user traffic.",
            "Private 30-minute architecture review call with our core systems team."
        ]
        audit_metrics = [
            ("AUDIT COST", "$0 (FREE)"),
            ("DURATION", "48 HOURS"),
            ("DELIVERABLE", "SCORECARD")
        ]
        gev.draw_card(
            draw, right_x, gev.FOCAL_START_Y, card_w, card_h,
            title="Free 48-Hour RPC Resilience Audit",
            subtitle="Empirical Single-Point-of-Failure Assessment",
            bullets=audit_bullets,
            fonts=fonts,
            border_color=gev.ARBITRUM_BLUE,
            tag="FREE AUDIT LEAD MAGNET",
            tag_color=gev.ARBITRUM_BLUE,
            wrap_width=58,
            metrics=audit_metrics
        )


class SceneClientAcquisitionOutro(gev.Scene):
    """
    Scene 7: Book Your Audit & Open Source Resources
    """
    def __init__(self, fps: int = 30, duration: float = 12.0) -> None:
        super().__init__(7, "Schedule Audit", "07 GET STARTED", duration, fps)

    def render(
        self,
        frame_idx: int,
        img: Image.Image,
        draw: ImageDraw.Draw,
        fonts: gev.FontManager,
        shield: Image.Image,
        glow: Image.Image,
        w: int,
        h: int
    ) -> None:
        gev.draw_scene_header(
            draw, fonts,
            title="Get Started: Book an Audit or Run the Sidecar",
            subtitle="Open Source Public Good (MIT) + Managed B2B Retainers for Enterprise Rollups"
        )

        card_w = 860
        card_h = 510
        left_x = gev.MARGIN_X
        right_x = w - gev.MARGIN_X - card_w

        # Left Anchor: Schedule Free Audit
        audit_cta_bullets = [
            "Book your Free 48-Hour Audit online: driftguard.live/audit",
            "Zero cost empirical diagnosis for Orbit rollups, games & paymasters.",
            "Empirical ranking of your upstream RPC vendors (Alchemy, QuickNode, Private).",
            "Custom HAProxy & Sentinel configuration blueprint provided.",
            "Dedicated onboarding for high-throughput teams needing <130ms failover.",
            "Direct Slack/Discord channel opened with DriftGuard systems engineers."
        ]
        audit_cta_metrics = [
            ("BOOK AUDIT", "DRIFTGUARD.LIVE/AUDIT"),
            ("RESPONSE", "SAME DAY"),
            ("STATUS", "ACCEPTING AUDITS")
        ]
        gev.draw_card(
            draw, left_x, gev.FOCAL_START_Y, card_w, card_h,
            title="Book Your Free Resilience Audit",
            subtitle="Private 48-Hour Diagnostic Assessment",
            bullets=audit_cta_bullets,
            fonts=fonts,
            border_color=gev.ARBITRUM_BLUE,
            tag="ACTION: BOOK AUDIT",
            tag_color=gev.ARBITRUM_BLUE,
            wrap_width=58,
            metrics=audit_cta_metrics
        )

        # Right Anchor: Open Source Core & Live Gateway
        open_source_bullets = [
            "Public GitHub repository: github.com/maskalfreeup-glitch/driftguard",
            "Permissive MIT license: 100% free for solo developers and validators.",
            "Live multi-node reference testbed active at: rpc.driftguard.live",
            "Full source code for Sentinel daemon, HAProxy templates & chaos scripts.",
            "Deploy in 60 seconds with Docker Compose or Kubernetes Helm charts.",
            "Community Discord and governance updates actively maintained."
        ]
        open_source_metrics = [
            ("REPOSITORY", "GITHUB (MIT)"),
            ("TESTBED", "RPC.DRIFTGUARD.LIVE"),
            ("STATUS", "OPERATIONAL")
        ]
        gev.draw_card(
            draw, right_x, gev.FOCAL_START_Y, card_w, card_h,
            title="Open Source Core & Live Testbed",
            subtitle="100% Reusable Public Good Architecture",
            bullets=open_source_bullets,
            fonts=fonts,
            border_color=gev.EMERALD,
            tag="OPEN SOURCE (MIT)",
            tag_color=gev.EMERALD,
            wrap_width=58,
            metrics=open_source_metrics
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="DriftGuard Client Acquisition Video Generator")
    parser.add_argument("--output", "-o", default="/home/masky/Desktop/DriftGuard_Client_Acquisition_Video/DriftGuard_Client_Acquisition_Episode1_1080p.mp4")
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--width", type=int, default=1920)
    parser.add_argument("--height", type=int, default=1080)
    parser.add_argument("--voice", default="ryan")
    args = parser.parse_args()

    # Patch SCENE_CUES in base module
    gev.SCENE_CUES = ACQUISITION_CUES

    # Instantiate custom core scenes
    custom_core_scenes = [
        gev.SceneIntro(fps=args.fps),
        gev.SceneProblem(fps=args.fps),
        gev.SceneArchitecture(fps=args.fps),
        gev.SceneQuickStart(fps=args.fps),
        gev.SceneLiveDrill(fps=args.fps),
        SceneClientAcquisitionSummary(fps=args.fps),
        SceneClientAcquisitionOutro(fps=args.fps),
    ]

    # Ensure output dir exists
    out_path = Path(args.output).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    print("=" * 72)
    print("  DriftGuard — Client Acquisition Positioning Video Generator")
    print(f"  Target Output: {out_path}")
    print(f"  Resolution:    {args.width}x{args.height} @ {args.fps}fps")
    print("  Positioning:   Systems Engineering Education + B2B Retainer CTA")
    print("=" * 72)

    # Monkey-patch core scenes in render pipeline
    original_render_video = gev.render_video

    def custom_render_video(*r_args, **r_kwargs):
        # We replace the core_scenes inside render_video
        gev.purge_caches()
        fonts = gev.FontManager()
        project_root = Path(__file__).resolve().parent.parent
        shield = gev.load_shield_asset(project_root, size=160)
        glow = gev.create_radial_glow(size=256, color=gev.ARBITRUM_BLUE)

        intro_bumper = gev.SceneIntroLogo(fps=args.fps)
        outro_bumper = gev.SceneOutroLogo(fps=args.fps)

        # Attach cues to scenes
        for sc in custom_core_scenes:
            if sc.scene_id in ACQUISITION_CUES:
                sc.cues = ACQUISITION_CUES[sc.scene_id]

        piper_bin, piper_model = gev.resolve_piper(voice_name=args.voice)
        voice_clips: Dict[int, str] = {}
        temp_dir = tempfile.mkdtemp(prefix="driftguard_acq_video_")

        scenes = [intro_bumper] + custom_core_scenes + [outro_bumper]

        if piper_bin and piper_model:
            print("[*] Local Piper TTS active:")
            print(f"    Binary: {piper_bin}")
            print(f"    Model : {piper_model}")
            print("[*] Generating speech narration clips with subtitle cues...")

            for sc in scenes:
                if not sc.cues:
                    continue
                cue_wavs = []
                accum_time = 0.5
                for idx, cue in enumerate(sc.cues):
                    cue_wav = os.path.join(temp_dir, f"acq_cue_{sc.scene_id}_{idx}.wav")
                    gev.synthesize_speech_clip(piper_bin, piper_model, cue.tts_text, cue_wav)

                    dur = 0.0
                    if os.path.isfile(cue_wav):
                        with wave.open(cue_wav, "rb") as w:
                            dur = w.getnframes() / float(w.getframerate())

                    cue.start_time = accum_time
                    cue.end_time = accum_time + dur
                    cue_wavs.append((cue, cue_wav, dur))
                    accum_time = cue.end_time + cue.pause_after

                sc.set_duration(accum_time + 0.6)

                scene_wav = os.path.join(temp_dir, f"acq_scene_{sc.scene_id}.wav")
                gev.build_scene_wav(scene_wav, sc.duration_sec, cue_wavs)
                voice_clips[sc.scene_id] = scene_wav
                speech_dur = sum(d for _, _, d in cue_wavs)
                print(f"    ✔ Scene {sc.scene_id} ({sc.name}): {len(sc.cues)} cues, {speech_dur:.2f}s speech -> {sc.duration_sec:.2f}s scene")

        total_frames = sum(sc.total_frames for sc in scenes)
        total_duration = sum(sc.duration_sec for sc in scenes)
        print(f"[*] Total video duration: {total_duration:.1f}s ({total_frames} frames)")

        # Audio synthesis
        print("[*] Synthesizing audio score (hum-free, studio narration)...")
        master_wav = os.path.join(temp_dir, "master_soundtrack.wav")
        gev.build_composite_audio(master_wav, total_duration, scenes, voice_clips, args.fps)
        print(f"✔ Master soundtrack synthesized: {os.path.getsize(master_wav)/1024:.1f} KB")

        # Encode via FFmpeg
        print(f"[*] Launching FFmpeg encoder -> {out_path}")
        ffmpeg_cmd = [
            "ffmpeg", "-y",
            "-f", "rawvideo",
            "-vcodec", "rawvideo",
            "-s", f"{args.width}x{args.height}",
            "-pix_fmt", "rgb24",
            "-r", str(args.fps),
            "-i", "-",
            "-i", master_wav,
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "18",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            str(out_path)
        ]

        p = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)

        rendered_frames = 0
        import time
        start_time = time.time()
        scene_start_frame = 0

        for sc_idx, sc in enumerate(scenes):
            is_bumper = isinstance(sc, (gev.SceneIntroLogo, gev.SceneOutroLogo))
            for local_f in range(sc.total_frames):
                img = Image.new("RGB", (args.width, args.height), gev.BG_COLOR)
                draw = ImageDraw.Draw(img)

                gev.draw_ambient_grid(draw, args.width, args.height)
                sc.render(local_f, img, draw, fonts, shield, glow, args.width, args.height)

                if not is_bumper:
                    active_sub = sc.get_active_subtitle(local_f)
                    if active_sub:
                        gev.draw_subtitle_pill(draw, fonts, active_sub, args.width, args.height)

                    core_idx = (sc_idx - 1) if (scenes[0] == intro_bumper) else sc_idx
                    gev.draw_global_ui(
                        img, draw, fonts, shield, custom_core_scenes, core_idx,
                        rendered_frames, total_frames, args.fps, args.width, args.height
                    )

                try:
                    p.stdin.write(img.tobytes())
                except BrokenPipeError:
                    break

                rendered_frames += 1

                if rendered_frames % 30 == 0 or rendered_frames == total_frames:
                    elapsed = time.time() - start_time
                    fps_val = rendered_frames / max(0.001, elapsed)
                    rem_sec = (total_frames - rendered_frames) / max(0.001, fps_val)
                    pct = int(rendered_frames / total_frames * 100)
                    prog_bar = ("=" * (pct // 4)).ljust(25)
                    print(f"\r  [{prog_bar}] {pct:3d}% | Frame {rendered_frames:04d}/{total_frames} | {fps_val:5.1f} fps | Scene: {sc.name:<17} | ETA: {rem_sec:4.1f}s", end="", flush=True)

            scene_start_frame += sc.total_frames

        p.stdin.close()
        p.wait()

        # Clean temp
        shutil.rmtree(temp_dir, ignore_errors=True)

        elapsed_total = time.time() - start_time
        print(f"\n\n✔ Video rendering complete in {elapsed_total:.1f}s ({rendered_frames/elapsed_total:.1f} avg fps)!")
        print(f"✔ Output file generated: {out_path} ({os.path.getsize(out_path)/(1024*1024):.2f} MB)")

    custom_render_video()

if __name__ == "__main__":
    main()
