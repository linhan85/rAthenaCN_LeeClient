# -*- coding: utf-8 -*-

import os
import json
import re
from LeePyLibs import LeeTowninfoLua
from LeePyLibs import LeeCommon

class LeeTowninfoTranslator:
	def __init__(self):
		self.leeCommon = LeeCommon()
		self.leeTowninfoLua = LeeTowninfoLua()
		self.translateDatabasePath = 'Resources/Databases/TowninfoTranslate.json'
		self.translateMap = []
	
	def loadTranslate(self, filename = None):
		if filename is None: filename = self.translateDatabasePath
		translatePath = '%s/%s' % (self.leeCommon.getScriptDirectory(), filename)
		self.translateMap = []
		if self.leeCommon.isFileExists(translatePath):
		    self.translateMap = json.load(open(translatePath, 'r', encoding='utf-8'))
	
	def saveTranslate(self, saveFilename = None):
		if saveFilename is None: saveFilename = self.translateDatabasePath
		scriptDir = self.leeCommon.getScriptDirectory()
		try:
			savePath = os.path.abspath('%s/%s' % (scriptDir, saveFilename))
			json.dump(self.translateMap, open(savePath, 'w', encoding='utf-8'), indent=4, ensure_ascii=False)
			return True
		except FileNotFoundError as _err:
			raise

	def clear(self):
		self.translateMap.clear()
	
	def doTranslate(self):
		leeClientDir = self.leeCommon.getLeeClientDirectory()
		scriptDir = self.leeCommon.getScriptDirectory()
		patchesDir = os.path.normpath('%s/Patches/' % scriptDir)
		rePathPattern = r'^.*?/Patches/.*?/Resource/Original/System/Towninfo.*?\.(lua|lub)'.replace('/', os.path.sep)
		self.loadTranslate()

		# 找到所有需要汉化的 towninfo 文件路径
		towninfoFilePathList = []
		for dirpath, _dirnames, filenames in os.walk(patchesDir):
			for filename in filenames:
				fullpath = os.path.normpath('%s/%s' % (dirpath, filename))
				if not (filename.lower().startswith('towninfo')): continue
				if not re.match(rePathPattern, fullpath, re.I): continue
				towninfoFilePathList.append(fullpath)
				# print(fullpath)
		
		# 挨个处理并保存到对应的 Translated 目录中
		for towninfoFilePath in towninfoFilePathList:
			print('正在汉化, 请稍候: %s' % os.path.relpath(towninfoFilePath, leeClientDir))
			regex = r'(^.*?/Patches/.*?/Resource)/Original/(System/Towninfo.*?\.(lua|lub))'.replace('/', os.path.sep)
			match = re.search(regex, towninfoFilePath, re.MULTILINE | re.IGNORECASE | re.DOTALL)
			if match is None:
				self.leeCommon.exitWithMessage('无法确定翻译后的 iteminfo 文件存放位置, 程序终止')
			savePath = '%s/Translated/%s' % (match.group(1), match.group(2))

			self.leeTowninfoLua.load(towninfoFilePath)
			for translateItem in self.translateMap:
				self.leeTowninfoLua.replaceName(translateItem['src'], translateItem['dst'])
			self.leeTowninfoLua.save(savePath)
			print('处理汉化, 保存到: %s\r\n' % os.path.relpath(savePath, leeClientDir))
