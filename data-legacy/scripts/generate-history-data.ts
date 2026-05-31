// 历史时期势力分布数据生成脚本
// 使用地级市级别（adcode 前4位）划分势力

import fs from 'fs';
import path from 'path';

// 势力颜色配置
const FACTION_COLORS: Record<string, { fill: string; outline: string }> = {
  'faction-1': { fill: '#dc2626', outline: '#991b1b' },
  'faction-2': { fill: '#1e40af', outline: '#1e3a8a' },
  'faction-3': { fill: '#15803d', outline: '#166534' },
  'faction-4': { fill: '#b45309', outline: '#92400e' },
  'faction-5': { fill: '#7c3aed', outline: '#5b21b6' },
  'faction-6': { fill: '#be185d', outline: '#9d174d' },
  'faction-7': { fill: '#0891b2', outline: '#0e7490' },
  'faction-8': { fill: '#65a30d', outline: '#3f6212' },
};

// 省份代码映射（adcode前2位）
const PROVINCE_MAP: Record<string, string> = {
  '11': '北京', '12': '天津', '13': '河北', '14': '山西', '15': '内蒙古',
  '21': '辽宁', '22': '吉林', '23': '黑龙江',
  '31': '上海', '32': '江苏', '33': '浙江', '34': '安徽', '35': '福建',
  '36': '江西', '37': '山东',
  '41': '河南', '42': '湖北', '43': '湖南', '44': '广东', '45': '广西', '46': '海南',
  '50': '重庆', '51': '四川', '52': '贵州', '53': '云南', '54': '西藏',
  '61': '陕西', '62': '甘肃', '63': '青海', '64': '宁夏', '65': '新疆',
  '71': '台湾',
};

// 历史时期配置：使用省份代码（adcode前2位）划分势力
// 之后会转换为地级市代码（adcode前4位）
const PERIODS = [
  {
    year: 100,
    name: '东汉',
    description: '东汉王朝鼎盛时期',
    factions: [
      { id: 'faction-1', name: '东汉', provinces: ['11','12','13','14','21','22','23','31','32','33','34','35','36','37','41','42','43','44','45','50','51','52','53','61','62','64','65'] },
      { id: 'faction-2', name: '匈奴', provinces: ['15'] },
      { id: 'faction-3', name: '西域', provinces: ['63', '54'] },
    ],
  },
  {
    year: 220,
    name: '三国',
    description: '魏蜀吴三国鼎立',
    factions: [
      { id: 'faction-1', name: '魏', provinces: ['11','12','13','14','15','21','22','23','31','32','34','35','36','37','41','42','44','45','46'] },
      { id: 'faction-2', name: '蜀', provinces: ['50','51','52','53','61','62'] },
      { id: 'faction-3', name: '吴', provinces: ['33','43','71'] },
    ],
  },
  {
    year: 400,
    name: '东晋十六国',
    description: '南北对峙时期',
    factions: [
      { id: 'faction-1', name: '东晋', provinces: ['33','34','35','36','43','44','45','46','71'] },
      { id: 'faction-2', name: '北魏', provinces: ['11','12','13','14','15','21','22','23','31','32','37','41','42','50','51','61','62','64'] },
      { id: 'faction-3', name: '前秦', provinces: ['52','53','63','65'] },
    ],
  },
  {
    year: 600,
    name: '隋朝',
    description: '隋朝统一天下',
    factions: [
      { id: 'faction-1', name: '隋', provinces: ['11','12','13','14','15','21','22','23','31','32','33','34','35','36','37','41','42','43','44','45','46','50','51','52','53','61','62','63','64','65','71'] },
      { id: 'faction-2', name: '吐谷浑', provinces: ['54'] },
    ],
  },
  {
    year: 750,
    name: '唐朝鼎盛',
    description: '唐朝疆域辽阔，万国来朝',
    factions: [
      { id: 'faction-1', name: '唐朝', provinces: ['11','12','13','14','15','21','22','23','31','32','33','34','35','36','37','41','42','43','44','45','46','50','51','52','53','61','62','63','64','65','71'] },
      { id: 'faction-2', name: '吐蕃', provinces: ['54'] },
    ],
  },
  {
    year: 900,
    name: '唐末五代',
    description: '藩镇割据，五代十国',
    factions: [
      { id: 'faction-1', name: '后梁', provinces: ['11','12','13','14','37','41'] },
      { id: 'faction-2', name: '前蜀', provinces: ['50','51','52','53'] },
      { id: 'faction-3', name: '吴越', provinces: ['31','32','33','34','35'] },
      { id: 'faction-4', name: '南汉', provinces: ['43','44','45','46','71'] },
      { id: 'faction-5', name: '契丹', provinces: ['15','21','22','23'] },
      { id: 'faction-6', name: '其他藩镇', provinces: ['36','42','61','62','63','64','65'] },
    ],
  },
  {
    year: 1100,
    name: '北宋',
    description: '北宋与辽、西夏并立',
    factions: [
      { id: 'faction-1', name: '北宋', provinces: ['11','12','13','14','31','32','33','34','35','36','37','41','42','43','44','45','46','50','51','52','53','61','62','71'] },
      { id: 'faction-2', name: '辽', provinces: ['15','21','22','23'] },
      { id: 'faction-3', name: '西夏', provinces: ['63','64','65'] },
    ],
  },
  {
    year: 1200,
    name: '南宋金朝',
    description: '南宋、金、西夏三国鼎立',
    factions: [
      { id: 'faction-1', name: '南宋', provinces: ['31','32','33','34','35','36','43','44','45','46','52','53','71'] },
      { id: 'faction-2', name: '金', provinces: ['11','12','13','14','15','21','22','23','37','41','42','50','51','61','62'] },
      { id: 'faction-3', name: '西夏', provinces: ['63','64','65'] },
      { id: 'faction-4', name: '大理', provinces: ['54'] },
    ],
  },
  {
    year: 1300,
    name: '元朝',
    description: '蒙古帝国统一天下',
    factions: [
      { id: 'faction-1', name: '元朝', provinces: ['11','12','13','14','15','21','22','23','31','32','33','34','35','36','37','41','42','43','44','45','46','50','51','52','53','54','61','62','63','64','65','71'] },
    ],
  },
  {
    year: 1500,
    name: '明朝鼎盛',
    description: '明朝疆域广阔',
    factions: [
      { id: 'faction-1', name: '明朝', provinces: ['11','12','13','14','15','21','22','23','31','32','33','34','35','36','37','41','42','43','44','45','46','50','51','52','53','61','62','63','64','65','71'] },
      { id: 'faction-2', name: '鞑靼', provinces: ['54'] },
    ],
  },
  {
    year: 1750,
    name: '清朝鼎盛',
    description: '康乾盛世，版图最大',
    factions: [
      { id: 'faction-1', name: '清朝', provinces: ['11','12','13','14','15','21','22','23','31','32','33','34','35','36','37','41','42','43','44','45','46','50','51','52','53','54','61','62','63','64','65','71'] },
    ],
  },
  {
    year: 1850,
    name: '清末',
    description: '太平天国运动',
    factions: [
      { id: 'faction-1', name: '清朝', provinces: ['11','12','13','14','15','21','22','23','31','32','33','34','35','36','37','41','42','44','45','46','50','51','52','53','54','61','62','63','64','65','71'] },
      { id: 'faction-2', name: '太平天国', provinces: ['43'] },
    ],
  },
  {
    year: 1912,
    name: '民国',
    description: '中华民国成立',
    factions: [
      { id: 'faction-1', name: '中华民国', provinces: ['11','12','13','14','15','21','22','23','31','32','33','34','35','36','37','41','42','43','44','45','46','50','51','52','53','61','62','63','64','65','71'] },
      { id: 'faction-2', name: '西藏', provinces: ['54'] },
    ],
  },
];

