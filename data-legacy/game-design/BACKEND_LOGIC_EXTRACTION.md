# 后端业务逻辑完整提取报告

> 提取来源：`E:\My Project\Parliamentary-Simulation\server\src\`
> 提取日期：2026-05-31
> 说明：原始 NestJS 源文件在 Coze 沙箱环境中，本地仅保留空目录结构。本报告从迁移文件（SQL schema）、CHANGELOG、架构文档、功能状态文档中完整还原所有业务逻辑。

---

## 目录

1. [系统总览](#系统总览)
2. [数据模型（PostgreSQL Schema）](#数据模型)
3. [模块详解](#模块详解)
   - [achievements - 成就系统](#achievements---成就系统)
   - [admin - 管理后台](#admin---管理后台)
   - [bilibili - B站用户集成](#bilibili---b站用户集成)
   - [cabinet - 内阁系统](#cabinet---内阁系统)
   - [decree - 敕令系统](#decree---敕令系统)
   - [diplomacy - 外交系统](#diplomacy---外交系统)
   - [economic - 经济系统](#economic---经济系统)
   - [faction - 派阀系统](#faction---派阀系统)
   - [history - 史官系统](#history---史官系统)
   - [ideology - 意识形态系统](#ideology---意识形态系统)
   - [military - 军部帷幄](#military---军部帷幄)
   - [notification - 通知系统](#notification---通知系统)
   - [opinion - 舆论系统](#opinion---舆论系统)
   - [parliament - 议会系统](#parliament---议会系统)
   - [party - 政党系统](#party---政党系统)
   - [search - 搜索系统](#search---搜索系统)
   - [storage - 存储系统](#storage---存储系统)
   - [treasury - 内帑系统](#treasury---内帑系统)
   - [upload - 上传系统](#upload---上传系统)
   - [users - 用户系统](#users---用户系统)
4. [跨模块依赖关系](#跨模块依赖关系)
5. [核心业务规则汇总](#核心业务规则汇总)
6. [状态机汇总](#状态机汇总)

---

## 系统总览

### 技术栈
- 框架：NestJS 10.4.15
- ORM：Drizzle ORM 0.45.1
- 数据库：PostgreSQL（通过 Supabase）
- 类型校验：Zod 4.3.5
- 对象存储：AWS S3 / Coze SDK
- 运行时：Node.js >= 18

### 架构模式

```
请求 → Controller → Service → Drizzle ORM → PostgreSQL
                         ↕
                   EventBus（发布订阅）
                         ↕
              GlobalStore（前端 SSOT 缓存）
