# MCP BSL Language Server

MCP-сервер для статического анализа и форматирования кода 1С:Предприятие с использованием **BSL Language Server 0.29.0**.

---

## 📋 Предварительные требования

- **JDK 17+** — для запуска JAR-файла BSL Language Server
- **Python 3.10+** — для работы MCP-сервера
- **[BSL Language Server 0.29.0](https://github.com/1c-syntax/bsl-language-server/releases)** — JAR-файл (`bsl-language-server-0.29.0-exec.jar`)

---

## 🚀 Установка

### Вариант 1: Изолированное окружение (рекомендуется)

```cmd
install.bat
```

Скрипт создаёт папку `venv` с изолированным Python и устанавливает все зависимости.

> ⚠️ Папка `venv` привязана к путям вашей системы — не копируйте её на другие ПК, просто запустите `install.bat` заново.

### Вариант 2: Системное окружение

```powershell
pip install -r requirements.txt
pip install -e .
```

---

## ⚙️ Настройка MCP-клиента

Пример конфигурации для Kiro (`~/.kiro/settings/mcp.json`) и Cursor (`~/.cursor/mcp.json`):

```json
{
  "mcpServers": {
    "bsl-mcp": {
      "command": "D:\\путь\\к\\проекту\\venv\\Scripts\\python.exe",
      "args": ["-m", "mcp_bsl.server"],
      "env": {
        "BSL_JAR": "D:\\путь\\к\\проекту\\bsl-language-server-0.29.0-exec.jar",
        "BSL_MEMORY_MB": "4096",
        "BSL_CONFIG": "D:\\путь\\к\\проекту\\.bsl-language-server.json",
        "BSL_LOG_LEVEL": "ERROR"
      }
    }
  }
}
```

Замените `D:\\путь\\к\\проекту` на реальный путь к папке проекта. В JSON-файлах используйте двойные обратные слеши `\\`.

---

## 🛠️ Доступные инструменты

| Инструмент | Описание |
|---|---|
| `bsl_analyze` | Статический анализ `.bsl`/`.os` файлов — возвращает ошибки, предупреждения и подсказки |
| `bsl_format` | Форматирование BSL-файлов согласно настроенным правилам стиля |

Оба инструмента принимают параметр `srcDir` — путь к файлу или директории с BSL-файлами.

---

## 🔧 Переменные окружения

| Переменная | По умолчанию | Описание |
|---|---|---|
| `BSL_JAR` | *(обязательно)* | Путь к JAR-файлу BSL Language Server |
| `BSL_MEMORY_MB` | `4096` | Размер кучи JVM в МБ |
| `BSL_CONFIG` | *(не задан)* | Путь к `.bsl-language-server.json` |
| `BSL_LOG_LEVEL` | `WARNING` | Уровень логирования (`DEBUG`, `WARNING`, `ERROR`) |

---

## 📁 Структура проекта

```
mcp-bsl-ls/
├── src/
│   └── mcp_bsl/
│       ├── server.py              # MCP-сервер, регистрация инструментов
│       ├── bsl_runner.py          # Запуск JAR, парсинг вывода
│       └── config.py              # Загрузка конфигурации из env
├── tests/
│   └── test_bsl_runner.py         # Unit, property-based и интеграционные тесты
├── rules/                         # Инструкции для AI-агента
├── .bsl-language-server.json      # Пример конфигурации BSL LS
├── mcp.json                       # Пример конфигурации MCP-клиента
├── pyproject.toml                 # Метаданные проекта
├── requirements.txt               # Зависимости Python
└── install.bat                    # Скрипт установки для Windows
```

---

## 🧪 Тесты

```powershell
# Unit и property-based тесты
venv\Scripts\python.exe -m pytest tests/test_bsl_runner.py -v

# Только интеграционные тесты (требуется реальный JAR)
venv\Scripts\python.exe -m pytest tests/test_bsl_runner.py -m integration -v
```

---

## 📝 Совместимость

Сервер поддерживает **BSL Language Server 0.29.0**. Версия 0.29.0 изменила синтаксис CLI:
- Подкоманды `analyze` и `format` теперь передаются без префикса `--`
- Параметры переименованы: `--srcDir` → `-s`, `--reporter` → `-r`, `--src` → `-s`
- JSON-отчёт записывается в явно указанную директорию через флаг `-o`

---

## 🔗 Ссылки

- [BSL Language Server — документация](https://1c-syntax.github.io/bsl-language-server/)
- [Оригинальный проект phsin/mcp-bsl-ls](https://github.com/phsin/mcp-bsl-ls)
