// 下载中国地级市级别的 GeoJSON 数据
// 包含：地级市 + 直辖市整体

import fs from 'fs';
import path from 'path';

const OUTPUT_DIR = path.join(process.cwd(), 'public', 'geo');
const OUTPUT_FILE = path.join(OUTPUT_DIR, 'china_cities.json');

const API_BASE = 'https://geo.datav.aliyun.com/areas_v3/bound';

// 省级行政区划代码
const PROVINCES = [
  '130000', '140000', '150000',  // 华北：河北、山西、内蒙古
  '210000', '220000', '230000',  // 东北：辽宁、吉林、黑龙江
  '320000', '330000', '340000', '350000', '360000', '370000',  // 华东
  '410000', '420000', '430000',  // 华中：河南、湖北、湖南
  '440000', '450000', '460000',  // 华南：广东、广西、海南
  '510000', '520000', '530000', '540000',  // 西南：四川、贵州、云南、西藏
  '610000', '620000', '630000', '640000', '650000',  // 西北
  '710000',  // 台湾
];

// 直辖市代码
const MUNICIPALITIES = ['110000', '120000', '310000', '500000'];

interface Feature {
  type: 'Feature';
  properties: {
    adcode: number;
    name: string;
    level: string;
    parent?: { adcode: number };
    center?: [number, number];
  };
  geometry: any;
}

async function fetchJson(url: string): Promise<any> {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Failed to fetch ${url}: ${response.status}`);
  }
  return response.json();
}

async function downloadCityData() {
  const allCities: Feature[] = [];
  
  console.log('==================================================');
  console.log('中国地级市 GeoJSON 数据下载工具');
  console.log('==================================================');
  console.log('开始下载数据...\n');
  
  // 1. 下载直辖市（省级边界）
  console.log('下载直辖市...');
  for (const code of MUNICIPALITIES) {
    try {
      const url = `${API_BASE}/${code}.json`;  // 不带 _full
      const data = await fetchJson(url);
      
      if (data.features?.length > 0) {
        const feature = data.features[0];
        // 修改 level 为 city 以保持一致
        feature.properties.level = 'city';
        allCities.push(feature);
        console.log(`  ✓ ${feature.properties.name}`);
      }
      
      await new Promise(resolve => setTimeout(resolve, 100));
    } catch (error) {
      console.log(`  ✗ ${code} 下载失败`);
    }
  }
  
  // 2. 下载省份的地级市
  console.log('\n下载省份地级市...');
  for (const provinceCode of PROVINCES) {
    try {
      const url = `${API_BASE}/${provinceCode}_full.json`;
      const data = await fetchJson(url);
      
      if (data.features) {
        const cities = data.features.filter((f: Feature) => 
          f.properties?.level === 'city'
        );
        if (cities.length > 0) {
          allCities.push(...cities);
          console.log(`  ✓ ${cities[0].properties.name.replace(/市$/, '')}省: ${cities.length}个地级市`);
        }
      }
      
      await new Promise(resolve => setTimeout(resolve, 100));
      
    } catch (error) {
      console.log(`  ✗ ${provinceCode} 下载失败`);
    }
  }

  console.log(`\n总共获取 ${allCities.length} 个地级行政区`);
  
  // 创建输出目录
  if (!fs.existsSync(OUTPUT_DIR)) {
    fs.mkdirSync(OUTPUT_DIR, { recursive: true });
  }
  
  // 保存结果
  const result = {
    type: 'FeatureCollection',
    features: allCities,
  };
  
  fs.writeFileSync(OUTPUT_FILE, JSON.stringify(result));
  
  const stats = fs.statSync(OUTPUT_FILE);
  console.log(`\n保存到: ${OUTPUT_FILE}`);
  console.log(`文件大小: ${(stats.size / 1024 / 1024).toFixed(2)} MB`);
  console.log('\n完成!');
}

downloadCityData().catch(console.error);
