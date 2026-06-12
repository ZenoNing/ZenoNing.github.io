#!/usr/bin/env python3
"""Regenerate Explorer demo assets with consistent body shapes and poses.

Each Explorer slot maps to one GarmentCode body. Bodies and try-ons are exported
for a fixed pose set (default pose1, pose3, pose7) so the page can switch pose
independently from body shape.
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

DEFAULT_POSE_IDS = (1, 3, 7)

# Must match top-orbit garment_0..4.webp (visual asset -> try-on unit/mode).
OUTFIT_SOURCES = [
    "dress2/one_piece",                 # garment_0: blue sleeveless dress
    "dress6/one_piece",                 # garment_1: orange short-sleeve dress
    "upper1_pants1/untucked",           # garment_2: yellow top + beige shorts
    "upper2_pencilskirt1/tucked_in",    # garment_3: blue top + navy pencil skirt
    "upper3_circleskirt1/untucked",     # garment_4: pink top + light-blue circle skirt
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


def parse_pose_ids(raw: str) -> tuple[int, ...]:
    poses = tuple(int(part.strip()) for part in raw.split(",") if part.strip())
    if not poses:
        raise SystemExit("At least one pose id is required.")
    return poses


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
    parser.add_argument(
        "--poses",
        type=str,
        default=",".join(str(p) for p in DEFAULT_POSE_IDS),
        help="Comma-separated pose ids, e.g. 1,3,7 -> pose1/pose3/pose7",
    )
    parser.add_argument("--skip-wear", action="store_true")
    parser.add_argument("--wear-only", action="store_true")
    args = parser.parse_args()

    pose_ids = parse_pose_ids(args.poses)

    if not args.wear_only:
        for slot, body_name in BODY_SOURCES.items():
            for pose_id in pose_ids:
                pose_name = f"pose{pose_id}"
                body_png = args.body_render_root / body_name / pose_name / "render_front.png"
                if not body_png.exists():
                    raise SystemExit(f"Missing body render: {body_png}")
                body_out = args.output_dir / f"body_{slot}_p{pose_id}.webp"
                png_to_webp(body_png, body_out)
                print(f"body_{slot}_p{pose_id}.webp <- {body_name}/{pose_name}/render_front.png")

    if args.skip_wear:
        return

    for slot, body_name in BODY_SOURCES.items():
        for pose_id in pose_ids:
            pose_name = f"pose{pose_id}"
            for outfit_idx, outfit_path in enumerate(OUTFIT_SOURCES):
                wear_png = (
                    args.dataset_root
                    / "female"
                    / body_name
                    / outfit_path
                    / pose_name
                    / "render_front.png"
                )
                if not wear_png.exists():
                    raise SystemExit(f"Missing try-on render: {wear_png}")
                wear_out = args.output_dir / f"wear_{slot}_{outfit_idx}_p{pose_id}.webp"
                png_to_webp(wear_png, wear_out)
                print(
                    f"wear_{slot}_{outfit_idx}_p{pose_id}.webp <- "
                    f"female/{body_name}/{outfit_path}/{pose_name}"
                )


if __name__ == "__main__":
    main()
