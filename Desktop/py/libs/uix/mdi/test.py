from io import StringIO
from pathlib import Path
from tokenize import COMMENT, NL, NEWLINE, ENCODING, generate_tokens, TokenInfo
import tokenize
import ast
from collections import defaultdict


PYTHON_SUFFIXES = {".py"}
KV_SUFFIXES = {".kv"}

BLACKLIST = {
    "test.py",
    "output.txt",
    "_textinput.py",
"check.py", "truly_textinput.py",
    "textinput.py",
}

# count of .py files: 181
# standard .py size: 767234
# step 1: alias_imported_names .py size 674611, -92623
# step 2: alias_repeated_attributes .py size 671263, -3348
# step 3: remove_comments .py size 669089, -2174
# step 4: remove_docstrings .py size 666908, -2181
# step 5: remove_type_hints .py size 647732, -19176
# step 6: remove_orphan_strings .py size 644158, -3574
# step 7: minify_spaces .py size 636236, -7922
# step 8: normalize_indents .py size 564305, -71931
# step 9: remove_blank_lines .py size 564305, -0
# step 10: minify_operator_spaces .py size 563287, -1018
# step 11: minify_numbers .py size 563092, -195


# count of .py files: 183
# standard .py size: 734536
# step 1: remove_comments .py size 703208, -31328
# step 2: remove_docstrings .py size 699170, -4038
# step 3: remove_type_hints .py size 679430, -19740
# step 4: remove_orphan_strings .py size 676492, -2938
# step 5: minify_spaces .py size 670384, -6108
# step 6: normalize_indents .py size 575925, -94459
# step 7: remove_blank_lines .py size 575925, -0
# step 8: minify_operator_spaces .py size 574914, -10
# step 9: minify_numbers .py size 574728, -186


# count of .py files: 185
# standard .py size: 740893
# step 1: remove_comments .py size 708756, -32137
# step 2: remove_docstrings .py size 704456, -4300
# step 3: remove_type_hints .py size 685107, -19349
# step 4: remove_orphan_strings .py size 682169, -2938
# step 5: minify_spaces .py size 675976, -6193
# step 6: normalize_indents .py size 580620, -95356
# step 7: remove_blank_lines .py size 580620, -0
# step 8: minify_operator_spaces .py size 579606, -1014
# step 9: minify_numbers .py size 579420, -186

# count of .py files: 184
# standard .py size: 731477
# step 1: remove_comments .py size 701927, -29550
# step 2: remove_docstrings .py size 697807, -4120
# step 3: remove_type_hints .py size 679341, -18466
# step 4: remove_orphan_strings .py size 676403, -2938
# step 5: minify_spaces .py size 670209, -6194
# step 6: normalize_indents .py size 576120, -94089
# step 7: remove_blank_lines .py size 576120, -0
# step 8: minify_operator_spaces .py size 575143, -977
# step 9: minify_numbers .py size 574957, -186

# count of .py files: 184
# standard .py size: 727342
# step 1: remove_comments .py size 697678, -29664
# step 2: remove_docstrings .py size 693558, -4120
# step 3: remove_type_hints .py size 675313, -18245
# step 4: remove_orphan_strings .py size 672375, -2938
# step 5: minify_spaces .py size 666231, -6144
# step 6: normalize_indents .py size 572728, -93503
# step 7: remove_blank_lines .py size 572728, -0
# step 8: minify_operator_spaces .py size 571760, -968
# step 9: minify_numbers .py size 571574, -186

# count of .py files: 185
# standard .py size: 726923
# step 1: remove_comments .py size 696578, -30345
# step 2: remove_docstrings .py size 692280, -4298
# step 3: remove_type_hints .py size 674136, -18144
# step 4: remove_orphan_strings .py size 671198, -2938
# step 5: minify_spaces .py size 664998, -6200
# step 6: normalize_indents .py size 571746, -93252
# step 7: remove_blank_lines .py size 571746, -0
# step 8: minify_operator_spaces .py size 570813, -933
# step 9: minify_numbers .py size 570627, -186


# count of .py files: 186
# standard .py size: 725432
# step 1: remove_comments .py size 695082, -30350
# step 2: remove_docstrings .py size 690784, -4298
# step 3: remove_type_hints .py size 672688, -18096
# step 4: remove_orphan_strings .py size 669750, -2938
# step 5: minify_spaces .py size 663574, -6176
# step 6: normalize_indents .py size 570559, -93015
# step 7: remove_blank_lines .py size 570559, -0
# step 8: minify_operator_spaces .py size 569626, -933
# step 9: minify_numbers .py size 569440, -186

