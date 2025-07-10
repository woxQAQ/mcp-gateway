<script setup lang="ts">
// 主应用组件，使用路由视图
</script>

<template>
  <div id="app">
    <router-view />
  </div>
</template>

<style>
#app {
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

/* Element Plus 基础主题定制 */
:root {
  --el-color-primary: #409eff;
  --el-color-primary-light-3: #79bbff;
  --el-color-primary-light-5: #a0cfff;
  --el-color-primary-light-7: #c6e2ff;
  --el-color-primary-light-8: #d9ecff;
  --el-color-primary-light-9: #ecf5ff;
  --el-color-primary-dark-2: #337ecc;

  /* 成功色 */
  --el-color-success: #67c23a;
  --el-color-success-light-3: #95d475;
  --el-color-success-light-5: #b3e19d;
  --el-color-success-light-7: #d1edc4;
  --el-color-success-light-8: #e1f3d8;
  --el-color-success-light-9: #f0f9eb;

  /* 警告色 */
  --el-color-warning: #e6a23c;
  --el-color-warning-light-3: #eebe77;
  --el-color-warning-light-5: #f3d19e;
  --el-color-warning-light-7: #f8e3c5;
  --el-color-warning-light-8: #faecd8;
  --el-color-warning-light-9: #fdf6ec;

  /* 错误色 */
  --el-color-danger: #f56c6c;
  --el-color-danger-light-3: #f89898;
  --el-color-danger-light-5: #fab6b6;
  --el-color-danger-light-7: #fcd3d3;
  --el-color-danger-light-8: #fde2e2;
  --el-color-danger-light-9: #fef0f0;

  /* 信息色 */
  --el-color-info: #909399;
  --el-color-info-light-3: #b1b3b8;
  --el-color-info-light-5: #c8c9cc;
  --el-color-info-light-7: #dedfe0;
  --el-color-info-light-8: #e9e9eb;
  --el-color-info-light-9: #f4f4f5;
}

/* 完整的暗色主题支持 */
html.dark {
  /* 背景色 */
  --el-bg-color: #1d1e1f;
  --el-bg-color-page: #0a0a0a;
  --el-bg-color-overlay: #1d1e1f;

  /* 文字色 */
  --el-text-color-primary: #e5eaf3;
  --el-text-color-regular: #cfd3dc;
  --el-text-color-secondary: #a3a6ad;
  --el-text-color-placeholder: #8d9095;
  --el-text-color-disabled: #6c6e72;

  /* 边框色 */
  --el-border-color: #4c4d4f;
  --el-border-color-light: #414243;
  --el-border-color-lighter: #363637;
  --el-border-color-extra-light: #2b2b2c;
  --el-border-color-dark: #58585b;
  --el-border-color-darker: #636466;

  /* 填充色 */
  --el-fill-color: #303133;
  --el-fill-color-light: #262727;
  --el-fill-color-lighter: #1d1e1f;
  --el-fill-color-extra-light: #191a1b;
  --el-fill-color-dark: #39393a;
  --el-fill-color-darker: #424243;
  --el-fill-color-blank: transparent;

  /* 主色在暗色模式下的调整 */
  --el-color-primary-light-3: #337ecc;
  --el-color-primary-light-5: #2b6bb2;
  --el-color-primary-light-7: #235899;
  --el-color-primary-light-8: #1d4b80;
  --el-color-primary-light-9: #173e66;

  /* 成功色在暗色模式下的调整 */
  --el-color-success-light-3: #529b2e;
  --el-color-success-light-5: #448425;
  --el-color-success-light-7: #376d1c;
  --el-color-success-light-8: #2a5515;
  --el-color-success-light-9: #1d3e0e;

  /* 警告色在暗色模式下的调整 */
  --el-color-warning-light-3: #b88230;
  --el-color-warning-light-5: #9e6b28;
  --el-color-warning-light-7: #845520;
  --el-color-warning-light-8: #6a3e18;
  --el-color-warning-light-9: #502810;

  /* 错误色在暗色模式下的调整 */
  --el-color-danger-light-3: #c45656;
  --el-color-danger-light-5: #a64a4a;
  --el-color-danger-light-7: #893e3e;
  --el-color-danger-light-8: #6b3232;
  --el-color-danger-light-9: #4d2626;

  /* 信息色在暗色模式下的调整 */
  --el-color-info-light-3: #767a82;
  --el-color-info-light-5: #65686f;
  --el-color-info-light-7: #54575c;
  --el-color-info-light-8: #434549;
  --el-color-info-light-9: #323336;

  /* 阴影 */
  --el-box-shadow: 0 12px 32px 4px rgba(0, 0, 0, 0.36), 0 8px 20px rgba(0, 0, 0, 0.72);
  --el-box-shadow-light: 0 0 12px rgba(0, 0, 0, 0.72);
  --el-box-shadow-lighter: 0 0 6px rgba(0, 0, 0, 0.72);
  --el-box-shadow-dark:
    0 16px 48px 16px rgba(0, 0, 0, 0.72), 0 12px 32px rgba(0, 0, 0, 0.72), 0 8px 16px -8px rgba(0, 0, 0, 0.72);

  /* 禁用状态 */
  --el-disabled-bg-color: var(--el-fill-color-light);
  --el-disabled-text-color: var(--el-text-color-placeholder);
  --el-disabled-border-color: var(--el-border-color-light);

  /* 遮罩层 */
  --el-mask-color: rgba(0, 0, 0, 0.8);
  --el-mask-color-extra-light: rgba(0, 0, 0, 0.3);
}

