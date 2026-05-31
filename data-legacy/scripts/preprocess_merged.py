#!/usr/bin/env python3
"""
预处理历史时期数据：合并同势力相邻地块
使用 Shapely 库进行几何合并，处理拓扑错误更健壮
"""

import json
import os
from pathlib import Path
from shapely.geometry import shape, mapping, MultiPolygon, Polygon
from shapely.ops import unary_union
from shapely.validation import make_valid

# 路径配置
GEOJSON_PATH = Path("/workspace/projects/public/geo/china_cities.json")
HISTORY_DIR = Path("/workspace/projects/public/history")
OUTPUT_DIR = Path("/workspace/projects/public/history-merged")

def load_geojson(path: Path) -> dict:
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_geojson(data: dict, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False)

def merge_polygons_for_faction(geojson: dict, city_to_faction: dict, faction_id: str) -> dict | None:
    """合并同一势力的所有多边形"""
    from shapely.geometry import MultiPolygon, Polygon
    from shapely.ops import unary_union
    
    # 收集该势力的所有地块几何
    polygons = []
    
    for feature in geojson['features']:
        if not feature.get('properties') or 'adcode' not in feature['properties']:
            continue
        
        adcode = str(feature['properties']['adcode'])
        
        if city_to_faction.get(adcode) == faction_id:
            geom = feature.get('geometry')
            if geom and geom.get('type') in ('Polygon', 'MultiPolygon'):
                try:
                    poly = shape(geom)
                    # 修复无效几何
                    if not poly.is_valid:
                        poly = make_valid(poly)
                    
                    # 只保留 Polygon 和 MultiPolygon
                    if poly.geom_type == 'Polygon':
                        polygons.append(poly)
                    elif poly.geom_type == 'MultiPolygon':
                        polygons.append(poly)
                    elif poly.geom_type == 'GeometryCollection':
                        for g in poly.geoms:
                            if g.geom_type == 'Polygon':
                                polygons.append(g)
                            elif g.geom_type == 'MultiPolygon':
                                polygons.append(g)
                except Exception as e:
                    print(f"      警告: 地块 {adcode} 几何解析失败: {e}")
    
    if not polygons:
        return None
    
    print(f"    合并 {len(polygons)} 个地块...")
    
    try:
        # 第一步：轻微扩展每个多边形（填充缝隙）
        # buffer_distance = 0.01 度 ≈ 1km
        BUFFER_DIST = 0.01
        buffered_polys = [p.buffer(BUFFER_DIST) for p in polygons]
        
        # 第二步：合并所有扩展后的多边形
        merged = unary_union(buffered_polys)
        
        # 第三步：收缩回来，恢复原始边界
        merged = merged.buffer(-BUFFER_DIST)
        
        # 简化几何以减少数据量
        merged = merged.simplify(0.01, preserve_topology=True)
        
        # 提取所有多边形
        def extract_polygons(geom):
            if geom.geom_type == 'Polygon':
                return [geom]
            elif geom.geom_type == 'MultiPolygon':
                return list(geom.geoms)
            elif geom.geom_type == 'GeometryCollection':
                result = []
                for g in geom.geoms:
                    result.extend(extract_polygons(g))
                return result
            return []
        
        poly_list = extract_polygons(merged)
        if not poly_list:
            return None
        
        if len(poly_list) == 1:
            merged = poly_list[0]
        else:
            merged = MultiPolygon(poly_list)
        
        if merged.is_empty:
            return None
            
        return mapping(merged)
    except Exception as e:
        print(f"      错误: 合并失败: {e}")
        return None

def process_period(year: int, geojson: dict) -> dict:
    """处理单个时期"""
    print(f"\n处理 {year} 年...")
    
    # 读取时期数据
    period_path = HISTORY_DIR / f"period_{year}.json"
    period_data = load_geojson(period_path)
    
    factions = period_data['factions']
    city_to_faction = period_data['cityToFaction']
    
    # 为每个势力合并多边形
    merged_features = []
    
    for faction_id, faction_data in factions.items():
        print(f"  势力: {faction_data['name']}")
        
        merged_geom = merge_polygons_for_faction(geojson, city_to_faction, faction_id)
        
        if merged_geom:
            # 创建合并后的 feature
            feature = {
                "type": "Feature",
                "properties": {
                    "factionId": faction_id,
                    "factionName": faction_data['name'],
                    "color": faction_data['color'],
                    "outlineColor": faction_data['outlineColor'],
                    "year": year,
                },
                "geometry": merged_geom,
            }
            merged_features.append(feature)
            print(f"    ✓ 合并完成")
        else:
            print(f"    ⚠ 无地块数据")
    
    # 输出合并后的数据
    output = {
        "type": "FeatureCollection",
        "features": merged_features,
    }
    
    output_path = OUTPUT_DIR / f"period_{year}.json"
    save_geojson(output, output_path)
    
    print(f"  保存到: {output_path} ({len(merged_features)} 个势力)")
    
    return {
        "year": year,
        "name": period_data['name'],
        "description": period_data['description'],
        "featuresCount": len(merged_features),
    }

def main():
    print("加载地理数据...")
    geojson = load_geojson(GEOJSON_PATH)
    print(f"共 {len(geojson['features'])} 个地块")
    
    # 获取所有时期
    index_data = load_geojson(HISTORY_DIR / "index.json")
    periods = index_data['periods']
    
    # 处理每个时期
    processed_periods = []
    for period in periods:
        result = process_period(period['year'], geojson)
        processed_periods.append(result)
    
    # 保存索引
    index_output = {
        "periods": [
            {
                "year": p['year'],
                "name": p['name'],
                "description": p['description'],
                "featuresCount": p['featuresCount'],
            }
            for p in processed_periods
        ]
    }
    save_geojson(index_output, OUTPUT_DIR / "index.json")
    
    print("\n========================================")
    print("预处理完成！")
    print(f"共处理 {len(processed_periods)} 个时期")
    print(f"输出目录: {OUTPUT_DIR}")

if __name__ == "__main__":
    main()
