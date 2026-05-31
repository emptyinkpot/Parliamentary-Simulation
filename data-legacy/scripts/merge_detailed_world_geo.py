#!/usr/bin/env python3
"""
合并详细的世界行政区划数据
使用中国地级市 + Natural Earth 省级数据
"""

import json
from pathlib import Path
from shapely.geometry import shape, mapping, MultiPolygon
from shapely.validation import make_valid

GEO_DIR = Path("/workspace/projects/public/geo")
OUTPUT_DIR = Path("/workspace/projects/public/geo")

def load_geojson(path: Path) -> dict:
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_geojson(data: dict, path: Path):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False)

def simplify_geometry(geom, tolerance=0.01):
    """简化几何体以减小文件大小"""
    try:
        simplified = geom.simplify(tolerance, preserve_topology=True)
        return simplified
    except:
        return geom

def process_geometry(geom_data: dict, simplify: bool = True, tolerance: float = 0.005) -> dict:
    """处理几何数据，确保有效性"""
    try:
        geom = shape(geom_data)
        if not geom.is_valid:
            geom = make_valid(geom)
        if simplify:
            geom = simplify_geometry(geom, tolerance=tolerance)
        return mapping(geom)
    except Exception as e:
        return geom_data

def main():
    print("=" * 60)
    print("合并详细世界行政区划数据")
    print("=" * 60)
    
    all_features = []
    
    # 1. 加载中国地级市数据
    print("\n处理中国地级市...")
    china_data = load_geojson(GEO_DIR / 'china_cities.json')
    china_count = 0
    for feature in china_data['features']:
        adcode = str(feature['properties']['adcode'])
        # 中国 adcode 以 1-6 开头，保留原有地级市数据
        if adcode[0] in '123456':
            # 添加国家标识
            feature['properties']['country'] = '中国'
            feature['properties']['country_code'] = 'CN'
            feature['properties']['region_type'] = '地级市'
            all_features.append(feature)
            china_count += 1
    print(f"  中国: {china_count} 个地级市")
    
    # 2. 加载日本数据
    print("\n处理日本...")
    try:
        japan_data = load_geojson(GEO_DIR / 'japan_prefectures.json')
        japan_count = 0
        for i, feature in enumerate(japan_data['features']):
            name = feature['properties'].get('name', feature['properties'].get('NAME', f'region_{i}'))
            # 简化几何
            feature['geometry'] = process_geometry(feature['geometry'], simplify=True, tolerance=0.01)
            feature['properties'] = {
                'adcode': f'JP_{i:02d}',
                'name': name,
                'country': '日本',
                'country_code': 'JP',
                'region_type': '都道府县',
            }
            all_features.append(feature)
            japan_count += 1
        print(f"  日本: {japan_count} 个都道府县")
    except Exception as e:
        print(f"  日本数据处理失败: {e}")
    
    # 3. 加载韩国数据
    print("\n处理韩国...")
    try:
        korea_data = load_geojson(GEO_DIR / 'south_korea_provinces.json')
        korea_count = 0
        for i, feature in enumerate(korea_data['features']):
            name = feature['properties'].get('name', feature['properties'].get('NAME', f'region_{i}'))
            feature['geometry'] = process_geometry(feature['geometry'], simplify=True, tolerance=0.01)
            feature['properties'] = {
                'adcode': f'KR_{i:02d}',
                'name': name,
                'country': '韩国',
                'country_code': 'KR',
                'region_type': '省/市',
            }
            all_features.append(feature)
            korea_count += 1
        print(f"  韩国: {korea_count} 个省")
    except Exception as e:
        print(f"  韩国数据处理失败: {e}")
    
    # 4. 加载朝鲜数据
    print("\n处理朝鲜...")
    try:
        nk_data = load_geojson(GEO_DIR / 'north_korea_provinces.json')
        nk_count = 0
        for i, feature in enumerate(nk_data['features']):
            name = feature['properties'].get('name', feature['properties'].get('NAME', f'region_{i}'))
            feature['geometry'] = process_geometry(feature['geometry'], simplify=True, tolerance=0.01)
            feature['properties'] = {
                'adcode': f'KP_{i:02d}',
                'name': name,
                'country': '朝鲜',
                'country_code': 'KP',
                'region_type': '省',
            }
            all_features.append(feature)
            nk_count += 1
        print(f"  朝鲜: {nk_count} 个省")
    except Exception as e:
        print(f"  朝鲜数据处理失败: {e}")
    
    # 5. 加载详细的世界省级数据
    print("\n处理世界其他地区...")
    world_data = load_geojson(GEO_DIR / 'detailed' / 'world_provinces_detailed.json')
    
    # 按国家统计
    country_counts = {}
    world_count = 0
    
    # 需要排除的国家（已单独处理）
    exclude_codes = ['CHN', 'JPN', 'KOR', 'PRK', 'TWN']
    exclude_names = ['China', 'Japan', 'South Korea', 'North Korea', 'Taiwan']
    
    for feature in world_data['features']:
        props = feature['properties']
        country = props.get('adm0name', props.get('admin', ''))
        country_en = props.get('adm0_a3', '')
        
        # 排除已处理的国家
        if country in exclude_names or country_en in exclude_codes:
            continue
        
        # 创建唯一 adcode
        iso_code = props.get('iso_3166_2', '')
        if iso_code:
            adcode = iso_code.replace('-', '_')
        else:
            name = props.get('name', props.get('name_en', 'unknown'))
            adcode = f"{country_en}_{name}".replace(' ', '_').replace('/', '_')
        
        # 简化几何（世界其他地区使用更大容差）
        feature['geometry'] = process_geometry(feature['geometry'], simplify=True, tolerance=0.02)
        
        # 标准化属性
        feature['properties'] = {
            'adcode': adcode,
            'name': props.get('name', props.get('name_en', '')),
            'name_en': props.get('name_en', ''),
            'country': country,
            'country_code': country_en,
            'region_type': props.get('type', '省/州'),
        }
        
        all_features.append(feature)
        country_counts[country] = country_counts.get(country, 0) + 1
        world_count += 1
    
    # 打印统计
    print(f"\n  世界其他地区共 {world_count} 个省级区域")
    print("\n  主要国家:")
    for country, count in sorted(country_counts.items(), key=lambda x: -x[1])[:20]:
        print(f"    {country}: {count} 个区域")
    
    # 保存合并数据
    output_data = {
        'type': 'FeatureCollection',
        'features': all_features,
    }
    
    output_file = OUTPUT_DIR / 'world_regions_detailed.json'
    save_geojson(output_data, output_file)
    
    print("\n" + "=" * 60)
    print(f"完成！共 {len(all_features)} 个地块")
    print(f"输出: {output_file}")
    print("=" * 60)

if __name__ == "__main__":
    main()
