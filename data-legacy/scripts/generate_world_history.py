#!/usr/bin/env python3
"""
生成世界历史时期势力分布数据
基于 world_regions.json，为所有区域分配势力
"""

import json
from pathlib import Path

GEO_DIR = Path("/workspace/projects/public/geo")
HISTORY_DIR = Path("/workspace/projects/public/history")
OUTPUT_DIR = Path("/workspace/projects/public/history-world")

# 势力颜色配置
FACTION_COLORS = {
    'faction-1': {'name': '中国王朝', 'color': '#dc2626', 'outlineColor': '#991b1b'},
    'faction-2': {'name': '游牧民族', 'color': '#1e40af', 'outlineColor': '#1e3a8a'},
    'faction-3': {'name': '西域诸国', 'color': '#15803d', 'outlineColor': '#166534'},
    'faction-4': {'name': '日本', 'color': '#b45309', 'outlineColor': '#92400e'},
    'faction-5': {'name': '朝鲜', 'color': '#7c3aed', 'outlineColor': '#5b21b6'},
    'faction-6': {'name': '东南亚', 'color': '#be185d', 'outlineColor': '#9d174d'},
    'faction-7': {'name': '南亚', 'color': '#0891b2', 'outlineColor': '#0e7490'},
    'faction-8': {'name': '中亚', 'color': '#65a30d', 'outlineColor': '#3f6212'},
    'faction-9': {'name': '西亚', 'color': '#ca8a04', 'outlineColor': '#a16207'},
    'faction-10': {'name': '欧洲', 'color': '#6366f1', 'outlineColor': '#4f46e5'},
    'faction-11': {'name': '非洲', 'color': '#f97316', 'outlineColor': '#ea580c'},
    'faction-12': {'name': '美洲', 'color': '#14b8a6', 'outlineColor': '#0d9488'},
    'faction-13': {'name': '未知', 'color': '#94a3b8', 'outlineColor': '#64748b'},
}

