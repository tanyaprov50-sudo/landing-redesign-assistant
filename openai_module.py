"""
Модуль для работы с OpenAI API.
Отправляет текст лендинга и получает рекомендации по улучшению.
"""

import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

# Загружаем переменные окружения из директории скрипта
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

logger = logging.getLogger(__name__)

# Системный промпт для модели
SYSTEM_PROMPT = """Ты опытный UX/UI дизайнер и специалист по лендингам. 
Проанализируй текст лендинга и предложи 5 конкретных рекомендаций по улучшению:
- структуры страницы
- заголовков
- призывов к действию (CTA)
- визуальной иерархии
- доверия пользователя

Каждая рекомендация должна быть короткой и конкретной."""


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
def get_redesign_tips(text: str) -> list[str]:
    """
    Получает рекомендации по улучшению лендинга от OpenAI.
    
    Args:
        text: Текст лендинга для анализа
        
    Returns:
        Список из 5 рекомендаций
        
    Raises:
        ValueError: Если API ключ не найден
        Exception: При ошибке OpenAI API
    """
    logger.info("Отправка запроса в OpenAI API")
    
    # Проверяем наличие API ключа
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY не найден. "
            "Создайте файл .env и добавьте ваш API ключ."
        )
    
    # Отладка: показываем длину ключа
    logger.info(f"Длина API ключа: {len(api_key)} символов")
    
    try:
        # Инициализируем клиент OpenAI через ProxyAPI
        client = OpenAI(
            api_key=api_key,
            base_url="https://api.proxyapi.ru/openai/v1"
        )
        
        # Отправляем запрос
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Текст лендинга:\n\n{text}"}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        
        # Извлекаем ответ
        content = response.choices[0].message.content
        
        # Парсим рекомендации
        tips = parse_tips(content)
        
        logger.info(f"Получено {len(tips)} рекомендаций")
        return tips
        
    except Exception as e:
        logger.error(f"Ошибка OpenAI API: {e}")
        raise


def parse_tips(content: str) -> list[str]:
    """
    Парсит рекомендации из ответа модели.
    
    Args:
        content: Текст ответа от модели
        
    Returns:
        Список рекомендаций
    """
    lines = content.strip().split('\n')
    tips = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Удаляем нумерацию в начале строки
        if line[0].isdigit() and ('. ' in line or ') ' in line):
            # Находим первую точку или скобку после цифры
            for sep in ['. ', ') ']:
                if sep in line:
                    line = line.split(sep, 1)[1]
                    break
        
        # Удаляем маркеры списка
        if line.startswith(('- ', '* ', '• ')):
            line = line[2:]
        
        if line:
            tips.append(line)
    
    # Возвращаем первые 5 рекомендаций
    return tips[:5] if tips else ["Не удалось получить рекомендации"]
