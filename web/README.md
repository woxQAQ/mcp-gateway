# MCP Gateway 管理系统

基于 Vue 3 + TypeScript + Element Plus 的现代化管理后台系统。

## 🎨 设计特性

### 🚀 技术栈

- **Vue 3** - 渐进式 JavaScript 框架
- **TypeScript** - 类型安全的 JavaScript 超集
- **Element Plus** - 企业级 Vue 3 组件库
- **Vite** - 下一代前端构建工具
- **Pinia** - Vue 状态管理库（计划集成）

### 💎 UI 组件库升级

#### 从自定义组件迁移到 Element Plus

**之前：**

- 自定义 UnoCSS 样式
- 手工制作的组件
- 复杂的样式维护

**现在：**

- 企业级 Element Plus 组件
- 统一的设计语言
- 完善的可访问性支持

### 🏗️ 组件架构

#### 1. 布局组件 (Layout.vue)

- 使用 `el-container`、`el-header`、`el-aside`、`el-main`
- 响应式侧边栏折叠
- 移动端适配

#### 2. 顶部导航 (Header.vue)

- `el-button` 菜单切换
- `el-dropdown` 用户菜单
- `el-badge` 通知徽章
- `el-avatar` 用户头像

#### 3. 侧边栏导航 (Sidebar.vue)

- `el-menu` 导航菜单
- `el-menu-item` 菜单项
- `el-badge` 状态徽章
- `el-divider` 分割线

#### 4. 仪表板 (Dashboard.vue)

- `el-page-header` 页面标题
- `el-card` 统计卡片
- `el-row`、`el-col` 网格布局
- `el-timeline` 活动时间线
- `el-button-group` 操作按钮组

### 🎯 功能特性

#### ✨ 现代化界面

- 渐变背景和阴影效果
- 平滑动画过渡
- 响应式设计
- 暗色主题支持

#### 📱 响应式设计

- 移动端优化
- 平板适配
- 桌面端完整功能

#### 🎨 主题定制

- Element Plus 主题变量
- 自定义颜色方案
- 暗色模式支持

### 📊 仪表板功能

#### 📈 统计面板

- MCP 配置数量: 12 (+8%)
- 活跃工具: 24 (+12%)
- 在线服务器: 8 (-2%)
- 系统用户: 156 (+5%)

#### 📋 活动时间线

- 实时系统活动
- 多种状态类型（成功、警告、错误、信息）
- 时间戳显示

#### ⚡ 快速操作

- 创建 MCP 配置
- 添加工具
- 查看日志

### 🛠️ 开发指南

#### 安装依赖

\`\`\`bash
pnpm install
\`\`\`

#### 启动开发服务器

\`\`\`bash
pnpm run dev
\`\`\`

#### 构建生产版本

\`\`\`bash
pnpm run build
\`\`\`

### 📁 项目结构

\`\`\`
src/
├── components/ # Vue 组件
│ ├── Layout.vue # 主布局
│ ├── Header.vue # 顶部导航
│ ├── Sidebar.vue # 侧边栏
│ └── Dashboard.vue # 仪表板
├── api/ # API 接口
├── generated/ # 自动生成的代码
└── style.css # 全局样式
\`\`\`

### 🔧 配置说明

#### Element Plus 配置

- 全局导入组件库
- 图标组件注册
- 主题变量定制

#### 样式覆盖

- 自定义滚动条
- 菜单项圆角
- 卡片阴影效果

### 🌟 升级亮点

1. **组件标准化** - 使用成熟的 UI 组件库
2. **开发效率** - 减少自定义样式维护
3. **用户体验** - 更好的交互反馈
4. **可访问性** - Element Plus 内置支持
5. **国际化** - 完善的多语言支持
6. **主题系统** - 灵活的主题定制

### 🚀 后续规划

- [ ] 集成 Vue Router 路由管理
- [ ] 添加 Pinia 状态管理
- [ ] 完善权限控制系统
- [ ] 集成图表库（ECharts）
- [ ] 添加表单验证
- [ ] 优化移动端体验

---

**项目地址：** http://localhost:5173
**技术支持：** MCP Gateway Team
