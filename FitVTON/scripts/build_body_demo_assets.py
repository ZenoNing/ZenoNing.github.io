#!/usr/bin/env python3
"""Regenerate Explorer demo assets with consistent body shapes and poses.

Each Explorer slot uses one body and one pose; center bodies and bottom-orbit
try-ons are generated from the same body/pose pair.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
from PIL import Image

# One body per Explorer slot; matches the original 10-shape demo grid.
BODY_SOURCES = {
    0: "female4",
    1: "female1",
    2: "female3",
    3: "female2",
    4: "female0",
    5: "female6",
    6: "female9",
    7: "female5",
    8: "female7",
    9: "female8",
}

# Explorer slot i uses pose{i} (pose0 .. pose9).
POSE_SOURCES = {slot: f"pose{slot}" for slot in BODY_SOURCES}

# Must match top-orbit garment_0..4.webp (Ref units -> try-on unit/mode).
OUTFIT_SOURCES = [
    "dress1/one_piece",                 # garment_0
    "dress8/one_piece",                 # garment_1
    "upper3_circleskirt2/tucked_in",    # garment_2
    "dress5/one_piece",                 # garment_3
    "dress4/one_piece",                 # garment_4
]


def png_to_webp(
    png_path: Path,
    webp_path: Path,
    *,
    target_h: int = 480,
    white_thresh: int = 250,
    quality: int = 92,
) -> None:
    im = Image.open(png_path).convert("RGBA")
    arr = np.array(im)
    white = (
        (arr[:, :, 0] > white_thresh)
        & (arr[:, :, 1] > white_thresh)
        & (arr[:, :, 2] > white_thresh)
    )
    arr[white, 3] = 0
    im = Image.fromarray(arr)
    bbox = im.getbbox()
    if bbox:
        im = im.crop(bbox)
    new_w = max(1, round(im.width * (target_h / im.height)))
    im = im.resize((new_w, target_h), Image.Resampling.LANCZOS)
    webp_path.parent.mkdir(parents=True, exist_ok=True)
    im.save(webp_path, "WEBP", quality=quality, method=6)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--body-render-root",
        type=Path,
        default=Path(__file__).resolve().parents[3]
        / "GarmentCodeVTON_v3"
        / "Ref"
        / "body_render",
    )
    parser.add_argument(
        "--dataset-root",
        type=Path,
        default=Path(__file__).resolve().parents[3] / "GarmentCodeVTON_v3",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "assets" / "demo",
    )
    parser.add_argument("--skip-wear", action="store_true")
    parser.add_argument("--wear-only", action="store_true")
    args = parser.parse_args()

    if not args.wear_only:
        for slot, body_name in BODY_SOURCES.items():
            pose_id = POSE_SOURCES[slot]
            body_png = args.body_render_root / body_name / pose_id / "render_front.png"
            if not body_png.exists():
                raise SystemExit(f"Missing body render: {body_png}")
            body_out = args.output_dir / f"body_{slot}.webp"
            png_to_webp(body_png, body_out)
            print(f"body_{slot}.webp <- {body_name}/{pose_id}/render_front.png")

    if args.skip_wear:
        return

    for slot, body_name in BODY_SOURCES.items():
        pose_id = POSE_SOURCES[slot]
        for outfit_idx, outfit_path in enumerate(OUTFIT_SOURCES):
            wear_png = (
                args.dataset_root
                / "female"
                / body_name
                / outfit_path
                / pose_id
                / "render_front.png"
            )
            if not wear_png.exists():
                raise SystemExit(f"Missing try-on render: {wear_png}")
            wear_out = args.output_dir / f"wear_{slot}_{outfit_idx}.webp"
            png_to_webp(wear_png, wear_out)
            print(
                f"wear_{slot}_{outfit_idx}.webp <- "
                f"female/{body_name}/{outfit_path}/{pose_id}"
            )


if __name__ == "__main__":
    main()