# count of .py files: 186
# standard .py size: 726181
# step 1: remove_comments .py size 694610, -31571
# step 2: remove_docstrings .py size 690312, -4298
# step 3: remove_type_hints .py size 672311, -18001
# step 4: remove_orphan_strings .py size 669373, -2938
# step 5: minify_spaces .py size 663205, -6168
# step 6: normalize_indents .py size 570112, -93093
# step 7: remove_blank_lines .py size 570112, -0
# step 8: minify_operator_spaces .py size 569177, -935
# step 9: minify_numbers .py size 568991, -186

# count of .py files: 186
# standard .py size: 724928
# step 1: remove_comments .py size 693356, -31572
# step 2: remove_docstrings .py size 689058, -4298
# step 3: remove_type_hints .py size 671127, -17931
# step 4: remove_orphan_strings .py size 668189, -2938
# step 5: minify_spaces .py size 662040, -6149
# step 6: normalize_indents .py size 569145, -92895
# step 7: remove_blank_lines .py size 569145, -0
# step 8: minify_operator_spaces .py size 568210, -935
# step 9: minify_numbers .py size 568024, -186

# count of .py files: 186
# standard .py size: 717041
# step 1: remove_comments .py size 688758, -28283
# step 2: remove_docstrings .py size 684460, -4298
# step 3: remove_type_hints .py size 666659, -17801
# step 4: remove_orphan_strings .py size 663721, -2938
# step 5: minify_spaces .py size 657573, -6148
# step 6: normalize_indents .py size 565368, -92205
# step 7: remove_blank_lines .py size 565368, -0
# step 8: minify_operator_spaces .py size 564440, -928
# step 9: minify_numbers .py size 564254, -186

# count of .py files: 180
# standard .py size: 700596
# step 1: remove_comments .py size 669923, -30673
# step 2: remove_docstrings .py size 665015, -4908
# step 3: remove_type_hints .py size 649656, -15359
# step 4: remove_orphan_strings .py size 646718, -2938
# step 5: minify_spaces .py size 640606, -6112
# step 6: normalize_indents .py size 551329, -89277
# step 7: remove_blank_lines .py size 551329, -0
# step 8: minify_operator_spaces .py size 550389, -940
# step 9: minify_numbers .py size 550187, -202

# count of .py files: 178
# standard .py size: 699389
# step 1: remove_comments .py size 668714, -30675
# step 2: remove_docstrings .py size 663626, -5088
# step 3: remove_type_hints .py size 648504, -15122
# step 4: remove_orphan_strings .py size 645566, -2938
# step 5: minify_spaces .py size 639466, -6100
# step 6: normalize_indents .py size 550375, -89091
# step 7: remove_blank_lines .py size 550375, -0
# step 8: minify_operator_spaces .py size 549435, -940
# step 9: minify_numbers .py size 549224, -211


def collect_files(root: Path, suffixes):
    files = []

    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue

        if path.name in BLACKLIST:
            continue

        if path.suffix not in suffixes:
            continue

        try:
            text = path.read_text(
                encoding="utf-8",
                errors="ignore",
            )
        except Exception as e:
            text = f"[Ошибка чтения файла: {e}]"

        files.append((path.relative_to(root), text))

    return files


def apply(files, func):
    """Применить преобразование к каждому файлу."""
    return [(path, func(text)) for path, text in files]


def remove_comments(text: str) -> str:
    tokens = list(generate_tokens(StringIO(text).readline))

    comment_lines = {
        token.start[0]
        for token in tokens
        if token.type == COMMENT
    }

    lines = text.splitlines()

    result = []

    for index, line in enumerate(lines, start=1):
        if index in comment_lines:
            # Если строка целиком комментарий — удалить
            if line.lstrip().startswith("#"):
                continue

            # Если комментарий в конце строки — убрать его
            line = line[:line.find("#")].rstrip()

        if line.strip():
            result.append(line.rstrip())

    return "\n".join(result)


def remove_docstrings(text: str) -> str:
    tree = ast.parse(text)

    docstrings = set()

    def check_body(node):
        if not hasattr(node, "body"):
            return

        body = node.body

        if (
            body
            and isinstance(body[0], ast.Expr)
            and isinstance(body[0].value, ast.Constant)
            and isinstance(body[0].value.value, str)
        ):
            docstrings.add(
                (
                    body[0].lineno,
                    body[0].end_lineno,
                )
            )

        for child in ast.iter_child_nodes(node):
            check_body(child)

    check_body(tree)

    lines = text.splitlines()

    result = []

    for number, line in enumerate(lines, start=1):
        remove = False

        for start, end in docstrings:
            if start <= number <= end:
                remove = True
                break

        if not remove:
            result.append(line)

    return "\n".join(result)


def normalize_indents(text: str) -> str:
    result = []

    for line in text.splitlines():
        stripped = line.lstrip(" ")
        spaces = len(line) - len(stripped)

        level = spaces // 4

        result.append("\t" * level + stripped)

    return "\n".join(result)


