# -*- coding: utf-8 -*-
import os
import sys

import pytest

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)

from scripts.feishu_setup import validate, mask  # noqa: E402


def test_validate_accepts_feishu_webhook():
    validate("https://open.feishu.cn/open-apis/bot/v2/hook/abc123")


def test_validate_accepts_larksuite_webhook():
    validate("https://open.larksuite.com/open-apis/bot/v2/hook/abc123")


def test_validate_rejects_other_urls():
    with pytest.raises(SystemExit):
        validate("https://example.com/hook/abc")


def test_mask_does_not_leak_token():
    url = "https://open.feishu.cn/open-apis/bot/v2/hook/abcdef123456"
    m = mask(url)
    assert "abcdef12" not in m
    assert m.endswith("3456")
