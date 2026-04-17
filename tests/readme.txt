Папка tests/ содержит один файл — test_bsl_runner.py с 23 тестами трёх типов.

Что там есть
1. Тесты верификации исправления (5 штук, префикс test_bug_condition_) Проверяют, что CLI-команды генерируются правильно для BSL LS 0.29.0 — без --analyze, с -s, -r, -o и т.д. Не запускают JAR, работают мгновенно.

2. Property-based тесты сохранения поведения (15 штук, префикс test_preservation_) Проверяют, что парсинг JSON-диагностик, фильтрация шума stderr, безопасное окружение и подсчёт файлов работают корректно. Используют hypothesis для генерации случайных входных данных. Не запускают JAR.

3. Интеграционные тесты (3 штуки, маркер @pytest.mark.integration) Запускают реальный JAR 0.29.0 против папки ЗаказКлиента. Требуют наличия JAR и BSL-файлов.

КАК ЗАПУСКАТЬ
# Все тесты (unit + property-based + интеграционные)
venv\Scripts\python.exe -m pytest tests/test_bsl_runner.py -v

# Только быстрые тесты (без JAR)
venv\Scripts\python.exe -m pytest tests/test_bsl_runner.py -v -m "not integration"

# Только интеграционные (нужен JAR)
venv\Scripts\python.exe -m pytest tests/test_bsl_runner.py -v -m integration

# Только тесты CLI-синтаксиса
venv\Scripts\python.exe -m pytest tests/test_bsl_runner.py -v -k "bug_condition"

# Только property-based тесты
venv\Scripts\python.exe -m pytest tests/test_bsl_runner.py -v -k "preservation"

Когда это полезно
После обновления JAR — запусти интеграционные тесты, чтобы убедиться, что новая версия совместима
После изменений в bsl_runner.py — запусти все тесты, чтобы не сломать существующее поведение
При переносе на другую машину — запусти not integration для быстрой проверки без JAR
Пути к JAR и BSL-файлам в тестах захардкожены под D:\NewMCP\bsl_mcp\... — если проект лежит в другом месте, нужно поправить константы JAR_PATH, CONFIG_FILE, SOURCE_PATH в начале файла.