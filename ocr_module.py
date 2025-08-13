import cv2
import easyocr
import numpy as np
from typing import List
import re

# Настройки
TARGET_COLOR_HEX = '#CACCD9'
DELTA = 12
PAD_DOWN = 40
UPSCALE = 4
AREA_MIN = 2000
ASPECT_MIN, ASPECT_MAX = 0.7, 10.0
IP_PATTERN = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'

# HEX to BGR
def hex2bgr(h):
    return np.array([int(h[5:7],16), int(h[3:5],16), int(h[1:3],16)], dtype=np.uint8)

# General text regognition tool
def _extract_text_from_image_np(img: np.ndarray, use_gpu: bool = False) -> List[str]:
    if img is None:
        return ["Error during image loading"]

    H, W = img.shape[:2]

    # Creating color mask
    target = hex2bgr(TARGET_COLOR_HEX)
    lower = np.clip(target - DELTA, 0, 255)
    upper = np.clip(target + DELTA, 0, 255)
    mask_raw = cv2.inRange(img, lower, upper)

    # Morphology
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    mask = cv2.morphologyEx(mask_raw, cv2.MORPH_CLOSE, kernel, iterations=2)

    # Finging contours of hardware elements
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    boxes = []
    for c in contours:
        x, y, w, h = cv2.boundingRect(c)
        area = w * h
        aspect = w / float(h)
        if area > AREA_MIN and ASPECT_MIN <= aspect <= ASPECT_MAX:
            boxes.append((x, y, w, h))

    if not boxes:
        return ["Устройства не обнаружены"]

    # Sorting of elemets up-to-down; left-to-right
    boxes.sort(key=lambda b: (b[1], b[0]))

    # Cropping boxes for text recognition
    crops = []
    for (x, y, w, h) in boxes:
        y2 = min(y + h + PAD_DOWN, H)
        crop = img[y:y2, x:x + w]
        up = cv2.resize(crop, None, fx=UPSCALE, fy=UPSCALE, interpolation=cv2.INTER_CUBIC)
        crops.append(up)

    # OCR
    reader = easyocr.Reader(['en'], gpu=use_gpu)
    results = []

    for crop in crops:
        gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
        th = cv2.adaptiveThreshold(
            gray, 255,
            cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY_INV,
            blockSize=11, C=6
        )
        lines = reader.readtext(th, detail=0)
        if lines:
            joined = " ".join(lines)
            results.append(joined)

    return results if results else ["Текст не найден"]

# With image path
def extract_text_from_image(image_path: str, use_gpu: bool = False) -> List[str]:
    img = cv2.imread(image_path)
    return _extract_text_from_image_np(img, use_gpu)

# OCR from memory
def extract_text_from_array(img_array: np.ndarray, use_gpu: bool = False) -> List[str]:
    if img_array.ndim != 3 or img_array.shape[2] != 3:
        return ["Ошибка: ожидается RGB изображение (HxWx3)"]
    return _extract_text_from_image_np(img_array, use_gpu)