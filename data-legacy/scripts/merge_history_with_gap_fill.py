#!/usr/bin/env python3
"""
合并历史时期数据 - 带间隙填充
使用 buffer 扩展-收缩法消除三角形碎片
"""

import json
from pathlib import Path
from shapely.geometry import shape, mapping, MultiPolygon
from shapely.ops import unary_union
from shapely.validation import make_valid
from shapely import buffer

# 路径配置
GEO_DIR = Path("/workspace/projects/public/geo")
HISTORY_DIR = Path("/workspace/projects/public/history-detailed")
OUTPUT_DIR = Path("/workspace/projects/public/history-detailed-merged")

# 间隙填充参数
BUFFER_DIST = 0.005  # 扩展距离（约500米），足够填充缝隙但不会过度模糊边界
SIMPLIFY_TOL = 0.005  # 简化容差
MIN_AREA = 0.0001     # 最小面积阈值


def load_geojson(path: Path) -> dict:
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_geojson(data: dict, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False)


def robust_fix(geom):
    """修复无效几何"""
    if geom.is_empty:
        return None
    if geom.is_valid:
        return geom
    
    # 方法1: buffer(0)
    fixed = buffer(geom, 0)
    if fixed.is_valid and not fixed.is_empty:
        return fixed
    
    # 方法2: make_valid
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


def merge_with_gap_fill(geometries, buffer_dist=BUFFER_DIST):
    """
    合并几何体，使用 buffer 扩展-收缩法填充间隙
    
    原理：
    1. 扩展每个多边形（buffer +dist），使相邻地块重叠
    2. 合并所有扩展后的多边形
    3. 收缩回来（buffer -dist），恢复原始边界
    """
    if not geometries:
        return None
    
    try:
        # 方法1：对小批量直接使用 buffer 扩展-收缩
        if len(geometries) <= 200:
            # 扩展
            buffered = [g.buffer(buffer_dist) for g in geometries]
            # 合并
            merged = unary_union(buffered)
            # 收缩
            merged = merged.buffer(-buffer_dist)
            return merged
        else:
            # 方法2：大批量分批处理，避免内存溢出
            batch_size = 150
            merged = None
            
            for i in range(0, len(geometries), batch_size):
                batch = geometries[i:i + batch_size]
                
                # 扩展
                buffered_batch = [g.buffer(buffer_dist) for g in batch]
                # 合并批次
                batch_merged = unary_union(buffered_batch)
                
                if merged is None:
                    merged = batch_merged
                else:
                    # 合并到总结果（需要再次扩展以填充间隙）
                    merged = unary_union([merged.buffer(buffer_dist), batch_merged.buffer(buffer_dist)])
                    merged = merged.buffer(-buffer_dist)
            
            return merged
            
    except Exception as e:
        print(f"      合并出错: {e}")
        return None


def process_period(year: int, regions_data: dict) -> dict:
    """处理单个时期"""
    print(f"\n处理 {year} 年...")
    
    # 读取时期数据
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
    
    # 合并每个势力
    merged_features = []
    
    for faction_id, region_features in faction_regions.items():
        faction_info = factions.get(faction_id, {
            'name': '未知',
            'color': '#94a3b8',
            'outlineColor': '#64748b'
        })
        
        print(f"  {faction_info['name']} ({len(region_features)} 区域)...")
        
        # 提取几何体
        geometries = []
        for feature in region_features:
            try:
                geom = shape(feature['geometry'])
                # 修复无效几何
                if not geom.is_valid:
                    geom = robust_fix(geom)
                if geom and not geom.is_empty:
                    geometries.append(geom)
            except Exception as e:
                continue
        
        if not geometries:
            continue
        
        # 使用 buffer 扩展-收缩法合并
        merged = merge_with_gap_fill(geometries, BUFFER_DIST)
        
        # 过滤小碎片
        merged = filter_small_polygons(merged, MIN_AREA)
        
        # 最终修复
        merged = robust_fix(merged)
        
        if merged is None or merged.is_empty:
            continue
        
        # 简化几何（可选，减少数据量）
        merged = merged.simplify(SIMPLIFY_TOL, preserve_topology=True)
        merged = robust_fix(merged)
        
        if merged is None or merged.is_empty:
            continue
        
        # 确保是 MultiPolygon
        if merged.geom_type == 'Polygon':
            merged = MultiPolygon([merged])
        
        if merged.geom_type != 'MultiPolygon':
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
    
    # 保存
    output_file = OUTPUT_DIR / f"period_{year}.json"
    save_geojson({'type': 'FeatureCollection', 'features': merged_features}, output_file)
    
    import os
    size = os.path.getsize(output_file) / 1024 / 1024
    print(f"  结果: {len(merged_features)} 势力, {size:.1f}MB")
    
    return {
        'year': year,
        'name': period_data['name'],
        'featuresCount': len(merged_features),
    }


def main():
    print("=" * 60)
    print("合并历史时期数据 - 带间隙填充")
    print(f"Buffer 距离: {BUFFER_DIST} 度")
    print(f"简化容差: {SIMPLIFY_TOL} 度")
    print("=" * 60)
    
    # 加载地理数据
    print("\n加载地理数据...")
    regions_data = load_geojson(GEO_DIR / "world_regions_detailed.json")
    print(f"共 {len(regions_data['features'])} 个区域")
    
    # 获取所有时期
    index_data = load_geojson(HISTORY_DIR / "index.json")
    periods = index_data['periods']
    
    # 处理每个时期
    for period in periods:
        process_period(period['year'], regions_data)
    
    # 保存索引
    save_geojson(index_data, OUTPUT_DIR / "index.json")
    
    print("\n" + "=" * 60)
    print("完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
