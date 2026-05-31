#!/usr/bin/env python3
"""
重新生成详细世界历史时期势力分布数据
修复国家代码映射问题
"""

import json
from pathlib import Path

GEO_DIR = Path("/workspace/projects/public/geo")
OUTPUT_DIR = Path("/workspace/projects/public/history-detailed")

# 势力颜色配置
FACTION_COLORS = {
    'faction-1': {'name': '中国王朝', 'color': '#dc2626', 'outlineColor': '#991b1b'},
    'faction-2': {'name': '北方游牧', 'color': '#1e40af', 'outlineColor': '#1e3a8a'},
    'faction-3': {'name': '西域/青藏', 'color': '#15803d', 'outlineColor': '#166534'},
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

# 国家代码到势力映射 - 使用2位ISO代码（与地理数据一致）
COUNTRY_FACTION_MAP = {
    # 东亚
    'CN': 'faction-1',  # 中国
    'JP': 'faction-4',  # 日本
    'KR': 'faction-5',  # 韩国
    'KP': 'faction-5',  # 朝鲜
    'TW': 'faction-1',  # 台湾
    
    # 东南亚
    'VN': 'faction-6', 'LA': 'faction-6', 'KH': 'faction-6',
    'TH': 'faction-6', 'MM': 'faction-6', 'MY': 'faction-6',
    'SG': 'faction-6', 'ID': 'faction-6', 'PH': 'faction-6',
    'BN': 'faction-6', 'TL': 'faction-6',
    
    # 南亚
    'IN': 'faction-7', 'PK': 'faction-7', 'BD': 'faction-7',
    'NP': 'faction-7', 'BT': 'faction-7', 'LK': 'faction-7',
    'MV': 'faction-7', 'AF': 'faction-8',
    
    # 中亚
    'KZ': 'faction-8', 'UZ': 'faction-8', 'TM': 'faction-8',
    'KG': 'faction-8', 'TJ': 'faction-8',
    
    # 西亚/中东
    'IR': 'faction-9', 'IQ': 'faction-9', 'SY': 'faction-9',
    'TR': 'faction-9', 'SA': 'faction-9', 'AE': 'faction-9',
    'IL': 'faction-9', 'JO': 'faction-9', 'LB': 'faction-9',
    'YE': 'faction-9', 'OM': 'faction-9', 'KW': 'faction-9',
    'QA': 'faction-9', 'BH': 'faction-9',
    
    # 欧洲
    'RU': 'faction-10', 'UA': 'faction-10', 'BY': 'faction-10',
    'PL': 'faction-10', 'DE': 'faction-10', 'FR': 'faction-10',
    'GB': 'faction-10', 'IT': 'faction-10', 'ES': 'faction-10',
    'PT': 'faction-10', 'NL': 'faction-10', 'BE': 'faction-10',
    'AT': 'faction-10', 'CH': 'faction-10', 'SE': 'faction-10',
    'NO': 'faction-10', 'DK': 'faction-10', 'FI': 'faction-10',
    'GR': 'faction-10', 'RO': 'faction-10', 'HU': 'faction-10',
    'CZ': 'faction-10', 'SK': 'faction-10', 'BG': 'faction-10',
    'RS': 'faction-10', 'HR': 'faction-10', 'SI': 'faction-10',
    'AL': 'faction-10', 'MK': 'faction-10', 'BA': 'faction-10',
    'ME': 'faction-10', 'XK': 'faction-10', 'MD': 'faction-10',
    'LT': 'faction-10', 'LV': 'faction-10', 'EE': 'faction-10',
    'IE': 'faction-10', 'IS': 'faction-10', 'LU': 'faction-10',
    'MT': 'faction-10', 'CY': 'faction-10',
    
    # 非洲
    'EG': 'faction-11', 'LY': 'faction-11', 'TN': 'faction-11',
    'DZ': 'faction-11', 'MA': 'faction-11', 'SD': 'faction-11',
    'ET': 'faction-11', 'SO': 'faction-11', 'KE': 'faction-11',
    'UG': 'faction-11', 'TZ': 'faction-11', 'RW': 'faction-11',
    'BI': 'faction-11', 'CD': 'faction-11', 'CG': 'faction-11',
    'CF': 'faction-11', 'CM': 'faction-11', 'NG': 'faction-11',
    'NE': 'faction-11', 'ML': 'faction-11', 'BF': 'faction-11',
    'GH': 'faction-11', 'CI': 'faction-11', 'SN': 'faction-11',
    'GM': 'faction-11', 'GN': 'faction-11', 'SL': 'faction-11',
    'LR': 'faction-11', 'MR': 'faction-11', 'DJ': 'faction-11',
    'ER': 'faction-11', 'SS': 'faction-11', 'TD': 'faction-11',
    'GA': 'faction-11', 'GQ': 'faction-11', 'AO': 'faction-11',
    'ZM': 'faction-11', 'ZW': 'faction-11', 'BW': 'faction-11',
    'NA': 'faction-11', 'ZA': 'faction-11', 'LS': 'faction-11',
    'SZ': 'faction-11', 'MZ': 'faction-11', 'MG': 'faction-11',
    'MU': 'faction-11', 'SC': 'faction-11', 'KM': 'faction-11',
    
    # 美洲
    'US': 'faction-12', 'CA': 'faction-12', 'MX': 'faction-12',
    'GT': 'faction-12', 'BZ': 'faction-12', 'HN': 'faction-12',
    'SV': 'faction-12', 'NI': 'faction-12', 'CR': 'faction-12',
    'PA': 'faction-12', 'CU': 'faction-12', 'JM': 'faction-12',
    'HT': 'faction-12', 'DO': 'faction-12', 'PR': 'faction-12',
    'CO': 'faction-12', 'VE': 'faction-12', 'GY': 'faction-12',
    'SR': 'faction-12', 'EC': 'faction-12', 'PE': 'faction-12',
    'BO': 'faction-12', 'PY': 'faction-12', 'UY': 'faction-12',
    'AR': 'faction-12', 'CL': 'faction-12', 'BR': 'faction-12',
    
    # 大洋洲
    'AU': 'faction-13', 'NZ': 'faction-13', 'PG': 'faction-13',
    'FJ': 'faction-13', 'SB': 'faction-13', 'VU': 'faction-13',
    'NC': 'faction-13', 'PF': 'faction-13', 'WS': 'faction-13',
    'TO': 'faction-13', 'KI': 'faction-13', 'FM': 'faction-13',
    'MH': 'faction-13', 'PW': 'faction-13', 'NR': 'faction-13',
    'TV': 'faction-13',
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
    with open(GEO_DIR / 'world_regions_detailed.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def generate_period_data(regions_data: dict, period: dict) -> dict:
    city_to_faction = {}
    
    # 构建中国省份势力映射
    china_province_faction = {}
    for faction_id, faction_data in period.get('china_factions', {}).items():
        for province_prefix in faction_data.get('provinces', []):
            china_province_faction[province_prefix] = faction_id
    
    # 为每个区域分配势力
    for feature in regions_data['features']:
        adcode = str(feature['properties']['adcode'])
        country_code = feature['properties'].get('country_code', '')
        country = feature['properties'].get('country', '')
        
        # 中国地级市：按省份前缀分配
        if country_code == 'CN' and adcode.isdigit():
            province_prefix = adcode[:2]
            faction_id = china_province_faction.get(province_prefix, 'faction-1')
            city_to_faction[adcode] = faction_id
        else:
            # 其他国家：按国家代码分配
            faction_id = COUNTRY_FACTION_MAP.get(country_code, 'faction-99')
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
    print("重新生成详细世界历史时期数据")
    print("=" * 60)
    
    regions_data = load_regions()
    print(f"加载 {len(regions_data['features'])} 个区域")
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
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
        for fname, count in sorted(faction_counts.items(), key=lambda x: -x[1])[:8]:
            print(f"    {fname}: {count}")
        
        # 保存
        output_file = OUTPUT_DIR / f"period_{period['year']}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(period_data, f, ensure_ascii=False)
        
        index_data['periods'].append({
            'year': period['year'],
            'name': period['name'],
            'description': period['description'],
        })
    
    with open(OUTPUT_DIR / 'index.json', 'w', encoding='utf-8') as f:
        json.dump(index_data, f, ensure_ascii=False, indent=2)
    
    print("\n" + "=" * 60)
    print(f"完成！")
    print("=" * 60)

if __name__ == "__main__":
    main()
