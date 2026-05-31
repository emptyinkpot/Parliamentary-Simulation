#!/usr/bin/env python3
"""
合并历史时期数据 - 优化版
使用 buffer 扩展-收缩法填充间隙，针对大批量数据优化
"""

import json
from pathlib import Path
from shapely.geometry import shape, mapping, MultiPolygon
from shapely.ops import unary_union
from shapely.validation import make_valid
from shapely import buffer
import os

# 路径配置
GEO_DIR = Path("/workspace/projects/public/geo")
HISTORY_DIR = Path("/workspace/projects/public/history-detailed")
OUTPUT_DIR = Path("/workspace/projects/public/history-detailed-merged")

# 间隙填充参数
BUFFER_DIST = 0.005      # 扩展距离
SIMPLIFY_TOL = 0.005     # 简化容差
MIN_AREA = 0.0001        # 最小面积阈值
BATCH_SIZE = 100         # 批次大小


def load_geojson(path: Path) -> dict:
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_geojson(data: dict, path: Path):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False)


def robust_fix(geom):
    """修复无效几何"""
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
    """过滤极小的多边形碎片"""
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


def merge_geometries_efficient(geometries, use_gap_fill=True):
    """
    高效合并几何体
    - 小批量: 使用 buffer 扩展-收缩法
    - 大批量: 分批合并后组装
    """
    if not geometries:
        return None
    
    n = len(geometries)
    
    if n <= BATCH_SIZE and use_gap_fill:
        # 小批量：直接使用 buffer 扩展-收缩
        try:
            buffered = [g.buffer(BUFFER_DIST) for g in geometries]
            merged = unary_union(buffered)
            merged = merged.buffer(-BUFFER_DIST)
            return merged
        except Exception as e:
            print(f"        合并失败: {e}")
            return None
    
    # 大批量：分批处理
    merged = None
    for i in range(0, n, BATCH_SIZE):
        batch = geometries[i:i + BATCH_SIZE]
        
        try:
            if use_gap_fill:
                # 扩展
                buffered = [g.buffer(BUFFER_DIST) for g in batch]
                # 合并批次
                batch_merged = unary_union(buffered)
                # 收缩
                batch_merged = batch_merged.buffer(-BUFFER_DIST)
            else:
                batch_merged = unary_union(batch)
            
            # 合并到总结果
            if merged is None:
                merged = batch_merged
            else:
                # 合并两个结果时也需要填充间隙
                if use_gap_fill:
                    merged = unary_union([
                        merged.buffer(BUFFER_DIST),
                        batch_merged.buffer(BUFFER_DIST)
                    ])
                    merged = merged.buffer(-BUFFER_DIST)
                else:
                    merged = unary_union([merged, batch_merged])
                    
        except Exception as e:
            print(f"        批次 {i//BATCH_SIZE} 失败: {e}")
            continue
    
    return merged


def process_period(year: int, regions_data: dict) -> bool:
    """处理单个时期"""
    print(f"\n处理 {year} 年...")
    
    period_data = load_geojson(HISTORY_DIR / f"period_{year}.json")
    
    factions = period_data['factions']
    city_to_faction = period_data['cityToFaction']
    features = regions_data['features']
    
    # 按势力分组
    faction_regions = {}
    for feature in features:
        adcode = str(feature['properties']['adcode'])
        faction_id = city_to_faction.get(adcode, 'faction-99')
        if faction_id not in faction_regions:
            faction_regions[faction_id] = []
        faction_regions[faction_id].append(feature)
    
    merged_features = []
    
    for faction_id, region_features in faction_regions.items():
        faction_info = factions.get(faction_id, {
            'name': '未知',
            'color': '#94a3b8',
            'outlineColor': '#64748b'
        })
        
        n_regions = len(region_features)
        print(f"  {faction_info['name']} ({n_regions})...", end=" ", flush=True)
        
        # 提取几何体
        geometries = []
        for feature in region_features:
            try:
                geom = shape(feature['geometry'])
                if not geom.is_valid:
                    geom = robust_fix(geom)
                if geom and not geom.is_empty:
                    geometries.append(geom)
            except:
                continue
        
        if not geometries:
            print("跳过")
            continue
        
        # 判断是否使用间隙填充（超大数量时不使用，避免超时）
        use_gap_fill = n_regions < 3000
        
        # 合并
        merged = merge_geometries_efficient(geometries, use_gap_fill)
        
        # 过滤小碎片
        merged = filter_small_polygons(merged, MIN_AREA)
        merged = robust_fix(merged)
        
        if merged is None or merged.is_empty:
            print("失败")
            continue
        
        # 简化
        merged = merged.simplify(SIMPLIFY_TOL, preserve_topology=True)
        merged = robust_fix(merged)
        
        if merged is None or merged.is_empty:
            print("失败")
            continue
        
        # 确保是 MultiPolygon
        if merged.geom_type == 'Polygon':
            merged = MultiPolygon([merged])
        
        if merged.geom_type != 'MultiPolygon':
            print("失败")
            continue
        
        merged_features.append({
            'type': 'Feature',
            'properties': {
                'factionId': faction_id,
                'name': faction_info['name'],
                'color': faction_info['color'],
                'outlineColor': faction_info['outlineColor'],
            },
            'geometry': mapping(merged),
        })
        
        print("完成")
    
    # 保存
    output_file = OUTPUT_DIR / f"period_{year}.json"
    save_geojson({'type': 'FeatureCollection', 'features': merged_features}, output_file)
    
    size = os.path.getsize(output_file) / 1024 / 1024
    print(f"  -> {len(merged_features)} 势力, {size:.1f}MB")
    
    return True


def main():
    print("=" * 60)
    print("合并历史时期数据 - 优化版（带间隙填充）")
    print(f"Buffer: {BUFFER_DIST}, Simplify: {SIMPLIFY_TOL}")
    print("=" * 60)
    
    regions_data = load_geojson(GEO_DIR / "world_regions_detailed.json")
    print(f"共 {len(regions_data['features'])} 个区域")
    
    index_data = load_geojson(HISTORY_DIR / "index.json")
    
    for period in index_data['periods']:
        process_period(period['year'], regions_data)
    
    save_geojson(index_data, OUTPUT_DIR / "index.json")
    print("\n" + "=" * 60)
    print("完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
