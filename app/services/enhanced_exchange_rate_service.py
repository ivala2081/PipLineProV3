"""
Enhanced Exchange Rate Service with Multiple Providers
Provides reliable exchange rate data with fallback mechanisms
"""

import requests
import yfinance as yf
import pandas as pd
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
import logging
from typing import Dict, Optional, Tuple, List
import time
import json
import threading
import warnings
import random
from collections import deque
from dataclasses import dataclass
import hashlib

# Suppress yfinance error logs
yfinance_logger = logging.getLogger('yfinance')
yfinance_logger.setLevel(logging.CRITICAL)

# Suppress yfinance warnings in terminal
warnings.filterwarnings('ignore', category=FutureWarning)

logger = logging.getLogger(__name__)

# Advanced YFinance Rate Limit Management
@dataclass
class SessionInfo:
    """YFinance session bilgileri"""
    session_id: str
    last_call_time: float
    call_count: int
    success_count: int
    fail_count: int
    is_blocked: bool
    block_until: float
    user_agent: str

class YFinanceSessionManager:
    """YFinance için multi-session ve rate limit yönetimi"""
    
    def __init__(self):
        self.sessions: Dict[str, SessionInfo] = {}
        self.session_queue = deque()
        self.lock = threading.Lock()
        self.min_call_interval = 1.5  # Başlangıç değeri
        self.max_call_interval = 10.0
        self.adaptive_delay = 2.0  # Dinamik olarak ayarlanacak
        
        # User agent rotasyonu
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 13_4) AppleWebKit/605.1.15',
        ]
        
        # Session'ları başlat
        self._initialize_sessions(5)  # 5 farklı session
        
    def _initialize_sessions(self, count: int):
        """Session'ları başlat"""
        for i in range(count):
            session_id = f"yf_session_{i}"
            user_agent = self.user_agents[i % len(self.user_agents)]
            
            session_info = SessionInfo(
                session_id=session_id,
                last_call_time=0,
                call_count=0,
                success_count=0,
                fail_count=0,
                is_blocked=False,
                block_until=0,
                user_agent=user_agent
            )
            
            self.sessions[session_id] = session_info
            self.session_queue.append(session_id)
    
    def get_next_session(self) -> Optional[SessionInfo]:
        """Kullanılabilir bir sonraki session'ı al"""
        with self.lock:
            current_time = time.time()
            attempts = 0
            max_attempts = len(self.sessions) * 2
            
            while attempts < max_attempts:
                if not self.session_queue:
                    # Tüm session'lar dolu, en eski olanı kullan
                    oldest_session = min(
                        self.sessions.values(),
                        key=lambda s: s.last_call_time
                    )
                    return oldest_session
                
                session_id = self.session_queue.popleft()
                session = self.sessions[session_id]
                
                # Bloklu mu kontrol et
                if session.is_blocked and current_time < session.block_until:
                    # Hala bloklu, sıraya geri koy
                    self.session_queue.append(session_id)
                    attempts += 1
                    continue
                
                # Blok süresi dolmuş, temizle
                if session.is_blocked and current_time >= session.block_until:
                    session.is_blocked = False
                    session.fail_count = 0
                
                # Rate limit kontrolü
                elapsed = current_time - session.last_call_time
                if elapsed < self.adaptive_delay:
                    # Çok erken, sıraya geri koy
                    self.session_queue.append(session_id)
                    attempts += 1
                    time.sleep(0.1)  # Kısa bekle
                    continue
                
                # Bu session kullanılabilir
                return session
            
            return None
    
    def mark_success(self, session: SessionInfo):
        """Başarılı çağrıyı işaretle"""
        with self.lock:
            session.last_call_time = time.time()
            session.call_count += 1
            session.success_count += 1
            
            # Başarı oranı yüksekse, delay'i azalt
            if session.success_count > 5:
                success_rate = session.success_count / session.call_count
                if success_rate > 0.9 and self.adaptive_delay > self.min_call_interval:
                    self.adaptive_delay = max(
                        self.min_call_interval,
                        self.adaptive_delay * 0.9
                    )
                    logger.debug(f"Adaptive delay reduced to {self.adaptive_delay:.2f}s")
            
            # Session'ı sıraya geri koy
            self.session_queue.append(session.session_id)
    
    def mark_failure(self, session: SessionInfo, is_rate_limit: bool = False):
        """Başarısız çağrıyı işaretle"""
        with self.lock:
            session.last_call_time = time.time()
            session.call_count += 1
            session.fail_count += 1
            
            if is_rate_limit:
                # Rate limit hatası, session'ı blokla
                session.is_blocked = True
                block_duration = min(60 * (2 ** session.fail_count), 600)  # Max 10 dakika
                session.block_until = time.time() + block_duration
                logger.warning(f"Session {session.session_id} blocked for {block_duration}s due to rate limit")
                
                # Global delay'i artır
                self.adaptive_delay = min(
                    self.max_call_interval,
                    self.adaptive_delay * 1.5
                )
                logger.debug(f"Adaptive delay increased to {self.adaptive_delay:.2f}s")
            else:
                # Normal hata, session'ı sıraya geri koy
                self.session_queue.append(session.session_id)
    
    def get_stats(self) -> Dict:
        """Session istatistiklerini al"""
        with self.lock:
            total_calls = sum(s.call_count for s in self.sessions.values())
            total_success = sum(s.success_count for s in self.sessions.values())
            total_fails = sum(s.fail_count for s in self.sessions.values())
            blocked_count = sum(1 for s in self.sessions.values() if s.is_blocked)
            
            return {
                'total_sessions': len(self.sessions),
                'blocked_sessions': blocked_count,
                'total_calls': total_calls,
                'success_count': total_success,
                'fail_count': total_fails,
                'success_rate': total_success / total_calls if total_calls > 0 else 0,
                'adaptive_delay': self.adaptive_delay
            }