def remove_blank_lines(text: str) -> str:
    return "\n".join(
        line.rstrip()
        for line in text.splitlines()
        if line.strip()
    )


def compact_imports(text: str) -> str:
    result = []
    deps = []

    for line in text.splitlines():
        stripped = line.strip()

        if stripped.startswith("from ") and " import " in stripped:
            module, names = stripped.split(" import ", 1)

            module = module[5:].strip()

            for name in names.split(","):
                name = name.strip()
                if name:
                    deps.append(f"{module}.{name}")

        elif stripped.startswith("import "):
            module = stripped[7:].strip()

            for name in module.split(","):
                name = name.strip()
                if name:
                    deps.append(name)

        else:
            result.append(line)

    if deps:
        result.insert(0, "# deps: " + "; ".join(deps))

    return "\n".join(result)


def remove_type_hints(text: str) -> str:
    tree = ast.parse(text)
    lines = text.splitlines()
    deletions = []  # (start_line, start_col, end_line, end_col)

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            # возвращаемый тип
            if node.returns:
                start_line = node.returns.lineno
                end_line = node.returns.end_lineno
                line_text = lines[start_line - 1]
                arrow_pos = line_text.rfind('->', 0, node.returns.col_offset)
                start_col = arrow_pos if arrow_pos != -1 else node.returns.col_offset
                deletions.append((start_line, start_col, end_line, node.returns.end_col_offset))

            # аргументы
            for arg in node.args.args + node.args.kwonlyargs:
                if arg.annotation:
                    start_line = arg.annotation.lineno
                    end_line = arg.annotation.end_lineno
                    line_text = lines[start_line - 1]
                    colon_pos = line_text.rfind(':', 0, arg.annotation.col_offset)
                    start_col = colon_pos if colon_pos != -1 else arg.annotation.col_offset
                    deletions.append((start_line, start_col, end_line, arg.annotation.end_col_offset))

            if node.args.vararg and node.args.vararg.annotation:
                ann = node.args.vararg.annotation
                start_line = ann.lineno
                end_line = ann.end_lineno
                line_text = lines[start_line - 1]
                colon_pos = line_text.rfind(':', 0, ann.col_offset)
                start_col = colon_pos if colon_pos != -1 else ann.col_offset
                deletions.append((start_line, start_col, end_line, ann.end_col_offset))

            if node.args.kwarg and node.args.kwarg.annotation:
                ann = node.args.kwarg.annotation
                start_line = ann.lineno
                end_line = ann.end_lineno
                line_text = lines[start_line - 1]
                colon_pos = line_text.rfind(':', 0, ann.col_offset)
                start_col = colon_pos if colon_pos != -1 else ann.col_offset
                deletions.append((start_line, start_col, end_line, ann.end_col_offset))

        elif isinstance(node, ast.AnnAssign):
            if node.annotation:
                start_line = node.annotation.lineno
                end_line = node.annotation.end_lineno
                line_text = lines[start_line - 1]
                colon_pos = line_text.rfind(':', 0, node.annotation.col_offset)
                start_col = colon_pos if colon_pos != -1 else node.annotation.col_offset
                deletions.append((start_line, start_col, end_line, node.annotation.end_col_offset))

    # Применяем удаления в обратном порядке
    deletions.sort(key=lambda x: (x[0], x[1]), reverse=True)
    for start_line, start_col, end_line, end_col in deletions:
        if start_line == end_line:
            # Однострочное удаление
            line = lines[start_line - 1]
            lines[start_line - 1] = line[:start_col] + line[end_col:]
        else:
            # Многострочное удаление
            # Начальная строка: удалить от start_col до конца строки
            lines[start_line - 1] = lines[start_line - 1][:start_col]
            # Конечная строка: удалить от начала до end_col
            lines[end_line - 1] = lines[end_line - 1][end_col:]
            # Промежуточные строки сделать пустыми
            for i in range(start_line, end_line - 1):
                lines[i] = ""

    return "\n".join(lines)

