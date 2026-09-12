import os
import time
from typing import Optional, Dict, Any, List
from openai import OpenAI, APIError, AuthenticationError

from app.core.database import SessionLocal
from app.models.entities import SysConfig
import json

class LLMService:
    """基于 OpenAI SDK 标准接口的多模态大模型接入服务 (DeepSeek/Qwen/OpenAI)"""
    
    @staticmethod
    def get_active_config() -> Dict[str, Any]:
        """从数据库系统设置中动态提取配置"""
        default_config = {
            "provider": "DeepSeek",
            "api_base": "https://api.deepseek.com/v1",
            "api_key": os.getenv("DEEPSEEK_API_KEY", ""),
            "chat_model": "deepseek-chat",
            "vl_model": "deepseek-vl",
            "temperature": 0.7,
            "max_tokens": 4096
        }
        db = SessionLocal()
        try:
            cfg = db.query(SysConfig).filter(SysConfig.config_key == "llm_settings").first()
            if cfg and cfg.config_value:
                val = json.loads(cfg.config_value)
                for k in default_config.keys():
                    if val.get(k):
                        default_config[k] = val[k]
        except Exception:
            pass
        finally:
            db.close()
        return default_config

    @classmethod
    def get_client(cls, api_key: Optional[str] = None, api_base: Optional[str] = None) -> OpenAI:
        cfg = cls.get_active_config()
        key = api_key or cfg.get("api_key") or "sk-placeholder"
        base = api_base or cfg.get("api_base") or "https://api.deepseek.com/v1"
        return OpenAI(api_key=key, base_url=base)

    @classmethod
    def test_connection(cls, api_key: str, api_base: str, model_name: str) -> Dict[str, Any]:
        """执行生产级连通性探测握手"""
        start = time.time()
        client = cls.get_client(api_key=api_key, api_base=api_base)
        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": "你好，请仅回复【津韵润乡测试连通成功】八个字。"}],
                max_tokens=30,
                timeout=10.0
            )
            latency = int((time.time() - start) * 1000)
            content = response.choices[0].message.content or "OK"
            return {
                "success": True,
                "latency_ms": latency,
                "reply": content,
                "model": model_name
            }
        except AuthenticationError as e:
            return {
                "success": False,
                "error": f"鉴权失败，API Key 无效或过期: {str(e)}",
                "latency_ms": int((time.time() - start) * 1000)
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"握手失败: {str(e)}",
                "latency_ms": int((time.time() - start) * 1000)
            }

llm_service = LLMService()
