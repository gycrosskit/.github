# WebView 与 Live 预发布

日期：2026-09-30。两库经受保护主分支的 PR 合并，使用不可变 `0.2.0-rc.2` 标签；设备及生产验收未完成。

| 组件 | 远程入口 | Maven 模块 |
| --- | --- | --- |
| Live | [GitHub prerelease](https://github.com/gycrosskit/live-sdk/releases/tag/0.2.0-rc.2)；JitPack 15 个模块构建成功 | `com.github.gycrosskit.live-sdk:{live-sdk,live-core,live-kuikly}:0.2.0-rc.2` |
| WebView | [GitHub prerelease](https://github.com/gycrosskit/compose-webview/releases/tag/0.2.0-rc.2)；JitPack 17 个模块构建成功 | `com.github.gycrosskit.compose-webview:{compose-webview,webview-core,webview-kuikly}:0.2.0-rc.2` |

WebView 的 `GYWebView.podspec` 与 HAR 同为 `0.2.0-rc.2`。ohpm 已接受 `@gycrosskit/webview` 的 `next` 提交，当前审核中，registry 尚未可安装；审核期间使用同标签 Release HAR，下载并校验附件 SHA-256。

## 验证与限制

- Live：31 项状态机/协议测试通过。纯 JitPack Android APK/D8、独立 Kuikly 无 Compose、混合 CMP/Kuikly 单份 SDK、iOS arm64/模拟器 Framework 通过；远程标签 Swift View 与真实 Kuikly Render 最终链接通过。
- WebView：60 项组件测试通过。#6 的旧实际 HAR 首航 throw 回归先红后绿；#4 独立来源白名单与 #5 typed capture 不支持已实现。纯 JitPack Kuikly Android APK/D8、无 Compose、iOS arm64 Framework/模拟器编译与 OHOS shared library 通过。远程标签 iOS 原生代码编译/最终链接/Swift 类型检查，以及 Release HAR 的安全/首航回归和独立消费编译通过。
- 应用由“鸿蒙生产接入”会话在其独占 Worktree 升级，应用结果与组件消费工程结果分别记录。Live 鸿蒙仍暂停等待腾讯正式 SDK；capture 仍不支持，不能伪造成功。

Live rc.1 的 JitPack 失败是默认 Linux Python 过旧；rc.2 仅安装发布前已校验的归档。WebView rc.1 的 ohpm 提交因 README 缺安装命令被拒，rc.2 补齐后接受。旧标签均保留，未覆盖归档。
