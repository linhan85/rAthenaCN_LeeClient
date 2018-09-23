# -*- coding: utf-8 -*-

import os
from LeePyLibs import LeeTowninfoLua
from LeePyLibs import LeeCommon
from LeePyLibs import LeeBaseTranslator

class LeeTowninfoTranslator(LeeBaseTranslator):
	def __init__(self):
		super().__init__()
		self.leeFileIO = LeeTowninfoLua()
		self.translateDefaultDBPath = 'Resources/Databases/TowninfoTranslate.json'
		self.reSrcPathPattern = r'^.*?/Patches/.*?/Resource/Original/System/Towninfo.*?\.(lua|lub)'.replace('/', os.path.sep)
		self.reDstPathPattern = r'(^.*?/Patches/.*?/Resource)/Original/(System/Towninfo.*?\.(lua|lub))'.replace('/', os.path.sep)

	def trans(self, srcFilepath, dstFilepath):
		self.leeFileIO.load(srcFilepath)
		for translateItem in self.translateMap:
			self.leeFileIO.replaceName(translateItem['src'], translateItem['dst'])
		self.leeFileIO.save(dstFilepath)
