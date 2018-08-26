# -*- coding: utf-8 -*-

import os
import re
import json
import hashlib
import copy
import time

class _LeeButtonTranslator:
	def __init__(self, leeCommon, buttonTranslator):
		self.leeCommon = leeCommon
		self.buttonTranslator = buttonTranslator
		self.trans_data = {}
		self.transFiles = []

		# demo_out.bmp | demo_over.bmp | demo_press.bmp | demo_disable.bmp
		# demo_out.bmp | demo_over.bmp | demo_press.bmp
		# demo.bmp | demo_a.bmp | demo_b.bmp | demo_c.bmp
		# demo.bmp | demo_a.bmp | demo_b.bmp | demo_dis.bmp
		# demo.bmp | demo_a.bmp | demo_b.bmp
		# demo_a.bmp | demo_b.bmp | demo_c.bmp | demo_d.bmp
		# demoa.bmp | demob.bmp

		self.fileNameModes = [
			{ 'base': '_over', 'refer': ['_out', '_press'], 'block': [''], 'disable': '_disable', 'n': '_out|_over|_press', 'd': '_out|_over|_press|_disable' },
			{ 'base': '_a', 'refer': ['', '_b'], 'block': ['_c'], 'disable': '_dis', 'n': '|_a|_b', 'd': '|_a|_b|_dis' },
			{ 'base': '_a', 'refer': ['', '_b'], 'block': ['_dis'], 'disable': '_c', 'n': '|_a|_b', 'd': '|_a|_b|_c' },
			{ 'base': '_b', 'refer': ['_a', '_c'], 'block': [''], 'disable': '_d', 'n': '_a|_b|_c', 'd': '_a|_b|_c|_d' },
			{ 'base': 'b', 'refer': ['a', 'c'], 'block': [''], 'disable': '', 'n': 'a|b|c', 'd': ''},
			{ 'base': 'b', 'refer': ['a'], 'block': ['c'], 'disable': '', 'n': 'a|b', 'd': ''}
		]
	
	def __getSessionPath(self):
		'''
		获取最后一次汉化按钮补丁时，信息数据库的存储路径
		'''
		scriptDir = self.leeCommon.getScriptDirectory()
		patchesDir = os.path.abspath('%s/Patches/' % scriptDir)
		os.makedirs(patchesDir, exist_ok = True)
		sessionInfoFile = os.path.abspath('%s/LastButtonTransInfo.json' % patchesDir)
		return sessionInfoFile

	def __createSession(self):
		self.transFiles.clear()

	def __loadSession(self):
		sessionInfoFile = self.__getSessionPath()
		if os.path.exists(sessionInfoFile) and os.path.isfile(sessionInfoFile):
			self.transFiles.clear()

			patchesInfo = json.load(open(sessionInfoFile, 'r', encoding = 'utf-8'))
			self.transFiles = patchesInfo['transfiles']
			return True
		return False
	
	def __transButtonFiles(self, filepath):
		scriptDir = self.leeCommon.getScriptDirectory()
		patchesDir = os.path.normpath('%s/Patches/' % scriptDir)
		self.transFiles.append(os.path.relpath(filepath, patchesDir))
	
	def __commitSession(self):
		# 记录成功被程序汉化的按钮文件路径
		sessionInfoFile = self.__getSessionPath()
		if os.path.exists(sessionInfoFile): os.remove(sessionInfoFile)
		json.dump({
			'transtime' : time.strftime('%Y-%m-%d %H:%M:%S',time.localtime()),
			'transfiles' : self.transFiles
		}, open(sessionInfoFile, 'w', encoding = 'utf-8'), indent = 4)
	
	def hasSomethingCanBeRevert(self):
		self.__loadSession()
		return len(self.transFiles) > 0

	def __detectFileMode(self, filepath):
		if not filepath.lower().endswith('.bmp'):
			return False, None, None, None, None
		
		dirpath = os.path.dirname(filepath)
		full_basename = (os.path.splitext(os.path.basename(filepath))[0]).lower()
		real_basename = ''
		refer_postfix = ''
		filename_mode = ''
		with_disabled = False

		isValid = False
		for fileNameMode in self.fileNameModes:
			if full_basename.endswith(fileNameMode['base']): isValid = True
		if not isValid: return False, None, None, None, None

		for fileNameMode in self.fileNameModes:
			real_basename = full_basename[:len(full_basename) - len(fileNameMode['base'])]
			refer_postfix = fileNameMode['base']

			referPass = True
			for refer in fileNameMode['refer']:
				if not self.leeCommon.isFileExists('%s/%s%s.bmp' % (dirpath, real_basename, refer)):
					referPass = False
			if not referPass: continue

			blockPass = True
			for block in fileNameMode['block']:
				if self.leeCommon.isFileExists('%s/%s%s.bmp' % (dirpath, real_basename, block)):
					blockPass = False
			if not blockPass: continue

			with_disabled = self.leeCommon.isFileExists('%s/%s%s.bmp' % (dirpath, real_basename, fileNameMode['disable']))
			filename_mode = fileNameMode['d'] if with_disabled else fileNameMode['n']
			break
		
		if len(filename_mode) <= 0:
			return False, None, None, None, None

		return True, real_basename, refer_postfix, filename_mode, with_disabled

	def updateTranslate(self):
		# 是否需要记录, 内容[目录, 基础文件名, 命名规则]
		scriptDir = self.leeCommon.getScriptDirectory()
		ragexeClientDir = os.path.normpath('%s/Patches' % scriptDir)
		ragexeButtons = {}

		for dirpath, _dirnames, filenames in os.walk(ragexeClientDir):
			# print('Directory: %s' % dirpath)
			for filename in filenames:
				if not filename.lower().endswith('.bmp'):
					continue
				if dirpath.lower().find('resource/translated') > 0:
					continue
				if dirpath.lower().find('utility/common') > 0:
					continue
				
				fullpath = '%s/%s' % (dirpath, filename)
				result, real_basename, refer_postfix, filename_mode, with_disabled = self.__detectFileMode(fullpath)
				if not result: continue

				relpath = re.search('Original/(.*)$'.replace('/', os.path.sep), fullpath).group(1)
				full_namemode = '%s#%s#%s' % (refer_postfix, filename_mode, with_disabled)
				nodekey = self.getNodeKey(os.path.dirname(relpath).lower() + os.path.sep, '%s%s' % (real_basename, refer_postfix))

				trans_item = {
					'Directory': os.path.dirname(relpath).lower() + os.path.sep,
					'Basename': real_basename, 
					'FilenameMode': full_namemode,
					'StyleFormat': '' if not (nodekey in self.trans_data) else self.trans_data[nodekey]['StyleFormat'],
					'ButtonText': '' if not (nodekey in self.trans_data) else self.trans_data[nodekey]['ButtonText']
				}

				ragexeButtons[nodekey] = trans_item

		self.trans_data.clear()
		self.trans_data = ragexeButtons

	def loadTranslate(self, filename = 'Resources/Databases/ButtonTranslate.json'):
		translatePath = '%s/%s' % (self.leeCommon.getScriptDirectory(), filename)
		self.trans_data = {}
		if self.leeCommon.isFileExists(translatePath):
			self.trans_data = json.load(open(translatePath, 'r', encoding='utf-8'))

	def saveTranslate(self, saveFilename = 'Resources/Databases/ButtonTranslate.json'):
		scriptDir = self.leeCommon.getScriptDirectory()
		try:
			savePath = os.path.abspath('%s/%s' % (scriptDir, saveFilename))
			json.dump(self.trans_data, open(savePath, 'w+', encoding='utf-8'), indent=4, ensure_ascii=False)
			return True
		except FileNotFoundError as _err:
			raise
		
	def clear(self):
		self.trans_data.clear()
	
	def getTranslateInfo(self, relpath):
		dirname = os.path.normpath(os.path.dirname(relpath).lower()) + os.path.sep
		filename = (os.path.splitext(os.path.basename(relpath))[0]).lower()
		nodekey = self.getNodeKey(dirname, filename)

		if nodekey not in self.trans_data: return None
		return self.trans_data[nodekey]

	def getNodeKey(self, dirpath, filename):
		hashstr = '%s%s' % (dirpath, filename)
		return hashlib.md5(hashstr.lower().encode(encoding='UTF-8')).hexdigest()

	def doApplyButtonTranslate(self):
		scriptDir = self.leeCommon.getScriptDirectory()
		patchesDir = os.path.normpath('%s/Patches/' % scriptDir)
		rePathPattern = '^.*?/Patches/.*?/Resource/Original/data/texture/蜡历牢磐其捞胶'.replace('/', os.path.sep)
		self.loadTranslate()
		self.__createSession()

		buildlist = []
		for dirpath, _dirnames, filenames in os.walk(patchesDir):
			for filename in filenames:
				fullpath = os.path.normpath('%s/%s' % (dirpath, filename))
				if not filename.lower().endswith('.bmp'): continue
				if not re.match(rePathPattern, fullpath, re.I): continue
				
				relpath = re.search('Original/(.*)$'.replace('/', os.path.sep), fullpath).group(1)
				traninfo = self.getTranslateInfo(relpath)
				if not (traninfo and traninfo['ButtonText'] and traninfo['StyleFormat']): continue
				
				traninfo['RelativePath'] = relpath
				traninfo['FullPath'] = fullpath
				traninfo['ButtonWidth'], traninfo['ButtonHeight'] = self.buttonTranslator.getImageSizeByFilePath(fullpath)
				deepcopy_traninfo = copy.deepcopy(traninfo)
				buildlist.append(deepcopy_traninfo)

		btnStateDefine = ['normal', 'hover', 'press', 'disabled']
		for item in buildlist:
			translatedDirPath = re.search('^(.*)Original/data/texture'.replace('/', os.path.sep), item['FullPath'], re.I).group(1) + 'Translated'
			textureDirPath = '%s/%s' % (translatedDirPath, os.path.dirname(item['RelativePath']))
			_refer_postfix, filename_mode, _with_disabled = item['FilenameMode'].split('#')

			os.makedirs(textureDirPath, exist_ok = True)

			for idx, postfix in enumerate(filename_mode.split('|')):
				btnState = btnStateDefine[idx]
				btnSavePath = '%s/%s%s.bmp' % (textureDirPath, item['Basename'], postfix)
				self.buttonTranslator.createButtonBmpFile(item['StyleFormat'], btnState, item['ButtonText'], item['ButtonWidth'], btnSavePath)
				self.__transButtonFiles(btnSavePath)
		
		self.__commitSession()

	def doRevertButtonTranslate(self, loadSession = True):
		if loadSession:
			self.__loadSession()

		scriptDir = self.leeCommon.getScriptDirectory()
		patchesDir = os.path.normpath('%s/Patches/' % scriptDir)

		for relpath in self.transFiles:
			fullpath = os.path.abspath('%s/%s' % (patchesDir, relpath))
			if self.leeCommon.isFileExists(fullpath):
				os.remove(fullpath)

		sessionInfoFile = self.__getSessionPath()
		if self.leeCommon.isFileExists(sessionInfoFile):
			os.remove(sessionInfoFile)

		self.leeCommon.removeEmptyDirectorys(patchesDir)

		return True
