from typing import Any
import requests
import uuid
import base64
import json
from dify_plugin import ToolProvider
from dify_plugin.errors.tool import ToolProviderCredentialValidationError

class DoubaoTtsProvider(ToolProvider):
    def _validate_credentials(self, credentials: dict[str, Any]) -> None:
        appid = credentials.get("appid")
        access_token = credentials.get("access_token")
        cluster = credentials.get("cluster")

        if not appid or not access_token or not cluster:
            raise ToolProviderCredentialValidationError("appid、access_token 或 cluster 缺失")

        # 准备测试调用 payload
        test_text = "测试"
        voice_type = "zh_female_wanqudashu_moon_bigtts"  # 默认音色
        headers = {
            "Authorization": f"Bearer;{access_token}"
        }
        request_json = {
            "app": {
                "appid": appid,
                "token": access_token,
                "cluster": cluster
            },
            "user": {
                "uid": "dify_plugin_validation_user"
            },
            "audio": {
                "voice_type": voice_type,
                "encoding": "mp3",
                "speed_ratio": 1.0,
                "volume_ratio": 1.0,
                "pitch_ratio": 1.0,
            },
            "request": {
                "reqid": str(uuid.uuid4()),
                "text": test_text,
                "text_type": "plain",
                "operation": "query",
                "with_frontend": 1,
                "frontend_type": "unitTson"
            }
        }

        try:
            resp = requests.post(
                url="https://openspeech.bytedance.com/api/v1/tts",
                headers=headers,
                json=request_json,
                timeout=(10, 30)
            )
            resp.raise_for_status()
            result = resp.json()
            if "data" not in result:
                raise ToolProviderCredentialValidationError("验证失败：API 返回无音频数据")
        except requests.RequestException as e:
            raise ToolProviderCredentialValidationError(f"请求失败: {str(e)}")
        except Exception as e:
            raise ToolProviderCredentialValidationError(f"验证异常: {str(e)}")