"""Playwright页面抓取器"""
from playwright.async_api import async_playwright, Browser, Page as PlaywrightPage
from typing import Optional, Dict
import re

from core.types import Page, FetchConfig


class PlaywrightFetcher:
    """使用Playwright抓取页面"""

    def __init__(self):
        self.browser: Optional[Browser] = None
        self.playwright = None

    async def start(self):
        """启动浏览器"""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=True)

    async def stop(self):
        """关闭浏览器"""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def fetch(self, url: str, config: FetchConfig) -> Page:
        """
        抓取页面
        
        Args:
            url: 目标URL
            config: 抓取配置
            
        Returns:
            Page对象
        """
        if not self.browser:
            await self.start()

        # 创建浏览器上下文，支持 viewport 配置
        context_options = {}
        if config.viewport:
            context_options["viewport"] = {
                "width": config.viewport.width,
                "height": config.viewport.height,
            }
        if config.user_agent:
            context_options["user_agent"] = config.user_agent

        context = await self.browser.new_context(**context_options)

        page = await context.new_page()
        
        # 存储已加载的图片资源
        image_resources: Dict[str, bytes] = {}
        
        # 拦截响应，捕获图片资源
        async def handle_response(response):
            """处理响应，捕获图片资源"""
            try:
                # 检查是否是图片资源
                content_type = response.headers.get('content-type', '')
                if 'image/' in content_type:
                    resource_url = response.url
                    try:
                        # 获取响应内容
                        body = await response.body()
                        if body:
                            image_resources[resource_url] = body
                    except Exception as e:
                        # 如果获取失败，忽略（可能是流式响应）
                        pass
            except Exception:
                # 忽略错误，继续处理
                pass
        
        # 监听响应事件
        page.on("response", handle_response)

        try:
            # 导航到页面（支持 goto 配置）
            goto_options = {}
            if config.goto:
                goto_options["wait_until"] = config.goto.wait_until
                goto_options["timeout"] = config.goto.timeout_ms
            else:
                goto_options["wait_until"] = config.wait_until
                goto_options["timeout"] = config.timeout_ms

            response = await page.goto(url, **goto_options)

            # 等待特定元素（wait_for 配置）
            if config.wait_for:
                for wait_config in config.wait_for:
                    try:
                        await page.wait_for_selector(
                            wait_config.selector,
                            state=wait_config.state,
                            timeout=5000,  # 默认5秒超时
                        )
                    except Exception:
                        # 等待失败不影响继续执行
                        pass

            # 获取HTML内容
            html_content = await page.content()

            status_code = response.status if response else 200

            return Page(url=url, html=html_content, status_code=status_code, resources=image_resources if image_resources else None)

        finally:
            await context.close()

