# GY CrossKit 共享发布规则

本文件是 `/Users/guoyang/gycrosskit` 下各仓库的共同规则。进入具体仓库后，先读该仓库已有的说明、构建配置和更具体的 `AGENTS.md`；源码与实际构建结果优先于文档。

## 发布前

- 先确认目标仓库、版本、Git 标签、依赖坐标和发布渠道。Gradle/KMP 产物走 JitPack；HarmonyOS HAR 走 ohpm。不要把两种产物当成同一个发布任务。
- 沿用仓库现有的构建入口。compose-webview、live-sdk、toast 在 JitPack 构建并修正 KMP 元数据；koin-ohos、stately-ohos、mmkv-ohos 从已校验摘要的 Release 归档安装产物。各仓库特有的构建步骤留在本仓库。
- 修改共用的 KMP 元数据修正脚本时，以本仓库的 `templates/jitpack-metadata.py` 为模板，同步检查 compose-webview、live-sdk、toast 的副本；不要为单一仓库的问题盲目改动所有仓库。
- 检查产物的版本、模块、POM、Gradle Module Metadata 和实际文件是否一致。不要把本地 `publishToMavenLocal` 成功当作远程可用。

## 发布与验收

- JitPack：检查目标标签的最终构建结果，并在干净的消费工程中从 JitPack 下载所需变体。
- ohpm：构建 HAR，确认包内 `CHANGELOG.md` 含当前版本，通过 `ohpm prepublish` 后再提交；提交审核不等于上架，以上架后的包查询和安装为准。
- 只有迁移后的远程坐标可用时，才清理旧的 `docs/maven` 产物和引用。新版本不再默认放进仓库自建 Maven 目录。
- 发布凭据只放在受控环境或本机配置中，不写入 Git、构建日志或回答。版本标签和已发布版本不可覆盖。

本规则记录共同检查项，不代替各仓库的 `jitpack.yml`、Gradle 配置、HAR 清单或实际验收。