# Global session manager
_session_manager = YFinanceSessionManager()

def _advanced_rate_limited_call(func):
    """Gelişmiş rate limiting decorator"""
    def wrapper(*args, **kwargs):
        max_retries = 3
        
        for attempt in range(max_retries):
            # Kullanılabilir session al
            session = _session_manager.get_next_session()
            if not session:
                logger.warning("No available yfinance sessions, waiting...")
                time.sleep(2)
                continue
            
            try:
                # Session bilgilerini kwargs'a ekle
                kwargs['_session_info'] = session
                result = func(*args, **kwargs)
                
                # Başarılı
                _session_manager.mark_success(session)
                return result
                
            except Exception as e:
                error_msg = str(e).lower()
                is_rate_limit = any(x in error_msg for x in [
                    'rate limit', '429', 'too many requests', 
                    'quota exceeded', 'throttle'
                ])
                
                _session_manager.mark_failure(session, is_rate_limit)
                
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) * 1.0
                    logger.debug(f"YFinance call failed (attempt {attempt + 1}/{max_retries}), "
                               f"retrying in {wait_time}s: {str(e)[:100]}")
                    time.sleep(wait_time)
                else:
                    logger.debug(f"YFinance call failed after {max_retries} attempts")
                    raise
        
        return None
    
    return wrapper

class ExchangeRateProvider:
    """Base class for exchange rate providers"""
    
    def __init__(self, name: str):
        self.name = name
        self.cache = {}
        self.cache_duration = 300  # 5 minutes
    
    def get_rate(self, from_currency: str, to_currency: str, target_date: date = None) -> Optional[float]:
        """Get exchange rate from provider"""
        raise NotImplementedError
    
    def is_available(self) -> bool:
        """Check if provider is available"""
        return True

