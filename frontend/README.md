frontend
├───.husky                    # Git hooks（提交代码前执行脚本，如eslint检查）
├───.vscode                   # VSCode 项目配置
├───build                     # 项目构建脚本（vite打包相关）
├───mock                      # mock接口数据（前端假数据）
├───node_modules              # npm依赖包
├───public                    # 静态资源（不会被vite处理）
├───src                       # 前端核心源码
│   ├───api                   # 后端接口请求（axios封装的API）
│   ├───assets                # 图片、字体、svg等资源
│   ├───components            # 可复用组件
│   ├───config                # 项目配置文件
│   ├───directives            # Vue自定义指令（如v-permission）
│   ├───layout                # 后台整体布局（侧边栏、顶部栏、主体）
│   ├───plugins               # 插件注册（element-plus、pinia等）
│   ├───router                # 路由系统
│   │   ├───modules           # 模块化路由（按功能拆分路由）
│   │   ├───index.ts          # 创建Vue Router实例
│   │   └───utils.ts          # 路由工具函数（如动态路由处理）
│   ├───store                 # Pinia状态管理（用户信息、token等）
│   ├───style                 # 全局样式（scss、主题）
│   ├───utils                 # 工具函数（request、storage等）
│   ├───views                 # 页面组件
│   │   ├───error             # 错误页面（404/403/500）
│   │   ├───login             # 登录页面
│   │   ├───permission        # 权限相关页面
│   │   ├───tickets           # 工单系统页面
│   │   └───welcome           # 后台首页
│   ├───App.vue               # Vue根组件
│   └───main.ts               # Vue应用入口（createApp）
├───types                     # TypeScript类型定义