def minify_spaces(text: str) -> str:
    """
    Удаляет пробелы в следующих позициях:
      - после открывающих скобок ( [ {
      - перед закрывающими скобками ) ] }
      - после запятой
      - перед двоеточием (только если оно не в срезе/лямбде – но мы
        действуем грубо, модель устойчива)
    Строковые литералы не затрагиваются.
    """
    # Токенизируем для получения позиций строк
    tokens = list(tokenize.generate_tokens(StringIO(text).readline))
    
    # Собираем интервалы строковых литералов (они неприкосновенны)
    string_ranges = []
    for tok in tokens:
        if tok.type == tokenize.STRING:
            # tok.start = (строка, колонка), tok.end = (строка, колонка)
            string_ranges.append((tok.start, tok.end))
    
    def is_inside_string(line, col):
        for (start_line, start_col), (end_line, end_col) in string_ranges:
            if start_line <= line <= end_line:
                if line == start_line and line == end_line:
                    if start_col <= col < end_col:
                        return True
                elif line == start_line:
                    if col >= start_col:
                        return True
                elif line == end_line:
                    if col < end_col:
                        return True
                else:  # между начальной и конечной строкой
                    return True
        return False

    lines = text.splitlines()
    new_lines = []
    for lineno, line in enumerate(lines, 1):
        # Не трогаем строки, начинающиеся с # (комментарии) — они уже удалены?
        # Лучше перестраховаться: если строка после strip начинается с #,
        # оставим как есть, т.к. это может быть строка внутри скобок, но
        # комментариев после remove_comments уже нет, так что можно не проверять.
        new_chars = []
        col = 0
        while col < len(line):
            # Пропускаем строковые литералы как есть
            if is_inside_string(lineno, col):
                new_chars.append(line[col])
                col += 1
                continue
            
            # Пробелы после ( [ {
            if col < len(line) - 1 and line[col] in '([{':
                next_col = col + 1
                while next_col < len(line) and line[next_col] == ' ':
                    next_col += 1
                new_chars.append(line[col])
                col = next_col
                continue
            
            # Пробелы перед ) ] }
            if line[col] in ')]}' and new_chars and new_chars[-1] == ' ':
                # Убираем последний пробел
                new_chars.pop()
                new_chars.append(line[col])
                col += 1
                continue
            
            # Пробелы после запятой
            if line[col] == ',' and col + 1 < len(line) and line[col+1] == ' ':
                new_chars.append(',')
                col += 2
                continue
            
            # Пробелы перед двоеточием (осторожно: лямбда, срезы)
            # Упростим: если двоеточие не внутри строки, убираем пробел перед ним,
            # только если предыдущий символ не буква/цифра/подчёркивание
            # (чтобы не ломать lambda x : y). Но можно просто убрать все пробелы
            # перед двоеточием, если перед ним нет скобок/операторов.
            # Применим простое правило: если перед двоеточием пробел, а перед
            # пробелом символ не является буквой/цифрой/_), удалим пробел.
            if line[col] == ':' and new_chars and new_chars[-1] == ' ':
                # Проверим, что перед пробелом не идентификатор
                if len(new_chars) >= 2 and not new_chars[-2].isalnum() and new_chars[-2] != '_':
                    # Это, скорее всего, slice или словарь
                    new_chars.pop()
                    new_chars.append(':')
                    col += 1
                    continue
            
            new_chars.append(line[col])
            col += 1
        
        new_lines.append(''.join(new_chars))
    
    return '\n'.join(new_lines)


def merge_adjacent_strings(text: str) -> str:
    tokens = list(tokenize.generate_tokens(StringIO(text).readline))
    new_tokens = []
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        if tok.type == tokenize.STRING:
            merged = tok
            j = i + 1
            while j < len(tokens) and tokens[j].type == tokenize.STRING and tokens[j].start[0] == merged.end[0] and tokens[j].start[1] == merged.end[1]:
                # Следующий строковой литерал на той же строке и сразу за текущим
                merged = merged._replace(string=merged.string + tokens[j].string,
                                        end=tokens[j].end)
                j += 1
            new_tokens.append(merged)
            i = j
        else:
            new_tokens.append(tok)
            i += 1
    # Собираем обратно текст
    # Используем tokenize.untokenize
    return tokenize.untokenize(new_tokens)


import re

def minify_operator_spaces(text: str) -> str:
    """
    Удаляет пробелы вокруг перечисленных ниже операторов, если они не внутри строк.
    Не трогает ключевые слова-операторы (and, or, not, in, is).
    """
    # Символьные операторы, отсортированы по длине (сначала составные)
    operators = [
        '//=', '**=', '>>=', '<<=', '+=', '-=', '*=', '/=', '%=',
        '&=', '|=', '^=', '==', '!=', '<=', '>=', '<<', '>>',
        '//', '**', '=', '+', '-', '*', '/', '%', '&', '|', '^',
        '<', '>', ';'
    ]
    escaped_ops = [re.escape(op) for op in operators]
    pattern = '|'.join(escaped_ops)

    def replacer(match):
        # Удаляем все пробелы вокруг оператора, оставляя только сам оператор
        op = match.group()
        # Внутри match может быть "  =" или "=  " – берём сам оператор без пробелов
        return op.strip()

    # Замена: (?<!\w) — перед оператором не буква/цифра/_
    #          \s*   — возможные пробелы
    #          (оператор) — захватываем
    #          \s*   — возможные пробелы
    #          (?!\w) — после оператора не буква/цифра/_
    regex = re.compile(fr'(?<!\w)\s*({pattern})\s*(?!\w)')
    return regex.sub(replacer, text)