class YFinanceProvider(ExchangeRateProvider):
    """Gelişmiş Yahoo Finance provider - Multi-session, rotasyon ve akıllı cache"""
    
    def __init__(self):
        super().__init__("Yahoo Finance Advanced")
        self.cache = {}
        self.cache_duration = 7200  # 2 saat agresif cache
        self.stale_cache_duration = 14400  # 4 saat stale cache (fallback için)
        
        # Ticker format alternatifleri
        self.ticker_formats = [
            "{from}{to}=X",      # Standart forex format
            "{to}=X",            # Alternatif format (sadece target currency)
            "{from}{to}",        # Format olmadan
        ]
        
        # Request queue ve priority
        self.request_queue = deque()
        self.queue_lock = threading.Lock()
        
    def _get_ticker_variations(self, from_currency: str, to_currency: str) -> List[str]:
        """Farklı ticker formatlarını döndür"""
        variations = []
        for fmt in self.ticker_formats:
            try:
                symbol = fmt.format(from_=from_currency, to=to_currency)
                variations.append(symbol)
            except:
                pass
        
        # Ters oranı da ekle (inverse)
        for fmt in self.ticker_formats:
            try:
                symbol = fmt.format(from_=to_currency, to=from_currency)
                variations.append((symbol, True))  # True = inverse flag
            except:
                pass
        
        return variations
    
    def _fetch_with_session(self, symbol: str, target_date: date = None, 
                           session_info: SessionInfo = None) -> Optional[float]:
        """Session bilgisiyle fetch yap"""
        try:
            # Session varsa custom headers kullan
            if session_info:
                # Custom session oluştur
                import requests
                session = requests.Session()
                session.headers.update({
                    'User-Agent': session_info.user_agent,
                    'Accept': 'text/html,application/json',
                    'Accept-Language': 'en-US,en;q=0.9',
                })
                
                # yfinance'e session'ı geçir (mümkünse)
                ticker = yf.Ticker(symbol, session=session)
            else:
                ticker = yf.Ticker(symbol)
            
            if target_date:
                # Historical data
                start = target_date - timedelta(days=7)
                end = target_date + timedelta(days=2)
                hist = ticker.history(start=start, end=end, interval="1d", auto_adjust=True)
                
                if hist.empty:
                    return None
                
                # En yakın tarihi bul
                available_dates = hist.index.date
                closest_date = min(available_dates, key=lambda x: abs((x - target_date).days))
                rate = float(hist.loc[hist.index.date == closest_date, 'Close'].iloc[0])
            else:
                # Current data - birden fazla yöntem dene
                try:
                    info = ticker.info
                    rate = info.get('regularMarketPrice') or info.get('previousClose') or info.get('bid')
                except:
                    rate = None
                
                if not rate:
                    # History'den al
                    hist = ticker.history(period="2d", auto_adjust=True)
                    if not hist.empty:
                        rate = float(hist['Close'].iloc[-1])
            
            # Validate
            if rate and rate > 0 and rate < 1000000:  # Makul aralık kontrolü
                return rate
            
            return None
            
        except Exception as e:
            error_msg = str(e).lower()
            if any(x in error_msg for x in ['rate limit', '429', 'too many']):
                raise  # Rate limit hatasını yukarı fırlat
            logger.debug(f"YFinance fetch error for {symbol}: {str(e)[:100]}")
            return None
    
    @_advanced_rate_limited_call
    def get_rate(self, from_currency: str, to_currency: str, target_date: date = None, 
                 _session_info: SessionInfo = None) -> Optional[float]:
        """Gelişmiş rate fetching - rotasyon ve fallback ile"""
        try:
            # Cache kontrolü - fresh cache
            cache_key = f"{from_currency}_{to_currency}_{target_date or 'current'}"
            if cache_key in self.cache:
                cached_data, timestamp = self.cache[cache_key]
                if time.time() - timestamp < self.cache_duration:
                    logger.debug(f"YFinance: Fresh cache hit for {from_currency}/{to_currency}")
                    return cached_data
            
            # Ticker varyasyonlarını dene
            variations = self._get_ticker_variations(from_currency, to_currency)
            
            for variation in variations:
                is_inverse = False
                if isinstance(variation, tuple):
                    symbol, is_inverse = variation
                else:
                    symbol = variation
                
                try:
                    logger.debug(f"YFinance: Trying {symbol} (inverse={is_inverse})")
                    rate = self._fetch_with_session(symbol, target_date, _session_info)
                    
                    if rate and rate > 0:
                        # Inverse ise tersini al
                        if is_inverse:
                            rate = 1.0 / rate
                        
                        # Cache'e kaydet
                        self.cache[cache_key] = (rate, time.time())
                        logger.info(f"YFinance: Success with {symbol} -> {from_currency}/{to_currency} = {rate}")
                        return rate
                        
                except Exception as e:
                    logger.debug(f"YFinance: Failed with {symbol}: {str(e)[:80]}")
                    continue
            
            # Stale cache kontrolü (eski ama kullanılabilir)
            if cache_key in self.cache:
                cached_data, timestamp = self.cache[cache_key]
                if time.time() - timestamp < self.stale_cache_duration:
                    logger.warning(f"YFinance: Using stale cache for {from_currency}/{to_currency}")
                    return cached_data
            
            logger.debug(f"YFinance: All variations failed for {from_currency}/{to_currency}")
            return None
                
        except Exception as e:
            logger.debug(f"YFinance: Failed for {from_currency}/{to_currency}: {str(e)[:100]}")
            return None
    
    def get_session_stats(self) -> Dict:
        """Session istatistiklerini döndür"""
        return _session_manager.get_stats()

