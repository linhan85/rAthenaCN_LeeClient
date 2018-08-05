#!/usr/local/bin/python3
# -*- coding: UTF-8 -*-

import copy
import distutils
import hashlib
import json
import os
import platform
import shutil
import sys
import time
from distutils import dir_util

# ==============================================================================
# 常量定义
# ==============================================================================

class LeeConstant(object):
	'''
	常量操作类
	这个类里面的所有变量只能赋值一次, 随后再也禁止赋值
	'''
	class ConstError(PermissionError): pass
	
	def __setattr__(self, name, value):
		if name in self.__dict__.keys():
			raise self.ConstError("Can't rebind constant : %s" % name)
		self.__dict__[name] = value
	
	def __delattr__(self, name):
		if name in self.__dict__:
			raise  self.ConstError("Can't unbind constant : %s" % name)
		raise  NameError(name)

CONST = LeeConstant()

# CONST.ENV_DEBUG = True
# CONST.ENV_BLOCK_REMOVE = False

# ==============================================================================
# 类的定义和实现
# ==============================================================================

class LeeCommonLib:
	'''
	这个类用来存放一些通用的函数
	主要为了让后面代码的分类更加直观一些
	'''
	def atoi(self, val):
		'''
		用于将一个字符串尝试转换成 Int 数值
		转换成功则返回 Int 数值，失败则返回布尔类型的 False
		'''
		try:
			int(val)
			return int(val)
		except ValueError:
			return False

	def strDictItemExists(self, dictobj, key):
		'''
		判断字典指定的 key 是否存在
		如果存在, 那么判断它的值是否为空字符串, 任何一个不成立则返回 False
		'''
		if dictobj is None or key is None:
			return False
		if key not in dictobj:
			return False
		return not (dictobj[key] is None or len(dictobj[key]) <= 0)
	
	def md5(self, data):
		'''
		获得给定字符串的 MD5 哈希值
		'''
		m = hashlib.md5(data.encode(encoding='utf8'))
		return m.hexdigest()
	
	def getSpiltText(self, str, spiltchar, index):
		'''
		将字符串按照特定分隔符切割, 并取得指定位数的字符串
		'''
		fields = str.split(spiltchar)
		if len(fields) < index + 1:
			return None
		else:
			return fields[index]

	def getStringLen(self, val):
		'''
		计算字符串长度, 一个中文算两个字符
		'''
		length = len(val)
		utf8_length = len(val.encode('utf-8'))
		return int((utf8_length - length)/2 + length)

	def cleanScreen(self):
		'''
		用于清理终端的屏幕 (Win下测试过, Linux上没测试过)
		'''
		sysstr = platform.system()
		if (sysstr == 'Windows'):
			os.system('cls')
		else:
			os.system('clear')
	
	def pauseScreen(self):
		'''
		如果在 Win 平台下的话, 输出一个 pause 指令
		'''
		sysstr = platform.system()
		if (sysstr == 'Windows'):
			os.system('pause')

	def remove_file(self, path):
		'''
		能够忽略文件不存在错误的文件删除函数
		'''
		try:
			return os.remove(path)
		except FileNotFoundError:
			return None

	def remove_tree(self, path):
		'''
		能够忽略目录不存在错误的目录删除函数
		'''
		try:
			return dir_util.remove_tree(path)
		except FileNotFoundError:
			return None

	def removeEmptyDirectorys(self, folderpath):
		'''
		递归移除指定目录中的所有空目录
		'''
		for parent, _dirnames, _filenames in os.walk(folderpath, topdown = False):
			if not os.listdir(parent):
				os.rmdir(parent)

	def throwMessageAndExit(self, mes, print_func = None):
		'''
		抛出一个错误消息并终止脚本的运行
		'''
		if print_func is None:
			print(mes + '\r\n')
		else:
			print_func(mes + '\r\n')
		
		commonlib.pauseScreen()
		sys.exit(0)
		return

	def getScriptDirectory(self):
		'''
		获取当前脚本所在的目录位置 (末尾自动补充斜杠)
		'''
		return os.path.split(os.path.realpath(__file__))[0] + os.sep

	def getLeeClientDirectory(self):
		'''
		获取 LeeClient 的主目录 (末尾自动补充斜杠)
		'''
		scriptDir = self.getScriptDirectory()
		return os.path.abspath(scriptDir + '..') + os.sep

	def getBeforePatchesDirectory(self):
		'''
		获取通用的 BeforePatches 目录 (末尾自动补充斜杠)
		'''
		scriptDir = self.getScriptDirectory()
		return os.path.abspath("%s/Patches/Common/BeforePatches" % scriptDir) + os.sep

	def getAfterPatchesDirectory(self):
		'''
		获取通用的 AfterPatches 目录 (末尾自动补充斜杠)
		'''
		scriptDir = self.getScriptDirectory()
		return os.path.abspath("%s/Patches/Common/AfterPatches" % scriptDir) + os.sep

	def getClientBuildDirectory(self, clientver):
		'''
		获取客户端版本的 Build 目录 (末尾自动补充斜杠)
		'''
		scriptDir = self.getScriptDirectory()
		return os.path.abspath("%s/Patches/RagexeClient/%s/Ragexe/Build" % (scriptDir, clientver)) + os.sep
	
	def getClientOriginDirectory(self, clientver):
		'''
		获取客户端版本的 Original 目录 (末尾自动补充斜杠)
		'''
		scriptDir = self.getScriptDirectory()
		return os.path.abspath("%s/Patches/RagexeClient/%s/Resource/Original" % (scriptDir, clientver)) + os.sep
	
	def getClientTranslatedDirectory(self, clientver):
		'''
		获取客户端版本的 Translated 目录 (末尾自动补充斜杠)
		'''
		scriptDir = self.getScriptDirectory()
		return os.path.abspath("%s/Patches/RagexeClient/%s/Resource/Translated" % (scriptDir, clientver)) + os.sep
	
	def isDirectoryExists(self, dirpath):
		'''
		判断指定的目录是否存在
		'''
		return os.path.exists(dirpath) and os.path.isdir(dirpath)
	
	def getRagexeClientList(self, dirpath):
		'''
		根据指定的 dir 中枚举出子目录的名字
		这里的目录名称为 Ragexe 客户端版本号的日期
		
		返回: Array 保存着每个子目录名称的数组
		'''
		dirlist = []
		
		try:
			list = os.listdir(dirpath)
		except:
			print("getRagexeClientList Access Deny")
			return None
		
		for dname in list:
			if os.path.isdir(os.path.normpath(dirpath) + os.path.sep + dname):
				dirlist.append(dname)
		
		dirlist.sort()
		return dirlist

	def simpleConfirm(self, lines, title, prompt, evalcmd):
		'''
		简易的确认对话框
		'''
		commonlib.cleanScreen()
		if not title is None:
			titleFmt = '= %s%-' + str(60 - commonlib.getStringLen(title)) + 's ='
			print('================================================================')
			print(titleFmt % (title, ''))
			print('================================================================')
		
		for line in lines:
			print(line)
		
		print('')
		user_select = input(prompt + ' [Y/N]: ')
		print('----------------------------------------------------------------')
		
		if user_select in ('N', 'n'):
			mainMenu_End()
		elif user_select in ('Y', 'y'):
			eval(evalcmd)
		else:
			commonlib.throwMessageAndExit('请填写 Y 或者 N 之后回车确认, 请不要输入其他字符')
		
		return

	def simpleMenu(self, items, title, prompt, withcancel = False):
		'''
		简易的选择菜单
		'''
		commonlib.cleanScreen()
		if not title is None:
			titleFmt = '= %s%-' + str(60 - commonlib.getStringLen(title)) + 's ='
			print('================================================================')
			print(titleFmt % (title, ''))
			print('================================================================')
		
		print('')
		index = 0
		for item in items:
			print('%d - %s' % (index, item[0]))
			index = index + 1
		if withcancel:
			print('%d - %s' % (index, "取消"))
		print('')
		user_select = input('%s (%d - %d): ' % (prompt, 0, len(items) - 1))
		print('----------------------------------------------------------------')
		
		if (False == commonlib.atoi(user_select) and user_select != '0'):
			commonlib.throwMessageAndExit('请填写正确的菜单编号(纯数字), 不要填写其他字符')
			
		user_select = commonlib.atoi(user_select)

		if (user_select == len(items) and withcancel):
			eval("main()")
			return
		
		if (user_select >= len(items) or items[user_select] is None):
			commonlib.throwMessageAndExit('请填写正确的菜单编号(纯数字), 不要超出范围')
		elif (items[user_select][1] is not None):
			eval(items[user_select][1])
		
		return commonlib.atoi(user_select)

