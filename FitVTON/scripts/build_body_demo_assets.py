#!/usr/bin/env python3
"""Regenerate Explorer demo assets with consistent body shapes.

Center bodies (pose0) and bottom-orbit try-ons share the same body per slot.
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

# Fixed outfits shown in the top / bottom orbits (unit/mode under GarmentCodeVTON_v3).
OUTFIT_SOURCES = [
    "dress2/one_piece",
    "upper3_circleskirt2/tucked_in",
    "dress1/one_piece",
    "upper2_pencilskirt1/tucked_in",
    "upper3_circleskirt2/untucked",
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
    parser.add_argument("--pose-id", default="pose0")
    parser.add_argument("--skip-wear", action="store_true")
    args = parser.parse_args()

    for slot, body_name in BODY_SOURCES.items():
        body_png = args.body_render_root / body_name / args.pose_id / "render_front.png"
        if not body_png.exists():
            raise SystemExit(f"Missing body render: {body_png}")
        body_out = args.output_dir / f"body_{slot}.webp"
        png_to_webp(body_png, body_out)
        print(f"body_{slot}.webp <- {body_name}/{args.pose_id}/render_front.png")

    if args.skip_wear:
        return

    for slot, body_name in BODY_SOURCES.items():
        for outfit_idx, outfit_path in enumerate(OUTFIT_SOURCES):
            wear_png = (
                args.dataset_root
                / "female"
                / body_name
                / outfit_path
                / args.pose_id
                / "render_front.png"
            )
            if not wear_png.exists():
                raise SystemExit(f"Missing try-on render: {wear_png}")
            wear_out = args.output_dir / f"wear_{slot}_{outfit_idx}.webp"
            png_to_webp(wear_png, wear_out)
            print(f"wear_{slot}_{outfit_idx}.webp <- female/{body_name}/{outfit_path}/{args.pose_id}")


if __name__ == "__main__":
    main()
