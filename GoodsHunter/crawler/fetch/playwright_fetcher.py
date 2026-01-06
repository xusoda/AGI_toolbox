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
                        # 使用配置的超时时间，如果没有则使用默认值10秒
                        timeout = (wait_config.timeout_ms / 1000) if wait_config.timeout_ms else 10000
                        await page.wait_for_selector(
                            wait_config.selector,
                            state=wait_config.state,
                            timeout=timeout,
                        )
                        print(f"[PlaywrightFetcher] 等待元素成功: {wait_config.selector} (state: {wait_config.state})")
                    except Exception as e:
                        # 等待失败不影响继续执行，但打印警告
                        print(f"[PlaywrightFetcher] 等待元素超时或失败: {wait_config.selector} (state: {wait_config.state}), 错误: {str(e)}")
                        pass

            # 处理懒加载图片：强制加载 + 滚动 + 等待网络空闲
            print(f"[PlaywrightFetcher] 开始处理懒加载图片...")
            
            # 1. 强制加载懒加载图片（将data-src等属性转换为src）
            try:
                await page.evaluate("""
                    () => {
                        // 处理所有可能的懒加载属性
                        const lazyAttrs = ['data-src', 'data-lazy-src', 'data-original', 'data-lazy', 'data-srcset'];
                        let loadedCount = 0;
                        
                        document.querySelectorAll('img').forEach(img => {
                            for (const attr of lazyAttrs) {
                                if (img.hasAttribute(attr)) {
                                    const srcValue = img.getAttribute(attr);
                                    if (srcValue) {
                                        img.src = srcValue;
                                        loadedCount++;
                                        break;
                                    }
                                }
                            }
                        });
                        
                        // 处理背景图片的懒加载
                        document.querySelectorAll('[data-bg], [data-background], [data-lazy-bg]').forEach(el => {
                            const bgAttr = el.getAttribute('data-bg') || 
                                          el.getAttribute('data-background') || 
                                          el.getAttribute('data-lazy-bg');
                            if (bgAttr) {
                                el.style.backgroundImage = `url(${bgAttr})`;
                                loadedCount++;
                            }
                        });
                        
                        return loadedCount;
                    }
                """)
                print(f"[PlaywrightFetcher] 强制加载懒加载图片完成")
            except Exception as e:
                print(f"[PlaywrightFetcher] 强制加载懒加载图片时出错: {str(e)}")
            
            # 2. 滚动页面触发懒加载（分步滚动，确保所有图片都有机会加载）
            try:
                await page.evaluate("""
                    async () => {
                        const scrollStep = 500;
                        const scrollDelay = 200;
                        let lastHeight = 0;
                        let currentHeight = document.body.scrollHeight;
                        let scrollPosition = 0;
                        let unchangedCount = 0;
                        
                        // 分步向下滚动
                        while (scrollPosition < currentHeight && unchangedCount < 3) {
                            scrollPosition += scrollStep;
                            window.scrollTo(0, Math.min(scrollPosition, currentHeight));
                            await new Promise(resolve => setTimeout(resolve, scrollDelay));
                            
                            const newHeight = document.body.scrollHeight;
                            if (newHeight === currentHeight) {
                                unchangedCount++;
                            } else {
                                unchangedCount = 0;
                                currentHeight = newHeight;
                            }
                        }
                        
                        // 滚动到底部
                        window.scrollTo(0, document.body.scrollHeight);
                        await new Promise(resolve => setTimeout(resolve, scrollDelay));
                        
                        // 滚动回顶部
                        window.scrollTo(0, 0);
                        await new Promise(resolve => setTimeout(resolve, scrollDelay));
                    }
                """)
                print(f"[PlaywrightFetcher] 页面滚动完成")
            except Exception as e:
                print(f"[PlaywrightFetcher] 页面滚动时出错: {str(e)}")
            
            # 3. 等待网络空闲，确保所有图片加载完成
            try:
                await page.wait_for_load_state("networkidle", timeout=10000)
                print(f"[PlaywrightFetcher] 网络空闲，图片加载完成")
            except Exception as e:
                print(f"[PlaywrightFetcher] 等待网络空闲超时: {str(e)}，继续执行")
            
            # 获取HTML内容
            html_content = await page.content()

            status_code = response.status if response else 200

            return Page(url=url, html=html_content, status_code=status_code, resources=image_resources if image_resources else None)

        finally:
            await context.close()

