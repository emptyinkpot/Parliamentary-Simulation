"""
GeoJSON → P社格式省份位图转换工具

将 GeoJSON 多边形数据光栅化为：
1. provinces.bmp — 每个省份一个唯一 RGB 颜色
2. definition.csv — 省份ID;R;G;B;名称
3. provinces_metadata.json — 省份元数据（面积、中心点等）

依赖：pip install pillow shapely numpy
"""

import json
import csv
import sys
import os
from pathlib import Path

try:
    from PIL import Image, ImageDraw
    import numpy as np
    from shapely.geometry import shape, MultiPolygon, Polygon
    from shapely.ops import transform
except ImportError:
    print("缺少依赖，请运行：")
    print("  pip install pillow shapely numpy")
    sys.exit(1)


# 配置
MAP_WIDTH = 5632   # P社标准宽度（EU4 为 5632）
MAP_HEIGHT = 2048  # P社标准高度
LON_MIN = -180.0
LON_MAX = 180.0
LAT_MIN = -90.0
LAT_MAX = 90.0


def lon_to_x(lon: float) -> int:
    return int((lon - LON_MIN) / (LON_MAX - LON_MIN) * MAP_WIDTH)


def lat_to_y(lat: float) -> int:
    # 纬度翻转（北在上）
    return int((LAT_MAX - lat) / (LAT_MAX - LAT_MIN) * MAP_HEIGHT)


def id_to_color(province_id: int) -> tuple:
    """将省份 ID 转为唯一 RGB 颜色（避免纯黑和纯白）"""
    # 从 ID 1 开始，跳过 (0,0,0) 黑色
    r = (province_id * 7 + 13) % 256
    g = (province_id * 13 + 37) % 256
    b = (province_id * 23 + 71) % 256
    # 避免纯黑（海洋）和纯白
    if r == 0 and g == 0 and b == 0:
        r = 1
    if r == 255 and g == 255 and b == 255:
        r = 254
    return (r, g, b)


def polygon_to_pixels(geom, draw, color):
    """将 Shapely 几何体绘制到 PIL Image"""
    if geom.is_empty:
        return

    if isinstance(geom, MultiPolygon):
        for poly in geom.geoms:
            polygon_to_pixels(poly, draw, color)
        return

    if not isinstance(geom, Polygon):
        return

    # 外环
    exterior_coords = []
    for lon, lat in geom.exterior.coords:
        x = lon_to_x(lon)
        y = lat_to_y(lat)
        exterior_coords.append((x, y))

    if len(exterior_coords) < 3:
        return

    draw.polygon(exterior_coords, fill=color)

    # 内环（孔洞）用黑色填充（海洋色）
    for interior in geom.interiors:
        hole_coords = []
        for lon, lat in interior.coords:
            x = lon_to_x(lon)
            y = lat_to_y(lat)
            hole_coords.append((x, y))
        if len(hole_coords) >= 3:
            draw.polygon(hole_coords, fill=(0, 0, 0))


def convert_geojson_to_provinces(
    geojson_path: str,
    output_dir: str,
    name_field: str = "name",
    adcode_field: str = "adcode",
):
    """
    主转换函数

    Args:
        geojson_path: GeoJSON 文件路径
        output_dir: 输出目录
        name_field: GeoJSON properties 中的名称字段
        adcode_field: GeoJSON properties 中的 ID 字段
    """
    os.makedirs(output_dir, exist_ok=True)

    print(f"读取 GeoJSON: {geojson_path}")
    with open(geojson_path, "r", encoding="utf-8") as f:
        geojson = json.load(f)

    features = geojson.get("features", [])
    print(f"共 {len(features)} 个区域")

    # 创建省份位图（黑色背景 = 海洋）
    img = Image.new("RGB", (MAP_WIDTH, MAP_HEIGHT), (0, 0, 0))
    draw = ImageDraw.Draw(img)

    # definition.csv 数据
    definitions = []
    metadata = []

    for idx, feature in enumerate(features):
        province_id = idx + 1
        props = feature.get("properties", {})
        name = props.get(name_field, f"Province_{province_id}")
        adcode = props.get(adcode_field, str(province_id))

        color = id_to_color(province_id)

        # 解析几何体
        geom = shape(feature["geometry"])

        # 绘制到位图
        polygon_to_pixels(geom, draw, color)

        # 记录定义
        definitions.append({
            "id": province_id,
            "r": color[0],
            "g": color[1],
            "b": color[2],
            "name": name,
            "adcode": adcode,
        })

        # 记录元数据
        centroid = geom.centroid
        metadata.append({
            "id": province_id,
            "name": name,
            "adcode": adcode,
            "center_lon": round(centroid.x, 4),
            "center_lat": round(centroid.y, 4),
            "area_approx": round(geom.area, 6),
        })

        if (idx + 1) % 50 == 0:
            print(f"  已处理 {idx + 1}/{len(features)} 个区域")

    # 保存 provinces.bmp
    bmp_path = os.path.join(output_dir, "provinces.bmp")
    img.save(bmp_path, "BMP")
    print(f"已保存: {bmp_path} ({MAP_WIDTH}x{MAP_HEIGHT})")

    # 保存 definition.csv
    csv_path = os.path.join(output_dir, "definition.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(["province_id", "r", "g", "b", "name", "adcode"])
        for d in definitions:
            writer.writerow([d["id"], d["r"], d["g"], d["b"], d["name"], d["adcode"]])
    print(f"已保存: {csv_path} ({len(definitions)} 条记录)")

    # 保存元数据 JSON
    meta_path = os.path.join(output_dir, "provinces_metadata.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    print(f"已保存: {meta_path}")

    # 保存 PNG 预览（BMP 太大，PNG 方便查看）
    png_path = os.path.join(output_dir, "provinces_preview.png")
    img.save(png_path, "PNG")
    print(f"已保存预览: {png_path}")

    print(f"\n转换完成！共 {len(definitions)} 个省份")
    print(f"输出目录: {output_dir}")


if __name__ == "__main__":
    # 默认路径
    script_dir = Path(__file__).parent
    project_root = script_dir.parent

    # 输入：世界地图 GeoJSON
    default_input = project_root / "data-legacy" / "geo" / "world_regions_detailed.json"
    # 输出：map 目录
    default_output = project_root / "map-output"

    geojson_path = sys.argv[1] if len(sys.argv) > 1 else str(default_input)
    output_dir = sys.argv[2] if len(sys.argv) > 2 else str(default_output)

    if not os.path.exists(geojson_path):
        print(f"错误：找不到输入文件 {geojson_path}")
        print(f"\n用法: python {sys.argv[0]} <geojson_path> [output_dir]")
        print(f"示例: python {sys.argv[0]} ../data-legacy/geo/world_regions_detailed.json ../map-output")
        sys.exit(1)

    convert_geojson_to_provinces(geojson_path, output_dir)
