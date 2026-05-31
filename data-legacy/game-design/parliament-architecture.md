# 议会系统架构设计文档

## 1. 架构概览

### 分层架构
```
┌─────────────────────────────────────┐
│   UI Layer (React Components)       │
│   - CongressGridPage                │
│   - ParliamentPage                  │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│   Service Layer (Business Logic)    │
│   - ParliamentService               │
│   - VotingService                   │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│   Data Layer (Data Management)      │
│   - ParliamentDataManager           │
│   - ParliamentConfig                │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│   Infrastructure Layer              │
│   - ImperialDataManager             │
│   - SessionManager                  │
└─────────────────────────────────────┘
```

## 2. 核心模块职责

### 2.1 ParliamentConfig（配置层）
**职责**：定义议会席位配置，支持动态扩展

**配置结构**：
```typescript
interface ParliamentConfig {
  // 贵族院配置
  upperHouse: {
    lifetime: ChamberConfig;   // 终身议员
    meritorious: ChamberConfig; // 功勋议员
    imperial: ChamberConfig;   // 敕任议员
  };
  // 众议院配置
  lowerHouse: ChamberConfig;
}

interface ChamberConfig {
  maxSeats: number;      // 最大席位
  columns: number;       // 列数（用于网格布局）
  name: string;          // 显示名称
  icon: string;          // 图标
}
```

**优势**：
- 可扩展：新增席位类型只需修改配置
- 集中管理：席位配置统一管理
- 易于调整：支持运行时调整席位数量

---

### 2.2 ParliamentDataManager（数据层）
**职责**：从 `Subject` 数据中提取、分类、过滤议员数据

**核心方法**：

```typescript
class ParliamentDataManager {
  // 获取所有议员（过滤管理员）
  getAllSubjects(): Subject[] {
    return ImperialDataManager.getSubjects()
      .filter(s => !s.isAdmin);  // 管理员不入议会
  }

  // 分类议员到各议院
  categorizeMembers(subjects: Subject[]): ParliamentData {
    // 1. 提取贵族院议员
    const upperMembers = subjects.filter(s =>
      s.parliamentaryStatus?.chamber === 'upper'
    );

    // 2. 分类贵族院议员类型
    const lifetime = upperMembers.filter(s =>
      s.parliamentaryStatus?.seatType === 'lifetime'
    );

    const meritorious = upperMembers.filter(s =>
      s.parliamentaryStatus?.seatType === 'meritorious'
    );

    const imperial = upperMembers.filter(s =>
      s.parliamentaryStatus?.seatType === 'imperial'
    );

    // 3. 众议院议员（未设置议会状态或设置为 lower）
    const lowerMembers = subjects.filter(s =>
      !s.parliamentaryStatus || s.parliamentaryStatus.chamber !== 'upper'
    );

    return {
      peers: { lifetime, meritorious, imperial },
      representatives: lowerMembers
    };
  }

  // 将 Subject 转换为 ParliamentMember
  toParliamentMember(subject: Subject): ParliamentMember {
    return {
      bilibiliUid: subject.bilibiliUid,
      displayName: subject.displayName,
      avatar: subject.avatar,
      sign: subject.sign,
      chamber: subject.parliamentaryStatus?.chamber || 'lower',
      peerType: subject.parliamentaryStatus?.seatType,
      politicalSpectrum: subject.politicalSpectrum,
      currentVote: 'abstain',
      voteHistory: []
    };
  }
}
```

**核心规则**：
1. **管理员不入议会**：通过 `!s.isAdmin` 过滤
2. **互斥原则**：用户只能在一个议院
   - 贵族院：`chamber === 'upper'` 且 `seatType` 为 lifetime/meritorious/imperial
   - 众议院：未设置议会状态或 `chamber !== 'upper'`
3. **动态席位**：根据席位配置裁剪或扩展列表

---

### 2.3 ParliamentService（服务层）
**职责**：议会业务逻辑管理

**核心方法**：

```typescript
class ParliamentService {
  // 获取议会数据
  getParliamentData(): ParliamentData {
    const subjects = ParliamentDataManager.getAllSubjects();
    return ParliamentDataManager.categorizeMembers(subjects);
  }

  // 获取统计信息
  getStatistics(): ParliamentStatistics {
    const data = this.getParliamentData();
    // 计算各议院投票统计
  }

  // 切换用户议院（管理员功能）
  transferMember(uid: string, targetChamber: ChamberType, seatType?: PeerType) {
    // 更新用户议会状态
    // 自动从原议院移除
  }
}
```

---

### 2.4 VotingService（投票服务层）
**职责**：投票流程管理

**核心方法**：

```typescript
class VotingService {
  // 开始投票
  startVoting(billId: string): void {
    // 初始化投票会话
    // 重置所有议员状态为 abstain
  }

  // 用户投票
  castVote(uid: string, billId: string, vote: VoteState): void {
    // 验证用户是否是议员
    // 验证投票会话是否开启
    // 更新投票状态
    // 记录投票历史
  }

  // 结束投票
  endVoting(): VotingResults {
    // 统计投票结果
    // 判断议案通过与否
    // 保存投票历史
  }
}
```