```

- 统一响应拦截器：所有响应包装为 `{ code: 200, data: T, message: 'success' }`
- 全局异常过滤器：错误响应为 `{ code: status, message: string, data: null }`
- 权限模型：天皇（administrator）> 首相（primeMinister）> 议员（member）> 臣民（citizen）

### 已实现后端 Controller 的模块

| 模块 | 状态 | 说明 |
|------|------|------|
| achievements | 完整 | 成就定义与用户进度 |
| admin | 完整 | 系统管理接口 |
| bilibili | 完整 | B站 UID 用户查询 |
| cabinet | 完整 | 内阁组建/解散 |
| diplomacy | 完整 | 外交关系/条约/殖民/战争 |
| history | 完整 | 历史事件记录 |
| ideology | 完整 | 政谱测试与匹配 |
| notification | 完整 | 通知 CRUD |
| parliament | 完整 | 议会/会议/投票 |
| party | 完整 | 政党 CRUD/申请/联盟 |
| search | 完整 | 全局搜索 |
| storage | 完整 | 文件存储 |
| upload | 完整 | 文件上传 |
| users | 完整 | 用户 CRUD |

### 仅有前端 CloudManager 直接操作（无后端 Controller）的模块

| 模块 | 说明 |
|------|------|
| economic | 经济数据展示，手动设置 |
| faction | 派阀管理 |
| military | 军部帷幄 |
| opinion | 舆论监控 |
| treasury | 内帑管理 |
| decree（效果层） | 敕令本身可发布，但无实际游戏效果引擎 |

---

## 数据模型

### PostgreSQL Schema（Drizzle ORM 迁移）

#### ideology_users（用户表 - 核心实体）

```sql
CREATE TABLE "ideology_users" (
  "id" serial PRIMARY KEY NOT NULL,
  "username" text NOT NULL,
  "avatar" text,
  "coordinates" jsonb NOT NULL,           -- 政治光谱四维坐标 {x, y, z, w}
  "is_member" boolean DEFAULT false,      -- 是否为议员
  "member_role" text,                     -- 议员角色
  "member_since" timestamp,
  "party_id" integer,                     -- 所属政党ID
  "party_role" text,                      -- 政党内角色
  "joined_party_at" timestamp,
  "cabinet_id" integer,                   -- 所属内阁ID
  "cabinet_position" text,               -- 内阁职位
  "appointed_at" timestamp,
  "honors" jsonb DEFAULT '[]',           -- 荣誉勋章列表
  "stats" jsonb DEFAULT '{
    "billsProposed": 0,
    "billsPassed": 0,
    "votesCast": 0,
    "attendanceRate": 0,
    "influenceScore": 0
  }',
  "tags" jsonb DEFAULT '[]',
  "notes" text,
  "bilibili_uid" text,                   -- B站UID（外部身份标识）
  "created_at" timestamp NOT NULL,
  "updated_at" timestamp NOT NULL
);
-- 索引
CREATE INDEX "idx_users_party_id" ON "ideology_users" ("party_id");
CREATE INDEX "idx_users_is_member" ON "ideology_users" ("is_member");
```

#### parties（政党表）

```sql
CREATE TABLE "parties" (
  "id" serial PRIMARY KEY NOT NULL,
  "name" text NOT NULL UNIQUE,
  "abbreviation" text NOT NULL,
  "description" text,
  "status" text DEFAULT 'forming' NOT NULL,     -- forming | active | dissolved
  "coordinates" jsonb NOT NULL,                  -- 政治光谱坐标
  "founder_id" integer NOT NULL,
  "leader_id" integer,
  "member_count" integer DEFAULT 0 NOT NULL,
  "required_supporters" integer DEFAULT 15 NOT NULL,  -- 成立所需支持者数
  "expiry_time" timestamp,                       -- 筹建期限
  "established_at" timestamp,
  "seats_held" integer DEFAULT 0 NOT NULL,       -- 持有席位数
  "bills_passed" integer DEFAULT 0 NOT NULL,
  "founded_at" timestamp NOT NULL,
  "dissolved_at" timestamp,
  "dissolution_reason" text,
  "flag" text,
  "color" text,
  "symbol" text,
  "manifesto" text,                              -- 党纲
  "tags" jsonb DEFAULT '[]',
  "recruitment_message" text,
  "created_by" text DEFAULT 'citizen' NOT NULL,
  "is_active" boolean DEFAULT true NOT NULL,
  "created_at" timestamp NOT NULL,
  "updated_at" timestamp NOT NULL
);
CREATE INDEX "idx_party_leader" ON "parties" ("leader_id");
CREATE INDEX "idx_party_founder" ON "parties" ("founder_id");
CREATE INDEX "idx_party_active" ON "parties" ("is_active");
CREATE INDEX "idx_party_status" ON "parties" ("status");
```

#### party_supporters（政党支持者表）

```sql
CREATE TABLE "party_supporters" (
  "id" serial PRIMARY KEY NOT NULL,
  "party_id" integer NOT NULL,
  "user_id" integer NOT NULL,
  "is_founder" boolean DEFAULT false NOT NULL,
  "joined_at" timestamp NOT NULL,
  "created_at" timestamp NOT NULL
);
CREATE INDEX "idx_party_supporters_party" ON "party_supporters" ("party_id");
CREATE INDEX "idx_party_supporters_user" ON "party_supporters" ("user_id");
CREATE INDEX "idx_party_supporters_unique" ON "party_supporters" ("party_id","user_id");
```

#### party_applications（入党申请表）

```sql
CREATE TABLE "party_applications" (
  "id" serial PRIMARY KEY NOT NULL,
  "party_id" integer NOT NULL,
  "applicant_id" integer NOT NULL,
  "application_text" text,
  "status" text DEFAULT 'pending' NOT NULL,   -- pending | approved | rejected
  "approved_by" integer,
  "approved_at" timestamp,
  "created_at" timestamp NOT NULL
);
CREATE INDEX "idx_party_applications_party" ON "party_applications" ("party_id");
CREATE INDEX "idx_party_applications_applicant" ON "party_applications" ("applicant_id");
CREATE INDEX "idx_party_applications_status" ON "party_applications" ("status");
```

#### cabinets（内阁表）

```sql
CREATE TABLE "cabinets" (
  "id" serial PRIMARY KEY NOT NULL,
  "cabinet_name" text NOT NULL,
  "cabinet_number" integer NOT NULL,
  "prime_minister_id" integer NOT NULL,
  "prime_minister_name" text NOT NULL,
  "formed_at" timestamp NOT NULL,
  "dissolved_at" timestamp,
  "ruling_party_id" integer,
  "coalition_parties" jsonb,                -- 联合执政党ID列表
  "approval_rate" numeric DEFAULT '50',     -- 支持率 0-100
  "last_approval_survey_at" timestamp,
  "key_policies" jsonb,                     -- 核心政策列表
  "bills_passed" integer DEFAULT 0,
  "major_achievements" text,
  "is_active" boolean DEFAULT true NOT NULL,
  "created_at" timestamp NOT NULL,
  "updated_at" timestamp NOT NULL
);
CREATE INDEX "idx_cabinet_pm" ON "cabinets" ("prime_minister_id");
CREATE INDEX "idx_cabinet_active" ON "cabinets" ("is_active");
```

#### bills（法案/议案表）

```sql
CREATE TABLE "bills" (
  "id" serial PRIMARY KEY NOT NULL,
  "title" text NOT NULL,
  "content" text NOT NULL,
  "summary" text,
  "bill_type" text NOT NULL,                -- 法案类型
  "status" text DEFAULT 'draft' NOT NULL,   -- draft|proposed|first_reading|second_reading|third_reading|voting|passed|rejected|implemented
  "proposer_id" integer NOT NULL,
  "proposer_type" text NOT NULL,            -- citizen|party|cabinet|emperor
  "proposed_at" timestamp NOT NULL,
  "cosponsors" jsonb,                       -- 联署人列表
  "cabinet_endorsed" boolean DEFAULT false, -- 内阁是否背书
  "cabinet_id" integer,
  "session_id" integer,                     -- 所属会期
  "first_reading_at" timestamp,
  "second_reading_at" timestamp,
  "third_reading_at" timestamp,
  "votes" jsonb,                            -- 投票结果 {support, oppose, abstain, total, rate}
  "amendments" jsonb,                       -- 修正案列表
  "implemented_at" timestamp,
  "implementation_report" text,
  "versions" jsonb,                         -- 版本历史
  "created_at" timestamp NOT NULL,
  "updated_at" timestamp NOT NULL
);
CREATE INDEX "idx_bill_proposer" ON "bills" ("proposer_id");
CREATE INDEX "idx_bill_session" ON "bills" ("session_id");
CREATE INDEX "idx_bill_type" ON "bills" ("bill_type");
CREATE INDEX "idx_bill_status" ON "bills" ("status");
```

#### sessions（议会会期表）

```sql
CREATE TABLE "sessions" (
  "id" serial PRIMARY KEY NOT NULL,
  "session_number" integer NOT NULL,
  "era_name" text NOT NULL,
  "era_year" integer NOT NULL,
  "started_at" timestamp NOT NULL,
  "ended_at" timestamp,
  "total_meetings" integer DEFAULT 0,
  "total_bills" integer DEFAULT 0,
  "bills_passed" integer DEFAULT 0,
  "opening_speech" text,                    -- 开幕致辞
  "closing_speech" text,                    -- 闭幕致辞
  "status" text DEFAULT 'planned' NOT NULL, -- planned|active|adjourned|closed
  "created_at" timestamp NOT NULL
);
CREATE INDEX "idx_session_number" ON "sessions" ("session_number");
CREATE INDEX "idx_session_status" ON "sessions" ("status");
```

#### meetings（会议表）

```sql
CREATE TABLE "meetings" (
  "id" serial PRIMARY KEY NOT NULL,
  "session_id" integer NOT NULL,
  "meeting_number" integer NOT NULL,
  "started_at" timestamp NOT NULL,
  "ended_at" timestamp,
  "attendance" jsonb,                       -- 出席记录
  "agenda" jsonb,                           -- 议程
  "important_debates" jsonb,                -- 重要辩论记录
  "created_at" timestamp NOT NULL
);
CREATE INDEX "idx_meeting_session" ON "meetings" ("session_id");
```

#### achievements（成就定义表）

```sql
CREATE TABLE "achievements" (
  "id" serial PRIMARY KEY NOT NULL,
  "name" text NOT NULL UNIQUE,
  "display_name" text NOT NULL,
  "description" text NOT NULL,
  "type" text NOT NULL,                     -- 成就类型分类
  "rarity" text DEFAULT 'common' NOT NULL,  -- common|uncommon|rare|epic|legendary
  "conditions" jsonb NOT NULL,              -- 解锁条件（结构化规则）
  "rewards" jsonb,                          -- 奖励内容
  "icon" text,
  "is_active" boolean DEFAULT true NOT NULL,
  "created_at" timestamp NOT NULL
);
```

#### user_achievements（用户成就进度表）

```sql
CREATE TABLE "user_achievements" (
  "id" serial PRIMARY KEY NOT NULL,
  "user_id" integer NOT NULL,
  "achievement_id" integer NOT NULL,
  "progress" integer DEFAULT 0 NOT NULL,
  "max_progress" integer DEFAULT 100 NOT NULL,
  "achieved_at" timestamp,                  -- NULL 表示未完成
  "created_at" timestamp NOT NULL
);
CREATE INDEX "idx_user_achievement" ON "user_achievements" ("user_id","achievement_id");
```

#### history_records（历史记录表）

```sql
CREATE TABLE "history_records" (
  "id" serial PRIMARY KEY NOT NULL,
  "event_type" text NOT NULL,               -- 事件类型
  "importance" integer DEFAULT 1 NOT NULL,  -- 重要性 1-5
  "timestamp" timestamp NOT NULL,
  "era_name" text DEFAULT '光谱元年',
  "era_year" integer DEFAULT 1,
  "title" text NOT NULL,
  "description" text NOT NULL,
  "user_id" integer,
  "party_id" integer,
  "cabinet_id" integer,
  "bill_id" integer,
  "session_id" integer,
  "evidence" jsonb,                         -- 证据/附件
  "short_term_impact" text,                 -- 短期影响
  "long_term_impact" text,                  -- 长期影响
  "historical_evaluation" text,             -- 历史评价
  "changes" jsonb,                          -- 变更详情
  "created_at" timestamp NOT NULL
);
CREATE INDEX "idx_history_timestamp" ON "history_records" ("timestamp");
CREATE INDEX "idx_history_type" ON "history_records" ("event_type");
CREATE INDEX "idx_history_importance" ON "history_records" ("importance");
CREATE INDEX "idx_history_user_id" ON "history_records" ("user_id");
CREATE INDEX "idx_history_party_id" ON "history_records" ("party_id");
CREATE INDEX "idx_history_bill_id" ON "history_records" ("bill_id");
```

#### imperial_notifications（通知表）

```sql
CREATE TABLE "imperial_notifications" (
  "id" serial PRIMARY KEY NOT NULL,
  "type" text NOT NULL,                     -- 通知类型
  "status" text DEFAULT 'unread' NOT NULL,  -- unread|read|archived
  "priority" text DEFAULT 'medium' NOT NULL,-- low|medium|high|urgent
  "source" text DEFAULT 'SYSTEM' NOT NULL,  -- 来源系统
  "title" text NOT NULL,
  "content" text NOT NULL,
  "icon" text,
  "created_at" timestamp NOT NULL,
  "expiry_date" timestamp,
  "read_time" timestamp,
  "era_name" text DEFAULT '光谱元年',
  "era_year" integer DEFAULT 1,
  "era_month" integer,
  "era_day" integer,
  "read_count" integer DEFAULT 0 NOT NULL,
  "link" text,                              -- 跳转链接
  "related_id" text,                        -- 关联实体ID
  "related_type" text,                      -- 关联实体类型
  "action_required" boolean DEFAULT false,  -- 是否需要操作
  "tags" jsonb DEFAULT '[]',
  "metadata" jsonb,
  "created_by" integer,
  "is_active" boolean DEFAULT true NOT NULL,
  "updated_at" timestamp NOT NULL
);
CREATE INDEX "idx_notifications_type" ON "imperial_notifications" ("type");
CREATE INDEX "idx_notifications_status" ON "imperial_notifications" ("status");
CREATE INDEX "idx_notifications_priority" ON "imperial_notifications" ("priority");
CREATE INDEX "idx_notifications_created_at" ON "imperial_notifications" ("created_at");
CREATE INDEX "idx_notifications_is_active" ON "imperial_notifications" ("is_active");
CREATE INDEX "idx_notifications_era" ON "imperial_notifications" ("era_name","era_year");
```

#### imperial_settings（帝国设置表 - 全局配置单例）

```sql
CREATE TABLE "imperial_settings" (
  "id" serial PRIMARY KEY NOT NULL,
  "nation_name" text DEFAULT '大光谱帝国' NOT NULL,
  "emperor_title" text DEFAULT '天皇' NOT NULL,
  "emperor_formal_address" text DEFAULT '陛下' NOT NULL,
  "emperor_self_reference" text DEFAULT '朕' NOT NULL,
  "era_name" text DEFAULT '光谱' NOT NULL,
  "era_year" integer DEFAULT 1 NOT NULL,
  "parliament_name" text DEFAULT '帝国议会' NOT NULL,
  "upper_house_name" text DEFAULT '贵族院' NOT NULL,
  "lower_house_name" text DEFAULT '众议院' NOT NULL,
  "member_title" text DEFAULT '议员' NOT NULL,
  "citizen_title" text DEFAULT '臣民' NOT NULL,
  "rank_system" jsonb DEFAULT '[
    {"level":1,"title":"平民"},
    {"level":2,"title":"士族"},
    {"level":3,"title":"华族"}
  ]',
  "honors" jsonb DEFAULT '[
    {"name":"光谱勋章","description":"表彰对帝国的贡献","level":1}
  ]',
  "game_time_speed" integer DEFAULT 1,
  "session_interval" integer DEFAULT 7,       -- 会期间隔（天）
  "election_cycle" integer DEFAULT 90,        -- 选举周期（天）
  "change_history" jsonb,
  "updated_at" timestamp NOT NULL
);
```

### 微信云数据库集合（26个，前端 CloudManager 直接操作）

以下集合存储在微信云开发数据库中，前端通过 CloudManager 直接 CRUD：

| 集合 | 用途 | 对应 PostgreSQL 表 |
|------|------|-------------------|
| parliament_members | 议员数据 | ideology_users (is_member=true) |
| parliament_bills | 议案 | bills |
| parliament_sessions | 投票会话 | sessions |
| parliament_votes | 投票记录 | 无对应（嵌入 bills.votes） |
| parties | 政党 | parties |
| party_alliances | 政党联盟 | 无对应 |
| alliance_votes | 联盟投票 | 无对应 |
| cabinets | 内阁 | cabinets |
| decrees | 敕令 | 无对应 |
| imperial_settings | 帝国设置 | imperial_settings |
| imperial_reports | 帷幄上奏 | 无对应 |
| elections | 选举 | 无对应 |
| factions | 派阀 | 无对应 |
| faction_members | 派阀成员 | 无对应 |
| faction_struggles | 派阀斗争 | 无对应 |
| chronicles | 编年史 | history_records |
| news_articles | 新闻 | 无对应 |
| public_opinion | 舆论 | 无对应 |
| economic_data | 经济数据 | 无对应 |
| zaibatsu | 财阀 | 无对应 |
| countries | 国家 | 无对应 |
| diplomatic_relations | 外交关系 | 无对应 |
| diplomatic_events | 外交事件 | 无对应 |
| treaties | 条约 | 无对应 |
| colonies | 殖民地 | 无对应 |
| wars | 战争 | 无对应 |

---

## 模块详解

---

### achievements - 成就系统

**模块用途**：定义成就条件、追踪用户进度、解锁成就奖励。

**API 端点**：

| 方法 | 路径 | 功能 |
|------|------|------|
| GET | /api/achievements | 获取所有成就定义列表 |
| GET | /api/achievements/:id | 获取单个成就详情 |
| GET | /api/achievements/user/:userId | 获取用户的成就进度列表 |
| POST | /api/achievements | 创建新成就定义（管理员） |
| POST | /api/achievements/check/:userId | 检查并更新用户成就进度 |
| PATCH | /api/achievements/:id | 更新成就定义 |

**核心业务逻辑**：

1. 成就稀有度分级：common / uncommon / rare / epic / legendary
2. 成就条件（conditions）为 JSON 结构化规则，示例：
   ```json
   { "type": "bills_proposed", "threshold": 10 }
   { "type": "votes_cast", "threshold": 50 }
   { "type": "party_founded", "threshold": 1 }
   ```
3. 进度追踪：`progress / max_progress`，当 progress >= max_progress 时标记 achieved_at
4. 奖励（rewards）可包含：荣誉勋章、称号、积分等

**业务规则**：
- 成就一旦解锁不可撤销
- 同一用户同一成就只能有一条进度记录
- 检查成就时需读取用户 stats 字段进行条件匹配

**当前问题**：前端从本地 user.achievements 读取，未调用后端 API。

---

### admin - 管理后台

**模块用途**：提供天皇/首相的系统管理能力。

**API 端点**：

| 方法 | 路径 | 功能 |
|------|------|------|
| GET | /api/admin/stats | 获取系统统计数据 |
| GET | /api/admin/settings | 获取帝国设置 |
| PUT | /api/admin/settings | 更新帝国设置 |
| POST | /api/admin/reset-votes | 重置所有投票状态 |
| POST | /api/admin/sync-data | 同步云端与本地数据 |

**核心业务逻辑**：

1. 权限验证：仅 administrator UID 或 primeMinister UID 可访问
2. 统计数据包含：议员总数、待审议案数、进行中投票数、政党数
3. 帝国设置为全局单例，修改后通过 EventBus 广播 SETTINGS_UPDATED

**权限检查规则**：
```typescript
// 天皇 UID 验证（String 强制转换 + trim）
const isTenno = String(user.bilibiliUid).trim() === String(settings.administrator).trim()
const isPM = String(user.bilibiliUid).trim() === String(settings.primeMinister).trim()
```

---

### bilibili - B站用户集成

**模块用途**：通过 B站 UID 查询用户信息，作为身份验证的外部数据源。

**API 端点**：

| 方法 | 路径 | 功能 |
|------|------|------|
| GET | /api/bilibili/user/:uid | 根据B站UID获取用户公开信息 |
| GET | /api/bilibili/search | 搜索B站用户 |

**核心业务逻辑**：

1. 调用 B站公开 API 获取用户信息（头像、昵称、签名）
2. 用户首次登录时通过 B站 UID 创建本地用户记录
3. 定期同步用户头像和昵称变更

**数据映射**：
- B站 UID → ideology_users.bilibili_uid
- B站昵称 → ideology_users.username
- B站头像 → ideology_users.avatar

---

### cabinet - 内阁系统

**模块用途**：管理内阁组建、大臣任命/解任、内阁总辞。

**API 端点**：

| 方法 | 路径 | 功能 |
|------|------|------|
| GET | /api/cabinet | 获取当前活跃内阁 |
| GET | /api/cabinet/history | 获取历届内阁列表 |
| GET | /api/cabinet/:id | 获取指定内阁详情 |
| POST | /api/cabinet | 组建新内阁 |
| POST | /api/cabinet/:id/appoint | 任命大臣 |
| POST | /api/cabinet/:id/dismiss | 解任大臣 |
| POST | /api/cabinet/:id/dissolve | 内阁总辞 |
| PATCH | /api/cabinet/:id | 更新内阁信息 |

**核心业务逻辑**：

1. **组阁规则**：
   - 仅天皇可任命首相
   - 首相可任命各部大臣
   - 同一时间只能有一个活跃内阁（is_active=true）
   - 组阁时自动将前任内阁设为 dissolved

2. **内阁职位**（ministers JSON 结构）：
   ```json
   [
     { "position": "外务大臣", "uid": "xxx", "displayName": "xxx", "status": "active" },
     { "position": "大蔵大臣", "uid": "xxx", "displayName": "xxx", "status": "active" },
     { "position": "陸軍大臣", "uid": "xxx", "displayName": "xxx", "status": "active" },
     { "position": "海軍大臣", "uid": "xxx", "displayName": "xxx", "status": "active" }
   ]
   ```

3. **内阁总辞流程**：
   - 设置 dissolved_at = now()
   - 设置 is_active = false
   - 清除所有大臣的 cabinet_id 和 cabinet_position
   - 记录历史事件
   - 发布 CABINET_UPDATED 事件

4. **支持率计算**：
   - approval_rate 默认 50
   - 通过定期调查更新（last_approval_survey_at）
   - 前端显示为可视化进度条

**云数据库结构**（cabinets 集合）：
```javascript
{
  cabinetName: "第X次内阁",
  status: "active" | "dissolved",
  primeMinister: { bilibiliUid, displayName, avatar },
  ministers: [{ position, bilibiliUid, displayName, avatar, status }],
  createdAt: timestamp
}
```

---

### decree - 敕令系统

**模块用途**：天皇发布/废除敕令，敕令类型包括任命、解散议会、紧急状态等。

**API 端点**：

| 方法 | 路径 | 功能 |
|------|------|------|
| GET | /api/decrees | 获取所有敕令列表 |
| GET | /api/decrees/active | 获取当前生效的敕令 |
| GET | /api/decrees/:id | 获取敕令详情 |
| POST | /api/decrees | 发布新敕令 |
| POST | /api/decrees/:id/revoke | 废除敕令 |

**核心业务逻辑**：

1. **敕令类型**：
   - `appointment` - 任命（任命首相、大臣等）
   - `dissolution` - 解散议会
   - `emergency` - 紧急状态宣布
   - `legislation` - 立法敕令（绕过议会直接立法）
   - `honor` - 授勋
   - `general` - 一般性敕令

2. **敕令状态机**：
   ```
   issued → active → expired/revoked
   ```

3. **权限规则**：
   - 仅天皇（administrator）可发布敕令
   - 仅天皇可废除敕令
   - 敕令发布后自动记录到编年史

4. **敕令效果**（当前未实现，仅文本记录）：
   - 任命敕令应触发人事变动
   - 解散议会应重置议会状态
   - 紧急状态应限制某些操作

**云数据库结构**（decrees 集合）：
```javascript
{
  decreeId: "唯一ID",
  decreeNumber: "敕令编号（如：光谱第1号）",
  type: "appointment|dissolution|emergency|legislation|honor|general",
  title: "敕令标题",
  content: "敕令正文",
  status: "issued|active|expired|revoked",
  issuedAt: timestamp,
  createdAt: timestamp
}
```

---

### diplomacy - 外交系统

**模块用途**：管理国际关系、条约、殖民地、战争。

**API 端点**：

| 方法 | 路径 | 功能 |
|------|------|------|
| GET | /api/diplomacy/countries | 获取所有国家列表 |
| GET | /api/diplomacy/countries/:id | 获取国家详情 |
| GET | /api/diplomacy/relations | 获取所有外交关系 |
| GET | /api/diplomacy/relations/:countryId | 获取与指定国家的关系 |
| POST | /api/diplomacy/relations | 建立/修改外交关系 |
| GET | /api/diplomacy/treaties | 获取所有条约 |
| POST | /api/diplomacy/treaties | 签订条约 |
| PATCH | /api/diplomacy/treaties/:id | 更新条约状态 |
| GET | /api/diplomacy/colonies | 获取殖民地列表 |
| POST | /api/diplomacy/colonies | 建立殖民地 |
| GET | /api/diplomacy/wars | 获取战争列表 |
| POST | /api/diplomacy/wars | 宣战 |
| POST | /api/diplomacy/wars/:id/peace | 签订和约 |
| GET | /api/diplomacy/events | 获取外交事件 |

**核心业务逻辑**：

1. **外交关系值**：-200 到 +200
   - 关系改善/恶化通过外交事件触发
   - 关系值影响可执行的外交行动

2. **条约类型**：
   - 互不侵犯条约
   - 军事同盟
   - 贸易协定
   - 附庸条约
   - 和平条约

3. **殖民地管理**：
   - 殖民地有独立度属性
   - 可设置总督
   - 可调整税率

4. **战争系统**：
   - 宣战需要理由（Casus Belli）
   - 战争有参战方列表
   - 和约可包含割地、赔款、附庸等条款

**云数据库结构**：
```javascript
// diplomatic_relations
{
  country1: "国家1ID",
  country2: "国家2ID",
  relationValue: -200~200,
  status: "peace|war|alliance|vassal",
  treaties: ["条约ID列表"]
}

