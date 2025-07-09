// orval 配置文件
// 使用前请先安装: npm install -D orval

export default {
  // API客户端生成配置
  api: {
    input: {
      // OpenAPI文档路径（可以是本地文件或URL）
      target: "../docs/api_docs.yaml",
      // 如果是远程URL，可以这样配置：
      // target: 'http://localhost:8000/openapi.json',
    },
    output: {
      // 生成文件的输出目录
      target: "./src/api/generated/api.ts",
      client: "fetch", // 可选: fetch, axios, angular, react-query, swr
      mode: "single", // split: 分文件, single: 单文件, tags: 按标签分组
      mock: true, // 启用 mock 数据生成
      prettier: true, // 使用 prettier 格式化生成的代码
      override: {
        // 自定义配置
        mutator: {
          path: "./src/api/mutator.ts",
          name: "customInstance",
        },
        // 请求/响应拦截器
        operations: {
          // 为所有操作添加通用配置
          "*": {
            mock: {
              // mock 数据生成配置
              delay: [100, 2000], // 随机延迟
            },
          },
        },
      },
    },
    // hooks: {
    //   // 钩子配置，可以在生成前后执行自定义逻辑
    //   afterAllFilesWrite: "npm run format:generated",
    // },
  },
};