class LeePatchManager:
	'''
	用于管理补丁文件列表的操作类
	'''
	class SourceFileNotFoundError(FileNotFoundError): pass

	def __init__(self):
		self.commonlib = LeeCommonLib()
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

	def getRestoreFiles(self):
		self._loadSession()
		leeClientDir = self.commonlib.getLeeClientDirectory()

		restoreFileInfo = []

		for folder in self.forceRemoveDirs:
			for parent, _dirnames, filenames in os.walk(os.path.join(leeClientDir, folder)):
				for filename in filenames:
					fullpath = os.path.join(parent, filename)
					restoreFileInfo.append([1, os.path.relpath(fullpath, leeClientDir)])

		for item in self.patchesFiles:
			path = item['dst']
			restoreFileInfo.append([1, path])
		
		return restoreFileInfo
		
	def restorePatch(self, loadSession = True):
		if loadSession:
			self._loadSession()

		leeClientDir = self.commonlib.getLeeClientDirectory()
		scriptDir = self.commonlib.getScriptDirectory()
		backupDir = os.path.abspath("%s/Patches/Backup" % scriptDir)
		sessionInfoFile = self._getSessionPath()

		# 删除之前应用的文件
		for item in self.patchesFiles:
			abspath = os.path.abspath("%s/%s" % (leeClientDir, item['dst']))
			if os.path.exists(abspath) and os.path.isfile(abspath):
				# print("即将删除 : %s" % abspath)
				os.remove(abspath)

		# 删除一些需要强制移除的目录
		for folder in self.forceRemoveDirs:
			for parent, _dirnames, filenames in os.walk(os.path.join(leeClientDir, folder)):
				for filename in filenames:
					fullpath = os.path.join(parent, filename)
					if os.path.exists(fullpath) and os.path.isfile(fullpath):
						# print("强制移除 : %s" % fullpath)
						os.remove(fullpath)
		
		# 还原之前备份的文件列表
		for item in self.backupFiles:
			backup_path = os.path.abspath("%s/%s" % (backupDir, item))
			source_path = os.path.abspath("%s/%s" % (leeClientDir, item))
			shutil.copyfile(backup_path, source_path)
			pass
		
		if os.path.exists(backupDir) and os.path.isdir(backupDir):
			shutil.rmtree(backupDir)
		
		if os.path.exists(sessionInfoFile) and os.path.isfile(sessionInfoFile):
			os.remove(sessionInfoFile)
		
		self.commonlib.removeEmptyDirectorys(leeClientDir)

		return True
	
	def applyPatch(self, clientver):
		'''
		应用特定版本的补丁
		'''
		scriptDir = self.commonlib.getScriptDirectory()
		# leeClientDir = self.commonlib.getLeeClientDirectory()
		clientList = self.commonlib.getRagexeClientList(os.path.abspath(scriptDir + 'Patches/RagexeClient') + os.sep)
		
		if not clientver in clientList:
			self.commonlib.throwMessageAndExit('您期望切换的版本号 %s 是无效的' % clientver)
		
		beforeDir = self.commonlib.getBeforePatchesDirectory()
		ragexeDir = self.commonlib.getClientBuildDirectory(clientver)
		originDir = self.commonlib.getClientOriginDirectory(clientver)
		translatedDir = self.commonlib.getClientTranslatedDirectory(clientver)
		afterDir = self.commonlib.getAfterPatchesDirectory()

		# 确认对应的资源目录在是存在的
		if not self.commonlib.isDirectoryExists(beforeDir):
			self.commonlib.throwMessageAndExit('无法找到 BeforePatches 目录: %s' % beforeDir)
		if not self.commonlib.isDirectoryExists(ragexeDir):
			self.commonlib.throwMessageAndExit('无法找到 %s 版本的 Ragexe 目录: %s' % (clientver, ragexeDir))
		if not self.commonlib.isDirectoryExists(originDir):
			self.commonlib.throwMessageAndExit('无法找到 %s 版本的 Original 目录: %s' % (clientver, originDir))
		if not self.commonlib.isDirectoryExists(translatedDir):
			self.commonlib.throwMessageAndExit('无法找到 %s 版本的 Translated 目录: %s' % (clientver, translatedDir))
		if not self.commonlib.isDirectoryExists(afterDir):
			self.commonlib.throwMessageAndExit('无法找到 AfterPatches 目录: %s' % afterDir)
		
		# 创建一个事务并执行复制工作, 最后提交事务
		self._createSession()
		self._copyDirectory(beforeDir)
		self._copyDirectory(ragexeDir)
		self._copyDirectory(originDir)
		self._copyDirectory(translatedDir)
		self._copyDirectory(afterDir)
		
		if not self._commitSession():
			print("应用特定版本的补丁过程中发生错误, 终止...")
			return False
		
		return True

	def _getSessionPath(self):
		'''
		获取最后一次应用补丁时，路径信息数据库的存储路径
		'''
		scriptDir = self.commonlib.getScriptDirectory()
		patchesDir = os.path.abspath("%s/Patches/" % scriptDir)
		os.makedirs(patchesDir, exist_ok = True)
		sessionInfoFile = os.path.abspath("%s/LastPatchesInfo.json" % patchesDir)
		return sessionInfoFile

	def _createSession(self):
		self.stagingFiles.clear()
		self.backupFiles.clear()
		self.patchesFiles.clear()
	
	def _loadSession(self):
		sessionInfoFile = self._getSessionPath()
		if os.path.exists(sessionInfoFile) and os.path.isfile(sessionInfoFile):
			self.backupFiles.clear()
			self.patchesFiles.clear()

			patchesInfo = json.load(open(sessionInfoFile, 'r', encoding = 'utf-8'))
			self.backupFiles = patchesInfo['backuplist']
			self.patchesFiles = patchesInfo['patchlist']
			return True
		return False

	def _copyDirectory(self, srcDirectory):
		scriptDir = self.commonlib.getScriptDirectory()
		useless_files = ["thumbs.db", ".ds_store", ".gitignore", ".gitkeep"]
		
		# 复制文件，且记录所有可能会应用的目的地址
		for parent, _dirnames, filenames in os.walk(srcDirectory):
			for filename in filenames:
				if filename.lower() in useless_files: continue
				file_path = os.path.join(parent, filename)
				srcrel_path = os.path.relpath(file_path, scriptDir)
				dstrel_path = os.path.relpath(file_path, srcDirectory)
				self.stagingFiles.append({'src' : srcrel_path, 'dst' : dstrel_path})
	
	def _commitSession(self):
		scriptDir = self.commonlib.getScriptDirectory()
		leeClientDir = self.commonlib.getLeeClientDirectory()
		backupDir = os.path.abspath("%s/Patches/Backup" % scriptDir)

		try:
			# 确保来源文件都存在
			for item in self.stagingFiles:
				src_path = os.path.abspath("%s/%s" % (scriptDir, item['src']))
				if not (os.path.exists(src_path) and os.path.isfile(src_path)):
					raise self.SourceFileNotFoundError("Can't found source patch file : %s" % src_path)

			# 备份所有可能会被覆盖的文件，并记录备份成功的文件
			for item in self.stagingFiles:
				dst_path = os.path.abspath("%s/%s" % (leeClientDir, item['dst']))
				dst_dirs = os.path.dirname(dst_path)

				try:
					# 目的地文件已经存在，需要备份避免误删
					if os.path.exists(dst_path) and os.path.isfile(dst_path):
						backup_path = os.path.abspath("%s/%s" % (backupDir, item['dst']))
						backup_dirs = os.path.dirname(backup_path)
						os.makedirs(backup_dirs, exist_ok = True)
						shutil.copyfile(dst_path, backup_path)
						self.backupFiles.append(item['dst'])
				except BaseException as err:
					print("文件备份失败 : %s" % dst_path)
					raise err

			# 执行文件复制工作，并记录复制成功的文件
			for item in self.stagingFiles:
				src_path = os.path.abspath("%s/%s" % (scriptDir, item['src']))
				dst_path = os.path.abspath("%s/%s" % (leeClientDir, item['dst']))
				dst_dirs = os.path.dirname(dst_path)
				
				os.makedirs(dst_dirs, exist_ok = True)
				if os.path.exists(dst_path): os.remove(dst_path)
				shutil.copyfile(src_path, dst_path)
				# print("复制 %s 到 %s" % (src_path, dst_path))
				self.patchesFiles.append(item)

		except BaseException as err:
			# 根据 self.backupFiles 和 self.patchesFiles 记录的信息回滚后报错
			print("_commitSession 失败, 正在回滚...")
			if self.restorePatch(loadSession = False):
				print("回滚成功, 请检查目前的文件状态是否正确")
			else:
				print("很抱歉, 回滚失败了, 请检查目前的文件状态")
			return False

		# 记录备份和成功替换的文件信息
		sessionInfoFile = self._getSessionPath()
		if os.path.exists(sessionInfoFile): os.remove(sessionInfoFile)
		json.dump({
			'patchtime' : time.strftime('%Y-%m-%d %H:%M:%S',time.localtime()),
			'backuplist' : self.backupFiles,
			'patchlist' : self.patchesFiles
		}, open(sessionInfoFile, 'w', encoding = 'utf-8'), indent = 4)
		
		return True

