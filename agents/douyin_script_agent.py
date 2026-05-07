"""
抖音脚本 Agent - 抖音短视频脚本专家
"""

from typing import Optional

from crewai import Agent
from crewai.tools import BaseTool

from config import LLMManagerConfig, DouyinConfig
from config.llm_config import get_llm_for_agent
from models import DouyinScript, DouyinVideo, DouyinContent
from tools.prompt_tools import prompt_manager
from tools.crewai_llm import create_llm
from tools.llm_tools import LLMResponseParser


class DouyinScriptAgent:
    """抖音脚本创作Agent"""

    def __init__(
        self,
        llm_config: Optional[LLMManagerConfig] = None,
        platform_config: Optional[DouyinConfig] = None,
        tools: Optional[list[BaseTool]] = None,
    ):
        self._llm_config = llm_config or get_llm_for_agent("douyin")
        self.platform_config = platform_config or DouyinConfig()
        self.tools = tools or []
        self._agent: Optional[Agent] = None

    @property
    def agent(self) -> Agent:
        """获取 CrewAI Agent 实例"""
        if self._agent is None:
            prompt = prompt_manager.load_prompt("douyin_script_agent")
            self._agent = Agent(
                role="抖音短视频脚本专家",
                goal="创作吸引眼球的短视频脚本",
                backstory=prompt,
                tools=self.tools,
                verbose=True,
                llm=create_llm(self._llm_config),
            )
        return self._agent

    def generate_script(
        self,
        topic: str,
        material_pack: dict,
        duration_seconds: int = 60,
    ) -> DouyinContent:
        """
        生成抖音脚本

        Args:
            topic: 视频主题
            material_pack: 素材包
            duration_seconds: 目标时长

        Returns:
            DouyinContent: 抖音内容
        """
        prompt = self._build_prompt(topic, material_pack, duration_seconds)

        response = self.agent.kickoff(prompt)

        try:
            content = response.content if hasattr(response, "content") else str(response)
            script_data = LLMResponseParser.parse_json(content)

            script = DouyinScript(
                title=script_data.get("title", topic),
                hooks=script_data.get("hooks", ""),
                script_content=script_data.get("script_content", ""),
                cta=script_data.get("cta", ""),
                duration_seconds=script_data.get("duration_seconds", duration_seconds),
                suggested_music=script_data.get("suggested_music"),
                visual_suggestions=script_data.get("visual_suggestions", []),
            )

            video = DouyinVideo(
                title=script.title,
                script=script,
                video_tags=script_data.get("video_tags", []),
                hashtags=script_data.get("hashtags", []),
            )

            return DouyinContent(
                video=video,
                platform="douyin",
                ai_flavor_score=script_data.get("ai_flavor_score", 75),
                compliance_status="passed",
            )
        except Exception as e:
            return DouyinContent(
                video=DouyinVideo(
                    title=topic,
                    script=DouyinScript(
                        title=topic,
                        hooks="",
                        script_content="",
                        cta="",
                        duration_seconds=duration_seconds,
                    ),
                ),
                platform="douyin",
                ai_flavor_score=0,
                compliance_status="failed",
                metadata={"error": str(e)},
            )

    def _build_prompt(
        self,
        topic: str,
        material_pack: dict,
        duration_seconds: int,
    ) -> str:
        """构建提示词"""
        return f"""
请根据以下信息创作抖音短视频脚本：

视频主题：{topic}

素材包信息：
- 品牌：{material_pack.get('brand', {}).get('name', '未知')}
- 产品：{material_pack.get('product', {}).get('name', '未知')}
- 核心卖点：{', '.join(material_pack.get('product', {}).get('selling_points', [])[:3])}
- 目标人群：{material_pack.get('persona', {}).get('profile', '未知')}

要求：
- 时长{duration_seconds}秒
- 前3秒必须有强力开场钩子抓住用户
- 每5秒一个信息点或小高潮
- 结尾有明确行动号召（评论/点赞/收藏）
- 提供3-5个画面切换建议
- 提供3-5个话题标签

输出格式为JSON：
{{"title": "标题", "hooks": "开场钩子", "script_content": "主体脚本", "cta": "行动号召", "duration_seconds": {duration_seconds}, "visual_suggestions": ["建议1", "建议2"], "hashtags": ["#话题1", "#话题2"]}}
"""

