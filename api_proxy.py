from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import httpx
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import json
import hashlib
import hmac
import os
from datetime import datetime
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="XBanking API",
    description="API для XBanking NFT Marketplace",
    version="1.0.0"
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Конфигурация
API_BASE = "https://portals-market.com/api"
TELEGRAM_BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN")

# Глобальный HTTP-клиент
client: Optional[httpx.AsyncClient] = None

@app.on_event("startup")
async def startup_event():
    """Инициализация при запуске"""
    global client
    headers = {
        "Accept": "application/json",
        "Accept-Encoding": "identity",
        "Referer": "https://portals-market.com/",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    client = httpx.AsyncClient(
        base_url=API_BASE,
        headers=headers,
        timeout=30.0
    )
    logger.info("✅ API сервер запущен")

@app.on_event("shutdown")
async def shutdown_event():
    """Очистка при завершении"""
    if client:
        await client.aclose()
    logger.info("❌ API сервер остановлен")

# ==================== TELEGRAM AUTH ====================
def verify_telegram_init_data(init_data: str) -> Optional[Dict[str, Any]]:
    """Верификация данных от Telegram Web App"""
    try:
        data_pairs = init_data.split('&')
        data_dict = {}
        
        for pair in data_pairs:
            key, value = pair.split('=')
            data_dict[key] = value
        
        # Проверяем хэш
        secret_key = hmac.new(
            b"WebAppData",
            msg=TELEGRAM_BOT_TOKEN.encode(),
            digestmod=hashlib.sha256
        ).digest()
        
        received_hash = data_dict.pop('hash', '')
        
        check_string = '\n'.join(
            f"{key}={data_dict[key]}" 
            for key in sorted(data_dict.keys())
        )
        
        computed_hash = hmac.new(
            secret_key,
            msg=check_string.encode(),
            digestmod=hashlib.sha256
        ).hexdigest()
        
        if computed_hash == received_hash:
            if 'user' in data_dict:
                try:
                    data_dict['user'] = json.loads(data_dict['user'])
                except:
                    data_dict['user'] = {}
            return data_dict
        
        return None
    except Exception as e:
        logger.error(f"Ошибка верификации: {e}")
        return None

# ==================== MAIN ENDPOINTS ====================
@app.get("/", response_class=HTMLResponse)
async def get_mini_app(request: Request):
    """Главная страница мини-приложения"""
    try:
        with open("index.html", "r", encoding="utf-8") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)
    except Exception as e:
        logger.error(f"Ошибка загрузки index.html: {e}")
        return HTMLResponse(content="<h1>Mini App</h1><p>Загрузите index.html</p>")

@app.get("/api/user")
async def get_user_data(init_data: str = Query(...)):
    """Получение данных пользователя из Telegram"""
    user_data = verify_telegram_init_data(init_data)
    
    if not user_data or 'user' not in user_data:
        raise HTTPException(status_code=401, detail="Invalid Telegram data")
    
    user = user_data['user']
    
    return {
        "success": True,
        "user": {
            "id": user.get('id'),
            "username": user.get('username', f"user_{user.get('id')}"),
            "first_name": user.get('first_name', ''),
            "last_name": user.get('last_name', ''),
            "photo_url": user.get('photo_url', ''),
            "is_premium": user.get('is_premium', False)
        }
    }

# ==================== PROXY ENDPOINTS ====================
@app.get("/api/market/config")
async def get_config():
    """Получение конфигурации маркетплейса"""
    try:
        resp = await client.get("/market/config")
        return resp.json()
    except Exception as e:
        logger.error(f"Ошибка получения конфигурации: {e}")
        raise HTTPException(500, "Failed to fetch config")

@app.get("/api/market/wallets/balance")
async def get_wallet_balance():
    """Получение баланса кошелька"""
    try:
        resp = await client.get("/users/wallets/")
        return resp.json()
    except Exception as e:
        logger.error(f"Ошибка получения баланса: {e}")
        raise HTTPException(500, "Failed to fetch wallet balance")

@app.get("/api/market/nfts")
async def list_nfts(
    offset: int = Query(0, ge=0),
    limit: int = Query(30, ge=1, le=100)
):
    """Получение списка NFT с маркетплейса"""
    try:
        params = {"offset": offset, "limit": limit}
        resp = await client.get("/nfts", params=params)
        return resp.json()
    except Exception as e:
        logger.error(f"Ошибка получения NFT: {e}")
        raise HTTPException(500, "Failed to list NFTs")

@app.get("/api/market/nfts/search")
async def search_nfts(
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    filter_by_collections: Optional[str] = None,
    filter_by_backdrops: Optional[str] = None,
    filter_by_symbols: Optional[str] = None,
    filter_by_models: Optional[str] = None,
    sort_by: str = Query("price asc"),
    status: str = Query("listed")
):
    """Поиск NFT"""
    try:
        params = {
            "offset": offset,
            "limit": limit,
            "sort_by": sort_by,
            "status": status,
        }
        if filter_by_collections:
            params["filter_by_collections"] = filter_by_collections
        if filter_by_backdrops:
            params["filter_by_backdrops"] = filter_by_backdrops
        if filter_by_symbols:
            params["filter_by_symbols"] = filter_by_symbols
        if filter_by_models:
            params["filter_by_models"] = filter_by_models

        resp = await client.get("/nfts/search", params=params)
        return resp.json()
    except Exception as e:
        logger.error(f"Ошибка поиска NFT: {e}")
        raise HTTPException(500, "Failed to search NFTs")

@app.get("/api/market/collections/backdrops")
async def get_backdrops():
    """Получение списка фонов"""
    try:
        resp = await client.get("/collections/filters/backdrops")
        return resp.json()
    except Exception as e:
        logger.error(f"Ошибка получения фонов: {e}")
        raise HTTPException(500, "Failed to fetch backdrops")

@app.get("/api/market/user/nfts")
async def get_user_nfts():
    """Получение NFT пользователя (заглушка)"""
    # В реальном приложении здесь будет логика получения NFT конкретного пользователя
    try:
        resp = await client.get("/nfts")
        return resp.json()
    except Exception as e:
        logger.error(f"Ошибка получения NFT пользователя: {e}")
        raise HTTPException(500, "Failed to fetch user NFTs")

@app.get("/api/referral/{user_id}")
async def get_referral_info(user_id: int):
    """Получение реферальной информации"""
    # Заглушка - в реальности данные из базы
    return {
        "success": True,
        "referral_code": f"XBANK_{user_id}",
        "referral_link": f"https://t.me/xbanking_bot?start=ref_{user_id}",
        "total_referrals": 0,
        "referral_bonus": "0.00",
        "is_active": False,
        "message": "Реферальная система временно отключена"
    }

@app.post("/api/withdraw/request")
async def request_withdraw():
    """Запрос на вывод средств"""
    return {
        "success": False,
        "message": "Вывод средств временно отключен"
    }

# ==================== HEALTH CHECK ====================
@app.get("/health")
async def health_check():
    """Проверка работоспособности API"""
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "service": "xbanking-api",
        "version": "1.0.0"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        log_level="info"
    )