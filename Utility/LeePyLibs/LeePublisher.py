# -*- coding: utf-8 -*-

import os
import re
import sys
import time
import uuid
import platform
import subprocess
import shutil

from LeePyLibs import LeeCommon
from LeePyLibs import LeeZipfile
from LeePyLibs import LeePatchManager
from LeePyLibs import LeeConfigure

if platform.system() == 'Windows':
	import winreg

class LeePublisher:
	def __init__(self):
		self.leeCommon = LeeCommon()
		self.patchManager = LeePatchManager()
	
	def makeSource(self):
		'''
		将 LeeClient 的内容复制到打包源目录(并删除多余文件)
		'''
		leeClientDir = self.leeCommon.getLeeClientDirectory()

		# 判断是否已经切换到某个客户端版本
		if not self.patchManager.canRevert():
			self.leeCommon.exitWithMessage('请先将 LeeClient 切换到某个客户端版本, 以便制作出来的 grf 文件内容完整.')

		# 判断 grf 文件是否已经生成
		if not self.leeCommon.isFileExists('%sdata.grf' % leeClientDir):
			self.leeCommon.exitWithMessage('请先将 data 目录打包为 data.grf, 以便提高文件系统的复制效率.')

		# 判断磁盘的剩余空间是否足够
		currentDriver = self.leeCommon.getScriptDirectory()[0]
		currentFreeSpace = self.leeCommon.getDiskFreeSpace(currentDriver)
		if currentFreeSpace <= 1024 * 1024 * 1024 * 3:
			self.leeCommon.exitWithMessage('磁盘 %s: 的空间不足 3GB, 请清理磁盘释放更多空间.' % currentDriver)

		# 生成一个 LeeClient 平级的发布目录
		nowTime = time.strftime("%Y%m%d_%H%M%S", time.localtime())
		releaseDirName = 'LeeClient_Release_%s' % nowTime
		releaseDirPath = '%s%s%s%s' % (
			os.path.abspath('%s../' % leeClientDir), os.path.sep,
			releaseDirName, os.path.sep
		)

		# 先列出需要复制到打包源的文件列表
		filterDirectories = ['Utility', 'data', '.git', '.vscode']
		filterFiles = ['.gitignore', '.DS_Store']

		copyFileList = []
		for dirpath, _dirnames, filenames in os.walk(os.path.join(leeClientDir, leeClientDir)):
			for filename in filenames:
				fullpath = os.path.join(dirpath, filename)

				# 过滤一下不需要导出的目录
				isBlocked = False
				for filterDir in filterDirectories:
					if ('%s%s%s' % (leeClientDir, filterDir, os.path.sep)).lower() in fullpath.lower(): 
						isBlocked = True
						break
				if isBlocked: continue
				
				# 过滤一下不需要导出的文件
				isBlocked = False
				for filterFile in filterFiles:
					if ('%s%s' % (leeClientDir, filterFile)).lower() in fullpath.lower(): 
						isBlocked = True
						break
				if isBlocked: continue
				
				# 记录到 copyFileList 表示需要复制此文件到打包源
				copyFileList.append(fullpath)
		
		# 把文件拷贝到打包源
		# TODO: 最好能够显示文件的复制进度
		# http://zzq635.blog.163.com/blog/static/1952644862013125112025129/
		for srcFilePath in copyFileList:
			relFilePath = os.path.relpath(srcFilePath, leeClientDir)
			dstFilePath = '%s%s' % (releaseDirPath, relFilePath)
			print('正在复制: %s' % relFilePath)
			os.makedirs(os.path.dirname(dstFilePath), exist_ok = True)
			shutil.copyfile(srcFilePath, dstFilePath)

		# 把最终发布源所在的目录当做参数返回值回传
		return releaseDirPath
	
	def getZipFilename(self, sourceDir):
		if sourceDir.endswith('\\') or sourceDir.endswith('/'):
			sourceDir = sourceDir[:-1]
		return '%s.zip' % sourceDir
	
	def getPackageSourceList(self, dirpath):
		'''
		根据指定的 dir 中枚举出子目录的名字 (即打包源的目录名)
		返回: Array 保存着每个子目录名称的数组
		'''
		dirlist = []
		
		try:
			list = os.listdir(dirpath)
		except:
			print('getPackageSourceList Access Deny')
			return None
		
		for dname in list:
			if not dname.lower().startswith('leeclient_release_'): continue
			if os.path.isdir(os.path.normpath(dirpath) + os.path.sep + dname):
				dirlist.append(dname)
		
		dirlist.sort()
		return dirlist

	def makeZip(self, sourceDir, zipSavePath):
		'''
		将打包源目录直接压缩成一个 zip 文件
		'''
		# https://blog.csdn.net/dou_being/article/details/81546172
		# https://blog.csdn.net/zhd199500423/article/details/80853405
		return LeeZipfile().zip(sourceDir, zipSavePath)
	
	def makeSetup(self, sourceDir, setupOutputDir = None):
		'''
		将打包源目录直接制作成一个 Setup 安装程序
		'''
		if setupOutputDir is None:
			setupOutputDir = './Output'

		sourceDir = os.path.abspath(sourceDir)
		setupOutputDir = os.path.abspath(setupOutputDir)

		# 判断 InnoSetup 是否已经安装
		if not self.__isInnoSetupInstalled():
			# 若未安装则进行安装 (此处需要管理员权限)
			if self.__instInnoSetup(): 
				# 安装后将补丁文件复制到 InnoSetup 的安装目录中
				self.__applyInnoSetupLdrPatch()
			else:
				self.leeCommon.exitWithMessage('无法成功安装 Inno Setup, 请联系作者进行排查')

		# 再次进行环境检查, 确保一切就绪
		if not self.__checkInnoSetupStatus():
			self.leeCommon.exitWithMessage('本机的 Inno Setup 环境不正确, 无法继续进行工作.')

		# 读取目前的配置值, 请求用户确认后继续
		configure = self.__choiceConfigure()
		if configure is None:
			self.leeCommon.exitWithMessage('您没有确定用于生成 Setup 的配置, 无法继续进行工作.')

		# 若是第一次使用, 则需要帮用户生成一个 GUID 并嘱咐用户保存 GUID
		if str(configure['LeeAppId']).lower() == 'none':
			# 需要帮用户初始化一个 AppId 并告知用户记录好这个值
			print('发现配置 “%s” 的 LeeAppId 值为 None' % configure['LeeName'])
			print('您必须为其分配一个 GUID. 程序已为您自动生成了一个 GUID:')
			print('')
			print(str(uuid.uuid1()).upper())
			print('')
			print('请复制后粘贴到 LeeClientAgent.yml 文件中 SetupConfigure 节点的')
			print('对应选项里面替换掉 None 值, 然后再重试一次.')
			print('')
			self.leeCommon.pauseScreen()
			sys.exit(0)

		# 在 configure 中补充其他参数
		configure['LeePackageSourceDirPath'] = sourceDir
		configure['LeeOutputDir'] = setupOutputDir
		configure['LeeAppId'] = (r'{{%s}' % configure['LeeAppId']).upper()

		# 确认打包源中配置里填写的“主程序”和“游戏设置程序”都存在, 不在则中断
		leeAppExePath = os.path.abspath('%s/%s' % (sourceDir, configure['LeeAppExeName']))
		leeGameSetupExePath = os.path.abspath('%s/%s' % (sourceDir, configure['LeeGameSetupExeName']))
		if not self.leeCommon.isFileExists(leeAppExePath):
			self.leeCommon.exitWithMessage('LeeAppExeName 指向的主程序 %s 不在打包源目录中: %s' % (configure['LeeAppExeName'], sourceDir))
		if not self.leeCommon.isFileExists(leeGameSetupExePath):
			self.leeCommon.exitWithMessage('leeGameSetupExePath 指向的主程序 %s 不在打包源目录中: %s' % (configure['LeeGameSetupExeName'], sourceDir))

		# 读取脚本模板
		scriptTemplateContent = self.__readScriptTemplate()

		# 根据配置进行配置项的值替换
		scriptFinallyContent = self.__generateFinallyScript(scriptTemplateContent, configure)

		# 将最终的脚本保存到临时目录中
		scriptCachePath = self.__saveFinallyScriptToCache(scriptFinallyContent)

		# 调用 ISCC.exe 执行 Setup 的打包操作
		return self.__runInnoScript(scriptCachePath)
	
	def __isInnoSetupInstalled(self):
		'''
		判断 Inno Setup 是否已经安装到电脑中
		'''
		innoSetupDir = self.__getInnoSetupInstallPath()
		if innoSetupDir is None: return False
		return self.leeCommon.isFileExists('%sCompil32.exe' % innoSetupDir)
	
	def __getInnoSetupInstallPath(self):
		'''
		获取 Inno Setup 的安装目录, 末尾自动补斜杠
		'''
		try:
			if platform.system() != 'Windows':
				self.leeCommon.exitWithMessage('很抱歉, %s 此函数目前只能在 Windows 平台上运行.' % __name__)
			
			# 根据不同的平台切换注册表路径
			if platform.machine() == 'AMD64':
				innoSetup_key = winreg.OpenKey(
					winreg.HKEY_LOCAL_MACHINE, 
					'SOFTWARE\\WOW6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\Inno Setup 5_is1'
				)
			else:
				innoSetup_key = winreg.OpenKey(
					winreg.HKEY_LOCAL_MACHINE,
					'SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\Inno Setup 5_is1'
				)

			# 读取 Inno Setup 的安装目录
			installLocation, _value_type = winreg.QueryValueEx(innoSetup_key, 'InstallLocation')
			if not (installLocation.endswith('\\') or installLocation.endswith('/')):
				installLocation = '%s%s' % (installLocation, os.path.sep)
			
			return installLocation
		except:
			return None
	
	def __applyInnoSetupLdrPatch(self):
		'''
		应用 SetupLdr.e32 补丁到 Inno Setup 的安装目录下 (要求管理员权限)
		'''
		# TODO: 此过程要求管理员权限, 看看如何检测一下

		scriptDir = self.leeCommon.getScriptDirectory()
		innoSetupDir = self.__getInnoSetupInstallPath()

		if innoSetupDir is None: return False

		srcFilePath = ('%sBin/InnoSetup/Resources/Installer/SetupLdr.e32' % scriptDir).replace('/', os.path.sep)
		dstFilePath = ('%sSetupLdr.e32' % innoSetupDir)
		bakFilePath = ('%sSetupLdr.e32.bak' % innoSetupDir)

		if (not self.leeCommon.isFileExists(bakFilePath)) and self.leeCommon.isFileExists(dstFilePath):
			shutil.copyfile(dstFilePath, bakFilePath)
		
		if not self.leeCommon.isFileExists(srcFilePath): return False
		os.remove(dstFilePath)
		shutil.copyfile(srcFilePath, dstFilePath)

		return True
	
	def __checkInnoSetupStatus(self):
		'''
		检查 Inno Setup 的状态是否正常且符合要求
		'''
		innoSetupDir = self.__getInnoSetupInstallPath()
		if innoSetupDir is None: return False

		# Inno Setup 是否已经安装
		if not self.__isInnoSetupInstalled(): return False

		# Inno Setup 的 ISCC.exe 是否存在
		if not self.leeCommon.isFileExists('%sISCC.exe' % innoSetupDir): return False
		
		# 是否已经安装了 SetupLdr.e32 补丁
		setupLdrMD5 = self.leeCommon.getMD5ForSmallFile('%sSetupLdr.e32' % innoSetupDir)
		if setupLdrMD5 != '544dbcf30c8ccb55082709b095173f6c': return False

		return True

	def __instInnoSetup(self):
		'''
		安装 Inno Setup 并确保安装成功 (要求管理员权限)
		'''
		# TODO: 此过程要求管理员权限, 看看如何检测一下

		# 先确认 Inno Setup 的安装程序是否存在
		scriptDir = self.leeCommon.getScriptDirectory()
		installerFilePath = ('%sBin/InnoSetup/Resources/Installer/innosetup-5.6.1-unicode.exe' % scriptDir).replace('/', os.path.sep)
		if not self.leeCommon.isFileExists(installerFilePath):
			return False
		
		# 执行静默安装过程
		setupProc = subprocess.Popen('%s /VERYSILENT' % installerFilePath, 
			stdout = sys.stdout, cwd = os.path.dirname(installerFilePath)
		)
		setupProc.wait()

		# 确认结果并输出提示信息表示压缩结束
		return (setupProc.returncode == 0 and self.__isInnoSetupInstalled())
	
	def choiceExit(self):
		print('不选择任何一个配置的话, 无法继续工作, 请重试.')

	def __choiceConfigure(self):
		'''
		让用户选择一个生成 Setup 的配置
		'''
		# 读取现在的所有 setup 配置
		setupConfigure = LeeConfigure().get('SetupConfigure')

		# 若只有一个配置, 则直接选中这个配置, 进入用户确认阶段
		if len(setupConfigure) > 1:
			# 列出来让用户进行选择, 选中哪个就把配置读取出来返回
			menus = []
			for cfgKey, cfgValue in enumerate(setupConfigure):
				menuItem = [cfgValue['LeeName'], None, cfgKey]
				menus.append(menuItem)
			
			configure = self.leeCommon.simpleMenu(
				items = menus,
				title = '选择生成配置', 
				prompt = '请选择用于生成安装程序的配置',
				injectClass = self, 
				cancelExec = 'injectClass.choiceExit()', 
				withCancel = True,
				resultMap = setupConfigure
			)
		else:
			configure = setupConfigure[0]

		# 把配置内容列出来让用户进行最终确认
		lines = self.__getConfigureInfos(configure)
		title = '确认配置的各个选项值'
		prompt = '是否继续?'
		
		if not self.leeCommon.simpleConfirm(lines, title, prompt, None, None):
			self.leeCommon.exitWithMessage('感谢您的使用, 再见')
		
		return configure
	
	def __getConfigureInfos(self, configure, dontPrint = True):
		'''
		给定一个配置的字典对象, 把内容构建成可读样式, 必要的话打印出来
		'''
		configureInfos = [
			'配置名称(LeeName): %s' % configure['LeeName'],
			'安装包唯一编号(LeeAppId): %s' % configure['LeeAppId'],
			'游戏名称(LeeAppName): %s' % configure['LeeAppName'],
			'游戏主程序(LeeAppExeName): %s' % configure['LeeAppExeName'],
			'安装包版本号(LeeAppVersion): %s' % configure['LeeAppVersion'],
			'安装包发布者(LeeAppPublisher): %s' % configure['LeeAppPublisher'],
			'发布者官网(LeeAppURL): %s' % configure['LeeAppURL'],
			'开始菜单程序组名称(LeeDefaultGroupName): %s' % configure['LeeDefaultGroupName'],
			'设置程序在开始菜单的名称(LeeGameSetupName): %s' % configure['LeeGameSetupName'],
			'设置程序在安装目录中的实际文件名(LeeGameSetupExeName): %s' % configure['LeeGameSetupExeName'],
			'安装时的默认目录名(LeeDefaultDirName): %s' % configure['LeeDefaultDirName'],
			'最终输出的安装程序文件名(LeeOutputBaseFilename): %s' % configure['LeeOutputBaseFilename'],
			'----------------------------------------------------------------',
			'若想修改以上选项的值, 或者想对他们的作用有更详细的了解, 请编辑',
			'Utility 目录下的 LeeClientAgent.yml 配置文件.',
			'----------------------------------------------------------------'
		]

		if not dontPrint: print('\r\n'.join(configureInfos))
		return configureInfos
	
	def __readScriptTemplate(self):
		'''
		获取 Inno Setup 的脚本模板并作为字符串返回
		'''
		scriptDir = self.leeCommon.getScriptDirectory()
		scriptTemplateFilePath = ('%sBin/InnoSetup/Resources/Scripts/Scripts_Template.iss' % scriptDir).replace('/', os.path.sep)

		if not self.leeCommon.isFileExists(scriptTemplateFilePath): return None
		return open(scriptTemplateFilePath, 'r', encoding = 'utf8').read()

	def __generateFinallyScript(self, templateContent, configure):
		'''
		把配置套到模板中, 并将处理后的脚本内容返回
		'''
		finallyContent = templateContent

		for k,v in configure.items():
			if v is None: continue
			rePattern = '(#define %s ".*?")' % k
			searchResult = re.search(rePattern, finallyContent)
			if searchResult is None: continue
			finallyContent = finallyContent.replace(searchResult.group(0), '#define %s "%s"' % (k, v))

		return finallyContent

	def __saveFinallyScriptToCache(self, finallyContent):
		'''
		将给定的最终脚本内容保存到一个临时目录中, 并返回脚本的全路径
		'''
		scriptDir = self.leeCommon.getScriptDirectory()
		scriptCacheDir = ('%sBin/InnoSetup/Cache/' % scriptDir).replace('/', os.path.sep)
		os.makedirs(scriptCacheDir, exist_ok = True)

		contentHash = self.leeCommon.getMD5ForString(finallyContent)
		scriptCachePath = os.path.abspath('%s%s.iss' % (scriptCacheDir, contentHash))

		if self.leeCommon.isFileExists(scriptCachePath):
			os.remove(scriptCachePath)

		# TODO: 这里的编码可能需要处理一下, 不能使用 utf8 编码
		# 开始菜单中的游戏设置快捷方式名称设置为 utf8 编码后, 实际上写入系统时被解读为 gbk 编码了 
		# 可能与现在用的 Inno Setup 默认语言文件的 Codepage 有一定关系, 需要研究一下
		cfile = open(scriptCachePath, 'w+', encoding = 'utf8')
		cfile.write(finallyContent)
		cfile.close()

		return scriptCachePath

	def __runInnoScript(self, scriptPath):
		'''
		调用 ISCC.exe 进行安装程序的制作, 同步等待结束
		'''
		innoSetupDir = self.__getInnoSetupInstallPath()
		if innoSetupDir is None: return False

		isccPath = '%sISCC.exe' % innoSetupDir
		if not self.leeCommon.isFileExists(isccPath): return False

		isccProc = subprocess.Popen('%s "%s"' % (isccPath, scriptPath), 
			stdout = sys.stdout, cwd = os.path.dirname(scriptPath)
		)
		isccProc.wait()
	
		return isccProc.returncode == 0