# class LeeVerifier:
# 	'''
# 	这个类主要实现了对 RO 常用客户端文件格式的简单解析
# 	目的用于验证客户端的文件是否完整
# 	'''
# 	pass

# class TranslateMapDictItem:
# 	'''
# 	此类用于保存从翻译对照表中加载成功的内容
# 	'''
# 	def __init__(self, lineno = None, content = None, origin = None, target = None):
# 		'''
# 		类的初始化, 主要做赋值工作
# 		'''
# 		self.lineno = lineno	# 行号
# 		self.content = content	# 读取到的一整行信息
# 		self.origin = origin	# 原文
# 		self.target = target	# 译文
# 		return
	
# 	def __str__(self):
# 		return ('LineNo: %d\nContent: %s\nOrigin: %s\nTarget: %s\n' % (self.lineno, self.content, self.origin, self.target))

# class SingleKeyReferItem:
# 	'''
# 	引用计数的记录类, 就是一个简单的计数器
# 	'''
# 	def __init__(self, origin = None):
# 		self.origin = origin
# 		self.referCount = 0
# 		return
	
# 	def incRefer(self):
# 		'''
# 		引用计数器自增1次
# 		'''
# 		self.referCount = self.referCount + 1
# 		return
	
# 	def __str__(self):
# 		return ('Origin: %s\nReferCount: %d\n' % (self.origin, self.referCount))
		
