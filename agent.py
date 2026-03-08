"""
Главный модуль Landing Redesign Assistant.
Загружает HTML лендинга, извлекает текст и получает рекомендации от OpenAI.
"""

import logging
import sys
from datetime import datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential

from openai_module import get_redesign_tips

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
def fetch_html(url: str) -> str:
    """
    Загружает HTML страницы по URL.
    
    Args:
        url: URL лендинга
        
    Returns:
        HTML содержимое страницы
        
    Raises:
        requests.RequestException: При ошибке загрузки
    """
    logger.info(f"Загрузка страницы: {url}")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    
    logger.info("Страница успешно загружена")
    return response.text


def extract_text(html: str) -> str:
    """
    Извлекает текст из HTML, удаляя ненужные теги.
    
    Args:
        html: HTML содержимое
        
    Returns:
        Очищенный текст (до 8000 символов)
    """
    logger.info("Извлечение текста из HTML")
    
    soup = BeautifulSoup(html, 'html.parser')
    
    # Удаляем ненужные теги
    for tag in soup(['script', 'style', 'nav', 'footer']):
        tag.decompose()
    
    # Извлекаем текст
    text = soup.get_text(separator=' ', strip=True)
    
    # Очищаем множественные пробелы
    text = ' '.join(text.split())
    
    # Обрезаем до 8000 символов
    text = text[:8000]
    
    logger.info(f"Извлечено {len(text)} символов текста")
    return text


def save_report(url: str, tips: list[str]) -> str:
    """
    Сохраняет отчёт с рекомендациями в файл.
    
    Args:
        url: URL проанализированного лендинга
        tips: Список рекомендаций
        
    Returns:
        Путь к сохранённому файлу
    """
    # Создаём директорию для отчётов
    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)
    
    # Генерируем имя файла
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"redesign_report_{timestamp}.txt"
    filepath = reports_dir / filename
    
    # Формируем содержимое отчёта
    report_content = f"""
{'=' * 80}
ОТЧЁТ ПО УЛУЧШЕНИЮ ЛЕНДИНГА
{'=' * 80}

URL: {url}
Дата анализа: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

{'=' * 80}
РЕКОМЕНДАЦИИ ПО УЛУЧШЕНИЮ:
{'=' * 80}

"""
    
    for i, tip in enumerate(tips, 1):
        report_content += f"{i}. {tip}\n\n"
    
    report_content += f"{'=' * 80}\n"
    
    # Сохраняем файл
    filepath.write_text(report_content, encoding='utf-8')
    logger.info(f"Отчёт сохранён: {filepath}")
    
    return str(filepath)


def main() -> None:
    """Основная функция программы."""
    print("=" * 80)
    print("LANDING REDESIGN ASSISTANT")
    print("=" * 80)
    print()
    
    try:
        # Получаем URL от пользователя
        url = input("Введите URL лендинга: ").strip()
        
        if not url:
            logger.error("URL не может быть пустым")
            sys.exit(1)
        
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        print()
        
        # Загружаем HTML
        html = fetch_html(url)
        
        # Извлекаем текст
        text = extract_text(html)
        
        # Получаем рекомендации от OpenAI
        tips = get_redesign_tips(text)
        
        # Выводим результаты
        print()
        print("=" * 80)
        print("РЕКОМЕНДАЦИИ ПО УЛУЧШЕНИЮ ЛЕНДИНГА:")
        print("=" * 80)
        print()
        
        for i, tip in enumerate(tips, 1):
            print(f"{i}. {tip}")
            print()
        
        # Сохраняем отчёт
        report_path = save_report(url, tips)
        
        print("=" * 80)
        print(f"✓ Отчёт сохранён: {report_path}")
        print("=" * 80)
        
    except requests.RequestException as e:
        logger.error(f"Ошибка при загрузке страницы: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Непредвиденная ошибка: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