def remove_orphan_strings(text: str) -> str:
    """Удаляет висячие строки-литералы (не docstrings)."""
    tree = ast.parse(text)
    lines_to_remove = []

    for node in ast.walk(tree):
        # Ищем выражение, состоящее только из строковой константы
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant):
            if isinstance(node.value.value, str):
                # Убедимся, что это не docstring (хотя они уже должны быть удалены)
                # Проверяем: является ли первый оператор в родительском теле?
                # Но даже если это docstring, мы уже удалили их, так что можно удалить все.
                # Исключим случай, когда это f-string или часть присваивания (не может быть в Expr).
                lines_to_remove.append((node.lineno, node.end_lineno))

    lines = text.splitlines()
    for start, end in sorted(lines_to_remove, reverse=True):
        del lines[start-1:end]

    return "\n".join(lines)


def remove_redundant_brackets(text: str) -> str:
    """Безопасно удаляет скобки вокруг простых условий/выражений."""
    def replacer(m):
        keyword = m.group(1)
        inner = m.group(2)
        # Не убираем скобки, если внутри есть запятая, `=` или `:`
        if any(c in inner for c in (',', '=', ':')):
            return m.group(0)
        return f"{keyword} {inner}:"
    return re.sub(r'\b(if|while|assert|return|yield|del)\s*\((.+?)\)\s*:', replacer, text)


def minify_numbers(text: str) -> str:
    """Минимизирует запись чисел с плавающей точкой."""
    # Убираем лишние нули в конце: 1.0 -> 1., 2.50 -> 2.5
    text = re.sub(r'(\d+\.\d*?)0+\b', r'\1', text)
    # Делаем .0 -> 0., если число без целой части: 0.5 -> .5
    text = re.sub(r'\b0\.(\d+)', r'.\1', text)
    # 1.0 -> 1. (уже покрыто, но на всякий случай)
    return text


def replace_builtins_constructors(text: str) -> str:
    """list() -> [], dict() -> {}, tuple() -> ()"""
    text = re.sub(r'\blist\(\)', '[]', text)
    text = re.sub(r'\bdict\(\)', '{}', text)
    text = re.sub(r'\btuple\(\)', '()', text)
    return text

def oneline_function_signatures(text: str) -> str:
    tree = ast.parse(text)
    lines = text.splitlines()
    replacements = []

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            start_line = node.lineno
            # последняя строка, где заканчивается любой аргумент или returns
            max_end = start_line
            # ast.arg есть у каждого аргумента, vararg, kwarg – у них есть end_lineno
            for arg in node.args.args + node.args.kwonlyargs:
                if hasattr(arg, 'end_lineno'):
                    max_end = max(max_end, arg.end_lineno)
            if node.args.vararg and hasattr(node.args.vararg, 'end_lineno'):
                max_end = max(max_end, node.args.vararg.end_lineno)
            if node.args.kwarg and hasattr(node.args.kwarg, 'end_lineno'):
                max_end = max(max_end, node.args.kwarg.end_lineno)
            if node.returns and hasattr(node.returns, 'end_lineno'):
                max_end = max(max_end, node.returns.end_lineno)

            # ищем строку с двоеточием (конец сигнатуры), начиная с max_end
            colon_line = None
            for i in range(max_end, len(lines) + 1):
                if ':' in lines[i - 1]:
                    colon_line = i
                    break
            if colon_line is None or start_line == colon_line:
                continue   # уже однострочная или ошибка

            # склеиваем строки от start_line до colon_line включительно
            sig_lines = lines[start_line - 1 : colon_line]
            joined = []
            for line in sig_lines:
                stripped = line.rstrip()
                if stripped.endswith('\\'):
                    stripped = stripped[:-1].rstrip()
                joined.append(stripped)
            single_line = ' '.join(p for p in joined if p)
            # убираем двойные пробелы
            while '  ' in single_line:
                single_line = single_line.replace('  ', ' ')

            # сохраняем отступ первой строки
            first_line = lines[start_line - 1]
            indent = first_line[:len(first_line) - len(first_line.lstrip())]
            new_line = indent + single_line.strip()

            replacements.append((start_line, colon_line, new_line))

    # применяем замены, лишние строки делаем пустыми (их потом уберёт remove_blank_lines)
    for start, end, new_line in sorted(replacements, reverse=True):
        lines[start - 1 : end] = [new_line] + [''] * (end - start)

    return '\n'.join(lines)


def remove_line_continuation(text: str) -> str:
    """
    Убирает символы продолжения строки \\ и склеивает строки.
    """
    lines = text.splitlines()
    new_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        while line.rstrip().endswith('\\'):
            stripped = line.rstrip()[:-1].rstrip()
            if i + 1 < len(lines):
                next_line = lines[i + 1]
                line = stripped + ' ' + next_line.lstrip()
                i += 1
            else:
                line = stripped
                break
        new_lines.append(line.rstrip())
        i += 1
    return '\n'.join(new_lines)


