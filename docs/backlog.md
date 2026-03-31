# WinCleaner Backlog

## P0

### 1. 建立 Windows 实机验证矩阵
- 标题：`test: add Windows 10/11 manual verification matrix`
- 目标：建立覆盖 Windows 10/11 的实机回归清单。
- 任务：
  - 覆盖管理员/非管理员启动
  - 覆盖 UAC 提权
  - 覆盖回收站读取与清空
  - 覆盖 Explorer 文件定位
  - 覆盖服务控制、注册表读写、WMI 信息读取
- 验收标准：
  - 仓库内新增验证矩阵文档
  - 每项功能都有环境、步骤、预期结果、实际结果
  - 至少完成一次 Windows 10 和 Windows 11 回归记录

### 2. 为高风险操作生成结构化执行报告
- 标题：`feat: add structured reports for risky operations`
- 目标：为垃圾清理、进程终止、更新控制生成统一格式结果。
- 任务：
  - 记录开始时间、结束时间、操作对象
  - 记录成功数、失败数、失败原因
  - 将结果接入统一日志或导出能力
- 验收标准：
  - 操作后能查看统一格式摘要
  - 失败项能定位到具体文件、进程或服务

### 3. 扩展测试覆盖关键安全逻辑
- 标题：`test: expand coverage for cleanup, process protection and logging`
- 目标：补足高风险逻辑测试覆盖。
- 任务：
  - 增加更新控制结果测试
  - 增加日志过滤逻辑测试
  - 增加清理统计结果测试
  - 增加进程保护和结果勾选逻辑测试
- 验收标准：
  - `python -m unittest discover -s tests -p "test_*.py"` 稳定通过
  - 核心安全逻辑均有测试覆盖

### 4. 统一后台任务执行框架
- 标题：`refactor: unify background task execution model`
- 目标：收口页面中的异步执行模式。
- 任务：
  - 统一开始、完成、失败回调
  - 统一进度上报
  - 支持取消和超时
  - 支持统一日志接入
- 验收标准：
  - 页面不再重复维护相似 worker 逻辑
  - 长耗时任务通过统一框架执行

## P1

### 5. 将阈值和默认路径改为可配置项
- 标题：`feat: move thresholds and default paths into config`
- 目标：减少运行策略硬编码。
- 任务：
  - 配置 CPU/内存阈值
  - 配置默认扫描路径
  - 配置日志级别
  - 配置危险操作开关
- 验收标准：
  - 关键策略均可从配置读取
  - 缺省配置下仍可运行

### 6. 为日志面板增加来源过滤和诊断导出
- 标题：`feat: add source filtering and diagnostic export to log panel`
- 目标：提升日志排查效率。
- 任务：
  - 增加按模块来源过滤
  - 增加关键字搜索
  - 支持导出完整运行日志
  - 规划诊断包格式
- 验收标准：
  - 可按页面或模块过滤日志
  - 可导出当前视图或完整日志

### 7. 支持持久化垃圾清理排除规则
- 标题：`feat: persist cleanup exclusion rules`
- 目标：让排除规则跨会话生效。
- 任务：
  - 支持按文件路径排除
  - 支持按目录排除
  - 支持按扩展名排除
  - 提供规则管理入口
- 验收标准：
  - 排除规则可持久化保存
  - 新一轮扫描自动应用规则

### 8. 统一版本号来源并接入发布流程
- 标题：`ci: use a single source of truth for app version`
- 目标：保证应用、文档、tag、Release 版本一致。
- 任务：
  - 确定单一版本来源
  - 应用和发布流程统一读取该来源
  - 在 CI 中校验 tag 与版本一致
- 验收标准：
  - 版本信息只维护一处
  - tag 与版本不一致时 CI 失败

## P2

### 9. 补完整发布和使用文档
- 标题：`docs: split user guide, developer guide and release guide`
- 目标：拆分用户、开发、发布文档。
- 任务：
  - 编写用户手册
  - 编写开发手册
  - 编写发布手册
  - 编写故障排查手册
- 验收标准：
  - README 保持总览职责
  - 各角色文档职责清晰

### 10. 规划清理规则和保护规则插件化
- 标题：`proposal: design a plugin-style rule system for cleanup and protection`
- 目标：为规则增长设计可扩展机制。
- 任务：
  - 定义规则格式
  - 设计加载方式
  - 设计优先级和冲突处理
  - 输出设计文档
- 验收标准：
  - 有明确设计文档
  - 给出最小可落地实施方案
