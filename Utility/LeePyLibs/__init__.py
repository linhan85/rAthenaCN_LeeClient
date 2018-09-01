# -*- coding: utf-8 -*-

__author__ = "CairoLee"

from .LeeCommon import _LeeCommon
from .LeeConstant import _LeeConstant
from .LeeButtonRender import _LeeButtonRender
from .LeeButtonTranslator import _LeeButtonTranslator
from .LeePatchManager import _LeePatchManager
from .LeeVerifier import _LeeVerifier

# 常量定义
# ====================================================
LeeConstant = _LeeConstant()
LeeConstant.Environment = 'develop'
LeeConstant.EncodingForSaveFile = 'gbk'

# 常量定义
# ====================================================
LeeCommon = _LeeCommon(LeeConstant)
LeePatchManager = _LeePatchManager(LeeCommon)
LeeButtonRender = _LeeButtonRender(LeeCommon)
LeeButtonTranslator = _LeeButtonTranslator(LeeCommon, LeeButtonRender)
LeeVerifier = _LeeVerifier(LeeCommon)
