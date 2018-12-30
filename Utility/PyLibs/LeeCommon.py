# -*- coding: utf-8 -*-

import ctypes
import hashlib
import os
import platform
import sys
from functools import partial

import chardet

from PyLibs import LeeConstant

if platform.system() == 'Windows':
    import winreg

class LeeCommon:
    '''
    这个类用来存放一些通用的函数
    此类中的任何一个方法都可以被独立使用, 无需依赖
    '''
    def __init__(self):
        self.leeConstant = LeeConstant()
        self.__cutup_len = 64

    def verifyAgentLocation(self):
        '''
        用于验证此脚本是否处于正确的运行位置
        '''
        scriptDir = self.getScriptDirectory()
        leeClientDir = self.getLeeClientDirectory()
        verifyPassFlag = True

        # 切换工作目录为脚本所在目录
        os.chdir(scriptDir)

        # 检查脚本所在的目录中, 是否存在特定的平级目录
        verifyDirList = ['PyLibs', 'Patches', 'Resources']
        for dirname in verifyDirList:
            verifyPath = (os.path.abspath(scriptDir + dirname) + os.sep)
            if not (os.path.isdir(verifyPath) and os.path.exists(verifyPath)):
                verifyPassFlag = False

        # 检查脚本所在的上级目录中, 是否存在特定的文件
        verifyFileList = ['cps.dll', 'aossdk.dll']
        for file in verifyFileList:
            verifyPath = (os.path.abspath(leeClientDir + file))
            if not (os.path.isfile(verifyPath) and os.path.exists(verifyPath)):
                verifyPassFlag = False

        # 任何一个不通过, 都认为脚本所处的位置不正确
        return verifyPassFlag

    def removeEmptyDirectorys(self, folderpath):
        '''
        递归移除指定目录中的所有空目录
        '''
        for dirpath, _dirnames, _filenames in os.walk(folderpath, topdown = False):
            if not os.listdir(dirpath):
                os.rmdir(dirpath)

    def getScriptDirectory(self):
        '''
        获取当前脚本所在的上级目录位置 (末尾自动补充斜杠)
        '''
        return os.path.abspath(
            os.path.join(os.path.split(os.path.realpath(__file__))[0], '..')
        ) + os.sep

    def getLeeClientDirectory(self):
        '''
        获取 LeeClient 的主目录 (末尾自动补充斜杠)
        '''
        scriptDir = self.getScriptDirectory()
        return os.path.abspath(os.path.join(scriptDir, '..')) + os.sep

    def getBeforePatchesDirectory(self, isImport = False):
        '''
        获取通用的 BeforePatches 目录 (末尾自动补充斜杠)
        '''
        scriptDir = self.getScriptDirectory()
        baseDirname = 'Import' if isImport else 'Patches'
        return os.path.abspath('%s/%s/Common/BeforePatches' % (scriptDir, baseDirname)) + os.sep

    def getAfterPatchesDirectory(self, isImport = False):
        '''
        获取通用的 AfterPatches 目录 (末尾自动补充斜杠)
        '''
        scriptDir = self.getScriptDirectory()
        baseDirname = 'Import' if isImport else 'Patches'
        return os.path.abspath('%s/%s/Common/AfterPatches' % (scriptDir, baseDirname)) + os.sep

    def getClientBuildDirectory(self, clientver):
        '''
        获取客户端版本的 Build 目录 (末尾自动补充斜杠)
        '''
        scriptDir = self.getScriptDirectory()
        return os.path.abspath('%s/Patches/%s/Ragexe/Build' % (scriptDir, clientver)) + os.sep

    def getClientOriginDirectory(self, clientver):
        '''
        获取客户端版本的 Original 目录 (末尾自动补充斜杠)
        '''
        scriptDir = self.getScriptDirectory()
        return os.path.abspath(
            '%s/Patches/%s/Resource/Original' % (scriptDir, clientver)
        ) + os.sep

    def getClientTranslatedDirectory(self, clientver):
        '''
        获取客户端版本的 Translated 目录 (末尾自动补充斜杠)
        '''
        scriptDir = self.getScriptDirectory()
        return os.path.abspath(
            '%s/Patches/%s/Resource/Translated' % (scriptDir, clientver)
        ) + os.sep

    def getClientImportDirectory(self, clientver):
        '''
        获取客户端版本的 Import 目录 (末尾自动补充斜杠)
        '''
        scriptDir = self.getScriptDirectory()
        return os.path.abspath('%s/Import/%s' % (scriptDir, clientver)) + os.sep

    def normpath(self, path):
        '''
        改进版本的 os.path.normpath 会自动根据系统调整路径
        '''
        return os.path.normpath(path.replace('\\', os.path.sep).replace('/', os.path.sep))

    def __encodingMaps(self, encoding):
        '''
        对一些编码的超集进行转换,
        比如 CP949 是 EUC-KR 的超集, GBK 是 GB2312 的超集
        '''
        encodeingMaps = {
            'EUC-KR': 'CP949',
            'GB2312': 'GBK'
        }

        if encoding.upper() in encodeingMaps:
            encoding = encodeingMaps[encoding.upper()]

        return encoding

    def getEncodingByByte(self, bytebuffer):
        if bytebuffer is not None:
            response = chardet.detect(bytebuffer)
            encoding = response['encoding']
            return None if encoding is None else self.__encodingMaps(encoding)
        return None

    def getEncodingByFile(self, filepath):
        def analysisBlocksEncoding(blocks_encoding):
            validEncoding = {}

            for encoding in blocks_encoding:
                # 检测不到编码内容, 或者概率小于 50% 的过滤掉
                if encoding is None or encoding['confidence'] < 0.5:
                    continue
                # 记录这个编码出现的次数, 后续推断使用
                codepage = encoding['encoding']
                if codepage is not None:
                    codepage = codepage.upper()
                codepage = self.__encodingMaps(codepage)
                if codepage not in validEncoding:
                    validEncoding[codepage] = 1
                else:
                    validEncoding[codepage] = validEncoding[codepage] + 1

            validEncodingList = sorted(validEncoding, reverse=True)

            if 'CP949' in validEncodingList or 'EUC-KR' in validEncodingList:
                validEncodingList.append('GBK')
                validEncodingList.append('LATIN1')

            return validEncodingList

        def tryUseingEncoding(filepath, encoding):
            try:
                encoding = self.__encodingMaps(encoding)
                f = open(filepath, 'r', encoding = encoding)
                _content = f.readlines()
                f.close()
                return True
            except UnicodeDecodeError as _err:
                return False

        f = open(filepath, 'rb')

        # 获取文件的总长度
        f.seek(0, 2)
        filesize = f.tell()
        f.seek(0, 0)

        # 初始化的块长度为 1024 * 4
        blocksize = 1024 * 4

        # 文件大小和块大小相比, 取最小那个值, 作为新的块大小
        blocksize = filesize if filesize < blocksize else blocksize

        # 每次读取 blocksize 长度的数据
        blocks = iter(partial(f.read, blocksize), b'')

        # 记录每个块的编码检测结果, 和判断准确率
        blocks_encoding = []
        failed_encoding = []

        for block in blocks:
            response = chardet.detect(block)
            if response is not None and \
                response['encoding'] not in failed_encoding:
                blocks_encoding.append(response)

            # 当获得的块结果小于 10 次, 那么继续分析
            if len(blocks_encoding) < 10:
                continue

            # 如果大于等于 10 次, 那么对内容进行一次排重整理
            validEncodingList = analysisBlocksEncoding(blocks_encoding)
            vaildEncoding = None

            for encoding in validEncodingList:
                if tryUseingEncoding(filepath, encoding):
                    vaildEncoding = self.__encodingMaps(encoding)
                    break
                else:
                    failed_encoding.append(encoding)

            if vaildEncoding is not None:
                return vaildEncoding
            blocks_encoding.clear()

        if blocks_encoding is not None:
            validEncodingList = analysisBlocksEncoding(blocks_encoding)
            for encoding in validEncodingList:
                if tryUseingEncoding(filepath, encoding):
                    return self.__encodingMaps(encoding)

        f.close()
        return None

    def getRagexeClientList(self, dirpath):
        '''
        根据指定的 dir 中枚举出子目录的名字
        这里的目录名称为 Ragexe 客户端版本号的日期

        返回: Array 保存着每个子目录名称的数组
        '''
        dirlist = []

        try:
            osdirlist = os.listdir(dirpath)
        except Exception as _err:
            print('getRagexeClientList Access Deny')
            return None

        for dname in osdirlist:
            if dname.lower() in ['common', 'backup']:
                continue
            if os.path.isdir(os.path.normpath(dirpath) + os.path.sep + dname):
                dirlist.append(dname)

        dirlist.sort()
        return dirlist

    def getMD5ForString(self, strContent):
        '''
        获取一段字符串内容的 MD5 值
        '''
        return hashlib.md5(strContent.encode(encoding = 'utf-8')).hexdigest()

    def getMD5ForSmallFile(self, filepath):
        '''
        获取一个小文件的 MD5 值
        '''
        return hashlib.md5(open(filepath, 'rb').read()).hexdigest()

    def cleanScreen(self):
        '''
        用于清理终端的屏幕 (Win下测试过, Linux上没测试过)
        '''
        sysstr = platform.system()
        if sysstr == 'Windows':
            os.system('cls')
        else:
            os.system('clear')

    def pauseScreen(self):
        '''
        如果在 Win 平台下的话, 输出一个 pause 指令
        '''
        sysstr = platform.system()
        if sysstr == 'Windows':
            os.system('pause')

    def exitWithMessage(self, message):
        '''
        抛出一个错误消息并终止脚本的运行
        '''
        print(message + '\r\n')

        self.pauseScreen()
        sys.exit(0)

    def isDirectoryExists(self, dirpath):
        '''
        判断指定的目录是否存在
        '''
        return os.path.exists(dirpath) and os.path.isdir(dirpath)

    def isFileExists(self, filepath):
        '''
        判断指定的文件是否存在
        '''
        return os.path.exists(filepath) and os.path.isfile(filepath)

    def isDotNetFrameworkInstalled(self, version):
        '''
        判断指定版本的 .Net framework 是否已安装
        此函数仅用于 Windows 平台
        '''
        try:
            if platform.system() != 'Windows':
                self.exitWithMessage(
                    '很抱歉, %s 此函数目前只能在 Windows 平台上运行.' % sys._getframe().f_code.co_name
                )
            framework_key = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                'SOFTWARE\\Microsoft\\NET Framework Setup\\NDP\\%s' % version
            )
            _value, _value_type = winreg.QueryValueEx(framework_key, 'InstallPath')
            return self.isDirectoryExists(_value)
        except Exception as _err:
            return False

    def getDiskFreeSpace(self, driver):
        '''
        获取指定盘符(比如 C:)的磁盘剩余空间字节数
        此函数仅用于 Windows 平台
        '''
        if platform.system() != 'Windows':
            self.exitWithMessage('很抱歉, %s 此函数目前只能在 Windows 平台上运行.' % sys._getframe().f_code.co_name)

        if driver.endswith(':'):
            driver = driver.upper().split(':')[0]

        if not driver.upper().isalpha() or len(driver) > 1:
            return None

        free_bytes = ctypes.c_ulonglong(0)
        ctypes.windll.kernel32.GetDiskFreeSpaceExW(
            ctypes.c_wchar_p('%s:' % driver), None, None, ctypes.pointer(free_bytes)
        )
        return free_bytes.value

    def isLastElement(self, list_or_dict, val):
        '''
        判断一个值是否处于某个列表或者字典的最后一个
        '''
        if isinstance(list_or_dict, dict):
            return list(list_or_dict).index(val) == len(list_or_dict) - 1
        else:
            return list_or_dict.index(val) == len(list_or_dict) - 1

    def isLastReturn(self, list_or_dict, val, true_str, false_str):
        '''
        根据一个值是否处于某个列表或者字典的最后一个来返回字符串
        '''
        return true_str if self.isLastElement(list_or_dict, val) else false_str

    def isEmpty(self, obj):
        '''
        判断一个对象的内容是否为空或者为 None
        '''
        if hasattr(obj, "__len__"):
            return not obj
        else:
            return obj is None

    def atoi(self, val):
        '''
        用于将一个字符串尝试转换成 Int 数值
        转换成功则返回 Int 数值，失败则返回布尔类型的 False
        '''
        try:
            int(val)
            return int(val)
        except ValueError:
            return False

    def iterlen(self, iterator):
        '''
        查询一个迭代器的内容长度(内容个数)
        '''
        if hasattr(iterator, "__len__"):
            return len(iterator)

        nelements = 0
        for _ in iterator:
            nelements += 1
            return nelements

    def normPattern(self, rePattern):
        '''
        对用于描述一个路径的正则表达式中的斜杆进行处理
        以便在 Linux 或者 Win 平台上都能兼容
        '''
        return rePattern.replace('/', r'\\' if os.path.sep == '\\' else '/')

    def strHexToRgb(self, val):
        '''
        将类似 #ffffff 的颜色代码转换成 (255, 255, 255)
        '''
        val = val.lstrip('#')
        lv = len(val)
        return tuple(int(val[i:i+lv//3], 16) for i in range(0, lv, lv//3))

    def is_positive(self, z):
        '''
        判断一个数字是否为正整数
        '''
        try:
            z_handle = int(z)
            if isinstance(z_handle,int) and z_handle >= 0:
                return True
        except Exception as _err:
            return False

    def getStringWidthLen(self, val):
        '''
        计算字符串长度, 一个中文算两个字符
        '''
        length = len(val)
        utf8_length = len(val.encode('utf-8'))
        return int((utf8_length - length)/2 + length)

    def simpleConfirm(self, lines, title, prompt, menus, evalcmd):
        '''
        简易的确认对话框
        '''
        self.cleanScreen()
        if not title is None:
            titleFmt = '= %s%-' + str(60 - self.getStringWidthLen(title)) + 's ='
            print('=' * self.__cutup_len)
            print(titleFmt % (title, ''))
            print('=' * self.__cutup_len)

        print('')

        for line in lines:
            print(line)

        print('')
        print('=' * self.__cutup_len)
        print('')
        user_select = input(prompt + ' [Y/N]: ')
        print('')

        if user_select in ('N', 'n'):
            if menus is not None:
                menus.item_End()
            elif evalcmd is None:
                return False
        elif user_select in ('Y', 'y'):
            if evalcmd is not None:
                exec(evalcmd)
            elif evalcmd is None:
                return True
        else:
            self.exitWithMessage('请填写 Y 或者 N 之后回车确认, 请不要输入其他字符')

    def simpleMenu(self, items, title, prompt, withCancel = False,
                   injectClass = None, cancelExec = None, resultMap = None):
        '''
        简易的选择菜单
        '''
        self.cleanScreen()
        if not title is None:
            titleFmt = '= %s%-' + str(60 - self.getStringWidthLen(title)) + 's ='
            print('=' * self.__cutup_len)
            print(titleFmt % (title, ''))
            print('=' * self.__cutup_len)

        print('')

        index = 0
        menuIndexAndResultIndexDict = {}
        for item in items:
            print('%d - %s' % (index, item[0]))
            menuIndexAndResultIndexDict[index] = None if item[2] is None else item[2]
            index = index + 1
        if withCancel:
            print('%d - %s' % (index, '取消'))
        print('')
        print('=' * self.__cutup_len)
        print('')
        userSelect = input('%s (%d - %d): ' % (prompt, 0, len(items) - 1))
        print('')

        if (not self.atoi(userSelect) and userSelect != '0'):
            self.exitWithMessage('请填写正确的菜单编号(纯数字), 不要填写其他字符')

        userSelect = self.atoi(userSelect)

        if (userSelect == len(items) and withCancel):
            if cancelExec is not None:
                exec(cancelExec)
            return None

        if (userSelect >= len(items) or items[userSelect] is None):
            self.exitWithMessage('请填写正确的菜单编号(纯数字), 不要超出范围')
        elif items[userSelect][1] is not None:
            exec(items[userSelect][1])

        if resultMap is None:
            return self.atoi(userSelect)
        elif (isinstance(resultMap, list) and
              userSelect in menuIndexAndResultIndexDict and
              menuIndexAndResultIndexDict[userSelect] is not None and
              len(resultMap) > menuIndexAndResultIndexDict[userSelect]
             ):
            return resultMap[menuIndexAndResultIndexDict[userSelect]]
        return None

    def simpleInput(self, lines, title, prompt, menus, evalcmd):
        '''
        简易的确认对话框
        '''
        self.cleanScreen()
        if not title is None:
            titleFmt = '= %s%-' + str(60 - self.getStringWidthLen(title)) + 's ='
            print('=' * self.__cutup_len)
            print(titleFmt % (title, ''))
            print('=' * self.__cutup_len)

        for line in lines:
            print(line)

        print('')
        print('=' * self.__cutup_len)
        print('')
        user_input = input(prompt + ': ')
        print('')

        if evalcmd is not None:
            exec(evalcmd)
        elif evalcmd is None:
            return user_input
