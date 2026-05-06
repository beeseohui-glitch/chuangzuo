from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class PlatformType(str, Enum):
    """平台类型"""
    XIAOHONGSHU = "xiaohongshu"
    WECHAT_PUBLIC = "wechat_public"
    DOUYIN = "douyin"
    WEIBO = "weibo"
    VIDEO_NUMBER = "video_number"


class PlatformComplianceRules(BaseModel):
    """平台合规规则"""
    prohibited_words: list[str] = Field(default_factory=list, description="违禁词列表")
    max_title_length: int = Field(default=20, description="标题最大字数")
    min_title_length: int = Field(default=10, description="标题最小字数")
    max_article_length: int = Field(default=1000, description="文章最大字数")
    min_article_length: int = Field(default=300, description="文章最小字数")
    max_tags: int = Field(default=10, description="最大标签数")
    requires_safety_warning: bool = Field(default=False, description="是否需要安全声明")


class XiaohongshuConfig(PlatformComplianceRules):
    """小红书平台配置"""
    platform: PlatformType = Field(default=PlatformType.XIAOHONGSHU)
    max_title_length: int = Field(default=20, ge=10, le=30)
    min_title_length: int = Field(default=15, ge=5, le=20)
    max_article_length: int = Field(default=600, ge=200, le=1000)
    min_article_length: int = Field(default=300, ge=100, le=500)
    max_tags: int = Field(default=10, ge=5, le=20)
    requires_safety_warning: bool = Field(default=True)
    prohibited_words: list[str] = Field(default_factory=lambda: [
        "最", "第一", "顶级", "绝对", "100%", "全网", "独家", "首发",
        "治疗", "治愈", "疗效", "疗效最好", "药到病除",
        "最好", "最强", "无敌", "完美"
    ])


class WechatPublicConfig(PlatformComplianceRules):
    """微信公众号配置"""
    platform: PlatformType = Field(default=PlatformType.WECHAT_PUBLIC)
    max_title_length: int = Field(default=30, ge=10, le=64)
    min_title_length: int = Field(default=5, ge=3, le=20)
    max_article_length: int = Field(default=20000, ge=500, le=50000)
    min_article_length: int = Field(default=500, ge=200, le=2000)
    max_tags: int = Field(default=5, ge=1, le=10)


class DouyinConfig(PlatformComplianceRules):
    """抖音平台配置"""
    platform: PlatformType = Field(default=PlatformType.DOUYIN)
    max_title_length: int = Field(default=30, ge=5, le=50)
    min_title_length: int = Field(default=5, ge=3, le=20)
    max_script_length: int = Field(default=2000, ge=100, le=5000)
    min_script_length: int = Field(default=100, ge=50, le=500)


class PlatformConfig(BaseModel):
    """平台配置管理器"""
    xiaohongshu: XiaohongshuConfig = Field(default_factory=XiaohongshuConfig)
    wechat_public: WechatPublicConfig = Field(default_factory=WechatPublicConfig)
    douyin: DouyinConfig = Field(default_factory=DouyinConfig)

    def get_config(self, platform: PlatformType) -> PlatformComplianceRules:
        """获取指定平台配置"""
        configs = {
            PlatformType.XIAOHONGSHU: self.xiaohongshu,
            PlatformType.WECHAT_PUBLIC: self.wechat_public,
            PlatformType.DOUYIN: self.douyin,
        }
        return configs.get(platform, self.xiaohongshu)
