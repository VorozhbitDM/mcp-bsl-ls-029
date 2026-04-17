# BSL LS 0.29.0 Compatibility Bugfix Design

## Overview

MCP-сервер перестал работать после обновления JAR-файла до BSL Language Server 0.29.0. Версия 0.29.0 изменила синтаксис CLI: подкоманды `analyze` и `format` теперь передаются без префикса `--`, параметры переименованы, а JSON-отчёт записывается в явно указанную директорию через флаг `-o`. Дополнительно JVM 0.29.0 выводит в stderr предупреждения `WARNING:`, которые текущий фильтр шума не распознаёт и ошибочно трактует как сбой.

Стратегия исправления: минимальные точечные изменения только в `bsl_runner.py` — обновить `_build_analyze_command`, `_build_format_command`, логику чтения JSON-отчёта и унифицировать фильтрацию stderr через `_is_noise_line`.

## Glossary

- **Bug_Condition (C)**: Условие, при котором проявляется баг — вызов `bsl_analyze` или `bsl_format` с любым корректным путём к исходникам при использовании JAR версии 0.29.0
- **Property (P)**: Ожидаемое поведение при выполнении условия бага — JAR запускается с корректным синтаксисом CLI 0.29.0 и возвращает результат без ошибок синтаксиса команды
- **Preservation**: Существующее поведение, которое не должно измениться: парсинг JSON-диагностик, удаление временных файлов, фильтрация `Analyzing files`, безопасное окружение, обработка таймаутов
- **`_build_analyze_command`**: Метод в `src/mcp_bsl/bsl_runner.py`, строящий список аргументов для `subprocess.run` при запуске анализа
- **`_build_format_command`**: Метод в `src/mcp_bsl/bsl_runner.py`, строящий список аргументов для `subprocess.run` при запуске форматирования
- **`_is_noise_line`**: Функция в `src/mcp_bsl/bsl_runner.py`, возвращающая `True` для строк stderr, которые являются шумом JVM/прогрессом, а не реальными ошибками
- **`analyze`**: Публичный метод `BSLRunner`, оркестрирующий запуск анализа, чтение JSON-отчёта и возврат `BSLResult`
- **`work_dir`**: Рабочая директория, передаваемая в `cwd` параметр `subprocess.run` — в текущем коде установлена в директорию исходников, что не требуется в 0.29.0
- **`output_dir`**: Временная директория, создаваемая через `tempfile.mkdtemp()`, передаваемая в `-o` и удаляемая после чтения отчёта

## Bug Details

### Bug Condition

Баг проявляется при любом вызове `bsl_analyze` или `bsl_format` с JAR версии 0.29.0. Методы `_build_analyze_command` и `_build_format_command` генерируют команды со старым синтаксисом (`--analyze`, `--format`, `--srcDir`, `--reporter`, `--src`), который версия 0.29.0 не распознаёт. Дополнительно метод `analyze` ищет JSON-отчёт в неверном месте и не фильтрует `WARNING:` строки через `_is_noise_line`.

**Formal Specification:**
```
FUNCTION isBugCondition(call)
  INPUT: call — вызов bsl_analyze или bsl_format с корректным путём к исходникам
  OUTPUT: boolean

  RETURN jarVersion(call.config.jar_path) == "0.29.0"
         AND (
           commandContains(call, "--analyze")
           OR commandContains(call, "--format")
           OR commandContains(call, "--srcDir")
           OR commandContains(call, "--reporter")
           OR commandContains(call, "--src")
           OR NOT commandContains(call, "-o")
           OR stderrContains("WARNING:") AND NOT isFiltered("WARNING:")
         )
END FUNCTION
```

### Examples

- **analyze вызов**: `java -jar bsl-ls.jar --analyze --srcDir C:\src --reporter json -c cfg.json` → ошибка `Unknown option: '--analyze'`, `returncode != 0`; ожидалось: `java -jar bsl-ls.jar -c cfg.json analyze -s C:\src -r json -o C:\tmp\bsl_xyz`
- **format вызов**: `java -jar bsl-ls.jar --format --src C:\src` → ошибка `Unknown option: '--format'`; ожидалось: `java -jar bsl-ls.jar format -s C:\src`
- **WARNING: в stderr**: строка `WARNING: A terminally deprecated method in java.lang.System has been called` → `BSLResult(success=False)`; ожидалось: строка игнорируется, анализ продолжается
- **JSON-отчёт не найден**: код ищет `work_dir / "bsl-json.json"`, но 0.29.0 записывает в директорию из `-o`; ожидалось: читать из `output_dir / "bsl-json.json"`

