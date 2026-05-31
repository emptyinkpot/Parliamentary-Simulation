#!/usr/bin/env python3
"""
生成详细世界历史时期势力分布数据
基于 world_regions_detailed.json，为所有区域分配势力
"""

import json
from pathlib import Path

GEO_DIR = Path("/workspace/projects/public/geo")
OUTPUT_DIR = Path("/workspace/projects/public/history-detailed")

# 势力颜色配置
FACTION_COLORS = {
    'faction-1': {'name': '中国王朝', 'color': '#dc2626', 'outlineColor': '#991b1b'},
    'faction-2': {'name': '北方游牧', 'color': '#1e40af', 'outlineColor': '#1e3a8a'},
    'faction-3': {'name': '西域/中亚', 'color': '#15803d', 'outlineColor': '#166534'},
    'faction-4': {'name': '日本', 'color': '#b45309', 'outlineColor': '#92400e'},
    'faction-5': {'name': '朝鲜半岛', 'color': '#7c3aed', 'outlineColor': '#5b21b6'},
    'faction-6': {'name': '东南亚', 'color': '#be185d', 'outlineColor': '#9d174d'},
    'faction-7': {'name': '南亚/印度', 'color': '#0891b2', 'outlineColor': '#0e7490'},
    'faction-8': {'name': '中亚', 'color': '#65a30d', 'outlineColor': '#3f6212'},
    'faction-9': {'name': '西亚/中东', 'color': '#ca8a04', 'outlineColor': '#a16207'},
    'faction-10': {'name': '欧洲', 'color': '#6366f1', 'outlineColor': '#4f46e5'},
    'faction-11': {'name': '非洲', 'color': '#f97316', 'outlineColor': '#ea580c'},
    'faction-12': {'name': '美洲', 'color': '#14b8a6', 'outlineColor': '#0d9488'},
    'faction-13': {'name': '大洋洲', 'color': '#ec4899', 'outlineColor': '#db2777'},
    'faction-99': {'name': '未标注', 'color': '#94a3b8', 'outlineColor': '#64748b'},
}

