#!/usr/local/bin/python3
# -*- coding: utf-8 -*-

import os

from LeePyLibs import LeeConstant
from LeePyLibs import LeeCommon
from LeePyLibs import LeePatchManager
from LeePyLibs import LeeGrf
from LeePyLibs import LeeButtonTranslator
from LeePyLibs import LeeVerifier
from LeePyLibs import LeeIteminfoTranslator
from LeePyLibs import LeeTowninfoTranslator
from LeePyLibs import LeeSkillinfolistTranslator
from LeePyLibs import LeeSkilldescriptTranslator
from LeePyLibs import LeePublisher

# pip3 install pygame -i https://pypi.douban.com/simple --trusted-host=pypi.douban.com
# pip3 install pillow -i https://pypi.douban.com/simple --trusted-host=pypi.douban.com
# pip3 install lupa -i https://pypi.douban.com/simple --trusted-host=pypi.douban.com
# pip3 install pyyaml -i https://pypi.douban.com/simple --trusted-host=pypi.douban.com

LeeConstant().Environment = 'develop'
LeeConstant().EncodingForSaveFile = 'utf-8'

# ==============================================================================
# 类的定义和实现
# ==============================================================================

class LeeMenu:
    def __init__(self, mainFunc):
        self.item_Main = mainFunc
        self.patchManager = LeePatchManager()
        self.buttonTranslator = LeeButtonTranslator()
        self.leeVerifier = LeeVerifier()
        self.leeCommon = LeeCommon()

    def resetWorkshop(self):
        '''
        重置 LeeClient 客户端环境
        为接下来切换其他版本的客户端做好准备
        '''
        try:
            print('正在重置按钮汉化文件 ...')
            self.buttonTranslator.doRevert('AllVersions')

            print('正在重置其他客户端资源 ...')
            self.patchManager.doRevertPatch()

            leeClientDir = self.leeCommon.getLeeClientDirectory()
            if self.leeCommon.isFileExists('%sdata.grf' % leeClientDir):
                os.remove('%sdata.grf' % leeClientDir)

            print('正在删除空目录 ...')
            self.leeCommon.removeEmptyDirectorys(leeClientDir)

            print('已成功重置 LeeClient 客户端环境')
        except:
            print('很抱歉, 重置 LeeClient 客户端环境的过程中发生了意外, 请检查结果')

    def switchWorkshop(self, clientver):
        '''
        重置工作区, 并切换 LeeClient 到指定的客户端版本
        '''
        if self.patchManager.canRevert():
            lines = [
                '在切换版本之前, 需要将 LeeClient 客户端恢复到干净状态',
                '请将自己添加的额外重要文件移出 LeeClient 目录, 避免被程序误删'
                ''
            ]
            title = '切换主程序版本到 %s' % clientver
            prompt = '是否立刻执行重置操作?'
            self.leeCommon.simpleConfirm(lines, title, prompt, self, 'menus.resetWorkshop()')
            print('----------------------------------------------------------------')

        # 先执行与此版本相关的汉化工作
        print('正在汉化 iteminfo ...')
        LeeIteminfoTranslator().doTranslate(clientver)

        print('正在汉化 towninfo ...')
        LeeTowninfoTranslator().doTranslate(clientver)

        print('正在汉化 skillinfolist ...')
        LeeSkillinfolistTranslator().doTranslate(clientver)

        print('正在汉化 skilldescript ...')
        LeeSkilldescriptTranslator().doTranslate(clientver)

        print('正在汉化 客户端按钮 ...')
        LeeButtonTranslator().doTranslate(clientver)

        # 将对应的资源覆盖到 LeeClient 主目录
        print('正在切换版本, 请耐心等待...')
        if not self.patchManager.doApplyPatch(clientver):
            print('很抱歉, 切换仙境传说的主程序到 %s 版本的时发生错误, 请检查结果' % clientver)
        else:
            print('已切换仙境传说的主程序到 %s 版本\r\n' % clientver)

    def makePackageSourceToZipfile(self, packageSourceDirname):
        '''
        将指定的打包源压缩成一个 ZIP 文件
        '''
        leeClientParantDir = os.path.abspath('%s..%s' % (self.leeCommon.getLeeClientDirectory(), os.path.sep))
        packageSourceDirpath = '%s%s%s' % (leeClientParantDir, os.path.sep, packageSourceDirname)

        zipFilename = LeePublisher().getZipFilename(packageSourceDirpath)
        if not LeePublisher().makeZip(packageSourceDirpath, zipFilename):
            print('很抱歉, 压缩 ZIP 文件时发生错误, 请检查结果')
        else:
            print('已压缩为 ZIP 文件: %s\r\n' % (zipFilename))

    def makePackageSourceToSetup(self, packageSourceDirname):
        '''
        将指定的打包源制作成一个 Setup 安装程序
        '''
        leeClientParantDir = os.path.abspath('%s..%s' % (self.leeCommon.getLeeClientDirectory(), os.path.sep))
        packageSourceDirpath = '%s%s%s' % (leeClientParantDir, os.path.sep, packageSourceDirname)
        outputDirpath = './Output/%s' % packageSourceDirname

        if not LeePublisher().makeSetup(packageSourceDirpath, outputDirpath):
            print('很抱歉, 制作 Setup 安装程序时发生错误, 请检查结果')
        else:
            print('\r\n已制作完毕的 Setup 安装程序存放在: %s 目录中, 请确认.\r\n' % (os.path.abspath(outputDirpath)))

    def maintenanceUpdateButtonTranslateDB(self):
        '''
        根据目前各个客户端的 Resource/Original 目录中的最新文件
        来更新目前正在使用的按钮汉化数据库文件
        '''
        print('正在读取数据库...')
        self.buttonTranslator.load()
        print('正在根据目前 Patches 的内容升级数据库...')
        self.buttonTranslator.update()
        print('正在保存数据库...')
        self.buttonTranslator.save()
        print('更新操作已经完成, 请确认文件的变更内容...\r\n')

    def maintenanceRunClientResourceCheck(self):
        '''
        对客户端进行资源完整性校验
        '''
        self.leeVerifier.runVerifier()
        print('完整性校验过程已结束\r\n')

    def maintenanceMakeDataToGrf(self):
        '''
        将客户端的 data 目录压缩为 data.grf 文件
        '''
        leeClientDir = self.leeCommon.getLeeClientDirectory()
        LeeGrf().makeGrf('%sdata%s' % (leeClientDir, os.path.sep), '%sdata.grf' % leeClientDir)

    def maintenanceMakePackageSource(self):
        '''
        生成客户端打包源
        '''
        LeePublisher().makeSource()

    def maintenanceMakePackageSourceToZipfile(self):
        '''
        用于将指定的打包源压缩成一个 ZIP 文件
        这了会将可用的打包源列出来, 让用户可以进行选择
        '''
        self.leeCommon.cleanScreen()

        leeClientDir = self.leeCommon.getLeeClientDirectory()
        packageSourceDirnameList = LeePublisher().getPackageSourceList(os.path.abspath(leeClientDir + '..' + os.path.sep) + os.sep)
        if packageSourceDirnameList is None:
            self.leeCommon.exitWithMessage('很抱歉, 无法获取打包源列表, 程序终止')

        if not packageSourceDirnameList:
            self.leeCommon.exitWithMessage('没有发现任何可用的打包源, 请先生成一个吧')

        menus = []
        for packageSourceDirname in packageSourceDirnameList:
            menuItem = [packageSourceDirname, 'injectClass.makePackageSourceToZipfile(\'%s\')' % packageSourceDirname, None]
            menus.append(menuItem)

        self.leeCommon.simpleMenu(
            items = menus,
            title = '将指定的打包源压缩成 ZIP 文件',
            prompt = '请选择你想压缩的打包源目录',
            injectClass = self,
            cancelExec = 'injectClass.item_Main()',
            withCancel = True
        )

    def maintenanceMakePackageSourceToSetup(self):
        '''
        用于将指定的打包源制作成一个 Setup 安装程序
        这了会将可用的打包源列出来, 让用户可以进行选择
        '''
        self.leeCommon.cleanScreen()

        leeClientDir = self.leeCommon.getLeeClientDirectory()
        packageSourceDirnameList = LeePublisher().getPackageSourceList(os.path.abspath(leeClientDir + '..\\') + os.sep)
        if packageSourceDirnameList is None:
            self.leeCommon.exitWithMessage('很抱歉, 无法获取打包源列表, 程序终止')

        if not packageSourceDirnameList:
            self.leeCommon.exitWithMessage('没有发现任何可用的打包源, 请先生成一个吧')

        menus = []
        for packageSourceDirname in packageSourceDirnameList:
            menuItem = [packageSourceDirname, 'injectClass.makePackageSourceToSetup(\'%s\')' % packageSourceDirname, None]
            menus.append(menuItem)

        self.leeCommon.simpleMenu(
            items = menus,
            title = '将指定的打包源制作成安装程序',
            prompt = '请选择你想制作的打包源目录',
            injectClass = self,
            cancelExec = 'injectClass.item_Main()',
            withCancel = True
        )

    def item_SwitchWorkshop(self):
        '''
        菜单处理函数
        当选择“切换仙境传说主程序的版本”时执行
        '''
        self.leeCommon.cleanScreen()

        scriptDir = self.leeCommon.getScriptDirectory()
        clientList = self.leeCommon.getRagexeClientList(os.path.abspath(scriptDir + 'Patches') + os.sep)
        if clientList is None:
            self.leeCommon.exitWithMessage('很抱歉, 无法获取客户端版本列表, 程序终止')

        menus = []
        for client in clientList:
            menuItem = [client, 'injectClass.switchWorkshop(\'%s\')' % client, None]
            menus.append(menuItem)

        self.leeCommon.simpleMenu(
            items = menus,
            title = '切换仙境传说主程序的版本',
            prompt = '请选择你想切换到的版本',
            injectClass = self,
            cancelExec = 'injectClass.item_Main()',
            withCancel = True
        )

        return

    def item_ResetWorkshop(self):
        '''
        菜单处理函数
        当选择“重置 LeeClient 客户端到干净状态”时执行
        '''
        self.leeCommon.cleanScreen()

        if self.patchManager.canRevert():
            lines = [
                '此操作可以将 LeeClient 客户端恢复到干净状态',
                '请将自己添加的额外重要文件移出 LeeClient 目录, 避免被程序误删',
                ''
            ]
            title = '重置 LeeClient 客户端到干净状态'
            prompt = '是否立刻执行重置操作?'
            self.leeCommon.simpleConfirm(lines, title, prompt, self, 'menus.resetWorkshop()')
        else:
            self.leeCommon.exitWithMessage('您的客户端环境看起来十分干净, 不需要再进行清理了.')

    def item_MaintenanceUpdateButtonTranslateDB(self):
        '''
        菜单处理函数
        当选择“维护 - 更新客户端按钮的翻译数据库”时执行
        '''
        self.leeCommon.cleanScreen()

        lines = [
            '已汉化的内容将会被自动继承, 请不用担心',
            '涉及的数据库文件为: Resources/Databases/ButtonTranslate.json',
            ''
        ]
        title = '更新客户端按钮的翻译数据库'
        prompt = '是否执行更新操作?'
        self.leeCommon.simpleConfirm(lines, title, prompt, self, 'menus.maintenanceUpdateButtonTranslateDB()')

    def item_MaintenanceRunClientResourceCheck(self):
        '''
        菜单处理函数
        当选择“维护 - 对客户端资源进行完整性校验”时执行
        '''
        lines = [
            '此过程可以协助排除可能的一些图档丢失情况.',
            '不过由于需要对客户端的大量文件进行判断, 时间可能会比较长.'
            ''
        ]
        title = '对客户端资源进行完整性校验'
        prompt = '是否确认执行?'
        self.leeCommon.simpleConfirm(lines, title, prompt, self, 'menus.maintenanceRunClientResourceCheck()')

    def item_MaintenanceMakeDataToGrf(self):
        '''
        菜单处理函数
        当选择“维护 - 将 data 目录打包为标准 grf 文件”时执行
        '''
        lines = [
            '1. 进行此过程之前, 您必须已经切换到想要的客户端版本,',
            '否则最终生成的 data.grf 文件内容将不完整 (若程序发现会提示您).',
            '',
            '2. 将几万个文件打包压缩成 grf 文件需要有足够的磁盘空间, ',
            '压缩期间可能会极大占用CPU, 您可以随时用 Ctrl + C 终止打包过程.',
            '',
            '3. 生成后的 data.grf 文件将直接存放在 LeeClient 的根目录下.',
            '',
            '4. 仅支持在 Windows 系统使用此功能, Linux 或 macOS 暂不支持.',
            '----------------------------------------------------------------'
        ]
        title = '将 data 目录打包为标准 grf 文件'
        prompt = '是否已经清楚以上事项?'
        self.leeCommon.simpleConfirm(lines, title, prompt, self, 'menus.maintenanceMakeDataToGrf()')

    def item_MaintenanceMakePackageSource(self):
        '''
        菜单处理函数
        当选择“维护 - 生成客户端打包源”时执行
        '''
        self.maintenanceMakePackageSource()

    def item_MaintenanceMakePackageSourceToZipfile(self):
        '''
        菜单处理函数
        当选择“维护 - 将指定的打包源压缩成 ZIP 文件”时执行
        '''
        self.maintenanceMakePackageSourceToZipfile()

    def item_MaintenanceMakePackageSourceToSetup(self):
        '''
        菜单处理函数
        当选择“维护 - 将指定的打包源制作 Setup 安装程序”时执行
        '''
        self.maintenanceMakePackageSourceToSetup()

    def item_End(self):
        '''
        菜单处理函数
        当选择“退出程序”时执行
        '''
        self.leeCommon.exitWithMessage('感谢您的使用, 再见')
        return

