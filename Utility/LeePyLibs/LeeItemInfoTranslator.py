# -*- coding: utf-8 -*-

import os
import json
import re
import chardet
from LeePyLibs import LeeItemInfoLua
from LeePyLibs import LeeCommon

class LeeItemInfoTranslator:
	def __init__(self):
		self.leeCommon = LeeCommon()
		self.leeItemInfoLua = LeeItemInfoLua()
		self.translateDatabasePath = 'Resources/Databases/ItemInfoTranslate.json'
		self.translateMap = {}
	
	def createTranslate(self, srcIteminfoPath, saveFilename = None):
		if saveFilename is None: saveFilename = self.translateDatabasePath
		self.leeItemInfoLua.clear()
		self.leeItemInfoLua.load(srcIteminfoPath)

		self.translateMap = {}
		for itemID in self.leeItemInfoLua.items():
			unidentifiedDescriptionName = self.leeItemInfoLua.getItemAttribute(itemID, 'unidentifiedDescriptionName')
			identifiedDescriptionName = self.leeItemInfoLua.getItemAttribute(itemID, 'identifiedDescriptionName')
			self.translateMap[itemID] = {
				'unidentifiedDisplayName' : self.leeItemInfoLua.getItemAttribute(itemID, 'unidentifiedDisplayName'),
				'unidentifiedDescriptionName' : [] if unidentifiedDescriptionName is None else unidentifiedDescriptionName.split('\r\n'),
				'identifiedDisplayName' : self.leeItemInfoLua.getItemAttribute(itemID, 'identifiedDisplayName'),
				'identifiedDescriptionName' : [] if identifiedDescriptionName is None else identifiedDescriptionName.split('\r\n')
			}
		self.saveTranslate(saveFilename)

	def loadTranslate(self, filename = None):
		if filename is None: filename = self.translateDatabasePath
		translatePath = '%s/%s' % (self.leeCommon.getScriptDirectory(), filename)
		self.translateMap = {}
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

	def isEmpty(self, obj):
		if isinstance(obj, str) or isinstance(obj, list):
			return len(obj) == 0
		else:
			return obj == None

	def __translateSingleIteminfo(self, loadfilepath, savefilepath):
		self.leeItemInfoLua.load(loadfilepath)
		for itemID in self.leeItemInfoLua.items():
			if str(itemID) not in self.translateMap: continue
			itemTranslateData = self.translateMap[str(itemID)]
			if not self.isEmpty(itemTranslateData['unidentifiedDisplayName']):
				self.leeItemInfoLua.setItemAttribute(itemID, 'unidentifiedDisplayName', itemTranslateData['unidentifiedDisplayName'])
			if not self.isEmpty(itemTranslateData['unidentifiedDescriptionName']):
				self.leeItemInfoLua.setItemAttribute(itemID, 'unidentifiedDescriptionName', '\r\n'.join(itemTranslateData['unidentifiedDescriptionName']))
			if not self.isEmpty(itemTranslateData['identifiedDisplayName']):
				self.leeItemInfoLua.setItemAttribute(itemID, 'identifiedDisplayName', itemTranslateData['identifiedDisplayName'])
			if not self.isEmpty(itemTranslateData['identifiedDescriptionName']):
				self.leeItemInfoLua.setItemAttribute(itemID, 'identifiedDescriptionName', '\r\n'.join(itemTranslateData['identifiedDescriptionName']))
		self.leeItemInfoLua.save(savefilepath)

	def doTranslate(self):
		leeClientDir = self.leeCommon.getLeeClientDirectory()
		scriptDir = self.leeCommon.getScriptDirectory()
		patchesDir = os.path.normpath('%s/Patches/' % scriptDir)
		rePathPattern = r'^.*?/Patches/.*?/Resource/Original/System/iteminfo.*?\.(lua|lub)'.replace('/', os.path.sep)
		self.loadTranslate()
		
		# 找到所有需要汉化的 iteminfo 文件路径
		iteminfoFilePathList = []
		for dirpath, _dirnames, filenames in os.walk(patchesDir):
			for filename in filenames:
				fullpath = os.path.normpath('%s/%s' % (dirpath, filename))
				if not (filename.lower().startswith('iteminfo')): continue
				if not re.match(rePathPattern, fullpath, re.I): continue
				iteminfoFilePathList.append(fullpath)

		# 挨个处理并保存到对应的 Translated 目录中
		for iteminfoFilePath in iteminfoFilePathList:
			print('正在处理, 请稍候: %s' % os.path.relpath(iteminfoFilePath, leeClientDir))
			regex = r'(^.*?/Patches/.*?/Resource)/Original/(System/iteminfo.*?\.(lua|lub))'.replace('/', os.path.sep)
			match = re.search(regex, iteminfoFilePath, re.MULTILINE | re.IGNORECASE | re.DOTALL)
			if match is None:
				self.leeCommon.exitWithMessage('无法确定翻译后的 iteminfo 文件存放位置, 程序终止')
			savePath = '%s/Translated/%s' % (match.group(1), match.group(2))
			self.__translateSingleIteminfo(iteminfoFilePath, savePath)
			print('处理完毕, 保存到: %s\r\n' % os.path.relpath(savePath, leeClientDir))