# 国家代码到势力映射（默认）- 使用 ISO 3166-1 三位字母代码
COUNTRY_FACTION_MAP = {
    # 东亚
    'CHN': 'faction-1',  # 中国
    'JPN': 'faction-4',  # 日本
    'KOR': 'faction-5',  # 韩国
    'PRK': 'faction-5',  # 朝鲜
    'TWN': 'faction-1',  # 台湾
    
    # 东南亚
    'VNM': 'faction-6', 'LAO': 'faction-6', 'KHM': 'faction-6',
    'THA': 'faction-6', 'MMR': 'faction-6', 'MYS': 'faction-6',
    'SGP': 'faction-6', 'IDN': 'faction-6', 'PHL': 'faction-6',
    'BRN': 'faction-6', 'TLS': 'faction-6',
    
    # 南亚
    'IND': 'faction-7', 'PAK': 'faction-7', 'BGD': 'faction-7',
    'NPL': 'faction-7', 'BTN': 'faction-7', 'LKA': 'faction-7',
    'MDV': 'faction-7', 'AFG': 'faction-8',
    
    # 中亚
    'KAZ': 'faction-8', 'UZB': 'faction-8', 'TKM': 'faction-8',
    'KGZ': 'faction-8', 'TJK': 'faction-8',
    
    # 西亚/中东
    'IRN': 'faction-9', 'IRQ': 'faction-9', 'SYR': 'faction-9',
    'TUR': 'faction-9', 'SAU': 'faction-9', 'ARE': 'faction-9',
    'ISR': 'faction-9', 'JOR': 'faction-9', 'LBN': 'faction-9',
    'YEM': 'faction-9', 'OMN': 'faction-9', 'KWT': 'faction-9',
    'QAT': 'faction-9', 'BHR': 'faction-9',
    
    # 欧洲
    'RUS': 'faction-10', 'UKR': 'faction-10', 'BLR': 'faction-10',
    'POL': 'faction-10', 'DEU': 'faction-10', 'FRA': 'faction-10',
    'GBR': 'faction-10', 'ITA': 'faction-10', 'ESP': 'faction-10',
    'PRT': 'faction-10', 'NLD': 'faction-10', 'BEL': 'faction-10',
    'AUT': 'faction-10', 'CHE': 'faction-10', 'SWE': 'faction-10',
    'NOR': 'faction-10', 'DNK': 'faction-10', 'FIN': 'faction-10',
    'GRC': 'faction-10', 'ROU': 'faction-10', 'HUN': 'faction-10',
    'CZE': 'faction-10', 'SVK': 'faction-10', 'BGR': 'faction-10',
    'SRB': 'faction-10', 'HRV': 'faction-10', 'SVN': 'faction-10',
    'ALB': 'faction-10', 'MKD': 'faction-10', 'BIH': 'faction-10',
    'MNE': 'faction-10', 'XKX': 'faction-10', 'MDA': 'faction-10',
    'LTU': 'faction-10', 'LVA': 'faction-10', 'EST': 'faction-10',
    'IRL': 'faction-10', 'ISL': 'faction-10', 'LUX': 'faction-10',
    'MLT': 'faction-10', 'CYP': 'faction-10',
    
    # 非洲
    'EGY': 'faction-11', 'LBY': 'faction-11', 'TUN': 'faction-11',
    'DZA': 'faction-11', 'MAR': 'faction-11', 'SDN': 'faction-11',
    'ETH': 'faction-11', 'SOM': 'faction-11', 'KEN': 'faction-11',
    'UGA': 'faction-11', 'TZA': 'faction-11', 'RWA': 'faction-11',
    'BDI': 'faction-11', 'COD': 'faction-11', 'COG': 'faction-11',
    'CAF': 'faction-11', 'CMR': 'faction-11', 'NGA': 'faction-11',
    'NER': 'faction-11', 'MLI': 'faction-11', 'BFA': 'faction-11',
    'GHA': 'faction-11', 'CIV': 'faction-11', 'SEN': 'faction-11',
    'GMB': 'faction-11', 'GIN': 'faction-11', 'SLE': 'faction-11',
    'LBR': 'faction-11', 'MRT': 'faction-11', 'DJI': 'faction-11',
    'ERI': 'faction-11', 'SSD': 'faction-11', 'TCD': 'faction-11',
    'GAB': 'faction-11', 'GNQ': 'faction-11', 'AGO': 'faction-11',
    'ZMB': 'faction-11', 'ZWE': 'faction-11', 'BWA': 'faction-11',
    'NAM': 'faction-11', 'ZAF': 'faction-11', 'LSO': 'faction-11',
    'SWZ': 'faction-11', 'MOZ': 'faction-11', 'MDG': 'faction-11',
    'MUS': 'faction-11', 'SYC': 'faction-11', 'COM': 'faction-11',
    
    # 美洲
    'USA': 'faction-12', 'CAN': 'faction-12', 'MEX': 'faction-12',
    'GTM': 'faction-12', 'BLZ': 'faction-12', 'HND': 'faction-12',
    'SLV': 'faction-12', 'NIC': 'faction-12', 'CRI': 'faction-12',
    'PAN': 'faction-12', 'CUB': 'faction-12', 'JAM': 'faction-12',
    'HTI': 'faction-12', 'DOM': 'faction-12', 'PRI': 'faction-12',
    'COL': 'faction-12', 'VEN': 'faction-12', 'GUY': 'faction-12',
    'SUR': 'faction-12', 'ECU': 'faction-12', 'PER': 'faction-12',
    'BOL': 'faction-12', 'PRY': 'faction-12', 'URY': 'faction-12',
    'ARG': 'faction-12', 'CHL': 'faction-12', 'BRA': 'faction-12',
    
    # 大洋洲
    'AUS': 'faction-13', 'NZL': 'faction-13', 'PNG': 'faction-13',
    'FJI': 'faction-13', 'SLB': 'faction-13', 'VUT': 'faction-13',
    'NCL': 'faction-13', 'PYF': 'faction-13', 'WSM': 'faction-13',
    'TON': 'faction-13', 'KIR': 'faction-13', 'FSM': 'faction-13',
    'MHL': 'faction-13', 'PLW': 'faction-13', 'NRU': 'faction-13',
    'TUV': 'faction-13',
}

# 中国省份代码前缀
CHINA_PROVINCES = {
    '11': '北京', '12': '天津', '13': '河北', '14': '山西', '15': '内蒙古',
    '21': '辽宁', '22': '吉林', '23': '黑龙江',
    '31': '上海', '32': '江苏', '33': '浙江', '34': '安徽', '35': '福建',
    '36': '江西', '37': '山东',
    '41': '河南', '42': '湖北', '43': '湖南', '44': '广东', '45': '广西', '46': '海南',
    '50': '重庆', '51': '四川', '52': '贵州', '53': '云南', '54': '西藏',
    '61': '陕西', '62': '甘肃', '63': '青海', '64': '宁夏', '65': '新疆',
    '71': '台湾',
}

