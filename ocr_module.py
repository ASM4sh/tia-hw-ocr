import cv2
import easyocr
import numpy as np
from typing import List
import re, unicodedata, ipaddress

# === Настройки детекции блоков ===
TARGET_COLOR_HEX = '#CACCD9'
DELTA = 12
PAD_DOWN = 40
UPSCALE = 4
AREA_MIN = 2000
ASPECT_MIN, ASPECT_MAX = 0.7, 10.0

# === Поиск IP: берём первое совпадение по регулярке в блоке ===
IP_PATTERN = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
_ip_re = re.compile(IP_PATTERN)

def _norm(s):
    s = "" if s is None else str(s)
    s = unicodedata.normalize("NFKC", s)
    return s.replace("\u00A0", " ").replace("\u200B", "")

def _valid_ip(s: str) -> bool:
    try:
        ipaddress.ip_address(s)
        return True
    except ValueError:
        return False

def _find_first_ip(lines: List[str]) -> str | None:
    # Ищем первое совпадение по регулярке среди всех строк блока,
    # приводим к «чистому» виду и валидируем как IPv4/IPv6.
    for line in lines:
        line = _norm(line)
        m = _ip_re.search(line)
        if not m:
            continue
        cand = m.group(0).strip(".,;:)]}>")
        if _valid_ip(cand):
            return cand
    return None

# Преобразование HEX в BGR
def hex2bgr(h):
    return np.array([int(h[5:7],16), int(h[3:5],16), int(h[1:3],16)], dtype=np.uint8)

# Кэшируем EasyOCR.Reader (важно для стабильности)
_READER = None
def get_reader(use_gpu=False):
    global _READER
    if _READER is None:
        # Если есть проблемы с CUDA — установи use_gpu=False
        _READER = easyocr.Reader(['en'], gpu=use_gpu)
    return _READER

# === ВСПОМОГАТЕЛЬНОЕ: OCR на np-массиве → Список блоков строк ===
def _extract_blocks_from_image_np(img: np.ndarray, use_gpu: bool = False) -> List[List[str]]:
    if img is None:
        return [["Fehler beim Laden des Bildes"]]

    H, W = img.shape[:2]

    # Маска по целевому серому цвету
    target = hex2bgr(TARGET_COLOR_HEX)
    lower = np.clip(target - DELTA, 0, 255)
    upper = np.clip(target + DELTA, 0, 255)
    mask_raw = cv2.inRange(img, lower, upper)

    # Морфология
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    mask = cv2.morphologyEx(mask_raw, cv2.MORPH_CLOSE, kernel, iterations=2)

    # Контуры и фильтр по площади/аспекту
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    boxes = []
    for c in contours:
        x, y, w, h = cv2.boundingRect(c)
        if h == 0:
            continue
        area = w * h
        aspect = w / float(h)
        if area > AREA_MIN and ASPECT_MIN <= aspect <= ASPECT_MAX:
            boxes.append((x, y, w, h))

    if not boxes:
        return [["Kein Gerät erkannt"]]

    # Сортировка блоков сверху-вниз, слева-направо
    boxes.sort(key=lambda b: (b[1], b[0]))

    # Подготовка кропов
    crops = []
    for (x, y, w, h) in boxes:
        y2 = min(y + h + PAD_DOWN, H)
        crop = img[y:y2, x:x + w]
        up = cv2.resize(crop, None, fx=UPSCALE, fy=UPSCALE, interpolation=cv2.INTER_CUBIC)
        crops.append(up)

    # OCR
    reader = get_reader(use_gpu=use_gpu)
    blocks: List[List[str]] = []

    for crop in crops:
        gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
        th = cv2.adaptiveThreshold(
            gray, 255,
            cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY_INV,
            blockSize=11, C=6
        )
        lines = reader.readtext(th, detail=0)  # список строк для кропа
        lines = [_norm(s) for s in lines] if lines else []
        blocks.append(lines)

    return blocks if blocks else [["Kein Text gefunden"]]

# === Форматирование под UI ===
def _blocks_to_ui_lines(blocks: List[List[str]]) -> List[str]:
    """
    Превращает блоки OCR в готовые строки для UI:
    DeviceName → 10.10.0.17
    DeviceName → IP- nicht gefunden
    """
    ui_lines: List[str] = []
    for lines in blocks:
        if not lines:
            # на всякий случай
            ui_lines.append("Unbekanntes Gerät → IP- nicht gefunden")
            continue

        device_name = lines[0].strip() or "Unbekanntes Gerät"
        ip = _find_first_ip(lines)
        ui = f"{device_name:20} → {ip if ip else 'IP- nicht gefunden'}"
        ui_lines.append(ui)
    return ui_lines

# === Публичные функции для вызова из UI ===
def extract_text_from_image(image_path: str, use_gpu: bool = False) -> List[str]:
    img = cv2.imread(image_path)
    blocks = _extract_blocks_from_image_np(img, use_gpu)
    return _blocks_to_ui_lines(blocks)