**投票流程**：
```
1. 开始投票 (startVoting)
   ├─ 验证议案状态
   ├─ 初始化投票会话
   └─ 重置所有议员为 abstain

2. 用户投票 (castVote)
   ├─ 验证用户权限（是否是议员）
   ├─ 验证投票会话状态
   ├─ 更新 currentVote
   └─ 记录到 voteHistory

3. 结束投票 (endVoting)
   ├─ 统计各议院投票数
   ├─ 判断通过条件
   └─ 保存到历史记录
```

---

## 3. 数据流

### 初始化流程
```
1. 用户登录
   ↓
2. SessionManager.getSession()
   ↓
3. ParliamentDataManager.getAllSubjects()
   ├─ 过滤管理员 (!isAdmin)
   └─ 过滤非活跃用户
   ↓
4. categorizeMembers()
   ├─ 贵族院：chamber === 'upper'
   │   ├─ lifetime
   │   ├─ meritorious
   │   └─ imperial
   └─ 众议院：chamber !== 'upper'
   ↓
5. toParliamentMember()
   ├─ 初始化 currentVote = 'abstain'
   └─ 初始化 voteHistory = []
   ↓
6. 渲染 UI
```

### 投票流程
```
1. 管理员点击"开始投票"
   ↓
2. VotingService.startVoting(billId)
   ↓
3. 用户点击格子投票
   ↓
4. VotingService.castVote(uid, billId, vote)
   ├─ 验证：用户是否是议员？
   ├─ 验证：投票会话是否开启？
   └─ 更新 currentVote
   ↓
5. UI 实时刷新（网格颜色变化）
   ↓
6. 管理员点击"结束投票"
   ↓
7. VotingService.endVoting()
   └─ 生成投票结果
```

---

## 4. 扩展性设计

### 4.1 新增席位类型
只需修改配置：
```typescript
// ParliamentConfig.ts
export const PARLIAMENT_CONFIG = {
  upperHouse: {
    lifetime: { maxSeats: 20, columns: 4, name: '终身议员', icon: '⚔️' },
    meritorious: { maxSeats: 40, columns: 5, name: '功勋议员', icon: '🏅' },
    imperial: { maxSeats: 40, columns: 5, name: '敕任议员', icon: '👑' },
    // 新增席位类型
    hereditary: { maxSeats: 50, columns: 5, name: '世袭议员', icon: '🏰' },
  },
  lowerHouse: {
    maxSeats: 300, columns: 10, name: '众议院', icon: '🏛️'
  }
};
```

### 4.2 新增议院类型
1. 修改 `ChamberType` 类型定义
2. 在配置中添加新议院配置
3. 在 `categorizeMembers` 中添加分类逻辑
4. 在 UI 中添加渲染逻辑

---

## 5. 关键约束

### 5.1 管理员规则
- ✅ `isAdmin === true` 的用户不进入议会
- ✅ 管理员可以操作投票（开始/结束）
- ✅ 管理员不可以投票

### 5.2 互斥原则
- ✅ 用户只能在一个议院
- ✅ 从贵族院转移到众议院，自动从贵族院移除
- ✅ 从众议院转移到贵族院，自动从众议院移除

### 5.3 席位限制
- ✅ 贵族院：按席位配置裁剪（先到先得）
- ✅ 众议院：按席位配置裁剪（按选区分配）
- ✅ 超出席位的用户进入待定区（可配置）

---

## 6. 实现清单

### Phase 1: 核心架构
- [x] 创建 `ParliamentConfig.ts` - 配置层
- [ ] 创建 `ParliamentDataManager.ts` - 数据层
- [ ] 重构 `ParliamentService.ts` - 服务层
- [ ] 创建 `VotingService.ts` - 投票服务

### Phase 2: UI 重构
- [ ] 重构 `CongressGridPage` - 使用新服务层
- [ ] 重构 `ParliamentPage` - 使用新服务层
- [ ] 添加管理员权限检测

### Phase 3: 投票功能
- [ ] 实现开始投票流程
- [ ] 实现用户投票流程
- [ ] 实现结束投票流程
- [ ] 实时更新 UI

---

## 7. 测试用例

### 用例1: 管理员不入议会
```typescript
// Given: 有一个管理员用户 admin
const admin = { bilibiliUid: 'admin', isAdmin: true };

// When: 获取所有议员
const members = ParliamentDataManager.getAllSubjects();

// Then: admin 不在议员列表中
expect(members.find(m => m.bilibiliUid === 'admin')).toBeUndefined();
```

### 用例2: 用户只能在单个议院
```typescript
// Given: 用户设置为敕任议员
const user = {
  bilibiliUid: 'user1',
  parliamentaryStatus: { chamber: 'upper', seatType: 'imperial' }
};

// When: 分类议员
const data = ParliamentDataManager.categorizeMembers([user]);

// Then: 用户只在贵族院敕任列表，不在众议院
expect(data.peers.imperial).toContain(user);
expect(data.representatives).not.toContain(user);
```

### 用例3: 投票流程
```typescript
// Given: 有一个投票会话开启
VotingService.startVoting(billId);

// When: 用户投票
VotingService.castVote(uid, billId, 'support');

// Then: 用户的 currentVote 更新
const member = ParliamentService.getMember(uid);
expect(member.currentVote).toBe('support');
```

---

## 8. 待办事项

- [ ] 实现 ParliamentConfig
- [ ] 实现 ParliamentDataManager
- [ ] 实现 VotingService
- [ ] 重构 UI 组件使用新服务层
- [ ] 添加单元测试
- [ ] 更新文档