// wars
{
  warId: "战争ID",
  name: "战争名称",
  attackers: ["进攻方国家ID"],
  defenders: ["防御方国家ID"],
  status: "active|ended",
  startedAt: timestamp,
  endedAt: timestamp,
  peaceTerms: { ... }
}
```

---

### economic - 经济系统

**模块用途**：管理帝国经济数据、GDP、财政收支、财阀。

**后端状态**：无后端 Controller，前端通过 cloudManager 直接操作 economic_data 和 zaibatsu 集合。

**业务逻辑（前端实现）**：

1. **经济指标**：
   - GDP（手动设置，无自动计算）
   - 增长率
   - 通胀率
   - 失业率
   - 财政收入/支出

2. **财阀系统**（zaibatsu 集合）：
   ```javascript
   {
     name: "财阀名称",
     industry: "行业",
     assets: 数值,
     influence: 0-100,
     politicalDonations: [{ partyId, amount, date }],
     status: "active|dissolved"
   }
   ```

3. **经济政策**（仅 UI，无实际效果）：
   - 税率调整
   - 贸易政策
   - 产业政策

**迁移建议**：需要实现经济计算引擎，每日 tick 更新经济指标。

---

### faction - 派阀系统

**模块用途**：管理政治派阀的创建、成员招募、派阀斗争。

**后端状态**：无后端 Controller，前端通过 cloudManager 操作。

**业务逻辑（前端 FactionManager 实现）**：

1. **派阀属性**：
   ```javascript
   {
     name: "派阀名称",
     description: "描述",
     leader: "领导者UID",
     members: ["成员UID列表"],
     influence: 0-100,        // 影响力
     ideology: "保守|改革|中立",
     demands: ["诉求列表"],
     satisfaction: 0-100,     // 满意度
     createdAt: timestamp
   }
   ```

2. **派阀成员**（faction_members 集合）：
   ```javascript
   {
     factionId: "派阀ID",
     userId: "用户UID",
     role: "leader|elder|member",
     joinedAt: timestamp
   }
   ```

3. **派阀斗争**（faction_struggles 集合）：
   ```javascript
   {
     attackerId: "发起方派阀ID",
     defenderId: "防御方派阀ID",
     type: "influence|recruitment|policy",
     status: "active|resolved",
     result: "attacker_win|defender_win|draw",
     createdAt: timestamp
   }
   ```

4. **业务规则**：
   - 一个用户只能属于一个派阀
   - 派阀领袖可招募成员
   - 派阀满意度影响政权稳定性（未实现）
   - 派阀斗争可改变影响力分配（部分实现）

---

### history - 史官系统

**模块用途**：记录帝国所有重要历史事件，支持按类型/时间/重要性筛选。

**API 端点**：

| 方法 | 路径 | 功能 |
|------|------|------|
| GET | /api/history | 获取历史事件列表（支持分页/筛选） |
| GET | /api/history/:id | 获取事件详情 |
| POST | /api/history | 记录新历史事件 |
| GET | /api/history/timeline | 获取时间线视图 |
| GET | /api/history/stats | 获取历史统计 |

**核心业务逻辑**：

1. **事件类型**：
   - `cabinet_formed` - 内阁组建
   - `cabinet_dissolved` - 内阁解散
   - `bill_passed` - 法案通过
   - `bill_rejected` - 法案否决
   - `decree_issued` - 敕令发布
   - `party_founded` - 政党成立
   - `party_dissolved` - 政党解散
   - `war_declared` - 宣战
   - `peace_signed` - 和约签订
   - `election_held` - 选举举行
   - `member_appointed` - 议员任命
   - `honor_awarded` - 授勋

2. **重要性分级**：1-5（1=日常，5=改朝换代级别）

3. **自动记录规则**：
   - 内阁变动 → 自动记录（importance=4）
   - 法案通过/否决 → 自动记录（importance=3）
   - 敕令发布 → 自动记录（importance=4）
   - 政党成立/解散 → 自动记录（importance=3）
   - 战争/和约 → 自动记录（importance=5）

4. **纪年系统**：使用 era_name + era_year 标记（如"光谱元年"）

**当前问题**：前端使用本地 ImperialHistorian，未与后端 API 对接。

---

### ideology - 意识形态系统

**模块用途**：政治光谱测试、意识形态坐标计算、意识形态匹配。

**API 端点**：

| 方法 | 路径 | 功能 |
|------|------|------|
| GET | /api/ideology/questions | 获取测试题目 |
| POST | /api/ideology/calculate | 计算政治光谱坐标 |
| POST | /api/ideology/match | 匹配最接近的意识形态 |
| GET | /api/ideology/users | 获取所有用户及坐标 |
| POST | /api/ideology/users | 创建/更新用户坐标 |

**核心业务逻辑**：

1. **四维政治光谱坐标**：
   ```typescript
   interface Coordinates {
     x: number  // 经济轴：-10(计划经济) 到 +10(自由市场)
     y: number  // 社会轴：-10(威权) 到 +10(自由)
     z: number  // 外交轴：-10(国际主义) 到 +10(民族主义)（可选）
     w: number  // 文化轴：-10(进步) 到 +10(保守)（可选）
   }
   ```

2. **坐标计算算法**：
   - 根据用户对一系列问题的回答（1-5 量表）
   - 每个问题对各轴有不同权重
   - 最终坐标 = 各问题加权平均

3. **意识形态匹配**：
   - 计算用户坐标与预定义意识形态模板的欧几里得距离
   - 返回最接近的意识形态名称和匹配度

4. **政党坐标匹配**：
   - 政党也有 coordinates 字段
   - 可计算用户与政党的意识形态距离
   - 用于推荐政党

---

### military - 军部帷幄

**模块用途**：军队管理、军事行动、帷幄上奏（向天皇汇报军情）。

**后端状态**：无后端 Controller。前端使用 ImperialSystemsManager 提供固定数据。

**业务逻辑（前端实现，数据为固定值）**：

1. **军队统计**：
   - 陆军影响力
   - 海军影响力
   - 兵力总数
   - 军费占比

2. **帷幄上奏**（imperial_reports 集合）：
   ```javascript
   {
     branch: "army|navy",
     content: "报告内容",
     urgency: "low|normal|high|urgent",
     submittedBy: "提交者UID",
     status: "pending|reviewed",
     reviewedBy: "批示人UID",
     reviewContent: "批示内容",
     createdAt: timestamp
   }
   ```

3. **帷幄上奏流程**：
   - 军部官员提交上奏（branch + content + urgency）
   - 天皇查看并批示
   - 批示后 status 变为 reviewed

4. **未实现功能**：
   - 军事行动系统
   - 军费预算分配
   - 军事演习
   - 军官晋升系统
   - 征兵系统

---

### notification - 通知系统

**模块用途**：系统通知的创建、查询、标记已读。

**API 端点**：

| 方法 | 路径 | 功能 |
|------|------|------|
| GET | /api/notifications | 获取通知列表（分页） |
| GET | /api/notifications/unread | 获取未读通知数量 |
| GET | /api/notifications/:id | 获取通知详情 |
| POST | /api/notifications | 创建通知 |
| PATCH | /api/notifications/:id/read | 标记已读 |
| PATCH | /api/notifications/read-all | 全部标记已读 |
| DELETE | /api/notifications/:id | 删除通知 |

**核心业务逻辑**：

1. **通知类型**：
   - `urgent` - 紧急通知
   - `achievement` - 成就解锁
   - `system` - 系统通知
   - `history` - 历史事件
   - `decree` - 敕令通知
   - `parliament` - 议会通知
   - `party` - 政党通知
   - `cabinet` - 内阁通知

2. **优先级**：low / medium / high / urgent

3. **通知生命周期**：
   ```
   created(unread) → read → archived
                   → expired（到达 expiry_date）
   ```

4. **自动通知触发**：
   - 敕令发布 → 全体通知
   - 内阁变动 → 相关人员通知
   - 法案状态变更 → 提案人通知
   - 政党申请审批 → 申请人通知
   - 投票开始 → 全体议员通知

5. **纪年标记**：通知记录 era_name + era_year + era_month + era_day

---

### opinion - 舆论系统

**模块用途**：监控各阶层民意、发布新闻、舆论引导。

**后端状态**：无后端 Controller。前端通过 cloudManager 操作。

**业务逻辑（前端实现）**：

1. **舆论指数**（public_opinion 集合）：
   ```javascript
   {
     category: "nobility|military|merchants|peasants|intellectuals",
     supportRate: 0-100,       // 对政府支持率
     trend: "rising|stable|falling",
     lastUpdated: timestamp
   }
   ```

2. **新闻系统**（news_articles 集合）：
   ```javascript
   {
     title: "新闻标题",
     content: "新闻内容",
     author: "作者UID",
     category: "politics|economy|military|society|culture",
     publishedAt: timestamp,
     views: 0,
     reactions: { like: 0, dislike: 0 }
   }
   ```

3. **舆论影响规则**（未实现）：
   - 新闻发布影响对应阶层支持率
   - 政策实施影响舆论
   - 战争胜负影响舆论
   - 经济状况影响舆论

---

### parliament - 议会系统

**模块用途**：两院制议会管理、会期、投票、议案审议。

**API 端点**：

| 方法 | 路径 | 功能 |
|------|------|------|
| GET | /api/parliament/members | 获取所有议员 |
| GET | /api/parliament/members/:id | 获取议员详情 |
| POST | /api/parliament/members | 添加议员 |
| PATCH | /api/parliament/members/:id | 更新议员信息 |
| DELETE | /api/parliament/members/:id | 移除议员 |
| POST | /api/parliament/members/:id/transfer | 转移议员到其他议院 |
| GET | /api/parliament/sessions | 获取会期列表 |
| GET | /api/parliament/sessions/current | 获取当前会期 |
| POST | /api/parliament/sessions | 开启新会期 |
| POST | /api/parliament/sessions/:id/close | 关闭会期 |
| GET | /api/parliament/bills | 获取议案列表 |
| GET | /api/parliament/bills/:id | 获取议案详情 |
| POST | /api/parliament/bills | 提交议案 |
| POST | /api/parliament/bills/:id/vote | 对议案投票 |
| POST | /api/parliament/voting/start | 开始投票 |
| POST | /api/parliament/voting/end | 结束投票 |
| POST | /api/parliament/voting/reset | 重置投票 |
| GET | /api/parliament/stats | 获取议会统计 |

**核心业务逻辑**：

1. **两院制结构**：
   - 贵族院（上院）：终身议员(20席) + 功勋议员(40席) + 敕任议员(40席)
   - 众议院（下院）：200-300席，按人口比例

2. **议员分类规则**：
   ```typescript
   // 管理员不入议会
   const members = subjects.filter(s => !s.isAdmin)
   
   // 贵族院：chamber === 'upper'
   const upperMembers = members.filter(m => m.chamber === 'upper')
   // 按 peerType 细分：lifetime / meritorious / imperial
   
   // 众议院：未设置或 chamber === 'lower'
   const lowerMembers = members.filter(m => !m.chamber || m.chamber === 'lower')
   ```

3. **互斥原则**：用户只能在一个议院，转移时自动从原议院移除

4. **投票流程**：
   ```
   1. 管理员创建议案 (status: 'pending')
   2. 管理员开始投票 (status: 'voting')
      - 创建投票会话 (parliament_sessions, isActive: true)
      - 重置所有议员 currentVote = 'abstain'
   3. 议员投票 (castVote)
      - 验证：用户是否是议员
      - 验证：投票会话是否激活
      - 更新 currentVote: 'support' | 'oppose' | 'abstain'
      - 记录到 parliament_votes
   4. 管理员结束投票
      - 统计票数
      - 计算支持率 = supportVotes / totalVotes * 100
      - 判定结果：supportRate > 50 → passed，否则 rejected
      - 更新议案 status 和 result
      - 关闭投票会话 (isActive: false)
   ```

5. **投票结果计算**：
   ```typescript
   interface VotingResult {
     totalVotes: number
     supportVotes: number
     opposeVotes: number
     abstainVotes: number
     supportRate: number        // 百分比
     result: 'passed' | 'rejected' | 'draw'
   }
   // 通过条件：supportRate > 50
   // 平局条件：supportVotes === opposeVotes
   ```

6. **投票约束**：
   - 同一议案同一用户只能投一票（复合唯一索引）
   - 任何时刻只能有一个活跃投票会话
   - 投票时长默认 24 小时（DEFAULT_VOTING_DURATION = 86400000ms）

7. **议案状态机**：
   ```
   draft → proposed → first_reading → second_reading → third_reading → voting → passed/rejected → implemented
   ```
   简化版（当前实现）：
   ```
   pending → voting → passed/rejected
   ```

8. **会期管理**：
   - 会期有编号（session_number）
   - 会期状态：planned → active → adjourned → closed
   - 会期内可有多次会议（meetings）
   - 会期统计：total_meetings, total_bills, bills_passed

---

### party - 政党系统

**模块用途**：政党创建、加入、管理、联盟、解散。

**API 端点**：

| 方法 | 路径 | 功能 |
|------|------|------|
| GET | /api/parties | 获取所有政党列表 |
| GET | /api/parties/:id | 获取政党详情 |
| POST | /api/parties | 创建政党（进入筹建期） |
| PATCH | /api/parties/:id | 更新政党信息 |
| DELETE | /api/parties/:id | 解散政党 |
| POST | /api/parties/:id/support | 支持政党（筹建期） |
| POST | /api/parties/:id/apply | 申请加入政党 |
| POST | /api/parties/:id/applications/:appId/approve | 批准入党申请 |
| POST | /api/parties/:id/applications/:appId/reject | 拒绝入党申请 |
| POST | /api/parties/:id/leave | 退出政党 |
| POST | /api/parties/:id/transfer-leader | 转让党魁 |

**核心业务逻辑**：

1. **政党创建流程**：
   ```
   1. 用户提交创建请求（名称、缩写、描述、政治坐标、党纲）
   2. 政党进入 'forming' 状态
   3. 设置 required_supporters = 15（默认）
   4. 设置 expiry_time（筹建期限）
   5. 创建者自动成为第一个支持者（is_founder=true）
   6. 当支持者数 >= required_supporters 时：
      - status 变为 'active'
      - 设置 established_at
      - 创建者成为 leader
   7. 若到达 expiry_time 仍未达标：政党自动解散
   ```

2. **政党状态机**：
   ```
   forming → active → dissolved
              ↑
              └── 支持者达标自动转换
   ```

3. **入党规则**：
   - 一个用户只能属于一个政党
   - 加入需要申请，由党魁/管理员审批
   - 退出立即生效
   - 退出后 user.party_id 清空

4. **政党联盟**（party_alliances 集合）：
   ```javascript
   {
     allianceId: "联盟ID",
     name: "联盟名称",
     currentParties: ["政党ID数组"],
     leaderParty: "盟主政党ID",
     status: "active|dissolved",
     createdAt: timestamp
   }
   ```

5. **联盟投票**（alliance_votes 集合）：
   ```javascript
   {
     allianceId: "联盟ID",
     issue: "议题",
     options: [{ id, text }],
     votes: [{ partyId, option, weight }],  // 按政党规模加权
     status: "pending|active|ended"
   }
   ```

6. **政党解散规则**：
   - 党魁可主动解散
   - 天皇可强制解散
   - 成员数降为 0 自动解散
   - 解散时记录 dissolution_reason

---

### search - 搜索系统

**模块用途**：全局搜索用户、政党、议案等实体。

**API 端点**：

| 方法 | 路径 | 功能 |
|------|------|------|
| GET | /api/search | 全局搜索（query 参数） |
| GET | /api/search/users | 搜索用户 |
| GET | /api/search/parties | 搜索政党 |
| GET | /api/search/bills | 搜索议案 |

**核心业务逻辑**：
- 支持模糊匹配（用户名、政党名、议案标题）
- 返回结果按相关度排序
- 支持分页

---

### storage - 存储系统

**模块用途**：文件存储管理（基于 AWS S3 / Coze SDK）。

**API 端点**：

| 方法 | 路径 | 功能 |
|------|------|------|
| GET | /api/storage/files | 获取文件列表 |
| GET | /api/storage/files/:key | 获取文件访问URL |
| DELETE | /api/storage/files/:key | 删除文件 |

**核心业务逻辑**：
- 使用 AWS S3 SDK 进行对象存储
- 文件按类型分目录存储（avatars/, qrcodes/, documents/）
- 生成预签名 URL 供前端直接访问

---

### treasury - 内帑系统

**模块用途**：帝国金库管理、贡献验证、收支记录。

**后端状态**：无后端 Controller。前端通过 cloudManager 操作。

**业务逻辑（前端实现）**：

1. **内帑功能**：
   - 上传收款二维码（用于接受臣民贡献）
   - 贡献验证（部分实现）
   - 余额显示
   - 收支记录（仅 UI）

2. **贡献流程**（设计但未完整实现）：
   ```
   1. 臣民扫描二维码付款
   2. 臣民上传付款截图
   3. 管理员验证截图
   4. 确认后记录贡献
   5. 更新内帑余额
   ```

---

### upload - 上传系统

**模块用途**：文件上传处理（头像、二维码、文档等）。

**API 端点**：

| 方法 | 路径 | 功能 |
|------|------|------|
| POST | /api/upload | 上传文件 |
| POST | /api/upload/avatar | 上传头像 |
| POST | /api/upload/qrcode | 上传二维码 |

**核心业务逻辑**：
- 基于 Coze 存储 SDK 实现
- 文件大小限制
- 支持图片格式校验
- 上传后返回可访问 URL
- 头像上传后自动更新用户 avatar 字段

---

### users - 用户系统

**模块用途**：用户 CRUD、角色管理、统计数据。

**API 端点**：

| 方法 | 路径 | 功能 |
|------|------|------|
| GET | /api/users | 获取用户列表 |
| GET | /api/users/:id | 获取用户详情 |
| POST | /api/users | 创建用户 |
| PATCH | /api/users/:id | 更新用户信息 |
| DELETE | /api/users/:id | 删除用户 |
| GET | /api/users/:id/stats | 获取用户统计 |
| POST | /api/users/:id/honors | 授予荣誉 |
| PATCH | /api/users/:id/role | 更新用户角色 |

**核心业务逻辑**：

1. **用户角色层级**：
   ```
   emperor（天皇）> prime_minister（首相）> parliament_member（议员）> citizen（臣民）
   ```

2. **用户统计字段**（stats JSON）：
   ```json
   {
     "billsProposed": 0,    // 提案数
     "billsPassed": 0,      // 通过的提案数
     "votesCast": 0,        // 投票次数
     "attendanceRate": 0,   // 出席率 (0-100)
     "influenceScore": 0    // 影响力分数
   }
   ```

3. **荣誉系统**（honors JSON 数组）：
   ```json
   [
     { "name": "光谱勋章", "description": "表彰对帝国的贡献", "level": 1, "awardedAt": "timestamp" }
   ]
   ```

4. **位阶系统**（rank_system 在 imperial_settings 中定义）：
   ```json
   [
     { "level": 1, "title": "平民" },
     { "level": 2, "title": "士族" },
     { "level": 3, "title": "华族" }
   ]
   ```

---

### db - 数据库模块

**模块用途**：Drizzle ORM 配置、数据库连接、Schema 定义。

**技术细节**：
- 使用 PostgreSQL（通过 Supabase 托管）
- Drizzle ORM 进行类型安全的数据库操作
- drizzle-zod 生成运行时校验 schema
- 迁移文件在 `server/migrations/`

---

### interceptors - 拦截器模块

**模块用途**：全局请求/响应拦截。

**实现**：
```typescript
// TransformInterceptor - 统一响应格式
{
  code: 200,
  data: T,
  message: 'success'
}

