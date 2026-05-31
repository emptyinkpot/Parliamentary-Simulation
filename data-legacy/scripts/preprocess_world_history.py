#!/usr/bin/env python3
"""
预处理世界历史数据：合并同势力地块边界
使用 Shapely 的 buffer 操作填充缝隙
"""

import json
import time
from pathlib import Path
from shapely.geometry import shape, mapping, MultiPolygon
from shapely.ops import unary_union
from shapely.validation import make_valid

GEO_DIR = Path("/workspace/projects/public/geo")
HISTORY_DIR = Path("/workspace/projects/public/history-world")
OUTPUT_DIR = Path("/workspace/projects/public/history-world-merged")

def load_geojson(path: Path) -> dict:
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_geojson(data: dict, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False)

def merge_faction_geometries(regions_data: dict, period_data: dict) -> dict:
    """合并同势力地块边界"""
    features = regions_data['features']
    city_to_faction = period_data['cityToFaction']
    factions = period_data['factions']
    
    # 按势力分组
    faction_regions = {}
    for feature in features:
        adcode = feature['properties']['adcode']
        faction_id = city_to_faction.get(adcode, 'faction-13')
        
        if faction_id not in faction_regions:
            faction_regions[faction_id] = []
        faction_regions[faction_id].append(feature)
    
    merged_features = []
    
    for faction_id, region_features in faction_regions.items():
        faction_info = factions.get(faction_id, {'name': '未知', 'color': '#94a3b8', 'outlineColor': '#64748b'})
        
        print(f"  合并 {faction_info['name']} ({len(region_features)} 个地块)...")
        
        # 收集几何体
        geometries = []
        for feature in region_features:
            try:
                geom = shape(feature['geometry'])
                if geom.is_valid:
                    # 使用小缓冲区填充缝隙
                    buffered = geom.buffer(0.01)
                    geometries.append(buffered)
                else:
                    valid_geom = make_valid(geom)
                    if valid_geom:
                        buffered = valid_geom.buffer(0.01)
                        geometries.append(buffered)
            except Exception as e:
                print(f"    警告: 跳过无效几何 {feature['properties'].get('name', 'unknown')}: {e}")
                continue
        
        if not geometries:
            continue
        
        # 合并几何体
        start_time = time.time()
        try:
            merged = unary_union(geometries)
            elapsed = time.time() - start_time
            print(f"    合并完成，耗时 {elapsed:.2f}秒")
        except Exception as e:
            print(f"    合并失败: {e}")
            continue
        
        # 收缩回原始大小
        try:
            merged = merged.buffer(-0.01)
        except:
            pass
        
        # 创建 Feature
        if merged.geom_type == 'Polygon':
            merged = MultiPolygon([merged])
        
        if merged.geom_type == 'MultiPolygon':
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
    
    return {
        'type': 'FeatureCollection',
        'features': merged_features,
    }

def main():
    print("=" * 60)
    print("预处理世界历史数据：合并同势力地块边界")
    print("=" * 60)
    
    # 加载世界区域数据
    regions_data = load_geojson(GEO_DIR / 'world_regions.json')
    print(f"加载 {len(regions_data['features'])} 个区域")
    
    # 加载时期索引
    index_data = load_geojson(HISTORY_DIR / 'index.json')
    periods = index_data['periods']
    print(f"共 {len(periods)} 个历史时期\n")
    
    # 创建输出目录
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # 处理每个时期
    for period_info in periods:
        year = period_info['year']
        print(f"处理 {year} 年 - {period_info['name']}...")
        
        # 加载时期数据
        period_file = HISTORY_DIR / f'period_{year}.json'
        period_data = load_geojson(period_file)
        
        # 合并边界
        merged_data = merge_faction_geometries(regions_data, period_data)
        
        # 保存
        output_file = OUTPUT_DIR / f'period_{year}.json'
        save_geojson(merged_data, output_file)
        print(f"  保存 {len(merged_data['features'])} 个合并区域 -> {output_file}")
    
    # 保存索引
    save_geojson(index_data, OUTPUT_DIR / 'index.json')
    print(f"\n保存索引 -> {OUTPUT_DIR / 'index.json'}")
    
    print("\n" + "=" * 60)
    print("完成！")
    print("=" * 60)

if __name__ == "__main__":
    main()
