# Технологический стек

## Язык и среда выполнения
- **Python 3.10+** — реализация сервера
- **Java 17+** (JDK) — необходим для запуска JAR-файла BSL Language Server

## Основные зависимости
- **`mcp>=1.0.0`** — SDK Model Context Protocol (серверный фреймворк, stdio-транспорт)
- **`pydantic>=2.0.0`** — валидация конфигурации через модель `BSLConfig`
- **`setuptools>=61.0`** + `wheel` — сборочный бэкенд

## Внешний инструмент
- **BSL Language Server** (`bsl-language-server-*.jar`) — движок статического анализа и форматирования BSL-кода 1С. Запускается как подпроцесс через `java -jar`.

## Структура пакета
- Имя пакета: `mcp-bsl` (PyPI), модуль: `mcp_bsl`
- Точка входа: `mcp-bsl-server` → `mcp_bsl.server:main`
- Устанавливается в режиме редактирования: `pip install -e .`

## Конфигурация (переменные окружения)

| Переменная | По умолчанию | Описание |
|---|---|---|
| `BSL_JAR` | `D:\NewMCP\mcp-bsl-ls\bsl-language-server-0.29.0-exec.jar` | Путь к JAR-файлу BSL LS |
| `BSL_MEMORY_MB` | `4096` | Размер кучи JVM в МБ |
| `BSL_CONFIG` | *(не задан)* | Путь к `.bsl-language-server.json` |
| `BSL_LOG_LEVEL` | `WARNING` | Уровень логирования Python (`DEBUG`, `WARNING`, `ERROR`) |

## Конфигурация BSL Language Server (`.bsl-language-server.json`)
- Язык: `RU`
- Диагностики запускаются: `onSave`
- Форматтер: отступ 2 пробела, без табуляции
- Примечательные правила: `SillyAssignment` → warning, `UsingHardcodeSecretInformation` → error

## Основные команды

### Установка (рекомендуется — изолированное окружение)
```cmd
install.bat
```

### Установка (вручную)
```powershell
pip install -r requirements.txt
pip install -e .
```

### Запуск MCP-сервера напрямую
```powershell
python -m mcp_bsl.server
```

### Запуск через точку входа (после установки)
```powershell
mcp-bsl-server
```

### Конфигурация MCP-клиента (Kiro `~/.kiro/settings/mcp.json`)
```json
{
  "mcpServers": {
    "bsl-mcp": {
      "command": "D:\\NewMCP\\mcp-bsl-ls\\venv\\Scripts\\python.exe",
      "args": ["-m", "mcp_bsl.server"],
      "env": {
        "BSL_JAR": "D:\\NewMCP\\mcp-bsl-ls\\bsl-language-server-0.29.0-exec.jar",
        "BSL_MEMORY_MB": "4096",
        "BSL_CONFIG": "D:\\NewMCP\\mcp-bsl-ls\\.bsl-language-server.json",
        "BSL_LOG_LEVEL": "ERROR"
      }
    }
  }
}
```

## Примечания
- В JSON-файлах всегда используй двойные обратные слеши `\\` в путях на Windows
- Папка `venv` привязана к конкретной машине — не копируй между ПК, запусти `install.bat` заново
- При уровне логирования `DEBUG` файл отчёта `bsl-json.json` сохраняется после анализа для проверки