/* 暗色模式下的组件特殊样式调整 */
html.dark .el-card {
  background-color: var(--el-bg-color);
  border-color: var(--el-border-color-lighter);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
}

html.dark .el-table {
  background-color: var(--el-bg-color);
  color: var(--el-text-color-primary);
}

html.dark .el-table td.el-table__cell,
html.dark .el-table th.el-table__cell.is-leaf {
  border-bottom-color: var(--el-border-color-lighter);
}

html.dark .el-table--striped .el-table__body tr.el-table__row--striped td.el-table__cell {
  background-color: var(--el-fill-color-lighter);
}

html.dark .el-table tr:hover > td.el-table__cell {
  background-color: var(--el-fill-color-light);
}

html.dark .el-input__wrapper {
  background-color: var(--el-fill-color-light);
  box-shadow: 0 0 0 1px var(--el-border-color-lighter) inset;
}

html.dark .el-input__wrapper:hover {
  box-shadow: 0 0 0 1px var(--el-border-color) inset;
}

html.dark .el-input__wrapper.is-focus {
  box-shadow: 0 0 0 1px var(--el-color-primary) inset;
}

html.dark .el-select .el-input__wrapper {
  background-color: var(--el-fill-color-light);
}

html.dark .el-dropdown-menu {
  background-color: var(--el-bg-color-overlay);
  border-color: var(--el-border-color-light);
  box-shadow: var(--el-box-shadow-light);
}

html.dark .el-menu {
  background-color: transparent;
}

html.dark .el-menu-item:hover {
  background-color: var(--el-fill-color-light);
}

html.dark .el-pagination .el-pager li {
  background-color: var(--el-fill-color-light);
  color: var(--el-text-color-primary);
}

/* ===== 全局通用组件样式 ===== */

/* 页面容器通用样式 */
.page-container {
  background: var(--el-bg-color-page);
  min-height: 100vh;
  transition: background-color 0.3s ease;
}

.page-container h1 {
  color: var(--el-text-color-primary);
}

.page-container p {
  color: var(--el-text-color-secondary);
}

/* 卡片通用样式增强 */
.el-card {
  background-color: var(--el-bg-color);
  border-color: var(--el-border-color-lighter);
  border-radius: 12px;
  box-shadow: var(--el-box-shadow-lighter);
  transition: all 0.3s ease;
}

.el-card:hover {
  box-shadow: var(--el-box-shadow-light);
  transform: translateY(-1px);
}

/* 表格通用样式增强 */
.el-table {
  background-color: var(--el-bg-color);
  color: var(--el-text-color-primary);
}

.el-table .el-table__header-wrapper {
  background-color: var(--el-fill-color-extra-light);
}

html.dark .el-table .el-table__header-wrapper {
  background-color: var(--el-fill-color-light);
}

.el-table .el-table__header th {
  background-color: transparent;
  color: var(--el-text-color-primary);
  font-weight: 600;
}

/* 按钮通用样式优化 */
.el-button {
  transition: all 0.2s ease;
  border-radius: 6px;
  font-weight: 500;
}

.el-button:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

html.dark .el-button:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
}

/* 主要按钮样式 */
.el-button--primary {
  background: linear-gradient(135deg, var(--el-color-primary) 0%, var(--el-color-primary-dark-2) 100%);
  border: none;
  box-shadow: 0 2px 4px rgba(64, 158, 255, 0.3);
}

.el-button--primary:hover {
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.4);
}

html.dark .el-button--primary {
  box-shadow: 0 2px 4px rgba(64, 158, 255, 0.2);
}

html.dark .el-button--primary:hover {
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.3);
}