# 各时期势力配置
PERIODS = [
    {
        'year': 100,
        'name': '东汉时期',
        'description': '东汉王朝鼎盛时期，丝绸之路连接东西方',
        'china_factions': {
            'faction-1': {
                'name': '东汉',
                'provinces': ['11','12','13','14','21','22','23','31','32','33','34','35','36','37','41','42','43','44','45','50','51','52','53','61','62','64','65','46','71'],
            },
            'faction-2': {
                'name': '匈奴/鲜卑',
                'provinces': ['15'],
            },
            'faction-3': {
                'name': '西域诸国',
                'provinces': ['63', '54'],
            },
        },
        'special_names': {
            'faction-4': '倭国',
            'faction-5': '三韩',
        }
    },
    {
        'year': 220,
        'name': '三国时期',
        'description': '魏蜀吴三国鼎立，英雄辈出',
        'china_factions': {
            'faction-1': {
                'name': '魏',
                'provinces': ['11','12','13','14','15','21','22','23','31','32','34','35','36','37','41','42','44','45','46'],
            },
            'faction-2': {
                'name': '蜀汉',
                'provinces': ['50','51','52','53','61','62'],
            },
            'faction-3': {
                'name': '东吴',
                'provinces': ['33','43','71'],
            },
        },
        'special_names': {
            'faction-4': '邪马台国',
            'faction-5': '三韩',
        }
    },
    {
        'year': 400,
        'name': '南北朝',
        'description': '南北对峙，民族融合',
        'china_factions': {
            'faction-1': {
                'name': '南朝',
                'provinces': ['33','34','35','36','43','44','45','46','71'],
            },
            'faction-2': {
                'name': '北朝',
                'provinces': ['11','12','13','14','15','21','22','23','31','32','37','41','42','50','51','61','62','64'],
            },
            'faction-3': {
                'name': '吐谷浑/西域',
                'provinces': ['52','53','63','65','54'],
            },
        },
        'special_names': {
            'faction-4': '大和朝廷',
            'faction-5': '高句丽/百济/新罗',
        }
    },
    {
        'year': 600,
        'name': '隋朝',
        'description': '隋朝统一天下，开创科举',
        'china_factions': {
            'faction-1': {
                'name': '隋朝',
                'provinces': [p for p in ['11','12','13','14','15','21','22','23','31','32','33','34','35','36','37','41','42','43','44','45','46','50','51','52','53','61','62','63','64','65','71']],
            },
            'faction-2': {
                'name': '吐蕃',
                'provinces': ['54'],
            },
        },
        'special_names': {
            'faction-4': '飞鸟时代',
            'faction-5': '朝鲜三国',
        }
    },
    {
        'year': 750,
        'name': '唐朝鼎盛',
        'description': '唐朝疆域辽阔，万国来朝',
        'china_factions': {
            'faction-1': {
                'name': '唐朝',
                'provinces': [p for p in ['11','12','13','14','15','21','22','23','31','32','33','34','35','36','37','41','42','43','44','45','46','50','51','52','53','61','62','63','64','65','71']],
            },
            'faction-2': {
                'name': '吐蕃',
                'provinces': ['54'],
            },
        },
        'special_names': {
            'faction-4': '奈良时代',
            'faction-5': '统一新罗',
        }
    },
    {
        'year': 900,
        'name': '唐末五代',
        'description': '藩镇割据，五代十国',
        'china_factions': {
            'faction-1': {
                'name': '后梁',
                'provinces': ['11','12','13','14','37','41'],
            },
            'faction-2': {
                'name': '前蜀',
                'provinces': ['50','51','52','53'],
            },
            'faction-3': {
                'name': '吴越',
                'provinces': ['31','32','33','34','35'],
            },
            'faction-6': {
                'name': '南汉',
                'provinces': ['43','44','45','46','71'],
            },
            'faction-7': {
                'name': '契丹',
                'provinces': ['15','21','22','23'],
            },
            'faction-8': {
                'name': '其他藩镇',
                'provinces': ['36','42','61','62','63','64','65'],
            },
        },
        'special_names': {
            'faction-4': '平安时代',
            'faction-5': '后三国',
        }
    },
    {
        'year': 1100,
        'name': '北宋',
        'description': '北宋与辽、西夏并立',
        'china_factions': {
            'faction-1': {
                'name': '北宋',
                'provinces': [p for p in ['11','12','13','14','31','32','33','34','35','36','37','41','42','43','44','45','46','50','51','52','53','61','62','71']],
            },
            'faction-2': {
                'name': '辽',
                'provinces': ['15','21','22','23'],
            },
            'faction-3': {
                'name': '西夏',
                'provinces': ['63','64','65'],
            },
        },
        'special_names': {
            'faction-4': '平安时代',
            'faction-5': '高丽',
        }
    },
    {
        'year': 1200,
        'name': '南宋',
        'description': '南宋与金、西夏对峙',
        'china_factions': {
            'faction-1': {
                'name': '南宋',
                'provinces': ['31','32','33','34','35','36','43','44','45','46','50','51','52','53','71'],
            },
            'faction-2': {
                'name': '金',
                'provinces': ['11','12','13','14','15','21','22','23','37','41','42','61','62'],
            },
            'faction-3': {
                'name': '西夏',
                'provinces': ['63','64','65'],
            },
            'faction-6': {
                'name': '大理国',
                'provinces': ['54'],
            },
        },
        'special_names': {
            'faction-4': '镰仓幕府',
            'faction-5': '高丽',
        }
    },
    {
        'year': 1300,
        'name': '元朝',
        'description': '蒙古帝国统一欧亚大陆',
        'china_factions': {
            'faction-1': {
                'name': '元朝',
                'provinces': [p for p in ['11','12','13','14','15','21','22','23','31','32','33','34','35','36','37','41','42','43','44','45','46','50','51','52','53','54','61','62','63','64','65','71']],
            },
        },
        'special_names': {
            'faction-4': '镰仓幕府',
            'faction-5': '高丽（元征东行省）',
        },
        # 元朝时期蒙古势力扩展
        'override_country_faction': {
            'faction-2': ['MN', 'KZ', 'UZ', 'TM', 'KG', 'TJ'],  # 蒙古/中亚
        }
    },
    {
        'year': 1500,
        'name': '明朝',
        'description': '明朝国力强盛，郑和下西洋',
        'china_factions': {
            'faction-1': {
                'name': '明朝',
                'provinces': [p for p in ['11','12','13','14','15','21','22','23','31','32','33','34','35','36','37','41','42','43','44','45','46','50','51','52','53','61','62','63','64','65','71']],
            },
            'faction-2': {
                'name': '鞑靼/瓦剌',
                'provinces': ['54'],
            },
        },
        'special_names': {
            'faction-4': '战国时代',
            'faction-5': '朝鲜',
        }
    },
    {
        'year': 1750,
        'name': '清朝鼎盛',
        'description': '清朝疆域达到极盛',
        'china_factions': {
            'faction-1': {
                'name': '清朝',
                'provinces': [p for p in ['11','12','13','14','15','21','22','23','31','32','33','34','35','36','37','41','42','43','44','45','46','50','51','52','53','54','61','62','63','64','65','71']],
            },
        },
        'special_names': {
            'faction-4': '江户时代',
            'faction-5': '朝鲜',
        }
    },
    {
        'year': 1850,
        'name': '清末',
        'description': '清朝衰落，太平天国运动',
        'china_factions': {
            'faction-1': {
                'name': '清朝',
                'provinces': [p for p in ['11','12','13','14','15','21','22','23','31','32','33','34','35','36','37','41','42','45','46','50','51','52','53','54','61','62','63','64','65','71']],
            },
            'faction-2': {
                'name': '太平天国',
                'provinces': ['43', '44'],
            },
        },
        'special_names': {
            'faction-4': '幕末',
            'faction-5': '朝鲜',
        }
    },
    {
        'year': 1912,
        'name': '民国初年',
        'description': '中华民国成立',
        'china_factions': {
            'faction-1': {
                'name': '中华民国',
                'provinces': [p for p in ['11','12','13','14','21','22','23','31','32','33','34','35','36','37','41','42','43','44','45','46','50','51','52','53','61','62','63','64','65','71']],
            },
            'faction-2': {
                'name': '西藏',
                'provinces': ['54'],
            },
            'faction-3': {
                'name': '外蒙古',
                'provinces': ['15'],
            },
        },
        'special_names': {
            'faction-4': '大正时代',
            'faction-5': '朝鲜（日占）',
        }
    },
]

