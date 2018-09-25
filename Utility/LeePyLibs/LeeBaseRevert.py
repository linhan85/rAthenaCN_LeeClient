# -*- coding: utf-8 -*-

import os
import re
import json
from LeePyLibs import LeeCommon

class LeeBaseRevert:
	def __init__(self):
		self.leeCommon = LeeCommon()
		self.revertDefaultDBPath = None
		self.revertFiles = []
	
	def clearRevert(self):
		self.revertFiles.clear()

	def loadRevert(self, revertDatabaseLoadpath = None):
		if revertDatabaseLoadpath is None: revertDatabaseLoadpath = self.revertDefaultDBPath
		revertDatabaseLoadpath = '%s/%s' % (self.leeCommon.getScriptDirectory(), revertDatabaseLoadpath)
		if not self.leeCommon.isFileExists(revertDatabaseLoadpath): return False

		self.revertFiles.clear()
		revertContent = json.load(open(revertDatabaseLoadpath, 'r', encoding = 'utf-8'))
		self.revertFiles = revertContent['files']
		return True
	
	def insertRecord(self, filepath):
		patchesDir = os.path.normpath('%s/Patches/' % self.leeCommon.getScriptDirectory())
		self.revertFiles.append(os.path.relpath(filepath, patchesDir))
	
	def saveRevert(self, revertDatabaseSavepath = None):
		if revertDatabaseSavepath is None: revertDatabaseSavepath = self.revertDefaultDBPath
		revertDatabaseSavepath = '%s/%s' % (self.leeCommon.getScriptDirectory(), revertDatabaseSavepath)
		if self.leeCommon.isFileExists(revertDatabaseSavepath): os.remove(revertDatabaseSavepath)
		os.makedirs(os.path.dirname(revertDatabaseSavepath), exist_ok = True)

		json.dump({
			'files' : self.revertFiles
		}, open(revertDatabaseSavepath, 'w', encoding = 'utf-8'), indent = 4, ensure_ascii = False)
	
	def hasRevertInfo(self, revertDatabaseLoadpath = None):
		if revertDatabaseLoadpath is None: revertDatabaseLoadpath = self.revertDefaultDBPath
		self.loadRevert(revertDatabaseLoadpath)
		return len(self.revertFiles) > 0

	def doRevert(self, revertDatabaseLoadpath = None):
		if revertDatabaseLoadpath is None: revertDatabaseLoadpath = self.revertDefaultDBPath
		self.loadRevert(revertDatabaseLoadpath)

		scriptDir = self.leeCommon.getScriptDirectory()
		patchesDir = os.path.normpath('%s/Patches/' % scriptDir)

		for relpath in self.revertFiles:
			fullpath = os.path.abspath('%s/%s' % (patchesDir, relpath))
			if self.leeCommon.isFileExists(fullpath):
				os.remove(fullpath)

		if self.leeCommon.isFileExists(revertDatabaseLoadpath):
			os.remove(revertDatabaseLoadpath)

		self.leeCommon.removeEmptyDirectorys(patchesDir)
		