# Bugfix Requirements Document

## Introduction

MCP-сервер для BSL Language Server перестал работать после обновления JAR-файла до версии 0.29.0. Версия 0.29.0 изменила синтаксис CLI: подкоманды `analyze` и `format` теперь передаются без префикса `--`, параметры источника и вывода переименованы, а JSON-отчёт записывается в явно указанную директорию через флаг `-o`. Кроме того, JVM версии 0.29.0 выводит в stderr предупреждения (`WARNING:` от `sun.misc.Unsafe` и т.д.), которые текущий фильтр шума не распознаёт и ошибочно трактует как сбой выполнения. В совокупности эти изменения делают оба инструмента — `bsl_analyze` и `bsl_format` — полностью неработоспособными.

## Bug Analysis

### Current Behavior (Defect)

1.1 WHEN вызывается `bsl_analyze` с любым корректным путём к исходникам THEN система запускает JAR с флагом `--analyze` (вместо подкоманды `analyze`), что приводит к ошибке «Unknown option: '--analyze'» и завершению с ненулевым кодом возврата

1.2 WHEN вызывается `bsl_analyze` THEN система передаёт параметр `--srcDir` (вместо `-s`) и `--reporter json` (вместо `-r json`), что дополнительно нарушает синтаксис команды версии 0.29.0

1.3 WHEN анализ завершается THEN система ищет файл `bsl-json.json` в рабочей директории (`work_dir / "bsl-json.json"`), тогда как версия 0.29.0 записывает его в директорию, указанную через флаг `-o`, которая в текущем коде не передаётся

1.4 WHEN вызывается `bsl_format` с любым корректным путём THEN система запускает JAR с флагом `--format` (вместо подкоманды `format`) и параметром `--src` (вместо `-s`), что приводит к ошибке синтаксиса и завершению с ненулевым кодом возврата

1.5 WHEN BSL Language Server 0.29.0 выводит в stderr строки вида `WARNING: A terminally deprecated method in java.lang.System has been called` или аналогичные предупреждения JVM THEN система считает их реальными ошибками выполнения и возвращает `BSLResult(success=False)` вместо продолжения обработки

1.6 WHEN запускается `bsl_analyze` THEN система устанавливает `cwd=work_dir` (директория с исходниками), что в версии 0.29.0 не требуется и может конфликтовать с путями, передаваемыми через параметры командной строки

### Expected Behavior (Correct)

2.1 WHEN вызывается `bsl_analyze` THEN система SHALL запускать JAR с подкомандой `analyze` без префикса `--` (т.е. `java -jar bsl-ls.jar analyze ...`)

2.2 WHEN вызывается `bsl_analyze` THEN система SHALL передавать путь к исходникам через параметр `-s` и репортер через `-r json`, соответствуя синтаксису CLI версии 0.29.0

2.3 WHEN вызывается `bsl_analyze` THEN система SHALL создавать временную директорию, передавать её через параметр `-o` в команду, и читать файл `bsl-json.json` из этой временной директории после завершения JAR

2.4 WHEN вызывается `bsl_format` THEN система SHALL запускать JAR с подкомандой `format` без префикса `--` и передавать путь через параметр `-s` (т.е. `java -jar bsl-ls.jar format -s <path>`)

2.5 WHEN BSL Language Server 0.29.0 выводит в stderr строки с префиксом `WARNING:` (предупреждения JVM о deprecated API) THEN система SHALL игнорировать эти строки как шум и не прерывать выполнение из-за них

2.6 WHEN запускается `bsl_analyze` THEN система SHALL НЕ устанавливать `cwd` в директорию с исходниками; рабочая директория должна быть нейтральной (директория JAR-файла или временная директория)

### Unchanged Behavior (Regression Prevention)

3.1 WHEN анализ завершается успешно и JSON-отчёт содержит диагностики THEN система SHALL CONTINUE TO парсить JSON-отчёт в список `BSLDiagnostic` с корректными полями `file`, `line`, `column`, `severity`, `message`, `code`

3.2 WHEN анализ завершается успешно THEN система SHALL CONTINUE TO возвращать `BSLResult(success=True)` при нулевом коде возврата JAR

3.3 WHEN анализ завершается успешно THEN система SHALL CONTINUE TO удалять временный файл `bsl-json.json` после чтения (если не установлен `BSL_LOG_LEVEL=DEBUG`)

3.4 WHEN stderr содержит строки прогресса `Analyzing files` THEN система SHALL CONTINUE TO игнорировать их как шум

3.5 WHEN путь к исходникам не существует или не содержит BSL/OS файлов THEN система SHALL CONTINUE TO возвращать `BSLResult(success=False)` с описательным сообщением об ошибке

3.6 WHEN `config_path` не передан THEN система SHALL CONTINUE TO использовать конфиг по умолчанию из директории JAR-файла, создавая его при необходимости

3.7 WHEN вызывается `bsl_format` и форматирование завершается успешно THEN система SHALL CONTINUE TO возвращать `BSLResult(success=True)` с количеством обработанных файлов

3.8 WHEN превышен таймаут выполнения THEN система SHALL CONTINUE TO возвращать `BSLResult(success=False)` с сообщением о таймауте

3.9 WHEN установлено безопасное окружение (`APPDATA`, `LOCALAPPDATA`, `TEMP`, `USERPROFILE`, `HOME` перенаправлены в `tempfile.gettempdir()`) THEN система SHALL CONTINUE TO передавать это окружение в подпроцесс JAR
