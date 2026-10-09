import { useState, useRef } from "react"
import { Download, ExternalLink } from "lucide-react"

export function ExplainerShowcase() {
  const [activeChapter, setActiveChapter] = useState(0)
  const videoRef = useRef<HTMLVideoElement>(null)

  const chapters = [
    { label: "00:00 Intro", time: 0 },
    { label: "00:23 Problem", time: 23 },
    { label: "00:43 Architecture", time: 43 },
    { label: "01:04 QuickStart", time: 64 },
    { label: "01:21 Failover Drill", time: 81 },
    { label: "01:53 Open Source", time: 113 },
  ]

  const seekToChapter = (seconds: number, index: number) => {
    setActiveChapter(index)
    if (videoRef.current) {
      videoRef.current.currentTime = seconds
      videoRef.current.play().catch(() => {})
    }
  }

  return (
    <div id="explainer-video" className="py-12 space-y-6">
      <div className="text-center space-y-2 max-w-2xl mx-auto">
        <h2 className="text-2xl sm:text-3xl font-bold tracking-tight text-white">
          Technical Walkthrough &amp; Failover Drill
        </h2>
        <p className="text-sm sm:text-base text-zinc-400 font-sans">
          Watch DriftGuard detect upstream consensus drift out-of-band and execute atomic UNIX socket failover in under 130 milliseconds.
        </p>
      </div>

      {/* Centered Full-Width Video Player Showcase */}
      <div className="max-w-4xl mx-auto rounded-xl border border-zinc-800 shadow-2xl overflow-hidden bg-black">
        <video
          ref={videoRef}
          controls
          preload="metadata"
          poster="/driftguard-explainer-poster.png"
          className="w-full aspect-video object-contain bg-black"
        >
          <source src="/driftguard-explainer.mp4" type="video/mp4" />
          Your browser does not support the video tag.
        </video>

        {/* Clean Chapter Scrub Bar Neatly Below the Video Player */}
        <div className="p-3 bg-zinc-950 border-t border-zinc-800/80 flex items-center justify-between gap-3 flex-wrap">
          <div className="flex items-center gap-1.5 overflow-x-auto no-scrollbar py-0.5">
            <span className="text-[11px] font-mono text-zinc-500 uppercase mr-1 hidden sm:inline">
              Chapters:
            </span>
            {chapters.map((ch, idx) => (
              <button
                key={idx}
                onClick={() => seekToChapter(ch.time, idx)}
                className={`px-2.5 py-1 rounded text-xs font-mono whitespace-nowrap transition-colors ${
                  activeChapter === idx
                    ? "bg-zinc-800 text-white font-medium border border-zinc-700"
                    : "text-zinc-400 hover:text-white hover:bg-zinc-900"
                }`}
              >
                {ch.label}
              </button>
            ))}
          </div>

          <div className="flex items-center gap-3 text-xs font-mono text-zinc-400 shrink-0">
            <a
              href="/driftguard-explainer.mp4"
              download="driftguard-explainer.mp4"
              className="hover:text-white transition-colors flex items-center gap-1"
            >
              <Download className="size-3.5" />
              <span>Download MP4</span>
            </a>
            <span>•</span>
            <a
              href="/driftguard-explainer.mp4"
              target="_blank"
              rel="noreferrer"
              className="hover:text-white transition-colors flex items-center gap-1"
            >
              <ExternalLink className="size-3.5" />
              <span>Fullscreen</span>
            </a>
          </div>
        </div>
      </div>
    </div>
  )
}