def collapse_multiline_brackets(text: str) -> str:
    """Схлопывает многострочные конструкции в скобках в одну строку, не трогая строки."""
    output = []
    i = 0
    n = len(text)
    paren = 0
    bracket = 0
    brace = 0
    in_string = False
    string_char = None   # ' или "
    triple = False

    while i < n:
        ch = text[i]

        if in_string:
            output.append(ch)
            if ch == '\\':
                # Экранирование: следующий символ добавить без обработки
                if i + 1 < n:
                    output.append(text[i + 1])
                    i += 2
                    continue
                else:
                    i += 1
                    continue

            if not triple:
                if ch == string_char:
                    in_string = False
                    string_char = None
                i += 1
                continue
            else:  # тройная кавычка
                if ch == string_char:
                    # Проверяем, не закрывается ли тройная кавычка
                    if i + 2 < n and text[i + 1] == string_char and text[i + 2] == string_char:
                        output.append(string_char)
                        output.append(string_char)
                        i += 3
                        in_string = False
                        string_char = None
                        triple = False
                        continue
                i += 1
                continue

        # Не внутри строки
        if ch in ('"', "'"):
            # Определяем, тройная ли кавычка
            if i + 2 < n and text[i + 1] == ch and text[i + 2] == ch:
                triple = True
                in_string = True
                string_char = ch
                output.append(ch)
                output.append(ch)
                output.append(ch)
                i += 3
                continue
            else:
                triple = False
                in_string = True
                string_char = ch
                output.append(ch)
                i += 1
                continue

        # Скобки
        if ch == '(':
            paren += 1
            output.append(ch)
            i += 1
            continue
        if ch == ')':
            if paren > 0:
                paren -= 1
            output.append(ch)
            i += 1
            continue
        if ch == '[':
            bracket += 1
            output.append(ch)
            i += 1
            continue
        if ch == ']':
            if bracket > 0:
                bracket -= 1
            output.append(ch)
            i += 1
            continue
        if ch == '{':
            brace += 1
            output.append(ch)
            i += 1
            continue
        if ch == '}':
            if brace > 0:
                brace -= 1
            output.append(ch)
            i += 1
            continue

        # Перенос строки
        if ch == '\n':
            if paren > 0 or bracket > 0 or brace > 0:
                # Внутри скобок – заменяем на пробел и пропускаем отступы
                if output and output[-1] != ' ':
                    output.append(' ')
                i += 1
                while i < n and text[i] in (' ', '\t'):
                    i += 1
                continue
            else:
                output.append(ch)
                i += 1
                continue

        # Обычный символ
        output.append(ch)
        i += 1

    return ''.join(output)


import ast
from collections import defaultdict

