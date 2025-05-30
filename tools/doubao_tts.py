import base64
import json
import uuid
import logging
import requests

from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

class DoubaoTtsTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        try:
            appid = self.runtime.credentials["appid"]
            access_token = self.runtime.credentials["access_token"]
            cluster = self.runtime.credentials.get("cluster", "volcano_tts")
        except KeyError:
            yield self.create_text_message("appid 或 access_token 未配置或无效")
            return

        text = tool_parameters.get("text", "")
        if not text:
            yield self.create_text_message("请输入要合成的文本")
            return

        voice_type = tool_parameters.get("voice_type", "zh_female_wanqudashu_moon_bigtts")
        speed = float(tool_parameters.get("speed_ratio", 1.0))
        volume = float(tool_parameters.get("volume_ratio", 1.0))
        pitch = float(tool_parameters.get("pitch_ratio", 1.0))

        api_url = "https://openspeech.bytedance.com/api/v1/tts"
        headers = {
            "Authorization": f"Bearer;{access_token}"
        }

        request_json = {
            "app": {
                "appid": appid,
                "token": "access_token",  # 需写字符串 "access_token"
                "cluster": cluster
            },
            "user": {
                "uid": str(uuid.uuid4())
            },
            "audio": {
                "voice_type": voice_type,
                "encoding": "mp3",
                "speed_ratio": speed,
                "volume_ratio": volume,
                "pitch_ratio": pitch,
            },
            "request": {
                "reqid": str(uuid.uuid4()),
                "text": text,
                "text_type": "plain",
                "operation": "query",
                "with_frontend": 1,
                "frontend_type": "unitTson"
            }
        }

        try:
            response = requests.post(api_url, data=json.dumps(request_json), headers=headers, timeout=(10, 30))
            response.raise_for_status()
            result = response.json()
            if "data" not in result:
                yield self.create_text_message("接口未返回音频数据")
                return

            audio_base64 = result["data"]
            audio_bytes = base64.b64decode(audio_base64)
            yield self.create_blob_message(audio_bytes, meta={"mime_type": "audio/mpeg"})
        except requests.exceptions.ReadTimeout:
            yield self.create_text_message("请求超时，请稍后重试")
        except requests.exceptions.ConnectionError:
            yield self.create_text_message("网络连接错误，请检查网络设置")
        except requests.exceptions.RequestException as e:
            try:
                error_msg = response.json().get("message", str(e))
            except:
                error_msg = str(e)
            yield self.create_text_message(f"请求失败: {error_msg}")

