"""
工具模块测试

测试覆盖:
- 核心 Base64 编解码
- 核心 Hash 工具
- 核心 JSON 格式化
"""

import pytest
import base64
import hashlib
import json


class TestBase64Codec:
    """Base64 编解码测试"""

    def test_encode(self):
        """测试 Base64 编码"""
        text = "Hello, World!"
        encoded = base64.b64encode(text.encode()).decode()
        assert encoded == "SGVsbG8sIFdvcmxkIQ=="

    def test_decode(self):
        """测试 Base64 解码"""
        encoded = "SGVsbG8sIFdvcmxkIQ=="
        decoded = base64.b64decode(encoded).decode()
        assert decoded == "Hello, World!"

    def test_encode_chinese(self):
        """测试中文编码"""
        text = "你好，世界！"
        encoded = base64.b64encode(text.encode('utf-8')).decode()
        decoded = base64.b64decode(encoded).decode('utf-8')
        assert decoded == text

    def test_empty_string(self):
        """测试空字符串"""
        text = ""
        encoded = base64.b64encode(text.encode()).decode()
        assert encoded == ""

    def test_round_trip(self):
        """测试编解码往返"""
        text = "Test Round Trip 123 !@#$%"
        encoded = base64.b64encode(text.encode()).decode()
        decoded = base64.b64decode(encoded).decode()
        assert decoded == text


class TestHashTool:
    """Hash 工具测试"""

    def test_md5(self):
        """测试 MD5 哈希"""
        text = "hello"
        md5_hash = hashlib.md5(text.encode()).hexdigest()
        assert md5_hash == "5d41402abc4b2a76b9719d911017c592"

    def test_sha256(self):
        """测试 SHA256 哈希"""
        text = "hello"
        sha256_hash = hashlib.sha256(text.encode()).hexdigest()
        assert sha256_hash == "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"

    def test_sha1(self):
        """测试 SHA1 哈希"""
        text = "hello"
        sha1_hash = hashlib.sha1(text.encode()).hexdigest()
        assert sha1_hash == "aaf4c61ddcc5e8a2dabede0f3b482cd9aea9434d"

    def test_hash_consistency(self):
        """测试哈希一致性"""
        text = "consistent"
        hash1 = hashlib.md5(text.encode()).hexdigest()
        hash2 = hashlib.md5(text.encode()).hexdigest()
        assert hash1 == hash2

    def test_hash_different_inputs(self):
        """测试不同输入产生不同哈希"""
        hash1 = hashlib.md5("input1".encode()).hexdigest()
        hash2 = hashlib.md5("input2".encode()).hexdigest()
        assert hash1 != hash2


class TestJSONFormatter:
    """JSON 格式化测试"""

    def test_valid_json(self):
        """测试有效 JSON"""
        data = {"name": "test", "value": 123}
        json_str = json.dumps(data, indent=2)
        assert '"name"' in json_str
        assert '"test"' in json_str

    def test_parse_json(self):
        """测试 JSON 解析"""
        json_str = '{"name": "test", "value": 123}'
        data = json.loads(json_str)
        assert data["name"] == "test"
        assert data["value"] == 123

    def test_nested_json(self):
        """测试嵌套 JSON"""
        data = {
            "user": {
                "name": "test",
                "profile": {
                    "age": 25
                }
            }
        }
        json_str = json.dumps(data)
        parsed = json.loads(json_str)
        assert parsed["user"]["profile"]["age"] == 25

    def test_json_array(self):
        """测试 JSON 数组"""
        data = [1, 2, 3, "test"]
        json_str = json.dumps(data)
        parsed = json.loads(json_str)
        assert len(parsed) == 4
        assert parsed[3] == "test"

    def test_invalid_json(self):
        """测试无效 JSON"""
        invalid_json = '{"name": "test"'
        with pytest.raises(json.JSONDecodeError):
            json.loads(invalid_json)


class TestTextCounter:
    """文本计数测试"""

    def test_count_characters(self):
        """测试字符计数"""
        text = "Hello, World!"
        assert len(text) == 13

    def test_count_words(self):
        """测试单词计数"""
        text = "Hello World Test"
        words = text.split()
        assert len(words) == 3

    def test_count_lines(self):
        """测试行数计数"""
        text = "Line 1\nLine 2\nLine 3"
        lines = text.split('\n')
        assert len(lines) == 3

    def test_count_chinese_characters(self):
        """测试中文字符计数"""
        text = "你好世界"
        assert len(text) == 4

    def test_count_mixed_text(self):
        """测试混合文本计数"""
        text = "Hello 你好 World 世界"
        # 空格分隔的单词数
        words = text.split()
        assert len(words) == 4


class TestURLCodec:
    """URL 编解码测试"""

    def test_url_encode(self):
        """测试 URL 编码"""
        from urllib.parse import quote
        text = "Hello World"
        encoded = quote(text)
        assert encoded == "Hello%20World"

    def test_url_decode(self):
        """测试 URL 解码"""
        from urllib.parse import unquote
        encoded = "Hello%20World"
        decoded = unquote(encoded)
        assert decoded == "Hello World"

    def test_url_encode_chinese(self):
        """测试中文 URL 编码"""
        from urllib.parse import quote, unquote
        text = "你好"
        encoded = quote(text)
        decoded = unquote(encoded)
        assert decoded == text

    def test_url_encode_special_chars(self):
        """测试特殊字符 URL 编码"""
        from urllib.parse import quote, unquote
        text = "a=1&b=2"
        encoded = quote(text, safe='')
        decoded = unquote(encoded)
        assert decoded == text
