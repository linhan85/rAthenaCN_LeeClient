# -*- coding: utf-8 -*-

import os
from LeePyLibs import LeeSkilldescriptLua
from LeePyLibs import LeeCommon
from LeePyLibs import LeeBaseTranslator

class LeeSkilldescriptTranslator(LeeBaseTranslator):
	def __init__(self):
		super().__init__()
		self.leeFileIO = LeeSkilldescriptLua()
		self.translateDefaultDBPath = 'Resources/Databases/SkillDescriptTranslate.json'
		self.reSrcPathPattern = r'^.*?/Patches/.*?/Resource/Original/data/luafiles514/lua files/skillinfoz/skilldescript\.(lua|lub)'.replace('/', os.path.sep)
		self.reDstPathPattern = r'(^.*?/Patches/.*?/Resource)/Original/(data/luafiles514/lua files/skillinfoz/skilldescript\.(lua|lub))'.replace('/', os.path.sep)

	def trans(self, srcFilepath, dstFilepath):
		self.leeFileIO.load(srcFilepath)
		for skillConstant in self.leeFileIO.items():
			if str(skillConstant) not in self.translateMap: continue
			skillTranslateData = self.translateMap[str(skillConstant)]
			if 'Description' in skillTranslateData:
				skillDescriptText = '\r\n'.join(skillTranslateData['Description'])
				self.leeFileIO.setItemAttribute(skillConstant, 'Description', skillDescriptText)
		self.leeFileIO.save(dstFilepath)
