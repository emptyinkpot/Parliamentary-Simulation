// 历史时期势力分布数据
// 根据谭其骧《中国历史地图集》及历史资料整理
// 省份代码(adcode前2位)划分控制范围

export interface HistoricalPeriod {
  year: number;
  name: string;
  description: string;
  factions: {
    id: string;
    name: string;
    color: string;
    outlineColor: string;
    provinces: string[]; // 省份adcode前2位
  }[];
}

// 中国省份adcode前2位映射
// 11-15: 北京、天津、河北、山西、内蒙古
// 21-23: 辽宁、吉林、黑龙江
// 31-37: 上海、江苏、浙江、安徽、福建、江西、山东
// 41-46: 河南、湖北、湖南、广东、广西、海南
// 50-54: 重庆、四川、贵州、云南、西藏
// 61-65: 陕西、甘肃、青海、宁夏、新疆
// 71: 台湾

export const HISTORICAL_PERIODS: HistoricalPeriod[] = [
  {
    year: 100,
    name: '东汉',
    description: '东汉王朝鼎盛时期，疆域东至大海，西至葱岭，南至交趾，北至大漠',
    factions: [
      {
        id: 'faction-1',
        name: '东汉',
        color: '#dc2626',
        outlineColor: '#991b1b',
        // 东汉控制：中原十八省 + 东北部分地区 + 西域都护府
        provinces: ['11', '12', '13', '14', '21', '22', '23', '31', '32', '33', '34', '35', '36', '37', '41', '42', '43', '44', '45', '46', '50', '51', '52', '53', '61', '62', '64', '65'],
      },
      {
        id: 'faction-2',
        name: '匈奴',
        color: '#1e40af',
        outlineColor: '#1e3a8a',
        // 匈奴控制：蒙古高原
        provinces: ['15'],
      },
      {
        id: 'faction-3',
        name: '羌族',
        color: '#65a30d',
        outlineColor: '#3f6212',
        // 羌族控制：青海、甘肃西部
        provinces: ['63'],
      },
      {
        id: 'faction-4',
        name: '西南夷',
        color: '#be185d',
        outlineColor: '#9d174d',
        // 西南夷：西藏、云南西部
        provinces: ['54'],
      },
    ],
  },
  {
    year: 200,
    name: '三国鼎立',
    description: '曹魏、蜀汉、东吴三国鼎立，天下三分',
    factions: [
      {
        id: 'faction-1',
        name: '曹魏',
        color: '#dc2626',
        outlineColor: '#991b1b',
        // 曹魏控制：北方中原地区（幽、冀、并、青、徐、兖、豫、司、雍、凉等州）
        provinces: ['11', '12', '13', '14', '15', '21', '22', '23', '31', '32', '33', '34', '35', '36', '37', '41', '42', '61', '62', '63', '64', '65'],
      },
      {
        id: 'faction-2',
        name: '蜀汉',
        color: '#15803d',
        outlineColor: '#166534',
        // 蜀汉控制：益州（四川、重庆、贵州、云南）
        provinces: ['50', '51', '52', '53'],
      },
      {
        id: 'faction-3',
        name: '东吴',
        color: '#1e40af',
        outlineColor: '#1e3a8a',
        // 东吴控制：江东六郡 + 荆州 + 交州
        provinces: ['31', '32', '33', '34', '35', '36', '37', '41', '42', '43', '44', '45', '46'],
      },
      {
        id: 'faction-4',
        name: '鲜卑',
        color: '#b45309',
        outlineColor: '#92400e',
        // 鲜卑控制：内蒙古、东北北部
        provinces: ['15', '21', '22', '23'],
      },
    ],
  },
  {
    year: 400,
    name: '东晋十六国',
    description: '五胡乱华，南北分裂，政权更迭频繁',
    factions: [
      {
        id: 'faction-1',
        name: '东晋',
        color: '#dc2626',
        outlineColor: '#991b1b',
        // 东晋控制：江南、荆湘、巴蜀
        provinces: ['31', '32', '33', '34', '35', '36', '37', '41', '42', '43', '44', '45', '46', '50', '51', '52', '53'],
      },
      {
        id: 'faction-2',
        name: '前秦',
        color: '#1e40af',
        outlineColor: '#1e3a8a',
        // 前秦控制：关中、河西
        provinces: ['61', '62', '63', '64', '65'],
      },
      {
        id: 'faction-3',
        name: '鲜卑诸部',
        color: '#0891b2',
        outlineColor: '#0e7490',
        // 鲜卑控制：河北、山西、东北
        provinces: ['11', '12', '13', '14', '15', '21', '22', '23'],
      },
    ],
  },
  {
    year: 600,
    name: '隋朝',
    description: '隋朝统一天下，结束了南北朝分裂局面',
    factions: [
      {
        id: 'faction-1',
        name: '隋朝',
        color: '#dc2626',
        outlineColor: '#991b1b',
        // 隋朝控制：全国大部分地区
        provinces: ['11', '12', '13', '14', '15', '21', '22', '23', '31', '32', '33', '34', '35', '36', '37', '41', '42', '43', '44', '45', '46', '50', '51', '52', '53', '61', '62', '63', '64', '65'],
      },
      {
        id: 'faction-2',
        name: '突厥',
        color: '#1e40af',
        outlineColor: '#1e3a8a',
        // 突厥控制：蒙古高原
        provinces: ['15'],
      },
      {
        id: 'faction-3',
        name: '吐谷浑',
        color: '#b45309',
        outlineColor: '#92400e',
        // 吐谷浑控制：青海地区
        provinces: ['63'],
      },
    ],
  },
  {
    year: 750,
    name: '唐朝鼎盛',
    description: '开元盛世，大唐帝国疆域空前辽阔',
    factions: [
      {
        id: 'faction-1',
        name: '唐朝',
        color: '#dc2626',
        outlineColor: '#991b1b',
        // 唐朝直接控制：中原十八省 + 西域 + 东北
        provinces: ['11', '12', '13', '14', '15', '21', '22', '23', '31', '32', '33', '34', '35', '36', '37', '41', '42', '43', '44', '45', '46', '50', '51', '52', '53', '61', '62', '63', '64', '65'],
      },
      {
        id: 'faction-2',
        name: '吐蕃',
        color: '#1e40af',
        outlineColor: '#1e3a8a',
        // 吐蕃控制：青藏高原
        provinces: ['54'],
      },
      {
        id: 'faction-3',
        name: '突厥',
        color: '#b45309',
        outlineColor: '#92400e',
        // 后突厥：蒙古高原
        provinces: ['15'],
      },
      {
        id: 'faction-4',
        name: '南诏',
        color: '#7c3aed',
        outlineColor: '#5b21b6',
        // 南诏：云南
        provinces: ['53'],
      },
      {
        id: 'faction-5',
        name: '渤海国',
        color: '#0891b2',
        outlineColor: '#0e7490',
        // 渤海国：东北东部
        provinces: ['21', '22', '23'],
      },
    ],
  },
  {
    year: 1000,
    name: '北宋',
    description: '北宋与辽国对峙，西夏崛起',
    factions: [
      {
        id: 'faction-1',
        name: '北宋',
        color: '#dc2626',
        outlineColor: '#991b1b',
        // 北宋控制：中原地区（不包括燕云十六州）
        provinces: ['31', '32', '33', '34', '35', '36', '37', '41', '42', '43', '44', '45', '46', '50', '51', '52', '53', '61', '62'],
      },
      {
        id: 'faction-2',
        name: '辽国',
        color: '#1e40af',
        outlineColor: '#1e3a8a',
        // 辽国控制：燕云十六州 + 东北 + 内蒙古
        provinces: ['11', '12', '13', '14', '15', '21', '22', '23'],
      },
      {
        id: 'faction-3',
        name: '西夏',
        color: '#b45309',
        outlineColor: '#92400e',
        // 西夏控制：宁夏、甘肃、青海部分地区
        provinces: ['63', '64', '62'],
      },
      {
        id: 'faction-4',
        name: '大理',
        color: '#7c3aed',
        outlineColor: '#5b21b6',
        // 大理国：云南
        provinces: ['53'],
      },
      {
        id: 'faction-5',
        name: '吐蕃',
        color: '#be185d',
        outlineColor: '#9d174d',
        // 吐蕃诸部：西藏
        provinces: ['54'],
      },
      {
        id: 'faction-6',
        name: '回鹘',
        color: '#65a30d',
        outlineColor: '#3f6212',
        // 回鹘：新疆
        provinces: ['65'],
      },
    ],
  },
  {
    year: 1200,
    name: '南宋',
    description: '宋金对峙，蒙古崛起',
    factions: [
      {
        id: 'faction-1',
        name: '南宋',
        color: '#dc2626',
        outlineColor: '#991b1b',
        // 南宋控制：江南、荆湘、巴蜀
        provinces: ['31', '32', '33', '34', '35', '36', '37', '41', '42', '43', '44', '45', '46', '50', '51', '52', '53'],
      },
      {
        id: 'faction-2',
        name: '金国',
        color: '#1e40af',
        outlineColor: '#1e3a8a',
        // 金国控制：北方中原 + 东北
        provinces: ['11', '12', '13', '14', '15', '21', '22', '23', '31', '32', '41', '61', '62'],
      },
      {
        id: 'faction-3',
        name: '西夏',
        color: '#b45309',
        outlineColor: '#92400e',
        // 西夏控制：宁夏、甘肃
        provinces: ['63', '64'],
      },
      {
        id: 'faction-4',
        name: '蒙古',
        color: '#0891b2',
        outlineColor: '#0e7490',
        // 蒙古控制：内蒙古、新疆
        provinces: ['15', '65'],
      },
      {
        id: 'faction-5',
        name: '大理',
        color: '#7c3aed',
        outlineColor: '#5b21b6',
        provinces: ['53'],
      },
      {
        id: 'faction-6',
        name: '吐蕃',
        color: '#be185d',
        outlineColor: '#9d174d',
        provinces: ['54'],
      },
    ],
  },
  {
    year: 1300,
    name: '元朝',
    description: '蒙古帝国统一天下，建立横跨欧亚的大帝国',
    factions: [
      {
        id: 'faction-1',
        name: '元朝',
        color: '#dc2626',
        outlineColor: '#991b1b',
        // 元朝控制：全国
        provinces: ['11', '12', '13', '14', '15', '21', '22', '23', '31', '32', '33', '34', '35', '36', '37', '41', '42', '43', '44', '45', '46', '50', '51', '52', '53', '54', '61', '62', '63', '64', '65'],
      },
      {
        id: 'faction-2',
        name: '察合台汗国',
        color: '#1e40af',
        outlineColor: '#1e3a8a',
        // 察合台汗国：新疆西部
        provinces: ['65'],
      },
    ],
  },
  {
    year: 1450,
    name: '明朝',
    description: '大明王朝，驱逐蒙元，恢复汉家天下',
    factions: [
      {
        id: 'faction-1',
        name: '明朝',
        color: '#dc2626',
        outlineColor: '#991b1b',
        // 明朝控制：两京十三省 + 东北部分
        provinces: ['11', '12', '13', '14', '21', '22', '23', '31', '32', '33', '34', '35', '36', '37', '41', '42', '43', '44', '45', '46', '50', '51', '52', '53', '61', '62', '63', '64'],
      },
      {
        id: 'faction-2',
        name: '北元/瓦剌',
        color: '#1e40af',
        outlineColor: '#1e3a8a',
        // 北元控制：内蒙古、新疆
        provinces: ['15', '65'],
      },
      {
        id: 'faction-3',
        name: '吐蕃',
        color: '#be185d',
        outlineColor: '#9d174d',
        // 乌思藏都司（羁縻）：西藏
        provinces: ['54'],
      },
    ],
  },
  {
    year: 1600,
    name: '明末',
    description: '明朝末年，后金崛起于东北',
    factions: [
      {
        id: 'faction-1',
        name: '明朝',
        color: '#dc2626',
        outlineColor: '#991b1b',
        // 明朝控制：两京十三省
        provinces: ['11', '12', '13', '14', '31', '32', '33', '34', '35', '36', '37', '41', '42', '43', '44', '45', '46', '50', '51', '52', '53', '61', '62', '63', '64'],
      },
      {
        id: 'faction-2',
        name: '后金',
        color: '#1e40af',
        outlineColor: '#1e3a8a',
        // 后金控制：东北
        provinces: ['21', '22', '23'],
      },
      {
        id: 'faction-3',
        name: '蒙古诸部',
        color: '#b45309',
        outlineColor: '#92400e',
        // 蒙古控制：内蒙古、新疆
        provinces: ['15', '65'],
      },
      {
        id: 'faction-4',
        name: '吐蕃',
        color: '#be185d',
        outlineColor: '#9d174d',
        provinces: ['54'],
      },
    ],
  },
  {
    year: 1750,
    name: '清朝鼎盛',
    description: '康乾盛世，大清帝国疆域达到极盛',
    factions: [
      {
        id: 'faction-1',
        name: '清朝',
        color: '#dc2626',
        outlineColor: '#991b1b',
        // 清朝控制：内地十八省 + 东北 + 内蒙古 + 新疆 + 西藏
        provinces: ['11', '12', '13', '14', '15', '21', '22', '23', '31', '32', '33', '34', '35', '36', '37', '41', '42', '43', '44', '45', '46', '50', '51', '52', '53', '54', '61', '62', '63', '64', '65', '71'],
      },
    ],
  },
  {
    year: 1850,
    name: '清末',
    description: '清朝末年，太平天国运动席卷南方',
    factions: [
      {
        id: 'faction-1',
        name: '清朝',
        color: '#dc2626',
        outlineColor: '#991b1b',
        // 清朝控制：北方各省
        provinces: ['11', '12', '13', '14', '15', '21', '22', '23', '31', '32', '33', '34', '35', '36', '37', '41', '42', '50', '51', '52', '53', '54', '61', '62', '63', '64', '65'],
      },
      {
        id: 'faction-2',
        name: '太平天国',
        color: '#b45309',
        outlineColor: '#92400e',
        // 太平天国控制：江南、江西、湖北、安徽等
        provinces: ['31', '32', '33', '34', '35', '36', '37', '41', '42', '43', '44', '45', '46'],
      },
    ],
  },
  {
    year: 1912,
    name: '民国',
    description: '中华民国成立，结束两千年帝制',
    factions: [
      {
        id: 'faction-1',
        name: '中华民国',
        color: '#dc2626',
        outlineColor: '#991b1b',
        // 民国控制：内地十八省
        provinces: ['11', '12', '13', '14', '15', '21', '22', '23', '31', '32', '33', '34', '35', '36', '37', '41', '42', '43', '44', '45', '46', '50', '51', '52', '53', '61', '62', '63', '64', '65'],
      },
      {
        id: 'faction-2',
        name: '西藏',
        color: '#be185d',
        outlineColor: '#9d174d',
        provinces: ['54'],
      },
      {
        id: 'faction-3',
        name: '外蒙古',
        color: '#1e40af',
        outlineColor: '#1e3a8a',
        provinces: ['15'],
      },
    ],
  },
];

// 根据年份找到最接近的历史时期
export function findClosestPeriod(year: number): HistoricalPeriod {
  let closest = HISTORICAL_PERIODS[0];
  let minDiff = Math.abs(year - closest.year);

  for (const period of HISTORICAL_PERIODS) {
    const diff = Math.abs(year - period.year);
    if (diff < minDiff) {
      minDiff = diff;
      closest = period;
    }
  }

  return closest;
}

// 获取某个adcode对应的历史势力
export function getFactionByAdcode(period: HistoricalPeriod, adcode: string | number): string | null {
  // 确保 adcode 是字符串
  const adcodeStr = String(adcode);
  const provinceCode = adcodeStr.substring(0, 2);
  
  for (const faction of period.factions) {
    if (faction.provinces.includes(provinceCode)) {
      return faction.id;
    }
  }
  
  return null;
}
