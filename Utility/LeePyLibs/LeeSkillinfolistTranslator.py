# -*- coding: utf-8 -*-

import os
from LeePyLibs import LeeSkillinfolistLua
from LeePyLibs import LeeCommon
from LeePyLibs import LeeBaseTranslator

class LeeSkillinfolistTranslator(LeeBaseTranslator):
	def __init__(self):
		super().__init__()
		self.leeFileIO = LeeSkillinfolistLua()
		self.translateDefaultDBPath = 'Resources/Databases/SkillDescriptTranslate.json'
		self.reSrcPathPattern = r'^.*?/Patches/.*?/Resource/Original/data/luafiles514/lua files/skillinfoz/skillinfolist\.(lua|lub)'.replace('/', os.path.sep)
		self.reDstPathPattern = r'(^.*?/Patches/.*?/Resource)/Original/(data/luafiles514/lua files/skillinfoz/skillinfolist\.(lua|lub))'.replace('/', os.path.sep)

	def trans(self, srcFilepath, dstFilepath):
		self.leeFileIO.load(srcFilepath)
		for skillConstant in self.leeFileIO.items():
			if str(skillConstant) not in self.translateMap: continue
			skillTranslateData = self.translateMap[str(skillConstant)]
			self.leeFileIO.setItemAttribute(skillConstant, 'SkillName', skillTranslateData['SkillName'])
		self.leeFileIO.save(dstFilepath)
