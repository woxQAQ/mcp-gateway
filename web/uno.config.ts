import { defineConfig, presetAttributify, presetIcons, presetUno } from 'unocss'

export default defineConfig({
  presets: [
    presetUno(),
    presetAttributify(),
    presetIcons({
      scale: 1.2,
      warn: true,
    }),
  ],

  // 主题配置
  theme: {
    colors: {
      // 与 Element Plus 主题色保持一致
      primary: {
        50: '#ecf5ff',
        100: '#d9ecff',
        200: '#b6d7ff',
        300: '#84c2ff',
        400: '#52a2ff',
        500: '#409eff', // Element Plus 主色
        600: '#337ecc',
        700: '#2b5f99',
        800: '#254066',
        900: '#1f2533',
      },
      success: '#67c23a',
      warning: '#e6a23c',
      danger: '#f56c6c',
      info: '#909399',
    },
    fontFamily: {
      sans: ['Segoe UI', 'Tahoma', 'Geneva', 'Verdana', 'sans-serif'],
    },
  },

  // 快捷方式
  shortcuts: {
    // 基础布局
    'flex-center': 'flex items-center justify-center',
    'flex-between': 'flex items-center justify-between',
    'flex-start': 'flex items-start',
    'flex-end': 'flex items-end',

    // 按钮样式
    'btn-base': 'px-4 py-2 rounded-lg font-medium transition-all duration-200 cursor-pointer',
    'btn-primary': 'btn-base bg-primary-500 text-white hover:bg-primary-600 shadow-sm',
    'btn-secondary': 'btn-base bg-gray-100 text-gray-700 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-200',
    'btn-ghost': 'btn-base bg-transparent hover:bg-gray-100 dark:hover:bg-gray-800',

    // 卡片样式
    'card-base': 'bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700',
    'card-shadow': 'card-base shadow-sm hover:shadow-md transition-shadow duration-200',
    'card-padding': 'p-6',

    // 文本样式
    'text-title': 'text-lg font-semibold text-gray-900 dark:text-white',
    'text-subtitle': 'text-base font-medium text-gray-700 dark:text-gray-300',
    'text-body': 'text-sm text-gray-600 dark:text-gray-400',
    'text-caption': 'text-xs text-gray-500 dark:text-gray-500',

    // 输入框样式
    'input-base': 'w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-colors',

    // 状态指示
    'status-success': 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
    'status-warning': 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200',
    'status-error': 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
    'status-info': 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
  },

  // 规则
  rules: [
    // 自定义规则，例如：
    [/^glass-(.+)$/, ([, opacity]) => ({
      'backdrop-filter': 'blur(10px)',
      'background-color': `rgba(255, 255, 255, ${Number.parseInt(opacity) / 100})`,
    })],

    // 渐变文本
    [/^text-gradient-(.+)$/, ([, _colors]) => ({
      'background-image': `linear-gradient(45deg, var(--un-gradient-stops))`,
      'background-clip': 'text',
      '-webkit-background-clip': 'text',
      'color': 'transparent',
    })],
  ],

  // 变体
  variants: [
    // 自定义变体
    (matcher) => {
      if (!matcher.startsWith('important:'))
        return matcher
      return {
        matcher: matcher.slice(10),
        body: (body) => {
          body.forEach((v) => {
            if (v[1])
              v[1] += ' !important'
          })
          return body
        },
      }
    },
  ],

  // 安全列表 - 确保这些类不被删除
  safelist: [
    // Element Plus 相关类
    'el-button',
    'el-card',
    'el-menu',
    'el-menu-item',

    // 常用工具类
    'flex',
    'grid',
    'hidden',
    'block',
    'inline',
    'inline-block',
    'w-full',
    'h-full',
    'w-auto',
    'h-auto',
    'text-center',
    'text-left',
    'text-right',
    'font-bold',
    'font-semibold',
    'font-medium',
    'font-normal',

    // 间距
    'p-0',
    'p-1',
    'p-2',
    'p-3',
    'p-4',
    'p-5',
    'p-6',
    'p-8',
    'm-0',
    'm-1',
    'm-2',
    'm-3',
    'm-4',
    'm-5',
    'm-6',
    'm-8',
    'px-2',
    'px-3',
    'px-4',
    'py-2',
    'py-3',
    'py-4',
    'mx-auto',
    'my-auto',

    // 颜色
    'text-white',
    'text-black',
    'text-gray-500',
    'text-gray-600',
    'text-gray-700',
    'bg-white',
    'bg-gray-50',
    'bg-gray-100',
    'bg-gray-200',
    'border-gray-200',
    'border-gray-300',

    // 尺寸
    'w-16',
    'w-32',
    'w-48',
    'w-64',
    'w-96',
    'h-16',
    'h-32',
    'h-48',
    'h-64',
    'h-96',

    // 圆角
    'rounded',
    'rounded-md',
    'rounded-lg',
    'rounded-xl',
    'rounded-full',

    // 阴影
    'shadow',
    'shadow-sm',
    'shadow-md',
    'shadow-lg',
    'shadow-xl',

    // 过渡
    'transition',
    'transition-all',
    'transition-colors',
    'transition-transform',
    'duration-200',
    'duration-300',
    'duration-500',

    // 响应式
    'sm:hidden',
    'md:block',
    'lg:flex',
    'xl:grid',
    'sm:w-full',
    'md:w-1/2',
    'lg:w-1/3',
    'xl:w-1/4',
  ],
})
