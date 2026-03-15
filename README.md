# CIAN Pages Feed

GitHub Pages проект, который публикует интерактивную страницу с объявлениями и фото.

## Как работает
- Workflow `Update and Deploy Pages` запускается вручную или каждые 6 часов.
- Скрипт `scripts/update.py` парсит страницу поиска и сохраняет `docs/data.json`.
- `docs/index.html` рендерит карточки объявлений из JSON.
- После обновления данные автоматически деплоятся в GitHub Pages.

## Ручной запуск
Actions → **Update and Deploy Pages** → Run workflow
- `search_url`: ссылка поиска (можно менять)
- `limit`: кол-во объявлений
