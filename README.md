# Imperial Strategy Game

P社风格全球大战略游戏，基于 Unity 引擎开发。Steam PC + 联机。

## 项目状态

当前处于 **资源整合阶段**，已完成：
- 全球 4913 个省级行政区 GeoJSON → P社格式省份位图转换
- 13 个历史时期数据（公元100年-1912年）提取整理
- 游戏设计规格文档（20个系统模块）

## 目录结构

```
├── data-legacy/           # 从旧项目提取的可复用数据
│   ├── geo/               # 19 个 GeoJSON 地理边界文件
│   ├── history*/          # 历史朝代势力分布数据
│   ├── scripts/           # 数据生成/处理脚本
│   └── game-design/       # 游戏设计规格文档
├── map-output/            # P社格式地图文件（已生成）
│   ├── definition.csv     # 省份ID-颜色-名称映射
│   ├── provinces_metadata.json
│   └── provinces_preview.png
└── tools/                 # 数据转换工具
    └── geojson_to_provinces.py
```

## 技术栈（计划）

- **引擎**: Unity 6 LTS (2D URP)
- **语言**: C#
- **地图**: 省份位图 + Shader 着色（P社方案）
- **联机**: Mirror Networking
- **数据**: ScriptableObject + JSON
- **发行**: Steam (Steamworks SDK)

## 快速开始

### 重新生成省份位图

```bash
pip install pillow shapely numpy
python tools/geojson_to_provinces.py
```

输出到 `map-output/`（provinces.bmp 约 34MB，已 gitignore）。

## 游戏设计

详见 [GAME_DESIGN_SPEC.md](data-legacy/game-design/GAME_DESIGN_SPEC.md)

## 开发路线

1. Unity 环境搭建 + C# 学习
2. 核心地图系统（省份渲染 + 点击交互）
3. 游戏模拟引擎（Tick 系统 + 经济/军事/外交）
4. MVP：东亚地图 + 3个国家 + 基本战争
5. 联机系统
6. Steam 发行