def alias_repeated_attributes(text: str) -> str:
    """
    Для каждой области видимости (функция или глобальный модуль) находит
    повторяющиеся цепочки атрибутов (вида x.y.z) и заменяет их на короткую
    локальную переменную _v0, _v1... Экономит символы, сохраняя семантику.
    """
    tree = ast.parse(text)

    class AliasTransformer(ast.NodeTransformer):
        def __init__(self):
            self.var_counter = 0

        def _make_alias_name(self):
            name = f"_v{self.var_counter}"
            self.var_counter += 1
            return name

        def _replace_chains_in_body(self, body, scope_local_names, is_module=False):
            # Рекурсивно обрабатываем вложенные функции/классы
            for stmt in body:
                self.generic_visit(stmt)

            chain_occurrences = defaultdict(list)

            class ChainCollector(ast.NodeVisitor):
                def __init__(self, is_module):
                    self.is_module = is_module

                def visit_Attribute(self, node):
                    chain_parts = []
                    curr = node
                    while isinstance(curr, ast.Attribute):
                        chain_parts.append(curr.attr)
                        curr = curr.value
                    if isinstance(curr, ast.Name):
                        chain_parts.append(curr.id)
                    else:
                        return
                    chain_str = ".".join(reversed(chain_parts))
                    base_name = chain_parts[-1]

                    # Пропускаем, если база переопределяется внутри области (кроме self)
                    if base_name != 'self' and base_name in scope_local_names:
                        return
                    # На уровне модуля запрещаем self (он там не существует)
                    if self.is_module and base_name == 'self':
                        return

                    chain_occurrences[chain_str].append(node)
                    self.generic_visit(node)

            collector = ChainCollector(is_module)
            for stmt in body:
                collector.visit(stmt)

            alias_map = {}
            assign_nodes = []
            for chain_str, nodes in chain_occurrences.items():
                count = len(nodes)

                # 1. Пропускаем короткие цепочки (ровно одна точка и длина <= 8)
                if chain_str.count('.') == 1 and len(chain_str) <= 8:
                    continue

                # 2. Считаем реальную прибыль
                # Пробуем имя-кандидат (счётчик пока не увеличиваем)
                candidate_name = f"_v{self.var_counter}"
                candidate_len = len(candidate_name)
                assignment_cost = candidate_len + 1 + len(chain_str)   # напр. _v0=self.x
                saving = (len(chain_str) - candidate_len) * count - assignment_cost

                if saving > 0:
                    # Принимаем алиас, фиксируем счётчик
                    self.var_counter += 1
                    alias_name = candidate_name
                    while alias_name in scope_local_names:
                        # такое имя уже занято, генерируем следующее
                        alias_name = f"_v{self.var_counter}"
                        self.var_counter += 1
                    scope_local_names.add(alias_name)
                    alias_map[chain_str] = alias_name

                    # Строим узел присваивания
                    parts = chain_str.split('.')
                    base = ast.Name(id=parts[0], ctx=ast.Load())
                    attr_node = base
                    for attr in parts[1:]:
                        attr_node = ast.Attribute(value=attr_node, attr=attr, ctx=ast.Load())
                    assign_nodes.append(
                        ast.Assign(
                            targets=[ast.Name(id=alias_name, ctx=ast.Store())],
                            value=attr_node,
                            lineno=0, col_offset=0,
                        )
                    )
                # иначе игнорируем цепочку и не тратим имя

            if alias_map:
                class ChainReplacer(ast.NodeTransformer):
                    def visit_Attribute(self, node):
                        chain_parts = []
                        curr = node
                        while isinstance(curr, ast.Attribute):
                            chain_parts.append(curr.attr)
                            curr = curr.value
                        if isinstance(curr, ast.Name):
                            chain_parts.append(curr.id)
                            chain_str = ".".join(reversed(chain_parts))
                            if chain_str in alias_map:
                                new_node = ast.Name(id=alias_map[chain_str], ctx=ast.Load())
                                return ast.copy_location(new_node, node)
                        self.generic_visit(node)
                        return node

                replacer = ChainReplacer()
                new_body = [replacer.visit(stmt) for stmt in body]
                return assign_nodes + new_body
            else:
                return body

        def _collect_local_names(self, node, exclude_nested=True):
            local_names = set()
            class Collector(ast.NodeVisitor):
                def visit_Name(self, n):
                    if isinstance(n.ctx, ast.Store):
                        local_names.add(n.id)
                def visit_FunctionDef(self, n):
                    pass
                def visit_AsyncFunctionDef(self, n):
                    pass
                def visit_ClassDef(self, n):
                    pass
            collector = Collector()
            for stmt in node.body:
                collector.visit(stmt)
            return local_names

        def visit_FunctionDef(self, node):
            local_names = set()
            for arg in node.args.args + node.args.kwonlyargs:
                if arg.arg:
                    local_names.add(arg.arg)
            if node.args.vararg and node.args.vararg.arg:
                local_names.add(node.args.vararg.arg)
            if node.args.kwarg and node.args.kwarg.arg:
                local_names.add(node.args.kwarg.arg)
            local_names.update(self._collect_local_names(node))
            node.body = self._replace_chains_in_body(node.body, local_names, is_module=False)
            return node

        def visit_AsyncFunctionDef(self, node):
            return self.visit_FunctionDef(node)

        def visit_Module(self, node):
            self.generic_visit(node)
            return node

    transformer = AliasTransformer()
    new_tree = transformer.visit(tree)
    ast.fix_missing_locations(new_tree)

    return ast.unparse(new_tree)


import ast
from collections import Counter

def alias_imported_names(text: str) -> str:
    """
    Для каждого файла находит импортированные имена, которые используются в коде
    >= 3 раз, и заменяет их на короткие алиасы (_i0, _i1...), добавляя as в импорт.
    """
    tree = ast.parse(text)
    transformer = _AliasImportedTransformer()
    new_tree = transformer.visit(tree)
    ast.fix_missing_locations(new_tree)
    return ast.unparse(new_tree)


