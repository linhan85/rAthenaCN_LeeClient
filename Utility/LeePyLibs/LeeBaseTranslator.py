# -*- coding: utf-8 -*-

import os
import re
import json
from LeePyLibs import LeeCommon

class LeeBaseTranslator:
    def __init__(self):
        self.leeCommon = LeeCommon()
        self.leeFileIO = None
        self.translateDefaultDBPath = None
        self.translateMap = {}
        self.reSrcPathPattern = None
        self.reDstPathPattern = None
    
    def clear(self):
        self.translateMap.clear()

    def load(self, translateDBPath = None):
        self.clear()
        if translateDBPath is None: translateDBPath = self.translateDefaultDBPath
        translatePath = '%s/%s' % (self.leeCommon.getScriptDirectory(), translateDBPath)
        if not self.leeCommon.isFileExists(translatePath): return False
        try:
            self.translateMap = json.load(open(translatePath, 'r', encoding = 'utf-8'))
            return True
        except FileNotFoundError as _err:
            raise
    
    def save(self, translateDBPath = None):
        if translateDBPath is None: translateDBPath = self.translateDefaultDBPath
        scriptDir = self.leeCommon.getScriptDirectory()
        try:
            savePath = os.path.abspath('%s/%s' % (scriptDir, translateDBPath))
            json.dump(self.translateMap, open(savePath, 'w', encoding = 'utf-8'), indent = 4, ensure_ascii = False)
            return True
        except FileNotFoundError as _err:
            raise
    
    def doTranslate(self, specifiedClientVer = None):
        leeClientDir = self.leeCommon.getLeeClientDirectory()
        scriptDir = self.leeCommon.getScriptDirectory()
        patchesDir = os.path.normpath('%s/Patches/' % scriptDir)

        if self.reSrcPathPattern is None: return False
        if self.reDstPathPattern is None: return False

        sourceFilepathList = []
        for dirpath, _dirnames, filenames in os.walk(patchesDir):
            for filename in filenames:
                fullpath = os.path.normpath('%s/%s' % (dirpath, filename))
                if not re.match(self.reSrcPathPattern, fullpath, re.I): continue
                sourceFilepathList.append(fullpath)

        self.load()
        
        for sourceFilepath in sourceFilepathList:
            if (specifiedClientVer is not None) and (specifiedClientVer not in sourceFilepath): continue
            print('正在汉化, 请稍候: %s' % os.path.relpath(sourceFilepath, leeClientDir))
            match = re.search(self.reDstPathPattern, sourceFilepath, re.MULTILINE | re.IGNORECASE | re.DOTALL)
            if match is None:
                self.leeCommon.exitWithMessage('无法确定翻译后的文件的存放位置, 程序终止')
            destinationPath = '%s/Translated/%s' % (match.group(1), match.group(2))
            self.translate(sourceFilepath, destinationPath)
            print('汉化完毕, 保存到: %s\r\n' % os.path.relpath(destinationPath, leeClientDir))
        
        return True

    def translate(self, srcFilepath, dstFilepath):
        pass
