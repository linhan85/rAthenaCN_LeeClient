# -*- coding: utf-8 -*-

__author__ = "CairoLee"

from .LeeCommon import _LeeCommon
from .LeeConstant import _LeeConstant
from .LeeButtonRender import _LeeButtonRender
from .LeeButtonTranslator import _LeeButtonTranslator

LeeCommon = _LeeCommon()
LeeConstant = _LeeConstant()
LeeButtonRender = _LeeButtonRender(LeeCommon)
LeeButtonTranslator = _LeeButtonTranslator(LeeCommon, LeeButtonRender)
