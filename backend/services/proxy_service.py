import httpx
import logging
import os
import random
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from tenacity import retry, stop_after_attempt, wait_exponential
from fake_useragent import UserAgent

logger = logging.getLogger(__name__)

class ProxyService:
    """Service for managing Webshare.io proxies"""
    
    def __init__(self):
        self.api_key = os.environ.get('WEBSHARE_API_KEY')
        self.base_url = os.environ.get('WEBSHARE_API_BASE_URL', 'https://proxy.webshare.io/api/v2')
        self.proxy_mode = os.environ.get('PROXY_MODE', 'direct')
        self.proxy_list: List[Dict[str, str]] = []
        self.last_fetch_time: Optional[datetime] = None
        self.fetch_interval = timedelta(minutes=30)
        self.current_proxy_index = 0
        
        # User-Agent rotation
        try:
            self.ua = UserAgent()
        except:
            self.ua = None
            logger.warning("Failed to initialize UserAgent, using fallbacks")
        
        if not self.api_key:
            logger.warning("WEBSHARE_API_KEY not set in environment")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def fetch_proxy_list(self) -> List[Dict[str, str]]:
        """
        Fetch proxy list from Webshare.io API
        Returns list of proxies in format: {server, username, password}
        """
        if not self.api_key:
            logger.warning("No API key, returning empty proxy list")
            return []
        
        headers = {
            "Authorization": f"Token {self.api_key}"
        }
        
        url = f"{self.base_url}/proxy/list/"
        params = {
            "mode": self.proxy_mode,
            "page_size": 25
        }
        
        async with httpx.AsyncClient(timeout=30) as client:
            try:
                response = await client.get(url, headers=headers, params=params)
                response.raise_for_status()
                
                data = response.json()
                self.proxy_list = self._parse_proxy_response(data)
                self.last_fetch_time = datetime.now()
                
                logger.info(f"✅ Fetched {len(self.proxy_list)} proxies from Webshare.io")
                return self.proxy_list
                
            except httpx.HTTPError as e:
                logger.error(f"HTTP error fetching proxies: {str(e)}")
                raise
            except Exception as e:
                logger.error(f"Unexpected error fetching proxies: {str(e)}")
                raise
    
    def _parse_proxy_response(self, response_data: Dict) -> List[Dict[str, str]]:
        """Parse Webshare.io API response and extract proxy details"""
        proxies = []
        
        for proxy in response_data.get('results', []):
            proxy_dict = {
                'server': f"http://{proxy['proxy_address']}:{proxy['port']}",
                'username': proxy.get('username', ''),
                'password': proxy.get('password', ''),
                'country': proxy.get('country_code', 'Unknown')
            }
            proxies.append(proxy_dict)
        
        return proxies
    
    async def get_proxies(self) -> List[Dict[str, str]]:
        """Get proxies, fetching fresh list if cache is stale"""
        if not self.proxy_list or self._is_cache_stale():
            await self.fetch_proxy_list()
        
        return self.proxy_list
    
    def _is_cache_stale(self) -> bool:
        """Check if cached proxy list is stale"""
        if not self.last_fetch_time:
            return True
        
        return datetime.now() - self.last_fetch_time > self.fetch_interval
    
    def get_next_proxy(self) -> Optional[Dict[str, str]]:
        """Get next proxy in rotation"""
        if not self.proxy_list:
            logger.warning("No proxies available for rotation")
            return None
        
        proxy = self.proxy_list[self.current_proxy_index % len(self.proxy_list)]
        self.current_proxy_index += 1
        
        logger.info(f"Selected proxy {self.current_proxy_index}/{len(self.proxy_list)}: {proxy['server']}")
        return proxy
    
    def get_random_proxy(self) -> Optional[Dict[str, str]]:
        """Get random proxy from list"""
        if not self.proxy_list:
            return None
        
        return random.choice(self.proxy_list)
    
    def get_random_user_agent(self) -> str:
        """Get random user agent string"""
        if self.ua:
            try:
                return self.ua.random
            except:
                pass
        
        # Fallback user agents
        fallback_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        ]
        return random.choice(fallback_agents)
    
    def get_proxy_count(self) -> int:
        """Get total number of available proxies"""
        return len(self.proxy_list)
    
    def is_enabled(self) -> bool:
        """Check if proxy service is enabled (has API key)"""
        return self.api_key is not None and len(self.api_key) > 0

# Create global proxy service instance
proxy_service = ProxyService()