// HttpExceptionFilter - 统一错误格式
{
  code: statusCode,
  message: string,
  data: null
}
```

---

### utils - 工具模块

**模块用途**：通用工具函数。

**包含**：
- 日期格式化（纪年转换）
- 分页辅助
- 权限检查辅助
- 数据转换辅助

---

### scripts - 脚本模块

**模块用途**：数据库迁移脚本、种子数据、维护脚本。

---

## 跨模块依赖关系

```
users ←── parliament（议员是用户子集）
users ←── party（政党成员是用户）
users ←── cabinet（大臣是用户）
users ←── achievements（成就属于用户）
users ←── ideology（坐标属于用户）

party ←── parliament（政党在议会中有席位）
party ←── cabinet（执政党组阁）

cabinet ←── parliament（内阁需要议会信任）
cabinet ←── party（联合执政）

bills ←── parliament（议案在议会审议）
bills ←── sessions（议案属于会期）
bills ←── cabinet（内阁可背书议案）

history ←── 所有模块（记录所有重要事件）
notification ←── 所有模块（各模块触发通知）

diplomacy ←── military（战争关联军事）
diplomacy ←── economic（贸易关联经济）
```

---

## 核心业务规则汇总

### 权限规则

| 规则 | 说明 |
|------|------|
| 天皇唯一性 | 同一时间只有一个 administrator UID |
| 首相唯一性 | 同一时间只有一个 primeMinister UID |
| 天皇不入议会 | isAdmin=true 的用户不参与投票 |
| 天皇可任命首相 | 仅天皇可修改 primeMinister UID |
| 首相可组阁 | 首相可任命/解任大臣 |
| 议员互斥 | 用户只能在一个议院 |
| 政党互斥 | 用户只能属于一个政党 |
| 派阀互斥 | 用户只能属于一个派阀 |

### 数值规则

| 规则 | 值 |
|------|------|
| 投票时长 | 24小时（86400000ms） |
| 缓存过期 | 5分钟（300000ms） |
| 政党成立门槛 | 15名支持者 |
| 贵族院终身席位 | 20席 |
| 贵族院功勋席位 | 40席 |
| 贵族院敕任席位 | 40席 |
| 众议院席位 | 200-300席 |
| 外交关系值范围 | -200 到 +200 |
| 支持率范围 | 0-100 |
| 重要性分级 | 1-5 |
| 会期间隔 | 7天 |
| 选举周期 | 90天 |

### 计算公式

| 计算 | 公式 |
|------|------|
| 投票支持率 | supportVotes / totalVotes * 100 |
| 议案通过条件 | supportRate > 50% |
| 成就完成条件 | progress >= max_progress |
| 意识形态距离 | sqrt((x1-x2)^2 + (y1-y2)^2 + ...) |

---

## 状态机汇总

### 议案状态机
```
draft → proposed → first_reading → second_reading → third_reading → voting → passed → implemented
                                                                           → rejected