// 从 GeoJSON 中提取所有地级市的 adcode 前4位
async function getCityCodes(): Promise<string[]> {
  const geojsonPath = path.join(process.cwd(), 'public', 'geo', 'china_cities.json');
  const geojson = JSON.parse(fs.readFileSync(geojsonPath, 'utf-8'));
  
  const cityCodes: string[] = [];
  for (const feature of geojson.features) {
    const adcode = String(feature.properties.adcode);
    cityCodes.push(adcode);
  }
  
  return cityCodes;
}

// 根据省份代码获取该省所有地级市代码
function getCityCodesByProvince(allCities: string[], provinceCode: string): string[] {
  // 台湾特殊处理：省份代码 71 对应所有 71xxxx 的县市
  if (provinceCode === '71') {
    return allCities.filter(city => city.startsWith('71'));
  }
  return allCities.filter(city => city.startsWith(provinceCode));
}

// 生成时期数据
function generatePeriodData(period: typeof PERIODS[0], allCities: string[]) {
  const factions: Record<string, { name: string; color: string; outlineColor: string }> = {};
  const cityToFaction: Record<string, string> = {};
  
  for (const faction of period.factions) {
    factions[faction.id] = {
      name: faction.name,
      color: FACTION_COLORS[faction.id].fill,
      outlineColor: FACTION_COLORS[faction.id].outline,
    };
    
    // 获取该省份下所有地级市
    for (const province of faction.provinces) {
      const cityCodes = getCityCodesByProvince(allCities, province);
      for (const cityCode of cityCodes) {
        cityToFaction[cityCode] = faction.id;
      }
    }
  }
  
  return {
    year: period.year,
    name: period.name,
    description: period.description,
    factions,
    cityToFaction,  // 地级市 -> 势力 映射
  };
}

async function main() {
  const outputDir = path.join(process.cwd(), 'public', 'history');
  
  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
  }
  
  // 获取所有地级市代码
  const allCities = await getCityCodes();
  console.log(`加载 ${allCities.length} 个地级市`);
  
  // 生成所有时期数据
  const allPeriods: any[] = [];
  
  for (const period of PERIODS) {
    const data = generatePeriodData(period, allCities);
    allPeriods.push({
      year: data.year,
      name: data.name,
      description: data.description,
    });
    
    const filename = `period_${period.year}.json`;
    fs.writeFileSync(
      path.join(outputDir, filename),
      JSON.stringify(data, null, 2)
    );
    console.log(`生成: ${filename} (${Object.keys(data.cityToFaction).length} 个地级市)`);
  }
  
  // 保存时期索引
  fs.writeFileSync(
    path.join(outputDir, 'index.json'),
    JSON.stringify({ periods: allPeriods }, null, 2)
  );
  console.log('生成: index.json');
}

main();
