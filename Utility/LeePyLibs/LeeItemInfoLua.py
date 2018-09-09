# -*- coding: utf-8 -*-

import re
import os
from dataclasses import dataclass
from LeePyLibs import LeeCommon

@dataclass
class LeeIteminfoSingleItem:
	itemID: int
	unidentifiedDisplayName: str
	unidentifiedResourceName: str
	unidentifiedDescriptionName: str
	identifiedDisplayName: str
	identifiedResourceName: str
	identifiedDescriptionName: str
	slotCount: int
	ClassNum: int

class LeeIteminfoLua:
	def __init__(self):
		self.leeCommon = LeeCommon()
		self.itemInfoDict = {}

		self.singleItemFormat = \
'''	[%s] = {
		unidentifiedDisplayName = "%s",
		unidentifiedResourceName = "%s",
		unidentifiedDescriptionName = {
%s
		},
		identifiedDisplayName = "%s",
		identifiedResourceName = "%s",
		identifiedDescriptionName = {
%s
		},
		slotCount = %s,
		ClassNum = %s
	}%s'''

		self.itemInfoFormat = \
'''tbl = {
%s
}

main = function()
	for ItemID,DESC in pairs(tbl) do
		result, msg = AddItem(ItemID, DESC.unidentifiedDisplayName, DESC.unidentifiedResourceName, DESC.identifiedDisplayName, DESC.identifiedResourceName, DESC.slotCount, DESC.ClassNum)
		if not result then
			return false, msg
		end
		for k,v in pairs(DESC.unidentifiedDescriptionName) do
			result, msg = AddItemUnidentifiedDesc(ItemID, v)
			if not result then
				return false, msg
			end
		end
		for k,v in pairs(DESC.identifiedDescriptionName) do
			result, msg = AddItemIdentifiedDesc(ItemID, v)
			if not result then
				return false, msg
			end
		end
	end
	return true, "good"
end
'''

	def __normdesc(self, desc):
		matches = re.finditer(r"(?<!\\)\"(.*?)(?<!\\)\"", desc, re.MULTILINE | re.IGNORECASE)
		descLines = []
		for match in matches:
			descLines.append(match.group(1))
		return None if len(descLines) <= 0 else '\r\n'.join(descLines)
	
	def __quotedesc(self, descLines):
		if descLines is None: return ''
		descLines = descLines.replace('\r\n', '\n').split('\n')
		for index, line in enumerate(descLines):
			descLines[index] = '\t\t\t"%s"%s' % (line, ',' if (index + 1) < len(descLines) else '')
		return '' if len(descLines) <= 0 else '\r\n'.join(descLines)

	def load(self, filepath):
		self.itemInfoDict.clear()

		luafile = open(filepath, 'r', encoding = 'latin1')
		content = luafile.read()
		luafile.close()

		# 已经读取到了 lua 文件的内容, 接下来开始解析
		# 先解析出每个不同的的物品信息, 如下面注释所示的样子

		# [501] = {
		# 	unidentifiedDisplayName = "红色药水",
		# 	unidentifiedResourceName = "弧埃器记",
		# 	unidentifiedDescriptionName = {
		# 		"将红色药草捣碎，制成的体力恢复剂。",
		# 		"恢复^00008845～65^000000的HP",
		# 		"依^000088(VITx2)%^000000增加恢复量",
		# 		"^ffffff_^000000",
		# 		"重量：7",
		# 	},
		# 	identifiedDisplayName = "红色药水",
		# 	identifiedResourceName = "弧埃器记",
		# 	identifiedDescriptionName = {
		# 		"将红色药草捣碎，制成的体力恢复剂。",
		# 		"恢复^00008845～65^000000的HP",
		# 		"依^000088(VITx2)%^000000增加恢复量",
		# 		"^ffffff_^000000",
		# 		"重量：7",
		# 	},
		# 	slotCount = 0,
		# 	ClassNum = 0
		# }
		
		regex = r"(\[\d+\]\s*=\s*{.*?{.*?}.*?{.*?}.*?ClassNum.*?}\s*)"
		matches = re.finditer(regex, content, re.MULTILINE | re.IGNORECASE | re.DOTALL)
		itemInfoTextList = []
		for match in matches:
			itemInfoTextList.append(match.group(1))
		
		# 接下来挨个拆解出字段的值, 存入到 self.itemInfoList 中
		
		regex = r"\[\s*?(\d*)\s*?\]\s*?=\s*?{\s*?unidentifiedDisplayName\s*?=\s*?\"(.*?)\"\s*?,\s*?unidentifiedResourceName\s*?=\s*?\"(.*?)\"\s*?,\s*?unidentifiedDescriptionName\s*?=\s*?{\s*(.*?)\s*?}\s*?,\s*?identifiedDisplayName\s*?=\s*?\"(.*?)\"\s*?,\s*?identifiedResourceName\s*?=\s*?\"(.*?)\"\s*?,\s*?identifiedDescriptionName\s*?=\s*?{\s*(.*?)\s*?}\s*?,\s*?slotCount\s*?=\s*?(\d*)\s*?,\s*?ClassNum\s*?=\s*?(\d*)\s*?}"
		
		for iteminfoText in itemInfoTextList:
			try:
				match = re.search(regex, iteminfoText, re.MULTILINE | re.IGNORECASE | re.DOTALL)
				singleItem = LeeIteminfoSingleItem(
					itemID = self.leeCommon.atoi(match.group(1)),		# 物品编号
					unidentifiedDisplayName = match.group(2),			# 物品未鉴定时候的道具名称
					unidentifiedResourceName = match.group(3),			# 物品未鉴定时候的图档资源名称
					unidentifiedDescriptionName = self.__normdesc(match.group(4)),		# 物品未鉴定时候的道具描述信息
					identifiedDisplayName = match.group(5),				# 物品已鉴定时候的道具名称
					identifiedResourceName = match.group(6),			# 物品已鉴定时候的图档资源名称
					identifiedDescriptionName = self.__normdesc(match.group(7)),		# 物品已鉴定时候的道具描述信息
					slotCount = self.leeCommon.atoi(match.group(8)),	# 物品的卡槽数量
					ClassNum = self.leeCommon.atoi(match.group(9))		# 物品的外观类别代码
				)
				self.itemInfoDict[self.leeCommon.atoi(match.group(1))] = singleItem
			except:
				print(iteminfoText)
				raise
	
	def save(self, savepath):
		# 构建表格主体部分, 先定义一下格式部分
		fullItemText = []	# 保存每一个道具完整的文本段

		for itemID in sorted(self.itemInfoDict):
			singleItemText = self.singleItemFormat % (
				self.itemInfoDict[itemID].itemID,
				self.itemInfoDict[itemID].unidentifiedDisplayName,
				self.itemInfoDict[itemID].unidentifiedResourceName,
				self.__quotedesc(self.itemInfoDict[itemID].unidentifiedDescriptionName),
				self.itemInfoDict[itemID].identifiedDisplayName,
				self.itemInfoDict[itemID].identifiedResourceName,
				self.__quotedesc(self.itemInfoDict[itemID].identifiedDescriptionName),
				self.itemInfoDict[itemID].slotCount,
				self.itemInfoDict[itemID].ClassNum,
				self.leeCommon.isLastReturn(sorted(self.itemInfoDict), itemID, '', ',')
			)
			fullItemText.append(singleItemText)
		
		luaContent = self.itemInfoFormat % ('\r\n'.join(fullItemText))
		
		fullSavePath = os.path.abspath(savepath)
		os.makedirs(os.path.dirname(fullSavePath), exist_ok = True)
		luafile = open(fullSavePath, 'w', encoding = 'latin1')
		luafile.write(luaContent)
		luafile.close

	def items(self):
		return self.itemInfoDict

	def getIteminfo(self, itemID):
		return None if itemID not in self.itemInfoDict else self.itemInfoDict[itemID]
	
	def getItemAttribute(self, itemID, attribname, dstEncode = 'gbk'):
		try:
			itemdata = self.getIteminfo(itemID)
			if itemdata == None: return None
			value = getattr(itemdata, attribname, None)
			if value is None: return None
			if isinstance(value, list):
				for index, val in enumerate(value):
					value[index] = val.encode('latin1').decode(dstEncode)
				return value
			else:
				return value.encode('latin1').decode(dstEncode)
		except:
			print('getItemAttribute: 处理 %d 的 %s 字段时出问题, 内容为: \r\n%s', (itemID, attribname, value))
			raise

	def setItemAttribute(self, itemID, attribname, value, srcEncode = 'gbk'):
		try:
			itemdata = self.getIteminfo(itemID)
			if itemdata == None: return False
			if isinstance(value, list):
				for index, val in enumerate(value):
					value[index] = val.encode(srcEncode).decode('latin1')
			else:
				value = value.encode(srcEncode).decode('latin1')
			return setattr(self.itemInfoDict[itemID], attribname, value)
		except:
			print('setItemAttribute: 处理 %d 的 %s 字段时出问题, 内容为: \r\n%s', (itemID, attribname, value))
			raise
	
	def clear(self):
		self.itemInfoDict.clear()
