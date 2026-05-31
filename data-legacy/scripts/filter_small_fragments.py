#!/usr/bin/env python3
"""
过滤小碎片 - 清理合并数据中的极小多边形
"""

import json
from pathlib import Path
from shapely.geometry import shape, mapping, MultiPolygon
from shapely.validation import make_valid
from shapely import buffer
import os

MERGED_DIR = Path("/workspace/projects/public/history-detailed-merged")

# 最小面积阈值（增大以过滤更多碎片）
MIN_AREA = 0.001  # 约 1km²


def load_geojson(path: Path) -> dict:
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_geojson(data: dict, path: Path):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False)


def robust_fix(geom):
    if geom.is_empty:
        return None
    if geom.is_valid:
        return geom
    
    fixed = buffer(geom, 0)
    if fixed.is_valid and not fixed.is_empty:
        return fixed
    
    fixed = make_valid(geom)
    if fixed.is_valid and not fixed.is_empty:
        return fixed
    
    return None


def filter_small_polygons(geom, min_area=MIN_AREA):
    """过滤面积小于阈值的多边形"""
    if geom is None or geom.is_empty:
        return None
    
    if geom.geom_type == 'Polygon':
        return geom if geom.area >= min_area else None
    elif geom.geom_type == 'MultiPolygon':
        polys = [p for p in geom.geoms if p.area >= min_area]
        if not polys:
            return None
        return MultiPolygon(polys) if len(polys) > 1 else polys[0]
    
    return geom


def process_file(year: int):
    print(f"\n处理 {year} 年...")
    
    data = load_geojson(MERGED_DIR / f"period_{year}.json")
    
    filtered_features = []
    total_before = 0
    total_after = 0
    removed = 0
    
    for f in data['features']:
        geom = shape(f['geometry'])
        name = f['properties']['name']
        
        # 统计过滤前的多边形数量
        if geom.geom_type == 'MultiPolygon':
            total_before += len(geom.geoms)
        else:
            total_before += 1
        
        # 过滤小碎片
        filtered_geom = filter_small_polygons(geom, MIN_AREA)
        
        if filtered_geom is None or filtered_geom.is_empty:
            print(f"  {name}: 完全过滤")
            removed += 1
            continue
        
        # 确保有效性
        filtered_geom = robust_fix(filtered_geom)
        if filtered_geom is None or filtered_geom.is_empty:
            print(f"  {name}: 过滤后无效")
            removed += 1
            continue
        
        # 统计过滤后的多边形数量
        if filtered_geom.geom_type == 'MultiPolygon':
            total_after += len(filtered_geom.geoms)
        else:
            total_after += 1
        
        filtered_features.append({
            'type': 'Feature',
            'properties': f['properties'],
            'geometry': mapping(filtered_geom),
        })
    
    # 保存
    output_file = MERGED_DIR / f"period_{year}.json"
    save_geojson({'type': 'FeatureCollection', 'features': filtered_features}, output_file)
    
    size = os.path.getsize(output_file) / 1024 / 1024
    print(f"  势力: {len(filtered_features)} (移除 {removed})")
    print(f"  多边形: {total_before} -> {total_after} (减少 {total_before - total_after})")
    print(f"  文件: {size:.1f}MB")


def main():
    print("=" * 60)
    print(f"过滤小碎片 (MIN_AREA = {MIN_AREA})")
    print("=" * 60)
    
    index_data = load_geojson(MERGED_DIR / "index.json")
    
    for period in index_data['periods']:
        process_file(period['year'])
    
    print("\n" + "=" * 60)
    print("完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