## Expected Behavior

### Preservation Requirements

**Unchanged Behaviors:**
- Парсинг JSON-отчёта в список `BSLDiagnostic` через `_parse_analyze_output` — без изменений
- Удаление временного файла `bsl-json.json` после чтения (если не `BSL_LOG_LEVEL=DEBUG`)
- Фильтрация строк прогресса `Analyzing files` как шума
- Передача безопасного окружения (`APPDATA`, `LOCALAPPDATA`, `TEMP`, `USERPROFILE`, `HOME` → `tempfile.gettempdir()`) в подпроцесс
- Возврат `BSLResult(success=True)` при нулевом коде возврата JAR
- Возврат `BSLResult(success=False)` при таймауте с описательным сообщением
- Использование конфига по умолчанию из директории JAR при отсутствии явного `config_path`
- Возврат `BSLResult(success=False)` при отсутствии исходников или некорректном пути

**Scope:**
Все вызовы, не связанные с построением команды CLI (парсинг, подсчёт файлов, обработка ошибок, форматирование результата в `server.py`), должны остаться полностью неизменными.

## Hypothesized Root Cause

На основе анализа кода и документации CLI 0.29.0:

1. **Устаревший синтаксис подкоманд**: `_build_analyze_command` использует `'--analyze'` как флаг, тогда как 0.29.0 требует `'analyze'` как позиционную подкоманду. Аналогично для `format`.

2. **Переименованные параметры**: `--srcDir` → `-s`/`--srcDir` (короткая форма), `--reporter` → `-r`, `--src` → `-s`. Версия 0.29.0 принимает только короткие формы или новые длинные.

3. **Отсутствие флага `-o`**: Текущий код не передаёт выходную директорию через `-o`, поэтому JAR либо не создаёт JSON-отчёт, либо создаёт его в непредсказуемом месте. Код ищет файл в `work_dir`, который больше не является рабочей директорией JAR.

4. **Глобальный флаг `-c` стоит после подкоманды**: В 0.29.0 флаг `-c` (конфиг) является глобальным и должен идти ДО подкоманды: `java -jar bsl-ls.jar -c cfg.json analyze ...`.

5. **Неполный фильтр шума**: `_is_noise_line` содержит `'WARNING:'` в `_IGNORE_PREFIXES`, но метод `analyze` фильтрует stderr inline с проверкой только `'Analyzing files'`, игнорируя `_is_noise_line`. Строки `WARNING:` от JVM 0.29.0 проходят фильтр и трактуются как ошибки.

6. **Лишний `cwd=work_dir`**: Установка рабочей директории в директорию исходников не нужна в 0.29.0 (все пути передаются абсолютными через параметры) и может конфликтовать с путями.

## Correctness Properties

Property 1: Bug Condition — Корректный синтаксис CLI 0.29.0

_For any_ вызова `bsl_analyze` или `bsl_format` с корректным путём к исходникам, где `isBugCondition` возвращает `true`, исправленный код SHALL генерировать команду с подкомандой без `--` (`analyze`/`format`), параметрами `-s`, `-r`, `-o` (для analyze) и глобальным флагом `-c` перед подкомандой, и SHALL читать JSON-отчёт из временной директории, переданной через `-o`.

**Validates: Requirements 2.1, 2.2, 2.3, 2.4**

Property 2: Preservation — Неизменность существующего поведения

_For any_ входных данных, где `isBugCondition` возвращает `false` (корректные пути, нормальный stderr без `WARNING:`, нулевой код возврата JAR), исправленный код SHALL производить тот же результат, что и оригинальный код, сохраняя парсинг диагностик, удаление временных файлов, передачу безопасного окружения и обработку ошибок.

**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.7, 3.8, 3.9**

Property 3: Preservation — Фильтрация шума stderr

_For any_ строки stderr, начинающейся с `'WARNING:'`, `'Analyzing files'`, `'OpenJDK'` или `'Java HotSpot'`, функция `_is_noise_line` SHALL возвращать `True`, и метод `analyze` SHALL использовать `_is_noise_line` для фильтрации (а не inline-проверку).

