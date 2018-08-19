#!/usr/local/bin/python3
# -*- coding: utf-8 -*-

import copy
import distutils
import hashlib
import json
import os
import platform
import re
import shutil
import sys
import time
from distutils import dir_util
from io import BytesIO, StringIO

from LeePyLibs import LeeCommon, LeeConstant, LeeButtonTranslator, LeeButtonRender

# pip3 install pygame -i https://pypi.douban.com/simple --trusted-host=pypi.douban.com
# pip3 install pillow -i https://pypi.douban.com/simple --trusted-host=pypi.douban.com

# ==============================================================================
# 常量定义
# ==============================================================================

LeeConstant.Environment = 'develop'

# ==============================================================================
# 类的定义和实现
# ==============================================================================

class LeePatchManager:
	'''
	用于管理补丁文件列表的操作类
	'''
	class SourceFileNotFoundError(FileNotFoundError): pass

	def __init__(self, common):
		self.common = common
		self.stagingFiles = []
		self.patchesFiles = []
		self.backupFiles = []

		self.forceRemoveDirs = [
			'AI',
			'AI_sakray',
			'_tmpEmblem',
			'memo',
			'Replay',
			'SaveData',
			'Navigationdata',
			'System'
		]
		return

	def __getSessionPath(self):
		'''
		获取最后一次应用补丁时，路径信息数据库的存储路径
		'''
		scriptDir = self.common.getScriptDirectory()
		patchesDir = os.path.abspath('%s/Patches/' % scriptDir)
		os.makedirs(patchesDir, exist_ok = True)
		sessionInfoFile = os.path.abspath('%s/LastPatchesInfo.json' % patchesDir)
		return sessionInfoFile

	def __createSession(self):
		self.stagingFiles.clear()
		self.backupFiles.clear()
		self.patchesFiles.clear()
	
	def __loadSession(self):
		sessionInfoFile = self.__getSessionPath()
		if os.path.exists(sessionInfoFile) and os.path.isfile(sessionInfoFile):
			self.backupFiles.clear()
			self.patchesFiles.clear()

			patchesInfo = json.load(open(sessionInfoFile, 'r', encoding = 'utf-8'))
			self.backupFiles = patchesInfo['backuplist']
			self.patchesFiles = patchesInfo['patchlist']
			return True
		return False

	def __copyDirectory(self, srcDirectory):
		scriptDir = self.common.getScriptDirectory()
		useless_files = ['thumbs.db', '.ds_store', '.gitignore', '.gitkeep']
		
		# 复制文件，且记录所有可能会应用的目的地址
		for dirpath, _dirnames, filenames in os.walk(srcDirectory):
			for filename in filenames:
				if filename.lower() in useless_files: continue
				file_path = os.path.join(dirpath, filename)
				srcrel_path = os.path.relpath(file_path, scriptDir)
				dstrel_path = os.path.relpath(file_path, srcDirectory)
				self.stagingFiles.append({'src' : srcrel_path, 'dst' : dstrel_path})
	
	def __commitSession(self):
		scriptDir = self.common.getScriptDirectory()
		leeClientDir = self.common.getLeeClientDirectory()
		backupDir = os.path.abspath('%s/Patches/Backup' % scriptDir)

		try:
			# 确保来源文件都存在
			for item in self.stagingFiles:
				src_path = os.path.abspath('%s/%s' % (scriptDir, item['src']))
				if not (os.path.exists(src_path) and os.path.isfile(src_path)):
					raise self.SourceFileNotFoundError("Can't found source patch file : %s" % src_path)

			# 备份所有可能会被覆盖的文件，并记录备份成功的文件
			for item in self.stagingFiles:
				dst_path = os.path.abspath('%s/%s' % (leeClientDir, item['dst']))
				dst_dirs = os.path.dirname(dst_path)

				try:
					# 目的地文件已经存在，需要备份避免误删
					if os.path.exists(dst_path) and os.path.isfile(dst_path):
						backup_path = os.path.abspath('%s/%s' % (backupDir, item['dst']))
						backup_dirs = os.path.dirname(backup_path)
						os.makedirs(backup_dirs, exist_ok = True)
						shutil.copyfile(dst_path, backup_path)
						self.backupFiles.append(item['dst'])
				except BaseException as err:
					print('文件备份失败 : %s' % dst_path)
					raise err

			# 执行文件复制工作，并记录复制成功的文件
			for item in self.stagingFiles:
				src_path = os.path.abspath('%s/%s' % (scriptDir, item['src']))
				dst_path = os.path.abspath('%s/%s' % (leeClientDir, item['dst']))
				dst_dirs = os.path.dirname(dst_path)
				
				os.makedirs(dst_dirs, exist_ok = True)
				if os.path.exists(dst_path): os.remove(dst_path)
				shutil.copyfile(src_path, dst_path)
				# print('复制 %s 到 %s' % (src_path, dst_path))
				self.patchesFiles.append(item)

		except BaseException as err:
			# 根据 self.backupFiles 和 self.patchesFiles 记录的信息回滚后报错
			print('_commitSession 失败, 正在回滚...')
			if self.doRevertPatch(loadSession = False):
				print('回滚成功, 请检查目前的文件状态是否正确')
			else:
				print('很抱歉, 回滚失败了, 请检查目前的文件状态')
			return False

		# 记录备份和成功替换的文件信息
		sessionInfoFile = self.__getSessionPath()
		if os.path.exists(sessionInfoFile): os.remove(sessionInfoFile)
		json.dump({
			'patchtime' : time.strftime('%Y-%m-%d %H:%M:%S',time.localtime()),
			'backuplist' : self.backupFiles,
			'patchlist' : self.patchesFiles
		}, open(sessionInfoFile, 'w', encoding = 'utf-8'), indent = 4)
		
		return True
	
	def getRestoreFiles(self):
		self.__loadSession()
		leeClientDir = self.common.getLeeClientDirectory()

		restoreFileInfo = []

		for folder in self.forceRemoveDirs:
			for dirpath, _dirnames, filenames in os.walk(os.path.join(leeClientDir, folder)):
				for filename in filenames:
					fullpath = os.path.join(dirpath, filename)
					restoreFileInfo.append([1, os.path.relpath(fullpath, leeClientDir)])

		for item in self.patchesFiles:
			path = item['dst']
			restoreFileInfo.append([1, path])
		
		return restoreFileInfo
		
	def doRevertPatch(self, loadSession = True):
		if loadSession:
			self.__loadSession()

		leeClientDir = self.common.getLeeClientDirectory()
		scriptDir = self.common.getScriptDirectory()
		backupDir = os.path.abspath('%s/Patches/Backup' % scriptDir)
		sessionInfoFile = self.__getSessionPath()

		# 删除之前应用的文件
		for item in self.patchesFiles:
			abspath = os.path.abspath('%s/%s' % (leeClientDir, item['dst']))
			if os.path.exists(abspath) and os.path.isfile(abspath):
				# print('即将删除 : %s' % abspath)
				os.remove(abspath)

		# 删除一些需要强制移除的目录
		for folder in self.forceRemoveDirs:
			for dirpath, _dirnames, filenames in os.walk(os.path.join(leeClientDir, folder)):
				for filename in filenames:
					fullpath = os.path.join(dirpath, filename)
					if os.path.exists(fullpath) and os.path.isfile(fullpath):
						# print('强制移除 : %s' % fullpath)
						os.remove(fullpath)
		
		# 还原之前备份的文件列表
		for item in self.backupFiles:
			backup_path = os.path.abspath('%s/%s' % (backupDir, item))
			source_path = os.path.abspath('%s/%s' % (leeClientDir, item))
			shutil.copyfile(backup_path, source_path)
			pass
		
		if os.path.exists(backupDir) and os.path.isdir(backupDir):
			shutil.rmtree(backupDir)
		
		if os.path.exists(sessionInfoFile) and os.path.isfile(sessionInfoFile):
			os.remove(sessionInfoFile)
		
		self.common.removeEmptyDirectorys(leeClientDir)
		return True
	
	def doApplyPatch(self, clientver):
		'''
		应用特定版本的补丁
		'''
		scriptDir = self.common.getScriptDirectory()
		# leeClientDir = self.common.getLeeClientDirectory()
		clientList = LeeCommon.getRagexeClientList(os.path.abspath(scriptDir + 'Patches/RagexeClient') + os.sep)
		
		if not clientver in clientList:
			self.common.exitWithMessage('您期望切换的版本号 %s 是无效的' % clientver)
		
		beforeDir = self.common.getBeforePatchesDirectory()
		ragexeDir = self.common.getClientBuildDirectory(clientver)
		originDir = self.common.getClientOriginDirectory(clientver)
		translatedDir = self.common.getClientTranslatedDirectory(clientver)
		afterDir = self.common.getAfterPatchesDirectory()

		# 确认对应的资源目录在是存在的
		if not self.common.isDirectoryExists(beforeDir):
			self.common.exitWithMessage('无法找到 BeforePatches 目录: %s' % beforeDir)
		if not self.common.isDirectoryExists(ragexeDir):
			self.common.exitWithMessage('无法找到 %s 版本的 Ragexe 目录: %s' % (clientver, ragexeDir))
		if not self.common.isDirectoryExists(originDir):
			self.common.exitWithMessage('无法找到 %s 版本的 Original 目录: %s' % (clientver, originDir))
		if not self.common.isDirectoryExists(translatedDir):
			self.common.exitWithMessage('无法找到 %s 版本的 Translated 目录: %s' % (clientver, translatedDir))
		if not self.common.isDirectoryExists(afterDir):
			self.common.exitWithMessage('无法找到 AfterPatches 目录: %s' % afterDir)
		
		# 创建一个事务并执行复制工作, 最后提交事务
		self.__createSession()
		self.__copyDirectory(beforeDir)
		self.__copyDirectory(ragexeDir)
		self.__copyDirectory(originDir)
		self.__copyDirectory(translatedDir)
		self.__copyDirectory(afterDir)
		
		if not self.__commitSession():
			print('应用特定版本的补丁过程中发生错误, 终止...')
			return False
		
		return True

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
		restoreInfo = self.patchManager.getRestoreFiles()

		if len(restoreInfo) > 0:
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
		
		restoreInfo = self.patchManager.getRestoreFiles()
		
		if len(restoreInfo) > 0:
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
	LeeCommon.simpleMenu(menus, title, prompt, LeeMenu(main, LeeCommon, LeePatchManager(LeeCommon)))
	
	# 若在 Win 环境下则输出 pause 指令, 暂停等待用户确认退出
	LeeCommon.pauseScreen()

if __name__ == '__main__':
	main()
