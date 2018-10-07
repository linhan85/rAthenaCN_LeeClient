# -*- coding: utf-8 -*-

import os
import yaml

from LeePyLibs import LeeCommon

class LeeConfigure:
	def __init__(self):
		self.leeCommon = LeeCommon()
		self.configureFilepath = './LeeClientAgent.yml'
		self.configureData = None
		self.load()
	
	def load(self):
		configureFileFullpath = os.path.abspath(self.configureFilepath)
		print('configureFileFullpath = %s' % configureFileFullpath)
		self.configureData = yaml.load(open(configureFileFullpath, 'r', encoding = 'utf8'))
		return self.configureData

	def get(self, configPath, default = None):
		if '.' in configPath:
			print('暂时不支持句号路径描述: %s' % configPath)
			return None
		
		if configPath in self.configureData:
			return self.configureData[configPath]

		return None