class ExchangeRateAPIProvider(ExchangeRateProvider):
    """ExchangeRate-API.com provider (free tier) - En guvenilir API"""
    
    def __init__(self):
        super().__init__("ExchangeRate-API")
        self.base_url = "https://api.exchangerate-api.com/v4/latest"
        self.cache_duration = 600  # 10 dakika cache (daha uzun)
    
    def get_rate(self, from_currency: str, to_currency: str, target_date: date = None) -> Optional[float]:
        """Get rate from ExchangeRate-API"""
        try:
            # Bu API free tier'da historical data desteklemiyor
            # Ama current rate icin cok guvenilir
            if target_date and target_date != date.today():
                logger.debug(f"ExchangeRate-API: Historical data not supported, skipping")
                return None
            
            cache_key = f"{from_currency}_{to_currency}"
            if cache_key in self.cache:
                cached_data, timestamp = self.cache[cache_key]
                if time.time() - timestamp < self.cache_duration:
                    logger.debug(f"ExchangeRate-API: Using cached rate {cached_data}")
                    return cached_data
            
            url = f"{self.base_url}/{from_currency}"
            logger.debug(f"ExchangeRate-API: Fetching from {url}")
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            rates = data.get('rates', {})
            rate = rates.get(to_currency)
            
            if rate and rate > 0:
                self.cache[cache_key] = (rate, time.time())
                logger.info(f"ExchangeRate-API: Successfully fetched {from_currency}/{to_currency} = {rate}")
                return float(rate)
            
            logger.warning(f"ExchangeRate-API: No rate found for {to_currency}")
            return None
        except requests.exceptions.Timeout:
            logger.warning(f"ExchangeRate-API: Request timeout")
            return None
        except requests.exceptions.RequestException as e:
            logger.warning(f"ExchangeRate-API: Request failed: {e}")
            return None
        except Exception as e:
            logger.warning(f"ExchangeRate-API: Unexpected error: {e}")
            return None