def load_regions():
    """加载详细世界区域数据"""
    with open(GEO_DIR / 'world_regions_detailed.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def generate_period_data(regions_data: dict, period: dict) -> dict:
    """生成单个时期的数据"""
    city_to_faction = {}
    
    # 构建中国省份势力映射
    china_province_faction = {}
    for faction_id, faction_data in period.get('china_factions', {}).items():
        for province_prefix in faction_data.get('provinces', []):
            china_province_faction[province_prefix] = faction_id
    
    # 为每个区域分配势力
    for feature in regions_data['features']:
        adcode = feature['properties']['adcode']
        country_code = feature['properties'].get('country_code', '')
        country = feature['properties'].get('country', '')
        
        # 中国地级市：按省份前缀分配
        if country_code == 'CN':
            adcode_str = str(adcode)
            if adcode_str.isdigit():
                province_prefix = adcode_str[:2]
                faction_id = china_province_faction.get(province_prefix, 'faction-1')
                city_to_faction[adcode] = faction_id
                continue
        else:
            # 其他国家：按国家代码分配
            faction_id = COUNTRY_FACTION_MAP.get(country_code, 'faction-99')
            
            # 应用时期特殊覆盖
            override = period.get('override_country_faction', {})
            for override_faction, countries in override.items():
                if country_code in countries:
                    faction_id = override_faction
                    break
            
            city_to_faction[adcode] = faction_id
    
    # 构建势力信息
    factions = {}
    
    # 添加中国势力
    for faction_id, faction_data in period.get('china_factions', {}).items():
        factions[faction_id] = {
            'name': faction_data['name'],
            'color': FACTION_COLORS.get(faction_id, FACTION_COLORS['faction-99'])['color'],
            'outlineColor': FACTION_COLORS.get(faction_id, FACTION_COLORS['faction-99'])['outlineColor'],
        }
    
    # 添加特殊势力名称
    for faction_id, name in period.get('special_names', {}).items():
        if faction_id not in factions:
            factions[faction_id] = {
                'name': name,
                'color': FACTION_COLORS.get(faction_id, FACTION_COLORS['faction-99'])['color'],
                'outlineColor': FACTION_COLORS.get(faction_id, FACTION_COLORS['faction-99'])['outlineColor'],
            }
    
    # 添加其他出现过的势力
    for adcode, faction_id in city_to_faction.items():
        if faction_id not in factions:
            factions[faction_id] = {
                'name': FACTION_COLORS.get(faction_id, FACTION_COLORS['faction-99'])['name'],
                'color': FACTION_COLORS.get(faction_id, FACTION_COLORS['faction-99'])['color'],
                'outlineColor': FACTION_COLORS.get(faction_id, FACTION_COLORS['faction-99'])['outlineColor'],
            }
    
    return {
        'year': period['year'],
        'name': period['name'],
        'description': period['description'],
        'factions': factions,
        'cityToFaction': city_to_faction,
    }

def main():
    print("=" * 60)
    print("生成详细世界历史时期数据")
    print("=" * 60)
    
    # 加载区域数据
    regions_data = load_regions()
    print(f"加载 {len(regions_data['features'])} 个区域")
    
    # 统计国家分布
    country_counts = {}
    for f in regions_data['features']:
        c = f['properties'].get('country', '未知')
        country_counts[c] = country_counts.get(c, 0) + 1
    
    print("\n主要国家:")
    for c, count in sorted(country_counts.items(), key=lambda x: -x[1])[:10]:
        print(f"  {c}: {count}")
    
    # 创建输出目录
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # 生成每个时期的数据
    index_data = {'periods': []}
    
    for period in PERIODS:
        print(f"\n处理 {period['year']} 年 - {period['name']}...")
        
        period_data = generate_period_data(regions_data, period)
        
        # 统计势力分布
        faction_counts = {}
        for fid in period_data['cityToFaction'].values():
            fname = period_data['factions'].get(fid, {}).get('name', fid)
            faction_counts[fname] = faction_counts.get(fname, 0) + 1
        
        print(f"  势力分布:")
        for fname, count in sorted(faction_counts.items(), key=lambda x: -x[1])[:5]:
            print(f"    {fname}: {count}")
        
        # 保存时期数据
        output_file = OUTPUT_DIR / f"period_{period['year']}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(period_data, f, ensure_ascii=False)
        
        index_data['periods'].append({
            'year': period['year'],
            'name': period['name'],
            'description': period['description'],
        })
    
    # 保存索引
    with open(OUTPUT_DIR / 'index.json', 'w', encoding='utf-8') as f:
        json.dump(index_data, f, ensure_ascii=False, indent=2)
    
    print("\n" + "=" * 60)
    print(f"完成！共生成 {len(PERIODS)} 个时期")
    print(f"输出目录: {OUTPUT_DIR}")
    print("=" * 60)

if __name__ == "__main__":
    main()