def main():
    '''
    LeeClientAgent 的主入口函数
    '''
    leeCommon = LeeCommon()

    # 验证此脚本所处的位置, 不正确则报错并退出
    if not leeCommon.verifyAgentLocation():
        leeCommon.exitWithMessage('LeeClientAgent 所处的位置不正确, 拒绝执行')

    # 选择操作
    menus = [
        ['切换客户端到指定版本', 'injectClass.item_SwitchWorkshop()', None],
        ['重置 LeeClient 客户端到干净状态', 'injectClass.item_ResetWorkshop()', None],
        ['进行文件资源的完整性校验', 'injectClass.item_MaintenanceRunClientResourceCheck()', None],
        ['维护 - 将 data 目录打包为标准 grf 文件', 'injectClass.item_MaintenanceMakeDataToGrf()', None],
        ['维护 - 生成客户端打包源', 'injectClass.item_MaintenanceMakePackageSource()', None],
        ['维护 - 将指定的打包源压缩成 ZIP 文件', 'injectClass.item_MaintenanceMakePackageSourceToZipfile()', None],
        ['维护 - 将指定的打包源制作 Setup 安装程序', 'injectClass.item_MaintenanceMakePackageSourceToSetup()', None],
        # ['维护 - 更新客户端按钮的翻译数据库', 'injectClass.item_MaintenanceUpdateButtonTranslateDB()', None],
        ['退出程序', 'injectClass.item_End()', None]
    ]

    leeCommon.simpleMenu(
        items = menus,
        title = 'LeeClient 控制台',
        prompt = '请填写想要执行的任务的菜单编号',
        injectClass = LeeMenu(main)
    )

    # 若在 Win 环境下则输出 pause 指令, 暂停等待用户确认退出
    leeCommon.pauseScreen()

if __name__ == '__main__':
    main()
