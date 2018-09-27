# -*- coding: utf-8 -*-

import os
import glob
import time
import timeit
import struct
import re
from LeePyLibs import LeeCommon
from LeePyLibs import LeeIteminfoLua

class LeeVerifier:
	'''
	这个类主要实现了对 RO 常用客户端文件格式的简单解析
	目的用于验证客户端的文件是否完整
	'''
	def __init__(self):
		self.leeCommon = LeeCommon()
		self.textureDirs = ['data/texture/']
		self.modelDirs = ['data/model/']
		self.spriteDirs = ['data/sprite/']

		self.reportInfo = []
		self.reportStartTime = 0    # 用于记录当前检测项目的启动时间
		self.reportFileCount = 0    # 记录本次检测项目中, 丢失了资源的文件数量
		self.reportMissCount = 0    # 记录本次检测项目中, 累计丢失的资源文件数量
	
	def __bytesToString(self, bytesArray, targetCode = 'gbk'):
		'''
		将以 0 结尾的 bytes 数组转成字符串对象

		Args:
			bytesArray: 以 0 结尾的 bytes 数组
			targetCode: 转换成功之后的字符串编码, 默认用 gbk 编码

		Returns:
			转换后的字符串
		'''
		for x in range(len(bytesArray)):
			if (bytesArray[x] == 0): break
		asciiString = bytesArray.decode('latin1')[:x]
		return asciiString.encode('latin1').decode(targetCode)
	
	def __readFormatVersionInfo(self, f):
		'''
		根据打开的文件对象获取其版本信息
		直接读取接下来的 2 个字节来获得版本信息, 要求指针紧跟在 Magic Bytes 后面

		Args:
			f: 已经打开的文件对象 (RSW 或 RSM 文件)

		Returns:
			此函数包括三个返回值, 需要使用多个变量来接收函数返回的内容

			Major: 主版本号
			Minor: 子版本号
			Version: 2 个字节连在一起的版本号数值
		'''
		Major, Minor = struct.unpack("2b", f.read(struct.calcsize("2b")))
		f.seek(-2, 1)
		Version = struct.unpack("1h", f.read(struct.calcsize("1h")))[0]
		# ShowDebug('Major %d | Minor %d | Version %d' % (Major, Minor, Version))
		return Major, Minor, Version
	
	def __parseGnd(self, gndfilepath):
		'''
		读取 GND 文件, 并获取它所有相关的贴图地址
		读取到的贴图地址相对于 data/texture/ 目录, 如: data/texture/BACKSIDE.BMP

		Returns:
			此函数包括两个返回值, 需要使用多个变量来接收函数返回的内容

			result: Boolean 执行成功与否
			texturePathList: List 保存着贴图文件路径的数组, 相对于 data/texture/ 目录
		'''
		if not self.leeCommon.isFileExists(gndfilepath):
			print('读取 Gnd 文件失败, 文件不存在: %s' % gndfilepath)
			return False, []

		gndfile = open(gndfilepath, "rb")
		gndfile.seek(len(b'GRGN\x01\x07')) # Magic Bytes

		_Width, _Height, _Ratio, TextureCount, TextureSize = struct.unpack("5I", gndfile.read(struct.calcsize("5I")))
		# ShowDebug("parseGnd_GetTexturePathList: Width %d | Height %d | Ratio %d | TextureCount %d | TextureSize %d" % (_Width, _Height, _Ratio, TextureCount, TextureSize))

		texturePathList = []
		for _i in range(TextureCount):
			fmt = "%ds" % TextureSize
			TexturePath = struct.unpack(fmt, gndfile.read(struct.calcsize(fmt)))[0]
			texturePathList.append(self.__bytesToString(TexturePath))
			# print(self.__bytesToString(TexturePath))

		gndfile.close()
		return True, texturePathList
	
	def __parseRsw(self, rswfilepath):
		'''
		读取 RSW 文件, 并获取它所有相关的 RSM 模型地址
		读取到的模型地址相对于 data/model/ 目录, 如: data/model/malaya/龋荐唱公03.rsm

		Args:
			rswfilepath: RSW 文件的路径

		Returns:
			此函数包括两个返回值, 需要使用多个变量来接收函数返回的内容

			result: Boolean 执行成功与否
			modelPathList: List 保存着 Rsm 模型文件路径的数组, 相对于 data/model/ 目录
		'''
		if not self.leeCommon.isFileExists(rswfilepath):
			print('读取 Rsw 文件失败, 文件不存在: %s' % rswfilepath)
			return False, []

		rswfile = open(rswfilepath, 'rb')
		rswfile.seek(len(b'GRSW')) 	# Magic Bytes
		fmtMajor, fmtMinor, _Version = self.__readFormatVersionInfo(rswfile)

		def isCompatible(major, minor):
			return (fmtMajor > major or (fmtMajor == major and fmtMinor >= minor))
		
		_IniFilename = rswfile.read(struct.calcsize("40s"))
		_GndFilename = rswfile.read(struct.calcsize("40s"))
		_GatFilename = '' if not isCompatible(1, 4) else rswfile.read(struct.calcsize("40s"))
		_ScrFilename = rswfile.read(struct.calcsize("40s"))

		# ==================== WaterData ====================

		_Level = 0.0
		_Type = 0
		_WaveHeight = 0.2
		_WaveSpeed = 2.0
		_WavePitch = 50.0
		_AnimSpeed = 3
		
		if isCompatible(1, 3):
			_Level = struct.unpack("1f", rswfile.read(struct.calcsize("1f")))[0]
    
		if isCompatible(1, 8):
			_Type, _WaveHeight, _WaveSpeed, _WavePitch = struct.unpack("1I3f", rswfile.read(struct.calcsize("1I3f")))
    
		if isCompatible(1, 9):
			_AnimSpeed = struct.unpack("1I", rswfile.read(struct.calcsize("1I")))[0]

		# ShowInfo('WaterData: Level %f | Type %d | WaveHeight %f | WaveSpeed %f | WavePitch %f | AnimSpeed %d' % 
		#     (_Level, _Type, _WaveHeight, _WaveSpeed, _WavePitch, _AnimSpeed))

		# ==================== LightData ====================

		_Longitude = 45
		_Latitude = 45
		_DiffuseColor = [1.0, 1.0, 1.0]
		_AmbientColor = [0.3, 0.3, 0.3]
		_Opacity = 1.0

		if isCompatible(1, 5):
			_Longitude, _Latitude = struct.unpack("2I", rswfile.read(struct.calcsize("2I")))
			_DiffuseColor[0], _DiffuseColor[1], _DiffuseColor[2] = struct.unpack("3f", rswfile.read(struct.calcsize("3f")))
			_AmbientColor[0], _AmbientColor[1], _AmbientColor[2] = struct.unpack("3f", rswfile.read(struct.calcsize("3f")))
    
		if isCompatible(1, 7):
			_Opacity = struct.unpack("1f", rswfile.read(struct.calcsize("1f")))[0]

		# ShowInfo('LightData: Longitude %d | Latitude %d | Opacity %f' % (_Longitude, _Latitude, _Opacity))
		# ShowInfo('LightData: DiffuseColorRed %f | DiffuseColorGreen %f | DiffuseColorBlue %f' % (_DiffuseColor[0], _DiffuseColor[1], _DiffuseColor[2]))
		# ShowInfo('LightData: AmbientColorRed %f | AmbientColorGreen %f | AmbientColorBlue %f' % (_AmbientColor[0], _AmbientColor[1], _AmbientColor[2]))
    
		# ==================== GroundData ====================

		_Top = -500
		_Bottom = 500
		_Left = -500
		_Right = 500

		if isCompatible(1, 6):
			_Top, _Bottom, _Left, _Right = struct.unpack("4I", rswfile.read(struct.calcsize("4I")))
    
		# ShowInfo('GroundData: Top %d | Bottom %d | Left %d | Right %d' % (_Top, _Bottom, _Left, _Right))

		# ==================== MapObject ====================

		objectCount = struct.unpack("1I", rswfile.read(struct.calcsize("1I")))[0]

		modelPathList = []
		for _i in range(objectCount):
			objectType = struct.unpack("1I", rswfile.read(struct.calcsize("1I")))[0]

			if (objectType == 1): # Model - 关注会加载的 RSM 模型
				if (isCompatible(1, 3)):
					_ModelName = self.__bytesToString(struct.unpack("40s", rswfile.read(struct.calcsize("40s")))[0])
					_AnimationType = struct.unpack("1I", rswfile.read(struct.calcsize("1I")))[0]
					_AnimationSpeed = struct.unpack("1f", rswfile.read(struct.calcsize("1f")))[0]
					_BlockType = struct.unpack("1I", rswfile.read(struct.calcsize("1I")))[0]
            
				modelFilename = self.__bytesToString(struct.unpack("80s", rswfile.read(struct.calcsize("80s")))[0])
				_ModelNodeName = self.__bytesToString(struct.unpack("80s", rswfile.read(struct.calcsize("80s")))[0])

				modelPathList.append(modelFilename)
				# ShowInfo("[RSM Model] Path = %s" % modelFilename)

		rswfile.close()
		return True, modelPathList
	
	def __parseRsm(self, rsmfilepath):
		'''
		读取 RSM 文件, 并获取它所有相关的贴图地址
		读取到的贴图地址相对于 data/texture/ 目录, 如: data/texture/eclage/ecl_obj15.bmp

		Args:
			rsmfilepath: RSM 文件的路径

		Returns:
			此函数包括两个返回值, 需要使用多个变量来接收函数返回的内容

			result: Boolean 执行成功与否
			texturePathList: List 保存着贴图文件路径的数组, 相对于 data/texture/ 目录
		'''
		if not self.leeCommon.isFileExists(rsmfilepath):
			print("读取 Rsm 文件失败, 文件不存在: %s" % rsmfilepath)
			return False, []

		rsmfile = open(rsmfilepath, "rb")
		rsmfile.seek(len(b'GRSM')) # Magic Bytes
		fmtMajor, fmtMinor, _Version = self.__readFormatVersionInfo(rsmfile)

		def isCompatible(major, minor):
			return (fmtMajor > major or (fmtMajor == major and fmtMinor >= minor))
    
		_AnimationLength, _ShadeType = struct.unpack("2I", rsmfile.read(struct.calcsize("2I")))
		_Alpha = 0 if not isCompatible(1, 4) else struct.unpack("1b", rsmfile.read(struct.calcsize("1b")))[0]
		_unknow = struct.unpack("16s", rsmfile.read(struct.calcsize("16s")))[0]
		textureCount = struct.unpack("1I", rsmfile.read(struct.calcsize("1I")))[0]

		texturePathList = []
		for _i in range(textureCount):
			texturePath = self.__bytesToString(struct.unpack("40s", rsmfile.read(struct.calcsize("40s")))[0])
			texturePathList.append(texturePath)

		rsmfile.close()
		return True, texturePathList
	
	def __parseStr(self, strfilepath):
		'''
		读取 STR 文件, 并获取它所有相关的贴图地址
    	读取到的贴图地址相对于 STR 文件所在目录, 如: data/texture/effect/magnus/ff.bmp

		Args:
			strfilepath: STR 文件的路径

		Returns:
			此函数包括两个返回值, 需要使用多个变量来接收函数返回的内容

			result: Boolean 执行成功与否
			texturePathList: List 保存着贴图文件路径的数组, 相对于 STR 文件所在目录
		'''
		if not self.leeCommon.isFileExists(strfilepath):
			print("读取 Str 文件失败, 文件不存在: %s" % strfilepath)
			return False, []

		strfile = open(strfilepath, "rb")
		strfile.seek(len(b'STRM')) # Magic Bytes
		_Version, _FPS, _frameCount, layerCount, _Reserved = struct.unpack("4I16s", strfile.read(struct.calcsize("4I16s")))

		texturePathList = []
		for _i in range(layerCount):
			textureCount = struct.unpack("1I", strfile.read(struct.calcsize("1I")))[0]
			for _k in range(textureCount):
				textureName = self.__bytesToString(struct.unpack("128s", strfile.read(struct.calcsize("128s")))[0])
				texturePathList.append(textureName)

			keyFrameCount = struct.unpack("1I", strfile.read(struct.calcsize("1I")))[0]
			for _k in range(keyFrameCount):
				struct.unpack("2I19f1I6f3I", strfile.read(struct.calcsize("2I19f1I6f3I")))

		strfile.close()
		return True, texturePathList
	
	def __parseIteminfo(self, iteminfofilepath):
		if not self.leeCommon.isFileExists(iteminfofilepath):
			print("读取 Iteminfo 文件失败, 文件不存在: %s" % iteminfofilepath)
			return False, [], []
		
		iteminfoLua = LeeIteminfoLua()
		iteminfoLua.load(iteminfofilepath)

		texturePathList = []
		spritePathList = []
		
		for itemID in iteminfoLua.items():
			unidentifiedResourceName = iteminfoLua.getItemAttribute(itemID, 'unidentifiedResourceName')
			texturePathList.append('蜡历牢磐其捞胶/collection/%s.bmp' % unidentifiedResourceName)
			texturePathList.append('蜡历牢磐其捞胶/item/%s.bmp' % unidentifiedResourceName)
			spritePathList.append('酒捞袍/%s.spr' % unidentifiedResourceName)
			spritePathList.append('酒捞袍/%s.act' % unidentifiedResourceName)
			
			identifiedResourceName = iteminfoLua.getItemAttribute(itemID, 'identifiedResourceName')
			texturePathList.append('蜡历牢磐其捞胶/collection/%s.bmp' % identifiedResourceName)
			texturePathList.append('蜡历牢磐其捞胶/item/%s.bmp' % identifiedResourceName)
			spritePathList.append('酒捞袍/%s.spr' % identifiedResourceName)
			spritePathList.append('酒捞袍/%s.act' % identifiedResourceName)

		texturePathList = list(set(texturePathList))
		spritePathList = list(set(spritePathList))

		return True, texturePathList, spritePathList

	def __verifyGnd(self, gndfilepath):
		result, texturePathList = self.__parseGnd(gndfilepath)
		if not result: return None

		missTexturePathList = []
		leeClientDir = self.leeCommon.getLeeClientDirectory()

		for texturePath in texturePathList:
			for textureDir in self.textureDirs:
				fullpath = self.leeCommon.normpath('%s/%s/%s' % (leeClientDir, textureDir, texturePath))
				if self.leeCommon.isFileExists(fullpath): break
			else:
				print(texturePath)
				missTexturePathList.append(fullpath)
		
		return missTexturePathList
	
	def __verifyRsw(self, rswfilepath):
		result, modelPathList = self.__parseRsw(rswfilepath)
		if not result: return None, None

		missModelPathList = []
		existsModelPathList = []
		leeClientDir = self.leeCommon.getLeeClientDirectory()

		for modelPath in modelPathList:
			for modelDir in self.modelDirs:
				fullpath = self.leeCommon.normpath('%s/%s/%s' % (leeClientDir, modelDir, modelPath))
				if self.leeCommon.isFileExists(fullpath):
					# print('existsModelPathList: %s' % modelPath)
					existsModelPathList.append(fullpath)
					break
			else:
				print('missModelPathList: %s' % modelPath)
				missModelPathList.append(fullpath)

		return existsModelPathList, missModelPathList
	
	def __verifyRsm(self, rsmfilepath):
		result, texturePathList = self.__parseRsm(rsmfilepath)
		if not result: return None
		
		missTexturePathList = []
		leeClientDir = self.leeCommon.getLeeClientDirectory()

		for texturePath in texturePathList:
			for textureDir in self.textureDirs:
				fullpath = self.leeCommon.normpath('%s/%s/%s' % (leeClientDir, textureDir, texturePath))
				if self.leeCommon.isFileExists(fullpath): break
			else:
				print(texturePath)
				missTexturePathList.append(fullpath)
		
		return missTexturePathList

	def __verifyStr(self, strfilepath):
		result, texturePathList = self.__parseStr(strfilepath)
		if not result: return None

		missTexturePathList = []
		leeClientDir = self.leeCommon.getLeeClientDirectory()
		strBaseDirectory = os.path.dirname(strfilepath)

		# 素材文件的归属位置略有不同, 优先探测 str 所在目录
		# 这一步保存的 missTexturePathList 只是资源的相对路径, 并非全路径
		for texturePath in texturePathList:
			fullpath = self.leeCommon.normpath('%s/%s' % (strBaseDirectory, texturePath))
			if self.leeCommon.isFileExists(fullpath): break
		else:
			missTexturePathList.append(texturePath)
		
		# 在 str 所在目录探测失败的再到 data/texture/effect 下找找
		# 这一步会将 missTexturePathList 中的路径处理成全路径, 而非资源的相对路径
		for texturePath in missTexturePathList:
			fullpath = self.leeCommon.normpath('%s/data/texture/effect/%s' % (leeClientDir, texturePath))
			if self.leeCommon.isFileExists(fullpath):
				missTexturePathList.remove(texturePath)
			else:
				missTexturePathList.remove(texturePath)
				missTexturePathList.append(fullpath)
		
		# for missTexturePath in missTexturePathList:
		# 	print(missTexturePath)

		return missTexturePathList
	
	def __verifyIteminfo(self, iteminfofilepath):
		result, texturePathList, spritePathList = self.__parseIteminfo(iteminfofilepath)
		if not result: return None, None

		leeClientDir = self.leeCommon.getLeeClientDirectory()

		missTexturePathList = []
		for texturePath in texturePathList:
			for textureDir in self.textureDirs:
				fullpath = self.leeCommon.normpath('%s/%s/%s' % (leeClientDir, textureDir, texturePath))
				if self.leeCommon.isFileExists(fullpath): break
			else:
				# print('missTexturePathList: %s' % texturePath)
				missTexturePathList.append(fullpath)
		
		missSpritePathList = []
		for spritePath in spritePathList:
			for spriteDir in self.spriteDirs:
				fullpath = self.leeCommon.normpath('%s/%s/%s' % (leeClientDir, spriteDir, spritePath))
				if self.leeCommon.isFileExists(fullpath): break
			else:
				# print('missSpritePathList: %s' % spritePath)
				missSpritePathList.append(fullpath)

		return missTexturePathList, missSpritePathList
	
	def __resetReport(self):
		self.reportInfo.clear

	def __appendReportMessage(self, mesType, message):
		if mesType.lower() == 'header':
			self.reportInfo.append('=============================================')
			self.reportInfo.append(message)
			self.reportInfo.append('=============================================')
			# 启动一个计时器和一个 __appendReportData 计数器
			self.reportFileCount = self.reportMissCount = 0
			self.reportStartTime = timeit.default_timer()
		elif mesType.lower() == 'footer':
			# 总结耗时以及写入一些统计信息
			spendTime = timeit.default_timer() - self.reportStartTime
			resourceInfo = '此项目无任何文件缺失' if self.reportFileCount == 0 else '共有 %d 个文件缺失 %d 个资源' % (
				self.reportFileCount, self.reportMissCount
			)
			self.reportInfo.append('%s / 校验耗时: %.2f 秒' % (resourceInfo, spendTime))
			self.reportInfo.append('=============================================')
			self.reportInfo.append('')
			self.reportInfo.append('')

	def __appendReportData(self, sourceFile, firstMissFiles, secondMissFiles = None):
		if len(firstMissFiles) <= 0: return
		leeClientDir = self.leeCommon.getLeeClientDirectory()
		missFileCount = len(firstMissFiles) + (0 if secondMissFiles is None else len(secondMissFiles))

		self.reportInfo.append('>>>> %s (缺失 %d 个文件)' % (os.path.relpath(sourceFile, leeClientDir), missFileCount))
		
		if firstMissFiles is not None:
			for missFile in firstMissFiles:
				self.reportInfo.append('     缺失: %s' % os.path.relpath(missFile, leeClientDir))
		
		if secondMissFiles is not None:
			for missFile in secondMissFiles:
				self.reportInfo.append('     缺失: %s' % os.path.relpath(missFile, leeClientDir))
		
		self.reportInfo.append('')
		self.reportFileCount = self.reportFileCount + 1
		self.reportMissCount = self.reportMissCount + missFileCount
	
	def __saveReport(self):
		reportTime = time.strftime("%Y%m%d_%H%M%S", time.localtime())
		leeClientDir = self.leeCommon.getLeeClientDirectory()
		savePath = '%s/Reports/VerifyRpt_%s.txt' % (self.leeCommon.getScriptDirectory(), reportTime)
		savePath = self.leeCommon.normpath(savePath)
		os.makedirs(os.path.dirname(savePath), exist_ok = True)
		
		rptfile = open(savePath, 'w+', encoding = 'utf-8', newline = '')
		rptfile.write('\r\n'.join(self.reportInfo))
		
		print('校验结果已保存到 : %s' % os.path.relpath(savePath, leeClientDir))
	
	def runVerifier(self):
		self.__resetReport()
		leeClientDir = self.leeCommon.getLeeClientDirectory()

		# 校验地图基础文件的 gnd 文件（地表纹理）
		gndfiles = glob.glob('%s/data/*.gnd' % leeClientDir)
		self.__appendReportMessage('header', '校验 gnd 地图文件共 %d 个' % len(gndfiles))
		print('正在校验 gnd 地图文件共 %d 个' % len(gndfiles))
		for gndfile in gndfiles:
			_missTexturePathList = self.__verifyGnd(gndfile)
			self.__appendReportData(gndfile, _missTexturePathList)
		self.__appendReportMessage('footer', '')

		# 校验地图基础文件的 rsw 文件（模型层）
		rswfiles = glob.glob('%s/data/*.rsw' % leeClientDir)
		self.__appendReportMessage('header', '校验 rsw 地图文件共 %d 个' % len(rswfiles))
		print('正在校验 rsw 地图文件共 %d 个' % len(rswfiles))
		validModelPathList = []
		for rswfile in rswfiles:
			_existsModelPathList, _missModelPathList = self.__verifyRsw(rswfile)
			self.__appendReportData(rswfile, _missModelPathList)
			validModelPathList.extend(_existsModelPathList)
		self.__appendReportMessage('footer', '')

		# 校验地图中有效的 rsm 模型文件的贴图
		# 这里的 validModelPathList 存储的是有效的全路径
		self.__appendReportMessage('header', '校验 rsm 模型文件共 %d 个' % len(validModelPathList))
		print('正在校验 rsm 模型文件共 %d 个' % len(validModelPathList))
		for modelpath in validModelPathList:
			_missTexturePathList = self.__verifyRsm(modelpath)
			self.__appendReportData(modelpath, _missTexturePathList)
		self.__appendReportMessage('footer', '')

		# 校验动画效果索引文件 str 中所需的贴图
		strFilePathList = []
		for dirpath, _dirnames, filenames in os.walk(('%s/data' % leeClientDir)): 
			for filename in filenames:
				fullpath = os.path.join(dirpath, filename)
				if fullpath.lower().endswith('.str'):
					strFilePathList.append(fullpath)
		
		self.__appendReportMessage('header', '校验 str 动画描述文件共 %d 个' % len(strFilePathList))
		print('正在校验 str 动画描述文件共 %d 个' % len(strFilePathList))
		for strfilepath in strFilePathList:
			_missTexturePathList = self.__verifyStr(strfilepath)
			self.__appendReportData(strfilepath, _missTexturePathList)
		self.__appendReportMessage('footer', '')

		# 校验 Iteminfo 文件中所需的贴图
		scriptDir = self.leeCommon.getScriptDirectory()
		patchesDir = os.path.normpath('%s/Patches/' % scriptDir)
		rePathPattern = self.leeCommon.normPattern(r'^.*?/Patches/.*?/Resource/Original/System/iteminfo.*?\.(lua|lub)')
		
		iteminfoFilePathList = []
		for dirpath, _dirnames, filenames in os.walk(patchesDir):
			for filename in filenames:
				fullpath = os.path.normpath('%s/%s' % (dirpath, filename))
				if not (filename.lower().startswith('iteminfo')): continue
				if not re.match(rePathPattern, fullpath, re.I): continue
				iteminfoFilePathList.append(fullpath)
		
		self.__appendReportMessage('header', '校验 Iteminfo 道具描述文件共 %d 个' % len(iteminfoFilePathList))
		print('正在校验 Iteminfo 道具描述文件共 %d 个' % len(iteminfoFilePathList))
		for iteminfofilepath in iteminfoFilePathList:
			_missTexturePathList, _missSpritePathList = self.__verifyIteminfo(iteminfofilepath)
			self.__appendReportData(iteminfofilepath, _missTexturePathList, _missSpritePathList)
		self.__appendReportMessage('footer', '')

		# TODO: 未来可能还有更多的数据校验...
		self.__saveReport()