# class LeeTransMsgStringTable:
# 	def __init__(self, mapsdir):
# 		self.dictTranslate = {}
# 		self.dictSingleTranslate = {}
		
# 		self.commonlib = LeeCommonLib()
# 		self.scriptDir = self.commonlib.getScriptDirectory()
# 		self.mapsdir = mapsdir
# 		return
	
# 	def execute(self, lang):
# 		'''
# 		对 RagexeClient 目录下的各个版本客户端的 msgstringtable.txt 执行汉化工作
# 		'''
# 		if not self.__loadTranslateDict(lang):
# 			self.commonlib.throwMessageAndExit('翻译映射表加载失败, 无法继续汉化')
		
# 		clientList = self.commonlib.getRagexeClientList(os.path.abspath(self.scriptDir + 'RagexeClient') + os.sep)
		
# 		for clientver in clientList:
# 			msgstringtablePath = os.path.abspath(self.scriptDir + 'RagexeClient' + os.sep + clientver) + os.sep
# 			msgstringtablePath = os.path.abspath(msgstringtablePath + 'Basic' + os.sep + 'data') + os.sep
			
# 			try:
# 				msgstringtableData = self.__loadMsgStringTable(msgstringtablePath + 'msgstringtable_original.txt')
# 				self.__translate(msgstringtableData)
# 				self.__saveMsgStringTable(msgstringtableData, msgstringtablePath + 'msgstringtable.txt')
# 				print('已成功汉化 %s 客户端版本的 msgstringtable.txt !' % clientver)
# 			except Exception as e:
# 				print('对 %s 客户端版本的 msgstringtable.txt 汉化出现了错误: %s' % (clientver, e))
# 				continue
		