**Validates: Requirements 2.5, 3.4**

## Fix Implementation

### Changes Required

**File**: `src/mcp_bsl/bsl_runner.py`

**Specific Changes**:

1. **`_build_analyze_command` — исправить синтаксис CLI**:
   - Убрать `'--analyze'`, заменить на позиционную подкоманду `'analyze'`
   - Переместить `-c config_path` ПЕРЕД подкомандой (глобальный флаг)
   - Заменить `'--srcDir'` на `'-s'`
   - Заменить `'--reporter', 'json'` на `'-r', 'json'`
   - Добавить `'-o', output_path` где `output_path` — временная директория из `tempfile.mkdtemp()`
   - Убрать закомментированный мёртвый код

2. **`_build_analyze_command` — управление временной директорией**:
   - Создавать `output_dir = tempfile.mkdtemp()` внутри метода или передавать как параметр
   - Возвращать `(cmd, output_dir)` или принимать `output_dir` как параметр, чтобы `analyze` знал, где читать отчёт

3. **`analyze` — читать отчёт из временной директории**:
   - Получать `output_dir` от `_build_analyze_command`
   - Искать `json_report_path = Path(output_dir) / "bsl-json.json"`
   - После чтения удалять всю директорию `shutil.rmtree(output_dir)` (не только файл)

4. **`analyze` — убрать `cwd=work_dir`**:
   - Убрать параметр `cwd=str(work_dir)` из `subprocess.run`
   - Убрать вычисление `work_dir` если оно больше не используется

5. **`analyze` — унифицировать фильтрацию stderr**:
   - Заменить inline-фильтр `not line.strip().startswith('Analyzing files')` на вызов `_is_noise_line(line)`
   - Убедиться, что `_IGNORE_PREFIXES` содержит `'WARNING:'` (уже есть)

6. **`_build_format_command` — исправить синтаксис CLI**:
   - Убрать `'--format'`, заменить на позиционную подкоманду `'format'`
   - Заменить `'--src'` на `'-s'`

### Итоговый синтаксис команд после исправления

```
# analyze
java -Xmx{memory}m -Dfile.encoding=UTF-8 -jar bsl-ls.jar -c cfg.json analyze -s <srcDir> -r json -o <tempDir>

# format
java -Dfile.encoding=UTF-8 -jar bsl-ls.jar format -s <path>
```

## Testing Strategy

### Validation Approach

Стратегия тестирования следует двухфазному подходу: сначала воспроизвести баг на неисправленном коде (exploratory), затем верифицировать исправление и убедиться в отсутствии регрессий (fix + preservation checking).

### Exploratory Bug Condition Checking

**Goal**: Воспроизвести баг ДО реализации исправления. Подтвердить или опровергнуть гипотезу о корневых причинах. При опровержении — пересмотреть гипотезу.

**Test Plan**: Написать тесты, которые вызывают `_build_analyze_command` и `_build_format_command` на текущем коде и проверяют содержимое сгенерированных команд. Запустить на НЕИСПРАВЛЕННОМ коде для наблюдения сбоев.

**Test Cases**:
1. **Analyze subcommand test**: Вызвать `_build_analyze_command` и проверить, что команда содержит `'--analyze'` (будет провалено на неисправленном коде, подтверждает баг)
2. **Analyze params test**: Проверить наличие `'--srcDir'` и `'--reporter'` в команде (будет провалено)
3. **Format subcommand test**: Вызвать `_build_format_command` и проверить наличие `'--format'` и `'--src'` (будет провалено)
4. **WARNING filter test**: Передать строку `'WARNING: A terminally deprecated method'` в inline-фильтр метода `analyze` и убедиться, что она НЕ фильтруется (будет провалено — подтверждает баг)
5. **Output dir test**: Проверить, что команда analyze НЕ содержит флаг `-o` (будет провалено — подтверждает баг)

**Expected Counterexamples**:
- Команда содержит `'--analyze'` вместо `'analyze'`
- Команда содержит `'--srcDir'` вместо `'-s'`
- Команда не содержит `'-o'`
- `WARNING:` строки не фильтруются inline-кодом в `analyze`

