#!/usr/bin/env python3
"""Rebuild Bré Thiar's two Hypnobius world runtime atlases from verified source ZIPs.

The licensed/free source archives stay outside the repository. This script verifies the exact
source archive and member hashes, rebuilds only production-derived world atlases from authentic
source pixels plus transparency, and optionally writes the two base64 runtime caches.

Default behavior is a dry run. Use --preview-dir to inspect derived PNGs outside the repo. Use
--write only after reviewing the preview/output hashes.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import io
import textwrap
import zipfile
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]

VILLAGE_ARCHIVE_SHA256 = "9283c11a67b13c7a2254e19551995d9743b8606d339890c0a268b6082fca7468"
SWAMP_ARCHIVE_SHA256 = "43cb4478dd3b4f80cf9f8e58f66bf68f4e08d37e2618f5d5ee3d9cae5dcf660e"

VILLAGE_MEMBERS = {
    "ground": (
        "MedievalVillageExteriorv1.0/RawAssets/Ground.png",
        "a18c83501af3d7b8cb1a9f424ffa7339e2d7c9d2aa2c6f23fc0db5d6baa90e63",
    ),
    "props": (
        "MedievalVillageExteriorv1.0/RawAssets/Props_Decor.png",
        "31400feaa6c72ad9c4a51fa3667d6319e7c23dd83a4ef7231a872cb2d3149457",
    ),
    "sconce": (
        "MedievalVillageExteriorv1.0/RawAssets/Sconce_Spritesheet.png",
        "7ecb7cd7b2d37dafdc413c8b1a188886ceb26093aa4efde005b16ddb82a2a164",
    ),
    "walls": (
        "MedievalVillageExteriorv1.0/RawAssets/Walls.png",
        "4b5f66ca4756e92d965d583fb92500c21c8fe5127dd27ace19a5d84cc8bf8866",
    ),
}
SWAMP_MEMBERS = {
    "altar0": (
        "Dark_Swamp_Starter_Pack_v1.0/RawAssets/Altar0.png",
        "a6a587d32e0c5d97f3a391d3d76b768a9850cbb973e6d8a36b60b5bb8b72905d",
    ),
    "ground": (
        "Dark_Swamp_Starter_Pack_v1.0/RawAssets/GroundTileset.png",
        "d0634919eee6f62b32c4314f7d7a6fd9d8b716c0a0f641d1beb639c51399f1e7",
    ),
    "props": (
        "Dark_Swamp_Starter_Pack_v1.0/RawAssets/PropsTileset.png",
        "5719de6b78d5b8cd9699d53c1ab073135efe3784ab318f12e67e86d95c5791b8",
    ),
}

EXPECTED_HOUSES_PNG_SHA256 = "f31ab8fb16d4511593af1023eb48e1a09b9b89b63feb095c173a31480a3a7130"
EXPECTED_PROPS_PNG_SHA256 = "8a931bc0d4a26b637e0836267689f43a8dad2f8fb021ab18fae7f8714a8bf8f9"

HOUSES_DEST = ROOT / "assets" / "runtime-v2" / "world_houses_atlas.b64"
PROPS_DEST = ROOT / "assets" / "runtime-v2" / "world_props_atlas.b64"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def verified_zip(path: Path, expected_sha: str, members: dict[str, tuple[str, str]]) -> dict[str, Image.Image]:
    raw = path.read_bytes()
    actual_archive = sha256(raw)
    if actual_archive != expected_sha:
        raise SystemExit(f"archive SHA-256 mismatch for {path}: expected {expected_sha}, got {actual_archive}")

    images: dict[str, Image.Image] = {}
    with zipfile.ZipFile(io.BytesIO(raw)) as zf:
        for key, (member, expected_member_sha) in members.items():
            try:
                member_raw = zf.read(member)
            except KeyError as exc:
                raise SystemExit(f"missing required source member in {path}: {member}") from exc
            actual_member = sha256(member_raw)
            if actual_member != expected_member_sha:
                raise SystemExit(
                    f"source member SHA-256 mismatch for {member}: expected {expected_member_sha}, got {actual_member}"
                )
            with Image.open(io.BytesIO(member_raw)) as im:
                images[key] = im.convert("RGBA")
    return images


def crop(im: Image.Image, x: int, y: int, w: int, h: int) -> Image.Image:
    return im.crop((x, y, x + w, y + h))


def build_house(kind: str, props: Image.Image, walls: Image.Image) -> Image.Image:
    canvas = Image.new("RGBA", (288, 336), (0, 0, 0, 0))
    x0 = 24

    if kind == "purple":
        top = crop(walls, 96, 0, 48, 48)
        bottom = crop(walls, 96, 48, 48, 48)
        roof = crop(props, 192, 0, 240, 240)
        door = crop(props, 48, 384, 48, 96)
    elif kind == "blue":
        top = crop(walls, 192, 0, 48, 48)
        bottom = crop(walls, 192, 48, 48, 48)
        roof = crop(props, 192, 240, 240, 240)
        door = crop(props, 96, 384, 48, 96)

        # The blue roof source has an open gable. Fill only that inner triangle with authentic
        # stone-wall source pixels behind the roof; transparency remains everywhere else.
        fill = Image.new("RGBA", (240, 240), (0, 0, 0, 0))
        for yy in range(96, 240, 48):
            for xx in range(0, 240, 48):
                fill.alpha_composite(top, (xx, yy))
        mask = Image.new("L", (240, 240), 0)
        ImageDraw.Draw(mask).polygon([(120, 116), (18, 239), (222, 239)], fill=255)
        fill.putalpha(Image.composite(fill.getchannel("A"), Image.new("L", (240, 240), 0), mask))
        canvas.alpha_composite(fill, (x0, 0))
    else:
        raise ValueError(f"unsupported house kind: {kind}")

    win_l = crop(props, 48, 288, 48, 96)
    win_r = crop(props, 144, 288, 48, 96)

    for col in range(5):
        canvas.alpha_composite(top, (x0 + 48 * col, 240))
        canvas.alpha_composite(bottom, (x0 + 48 * col, 288))

    canvas.alpha_composite(win_l, (x0 + 48, 240))
    canvas.alpha_composite(door, (x0 + 96, 240))
    canvas.alpha_composite(win_r, (x0 + 144, 240))
    canvas.alpha_composite(roof, (x0, 0))
    return canvas


def build_houses_atlas(village: dict[str, Image.Image]) -> Image.Image:
    blue = build_house("blue", village["props"], village["walls"])
    purple = build_house("purple", village["props"], village["walls"])
    atlas = Image.new("RGBA", (578, 336), (0, 0, 0, 0))
    atlas.alpha_composite(blue, (0, 0))
    atlas.alpha_composite(purple, (290, 0))
    return atlas


def build_props_atlas(village: dict[str, Image.Image], swamp: dict[str, Image.Image]) -> Image.Image:
    props = village["props"]
    atlas = Image.new("RGBA", (500, 294), (0, 0, 0, 0))

    # Normalize the 96x144 altar to the locked legacy 92x146 slot without resampling: crop two
    # transparent/outboard columns from each side, then add one transparent row above/below.
    altar92 = swamp["altar0"].crop((2, 0, 94, 144))
    atlas.alpha_composite(altar92, (0, 1))

    atlas.alpha_composite(crop(swamp["props"], 288, 0, 96, 96), (94, 0))       # bridge_h
    atlas.alpha_composite(crop(props, 48, 48, 144, 96), (192, 0))              # cart
    atlas.alpha_composite(crop(props, 48, 96, 96, 96), (338, 0))               # crate_stack
    atlas.alpha_composite(crop(props, 48, 192, 144, 96), (0, 148))             # fence/garden
    atlas.alpha_composite(crop(props, 144, 96, 48, 96), (146, 148))            # tree

    terrain_tiles = [
        crop(village["ground"], 0, 0, 48, 48),
        crop(village["ground"], 48, 0, 48, 48),
        crop(village["ground"], 192, 0, 48, 48),
        crop(swamp["ground"], 0, 0, 48, 48),
        crop(swamp["ground"], 48, 0, 48, 48),
    ]
    for i, tile in enumerate(terrain_tiles):
        atlas.alpha_composite(tile, (196 + i * 48, 148))

    atlas.alpha_composite(crop(props, 0, 0, 48, 48), (438, 148))               # barrel

    bench_src = props.crop((3, 166, 46, 191))  # isolated 43x25 wooden bench component
    bench_slot = Image.new("RGBA", (96, 48), (0, 0, 0, 0))
    bench_slot.alpha_composite(bench_src, ((96 - bench_src.width) // 2, 48 - bench_src.height))
    atlas.alpha_composite(bench_slot, (0, 246))

    atlas.alpha_composite(crop(props, 0, 432, 48, 48), (98, 246))              # flower_tub
    atlas.alpha_composite(crop(village["sconce"], 0, 0, 48, 48), (148, 246))  # lantern
    atlas.alpha_composite(crop(swamp["props"], 384, 48, 48, 48), (198, 246))  # reeds
    atlas.alpha_composite(crop(swamp["props"], 0, 48, 48, 48), (248, 246))    # rocks
    return atlas


def png_bytes(im: Image.Image) -> bytes:
    buf = io.BytesIO()
    im.save(buf, format="PNG")
    return buf.getvalue()


def wrapped_base64(data: bytes) -> str:
    encoded = base64.b64encode(data).decode("ascii")
    return "\n".join(textwrap.wrap(encoded, 120)) + "\n"


def verify_output(name: str, data: bytes, expected_sha: str, expected_size: tuple[int, int]) -> None:
    actual_sha = sha256(data)
    if actual_sha != expected_sha:
        raise SystemExit(f"{name} deterministic output drift: expected {expected_sha}, got {actual_sha}")
    with Image.open(io.BytesIO(data)) as im:
        if im.format != "PNG" or im.size != expected_size:
            raise SystemExit(f"{name} wrong output geometry/format: got {im.format} {im.size}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("village_zip", type=Path)
    parser.add_argument("swamp_zip", type=Path)
    parser.add_argument("--preview-dir", type=Path, help="write derived PNG previews outside the repo")
    parser.add_argument("--write", action="store_true", help="write the two derived base64 runtime caches")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    village = verified_zip(args.village_zip, VILLAGE_ARCHIVE_SHA256, VILLAGE_MEMBERS)
    swamp = verified_zip(args.swamp_zip, SWAMP_ARCHIVE_SHA256, SWAMP_MEMBERS)

    houses_png = png_bytes(build_houses_atlas(village))
    props_png = png_bytes(build_props_atlas(village, swamp))
    verify_output("world_houses_atlas", houses_png, EXPECTED_HOUSES_PNG_SHA256, (578, 336))
    verify_output("world_props_atlas", props_png, EXPECTED_PROPS_PNG_SHA256, (500, 294))

    if args.preview_dir:
        args.preview_dir.mkdir(parents=True, exist_ok=True)
        (args.preview_dir / "world_houses_atlas_rebuilt.png").write_bytes(houses_png)
        (args.preview_dir / "world_props_atlas_rebuilt.png").write_bytes(props_png)

    if args.write:
        HOUSES_DEST.write_text(wrapped_base64(houses_png))
        PROPS_DEST.write_text(wrapped_base64(props_png))

    print("BRÉ THIAR VERIFIED WORLD ATLAS REBUILD: PASS")
    print(f"- village source ZIP SHA-256: {VILLAGE_ARCHIVE_SHA256}")
    print(f"- swamp source ZIP SHA-256:   {SWAMP_ARCHIVE_SHA256}")
    print(f"- houses PNG: 578x336 sha256={EXPECTED_HOUSES_PNG_SHA256}")
    print(f"- props PNG:  500x294 sha256={EXPECTED_PROPS_PNG_SHA256}")
    print(f"- repository writes: {'two derived .b64 caches' if args.write else 'none (dry run)'}")
    if args.preview_dir:
        print(f"- preview directory: {args.preview_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