# 		print('----------------------------------------------------------------')
# 		print('完成汉化之后您需要切换一次客户端版本, 才能使修改生效. 请务必记得')
# 		print('备份一下自己添加或修改的文件, 避免在切换版本的过程中被误删.')
		
# 		return
	
# 	def __buildKey(self, obj, index, callback, attr):
# 		'''
# 		类私有函数, 用于建立一个与上下文对象关联的 Key
# 		主要用于将 A-1, A, A+1 自己前后的两个对象的 origin (在 attr 里面指定) 构建成一个 key
# 		'''
# 		identity = ''
		
# 		if index >= 1: identity = '%s|' % callback(obj[index - 1], attr)
# 		identity = '%s%s|' % (identity, callback(obj[index], attr))
# 		if index + 1 < len(obj): identity = '%s%s|' % (identity, callback(obj[index + 1], attr))
# 		identity = self.commonlib.md5(identity)
		
# 		return identity
	
# 	def __buildKey_callback_for_attribute(self, item, attr):
# 		'''
# 		类私有函数, 服务于 __buildKey 的回调
# 		直接使用 eval 函数返回给定 item 指定的属性名称的值
# 		'''
# 		return eval('item.' + attr)
	
# 	def __buildKey_callback_for_msgstringtable_list(self, item, attr):
# 		'''
# 		类私有函数, 服务于 __buildKey 的回调
# 		将给定的 item 字符串按 # 分割, 返回第一个元素
# 		'''
# 		return self.commonlib.getSpiltText(item, '#', 0)