class CurrencyAPIProvider(ExchangeRateProvider):
    """CurrencyAPI.com provider (free tier)"""
    
    def __init__(self):
        super().__init__("CurrencyAPI")
        self.base_url = "https://api.currencyapi.com/v3/latest"
        # Note: API key gerekli ama optional
        self.api_key = None  # API key varsa buraya ekle
    
    def get_rate(self, from_currency: str, to_currency: str, target_date: date = None) -> Optional[float]:
        """Get rate from CurrencyAPI"""
        try:
            if not self.api_key:
                logger.debug("CurrencyAPI: No API key configured, skipping")
                return None  # API key yoksa atla
            
            cache_key = f"{from_currency}_{to_currency}"
            if cache_key in self.cache:
                cached_data, timestamp = self.cache[cache_key]
                if time.time() - timestamp < self.cache_duration:
                    return cached_data
            
            params = {
                'apikey': self.api_key,
                'base_currency': from_currency,
                'currencies': to_currency
            }
            
            response = requests.get(self.base_url, params=params, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            rates = data.get('data', {})
            rate_data = rates.get(to_currency, {})
            rate = rate_data.get('value')
            
            if rate and rate > 0:
                self.cache[cache_key] = (rate, time.time())
                logger.info(f"CurrencyAPI: Successfully fetched {from_currency}/{to_currency} = {rate}")
                return float(rate)
            
            return None
        except Exception as e:
            logger.debug(f"CurrencyAPI: Failed: {e}")
            return None

class FreeCurrencyAPIProvider(ExchangeRateProvider):
    """FreeCurrencyAPI provider - API key gerektirmeyen alternatif"""
    
    def __init__(self):
        super().__init__("FreeCurrencyAPI")
        self.base_url = "https://cdn.jsdelivr.net/gh/fawazahmed0/currency-api@1/latest/currencies"
    
    def get_rate(self, from_currency: str, to_currency: str, target_date: date = None) -> Optional[float]:
        """Get rate from FreeCurrencyAPI (GitHub-hosted, no API key needed)"""
        try:
            from_curr = from_currency.lower()
            to_curr = to_currency.lower()
            
            # Historical data icin farkli URL
            if target_date:
                date_str = target_date.isoformat()
                url = f"https://cdn.jsdelivr.net/gh/fawazahmed0/currency-api@1/{date_str}/currencies/{from_curr}/{to_curr}.json"
            else:
                url = f"{self.base_url}/{from_curr}/{to_curr}.json"
            
            cache_key = f"{from_currency}_{to_currency}_{target_date or 'current'}"
            if cache_key in self.cache:
                cached_data, timestamp = self.cache[cache_key]
                if time.time() - timestamp < self.cache_duration:
                    logger.debug(f"FreeCurrencyAPI: Using cached rate {cached_data}")
                    return cached_data
            
            logger.debug(f"FreeCurrencyAPI: Fetching from {url}")
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            rate = data.get(to_curr)
            
            if rate and rate > 0:
                self.cache[cache_key] = (rate, time.time())
                logger.info(f"FreeCurrencyAPI: Successfully fetched {from_currency}/{to_currency} = {rate}")
                return float(rate)
            
            logger.warning(f"FreeCurrencyAPI: No rate found")
            return None
        except requests.exceptions.Timeout:
            logger.warning(f"FreeCurrencyAPI: Request timeout")
            return None
        except requests.exceptions.RequestException as e:
            logger.debug(f"FreeCurrencyAPI: Request failed: {e}")
            return None
        except Exception as e:
            logger.debug(f"FreeCurrencyAPI: Unexpected error: {e}")
            return None

class ECBProvider(ExchangeRateProvider):
    """European Central Bank provider - Historical data destekler"""
    
    def __init__(self):
        super().__init__("European Central Bank")
        self.base_url = "https://api.exchangerate.host/latest"
        self.cache_duration = 3600  # 1 saat cache (historical data icin)
    
    def get_rate(self, from_currency: str, to_currency: str, target_date: date = None) -> Optional[float]:
        """Get rate from ECB via exchangerate.host"""
        try:
            cache_key = f"{from_currency}_{to_currency}_{target_date or 'current'}"
            if cache_key in self.cache:
                cached_data, timestamp = self.cache[cache_key]
                if time.time() - timestamp < self.cache_duration:
                    logger.debug(f"ECB: Using cached rate {cached_data}")
                    return cached_data
            
            params = {
                'base': from_currency,
                'symbols': to_currency
            }
            
            if target_date:
                # Historical endpoint kullan
                url = f"https://api.exchangerate.host/{target_date.isoformat()}"
                logger.debug(f"ECB: Fetching historical rate from {url}")
            else:
                url = self.base_url
                logger.debug(f"ECB: Fetching current rate from {url}")
            
            response = requests.get(url, params=params, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            if data.get('success'):
                rates = data.get('rates', {})
                rate = rates.get(to_currency)
                
                if rate and rate > 0:
                    self.cache[cache_key] = (rate, time.time())
                    logger.info(f"ECB: Successfully fetched {from_currency}/{to_currency} = {rate}")
                    return float(rate)
            
            logger.warning(f"ECB: No rate found or request unsuccessful")
            return None
        except requests.exceptions.Timeout:
            logger.warning(f"ECB: Request timeout")
            return None
        except requests.exceptions.RequestException as e:
            logger.warning(f"ECB: Request failed: {e}")
            return None
        except Exception as e:
            logger.warning(f"ECB: Unexpected error: {e}")
            return None

class EnhancedExchangeRateService:
    """Enhanced exchange rate service with multiple providers and fallback"""
    
    def __init__(self):
        # Provider sirasi - YFinance artik gelismis sistemle daha guvenilir
        self.providers = [
            YFinanceProvider(),          # Gelismis rotasyon sistemiyle once dene
            ExchangeRateAPIProvider(),   # Guvenilir API
            FreeCurrencyAPIProvider(),   # API key gerektirmeyen
            ECBProvider(),               # ECB historical data
            CurrencyAPIProvider(),       # API key gerekli (optional)
        ]
        self.fallback_rates = {
            'USDTRY': 34.50,  # Guncel fallback USD/TRY (Kasim 2024)
            'TRYUSD': 1/34.50,
            'EURUSD': 1.05,
            'USDEUR': 1/1.05,
            'EURTRY': 36.23,  # Guncel EUR/TRY (Kasim 2024)
            'TRYEUR': 1/36.23
        }
        self.cache = {}
        self.cache_duration = 300  # 5 dakika global cache
        
        # Predictive pre-fetching
        self.prefetch_enabled = True
        self.prefetch_currencies = [
            ('USD', 'TRY'),
            ('EUR', 'TRY'),
            ('EUR', 'USD'),
            ('GBP', 'USD'),
        ]
        self.last_prefetch = 0
        self.prefetch_interval = 1800  # 30 dakika
    
    def _predictive_prefetch(self):
        """Sık kullanılan currency pair'leri önceden fetch et"""
        if not self.prefetch_enabled:
            return
        
        current_time = time.time()
        if current_time - self.last_prefetch < self.prefetch_interval:
            return
        
        logger.debug("Starting predictive prefetch...")
        self.last_prefetch = current_time
        
        # Arka planda prefetch yap
        def _prefetch_worker():
            for from_curr, to_curr in self.prefetch_currencies:
                try:
                    # Sadece cache'i doldur, sonucu kullanma
                    self.get_exchange_rate(from_curr, to_curr, None)
                    time.sleep(0.5)  # Rate limit için kısa bekle
                except Exception as e:
                    logger.debug(f"Prefetch failed for {from_curr}/{to_curr}: {e}")
        
        # Thread'de çalıştır
        prefetch_thread = threading.Thread(target=_prefetch_worker, daemon=True)
        prefetch_thread.start()
    
    def get_exchange_rate(self, from_currency: str, to_currency: str, 
                         target_date: date = None) -> float:
        """
        Get exchange rate with fallback mechanism
        
        Args:
            from_currency: Source currency (e.g., 'USD')
            to_currency: Target currency (e.g., 'TRY')
            target_date: Date for historical rates (None for current)
            
        Returns:
            Exchange rate as float
        """
        # Normalize currency codes
        from_currency = from_currency.upper()
        to_currency = to_currency.upper()
        
        # Same currency
        if from_currency == to_currency:
            return 1.0
        
        # Predictive prefetch (sadece current rate için)
        if not target_date:
            self._predictive_prefetch()
        
        # Check cache first
        cache_key = f"{from_currency}_{to_currency}_{target_date or 'current'}"
        if cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if time.time() - timestamp < self.cache_duration:
                logger.debug(f"Using cached rate for {from_currency}/{to_currency}: {cached_data}")
                return cached_data
        
        # Her provider'i sirayla dene
        for provider in self.providers:
            try:
                logger.debug(f"Trying provider: {provider.name}")
                rate = provider.get_rate(from_currency, to_currency, target_date)
                if rate and rate > 0:
                    self.cache[cache_key] = (rate, time.time())
                    logger.info(f"Successfully got rate from {provider.name}: {from_currency}/{to_currency} = {rate}")
                    return rate
            except Exception as e:
                logger.debug(f"Provider {provider.name} failed: {e}")
                continue
        
        # Ters oran dene (inverse rate)
        logger.debug(f"Trying inverse rates for {from_currency}/{to_currency}")
        try:
            for provider in self.providers:
                try:
                    inverse_rate = provider.get_rate(to_currency, from_currency, target_date)
                    if inverse_rate and inverse_rate > 0:
                        rate = 1.0 / inverse_rate
                        self.cache[cache_key] = (rate, time.time())
                        logger.info(f"Got inverse rate from {provider.name}: {from_currency}/{to_currency} = {rate}")
                        return rate
                except Exception:
                    continue
        except Exception:
            pass
        
        # Fallback rate kullan
        fallback_key = f"{from_currency}{to_currency}"
        if fallback_key in self.fallback_rates:
            rate = self.fallback_rates[fallback_key]
            logger.warning(f"Using fallback rate for {from_currency}/{to_currency}: {rate}")
            return rate
        
        # Son care: default USD/TRY rate
        logger.warning(f"No rate found for {from_currency}/{to_currency}, using default USD/TRY rate")
        return 34.50
    
    def get_historical_rate(self, target_date: date, from_currency: str = "USD", 
                           to_currency: str = "TRY") -> float:
        """Get historical exchange rate for a specific date"""
        return self.get_exchange_rate(from_currency, to_currency, target_date)
    
    def get_current_rate(self, from_currency: str = "USD", to_currency: str = "TRY") -> float:
        """Get current exchange rate"""
        return self.get_exchange_rate(from_currency, to_currency)
    
    def get_monthly_average_rate(self, year: int, month: int, 
                                from_currency: str = "USD", to_currency: str = "TRY") -> float:
        """Get average rate for a specific month"""
        try:
            # Get first and last day of month
            start_date = date(year, month, 1)
            if month == 12:
                end_date = date(year + 1, 1, 1) - timedelta(days=1)
            else:
                end_date = date(year, month + 1, 1) - timedelta(days=1)
            
            # Collect rates for the month (sample every few days to avoid too many requests)
            rates = []
            current_date = start_date
            while current_date <= end_date:
                try:
                    rate = self.get_exchange_rate(from_currency, to_currency, current_date)
                    if rate and rate > 0:
                        rates.append(rate)
                except Exception as e:
                    logger.debug(f"Failed to get rate for {current_date}: {e}")
                
                # Sample every 5 days to reduce API calls and prevent spam
                current_date += timedelta(days=5)
            
            if rates:
                average_rate = sum(rates) / len(rates)
                logger.info(f"Monthly average rate for {year}-{month:02d}: {average_rate} (from {len(rates)} samples)")
                return average_rate
            else:
                # Fallback to current rate
                return self.get_current_rate(from_currency, to_currency)
                
        except Exception as e:
            logger.error(f"Error calculating monthly average rate: {e}")
            return self.get_current_rate(from_currency, to_currency)
    
    def clear_cache(self):
        """Clear the cache"""
        self.cache.clear()
        for provider in self.providers:
            provider.cache.clear()
        logger.info("Exchange rate cache cleared")
    
    def get_provider_status(self) -> Dict[str, bool]:
        """Get status of all providers"""
        status = {}
        for provider in self.providers:
            try:
                # Test with a simple USD/EUR rate
                test_rate = provider.get_rate("USD", "EUR")
                status[provider.name] = test_rate is not None
            except Exception:
                status[provider.name] = False
        
        # YFinance session stats ekle
        for provider in self.providers:
            if isinstance(provider, YFinanceProvider):
                try:
                    session_stats = provider.get_session_stats()
                    status['yfinance_sessions'] = session_stats
                except:
                    pass
        
        return status
    
    def get_detailed_stats(self) -> Dict:
        """Detaylı istatistikleri döndür"""
        stats = {
            'providers': {},
            'cache_size': len(self.cache),
            'yfinance_sessions': None
        }
        
        # Her provider için durum
        for provider in self.providers:
            provider_stats = {
                'name': provider.name,
                'cache_size': len(provider.cache) if hasattr(provider, 'cache') else 0,
                'available': True
            }
            
            # YFinance için özel stats
            if isinstance(provider, YFinanceProvider):
                try:
                    provider_stats['session_stats'] = provider.get_session_stats()
                except:
                    pass
            
            stats['providers'][provider.name] = provider_stats
        
        return stats
    
    # Legacy API compatibility methods
    def get_current_rate_from_api(self, currency='USD'):
        """
        Legacy compatibility: Get current rate from API (returns dict format)
        
        Args:
            currency: Currency code (USD, EUR)
            
        Returns:
            Dict with rate data or None if failed
        """
        try:
            to_currency = 'TRY'  # Legacy service always converts to TRY
            rate = self.get_current_rate(currency, to_currency)
            
            if rate and rate > 0:
                return {
                    'currency': currency,
                    'rate': rate,
                    'bid_price': None,  # Enhanced service doesn't provide bid/ask
                    'ask_price': None,
                    'volume': None,
                    'source': 'enhanced_multi_provider',
                    'timestamp': datetime.now(timezone.utc) if hasattr(datetime, 'timezone') else datetime.utcnow()
                }
            return None
        except Exception as e:
            logger.error(f"Error in get_current_rate_from_api: {e}")
            return None
    
    def get_or_fetch_rate(self, currency: str, date_obj) -> Optional[Decimal]:
        """
        Legacy compatibility: Get exchange rate for a specific currency and date
        
        Args:
            currency: Currency code (USD, EUR)
            date_obj: Date for the rate (date object)
            
        Returns:
            Decimal: Exchange rate or None if not available
        """
        try:
            # Convert date_obj to date if it's a datetime
            if isinstance(date_obj, datetime):
                target_date = date_obj.date()
            elif isinstance(date_obj, date):
                target_date = date_obj
            else:
                target_date = date.today()
            
            to_currency = 'TRY'  # Legacy service always converts to TRY
            rate = self.get_exchange_rate(currency, to_currency, target_date)
            
            if rate and rate > 0:
                return Decimal(str(rate))
            return None
        except Exception as e:
            logger.error(f"Error in get_or_fetch_rate: {e}")
            return None
    
    def update_exchange_rate(self, app=None, currency='USD') -> bool:
        """
        Legacy compatibility: Update exchange rate in database
        
        Args:
            app: Flask app instance for context (optional)
            currency: Currency to update (USD, EUR)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            from app.models.exchange_rate import ExchangeRate
            
            # Get current rate
            rate_data = self.get_current_rate_from_api(currency)
            if not rate_data:
                logger.error(f"Failed to get {currency} exchange rate")
                return False
            
            # Database operations need app context
            def _update_in_context():
                try:
                    currency_pair = f"{currency}TRY"
                    new_rate = ExchangeRate.create_new_rate(
                        rate=rate_data['rate'],
                        currency_pair=currency_pair,
                        source=rate_data['source'],
                        bid_price=rate_data.get('bid_price'),
                        ask_price=rate_data.get('ask_price'),
                        volume=rate_data.get('volume')
                    )
                    logger.debug(f"Exchange rate updated successfully: {new_rate.rate} TRY/{currency}")
                    return True
                except Exception as e:
                    logger.error(f"Error updating exchange rate in database: {e}")
                    return False
            
            # Try to use provided app context or current context
            if app:
                with app.app_context():
                    return _update_in_context()
            else:
                try:
                    from flask import current_app
                    with current_app.app_context():
                        return _update_in_context()
                except RuntimeError:
                    logger.warning("No Flask app context available for database operations")
                    return False
            
        except Exception as e:
            logger.error(f"Error updating {currency} exchange rate: {e}")
            return False
    
    def force_update(self) -> bool:
        """
        Legacy compatibility: Force update of exchange rates
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Clear cache and update both USD and EUR
            self.clear_cache()
            usd_success = self.update_exchange_rate(currency='USD')
            eur_success = self.update_exchange_rate(currency='EUR')
            return usd_success or eur_success  # At least one should succeed
        except Exception as e:
            logger.error(f"Error in force_update: {e}")
            return False
    
    def start_auto_update(self, app=None):
        """
        Legacy compatibility: Start automatic rate updates every 15 minutes
        
        Args:
            app: Flask app instance for context
        """
        if hasattr(self, 'is_running') and self.is_running:
            logger.warning("Exchange rate auto-update is already running")
            return
        
        self.is_running = True
        self.app = app
        self.update_interval = 15 * 60  # 15 minutes
        self.update_thread = threading.Thread(target=self._auto_update_loop, daemon=True)
        self.update_thread.start()
        logger.info("Started automatic exchange rate updates (every 15 minutes) using enhanced service")
    
    def stop_auto_update(self):
        """Legacy compatibility: Stop automatic rate updates"""
        self.is_running = False
        if hasattr(self, 'update_thread') and self.update_thread:
            self.update_thread.join(timeout=5)
        logger.info("Stopped automatic exchange rate updates")
    
    def _auto_update_loop(self):
        """Internal loop for automatic updates"""
        while self.is_running:
            try:
                # Update USD and EUR rates
                usd_success = self.update_exchange_rate(self.app, 'USD')
                eur_success = self.update_exchange_rate(self.app, 'EUR')
                
                if usd_success and eur_success:
                    logger.debug("Successfully updated both USD and EUR exchange rates")
                elif usd_success or eur_success:
                    logger.warning("Partially updated exchange rates")
                else:
                    logger.warning("Failed to update exchange rates")
                
                # Wait for next update interval
                time.sleep(self.update_interval)
            except Exception as e:
                logger.error(f"Error in auto-update loop: {e}")
                time.sleep(60)  # Wait 1 minute before retrying on error

# Global instance
enhanced_exchange_service = EnhancedExchangeRateService()

# Backward compatibility
def get_historical_rate(target_date: date, symbol: str = "USDTRY=X") -> float:
    """Backward compatibility function"""
    if symbol == "USDTRY=X":
        return enhanced_exchange_service.get_historical_rate(target_date, "USD", "TRY")
    return 48.0

def get_current_rate(symbol: str = "USDTRY=X") -> float:
    """Backward compatibility function"""
    if symbol == "USDTRY=X":
        return enhanced_exchange_service.get_current_rate("USD", "TRY")
    return 48.0
