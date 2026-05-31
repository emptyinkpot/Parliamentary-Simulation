# 前端游戏逻辑完整提取报告

> 提取自 `Parliamentary-Simulation/src/pages/` 和 `src/components/`
> 提取日期：2026-05-31

---

## 目录

1. [权限与角色系统](#1-权限与角色系统)
2. [议会投票系统](#2-议会投票系统)
3. [敕令系统](#3-敕令系统)
4. [政党系统](#4-政党系统)
5. [内阁系统](#5-内阁系统)
6. [外交系统](#6-外交系统)
7. [军事系统](#7-军事系统)
8. [经济系统](#8-经济系统)
9. [派系系统](#9-派系系统)
10. [舆论系统](#10-舆论系统)
11. [内帑系统](#11-内帑系统)
12. [成就系统](#12-成就系统)
13. [编年史系统](#13-编年史系统)
14. [政治光谱系统](#14-政治光谱系统)
15. [沉浸感系统](#15-沉浸感系统)
16. [通知系统](#16-通知系统)

---

## 1. 权限与角色系统

### 角色层级

| 角色 | 判定条件 | 权限范围 |
|------|----------|----------|
| 天皇（Administrator） | `currentUser.bilibiliUid === settings.administrator` | 最高权限，所有操作 |
| 首相（Prime Minister） | `currentUser.bilibiliUid === settings.primeMinister` | 行政权限，部分立法权 |
| 政党领袖 | `currentUser.partyRole === 'leader' \|\| 'chairman'` | 政党管理、联盟操作 |
| 普通议员 | 已登录用户 | 投票、提案、加入政党 |

### 硬编码管理员 UID（Dashboard 页面）

```typescript
const DEFAULT_ADMINISTRATOR_UID = '3461570143193870' // 天皇
const DEFAULT_PRIME_MINISTER_UID = '240847721' // 首相
```

### 权限检查逻辑（Dashboard）

```typescript
const checkPermission = async (user: Subject) => {
  const cloudSettings = await cloudManager.getSettings()
  const adminUid = String(settingsData.administrator || DEFAULT_ADMINISTRATOR_UID)
  const pmUid = String(settingsData.primeMinister || DEFAULT_PRIME_MINISTER_UID)
  const emperor = currentUserUid.trim() === adminUid.trim()
  const pm = currentUserUid.trim() === pmUid.trim()
  const permitted = emperor || pm
}
```

### 登录认证规则

- 管理员 UID 列表硬编码，需要密码验证
- 普通用户仅需输入 Bilibili UID（纯数字），无需密码
- 会话有效时自动跳转到议会页面
- 登录时重置所有单例状态（realtimeService, votingSessionManager, partyAllianceSystem, cabinetManagerCloud）

---

## 2. 议会投票系统

### 议会结构

#### 贵族院（Upper House）
- **终身议员（lifetime）**：上限 20 席
- **功勋议员（meritorious）**：上限 40 席
- **敕任议员（imperial）**：上限 30 席

#### 众议院（Lower House）
- 总席位：**435 席**

### 投票机制

#### 投票类型
```typescript
type VoteType = 'support' | 'oppose' | 'abstain'
```

#### 投票通过条件（两院制）
```typescript
const upperPassed = upperStats.support > upperStats.total * 0.5  // 贵族院过半
const lowerPassed = lowerStats.support > lowerStats.total * 0.5  // 众议院过半
const result = (upperPassed && lowerPassed) // 两院均过半才通过
```

#### 投票百分比计算
```typescript
const getVotePercentages = (bill: BillProposal) => {
  const total = bill.votes.agree + bill.votes.disagree + bill.votes.abstain
  if (total === 0) return { agree: 0, disagree: 0, abstain: 0 }
  return {
    agree: (bill.votes.agree / total) * 100,
    disagree: (bill.votes.disagree / total) * 100,
    abstain: (bill.votes.abstain / total) * 100,
  }
}
```

#### 议院统计计算
```typescript
const calculateChamberStats = (chamber: 'upper' | 'lower') => {
  let members = chamber === 'upper'
    ? [...peers.lifetime, ...peers.meritorious, ...peers.imperial]
    : parliamentData.representatives
  return members.reduce((acc, member) => {
    acc[member.currentVote]++
    return acc
  }, { support: 0, oppose: 0, abstain: 0, total: members.length })
}
```

### 投票控制面板（VotingControlPanel）

#### 状态机
```
投票会话状态: null -> active -> ended
投票操作状态: null -> voting -> voted (support|oppose|abstain)
改票状态: canChangeVote (时间限制内可改票)
```

#### 权限控制
| 操作 | 权限要求 |
|------|----------|
| 开始投票 | 首相 或 天皇 |
| 结束投票 | 仅天皇 |
| 重置投票 | 仅天皇 |
| 延长时间 | 管理员（isAdmin） |
| 投票 | 所有议员（session.status === 'active'） |

#### 延长时间规则
- 每次延长 **60 秒**

#### 改票规则
- 投票期间内可改票（`stats.canChangeVote`）
- 改票需确认弹窗

#### 法定人数（Quorum）
```typescript
interface QuorumDisplay {
  met: boolean           // 是否达成
  current: number        // 当前投票人数
  required: number       // 法定人数要求
  percentage: number     // 达成百分比
}
```

### 政党席位计算
```typescript
const getPartySeats = (partyId) => {
  return parliamentData.representatives.filter(member => {
    const subject = subjects.find(s => s.bilibiliUid === member.bilibiliUid)
    return subject?.partyId?.toString() === partyId.toString()
  }).length
}
// 席位百分比显示：partySeats / 435 * 100
// 席位条宽度：partySeats / 4.35 %
```

### 法案数据模型
```typescript
interface BillProposal {
  id: string
  title: string
  content: string
  status: 'proposed' | 'debating' | 'voting' | 'passed' | 'rejected'
  proposerId: string
  proposerName: string
  proposeDate: string
  votes: { agree: number; disagree: number; abstain: number }
}
```

### 投票记录数据模型
```typescript
interface VotingRecord {
  id: string
  billId: string
  vote: 'agree' | 'disagree' | 'abstain'
  timestamp: string
  sessionNumber: number
}
```

### 议员数据模型
```typescript
interface ParliamentMember {
  bilibiliUid: string
  displayName: string
  avatar: string
  sign?: string
  chamber: 'upper' | 'lower'
  peerType?: 'lifetime' | 'meritorious' | 'imperial'
  currentVote: 'support' | 'oppose' | 'abstain'
}
```

---

## 3. 敕令系统

### 敕令类型（8种）

| 类型 | 标识符 | 说明 |
|------|--------|------|
| 任命敕令 | `appointment` | 任命总理、大臣等职位 |
| 解散敕令 | `dissolution` | 解散议会、内阁等机构 |
| 紧急敕令 | `emergency` | 宣布紧急状态 |
| 授勋敕令 | `honor` | 授予勋章、荣誉称号 |
| 特赦敕令 | `pardon` | 特赦、减刑 |
| 行政敕令 | `administrative` | 行政命令、政策发布 |
| 军事敕令 | `military` | 军事动员、宣战 |
| 外交敕令 | `diplomatic` | 外交关系、条约 |

### 任命敕令 - 可任命职位

| 职位 ID | 名称 |
|---------|------|
| `prime_minister` | 内阁总理大臣 |
| `foreign_minister` | 外务大臣 |
| `home_minister` | 内务大臣 |
| `finance_minister` | 大藏大臣 |
| `army_minister` | 陆军大臣 |
| `navy_minister` | 海军大臣 |
| `justice_minister` | 司法大臣 |
| `education_minister` | 文部大臣 |

另外在 DecreeIssueModal 中增加了贵族院职位：
- `peer_lifetime` - 终身贵族院议员
- `peer_meritorious` - 功勋贵族院议员
- `peer_imperial` - 皇室贵族院议员

### 解散敕令 - 可解散对象

| 目标 | 标识符 | 效果 |
|------|--------|------|
| 帝国议会 | `parliament` | 新选举30日内举行 |
| 贵族院 | `upper` | 同上 |
| 众议院 | `lower` | 同上 |
| 内阁 | `cabinet` | 看守内阁维持政务 |

### 紧急敕令参数

#### 紧急类型
- `military` - 军事紧急
- `economic` - 经济紧急
- `natural_disaster` - 自然灾害
- `civil_unrest` - 社会动荡

#### 严重等级
- `minor` - 轻微
- `moderate` - 中等
- `major` - 严重
- `critical` - 危急

#### 特殊措施（可多选）
- 宵禁
- 言论管制
- 军事动员
- 物资征用

#### 紧急敕令特殊规则
- `severity === 'critical'` 时自动暂停议会运作（`parliamentSuspended: true`）
- 有效期由 `duration` 天数指定，期满后自动解除
- 解散敕令中新选举日期为 **60天后**（`Date.now() + 60 * 24 * 60 * 60 * 1000`）

### 敕令通用属性

```typescript
// 有效期计算
expiryDate = duration > 0 ? Date.now() + duration * 24 * 60 * 60 * 1000 : undefined
// duration = 0 表示永久有效

// 优先级范围：1-10
// 重要性映射（用于编年史记录）：
importance = priority >= 8 ? 4 : priority >= 5 ? 3 : 2
```

### 敕令发布流程（三步骤状态机）

```
type → details → preview → [发布]
```

1. **选择类型**：8种敕令类型
2. **填写内容**：根据类型显示专属字段 + 通用字段（标题、内容、有效期、优先级）
3. **预览发布**：生成模板预览 → 确认发布

### 敕令验证规则

- 任命敕令必须选择任命对象（`selectedMemberId`）
- 解散敕令必须填写理由（`reason.trim()`）
- 通用验证：标题和内容不能为空

---

## 4. 政党系统

### 政党创建规则

- 需在 **7天内** 获得至少 **15人** 支持
- 支持达标后自动成立，创始人成为党首
- 政党名称需 2-20 字
- 简称需 2-4 字
- 政纲需 50-500 字
- 标签最多 5 个
- 招募口号最多 50 字

### 政党状态机

```
forming（创建中，等待支持） → established（已成立） 
forming → expired（7天内未达15人支持）
```

### 政党数据模型

```typescript
interface Party {
  id: string
  name: string
  abbreviation: string
  color: string
  symbol: string
  ideology: string
  manifesto: string
  tags: string[]
  status: 'forming' | 'active'
  createdBy: 'citizen'
  founderId: string
  founderName: string
  foundedDate: string
  leaderId: string
  leaderName: string
  members: any[]
  memberCount: number
  seats: { upper: number; lower: number }
  supporters?: Array<{ userId: string }>
  expiryTime?: string
}
```

### 政党操作权限

| 操作 | 权限 |
|------|------|
| 创建政党 | 所有用户 |
| 支持创建中的政党 | 所有用户 |
| 申请入党 | 未加入政党的用户 |
| 删除政党 | 天皇/首相（且政党无成员） |
| 清理无效政党 | 天皇/首相 |

### 政党联盟系统

#### 联盟操作权限
| 操作 | 权限 |
|------|------|
| 创建联盟 | 政党领袖（`partyRole === 'leader' \|\| 'chairman'`） |
| 加入联盟 | 政党领袖 |
| 退出联盟 | 联盟成员（非盟主） |
| 解散联盟 | 盟主（`alliance.leaderParty === currentUser.partyId`） |
| 发起联盟投票 | 联盟成员 |

#### 联盟投票选项
```typescript
options: [
  { id: 'agree', text: '赞成' },
  { id: 'disagree', text: '反对' },
  { id: 'abstain', text: '弃权' }
]
```

### 政治光谱（四维坐标）

| 维度 | 标识 | 左端（0） | 右端（100） |
|------|------|-----------|-------------|
| 经济政策 | E | 计划经济 | 市场经济 |
| 政体倾向 | P | 民主 | 威权 |
| 社会政策 | S | 自由 | 保守 |
| 外交政策 | I | 国际主义 | 民族主义 |

### 意识形态标签映射规则

```typescript
// 经济维度 E
E <= 20 → '计划经济派'
E <= 40 → '左翼经济'
E <= 60 → '中间派'
E <= 80 → '右翼经济'
E > 80  → '自由市场派'

// 政体维度 P
P <= 20 → '民主主义者'
P <= 40 → '温和民主'
P <= 60 → '中间派'
P <= 80 → '威权主义'
P > 80  → '绝对权威'

// 社会维度 S
S <= 20 → '激进自由派'
S <= 40 → '自由派'
S <= 60 → '温和派'
S <= 80 → '保守派'
S > 80  → '传统主义者'

// 外交维度 I
I <= 20 → '国际主义者'
I <= 40 → '亲国际派'
I <= 60 → '中立派'
I <= 80 → '民族主义者'
I > 80  → '极端民族主义'
```

### 默认政党标签选项
- 改革派、保守派、民族主义、自由经济、社会福利、民主派、威权派

---

## 5. 内阁系统

### 内阁职位体系

内阁由首相和各大臣组成，职位定义在 `CABINET_POSITIONS` 中，按 rank 排序。

### 内阁操作权限

| 操作 | 权限 |
|------|------|
| 创建新内阁（任命首相） | 天皇 |
| 任命大臣 | 天皇 或 首相 |
| 解任大臣 | 仅天皇 |
| 内阁总辞 | 天皇 |
| 召开内阁会议 | 天皇/首相 |

### 罢免首相特殊规则

罢免首相（`positionId === 'PRIME_MINISTER'`）会触发 **整个内阁总辞解散**。

### 内阁状态

```typescript
type CabinetStatus = 'active' | 'resigned' | 'dissolved'
// active - 执政中
// resigned - 已总辞
// dissolved - 已解散
```

### 大臣任命类型

```typescript
appointmentType: 'imperial' | 'prime_minister'
// imperial - 天皇敕任
// prime_minister - 首相推荐
```

### 空缺职位计算

```typescript
const getVacantPositions = () => {
  const filledPositions = Object.keys(currentCabinet.ministers)
    .filter(id => ministers[id]?.status === 'serving')
  return Object.entries(CABINET_POSITIONS)
    .filter(([key]) => !filledPositions.includes(key) && key !== 'PRIME_MINISTER')
}
```

---

## 6. 外交系统

### 国家分类

| 类型 | 标识符 | 示例 |
|------|--------|------|
| 列强 | `great_power` | 大英帝国、德意志帝国、法兰西、俄罗斯、美国、日本 |
| 区域强国 | `regional_power` | 意大利、奥匈帝国、奥斯曼帝国 |
| 小国 | `minor_power` | 大清帝国、大韩帝国 |
| 殖民地 | `colony` | - |

### 国家数据模型

```typescript
interface Country {
  code: string           // 国家代码 (GBR, DEU, FRA...)
  name: string           // 国家名称
  flag: string           // emoji 国旗
  type: 'great_power' | 'regional_power' | 'minor_power' | 'colony'
  ideology: string       // 意识形态
  power: number          // 综合国力 (0-100)
  military: { navy: number; army: number }  // 军事力量
  economy: number        // 经济实力
  stability: number      // 稳定性
  colonies?: string[]    // 殖民地列表
  weakness?: number      // 衰弱程度 (0-100)
  flagImageKey?: string  // 自定义国旗图片
}
```

### 初始国家数据（硬编码）

| 国家 | 综合国力 | 海军 | 陆军 | 经济 | 稳定 | 衰弱 |
|------|----------|------|------|------|------|------|
| 大英帝国 | 95 | 100 | 60 | 95 | 80 | - |
| 德意志帝国 | 90 | 70 | 95 | 88 | 75 | - |
| 法兰西 | 85 | 75 | 80 | 82 | 70 | - |
| 俄罗斯帝国 | 82 | 50 | 90 | 65 | 55 | 25 |
| 美国 | 88 | 65 | 60 | 100 | 85 | - |
| 日本帝国 | 75 | 75 | 70 | 60 | 75 | - |
| 意大利 | 60 | 50 | 55 | 55 | 60 | - |
| 奥匈帝国 | 65 | 30 | 70 | 58 | 50 | 35 |
| 奥斯曼帝国 | 45 | 30 | 45 | 35 | 40 | 50 |
| 大清帝国 | 30 | 10 | 40 | 25 | 30 | 70 |
| 大韩帝国 | 15 | 5 | 15 | 12 | 35 | - |

### 外交关系等级

| 等级 | 标识符 | 颜色 |
|------|--------|------|
| 敌对 | `hostile` | #c62828 |
| 紧张 | `strained` | #ef6c00 |
| 中立 | `neutral` | #757575 |
| 友好 | `friendly` | #2e7d32 |
| 同盟 | `allied` | #1565c0 |

### 条约类型

| 类型 | 标识符 |
|------|--------|
| 同盟条约 | `alliance` |
| 互不侵犯 | `non_aggression` |
| 贸易条约 | `commerce` |
| 友好条约 | `friendship` |
| 不平等条约 | `unequal` |

### 殖民地数据模型

```typescript
interface Colony {
  name: string
  region: string
  population: number
  garrison: number        // 驻军
  loyalty: number         // 忠诚度 (0-100)
  status: 'stable' | 'unrest' | 'rebellion'
  resources: string[]
}
// 忠诚度阈值：< 30 低, < 60 中, >= 60 高
```

### 战争系统

```typescript
interface War {
  name: string
  status: 'preparing' | 'ongoing' | 'negotiating' | 'concluded'
  aggressor: string       // 进攻方
  defender: string        // 防御方
  allies: { aggressor: string[]; defender: string[] }
  casusBelli: 'territorial_claim' | 'trade_dispute' | 'colonial_conflict' | 'honor_defense' | 'alliance_obligation'
  casualties: { aggressor: number; defender: number; civilians: number }
}
```

### 外交事件系统

```typescript
interface DiplomaticEvent {
  type: 'naval_incident' | 'trade_dispute' | 'colonial_rebellion' | 'arms_race' | 'border_incident' | 'diplomatic_insult'
  severity: number        // 严重度
  parties: string[]       // 相关国家
  resolutionOptions: DiplomaticResolution[]  // 可选解决方案
}

interface DiplomaticResolution {
  name: string
  description: string
  effects: {
    prestige?: number     // 威望变化
    tension?: number      // 紧张度变化
  }
}
```

### 外交统计

```typescript
interface DiplomaticStats {
  totalRelations: number
  allies: number
  friendly: number
  neutral: number
  strained: number
  hostile: number
  activeTreaties: number
  colonies: number
  ongoingWars: number
  activeEvents: number
}
// 统计基于日本帝国（JPN）与其他国家的关系
```

---

## 7. 军事系统

### 军种数据模型

```typescript
interface MilitaryBranch {
  name: string          // 陆军/海军/空军
  personnel: number     // 兵力
  budget: number        // 预算（亿）
  influence: number     // 影响力百分比
  readiness: number     // 战备百分比
  commander?: string    // 指挥官
}
```

### 军事行动

```typescript
interface MilitaryAction {
  type: 'exercise' | 'operation' | 'deployment'  // 演习/作战/部署
  status: 'planning' | 'active' | 'completed' | 'cancelled'
  branch: 'army' | 'navy' | 'air_force'
  budget: number
  outcome?: string
}
```

### 军官系统

```typescript
interface Officer {
  name: string
  rank: string
  branch: 'army' | 'navy' | 'air_force'
  position: string
  influence: number     // 影响力
  loyalty: number       // 忠诚度百分比
  promotions: number    // 晋升次数
}
// 晋升操作：仅管理员可操作
```

### 帷幄上奏（军事报告）

```typescript
interface MilitaryReport {
  branch: 'army' | 'navy' | 'air_force'
  urgency: 'low' | 'normal' | 'high' | 'urgent'
  status: 'pending' | 'reviewed' | 'approved' | 'rejected'
  imperialResponse?: string  // 天皇批示
}
// 批准操作：仅天皇（isAdmin）可批准
```

### 军费预算

```typescript
interface MilitaryBudget {
  total: number
  army: number
  navy: number
  airForce: number
  gdpPercent: number    // 占GDP比例
  fiscalYear: number
}
// 军种预算占比 = branch.budget / total * 100
```

---

## 8. 经济系统

### 宏观经济指标

```typescript
interface EconomicIndicator {
  gdp: number           // GDP（亿日元）
  gdpGrowth: number     // 增长率%
  inflation: number     // 通胀率%
  unemployment: number  // 失业率%
  tradeBalance: number  // 贸易顺差（亿日元）
  currencyReserve: number // 外汇储备（亿美元）
  exchangeRate: number  // 汇率
}
```

### 财政数据

```typescript
interface FiscalData {
  revenue: number       // 财政收入
  expenditure: number   // 财政支出
  deficit: number       // 赤字（>0）或盈余（<0）
  nationalDebt: number  // 国债总额
  debtToGdp: number     // 债务/GDP比率%
  taxRate: number       // 税率%
}
```

### 财阀系统

```typescript
interface Zaibatsu {
  name: string
  nameJapanese?: string
  industries: string[]        // 涉足产业
  assets: number              // 资产（亿）
  revenue: number             // 营收（亿）
  profit: number              // 利润（亿）
  politicalInfluence: number  // 政治影响力%
  financialHealth: 'healthy' | 'stable' | 'critical'
}
```

### 经济政策

```typescript
interface EconomicPolicy {
  name: string
  type: string
  status: 'active' | 'pending' | 'expired'
  effects: Record<string, number>  // 效果：key为指标名，value为变化百分比
  startDate: string
  endDate?: string
}
// 执行政策：仅管理员可对 pending 状态的政策执行
```

### 经济事件

```typescript
interface EconomicEvent {
  title: string
  description: string
  impact: 'positive' | 'negative' | 'neutral'  // 利好/利空/中性
  severity: number
}
```

---

## 9. 派系系统

### 派系数据模型

```typescript
interface Faction {
  name: string
  description: string
  ideology: string
  leader: string
  memberCount: number
  influence: number      // 影响力
  treasury: number       // 资金
}

interface FactionMember {
  name: string
  role: 'leader' | 'core' | 'member'
  influence: number
  loyalty: number        // 忠诚度
}
```

### 派系斗争

```typescript
interface FactionConflict {
  type: 'political' | 'economic' | 'ideological'
  status: 'ongoing' | 'resolved' | 'stalemate'
  attackerName: string
  defenderName: string
  winnerId?: number
}
// 斗争类型：政治斗争、经济斗争、意识形态斗争
// 发起斗争：仅管理员
```

### 影响力排行

```typescript
interface InfluenceRanking {
  rank: number
  factionName: string
  influence: number
  memberCount: number
  change: number         // 排名变化（正=上升，负=下降）
}
```

---

## 10. 舆论系统

### 舆论指标

```typescript
interface OpinionIndicator {
  supportRate: number      // 支持率%
  oppositionRate: number   // 反对率%
  neutralRate: number      // 中立率%
  engagement: number       // 参与度%
  topTopics: string[]      // 热门话题
  sentiment: 'positive' | 'neutral' | 'negative'  // 情感倾向
  trend: 'up' | 'stable' | 'down'                 // 舆论趋势
}
```

### 新闻系统

```typescript
interface NewsItem {
  title: string
  content: string
  category: 'politics' | 'military' | 'economy' | 'society'
  importance: 'high' | 'medium' | 'low'
  status: 'draft' | 'published' | 'archived'
  views: number
}
// 发布新闻：仅管理员
```

### 媒体机构

```typescript
interface MediaOutlet {
  name: string
  type: 'newspaper' | 'radio' | 'television'
  influence: number      // 影响力%
  bias: 'government' | 'neutral' | 'opposition'  // 立场偏向
  reach: number          // 覆盖面（万人）
}
```

### 舆论事件

```typescript
interface OpinionEvent {
  impact: 'positive' | 'negative' | 'neutral'
  severity: number       // 影响程度 (1-5)
}
// 影响程度条宽度 = severity * 20 %
```

---

## 11. 内帑系统

### 内帑余额

```typescript
interface TreasuryBalance {
  total: number        // 总额
  available: number    // 可用
  reserved: number     // 预留
}
```

### 贡献系统

```typescript
interface Contribution {
  amount: number
  status: 'pending' | 'verified' | 'rejected'
  paymentMethod: string   // 'alipay' | 'wechat' | 'bank'
  transactionId?: string
  verifierName?: string
}
// 验证贡献：仅管理员
// 支付方式：支付宝、微信支付、银行转账
```

### 支出分类

```typescript
type ExpenseCategory = 'royal' | 'military' | 'ceremony' | 'charity' | 'other'
// 皇室支出、军事支出、典礼支出、慈善支出、其他支出

interface ExpenseRecord {
  amount: number
  category: ExpenseCategory
  status: 'pending' | 'approved' | 'completed'
  approvedBy: string
}
```

### 内帑统计

```typescript
interface TreasuryStats {
  totalContributions: number    // 累计贡献
  totalExpenses: number         // 累计支出
  monthlyContributions: number  // 本月收入
  monthlyExpenses: number       // 本月支出
  pendingVerifications: number  // 待验证数
  topContributors: Array<{ userName: string; totalAmount: number }>
}
```

### 收款二维码
- 仅管理员可生成
- 通过后端 API `/api/treasury/qrcode` 获取

---

## 12. 成就系统

### 成就数据模型

```typescript
interface BackendAchievement {
  id: number
  name: string
  displayName: string
  description: string
  type: string
  rarity: 'common' | 'rare' | 'epic' | 'legendary'
  conditions: { type: string; count: number }
  rewards: { badge?: string; title?: string; coins?: number }
}
```

### 成就稀有度

| 稀有度 | 标识符 | 颜色 | 图标 |
|--------|--------|------|------|
| 普通 | `common` | #90caf9 | Award |
| 稀有 | `rare` | #42a5f5 | Star |
| 史诗 | `epic` | #ab47bc | Trophy |
| 传说 | `legendary` | #ffd700 | Crown |

### 成就进度计算

```typescript
const getAchievementProgress = (achievement) => {
  const { type, count } = achievement.conditions
  let current = 0
  switch (type) {
    case 'vote_count': current = userStats.voteCount; break
    case 'bill_proposed': current = userStats.billProposed; break
    case 'bill_passed': current = userStats.billPassed; break
  }
  return { current: Math.min(current, count), target: count }
}
// 进度百分比 = (current / target) * 100
```

### 成就条件类型
- `vote_count` - 投票次数
- `bill_proposed` - 提案数
- `bill_passed` - 通过法案数

### 成就奖励类型
- `badge` - 徽章
- `title` - 称号
- `coins` - 金币

### 成就检查
- 通过 POST 请求 `/api/achievements/user/{uid}/check` 触发服务端检查
- 新解锁的成就会逐一弹窗通知

---

## 13. 编年史系统

### 历史事件数据模型

```typescript
interface HistoricalEvent {
  id: number
  eventType: string
  eventTitle: string
  eventDescription: string
  relatedUserId?: number
  relatedUserName?: string
  relatedPartyId?: number
  relatedPartyName?: string
  relatedBillId?: number
  relatedBillTitle?: string
  importance: number        // 1-5 星级
  eventDate: string
  metadata?: Record<string, any>
}
```

### 事件类型

| 类型 | 标签 |
|------|------|
| `user_joined` | 臣民归附 |
| `peer_appointed` | 贵族敕任 |
| `cabinet_formed` | 内阁组阁 |
| `bill_passed` | 议案通过 |
| `vote_cast` | 投票记录 |
| `era_change` | 纪元更替 |
| `empire_created` | 帝国创立 |
| `major_war` | 战事记录 |
| `peace_treaty` | 和平条约 |
| `achievement_earned` | 荣誉封赏 |
| `login` | 朝见记录 |
| `settings_updated` | 制度变更 |
| `decree_issued` | 敕令颁布 |

### 重要性等级
- 1星 - 琐事
- 2星 - 次要
- 3星 - 一般
- 4星 - 重要
- 5星 - 极重要

### 筛选系统
- 关键词搜索（标题、描述、人物名、政党名）
- 时间范围：全部/今日/本周/本月/本年
- 重要性过滤
- 事件类型过滤
- 排序：按日期或重要性（升序/降序）

### 历史统计

```typescript
interface HistoryStatistics {
  totalEvents: number
  eventsByType: Record<string, number>
  eventsByMonth: Array<{ month: string; count: number }>
  topParticipants: Array<{ userId: number; userName: string; eventCount: number }>
}
```

---

## 14. 政治光谱系统

### 四维政治坐标

```typescript
interface PoliticalSpectrum {
  E: number  // 经济：0(计划) → 100(市场)
  P: number  // 政体：0(民主) → 100(威权)
  S: number  // 社会：0(自由) → 100(保守)
  I: number  // 外交：0(国际主义) → 100(民族主义)
}
```

- 每个维度范围 0-100，步进 1
- 用户可随时调整并保存到云端
- 调整后自动计算意识形态标签

---

## 15. 沉浸感系统

### ImperialTicker（帝国新闻滚动条）

- 每 **12秒** 切换一条消息
- 动画三阶段：`in`(300ms) → `stable` → `out`(200ms) → 切换
- 消息来源：`immersiveSystem.narrative`
- 消息包含：icon、title、text、style

### ImperialScrollBar（通知滚动栏）

- 每 **5秒** 自动滚动到下一条
- 每 **30秒** 从后端刷新通知
- 用户触摸暂停滚动，松开 **2秒后** 恢复
- 点击通知跳转到详情页并标记已读
- 无缝循环实现：复制第一条到末尾，CSS translate 滚动

### 叙事事件触发

```typescript
// 议会相关
immersiveSystem.narrative.triggerEventNarrative('parliament', {})
// 投票相关
immersiveSystem.narrative.triggerEventNarrative('vote_cast', { voter, vote })
// 成就相关
immersiveSystem.narrative.triggerEventNarrative('achievement', { count })
```

### 反馈音效触发点

```typescript
playImperialFeedback('buttonClick')  // 按钮点击
playImperialFeedback('success')      // 操作成功
playImperialFeedback('vote')         // 投票
```

---

## 16. 通知系统

### 通知数据模型

```typescript
interface ImperialNotification {
  id: string
  type: string           // 'system' 等
  source: string         // 来源标识
  title: string
  content: string
  icon: string           // emoji
  priority: 'high' | 'medium' | 'low'
  createdAt: string
  expiryDate: string | null
  readCount: number
  isRead: boolean
  metadata: { link?: string }
}
```

### 默认通知（后端不可用时）

```typescript
{
  id: 'default_001',
  type: 'system',
  source: 'SYSTEM',
  title: '歡迎蒞臨大光譜帝國',
  content: '規則に従を、真実の味、を止めろ。',
  icon: '🏛️',
  priority: 'medium'
}
```

---

## 附录：Dashboard 仪表盘统计

### 仪表盘数据计算

```typescript
interface DashboardStats {
  totalMembers: number        // 云端 getAllMembers().length
  activeBills: number         // parliament_bills where status='proposed'
  activeVoting: number        // votingSessionManager 当前会话 ? 1 : 0
  pendingDecrees: number      // decrees where status='pending'
  supportRate: number         // supportVotes / totalVotes * 100
  crisisLevel: number         // 默认0
}
```

### 支持率计算

```typescript
const votesData = await getDB().collection('parliament_votes').get()
const totalVotes = votesData.length
const supportVotes = votesData.filter(v => v.vote === 'support').length
const supportRate = totalVotes > 0 ? (supportVotes / totalVotes) * 100 : 0
```

---

## 附录：臣民管理功能（Dashboard）

### 臣民操作

| 操作 | 说明 |
|------|------|
| 封禁/解封 | 切换 isBanned 状态，保存到云端 |
| 删除臣民 | 从云端删除，不可恢复 |
| 调整影响力 | `Math.max(0, influence + delta)` |
| 贵族院敕任 | 将臣民任命为贵族院议员 |

### 贵族院议员类型

```typescript
type PeerType = 'lifetime' | 'meritorious' | 'imperial'
// lifetime - 终身议员
// meritorious - 功勋议员
// imperial - 敕任议员
```

---

## 附录：御前广场

### 公告板类型
- `urgent` - 紧急
- `official` - 官方
- `notice` - 通知

### 讨论帖数据

```typescript
interface Discussion {
  author: string
  title: string
  content: string
  category: string
  tags: string[]
  likes: number
  replies: number
  views: number
  hotScore: number    // 热度分数
}
```

---

## 附录：数据流与服务依赖

### 云开发服务（微信小程序）
- `cloudManager` - 核心数据 CRUD
- `realtimeService` - 实时数据监听
- `votingServiceCloud` - 投票会话管理
- `ParliamentDataManagerCloud` - 议会数据缓存
- `cabinetManagerCloud` - 内阁管理

### 后端 API 服务
- `/api/history/*` - 编年史
- `/api/achievements/*` - 成就
- `/api/parties/*` - 政党
- `/api/economic/*` - 经济
- `/api/military/*` - 军事
- `/api/faction/*` - 派系
- `/api/opinion/*` - 舆论
- `/api/treasury/*` - 内帑
- `/api/upload/*` - 文件上传

### 降级策略
- 云开发不可用时降级到本地模式（`useLocalMode = true`）
- 本地模式下投票功能不可用
- 政党数据从云端获取失败时显示错误提示