# 各时期势力配置
# 中国内部使用省份代码前缀，其他国家使用 adcode 前缀
PERIODS = [
    {
        'year': 100,
        'name': '东汉时期',
        'description': '东汉王朝鼎盛时期，丝绸之路连接东西方',
        'factions': {
            'faction-1': {
                'name': '东汉',
                'regions': [
                    # 中国主体（不含西域、西藏）
                    *[f"{p}" for p in ['11','12','13','14','21','22','23','31','32','33','34','35','36','37','41','42','43','44','45','50','51','52','53','61','62','64','65','46','71']],
                ]
            },
            'faction-2': {
                'name': '匈奴',
                'regions': ['15']  # 内蒙古
            },
            'faction-3': {
                'name': '西域诸国',
                'regions': ['63', '54']  # 青海、西藏
            },
            'faction-4': {
                'name': '倭国',
                'regions': ['JP']  # 日本
            },
            'faction-5': {
                'name': '三韩',
                'regions': ['KR', 'KP']  # 韩国、朝鲜
            },
            'faction-6': {
                'name': '东南亚诸国',
                'regions': ['AS_VI', 'AS_LA', 'AS_CA', 'AS_TH', 'AS_MY', 'AS_ID', 'AS_PH']
            },
        }
    },
    {
        'year': 220,
        'name': '三国时期',
        'description': '魏蜀吴三国鼎立，英雄辈出',
        'factions': {
            'faction-1': {
                'name': '魏',
                'regions': ['11','12','13','14','15','21','22','23','31','32','34','35','36','37','41','42','44','45','46']
            },
            'faction-2': {
                'name': '蜀汉',
                'regions': ['50','51','52','53','61','62']
            },
            'faction-3': {
                'name': '东吴',
                'regions': ['33','43','71']
            },
            'faction-4': {
                'name': '邪马台国',
                'regions': ['JP']
            },
            'faction-5': {
                'name': '三韩',
                'regions': ['KR', 'KP']
            },
        }
    },
    {
        'year': 400,
        'name': '南北朝',
        'description': '南北对峙，民族融合',
        'factions': {
            'faction-1': {
                'name': '东晋/南朝',
                'regions': ['33','34','35','36','43','44','45','46','71']
            },
            'faction-2': {
                'name': '北魏',
                'regions': ['11','12','13','14','15','21','22','23','31','32','37','41','42','50','51','61','62','64']
            },
            'faction-3': {
                'name': '吐谷浑等',
                'regions': ['52','53','63','65','54']
            },
            'faction-4': {
                'name': '大和朝廷',
                'regions': ['JP']
            },
            'faction-5': {
                'name': '高句丽/百济/新罗',
                'regions': ['KR', 'KP']
            },
        }
    },
    {
        'year': 600,
        'name': '隋朝',
        'description': '隋朝统一天下，开创科举',
        'factions': {
            'faction-1': {
                'name': '隋朝',
                'regions': [p for p in ['11','12','13','14','15','21','22','23','31','32','33','34','35','36','37','41','42','43','44','45','46','50','51','52','53','61','62','63','64','65','71']]
            },
            'faction-2': {
                'name': '吐蕃',
                'regions': ['54']
            },
            'faction-4': {
                'name': '飞鸟时代日本',
                'regions': ['JP']
            },
            'faction-5': {
                'name': '朝鲜三国',
                'regions': ['KR', 'KP']
            },
        }
    },
    {
        'year': 750,
        'name': '唐朝鼎盛',
        'description': '唐朝疆域辽阔，万国来朝',
        'factions': {
            'faction-1': {
                'name': '唐朝',
                'regions': [p for p in ['11','12','13','14','15','21','22','23','31','32','33','34','35','36','37','41','42','43','44','45','46','50','51','52','53','61','62','63','64','65','71']]
            },
            'faction-2': {
                'name': '吐蕃',
                'regions': ['54']
            },
            'faction-4': {
                'name': '奈良时代日本',
                'regions': ['JP']
            },
            'faction-5': {
                'name': '统一新罗',
                'regions': ['KR', 'KP']
            },
            'faction-6': {
                'name': '东南亚诸国',
                'regions': ['AS_VI', 'AS_LA', 'AS_CA', 'AS_TH', 'AS_MY', 'AS_ID', 'AS_PH']
            },
        }
    },
    {
        'year': 900,
        'name': '唐末五代',
        'description': '藩镇割据，五代十国',
        'factions': {
            'faction-1': {
                'name': '后梁',
                'regions': ['11','12','13','14','37','41']
            },
            'faction-2': {
                'name': '前蜀',
                'regions': ['50','51','52','53']
            },
            'faction-3': {
                'name': '吴越',
                'regions': ['31','32','33','34','35']
            },
            'faction-4': {
                'name': '南汉',
                'regions': ['43','44','45','46','71']
            },
            'faction-5': {
                'name': '契丹',
                'regions': ['15','21','22','23']
            },
            'faction-6': {
                'name': '其他藩镇',
                'regions': ['36','42','61','62','63','64','65']
            },
            'faction-7': {
                'name': '平安时代日本',
                'regions': ['JP']
            },
            'faction-8': {
                'name': '后三国',
                'regions': ['KR', 'KP']
            },
        }
    },
    {
        'year': 1100,
        'name': '北宋',
        'description': '北宋与辽、西夏并立',
        'factions': {
            'faction-1': {
                'name': '北宋',
                'regions': [p for p in ['11','12','13','14','31','32','33','34','35','36','37','41','42','43','44','45','46','50','51','52','53','61','62','71']]
            },
            'faction-2': {
                'name': '辽',
                'regions': ['15','21','22','23']
            },
            'faction-3': {
                'name': '西夏',
                'regions': ['63','64','65']
            },
            'faction-4': {
                'name': '平安时代日本',
                'regions': ['JP']
            },
            'faction-5': {
                'name': '高丽',
                'regions': ['KR', 'KP']
            },
            'faction-6': {
                'name': '东南亚诸国',
                'regions': ['AS_VI', 'AS_LA', 'AS_CA', 'AS_TH', 'AS_MY', 'AS_ID', 'AS_PH']
            },
        }
    },
    {
        'year': 1200,
        'name': '南宋',
        'description': '南宋与金、西夏对峙',
        'factions': {
            'faction-1': {
                'name': '南宋',
                'regions': ['31','32','33','34','35','36','43','44','45','46','50','51','52','53','71']
            },
            'faction-2': {
                'name': '金',
                'regions': ['11','12','13','14','15','21','22','23','37','41','42','61','62']
            },
            'faction-3': {
                'name': '西夏',
                'regions': ['63','64','65']
            },
            'faction-4': {
                'name': '幕府时代日本',
                'regions': ['JP']
            },
            'faction-5': {
                'name': '高丽',
                'regions': ['KR', 'KP']
            },
            'faction-6': {
                'name': '大理国',
                'regions': ['54']
            },
        }
    },
    {
        'year': 1300,
        'name': '元朝',
        'description': '蒙古帝国统一欧亚大陆',
        'factions': {
            'faction-1': {
                'name': '元朝',
                'regions': ['JP'] + [p for p in ['11','12','13','14','15','21','22','23','31','32','33','34','35','36','37','41','42','43','44','45','46','50','51','52','53','54','61','62','63','64','65','71']] + ['KR', 'KP']
            },
            'faction-2': {
                'name': '东南亚',
                'regions': ['AS_VI', 'AS_LA', 'AS_CA', 'AS_TH', 'AS_MY', 'AS_ID', 'AS_PH']
            },
        }
    },
    {
        'year': 1500,
        'name': '明朝',
        'description': '明朝国力强盛，郑和下西洋',
        'factions': {
            'faction-1': {
                'name': '明朝',
                'regions': [p for p in ['11','12','13','14','15','21','22','23','31','32','33','34','35','36','37','41','42','43','44','45','46','50','51','52','53','61','62','63','64','65','71']]
            },
            'faction-2': {
                'name': '鞑靼/瓦剌',
                'regions': ['54']
            },
            'faction-4': {
                'name': '战国时代日本',
                'regions': ['JP']
            },
            'faction-5': {
                'name': '朝鲜',
                'regions': ['KR', 'KP']
            },
            'faction-6': {
                'name': '东南亚诸国',
                'regions': ['AS_VI', 'AS_LA', 'AS_CA', 'AS_TH', 'AS_MY', 'AS_ID', 'AS_PH']
            },
        }
    },
    {
        'year': 1750,
        'name': '清朝鼎盛',
        'description': '清朝疆域达到极盛',
        'factions': {
            'faction-1': {
                'name': '清朝',
                'regions': [p for p in ['11','12','13','14','15','21','22','23','31','32','33','34','35','36','37','41','42','43','44','45','46','50','51','52','53','54','61','62','63','64','65','71']]
            },
            'faction-4': {
                'name': '江户时代日本',
                'regions': ['JP']
            },
            'faction-5': {
                'name': '朝鲜',
                'regions': ['KR', 'KP']
            },
            'faction-6': {
                'name': '东南亚诸国',
                'regions': ['AS_VI', 'AS_LA', 'AS_CA', 'AS_TH', 'AS_MY', 'AS_ID', 'AS_PH']
            },
        }
    },
    {
        'year': 1850,
        'name': '清末',
        'description': '清朝衰落，太平天国运动',
        'factions': {
            'faction-1': {
                'name': '清朝',
                'regions': [p for p in ['11','12','13','14','15','21','22','23','31','32','33','34','35','36','37','41','42','45','46','50','51','52','53','54','61','62','63','64','65','71']]
            },
            'faction-2': {
                'name': '太平天国',
                'regions': ['43', '44']  # 湖南、广东
            },
            'faction-4': {
                'name': '幕末日本',
                'regions': ['JP']
            },
            'faction-5': {
                'name': '朝鲜',
                'regions': ['KR', 'KP']
            },
        }
    },
    {
        'year': 1912,
        'name': '民国初年',
        'description': '中华民国成立',
        'factions': {
            'faction-1': {
                'name': '中华民国',
                'regions': [p for p in ['11','12','13','14','21','22','23','31','32','33','34','35','36','37','41','42','43','44','45','46','50','51','52','53','61','62','63','64','65','71']]
            },
            'faction-2': {
                'name': '西藏',
                'regions': ['54']
            },
            'faction-3': {
                'name': '外蒙古',
                'regions': ['15']
            },
            'faction-4': {
                'name': '大正时代日本',
                'regions': ['JP']
            },
            'faction-5': {
                'name': '朝鲜（日占）',
                'regions': ['KR', 'KP']
            },
        }
    },
]