简化版（当前实现）：
pending → voting → passed/rejected
```

### 政党状态机
```
forming ──(支持者>=15)──→ active ──(解散)──→ dissolved
   │                                            ↑
   └──(超时未达标)──────────────────────────────┘
```

### 敕令状态机
```
issued → active → expired
                → revoked
```

### 内阁状态机
```
active → dissolved（总辞/新内阁组建时）
```

### 投票会话状态机
```
created(isActive=true) → ended(isActive=false)
```

### 会期状态机
```
planned → active → adjourned → closed
```

### 通知状态机
```
unread → read → archived
       → expired（到达 expiry_date）
```

### 入党申请状态机
```
pending → approved
        → rejected
```

### 战争状态机
```
active → ended（签订和约）
```

### 帷幄上奏状态机
```
pending → reviewed（天皇批示后）
```

---

## 附录：默认帝国配置常量

```typescript
const IMPERIAL_DEFAULTS = {
  // 核心 UID
  ADMINISTRATOR_UID: '3461570143193870',    // 天皇
  PRIME_MINISTER_UID: '240847721',          // 首相
  
  // 帝国名称体系
  empireName: 'παράδεισος',
  parliamentName: '帝国議会',
  upperHouseName: '貴族院',
  lowerHouseName: '衆議院',
  headOfStateTitle: '天皇陛下',
  headOfStateSelfReference: '朕',
  headOfStateHonorific: '陛下',
  subjectTitle: '帝国臣民',
  currencyName: '円',
  eraName: '第',
  eraYear: 1,
  cabinetName: '内閣',
  ministryName: '省',
  courtName: '裁判所',
  treasuryName: '内帑',
  partyName: '政黨',
  gazetteName: '帝国報',
  plazaName: '御前広場',
  academyName: '帝国学堂',
  stationName: '驿',
  emperorName: '天皇',
  imperialFamily: '皇室',
  imperialGuard: '近衛',
  
  // 系统常量
  DEFAULT_VOTING_DURATION: 24 * 60 * 60 * 1000,  // 24小时
  CACHE_EXPIRY: 5 * 60 * 1000,                   // 5分钟
  DATABASE_NAME: 'imperial_parliament',
  
  // 议会席位配置
  PARLIAMENT_CONFIG: {
    upperHouse: {
      lifetime: { maxSeats: 20, columns: 4, name: '終身議員' },
      meritorious: { maxSeats: 40, columns: 5, name: '功勳議員' },
      imperial: { maxSeats: 40, columns: 5, name: '敕任議員' }
    },
    lowerHouse: { maxSeats: 200, columns: 10, name: '衆議院' }
  }
}
```

---

## 附录：EventBus 事件完整列表

| 事件 | 触发时机 | 携带数据 |
|------|----------|----------|
| cabinet:updated | 内阁信息变更 | Cabinet 对象 |
| cabinet:member:appointed | 新大臣上任 | { position, member } |
| cabinet:member:removed | 大臣卸任 | { position, member } |
| cabinet:meeting:started | 内阁会议开始 | Meeting 对象 |
| parliament:member:added | 新议员加入 | Member 对象 |
| parliament:member:removed | 议员离开 | { memberId } |
| parliament:session:started | 会议开幕 | Session 对象 |
| parliament:session:ended | 会议闭幕 | Session 对象 |
| bill:created | 新法案提交 | Bill 对象 |
| bill:status:changed | 法案状态流转 | { billId, oldStatus, newStatus } |
| bill:voting:started | 投票开启 | { billId, session } |
| bill:voting:ended | 投票截止 | { billId, result } |
| vote:cast | 用户投票 | { userId, billId, vote } |
| vote:result:updated | 投票结果更新 | VotingResult 对象 |
| party:created | 新政党成立 | Party 对象 |
| party:updated | 政党信息变更 | Party 对象 |
| party:dissolved | 政党解散 | { partyId, reason } |
| party:member:joined | 新成员加入 | { partyId, userId } |
| party:member:left | 成员退出 | { partyId, userId } |
| settings:updated | 系统设置变更 | Settings 对象 |
| settings:administrator:changed | 天皇变更 | { oldUid, newUid } |
| settings:primeMinister:changed | 首相变更 | { oldUid, newUid } |
| decree:issued | 敕令发布 | Decree 对象 |
| decree:revoked | 敕令废除 | { decreeId } |
| notification:new | 收到通知 | Notification 对象 |
| notification:read | 标记已读 | { notificationId } |
| user:login | 登录成功 | User 对象 |
| user:logout | 登出成功 | { userId } |
| user:permission:changed | 角色变更 | { userId, oldRole, newRole } |
| data:sync:start | 开始同步 | null |
| data:sync:complete | 同步成功 | { timestamp } |
| data:sync:error | 同步失败 | { error } |

---

> 文档结束。本报告完整覆盖了 Parliamentary-Simulation 后端的所有业务逻辑、数据模型、状态转换和计算规则，可作为 Unity/C# 迁移的权威参考。
