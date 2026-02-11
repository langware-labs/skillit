"""Tests for xml_str_to_flow_data_dict and MCP server flow_tag integration."""

import json
import pytest

from notify import xml_str_to_flow_data_dict


class TestXmlStrToFlowDataDict:
    """Unit tests for xml_str_to_flow_data_dict."""

    def test_simple_string_content(self):
        xml = '<flow-chat>Hello world</flow-chat>'
        result = xml_str_to_flow_data_dict(xml)
        assert result == {
            "element_type": "chat",
            "data_type": "string",
            "flow_value": "Hello world",
        }

    def test_element_type_extraction(self):
        xml = '<flow-started_generating_skill>progress</flow-started_generating_skill>'
        result = xml_str_to_flow_data_dict(xml)
        assert result["element_type"] == "started_generating_skill"

    def test_skill_ready_type(self):
        xml = '<flow-skill_ready>done</flow-skill_ready>'
        result = xml_str_to_flow_data_dict(xml)
        assert result["element_type"] == "skill_ready"
        assert result["flow_value"] == "done"

    def test_index_attribute(self):
        xml = '<flow-chat i="5">Hello</flow-chat>'
        result = xml_str_to_flow_data_dict(xml)
        assert result["index"] == 5

    def test_index_absent(self):
        xml = '<flow-chat>Hello</flow-chat>'
        result = xml_str_to_flow_data_dict(xml)
        assert "index" not in result

    def test_created_time_attribute(self):
        xml = '<flow-chat t="2026-02-11T10:00:00Z">Hello</flow-chat>'
        result = xml_str_to_flow_data_dict(xml)
        assert result["created_time"] == "2026-02-11T10:00:00Z"

    def test_created_time_absent(self):
        xml = '<flow-chat>Hello</flow-chat>'
        result = xml_str_to_flow_data_dict(xml)
        assert "created_time" not in result

    def test_all_attributes(self):
        xml = '<flow-task i="3" t="2026-01-15" data-type="string">Buy milk</flow-task>'
        result = xml_str_to_flow_data_dict(xml)
        assert result == {
            "element_type": "task",
            "data_type": "string",
            "flow_value": "Buy milk",
            "index": 3,
            "created_time": "2026-01-15",
        }

    def test_object_data_type_json(self):
        obj = {"title": "hello task", "description": "some desc"}
        xml = f'<flow-task data-type="object">{json.dumps(obj)}</flow-task>'
        result = xml_str_to_flow_data_dict(xml)
        assert result["data_type"] == "object"
        assert result["flow_value"] == obj

    def test_json_data_type(self):
        obj = {"key": "value"}
        xml = f'<flow-task data-type="json">{json.dumps(obj)}</flow-task>'
        result = xml_str_to_flow_data_dict(xml)
        assert result["flow_value"] == obj

    def test_entity_data_type(self):
        obj = {"id": 1, "name": "test"}
        xml = f'<flow-entity data-type="entity">{json.dumps(obj)}</flow-entity>'
        result = xml_str_to_flow_data_dict(xml)
        assert result["flow_value"] == obj

    def test_object_data_type_invalid_json_fallback(self):
        xml = '<flow-task data-type="object">not valid json</flow-task>'
        result = xml_str_to_flow_data_dict(xml)
        assert result["flow_value"] == "not valid json"
        assert result["data_type"] == "object"

    def test_html_entities_decoded(self):
        xml = '<flow-chat>Tom &amp; Jerry &lt;3</flow-chat>'
        result = xml_str_to_flow_data_dict(xml)
        assert result["flow_value"] == "Tom & Jerry <3"

    def test_html_entities_in_json(self):
        xml = '<flow-task data-type="object">{"msg": "a &amp; b"}</flow-task>'
        result = xml_str_to_flow_data_dict(xml)
        assert result["flow_value"] == {"msg": "a & b"}

    def test_empty_content(self):
        xml = '<flow-status></flow-status>'
        result = xml_str_to_flow_data_dict(xml)
        assert result["flow_value"] == ""

    def test_self_closing_tag(self):
        xml = '<flow-ping i="1"/>'
        result = xml_str_to_flow_data_dict(xml)
        assert result["element_type"] == "ping"
        assert result["flow_value"] == ""
        assert result["index"] == 1

    def test_default_data_type_is_string(self):
        xml = '<flow-chat>Hello</flow-chat>'
        result = xml_str_to_flow_data_dict(xml)
        assert result["data_type"] == "string"

    def test_non_flow_tag_raises(self):
        with pytest.raises(ValueError, match="Expected a flow-\\* element"):
            xml_str_to_flow_data_dict('<div>not a flow tag</div>')

    def test_invalid_xml_raises(self):
        with pytest.raises(Exception):
            xml_str_to_flow_data_dict('not xml at all')

    def test_extra_attributes_ignored(self):
        xml = '<flow-chat i="1" focus="true" warning="oops" custom="val">Hi</flow-chat>'
        result = xml_str_to_flow_data_dict(xml)
        assert result["element_type"] == "chat"
        assert result["flow_value"] == "Hi"
        assert result["index"] == 1
        # Extra attributes like focus, warning, custom are not in the result
        assert "focus" not in result
        assert "warning" not in result
        assert "custom" not in result