def load_regions():
    """加载世界区域数据"""
    with open(GEO_DIR / 'world_regions.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def match_region(adcode: str, region_pattern: str) -> bool:
    """检查 adcode 是否匹配区域模式"""
    if adcode.startswith(region_pattern):
        return True
    # 中国省份代码匹配
    if len(adcode) == 6 and adcode.isdigit():
        if adcode[:2] == region_pattern:
            return True
    return False

def generate_period_data(regions_data: dict, period: dict) -> dict:
    """生成单个时期的数据"""
    city_to_faction = {}
    
    # 为每个区域分配势力
    for feature in regions_data['features']:
        adcode = feature['properties']['adcode']
        country = feature['properties'].get('country', '')
        
        assigned = False
        
        # 检查每个势力的区域匹配
        for faction_id, faction_data in period['factions'].items():
            for region_pattern in faction_data['regions']:
                if match_region(adcode, region_pattern):
                    city_to_faction[adcode] = faction_id
                    assigned = True
                    break
            if assigned:
                break
        
        # 未分配的区域根据国家分配默认势力
        if not assigned:
            # 根据国家/地区分配
            if country == '日本':
                city_to_faction[adcode] = 'faction-4'
            elif country in ['韩国', '朝鲜']:
                city_to_faction[adcode] = 'faction-5'
            elif country in ['越南', '老挝', '柬埔寨', '泰国', '缅甸', '马来西亚', '印度尼西亚', '菲律宾', '新加坡', '文莱', '东帝汶']:
                city_to_faction[adcode] = 'faction-6'
            elif country in ['印度', '巴基斯坦', '孟加拉国', '尼泊尔', '不丹', '斯里兰卡']:
                city_to_faction[adcode] = 'faction-7'
            elif country in ['哈萨克斯坦', '乌兹别克斯坦', '土库曼斯坦', '吉尔吉斯斯坦', '塔吉克斯坦']:
                city_to_faction[adcode] = 'faction-8'
            elif country in ['伊朗', '伊拉克', '叙利亚', '土耳其', '沙特阿拉伯', '阿联酋', '以色列', '约旦', '黎巴嫩']:
                city_to_faction[adcode] = 'faction-9'
            else:
                city_to_faction[adcode] = 'faction-13'  # 未知
    
    # 构建势力信息
    factions = {}
    for faction_id, faction_data in period['factions'].items():
        factions[faction_id] = {
            'name': faction_data['name'],
            'color': FACTION_COLORS.get(faction_id, FACTION_COLORS['faction-13'])['color'],
            'outlineColor': FACTION_COLORS.get(faction_id, FACTION_COLORS['faction-13'])['outlineColor'],
        }
    
    return {
        'year': period['year'],
        'name': period['name'],
        'description': period['description'],
        'factions': factions,
        'cityToFaction': city_to_faction,
    }

def main():
    print("=" * 50)
    print("生成世界历史时期数据")
    print("=" * 50)
    
    # 加载区域数据
    regions_data = load_regions()
    print(f"加载 {len(regions_data['features'])} 个区域")
    
    # 创建输出目录
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # 生成每个时期的数据
    index_data = {'periods': []}
    
    for period in PERIODS:
        print(f"处理 {period['year']} 年 - {period['name']}...")
        
        period_data = generate_period_data(regions_data, period)
        
        # 保存时期数据
        output_file = OUTPUT_DIR / f"period_{period['year']}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(period_data, f, ensure_ascii=False, indent=2)
        
        index_data['periods'].append({
            'year': period['year'],
            'name': period['name'],
            'description': period['description'],
        })
    
    # 保存索引
    with open(OUTPUT_DIR / 'index.json', 'w', encoding='utf-8') as f:
        json.dump(index_data, f, ensure_ascii=False, indent=2)
    
    print("\n" + "=" * 50)
    print(f"完成！共生成 {len(PERIODS)} 个时期")
    print(f"输出目录: {OUTPUT_DIR}")
    print("=" * 50)

if __name__ == "__main__":
    main()
