LeeClient 仙境传说客户端
======================

目录
----
1. LeeClient 项目简介
2. 关闭 filemode 检测

LeeClient 项目简介
-------------------
简单的理解为：LeeClient 就是一个被整理过的、力图整合RO官方所有图档资源的、方便
各位 GM 切换不同版本客户端进行调试的仙境传说完整客户端。

此项目中的官方图档和 Ragexe 系列主程序的版权归韩国重力社（GRAVITY CO., Ltd.）
所有, 维护团队仅根据网上收集的信息进行整理和归纳。

用于维护此项目的管理程序名为: LeeClientAgent 是一套基于 Python 3.x 编写的脚
本程序, 该程序基于 GNU GPLv3. 开源许可协议（位于 Utility 目录）。

关闭 filemode 检测
-------------------
在您第一次克隆完成此 LeeClient 仓库时, 如果发现刚克隆完成, git 就显示大量红色
的“已修改”状态, 那么您需要修改您本地该仓库的 git 配置：

- 请打开可调用 git 指令的命令行控制台
- cd 切换到本仓库在您电脑上的路径（例如：C:\LeeClient）
- 执行 `git config core.filemode false` 关闭当前仓库的 filemode 检测

