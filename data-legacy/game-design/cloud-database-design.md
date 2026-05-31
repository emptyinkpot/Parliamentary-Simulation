# 微信云开发数据库设计文档

> **更新日期**: 2025-03-12
> **集合数量**: 26 个

## 数据库集合列表

| 集合名称 | 用途 |
|---------|------|
| `parliament_members` | 议员数据 |
| `parliament_bills` | 议会议案 |
| `parliament_sessions` | 投票会话 |
| `parliament_votes` | 投票记录 |
| `parties` | 政党数据 |
| `party_alliances` | 政党联盟 |
| `alliance_votes` | 联盟投票 |
| `cabinets` | 内阁数据 |
| `decrees` | 天皇敕令 |
| `imperial_settings` | 帝国设置 |
| `imperial_reports` | 帷幄上奏报告 |
| `elections` | 选举记录 |
| `factions` | 派阀数据 |
| `faction_members` | 派阀成员 |
| `faction_struggles` | 派阀斗争 |
| `chronicles` | 编年史 |
| `news_articles` | 新闻报道 |
| `public_opinion` | 舆论数据 |
| `economic_data` | 经济数据 |
| `zaibatsu` | 财阀数据 |
| `countries` | 国家数据 |
| `diplomatic_relations` | 外交关系 |
| `diplomatic_events` | 外交事件 |
| `treaties` | 条约数据 |
| `colonies` | 殖民地数据 |
| `wars` | 战争数据 |

---

## 数据库集合结构

### 1. parliament_members（议员集合）

存储所有议员的基本信息和当前投票状态。

```javascript
{
  "_id": "自动生成",
  "bilibiliUid": "用户B站ID",
  "displayName": "显示名称",
  "avatar": "头像URL",
  "sign": "签名",
  "chamber": "upper" | "lower",  // 议院类型
  "peerType": "lifetime" | "meritorious" | "imperial" | null,  // 贵族院席位类型
  "currentVote": "abstain" | "support" | "oppose",  // 当前投票状态
  "createdAt": 1234567890000,  // 创建时间
  "updatedAt": 1234567890000   // 更新时间
}
```

**索引**:
- `bilibiliUid`（唯一索引）
- `chamber` + `peerType`（复合索引）

---

### 2. parliament_bills（议案集合）

存储所有议案信息。

```javascript
{
  "_id": "自动生成",
  "title": "议案标题",
  "description": "议案描述",
  "proposer": "提案人",
  "status": "pending" | "voting" | "passed" | "rejected",  // 议案状态
  "createdAt": 1234567890000,
  "votedAt": 1234567890000,  // 投票结束时间
  "result": {
    "totalVotes": 100,
    "supportVotes": 60,
    "opposeVotes": 30,
    "abstainVotes": 10,
    "supportRate": 60,
    "result": "passed" | "rejected" | "draw"
  }
}
```

**索引**:
- `createdAt`（降序）
- `status`

---

### 3. parliament_votes（投票记录集合）

存储每次投票的详细记录。

```javascript
{
  "_id": "自动生成",
  "billId": "议案ID",
  "bilibiliUid": "用户ID",
  "vote": "support" | "oppose" | "abstain",  // 投票选项
  "timestamp": 1234567890000,  // 投票时间戳
  "chamber": "upper" | "lower",  // 议院类型（用于统计）
  "peerType": "lifetime" | "meritorious" | "imperial" | null
}
```

**索引**:
- `billId` + `bilibiliUid`（复合唯一索引）
- `billId` + `vote`（复合索引，用于统计）

---

### 4. parliament_sessions（投票会话集合）

存储当前激活的投票会话。

```javascript
{
  "_id": "自动生成",
  "billId": "议案ID",
  "billTitle": "议案标题",
  "startTime": 1234567890000,
  "endTime": 1234567890000,
  "isActive": true | false,  // 会话是否激活
  "createdAt": 1234567890000
}
```

**约束**:
- 任何时候只能有一个 `isActive: true` 的会话

---

### 5. parliament_settings（议会设置集合）

存储议会全局设置。

```javascript
{
  "_id": "自动生成",
  "key": "configuration",
  "config": {
    "upperHouse": {
      "lifetime": { "maxSeats": 20, "columns": 4 },
      "meritorious": { "maxSeats": 40, "columns": 5 },
      "imperial": { "maxSeats": 40, "columns": 5 }
    },
    "lowerHouse": {
      "maxSeats": 200,
      "columns": 10
    }
  },
  "updatedAt": 1234567890000
}
```

---

## 数据库操作说明

### 初始化数据

