#!/usr/bin/env python3
"""
下载详细的世界行政区划数据（省级/州级）
使用 Natural Earth 1:10m 数据和 GADM 数据
"""

import json
import urllib.request
import zipfile
import io
import os
from pathlib import Path
import shapefile  # pyshp

OUTPUT_DIR = Path("/workspace/projects/public/geo/detailed")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Natural Earth 1:10m 省级数据
NE_URL = "https://naturalearth.s3.amazonaws.com/10m_cultural/ne_10m_admin_1_states_provinces.zip"

def download_natural_earth():
    """下载 Natural Earth 1:10m 省级数据"""
    print("下载 Natural Earth 1:10m 省级数据...")
    
    try:
        req = urllib.request.Request(NE_URL, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=60) as response:
            data = response.read()
        
        # 解压
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            z.extractall('/tmp/ne_10m_provinces')
        
        print("下载完成！")
        return '/tmp/ne_10m_provinces'
    except Exception as e:
        print(f"下载失败: {e}")
        return None

def convert_shapefile_to_geojson(shp_dir: str):
    """转换 Shapefile 为 GeoJSON"""
    print("转换 Shapefile 为 GeoJSON...")
    
    shp_file = None
    for f in os.listdir(shp_dir):
        if f.endswith('.shp'):
            shp_file = os.path.join(shp_dir, f)
            break
    
    if not shp_file:
        print("未找到 .shp 文件")
        return None
    
    sf = shapefile.Reader(shp_file)
    fields = [f[0] for f in sf.fields[1:]]  # 跳过第一个 DeletionFlag
    
    features = []
    for shape_rec in sf.shapeRecords():
        # 获取属性
        attrs = dict(zip(fields, shape_rec.record))
        
        # 获取几何
        geom = None
        if shape_rec.shape.shapeType == shapefile.POLYGON:
            # 处理多边形
            parts = shape_rec.shape.parts
            points = shape_rec.shape.points
            
            if len(parts) == 1:
                # 单个多边形
                geom = {
                    'type': 'Polygon',
                    'coordinates': [points]
                }
            else:
                # 多部分多边形
                polygons = []
                for i in range(len(parts)):
                    start = parts[i]
                    end = parts[i + 1] if i + 1 < len(parts) else len(points)
                    ring = points[start:end]
                    if len(ring) >= 4:  # 有效多边形至少4个点
                        polygons.append([ring])
                
                if len(polygons) == 1:
                    geom = {
                        'type': 'Polygon',
                        'coordinates': polygons[0]
                    }
                elif len(polygons) > 1:
                    geom = {
                        'type': 'MultiPolygon',
                        'coordinates': polygons
                    }
        
        if geom:
            feature = {
                'type': 'Feature',
                'properties': {
                    'name': attrs.get('name', attrs.get('NAME', '')),
                    'name_en': attrs.get('name_en', attrs.get('NAME_EN', '')),
                    'adm0name': attrs.get('adm0name', attrs.get('ADM0NAME', attrs.get('admin', ''))),  # 国家名
                    'adm0_a3': attrs.get('adm0_a3', attrs.get('ADM0_A3', '')),  # 国家代码
                    'iso_3166_2': attrs.get('iso_3166_2', ''),  # ISO 代码
                    'type': attrs.get('type', attrs.get('TYPE', '')),
                },
                'geometry': geom
            }
            features.append(feature)
    
    return {
        'type': 'FeatureCollection',
        'features': features
    }

def main():
    print("=" * 60)
    print("下载详细世界行政区划数据")
    print("=" * 60)
    
    # 下载 Natural Earth 数据
    shp_dir = download_natural_earth()
    if not shp_dir:
        print("下载失败，尝试使用备用数据...")
        return
    
    # 转换为 GeoJSON
    geojson = convert_shapefile_to_geojson(shp_dir)
    if not geojson:
        print("转换失败")
        return
    
    # 统计
    countries = set()
    for f in geojson['features']:
        country = f['properties'].get('adm0name', '')
        if country:
            countries.add(country)
    
    print(f"\n统计:")
    print(f"  总地块数: {len(geojson['features'])}")
    print(f"  国家/地区数: {len(countries)}")
    
    # 保存
    output_file = OUTPUT_DIR / 'world_provinces_detailed.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(geojson, f, ensure_ascii=False)
    
    print(f"\n保存到: {output_file}")
    print("=" * 60)

if __name__ == "__main__":
    main()
