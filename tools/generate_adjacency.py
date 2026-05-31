"""
Generate province adjacency data from provinces.bmp.

Strategy:
- Colors in the BMP are reused (graph-coloring with 256 colors for 4913 provinces).
- Each contiguous same-color region is one province.
- We use scipy.ndimage.label to find connected components per color.
- We match each component to a province_id using center_lon/center_lat from
  provinces_metadata.json (equirectangular projection).
- Then we scan pixel neighbors to find which province-labeled regions touch.

Outputs: data/adjacency.json
"""

import json
import csv
import time
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

BASE_DIR = Path(__file__).resolve().parent.parent
MAP_OUTPUT = BASE_DIR / "map-output"
DATA_DIR = BASE_DIR / "data"

PROVINCES_BMP = MAP_OUTPUT / "provinces.bmp"
DEFINITION_CSV = MAP_OUTPUT / "definition.csv"
METADATA_JSON = MAP_OUTPUT / "provinces_metadata.json"
OUTPUT_JSON = DATA_DIR / "adjacency.json"

SKIP_COLORS_ENCODED = {0, 255 * 65536 + 255 * 256 + 255}  # black, white


def lonlat_to_pixel(lon: float, lat: float, img_w: int, img_h: int):
    """Convert lon/lat to pixel coordinates (equirectangular)."""
    x = int((lon + 180) / 360 * img_w)
    y = int((90 - lat) / 180 * img_h)
    x = max(0, min(img_w - 1, x))
    y = max(0, min(img_h - 1, y))
    return x, y


def main():
    print("=== Province Adjacency Generator ===")
    t0 = time.time()

    # --- Load metadata (center coordinates) ---
    print("Loading provinces_metadata.json...")
    with open(METADATA_JSON, "r", encoding="utf-8") as f:
        metadata = json.load(f)
    print(f"  {len(metadata)} provinces")

    # --- Load definition.csv (color per province) ---
    print("Loading definition.csv...")
    id_to_color_enc = {}
    with open(DEFINITION_CSV, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f, delimiter=";")
        for row in reader:
            pid = int(row["province_id"])
            r, g, b = int(row["r"]), int(row["g"]), int(row["b"])
            id_to_color_enc[pid] = r * 65536 + g * 256 + b

    # --- Load image ---
    print("Loading provinces.bmp...")
    img = Image.open(PROVINCES_BMP).convert("RGB")
    arr = np.array(img)
    img_h, img_w, _ = arr.shape
    print(f"  Image: {img_w} x {img_h}")

    # Encode pixel colors as single int
    encoded = (
        arr[:, :, 0].astype(np.int32) * 65536
        + arr[:, :, 1].astype(np.int32) * 256
        + arr[:, :, 2].astype(np.int32)
    )

    # --- Label connected components per color ---
    print("Labeling connected components (4-connectivity)...")
    structure = np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]])  # 4-conn
    # id_map: pixel -> province_id (0 = unassigned/skip)
    id_map = np.zeros((img_h, img_w), dtype=np.int32)

    # Group provinces by their encoded color
    color_to_pids: dict[int, list[int]] = {}
    for pid, cenc in id_to_color_enc.items():
        color_to_pids.setdefault(cenc, []).append(pid)

    # For each province, precompute its center pixel
    pid_to_center: dict[int, tuple[int, int]] = {}
    for prov in metadata:
        pid = prov["id"]
        cx, cy = lonlat_to_pixel(prov["center_lon"], prov["center_lat"], img_w, img_h)
        pid_to_center[pid] = (cx, cy)

    unique_colors = np.unique(encoded)
    unique_colors = unique_colors[~np.isin(unique_colors, list(SKIP_COLORS_ENCODED))]
    total_colors = len(unique_colors)
    assigned = 0
    unmatched = 0

    print(f"  Processing {total_colors} unique colors...")
    for ci, cenc in enumerate(unique_colors):
        if (ci + 1) % 25 == 0 or ci == 0:
            print(f"    Color {ci+1}/{total_colors}...")
        mask = encoded == int(cenc)
        labeled, num_components = ndimage.label(mask, structure=structure)

        # Which province IDs use this color?
        pids_for_color = color_to_pids.get(int(cenc), [])
        if not pids_for_color:
            continue

        # Match each province to the component containing its center
        for pid in pids_for_color:
            if pid not in pid_to_center:
                unmatched += 1
                continue
            cx, cy = pid_to_center[pid]
            comp_label = labeled[cy, cx]
            if comp_label > 0:
                id_map[labeled == comp_label] = pid
                assigned += 1
            else:
                # Center pixel not on this color; search nearby
                # (can happen if center is on a border pixel)
                found = False
                for radius in range(1, 10):
                    for dy in range(-radius, radius + 1):
                        for dx in range(-radius, radius + 1):
                            ny, nx = cy + dy, cx + dx
                            if 0 <= ny < img_h and 0 <= nx < img_w:
                                cl = labeled[ny, nx]
                                if cl > 0:
                                    id_map[labeled == cl] = pid
                                    assigned += 1
                                    found = True
                                    break
                        if found:
                            break
                    if found:
                        break
                if not found:
                    unmatched += 1

    print(f"  Assigned: {assigned}, Unmatched: {unmatched}")
    print(f"  Component labeling done in {time.time() - t0:.1f}s")

    # --- Find adjacencies ---
    print("Scanning for adjacencies...")
    t1 = time.time()

    # Horizontal neighbors
    h_left = id_map[:, :-1]
    h_right = id_map[:, 1:]
    h_mask = (h_left != h_right) & (h_left != 0) & (h_right != 0)
    h_pairs = np.column_stack((h_left[h_mask], h_right[h_mask]))

    # Vertical neighbors
    v_top = id_map[:-1, :]
    v_bot = id_map[1:, :]
    v_mask = (v_top != v_bot) & (v_top != 0) & (v_bot != 0)
    v_pairs = np.column_stack((v_top[v_mask], v_bot[v_mask]))

    all_pairs = np.vstack((h_pairs, v_pairs))
    print(f"  {len(all_pairs)} border pixel pairs found")

    # Build adjacency dict
    adjacency: dict[int, set[int]] = {}
    unique_pairs = set(map(tuple, all_pairs.tolist()))
    for a, b in unique_pairs:
        if a == b:
            continue
        adjacency.setdefault(a, set()).add(b)
        adjacency.setdefault(b, set()).add(a)

    print(f"  Adjacency computed in {time.time() - t1:.1f}s")
    print(f"  Provinces with neighbors: {len(adjacency)}")

    # --- Write output ---
    result = {str(k): sorted(v) for k, v in sorted(adjacency.items())}
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False)

    print(f"\nOutput: {OUTPUT_JSON}")
    print(f"Total provinces with adjacency: {len(result)}")
    neighbor_counts = [len(v) for v in result.values()]
    if neighbor_counts:
        print(f"Avg neighbors: {sum(neighbor_counts)/len(neighbor_counts):.1f}")
        print(f"Max: {max(neighbor_counts)}, Min: {min(neighbor_counts)}")
    print(f"Total time: {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()
