# GY CrossKit

面向 Kotlin Multiplatform、Compose Multiplatform（CMP）与 Kuikly 应用的跨平台组件。按用途选择仓库，再阅读对应 README 完成安装和平台接线。

组件版本核对日期：**2026-10-10**，依据各库远程 README 与 Release。Maven 由 JitPack 提供；Git Pod、Swift Package（SPM）与 HarmonyOS HAR 分别安装，配套版本可能不同。预发布状态以 Release 标记为准；发布、精确远程消费和设备业务验收分别记录。OHPM 当前可安装性以组件 README 和 Registry 即时查询为准，本次未查询 Registry。

本轮审查修复涉及回调、测试、CI 与文档；新增生产发版仅为微信 iOS **[native-0.1.8](https://github.com/gycrosskit/wechat/releases/tag/native-0.1.8)**。下表其他版本为已有发布组合，不表示本轮重新发布。

## 组件地图与接入流程

下图按用途分组，不表示组内组件互相依赖；各库独立安装，按业务需要选择。具体内部结构、公共类型和生命周期见各仓库 README 的“架构与调用流程”。

```mermaid
flowchart LR
    App["宿主应用：业务、账号、UI、隐私准入"] --> Foundation["基础：Koin / Stately / MMKV"]
    App --> Platform["平台能力：permission / media / scanner / location / toast / sound / system-actions"]
    App --> Web["网页：compose-webview"]
    App --> Vendor["厂商适配：jverification / wechat / customer-service / live-sdk"]
    App --> Diagnostics["诊断：diagnostics / debug-tools"]
    Web -->|"HarmonyOS 窗口策略共用"| Window["system-actions HAR"]
    Foundation -->|"Koin Core 使用"| Stately["配套 Stately 适配版本"]
```

```mermaid
flowchart TB
    Choose["选择组件与 UI 入口"] --> Matrix["核对平台、工具链与配套版本"]
    Matrix --> Maven["安装 Maven / KMP 依赖"]
    Maven --> Native{"该入口需要独立原生包？"}
    Native -->|"需要"| Package["按 README 安装 Pod / SPM / HAR"]
    Native -->|"不需要"| Wire["宿主初始化、注册、权限与生命周期接线"]
    Package --> Wire
    Wire --> Build["目标平台编译与链接"]
    Build --> Device["真机与业务验收"]
```

Maven 和原生包可能使用不同版本；HAR 的 Release 下载与 OHPM 上架分别确认，编译通过后仍需真机验收。

## 基础依赖与 OpenHarmony 适配

| 仓库 | 用途 | 已发布平台 | Maven 版本 |
| --- | --- | --- | --- |
| [koin-ohos](https://github.com/gycrosskit/koin-ohos/tree/codex/ohos-4.1.1) | Koin 依赖注入，发布 `koin-core` | JVM / Android、iOS、OHOS | [4.1.1-ohos-2.2.21-7](https://github.com/gycrosskit/koin-ohos/releases/tag/4.1.1-ohos-2.2.21-7) |
| [stately-ohos](https://github.com/gycrosskit/stately-ohos/tree/codex/ohos-2.1.0) | 并发与状态工具 | JVM / Android、iOS、OHOS | [2.1.0-ohos-2.2.21-11](https://github.com/gycrosskit/stately-ohos/releases/tag/2.1.0-ohos-2.2.21-11) |
| [mmkv-ohos](https://github.com/gycrosskit/mmkv-ohos) | MMKV KMP 键值存储 | Android、iOS、OHOS | [2.4.2-ohos-2.2.21-5](https://github.com/gycrosskit/mmkv-ohos/releases/tag/2.4.2-ohos-2.2.21-5) |

以上基础依赖本次仅核对适配分支 README 与 Release 版本，未新增构建或远程消费验收。这些仓库保留上游来源和许可证。Koin / Stately 默认 `main` 是上游基线，上述仓库链接直接指向实际 OHOS 适配分支。OHOS 消费使用对应 Kotlin 工具链，按指南替换上游坐标以避免重复 KLIB。

## UI 与平台能力

| 仓库 | 用途 | 平台 | Maven 版本 | 独立原生渠道 |
| --- | --- | --- | --- | --- |
| [compose-webview](https://github.com/gycrosskit/compose-webview) | 网页、导航、JSBridge、资源缓存与网站数据清理 | CMP：Android/iOS；Kuikly：三端 | [0.2.0-rc.16](https://github.com/gycrosskit/compose-webview/releases/tag/0.2.0-rc.16) | Git Pod **0.2.0-rc.16**；HAR **0.2.0-rc.14**，配套 system-actions HAR **0.2.0-rc.4**；导航、文件选择及 Cookie 限制见 README |
| [permission](https://github.com/gycrosskit/permission) | 权限请求与历史状态 | 三端 | [0.1.9](https://github.com/gycrosskit/permission/releases/tag/0.1.9) | 可选 `GycPermissionKuikly/Kuikly` Git Pod **0.1.9**；HAR **0.1.6**；iOS core 为 KMP 原生实现 |
| [media](https://github.com/gycrosskit/media) | 选图、拍照、压缩、保存相册与 Kuikly 传输桥 | 三端 | [0.1.9](https://github.com/gycrosskit/media/releases/tag/0.1.9) | 可选 `GycMediaKuikly/Kuikly` Git Pod **0.1.9**；SPM **[native-0.1.4](https://github.com/gycrosskit/media/releases/tag/native-0.1.4)**；HAR **0.1.6** |
| [scanner](https://github.com/gycrosskit/scanner) | 二维码解码与原生扫码 | 三端 | [0.1.9](https://github.com/gycrosskit/scanner/releases/tag/0.1.9) | SPM **[0.1.8](https://github.com/gycrosskit/scanner/releases/tag/0.1.8)**；HAR **0.1.4**；OHOS 使用系统扫码 |
| [toast](https://github.com/gycrosskit/toast) | 原生短消息、CMP/KuiklyCompose 消息展示 | 三端 | [0.1.6](https://github.com/gycrosskit/toast/releases/tag/0.1.6) | Git Pod **0.1.6**（可选 `/Kuikly` receiver）；SPM presenter **[0.1.5](https://github.com/gycrosskit/toast/releases/tag/0.1.5)**；HAR **0.1.3** |
| [location](https://github.com/gycrosskit/location) | 位置请求、取消与 Kuikly 请求桥 | 三端 | [0.1.6](https://github.com/gycrosskit/location/releases/tag/0.1.6) | 可选 `GycLocationKuikly/Kuikly` Git Pod **0.1.6**；HAR **0.1.4**；iOS core 为 KMP 原生实现 |
| [system-actions](https://github.com/gycrosskit/system-actions) | 系统设置、分享、UIKit 与窗口策略 | 三端 | [0.2.0-rc.7](https://github.com/gycrosskit/system-actions/releases/tag/0.2.0-rc.7) | Git Pod **0.2.0-rc.7**（可选 `/Kuikly` receiver）；SPM **[0.2.0-rc.6](https://github.com/gycrosskit/system-actions/releases/tag/0.2.0-rc.6)**；HAR **0.2.0-rc.5**（[独立 Release](https://github.com/gycrosskit/system-actions/releases/tag/native-0.2.0-rc.7)） |
| [sound](https://github.com/gycrosskit/sound) | 音频准备、播放与事件 | 三端 | [0.1.6](https://github.com/gycrosskit/sound/releases/tag/0.1.6) | 可选 `GYCSound/Kuikly` Git Pod **0.1.6**；HAR **[0.1.2](https://github.com/gycrosskit/sound/releases/tag/har-0.1.2)** |


“三端”指 Android、iOS 与 HarmonyOS / OpenHarmony。CMP 与 Kuikly 的同平台入口优先复用组件原生能力；UI、注册及生命周期按入口接线。OHOS 使用 Kuikly/ArkTS HAR 或已声明的 core 能力，本组织未提供独立 CMP OHOS runtime。各平台入口和能力以仓库说明为准。HAR 的完整包名、最低系统要求、权限与释放规则请查对应 README；库版本相同也不代表 API 和设备行为完全一致。

## 诊断与开发工具

| 仓库 | 用途 | 平台 | Maven 版本 | 接入边界 |
| --- | --- | --- | --- | --- |
| [diagnostics](https://github.com/gycrosskit/diagnostics) | 系统采集、私有文件、日志与有界网络诊断 | 三端、JVM | [0.2.0-rc.10](https://github.com/gycrosskit/diagnostics/releases/tag/0.2.0-rc.10) | Git Pod / SPM **[0.2.0-rc.1](https://github.com/gycrosskit/diagnostics/releases/tag/0.2.0-rc.1)**；可选 Ktor / OkHttp 采集；宿主配置正文额度、准入、脱敏、上传与凭据，无 HAR |
| [debug-tools](https://github.com/gycrosskit/debug-tools) | Bug 协议、安全存储与摇动 | Android、iOS、OHOS | [0.2.0-rc.6](https://github.com/gycrosskit/debug-tools/releases/tag/0.2.0-rc.6) | OHOS 配套 HAR **0.2.0-rc.3**；宿主提供 UI、品牌、凭据与准入 |

## 厂商 SDK 集成

| 仓库 | 用途 | 平台 | Maven 版本 | 独立原生渠道与状态 |
| --- | --- | --- | --- | --- |
| [customer-service](https://github.com/gycrosskit/customer-service) | 腾讯 AI Desk 客服原生适配与 SDK 身份归属 | Android、iOS | [0.1.6](https://github.com/gycrosskit/customer-service/releases/tag/0.1.6) | Git Pod **[0.1.5](https://github.com/gycrosskit/customer-service/releases/tag/0.1.5)**；OHOS 排除，未提供原生 HAR 或运行时 |
| [live-sdk](https://github.com/gycrosskit/live-sdk) | 腾讯 AtomicX 直播、预览、中立 IM 与 SDK 身份归属 | 直播：Android、iOS；core 中立协议：三端 | [0.2.1-rc.13](https://github.com/gycrosskit/live-sdk/releases/tag/0.2.1-rc.13) | Git Pod **0.2.1-rc.13**；OHOS core KLIB 不提供直播、IM 原生运行时或 PiP |
| [jverification](https://github.com/gycrosskit/jverification) | 极光一键登录与授权页事件 | 三端 | [0.1.5](https://github.com/gycrosskit/jverification/releases/tag/0.1.5) | Git Pod **0.1.5**（可选 `/Kuikly` receiver）；HAR **0.1.0** |
| [wechat](https://github.com/gycrosskit/wechat) | 微信授权、分享、转账确认页与请求恢复存储 | 三端 | [0.1.8](https://github.com/gycrosskit/wechat/releases/tag/0.1.8) | SPM / Git Pod **[native-0.1.8](https://github.com/gycrosskit/wechat/releases/tag/native-0.1.8)**（Pod 内部 **0.1.8**，可选 `/Kuikly` receiver）；HAR **0.1.6** |

厂商 SDK、AppID、签名、Universal Link、账号及隐私准入由宿主负责。Git Pod 不表示发布到 CocoaPods Specs；Swift Package 是否包含厂商二进制须查仓库接线说明。

微信 **native-0.1.8** 的精确远程 Git Pod / SPM 消费及 Release CI 已通过；Maven **0.1.8**、HAR **0.1.6** 保持既有版本。设备业务仍待宿主验收，微信页面回执不证明资金到账；Live 实际账号与设备行为也需单独验收。

## CI 与自动评审

14 个功能库按三层分别记录：PR 源码回归与 SDK 编译、固定 Release 公开文件与哈希校验、精确远程版本的独立消费者构建。共享脚本从固定提交安装；HAR/Registry 和真机业务不能由源码 job 代算。实际运行状态与提交覆盖范围以各库 Actions 为准。

自动 AI 评审在创建待审查 PR / 草稿转为可审查时触发，不能保证每次 push 都完成最新提交评审。中文状态摘要同步到固定评论，原文折叠保留；评审不自动修复或合并。规则见[AI 评审与中文状态](https://github.com/gycrosskit/.github/blob/main/docs/AI评审与中文状态.md)。

## 文档与反馈

- 安装与使用：对应仓库 **README → 接入指南**，开发和构建方法另见仓库验证文档。
- 版本与变更：对应 **Releases / Git 标签**，固定版本消费，升级时同时检查平台原生包版本。
- 问题反馈：在对应仓库 **Issues** 提供版本、平台、脱敏复现和日志，不上传凭据。
- 测试与 API 审查：[14 个功能组件的回归、注释与验收边界](https://github.com/gycrosskit/.github/blob/main/docs/组件测试与API审查.md)。
- 自动门禁：[14 库源码、发布产物及独立消费验证](https://github.com/gycrosskit/.github/blob/main/docs/持续集成门禁.md)。
- 共用维护：[组件文档规范](https://github.com/gycrosskit/.github/blob/main/docs/组件文档规范.md) · [发布流程](https://github.com/gycrosskit/.github/blob/main/docs/发布流程.md)。

debug-tools 和 customer-service 为多模块 JitPack 项目，根 KMP 坐标分别使用 `com.github.gycrosskit.debug-tools:debug-tools` 与 `com.github.gycrosskit.customer-service:customer-service`；安装时按 README 固定版本。Maven、Git Pod 与 OHPM 各自验收，Release 可下载不表示 OHPM 已上架。

各组件与上游、厂商 SDK 的许可证分别以对应仓库 README 和 LICENSE 为准。
