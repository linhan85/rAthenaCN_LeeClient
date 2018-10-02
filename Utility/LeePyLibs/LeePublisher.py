# -*- coding: utf-8 -*-

import os
import sys
import time
import platform
import subprocess
import shutil

from LeePyLibs import LeeCommon
from LeePyLibs import LeeZipfile
from LeePyLibs import LeePatchManager

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
	
	def makeSetup(self, sourceDir, setupSavePath):
		'''
		将打包源目录直接制作成一个 Setup 安装程序
		'''
		# http://www.jrsoftware.org/isdl.php
		pass
