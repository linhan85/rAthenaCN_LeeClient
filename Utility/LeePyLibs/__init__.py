# -*- coding: utf-8 -*-

__author__ = "CairoLee"

from .LeeCommon import _LeeCommon
from .LeeConstant import _LeeConstant
from .LeeButtonRender import _LeeButtonRender
from .LeeButtonTranslator import _LeeButtonTranslator
from .LeePatchManager import _LeePatchManager

LeeCommon = _LeeCommon()
LeeConstant = _LeeConstant()
LeePatchManager = _LeePatchManager(LeeCommon)
LeeButtonRender = _LeeButtonRender(LeeCommon)
LeeButtonTranslator = _LeeButtonTranslator(LeeCommon, LeeButtonRender)
