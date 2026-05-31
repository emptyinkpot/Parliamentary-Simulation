# 架构说明

## 架构决策：统一使用微信云数据库

### 背景
项目最初设计为前后端分离架构，后端使用 NestJS + PostgreSQL。但由于微信小程序的特性，最终选择了**统一使用微信云数据库**作为数据存储方案。

### 当前架构

```
┌─────────────────────────────────────────────────────────────┐
│                        前端 (Taro + React)                    │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Pages                    Utils/Managers                     │
│  ├── congress/           ├── voting-service-cloud.ts        │
│  ├── cabinet/            ├── cabinet-manager-cloud.ts       │
│  ├── party/              ├── party-alliance-system.ts       │
│  ├── dashboard/          ├── imperial-decree-system.ts      │
│  └── tenno-admin/        └── cloud-manager.ts               │
│                                                              │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ 直接操作
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    微信云开发数据库                           │
├─────────────────────────────────────────────────────────────┤
│  集合列表 (26个)                                             │
│  ├── parliament_members    议员数据                          │
│  ├── parliament_bills      议案数据                          │
│  ├── parliament_sessions   投票会话                          │
│  ├── parliament_votes      投票记录                          │
│  ├── cabinets              内阁数据                          │
│  ├── decrees               天皇敕令                          │
│  ├── parties               政党数据                          │
│  ├── party_alliances       政党联盟                          │
│  └── ...                                                    │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    后端 (NestJS) - 已废弃                     │
├─────────────────────────────────────────────────────────────┤
│  ⚠️ 后端API已不再被前端调用，保留仅供参考                      │
│  - ParliamentController                                     │
│  - CabinetController                                        │
│  - PartyController                                          │
│                                                              │
│  后端服务仍可用于：                                          │
│  - 管理后台 (如需)                                           │
│  - 第三方API集成                                             │
│  - 复杂数据分析                                              │
└─────────────────────────────────────────────────────────────┘
```

### 数据流

#### 投票系统
```
前端页面 → voting-service-cloud.ts → cloud-manager.ts → 云数据库
                                              ↓
                                    parliament_bills (议案)
                                    parliament_sessions (会话)
                                    parliament_votes (投票记录)
```

#### 内阁管理
```
前端页面 → cabinet-manager-cloud.ts → cloud-manager.ts → 云数据库
                                              ↓
                                    cabinets (内阁数据)
```

#### 政党联盟
```
前端页面 → party-alliance-system.ts → cloud-manager.ts → 云数据库
                                              ↓
                                    parties (政党)
                                    party_alliances (联盟)
                                    alliance_votes (联盟投票)
```

#### 天皇敕令
```
前端页面 → imperial-decree-system.ts → cloud-manager.ts → 云数据库
                                              ↓
                                    decrees (敕令)
```

### 核心工具类

| 文件 | 用途 |
|-----|------|
| `cloud-manager.ts` | 云数据库基础操作封装 |
| `voting-service-cloud.ts` | 投票系统管理 |
| `cabinet-manager-cloud.ts` | 内阁管理（新增） |
| `party-alliance-system.ts` | 政党联盟管理 |
| `imperial-decree-system.ts` | 天皇敕令管理 |
| `realtime-service.ts` | 实时数据监听 |
| `parliament-data-manager-cloud.ts` | 议员数据管理 |

### 后端API状态

| Controller | 状态 | 说明 |
|-----------|------|------|
| ParliamentController | ⚠️ 废弃 | 前端使用云数据库 |
| CabinetController | ⚠️ 废弃 | 前端使用云数据库 |
| PartyController | ⚠️ 废弃 | 前端使用云数据库 |
| BilibiliController | ✅ 活跃 | B站API代理 |
| StorageController | ✅ 活跃 | 文件上传 |
| HistoryController | ⚠️ 废弃 | 前端使用云数据库 |

### 注意事项

1. **数据一致性**：所有数据存储在云数据库中，确保单一数据源 (SSOT)
2. **权限控制**：云数据库安全规则需要在微信云开发控制台配置
3. **实时同步**：使用 `realtimeService` 实现数据变化监听
4. **离线支持**：部分数据支持本地缓存，可在弱网环境下使用

### 未来优化

如需更强的数据分析和复杂查询能力，可以考虑：
1. 添加云函数作为中间层
2. 定期同步数据到 PostgreSQL 进行分析
3. 使用微信云开发的聚合查询能力
