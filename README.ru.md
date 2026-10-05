# КОМПАС-3D на Linux: скилл для Claude Code

**[English version](README.md)**

[Скилл для Claude Code](https://claude.com/claude-code) и Python-помощники, которые управляют **КОМПАС-3D v25** через его Python API (`ksapi`) в нативной Linux-сборке. Claude с ними строит фрагменты и чертежи: геометрию, размеры, заливку, экспорт в PNG. Плюс лаунчер, из-за которого КОМПАС больше не роняет Wayland-сессию.

<p align="center">
  <img src="docs/flange.png" width="520" alt="Фланец, построенный examples/flange.py">
  <br><sub>Построено целиком через API скриптом <a href="examples/flange.py">examples/flange.py</a>: усечённая геометрия, размеры, проверка наслоений.</sub>
</p>

## Что внутри

| Путь | Что это |
|---|---|
| [`skill/kompas-3d/SKILL.md`](skill/kompas-3d/SKILL.md) | Сам скилл: настройка, порядок работы над чертежом и подводные камни API, проверенные на v25 |
| [`skill/kompas-3d/scripts/ks.py`](skill/kompas-3d/scripts/ks.py) | Помощники: `seg` `arc` `circle` `polygon` `text`, `rdim` `ddim` `ldim` `adim`, `fill`, `overlaps`, `export_png`, `save` |
| [`skill/kompas-3d/scripts/run.sh`](skill/kompas-3d/scripts/run.sh) | Запускает Python-скрипт внутри distrobox против запущенного КОМПАСа |
| [`skill/kompas-3d/scripts/pdf_images.py`](skill/kompas-3d/scripts/pdf_images.py) | Достаёт рисунки и текст из PDF с заданием |
| [`launcher/kompas-nested`](launcher/kompas-nested) | Запускает КОМПАС внутри Xephyr + openbox |
| [`examples/`](examples) | `flange.py` (картинка выше) и `selftest.py` (проверяет все помощники на твоём КОМПАСе) |

## Зачем

- **API почти не документирован, и часть вызовов делает не то, что обещает название.** Например:
  - `SetDirection` у дуги иногда рисует вторую часть окружности;
  - угловой размер по точкам меряет второй луч от начала координат листа;
  - диаметральный размер игнорирует `SetShelfAngle`/`SetShelfLength`;
  - растровый экспорт по умолчанию серый и зависает на модальном окне, если файл уже есть.

  В скилле записано, что реально работает, чтобы Claude не наступал на это каждый раз заново.
- **КОМПАС роняет swayfx.** Его контекстная панель — всплывающее окно XWayland, которое очень быстро появляется и исчезает. swayfx 0.6 на нём падает вместе со всей сессией. `kompas-nested` запускает КОМПАС во вложенном X-сервере, и композитор видит одно обычное окно.

## Что нужно

- Linux с [distrobox](https://distrobox.it/) (podman или docker).
- КОМПАС-3D v25 для Linux в боксе на Ubuntu 24.04, установленный из apt-репозитория АСКОН по их инструкции. Проверено на КОМПАС-3D v25 Home 25.0.1.2738 (`ascon-kompas3d-home-v25-full`).
- В боксе для лаунчера: `xserver-xephyr openbox x11-xkb-utils`.
- [Claude Code](https://claude.com/claude-code) для скилла. Помощники работают и без него.

## Установка

```bash
# один раз: бокс (потом поставь в него КОМПАС по инструкции АСКОН)
distrobox create -n kompas-box -i ubuntu:24.04
distrobox enter kompas-box -- sudo apt install -y xserver-xephyr openbox x11-xkb-utils

git clone https://github.com/IsWaFF/kompas3d-linux-skill
cd kompas3d-linux-skill
./install.sh            # или ./install.sh --link, чтобы ставить симлинками
```

`install.sh` кладёт скилл в `~/.claude/skills/kompas-3d`, лаунчер в `~/.local/bin/kompas-nested` и добавляет пункт меню «КОМПАС-3D (во вложенном X)». Если там уже что-то лежит, оно переезжает в `~/.claude/backups/kompas-3d-install-<время>/`. Куда ставить, меняется через `CLAUDE_CONFIG_DIR`, `BIN_DIR` и `XDG_DATA_HOME`.

## Как пользоваться

Запусти КОМПАС через `kompas-nested` и попроси Claude Code, например: «начерти в компасе фланец Ø120 с четырьмя отверстиями». Скилл срабатывает на слова КОМПАС / чертёж / фрагмент.

Без Claude:

```bash
skill/kompas-3d/scripts/run.sh examples/flange.py ~/out     # -> ~/out/flange.frw, ~/out/flange.png
skill/kompas-3d/scripts/run.sh examples/selftest.py ~/out   # быстрая проверка всех помощников
```

```python
import ks

ks.new_fragment()                 # эксперименты — в новом документе, не в чужом
ks.circle(0, 0, 30)               # контур + осевые
ks.ddim(0, 0, 30, 45)             # Ø60
assert ks.overlaps() == []        # нет наслоений
ks.save('/home/me/part.frw')
ks.export_png('/home/me/part.png')
```

Переменные окружения (бокс, путь установки, дисплей, раскладка и т.д.) описаны в [английском README](README.md#configuration). Для sway есть [`launcher/sway.conf`](launcher/sway.conf).

## Ограничения

- Проверено на одной системе: Garuda Linux, swayfx 0.6, КОМПАС-3D v25 Home. Другие композиторы и редакции должны работать, но не проверялись.
- Только 2D (фрагменты и чертежи).
- API нужен настоящий дисплей: под Xvfb окно лицензий не завершается и порт API не открывается. Запускай в обычной графической сессии.
- Windows не покрыт. Сам `ksapi.py` поддерживает Windows, так что `ks.py` там, возможно, заработает, но `run.sh` и лаунчер только для Linux.

## Лицензия

[MIT](LICENSE). КОМПАС-3D — товарный знак АСКОН. Проект с АСКОН не связан. `ksapi.py` и SDK КОМПАСа сюда не входят: они идут с твоей установкой КОМПАСа.

Сделано вместе с Claude Code.