# 	def __loadMsgStringTable(self, path):
# 		'''
# 		类私有函数, 读取指定路径的 msgstringtable.txt 并返回一个列表
# 		'''
# 		file = open(path, 'r', encoding='gb18030')
# 		msgstringtableData = file.readlines()
# 		file.close()
		
# 		# 去掉每行结尾的换行符
# 		for index in range(len(msgstringtableData)):
# 			line = msgstringtableData[index]
# 			msgstringtableData[index] = line.rstrip()
		
# 		return msgstringtableData
		
# 	def __loadTranslateDict(self, lang):
# 		'''
# 		类私有函数, 用来载入特定语言的翻译字典文件
# 		'''
# 		mappath = os.path.abspath(self.mapsdir + lang + '.txt')
# 		if not (os.path.exists(mappath) and os.path.isfile(mappath)):
# 			self.commonlib.throwMessageAndExit('翻译映射表不存在, 请检查: %s' % mappath)
		
# 		# 仅在加载字典时需要的一个列表
# 		# 里面存放的都是 TranslateMapDictItem 对象
# 		translateMap = []
		
# 		# 将字典文件载入到内存中
# 		file = open(mappath, 'r', encoding='gb18030')
# 		line = file.readline()
# 		lineNo = 1
# 		while line:
# 			line = line.rstrip()
# 			fields = line.split('#')
# 			origin = self.commonlib.getSpiltText(line, '#', 0)
# 			target = self.commonlib.getSpiltText(line, '#', 1)
			
# 			if (len(fields) < 2 or origin.startswith('//')):
# 				line = file.readline()
# 				continue
			
# 			item = TranslateMapDictItem(lineNo, line, origin, target)
# 			translateMap.append(item)
# 			# print(item)
			
# 			line = file.readline()
# 			lineNo = lineNo + 1
# 		file.close()
		
# 		# 根据读取到的数组内容 基于上下文的原文(origin) 构建字典
# 		# 并保存 A 的 target 值作为字典的 value
# 		self.dictTranslate.clear()
		
# 		for index in range(len(translateMap)):
# 			item = translateMap[index]
# 			origin_key = self.__buildKey(translateMap, index, self.__buildKey_callback_for_attribute, 'origin')
			
# 			if origin_key not in self.dictTranslate:
# 				self.dictTranslate[origin_key] = item.target
		
# 		# 创建以 origin 为 key 的引用计数表(字典)
# 		dictRefer = {}
		
# 		for item in translateMap:
# 			key = self.commonlib.md5(item.origin)
			