### Fix Checking

**Goal**: Верифицировать, что для всех входных данных, где `isBugCondition` истинно, исправленный код производит ожидаемое поведение.

**Pseudocode:**
```
FOR ALL call WHERE isBugCondition(call) DO
  cmd := fixedBuildAnalyzeCommand(call.source_path, call.config_file, call.memory)
  ASSERT 'analyze' IN cmd AND '--analyze' NOT IN cmd
  ASSERT '-s' IN cmd AND '--srcDir' NOT IN cmd
  ASSERT '-r' IN cmd AND 'json' IN cmd
  ASSERT '-o' IN cmd
  ASSERT '-c' appears BEFORE 'analyze' IN cmd
  ASSERT cmd[cmd.index('-o') + 1] is a valid temp directory path
END FOR

FOR ALL call WHERE isBugCondition(call) AND call.type == 'format' DO
  cmd := fixedBuildFormatCommand(call.source_path)
  ASSERT 'format' IN cmd AND '--format' NOT IN cmd
  ASSERT '-s' IN cmd AND '--src' NOT IN cmd
END FOR
```

### Preservation Checking

**Goal**: Верифицировать, что для всех входных данных, где `isBugCondition` ложно, исправленный код производит тот же результат, что и оригинальный.

**Pseudocode:**
```
FOR ALL stderr_line WHERE NOT isBugCondition(stderr_line) DO
  ASSERT _is_noise_line_original(stderr_line) == _is_noise_line_fixed(stderr_line)
END FOR

FOR ALL json_payload WHERE NOT isBugCondition(json_payload) DO
  ASSERT _parse_analyze_output_original(json_payload) == _parse_analyze_output_fixed(json_payload)
END FOR
```

**Testing Approach**: Property-based testing рекомендуется для preservation checking потому что:
- Автоматически генерирует множество тест-кейсов по всему входному пространству
- Выявляет граничные случаи, которые ручные тесты могут пропустить
- Даёт сильные гарантии неизменности поведения для всех не-багованных входных данных

**Test Plan**: Наблюдать поведение на НЕИСПРАВЛЕННОМ коде для нормальных входных данных (корректный JSON, нормальный stderr), затем написать property-based тесты, фиксирующие это поведение.

**Test Cases**:
1. **JSON parsing preservation**: Передать известный JSON-payload в `_parse_analyze_output` и убедиться, что список `BSLDiagnostic` идентичен до и после исправления
2. **Noise filter preservation**: Убедиться, что `_is_noise_line('Analyzing files ...')` возвращает `True` после исправления
3. **Safe environment preservation**: Убедиться, что `_get_safe_environment()` возвращает словарь с перенаправленными `APPDATA`, `TEMP` и т.д.
4. **Temp file cleanup preservation**: Убедиться, что временная директория удаляется после чтения отчёта (не только файл)

### Unit Tests

- Тест синтаксиса команды `analyze`: проверить позицию `-c`, наличие `analyze`, `-s`, `-r json`, `-o`
- Тест синтаксиса команды `format`: проверить наличие `format`, `-s`
- Тест `_is_noise_line` для всех префиксов из `_IGNORE_PREFIXES` включая `WARNING:`
- Тест чтения JSON-отчёта из временной директории (mock subprocess)
- Тест удаления всей временной директории после чтения (не только файла)
- Тест отсутствия `cwd` в вызове `subprocess.run` для analyze

### Property-Based Tests

- Генерировать случайные строки stderr и проверять, что `_is_noise_line` согласован с `_IGNORE_PREFIXES`
- Генерировать случайные JSON-payload диагностик и проверять, что `_parse_analyze_output` возвращает корректные `BSLDiagnostic` объекты (preservation)
- Генерировать случайные пути к исходникам и проверять, что команда всегда содержит `-s <path>` с корректным абсолютным путём

### Integration Tests

- Запустить реальный JAR 0.29.0 на тестовой директории с BSL-файлами и убедиться, что `bsl_analyze` возвращает `BSLResult(success=True)` с диагностиками
- Запустить реальный JAR 0.29.0 на тестовом BSL-файле и убедиться, что `bsl_format` возвращает `BSLResult(success=True)`
- Убедиться, что временная директория для JSON-отчёта удаляется после успешного анализа
