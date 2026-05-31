#!/usr/bin/env python3
"""
合并世界地理数据，创建统一的地块数据
包含：中国地级市 + 日本都道府县 + 韩国省 + 朝鲜省 + 其他亚洲国家 + 世界主要国家
"""

import json
from pathlib import Path
from shapely.geometry import shape, mapping, MultiPolygon, Polygon
from shapely.validation import make_valid
from shapely.ops import unary_union

GEO_DIR = Path("/workspace/projects/public/geo")
OUTPUT_FILE = GEO_DIR / "world_regions.json"

def load_geojson(filename: str) -> dict:
    path = GEO_DIR / filename
    if not path.exists():
        print(f"  文件不存在: {filename}")
        return {"type": "FeatureCollection", "features": []}
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def simplify_geometry(geom, tolerance=0.05):
    """简化几何以减少数据量"""
    simplified = geom.simplify(tolerance, preserve_topology=True)
    if simplified.is_empty:
        return geom
    return simplified

def process_china():
    """处理中国地级市数据"""
    print("处理中国地级市...")
    data = load_geojson("china_cities.json")
    features = []
    
    for f in data['features']:
        props = f['properties']
        geom = shape(f['geometry'])
        if not geom.is_valid:
            geom = make_valid(geom)
        
        features.append({
            "type": "Feature",
            "properties": {
                "adcode": str(props.get('adcode', '')),
                "name": props.get('name', ''),
                "country": "中国",
                "level": "city",
            },
            "geometry": mapping(geom)
        })
    
    print(f"  中国: {len(features)} 个地级市")
    return features

def process_japan():
    """处理日本都道府县数据"""
    print("处理日本...")
    data = load_geojson("japan_prefectures.json")
    features = []
    
    for f in data['features']:
        props = f['properties']
        geom = shape(f['geometry'])
        if not geom.is_valid:
            geom = make_valid(geom)
        geom = simplify_geometry(geom, 0.02)
        
        # 尝试获取名称
        name = props.get('name') or props.get('NAME_1') or props.get('name_1') or props.get('NL_NAME_1') or 'Unknown'
        
        features.append({
            "type": "Feature",
            "properties": {
                "adcode": f"JP_{len(features):03d}",
                "name": name,
                "country": "日本",
                "level": "prefecture",
            },
            "geometry": mapping(geom)
        })
    
    print(f"  日本: {len(features)} 个都道府县")
    return features

def process_korea():
    """处理韩国和朝鲜数据"""
    print("处理朝鲜半岛...")
    features = []
    
    # 韩国
    sk_data = load_geojson("south_korea_provinces.json")
    for i, f in enumerate(sk_data['features']):
        props = f['properties']
        geom = shape(f['geometry'])
        if not geom.is_valid:
            geom = make_valid(geom)
        geom = simplify_geometry(geom, 0.02)
        
        name = props.get('name') or props.get('NAME_1') or props.get('name_1') or f'韩国{i+1}'
        
        features.append({
            "type": "Feature",
            "properties": {
                "adcode": f"KR_{i:03d}",
                "name": name,
                "country": "韩国",
                "level": "province",
            },
            "geometry": mapping(geom)
        })
    print(f"  韩国: {len(sk_data['features'])} 个省")
    
    # 朝鲜
    nk_data = load_geojson("north_korea_provinces.json")
    for i, f in enumerate(nk_data['features']):
        props = f['properties']
        geom = shape(f['geometry'])
        if not geom.is_valid:
            geom = make_valid(geom)
        geom = simplify_geometry(geom, 0.02)
        
        name = props.get('name') or props.get('NAME_1') or props.get('name_1') or f'朝鲜{i+1}'
        
        features.append({
            "type": "Feature",
            "properties": {
                "adcode": f"KP_{i:03d}",
                "name": name,
                "country": "朝鲜",
                "level": "province",
            },
            "geometry": mapping(geom)
        })
    print(f"  朝鲜: {len(nk_data['features'])} 个省")
    
    return features

def process_asian_countries():
    """处理其他亚洲国家"""
    print("处理亚洲其他国家...")
    data = load_geojson("asian_countries.json")
    features = []
    
    # 亚洲国家列表（排除已处理的）
    exclude = ['China', 'Japan', 'South Korea', 'North Korea', 'Taiwan']
    
    for f in data['features']:
        props = f['properties']
        name = props.get('name') or props.get('NAME') or props.get('SOVEREIGNT') or 'Unknown'
        
        # 跳过已处理的国家
        if any(ex.lower() in name.lower() for ex in exclude):
            continue
        
        geom = shape(f['geometry'])
        if not geom.is_valid:
            geom = make_valid(geom)
        geom = simplify_geometry(geom, 0.05)
        
        # 生成唯一 adcode
        country_code = name[:2].upper()
        
        features.append({
            "type": "Feature",
            "properties": {
                "adcode": f"AS_{country_code}_{len(features):03d}",
                "name": name,
                "country": name,
                "level": "country",
            },
            "geometry": mapping(geom)
        })
    
    print(f"  亚洲其他国家: {len(features)} 个")
    return features

def process_world_countries():
    """处理世界其他国家"""
    print("处理世界其他国家...")
    data = load_geojson("world_countries.json")
    features = []
    
    # 已处理的国家/地区
    processed = ['china', 'japan', 'korea', 'taiwan', 'mongolia', 'vietnam', 'laos', 
                 'cambodia', 'thailand', 'myanmar', 'malaysia', 'indonesia', 'philippines',
                 'singapore', 'brunei', 'east timor', 'india', 'pakistan', 'bangladesh',
                 'nepal', 'bhutan', 'sri lanka', 'afghanistan']
    
    for f in data['features']:
        props = f['properties']
        name = props.get('name') or props.get('NAME') or props.get('SOVEREIGNT') or 'Unknown'
        
        # 跳过已处理的亚洲国家
        if any(p in name.lower() for p in processed):
            continue
        
        geom = shape(f['geometry'])
        if not geom.is_valid:
            geom = make_valid(geom)
        
        # 对于大国进一步简化，对于小国保持原样
        area = geom.area
        if area > 100:  # 大国如俄罗斯、加拿大
            geom = simplify_geometry(geom, 0.2)
        elif area > 10:  # 中等国家
            geom = simplify_geometry(geom, 0.1)
        else:
            geom = simplify_geometry(geom, 0.05)
        
        country_code = name[:2].upper()
        
        features.append({
            "type": "Feature",
            "properties": {
                "adcode": f"WL_{country_code}_{len(features):03d}",
                "name": name,
                "country": name,
                "level": "country",
            },
            "geometry": mapping(geom)
        })
    
    print(f"  世界其他国家: {len(features)} 个")
    return features

def main():
    print("=" * 50)
    print("合并世界地理数据")
    print("=" * 50)
    
    all_features = []
    
    # 处理各地区
    all_features.extend(process_china())
    all_features.extend(process_japan())
    all_features.extend(process_korea())
    all_features.extend(process_asian_countries())
    all_features.extend(process_world_countries())
    
    # 输出合并结果
    output = {
        "type": "FeatureCollection",
        "features": all_features
    }
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False)
    
    print("\n" + "=" * 50)
    print(f"完成！共 {len(all_features)} 个地块")
    print(f"输出: {OUTPUT_FILE}")
    print("=" * 50)

if __name__ == "__main__":
    main()
