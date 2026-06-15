#!/usr/bin/env python3
"""
ComfyUI Cloud Flyer Generator

Generates event flyer posters by:
1. Submitting a background image generation job to ComfyUI Cloud
2. Polling until the job completes
3. Downloading the generated background
4. Compositing an SVG flyer with event details overlaid on the background
"""

import argparse
import base64
import json
import math
import os
import random
import sys
import time
import urllib.parse
from pathlib import Path

import requests


# ─── Default Event Parameters ───────────────────────────────────────────────

DEFAULT_EVENT = {
    "event_title": "Neighborhood Clean-Up Day",
    "event_date": "Saturday, May 2, 2026",
    "event_time": "9:00 AM – 12:00 PM",
    "event_location_name": "Riverside Park Pavilion",
    "event_location_address": "123 Park Rd, San Antonio, TX 78205",
    "event_fees": "FREE",
    "event_org": "Friends of Riverside Park",
    "event_url": "",
    "style_concept": (
        "community outdoor event, park setting, sunny morning, "
        "volunteers with trash bags, warm friendly atmosphere"
    ),
    "color_accent": "#F59E0B",
}

COMFY_CLOUD_BASE = "https://cloud.comfy.org/api"
MAX_POLL_RETRIES = 15
INITIAL_WAIT_S = 3
RETRY_WAIT_S = 4


# ─── Step 1: Build the ComfyUI workflow ─────────────────────────────────────

def build_comfyui_workflow(event: dict) -> tuple[dict, str]:
    """Build the ComfyUI API workflow and return (workflow_dict, bg_prompt)."""

    bg_prompt = " ".join([
        f"A cinematic photograph: {event['style_concept']}.",
        "Shot on 35mm film, shallow depth of field, golden hour lighting.",
        "Smooth clean bokeh areas in the upper and lower portions of the frame.",
        "No text, no writing, no letters, no signs.",
        "Pure photography with no graphic design elements.",
        "Professional color grading, warm tones, inviting atmosphere.",
        "Tall portrait composition 9:16.",
    ])

    neg_prompt = " ".join([
        "text, writing, letters, words, numbers, watermark, logo, signs, symbols,",
        "UI, overlay, graphic design, borders, captions, labels,",
        "blurry, low quality, deformed, disfigured, noisy, grainy",
    ])

    workflow = {
        "9": {
            "inputs": {"filename_prefix": "flyer-bg", "images": ["57:8", 0]},
            "class_type": "SaveImage",
            "_meta": {"title": "Save Image"},
        },
        "57:30": {
            "inputs": {
                "clip_name": "qwen_3_4b.safetensors",
                "type": "lumina2",
                "device": "default",
            },
            "class_type": "CLIPLoader",
            "_meta": {"title": "Load CLIP"},
        },
        "57:29": {
            "inputs": {"vae_name": "ae.safetensors"},
            "class_type": "VAELoader",
            "_meta": {"title": "Load VAE"},
        },
        "57:34": {
            "inputs": {"text": neg_prompt, "clip": ["57:30", 0]},
            "class_type": "CLIPTextEncode",
            "_meta": {"title": "Negative Prompt"},
        },
        "57:8": {
            "inputs": {"samples": ["57:3", 0], "vae": ["57:29", 0]},
            "class_type": "VAEDecode",
            "_meta": {"title": "VAE Decode"},
        },
        "57:28": {
            "inputs": {
                "unet_name": "z_image_turbo_bf16.safetensors",
                "weight_dtype": "default",
            },
            "class_type": "UNETLoader",
            "_meta": {"title": "Load Diffusion Model"},
        },
        "57:27": {
            "inputs": {"text": bg_prompt, "clip": ["57:30", 0]},
            "class_type": "CLIPTextEncode",
            "_meta": {"title": "Positive Prompt"},
        },
        "57:13": {
            "inputs": {"width": 1080, "height": 1920, "batch_size": 1},
            "class_type": "EmptySD3LatentImage",
            "_meta": {"title": "EmptySD3LatentImage"},
        },
        "57:11": {
            "inputs": {"shift": 3, "model": ["57:28", 0]},
            "class_type": "ModelSamplingAuraFlow",
            "_meta": {"title": "ModelSamplingAuraFlow"},
        },
        "57:3": {
            "inputs": {
                "seed": random.randint(0, 2147483647),
                "steps": 8,
                "cfg": 1,
                "sampler_name": "res_multistep",
                "scheduler": "simple",
                "denoise": 1,
                "model": ["57:11", 0],
                "positive": ["57:27", 0],
                "negative": ["57:34", 0],
                "latent_image": ["57:13", 0],
            },
            "class_type": "KSampler",
            "_meta": {"title": "KSampler"},
        },
    }

    return workflow, bg_prompt