class _AliasImportedTransformer(ast.NodeTransformer):
    def __init__(self):
        self.counter = 0

    def _make_alias(self):
        name = f"_i{self.counter}"
        self.counter += 1
        return name

    def visit_Module(self, node):
        # Собираем все имена, используемые в модуле (Load), кроме имён из импортов?
        # Но нам нужны именно имена, которые импортированы и используются.
        # Сначала соберём все импорты и их локальные имена.
        imports = []  # список (узел импорта, список (оригинальное_имя, локальное_имя))
        for stmt in node.body:
            if isinstance(stmt, ast.Import):
                for alias in stmt.names:
                    local_name = alias.asname or alias.name.split('.')[0]
                    imports.append((stmt, alias.name, local_name))
            elif isinstance(stmt, ast.ImportFrom):
                if stmt.module is None:  # from . import ...
                    continue
                for alias in stmt.names:
                    local_name = alias.asname or alias.name
                    imports.append((stmt, alias.name, local_name))

        # Подсчитываем использование каждого локального имени в коде
        usage_counter = Counter()
        class UsageCollector(ast.NodeVisitor):
            def visit_Name(self, node):
                if isinstance(node.ctx, ast.Load):
                    usage_counter[node.id] += 1
                self.generic_visit(node)
        UsageCollector().visit(node)

        # Отбираем имена, которые используются >= 3 раз и присутствуют в imports
        alias_map = {}  # локальное_имя -> новый_алиас
        for stmt, orig_name, local_name in imports:
            if usage_counter.get(local_name, 0) >= 3:
                new_alias = self._make_alias()
                alias_map[local_name] = new_alias

        if not alias_map:
            return node

        # Меняем импорты: добавляем as new_alias
        new_body = []
        for stmt in node.body:
            if isinstance(stmt, ast.Import):
                new_names = []
                for alias in stmt.names:
                    local = alias.asname or alias.name.split('.')[0]
                    if local in alias_map:
                        new_names.append(ast.alias(name=alias.name, asname=alias_map[local]))
                    else:
                        new_names.append(alias)
                if new_names:
                    stmt.names = new_names
                    new_body.append(stmt)
            elif isinstance(stmt, ast.ImportFrom):
                new_names = []
                for alias in stmt.names:
                    local = alias.asname or alias.name
                    if local in alias_map:
                        new_names.append(ast.alias(name=alias.name, asname=alias_map[local]))
                    else:
                        new_names.append(alias)
                if new_names:
                    stmt.names = new_names
                    new_body.append(stmt)
            else:
                new_body.append(stmt)
        node.body = new_body

        # Заменяем все обращения к старым локальным именам на новые алиасы
        class NameReplacer(ast.NodeTransformer):
            def visit_Name(self, node):
                if isinstance(node.ctx, ast.Load) and node.id in alias_map:
                    return ast.Name(id=alias_map[node.id], ctx=ast.Load())
                return node
        replacer = NameReplacer()
        node = replacer.visit(node)

        return node


def optimize_python(files):
    print("count of .py files:", len(files))
    print("standard .py size:", len(render(files)))

    # d = {path: len(content) for path, content in files}
    # for path, content in files:
    #     print(path, len(content))

    steps = {
        # "alias_imported_names": alias_imported_names,
        # "alias_repeated_attributes": alias_repeated_attributes,
        # "remove_comments": remove_comments,
        # "remove_docstrings": remove_docstrings,
        # "remove_type_hints": remove_type_hints,
        # неэффективно
        # "remove_line_continuation": remove_line_continuation,
        # "remove_orphan_strings": remove_orphan_strings,
        # неэффективно
        # "collapse_multiline_brackets": collapse_multiline_brackets,
        # "minify_spaces": minify_spaces,
        # неэффективно
        # "oneline_function_signatures": oneline_function_signatures,
        "normalize_indents": normalize_indents,
        # неэффективно
        # "merge_adjacent_strings": merge_adjacent_strings,
        # "remove_blank_lines": remove_blank_lines,
        # "compact_imports": compact_imports,
        # "minify_operator_spaces": minify_operator_spaces,
        # неэффективно
        # "remove_redundant_brackets": remove_redundant_brackets,
        # "minify_numbers": minify_numbers,
        # неэффективно
        # "replace_builtins_constructors": replace_builtins_constructors,
        # "remove_type_hints2": remove_type_hints,
    }

    prev_size = len(render(files))
    for i, stepname in enumerate(steps):
        func = steps[stepname]
        files = apply(files, func)
        now_size = len(render(files))
        print(f"step {i + 1}: {stepname} .py size {now_size}, -{prev_size - now_size}")
        prev_size = now_size
    return files


def optimize_kv(files):
    return files


def render(files):
    parts = []

    for path, text in files:
        parts.append(f"@{path.as_posix()}")
        parts.append(text)
        parts.append("")

    return "\n".join(parts)


def save(path: Path, text: str):
    path.write_text(text, encoding="utf-8")


def main():
    root = Path.cwd()

    python_files = collect_files(root, PYTHON_SUFFIXES)
    # kv_files = collect_files(root, KV_SUFFIXES)

    python_files = optimize_python(python_files)
    # kv_files = optimize_kv(kv_files)

    save(root / "python.txt", render(python_files))
    # save(root / "kv.txt", render(kv_files))


if __name__ == "__main__":
    main()