首次启动时，需要：
1. 创建所有集合
2. 初始化 `parliament_settings`
3. 从 `ImperialDataManager` 导入用户数据到 `parliament_members`

### 实时监听

使用 `db.collection().watch()` 实现实时同步：

```javascript
// 监听议员投票状态变化
db.collection('parliament_members').watch({
  onChange: (snapshot) => {
    snapshot.docs.forEach(doc => {
      console.log('议员投票状态更新:', doc._id, doc.currentVote)
    })
  }
})

// 监听投票会话变化
db.collection('parliament_sessions')
  .where({ isActive: true })
  .watch({
    onChange: (snapshot) => {
      if (snapshot.docs.length > 0) {
        const session = snapshot.docs[0]
        console.log('当前投票会话:', session)
      }
    }
  })
```

### 权限控制

在微信云开发控制台设置数据库权限：

**parliament_members**:
- 所有用户可读
- 仅管理员可写

**parliament_bills**:
- 所有用户可读
- 仅管理员可创建/更新状态

**parliament_votes**:
- 所有用户可读
- 所有用户可创建（只能创建自己的投票）
- 禁止更新和删除

**parliament_sessions**:
- 所有用户可读
- 仅管理员可写

---

## 数据流

### 用户投票流程

```
1. 用户点击"支持"
   ↓
2. 前端调用 CloudManager.vote(uid, billId, 'support')
   ↓
3. 云函数/SDK 更新 parliament_members 的 currentVote
   ↓
4. 添加投票记录到 parliament_votes
   ↓
5. 数据库触发 watch 事件
   ↓
6. 所有在线用户的 UI 自动更新
```

### 开始投票流程

```
1. 管理员点击"开始投票"
   ↓
2. 创建议案到 parliament_bills
   ↓
3. 创建会话到 parliament_sessions (isActive: true)
   ↓
4. 重置所有议员的 currentVote 为 'abstain'
   ↓
5. 数据库触发 watch 事件
   ↓
6. 所有在线用户看到投票开始
```

---

## 云函数（可选）

如果需要复杂业务逻辑，可以使用云函数：

### addVote（投票云函数）
```javascript
// 云函数入口
exports.main = async (event) => {
  const { billId, uid, vote } = event

  // 验证投票会话是否激活
  const session = await db.collection('parliament_sessions')
    .where({ isActive: true })
    .get()

  if (session.data.length === 0) {
    return { code: 400, msg: '投票会话未激活' }
  }

  // 验证用户是否是议员
  const member = await db.collection('parliament_members')
    .where({ bilibiliUid: uid })
    .get()

  if (member.data.length === 0) {
    return { code: 400, msg: '用户不是议员' }
  }

  // 更新投票状态
  await db.collection('parliament_members')
    .doc(member.data[0]._id)
    .update({
      currentVote: vote,
      updatedAt: Date.now()
    })

  // 添加投票记录
  await db.collection('parliament_votes').add({
    billId,
    bilibiliUid: uid,
    vote,
    timestamp: Date.now(),
    chamber: member.data[0].chamber,
    peerType: member.data[0].peerType
  })

  return { code: 200, msg: '投票成功' }
}
```

---

## 迁移说明

### 从本地数据迁移到云数据库

```javascript
// 1. 获取本地用户数据
const subjects = ImperialDataManager.getSubjects()

// 2. 过滤管理员
const members = subjects.filter(s => !s.isAdmin)

// 3. 转换并上传到云数据库
for (const subject of members) {
  await db.collection('parliament_members').add({
    bilibiliUid: subject.bilibiliUid,
    displayName: subject.displayName,
    avatar: subject.avatar,
    sign: subject.sign,
    chamber: subject.parliamentaryStatus?.chamber || 'lower',
    peerType: subject.parliamentaryStatus?.seatType,
    currentVote: 'abstain',
    createdAt: Date.now(),
    updatedAt: Date.now()
  })
}
```

---

## 监控与维护

### 数据库性能监控
- 在云开发控制台查看读写次数
- 监控集合大小
- 查看慢查询日志

### 备份策略
- 云开发自动备份（免费）
- 建议定期导出重要数据

### 清理策略
- 定期清理过期的投票记录
- 归档历史议案数据

---

## 注意事项

1. **并发控制**: 同一用户同时多次投票，使用事务处理
2. **数据一致性**: 使用 watch 监听确保 UI 与数据库一致
3. **错误处理**: 网络异常时，本地缓存并重试
4. **性能优化**: 避免频繁读取，合理使用 watch
5. **安全性**: 不要在前端暴露敏感操作