# 			if key in dictRefer:
# 				dictRefer[key].incRefer()
# 			else:
# 				referItem = SingleKeyReferItem(item.origin)
# 				referItem.incRefer()
# 				dictRefer[key] = referItem
		
# 		# 将引用计数为 1 的项目挑出来, 单独建立一个独立项字典
# 		self.dictSingleTranslate.clear()
		
# 		for item in translateMap:
# 			key = self.commonlib.md5(item.origin)
			
# 			if key in dictRefer and dictRefer[key].referCount == 1:
# 				self.dictSingleTranslate[key] = item.target
		
# 		return True
	
# 	def __translate(self, msgstringtableData):
# 		'''
# 		根据字典来翻译 msgstringtableData 列表对象中的内容
# 		'''
# 		# 浅拷贝 msgstringtableData 列表
# 		msgstringtableBackupData = copy.copy(msgstringtableData)
		
# 		# 根据上下文字典进行翻译
# 		for index in range(len(msgstringtableBackupData)):
# 			line = msgstringtableBackupData[index]
# 			origin_key = self.__buildKey(msgstringtableBackupData, index, self.__buildKey_callback_for_msgstringtable_list, None)
			
# 			if self.commonlib.strDictItemExists(self.dictTranslate, origin_key):
# 				msgstringtableData[index] = self.dictTranslate[origin_key] + '#'
		
# 		# 根据独立项字典进行翻译
# 		for index in range(len(msgstringtableData)):
# 			line = msgstringtableData[index]
# 			line = self.commonlib.getSpiltText(line, '#', 0)
# 			key = self.commonlib.md5(line)
			
# 			if self.commonlib.strDictItemExists(self.dictSingleTranslate, key):
# 				msgstringtableData[index] = self.dictSingleTranslate[key] + '#'
		
# 		return
	
# 	def __saveMsgStringTable(self, msgstringtableData, savepath):
# 		'''
# 		将 msgstringtableData 列表对象的内容保存到文件
# 		'''
# 		file = open(savepath, 'w+', newline='', encoding='gb18030')
# 		for index in range(len(msgstringtableData)):
# 			msgstringtableData[index] = msgstringtableData[index] + os.linesep
# 			try:
# 				file.write(msgstringtableData[index])
# 			except:
# 				print('Index %d | Error: %s' % (index, msgstringtableData[index]))
# 		file.close
# 		return

# ==============================================================================
# 以下为未被封装为类的零散方法
# ==============================================================================

# 实体化公用库类
commonlib = LeeCommonLib()
patchManager = LeePatchManager()

def verifyAgentLocation():
	'''
	用于验证此脚本是否处于正确的运行位置
	'''
	scriptDir = commonlib.getScriptDirectory()
	leeClientDir = commonlib.getLeeClientDirectory()
	verifyPassFlag = True
	
	# 检查脚本所在的目录中, 是否存在特定的平级目录
	verifyDirList = ['Patches', '3rdparty']
	for dir in verifyDirList:
		verifyPath = (os.path.abspath(scriptDir + dir) + os.sep)
		if False == (os.path.isdir(verifyPath) and os.path.exists(verifyPath)):
			verifyPassFlag = False
	
	# 检查脚本所在的上级目录中, 是否存在特定的文件
	verifyFileList = ['cps.dll', 'aossdk.dll']
	for file in verifyFileList:
		verifyPath = (os.path.abspath(leeClientDir + file))
		if False == (os.path.isfile(verifyPath) and os.path.exists(verifyPath)):
			verifyPassFlag = False
	
	# 任何一个不通过, 都认为脚本所处的位置不正确, 终止执行
	if False == verifyPassFlag:
		commonlib.throwMessageAndExit('LeeClientAgent 所处的位置不正确, 拒绝执行')
	
	return

def resetWorkshop():
	'''
	重置 LeeClient 客户端环境
	为接下来切换其他版本的客户端做好准备
	'''
	try:
		patchManager.restorePatch()
		print('已成功重置 LeeClient 客户端环境')
	except:
		print('很抱歉, 重置 LeeClient 客户端环境的过程中发生了意外, 请检查结果')

