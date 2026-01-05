"""Playwright页面抓取器"""
from playwright.async_api import async_playwright, Browser, Page as PlaywrightPage
from typing import Optional

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

        context = await self.browser.new_context()
        if config.user_agent:
            await context.set_extra_http_headers(
                {"User-Agent": config.user_agent}
            )

        page = await context.new_page()

        try:
            # 导航到页面
            response = await page.goto(
                url,
                wait_until=config.wait_until,
                timeout=config.timeout_ms,
            )

            # 获取HTML内容
            html = await page.content()

            status_code = response.status if response else 200

            return Page(url=url, html=html, status_code=status_code)

        finally:
            await context.close()