# ─── Step 2: Submit job to ComfyUI Cloud ────────────────────────────────────

def submit_job(workflow: dict, api_key: str) -> str:
    """Submit the workflow to ComfyUI Cloud and return the prompt_id."""
    print("[1/5] Submitting background generation job to ComfyUI Cloud...")

    resp = requests.post(
        f"{COMFY_CLOUD_BASE}/prompt",
        headers={
            "Content-Type": "application/json",
            "X-API-Key": api_key,
        },
        json={"prompt": workflow},
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    prompt_id = data["prompt_id"]
    print(f"       Job submitted: {prompt_id}")
    return prompt_id


# ─── Step 3: Poll for completion ────────────────────────────────────────────

def poll_until_done(prompt_id: str, api_key: str) -> None:
    """Poll the job status until success, failure, or timeout."""
    print(f"[2/5] Waiting {INITIAL_WAIT_S}s before first poll...")
    time.sleep(INITIAL_WAIT_S)

    headers = {"X-API-Key": api_key}
    start = time.time()

    for attempt in range(1, MAX_POLL_RETRIES + 1):
        elapsed = round(time.time() - start)
        resp = requests.get(
            f"{COMFY_CLOUD_BASE}/job/{prompt_id}/status",
            headers=headers,
            timeout=15,
        )
        resp.raise_for_status()
        status = resp.json().get("status", "unknown")
        print(f"       Poll {attempt}/{MAX_POLL_RETRIES}: status={status} ({elapsed}s elapsed)")

        if status == "success":
            return

        if status in ("failed", "cancelled"):
            raise RuntimeError(f"ComfyCloud job {status}: {resp.text}")

        if attempt < MAX_POLL_RETRIES:
            time.sleep(RETRY_WAIT_S)

    elapsed = round(time.time() - start)
    raise TimeoutError(
        f"ComfyCloud job timed out after {MAX_POLL_RETRIES} polls ({elapsed}s elapsed). "
        f"Last status: {status}"
    )


# ─── Step 4: Download the generated background ─────────────────────────────

def download_background(prompt_id: str, api_key: str) -> bytes:
    """Fetch job history, extract image URL, and download the background."""
    print("[3/5] Fetching job history...")
    headers = {"X-API-Key": api_key}

    resp = requests.get(
        f"{COMFY_CLOUD_BASE}/history_v2/{prompt_id}",
        headers=headers,
        timeout=15,
    )
    resp.raise_for_status()
    history = resp.json()

    # Extract image info from history
    images = []
    for job_id, job_data in history.items():
        outputs = job_data.get("outputs", {})
        for node_id, node_output in outputs.items():
            if node_output and "images" in node_output:
                for img in node_output["images"]:
                    images.append({
                        "filename": img["filename"],
                        "subfolder": img.get("subfolder", ""),
                        "download_url": (
                            f"{COMFY_CLOUD_BASE}/view"
                            f"?filename={urllib.parse.quote(img['filename'])}"
                            f"&subfolder={urllib.parse.quote(img.get('subfolder', ''))}"
                            f"&type=output"
                        ),
                    })

    if not images:
        raise RuntimeError(f"No images found in job history: {json.dumps(history)[:500]}")

    print(f"       Found {len(images)} image(s). Downloading first...")

    # Download the first image
    img_info = images[0]
    print(f"[4/5] Downloading background: {img_info['filename']}")
    resp = requests.get(
        img_info["download_url"],
        headers=headers,
        timeout=60,
        allow_redirects=True,
    )
    resp.raise_for_status()
    print(f"       Downloaded {len(resp.content)} bytes")
    return resp.content


# ─── Step 5: Compose the SVG poster ────────────────────────────────────────

def wrap_text(text: str, max_chars: int) -> list[str]:
    """Word-wrap text into lines of at most max_chars."""
    words = text.split()
    if len(words) <= 2:
        return [text]

    lines = []
    current = ""
    for word in words:
        if len(current) + len(word) + 1 > max_chars and current:
            lines.append(current)
            current = word
        else:
            current = f"{current} {word}" if current else word
    if current:
        lines.append(current)

    # Rebalance: merge short last line into previous
    if len(lines) > 1:
        last = lines[-1]
        prev = lines[-2]
        if len(last) < len(prev) * 0.4:
            lines.pop()
            lines[-1] = f"{prev} {last}"

    return lines


def compose_poster_svg(event: dict, bg_image_data: bytes | None) -> tuple[str, str]:
    """Build the final SVG flyer and return (svg_string, filename)."""
    print("[5/5] Composing poster SVG...")

    accent = event.get("color_accent", "#F59E0B")
    title = (event.get("event_title", "EVENT")).upper()
    date = event.get("event_date", "")
    time_str = event.get("event_time", "")
    venue_name = event.get("event_location_name", "")
    venue_addr = event.get("event_location_address", "")
    fees = event.get("event_fees", "")
    org = event.get("event_org", "")
    url = event.get("event_url", "")

    # Smart title sizing
    title_len = len(title)
    if title_len <= 14:
        font_size, max_chars = 82, 14
    elif title_len <= 20:
        font_size, max_chars = 72, 20
    elif title_len <= 30:
        font_size, max_chars = 62, 18
    else:
        font_size, max_chars = 52, 22

    title_lines = wrap_text(title, max_chars)
    line_height = font_size * 1.25
    title_start_y = 180

    title_svg = "\n  ".join(
        f'<text x="540" y="{title_start_y + i * line_height}" text-anchor="middle" '
        f'font-family="\'Arial Black\', \'Helvetica Neue\', Arial, sans-serif" '
        f'font-size="{font_size}" font-weight="900" fill="white" letter-spacing="2" '
        f'paint-order="stroke" stroke="rgba(0,0,0,0.4)" stroke-width="3">{line}</text>'
        for i, line in enumerate(title_lines)
    )

    title_block_bottom = title_start_y + (len(title_lines) - 1) * line_height + 30
    details_base_y = max(1280, title_block_bottom + 400)

    # Background image embed
    bg_image_href = ""
    if bg_image_data:
        bg_b64 = base64.b64encode(bg_image_data).decode("ascii")
        bg_image_href = f"data:image/png;base64,{bg_b64}"

    bg_image_tag = (
        f'<image href="{bg_image_href}" width="1080" height="1920" '
        f'preserveAspectRatio="xMidYMid slice"/>'
        if bg_image_href else ""
    )

    # Fee badge
    fee_badge = ""
    if fees:
        badge_w = min(max(len(fees) * 22 + 60, 140), 500)
        fee_badge = (
            f'<rect x="{540 - badge_w // 2}" y="{details_base_y - 80}" '
            f'width="{badge_w}" height="56" rx="28" fill="{accent}"/>\n'
            f'  <text x="540" y="{details_base_y - 44}" text-anchor="middle" '
            f'font-family="Arial, Helvetica, sans-serif" font-size="30" '
            f'font-weight="bold" fill="#1a1a1a">{fees}</text>'
        )

    # URL line
    url_line = ""
    if url:
        url_line = (
            f'<text x="540" y="{details_base_y + 260}" text-anchor="middle" '
            f'font-family="Arial, Helvetica, sans-serif" font-size="22" '
            f'fill="white" opacity="0.7">{url}</text>'
        )

    top_fade_height = max(500, title_block_bottom + 120)
    bottom_fade_y = details_base_y - 200
    bottom_fade_height = 1920 - bottom_fade_y

    svg = f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"
     width="1080" height="1920" viewBox="0 0 1080 1920">
  <defs>
    <linearGradient id="topFade" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#000" stop-opacity="0.7"/>
      <stop offset="100%" stop-color="#000" stop-opacity="0"/>
    </linearGradient>
    <linearGradient id="bottomFade" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#000" stop-opacity="0"/>
      <stop offset="100%" stop-color="#000" stop-opacity="0.85"/>
    </linearGradient>
    <linearGradient id="fallbackBg" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#1B3A57"/>
      <stop offset="50%" stop-color="#0f2640"/>
      <stop offset="100%" stop-color="#0a1628"/>
    </linearGradient>
  </defs>

  <rect width="1080" height="1920" fill="url(#fallbackBg)"/>
  {bg_image_tag}

  <rect x="0" y="0" width="1080" height="{top_fade_height}" fill="url(#topFade)"/>
  <rect x="0" y="{bottom_fade_y}" width="1080" height="{bottom_fade_height}" fill="url(#bottomFade)"/>

  <rect x="440" y="{title_block_bottom + 15}" width="200" height="4" rx="2" fill="{accent}" opacity="0.9"/>

  {title_svg}
  {fee_badge}

  <text x="540" y="{details_base_y}" text-anchor="middle" font-family="'Arial Black', Arial, sans-serif" font-size="40" font-weight="bold" fill="white" letter-spacing="1">{date}</text>
  <text x="540" y="{details_base_y + 55}" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="34" fill="white" opacity="0.9">{time_str}</text>
  <rect x="470" y="{details_base_y + 82}" width="140" height="2" rx="1" fill="white" opacity="0.3"/>
  <text x="540" y="{details_base_y + 130}" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="30" font-weight="bold" fill="white" opacity="0.95">{venue_name}</text>
  <text x="540" y="{details_base_y + 172}" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="24" fill="white" opacity="0.7">{venue_addr}</text>
  {url_line}

  <text x="540" y="1840" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="20" fill="white" opacity="0.45">Presented by {org}</text>
  <rect x="0" y="1908" width="1080" height="12" fill="{accent}" opacity="0.8"/>
</svg>"""

    safe_name = event.get("event_title", "event").lower()
    safe_name = "".join(c if c.isalnum() else "_" for c in safe_name).strip("_")
    filename = f"flyer_{safe_name}.svg"

    return svg, filename


# ─── Main ───────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Generate an event flyer using ComfyUI Cloud for background generation"
    )
    parser.add_argument(
        "--api-key",
        default=os.environ.get("COMFYUI_API_KEY", ""),
        help="ComfyUI Cloud API key (or set COMFYUI_API_KEY env var)",
    )
    parser.add_argument(
        "--event-json",
        type=Path,
        help="Path to JSON file with event parameters (overrides defaults)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("."),
        help="Directory to save the output SVG (default: current dir)",
    )
    parser.add_argument(
        "--skip-bg",
        action="store_true",
        help="Skip background generation (use gradient fallback)",
    )
    args = parser.parse_args()

    # Load event parameters
    event = dict(DEFAULT_EVENT)
    if args.event_json:
        with open(args.event_json) as f:
            overrides = json.load(f)
        event.update(overrides)
        print(f"Loaded event parameters from {args.event_json}")

    api_key = args.api_key
    if not api_key and not args.skip_bg:
        print("Error: --api-key or COMFYUI_API_KEY required (or use --skip-bg)", file=sys.stderr)
        sys.exit(1)

    print(f"Event: {event['event_title']}")
    print(f"Date:  {event['event_date']} @ {event['event_time']}")
    print()

    bg_data = None

    if not args.skip_bg:
        # Step 1: Build workflow
        workflow, bg_prompt = build_comfyui_workflow(event)
        print(f"Background prompt: {bg_prompt[:80]}...")
        print()

        # Step 2: Submit to ComfyUI Cloud
        prompt_id = submit_job(workflow, api_key)

        # Step 3: Poll until done
        poll_until_done(prompt_id, api_key)

        # Step 4: Download background
        bg_data = download_background(prompt_id, api_key)
    else:
        print("[SKIP] Background generation skipped — using gradient fallback")
        print()

    # Step 5: Compose SVG
    svg_content, filename = compose_poster_svg(event, bg_data)

    # Save output
    output_path = args.output_dir / filename
    args.output_dir.mkdir(parents=True, exist_ok=True)
    output_path.write_text(svg_content, encoding="utf-8")

    print()
    print(f"Flyer saved to: {output_path}")
    print(f"Background embedded: {bg_data is not None}")
    print(f"File size: {output_path.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