def switchWorkshop(clientver):
	'''
	重置工作区, 并切换 LeeClient 到指定的客户端版本
	'''
	restoreInfo = patchManager.getRestoreFiles()

	if len(restoreInfo) > 0:
		lines = [
			'在切换版本之前, 需要将 LeeClient 客户端恢复到干净状态',
			'请将自己添加的额外重要文件移出 LeeClient 目录, 避免被程序误删'
			''
		]
		title = '切换主程序版本到 %s' % clientver
		prompt = '是否立刻执行重置操作?'
		commonlib.simpleConfirm(lines, title, prompt, 'resetWorkshop()')

	# 将对应的资源覆盖到 LeeClient 主目录
	print('正在切换版本, 请耐心等待...')
	if not patchManager.applyPatch(clientver):
		print('很抱歉, 切换仙境传说的主程序到 %s 版本的时发生错误, 请检查结果' % clientver)
	else:
		print('已切换仙境传说的主程序到 %s 版本\r\n' % clientver)
	
def mainMenu_ResetWorkshop():
	'''
	菜单处理函数
	当选择“重置 LeeClient 客户端到干净状态”时执行
	'''
	commonlib.cleanScreen()
	
	restoreInfo = patchManager.getRestoreFiles()
	
	if len(restoreInfo) > 0:
		lines = [
			'此操作可以将 LeeClient 客户端恢复到干净状态',
			'请将自己添加的额外重要文件移出 LeeClient 目录, 避免被程序误删',
			''
		]
		title = '重置 LeeClient 客户端到干净状态'
		prompt = '是否立刻执行重置操作?'
		commonlib.simpleConfirm(lines, title, prompt, 'resetWorkshop()')
	else:
		commonlib.throwMessageAndExit('您的客户端环境看起来十分干净, 不需要再进行清理了.')

def mainMenu_SwitchWorkshop():
	'''
	菜单处理函数
	当选择“切换仙境传说主程序的版本”时执行
	'''
	commonlib.cleanScreen()
	
	scriptDir = commonlib.getScriptDirectory()
	clientList = commonlib.getRagexeClientList(os.path.abspath(scriptDir + 'Patches/RagexeClient') + os.sep)
	
	menus = []
	for client in clientList:
		menuItem = [client, 'switchWorkshop(\'%s\')' % client]
		menus.append(menuItem)
	
	commonlib.simpleMenu(menus, '切换仙境传说主程序的版本', '请选择你想切换到的版本', withcancel = True)
	
	return

# def mainMenu_TransMsgStringTable():
# 	'''
# 	菜单处理函数
# 	当选择“汉化各版本客户端的 msgstringtable.txt 文件”时执行
# 	'''
# 	scriptDir = commonlib.getScriptDirectory()
# 	msgStringTableMapsDir = os.path.abspath(scriptDir + 'TranslateData' + os.sep + 'msgstringtable') + os.sep
	
# 	transMsg = LeeTransMsgStringTable(msgStringTableMapsDir)
# 	transMsg.execute('zh-CN')
# 	return
	
def mainMenu_End():
	'''
	菜单处理函数
	当选择“退出程序”时执行
	'''
	commonlib.throwMessageAndExit('感谢您的使用, 再见')
	return
	
def main():
	'''
	此脚本的主入口函数
	'''
	# 验证此脚本所处的位置, 不正确则报错并退出
	verifyAgentLocation()
	
	# 获取支持的客户端版本列表
	scriptDir = commonlib.getScriptDirectory()
	ragexeClientList = commonlib.getRagexeClientList(scriptDir + 'Patches/RagexeClient')
	if ragexeClientList is None:
		commonlib.throwMessageAndExit("很抱歉, 无法获取客户端版本列表, 程序终止")
	
	# 选择操作
	menus = [
		['切换仙境传说主程序的版本', 'mainMenu_SwitchWorkshop()'],
		['重置 LeeClient 客户端到干净状态', 'mainMenu_ResetWorkshop()'],
		# ['汉化各版本客户端的 msgstringtable.txt 文件', 'mainMenu_TransMsgStringTable()'],
		['退出程序', 'mainMenu_End()']
	]
	
	title = 'LeeClient 控制台'
	prompt = '请填写想要执行的任务的菜单编号'
	
	commonlib.simpleMenu(menus, title, prompt)
	
if __name__ == "__main__":
	main()
	commonlib.pauseScreen()
