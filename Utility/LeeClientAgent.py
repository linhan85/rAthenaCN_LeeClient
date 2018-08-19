#!/usr/local/bin/python3
# -*- coding: utf-8 -*-

import os

from LeePyLibs import LeeCommon, LeeConstant, LeeButtonTranslator, LeeButtonRender, LeePatchManager

# pip3 install pygame -i https://pypi.douban.com/simple --trusted-host=pypi.douban.com
# pip3 install pillow -i https://pypi.douban.com/simple --trusted-host=pypi.douban.com

# ==============================================================================
# 常量定义
# ==============================================================================

LeeConstant.Environment = 'develop'

# ==============================================================================
# 类的定义和实现
# ==============================================================================

# class LeeVerifier:
# 	'''
# 	这个类主要实现了对 RO 常用客户端文件格式的简单解析
# 	目的用于验证客户端的文件是否完整
# 	'''
# 	pass

class LeeMenu:
	def __init__(self, mainFunc, leeCommon, patchManager):
		self.item_Main = main
		self.patchManager = patchManager
		self.leeCommon = leeCommon

	def resetWorkshop(self):
		'''
		重置 LeeClient 客户端环境
		为接下来切换其他版本的客户端做好准备
		'''
		try:
			self.patchManager.doRevertPatch()
			print('已成功重置 LeeClient 客户端环境')
		except:
			print('很抱歉, 重置 LeeClient 客户端环境的过程中发生了意外, 请检查结果')

	def switchWorkshop(self, clientver):
		'''
		重置工作区, 并切换 LeeClient 到指定的客户端版本
		'''
		if self.patchManager.hasSomethingCanBeRevert():
			lines = [
				'在切换版本之前, 需要将 LeeClient 客户端恢复到干净状态',
				'请将自己添加的额外重要文件移出 LeeClient 目录, 避免被程序误删'
				''
			]
			title = '切换主程序版本到 %s' % clientver
			prompt = '是否立刻执行重置操作?'
			self.leeCommon.simpleConfirm(lines, title, prompt, self, 'menus.resetWorkshop()')

		# 将对应的资源覆盖到 LeeClient 主目录
		print('正在切换版本, 请耐心等待...')
		if not self.patchManager.doApplyPatch(clientver):
			print('很抱歉, 切换仙境传说的主程序到 %s 版本的时发生错误, 请检查结果' % clientver)
		else:
			print('已切换仙境传说的主程序到 %s 版本\r\n' % clientver)
	
	def updateButtonTranslateDataBase(self):
		'''
		根据目前 RagexeClient 中各个客户端的 Resource/Original 目录中的最新文件
		来更新目前正在使用的按钮汉化数据库文件
		'''
		try:
			print('正在读取数据库...')
			LeeButtonTranslator.loadTranslate()
			print('正在根据目前 Patches/RagexeClient 的内容升级数据库...')
			LeeButtonTranslator.updateTranslate()
			print('正在保存数据库...')
			LeeButtonTranslator.saveTranslate()
			print('更新操作已经完成, 请确认文件的变更内容...\r\n')
		except:
			raise
	
	def maintenanceApplyButtonTranslate(self):
		'''
		根据按钮汉化数据库的内容, 对客户端按钮进行汉化
		'''
		LeeButtonTranslator.doApplyButtonTranslate()
		pass

	def maintenanceRevertButtonTranslate(self):
		'''
		根据上次对按钮汉化时备份的信息, 删掉被汉化出来的按钮文件
		'''
		try:
			LeeButtonTranslator.doRevertButtonTranslate()
			print('已成功撤销对客户端按钮的汉化')
		except:
			print('很抱歉, 撤销对客户端按钮的汉化过程中发生了意外, 请检查结果')
			
	def item_SwitchWorkshop(self):
		'''
		菜单处理函数
		当选择“切换仙境传说主程序的版本”时执行
		'''
		self.leeCommon.cleanScreen()
		
		scriptDir = self.leeCommon.getScriptDirectory()
		clientList = self.leeCommon.getRagexeClientList(os.path.abspath(scriptDir + 'Patches/RagexeClient') + os.sep)
		
		menus = []
		for client in clientList:
			menuItem = [client, 'menus.switchWorkshop(\'%s\')' % client]
			menus.append(menuItem)
		self.leeCommon.simpleMenu(menus, '切换仙境传说主程序的版本', '请选择你想切换到的版本', self, withcancel = True)
		
		return

	def item_ResetWorkshop(self):
		'''
		菜单处理函数
		当选择“重置 LeeClient 客户端到干净状态”时执行
		'''
		self.leeCommon.cleanScreen()
		
		if self.patchManager.hasSomethingCanBeRevert():
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

	def item_UpdateButtonTranslateDataBase(self):
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
		self.leeCommon.simpleConfirm(lines, title, prompt, self, 'menus.updateButtonTranslateDataBase()')

	def item_MaintenanceApplyButtonTranslate(self):
		'''
		菜单处理函数
		当选择“维护 - 执行客户端按钮汉化”时执行
		'''
		self.maintenanceApplyButtonTranslate()
		pass

	def item_MaintenanceRevertButtonTranslate(self):
		'''
		菜单处理函数
		当选择“维护 - 撤销客户端按钮汉化”时执行
		'''
		self.maintenanceRevertButtonTranslate()
		pass

	def item_End(self):
		'''
		菜单处理函数
		当选择“退出程序”时执行
		'''
		self.leeCommon.exitWithMessage('感谢您的使用, 再见')
		return
	
def main():
	'''
	此脚本的主入口函数
	'''
	# 验证此脚本所处的位置, 不正确则报错并退出
	if not LeeCommon.verifyAgentLocation():
		LeeCommon.exitWithMessage('LeeClientAgent 所处的位置不正确, 拒绝执行')
	
	# 获取支持的客户端版本列表
	scriptDir = LeeCommon.getScriptDirectory()
	ragexeClientList = LeeCommon.getRagexeClientList(scriptDir + 'Patches/RagexeClient')
	if ragexeClientList is None:
		LeeCommon.exitWithMessage('很抱歉, 无法获取客户端版本列表, 程序终止')
	
	# 选择操作
	menus = [
		['切换仙境传说主程序的版本', 'menus.item_SwitchWorkshop()'],
		['重置 LeeClient 客户端到干净状态', 'menus.item_ResetWorkshop()'],
		['维护 - 更新客户端按钮的翻译数据库', 'menus.item_UpdateButtonTranslateDataBase()'],
		['维护 - 执行客户端按钮汉化', 'menus.item_MaintenanceApplyButtonTranslate()'],
		['维护 - 撤销客户端按钮汉化', 'menus.item_MaintenanceRevertButtonTranslate()'],
		['退出程序', 'menus.item_End()']
	]
	title = 'LeeClient 控制台'
	prompt = '请填写想要执行的任务的菜单编号'
	LeeCommon.simpleMenu(menus, title, prompt, LeeMenu(main, LeeCommon, LeePatchManager))
	
	# 若在 Win 环境下则输出 pause 指令, 暂停等待用户确认退出
	LeeCommon.pauseScreen()

if __name__ == '__main__':
	main()
