# -*- coding: utf-8 -*-

import os
import json
import shutil
import time

class _LeePatchManager:
	'''
	用于管理补丁文件列表的操作类
	'''
	class SourceFileNotFoundError(FileNotFoundError): pass

	def __init__(self, leeCommon):
		self.leeCommon = leeCommon
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
		scriptDir = self.leeCommon.getScriptDirectory()
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
		scriptDir = self.leeCommon.getScriptDirectory()
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
		scriptDir = self.leeCommon.getScriptDirectory()
		leeClientDir = self.leeCommon.getLeeClientDirectory()
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
	
	def hasSomethingCanBeRevert(self):
		self.__loadSession()
		leeClientDir = self.leeCommon.getLeeClientDirectory()

		restoreFileInfo = []

		for folder in self.forceRemoveDirs:
			for dirpath, _dirnames, filenames in os.walk(os.path.join(leeClientDir, folder)):
				for filename in filenames:
					fullpath = os.path.join(dirpath, filename)
					restoreFileInfo.append([1, os.path.relpath(fullpath, leeClientDir)])

		for item in self.patchesFiles:
			path = item['dst']
			restoreFileInfo.append([1, path])
		
		return len(restoreFileInfo) > 0
		
	def doRevertPatch(self, loadSession = True):
		if loadSession:
			self.__loadSession()

		leeClientDir = self.leeCommon.getLeeClientDirectory()
		scriptDir = self.leeCommon.getScriptDirectory()
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
		
		self.leeCommon.removeEmptyDirectorys(leeClientDir)
		return True
	
	def doApplyPatch(self, clientver):
		'''
		应用特定版本的补丁
		'''
		scriptDir = self.leeCommon.getScriptDirectory()
		clientList = self.leeCommon.getRagexeClientList(os.path.abspath(scriptDir + 'Patches/RagexeClient') + os.sep)
		
		if not clientver in clientList:
			self.leeCommon.exitWithMessage('您期望切换的版本号 %s 是无效的' % clientver)
		
		beforeDir = self.leeCommon.getBeforePatchesDirectory()
		ragexeDir = self.leeCommon.getClientBuildDirectory(clientver)
		originDir = self.leeCommon.getClientOriginDirectory(clientver)
		translatedDir = self.leeCommon.getClientTranslatedDirectory(clientver)
		afterDir = self.leeCommon.getAfterPatchesDirectory()

		# 确认对应的资源目录在是存在的
		if not self.leeCommon.isDirectoryExists(beforeDir):
			self.leeCommon.exitWithMessage('无法找到 BeforePatches 目录: %s' % beforeDir)
		if not self.leeCommon.isDirectoryExists(ragexeDir):
			self.leeCommon.exitWithMessage('无法找到 %s 版本的 Ragexe 目录: %s' % (clientver, ragexeDir))
		if not self.leeCommon.isDirectoryExists(originDir):
			self.leeCommon.exitWithMessage('无法找到 %s 版本的 Original 目录: %s' % (clientver, originDir))
		if not self.leeCommon.isDirectoryExists(translatedDir):
			self.leeCommon.exitWithMessage('无法找到 %s 版本的 Translated 目录: %s' % (clientver, translatedDir))
		if not self.leeCommon.isDirectoryExists(afterDir):
			self.leeCommon.exitWithMessage('无法找到 AfterPatches 目录: %s' % afterDir)
		
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