/* 成功按钮样式 */
.el-button--success {
  background: linear-gradient(135deg, var(--el-color-success) 0%, #529b2e 100%);
  border: none;
  box-shadow: 0 2px 4px rgba(103, 194, 58, 0.3);
}

.el-button--success:hover {
  box-shadow: 0 4px 12px rgba(103, 194, 58, 0.4);
}

html.dark .el-button--success {
  box-shadow: 0 2px 4px rgba(103, 194, 58, 0.2);
}

html.dark .el-button--success:hover {
  box-shadow: 0 4px 12px rgba(103, 194, 58, 0.3);
}

/* 警告按钮样式 */
.el-button--warning {
  background: linear-gradient(135deg, var(--el-color-warning) 0%, #b88230 100%);
  border: none;
  box-shadow: 0 2px 4px rgba(230, 162, 60, 0.3);
}

.el-button--warning:hover {
  box-shadow: 0 4px 12px rgba(230, 162, 60, 0.4);
}

html.dark .el-button--warning {
  box-shadow: 0 2px 4px rgba(230, 162, 60, 0.2);
}

html.dark .el-button--warning:hover {
  box-shadow: 0 4px 12px rgba(230, 162, 60, 0.3);
}

/* 危险按钮样式 */
.el-button--danger {
  background: linear-gradient(135deg, var(--el-color-danger) 0%, #c45656 100%);
  border: none;
  box-shadow: 0 2px 4px rgba(245, 108, 108, 0.3);
}

.el-button--danger:hover {
  box-shadow: 0 4px 12px rgba(245, 108, 108, 0.4);
}

html.dark .el-button--danger {
  box-shadow: 0 2px 4px rgba(245, 108, 108, 0.2);
}

html.dark .el-button--danger:hover {
  box-shadow: 0 4px 12px rgba(245, 108, 108, 0.3);
}

/* 禁用按钮样式 */
.el-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.el-button:disabled:hover {
  transform: none;
  box-shadow: none;
}

/* 输入框通用样式增强 */
.el-input .el-input__wrapper {
  border-radius: 6px;
  transition: all 0.2s ease;
  background-color: var(--el-fill-color-light);
}

.el-input .el-input__wrapper:hover {
  transform: translateY(-1px);
  box-shadow: var(--el-box-shadow-lighter);
}

html.dark .el-input .el-input__wrapper:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
}

/* 选择框通用样式 */
.el-select .el-input__wrapper {
  transition: all 0.2s ease;
}

.el-select .el-input__wrapper:hover {
  transform: translateY(-1px);
  box-shadow: var(--el-box-shadow-lighter);
}

html.dark .el-select .el-input__wrapper:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
}

/* 文本区域通用样式 */
.el-textarea .el-textarea__inner {
  background-color: var(--el-fill-color-light);
  border-color: var(--el-border-color);
  color: var(--el-text-color-primary);
  border-radius: 6px;
  transition: all 0.2s ease;
}

.el-textarea .el-textarea__inner:hover {
  border-color: var(--el-border-color-hover);
  box-shadow: var(--el-box-shadow-lighter);
}

/* 分页通用样式 */
.el-pagination {
  padding: 16px 0;
}

.el-pagination .el-pagination__total,
.el-pagination .el-pagination__jump {
  color: var(--el-text-color-secondary);
}

/* 对话框通用样式增强 */
.el-dialog {
  border-radius: 12px;
  overflow: hidden;
  box-shadow: var(--el-box-shadow);
}

.el-dialog .el-dialog__header {
  background: linear-gradient(135deg, var(--el-fill-color-extra-light) 0%, var(--el-fill-color-light) 100%);
  border-bottom: 1px solid var(--el-border-color-lighter);
  padding: 20px 24px;
}

html.dark .el-dialog .el-dialog__header {
  background: linear-gradient(135deg, var(--el-fill-color-light) 0%, var(--el-fill-color) 100%);
  border-bottom-color: var(--el-border-color-light);
}

.el-dialog .el-dialog__title {
  color: var(--el-text-color-primary);
  font-weight: 600;
  font-size: 18px;
}

.el-dialog .el-dialog__body {
  padding: 24px;
  background-color: var(--el-bg-color);
}

/* 表单项通用增强 */
.el-form-item .el-form-item__label {
  color: var(--el-text-color-primary);
  font-weight: 500;
}

/* 标签通用样式 */
.el-tag {
  border-radius: 6px;
  font-weight: 500;
}

/* 警报组件通用样式 */
.el-alert {
  border-radius: 8px;
  background-color: var(--el-color-danger-light-9);
  border-color: var(--el-color-danger-light-7);
}

html.dark .el-alert {
  background-color: rgba(196, 86, 86, 0.1);
  border-color: var(--el-color-danger-light-7);
}

/* 加载状态通用样式 */
.el-loading-mask {
  background-color: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(4px);
}

html.dark .el-loading-mask {
  background-color: rgba(0, 0, 0, 0.6);
}

/* 空状态通用样式 */
.el-table .el-table__empty-text {
  color: var(--el-text-color-placeholder);
}

.el-empty {
  color: var(--el-text-color-secondary);
}

/* 对话框底部按钮区域 */
.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

/* 通用动画效果 */
@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.fade-in-up {
  animation: fadeInUp 0.5s ease-out;
}

/* 响应式通用样式 */
@media (max-width: 768px) {
  .page-container {
    padding: 16px;
  }

  .el-dialog {
    width: 95% !important;
    margin: 20px auto;
  }

  .el-table .el-table__column {
    min-width: 120px;
  }

  .mobile-stack {
    flex-direction: column;
    gap: 8px;
  }

  .mobile-stack .el-button {
    width: 100%;
    margin: 0;
  }
}
</style>
