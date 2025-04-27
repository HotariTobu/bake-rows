# -*- coding: utf-8 -*-
"""
2025-04-18_ota_mitani-helper_4.py
  – SBERT + LOF + 強化ルール (文字化け / 型番 / 英語フレーズ) 改良版
"""

from __future__ import annotations
import argparse
from pathlib import Path
from collections.abc import Sequence
import numpy as np
import polars as pl
import regex as re
from sentence_transformers import SentenceTransformer
from sklearn.neighbors import LocalOutlierFactor
from langdetect import detect, DetectorFactory

DetectorFactory.seed = 0

type ArrayLike = Sequence | np.ndarray | pl.Series

# ---------- SBERT ---------------------------------------------------
MODEL = SentenceTransformer("paraphrase-multilingual-mpnet-base-v2")

# ---------- 文字種パターン ------------------------------------------
KANJI = r'\p{Script=Han}'
KANA  = r'\p{Hiragana}|\p{Katakana}'
HALF_KATA_RGX = re.compile(r'[\uFF61-\uFF9F]')

CTRL_RGX  = re.compile(r'[\x00-\x08\x0B\x0C\x0E-\x1F]')
NON_BMP   = re.compile(r'[\U00010000-\U0010FFFF]')
JP_RGX    = re.compile(fr'[{KANA}{KANJI}]')
ASCII_PRT = re.compile(r'[ -~]')

GARBLED_CHARS = "ÂÃÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖØÙÚÛÜÝÞßäàáâãåæçèéêëìíîïðñòóôõöøùúûüýÿ¤¢¿½¼¾"

# ---------- 型番用 ---------------------------------------------------
PART_DELIMS = r"\-_/\\"
PART_RGX = re.compile(fr'^[A-Za-z0-9{PART_DELIMS}]{{4,30}}$', flags=re.ASCII)
# 容量・サイズ単位 (除外対象から外す)  # ★updated
UNIT_SUFFIX = ("gb", "tb", "mb", "kb", "mm", "cm", "kg", "g")

# 代表的ブランド (除外対象から外す)    # ★updated
BRANDS = (
    "apple", "oppo", "brother", "canon", "sony", "panasonic", "sharp",
    "twinbird", "toshiba", "lenovo", "asus", "dell", "hp"
)

# ---------- 英語フレーズ用 ------------------------------------------
WH_WORDS  = {"how", "what", "why", "where", "when", "who"}
ENG_HINTS = {"wiki", "documentary", "lyrics", "translation", "meaning"}

# --------------------------------------------------------------------
# 1. ファイル読み込み
# --------------------------------------------------------------------
def load_files(files: list[str], head: int | None = None) -> pl.DataFrame:
    frames = []
    for f in files:
        p = Path(f)
        if not p.exists():
            print(f"[WARN] {f} not found. skip.")
            continue
        if p.suffix.lower() == ".csv":
            df = pl.read_csv(p, infer_schema_length=0)
        elif p.suffix.lower() in (".xlsx", ".xls"):
            df = pl.read_excel(p)
        else:
            print(f"[WARN] unsupported {p.suffix}. skip.")
            continue
        df = df.select([
            pl.col(df.columns[0]).cast(pl.Utf8).alias("keyword"),
            pl.col(df.columns[1]).cast(pl.Int64).alias("count")
        ])
        if head:
            df = df.head(head)
        frames.append(df)
    if not frames:
        raise RuntimeError("no readable files")
    return pl.concat(frames)

# --------------------------------------------------------------------
# 2. 文字化け判定
# --------------------------------------------------------------------
def is_garbled(s: str) -> bool:
    if not s or not s.strip():
        return True
    L = len(s)
    weird = s.count('�') + len(CTRL_RGX.findall(s)) + len(NON_BMP.findall(s))
    if weird / L > 0.05:
        return True
    if any(ch in GARBLED_CHARS for ch in s):
        return True
    jp_ratio = len(JP_RGX.findall(s)) / L
    ascii_ratio = len(ASCII_PRT.findall(s)) / L
    if HALF_KATA_RGX.search(s) and jp_ratio < 0.2:
        return True
    if jp_ratio < 0.05 and ascii_ratio < 0.4:
        return True
    return False

# --------------------------------------------------------------------
# 3. 型番（品番）判定  ★updated
# --------------------------------------------------------------------
def is_part_number(s: str) -> bool:
    if not s:
        return False
    s_strip = s.strip()
    low = s_strip.lower()

    # 容量・サイズ(128gb 等)は除外しない
    for unit in UNIT_SUFFIX:
        if low.endswith(unit) and low[:-len(unit)].isdigit():
            return False

    # ブランドを含むなら型番扱いしない
    if any(b in low for b in BRANDS):
        return False

    # 日本語を含むなら型番ではない
    if re.search(fr'[{KANA}{KANJI}]', s_strip):
        return False

    # パターン一致 + 英字 & 数字を両方含む
    if PART_RGX.fullmatch(s_strip) and re.search(r'[A-Za-z]', s_strip) and re.search(r'\d', s_strip):
        return True
    return False

# --------------------------------------------------------------------
# 4. “無関係な英語フレーズ” 判定  ★updated
# --------------------------------------------------------------------
def is_irrelevant_english_phrase(s: str) -> bool:
    if s.count(' ') < 2:        # 3 語未満は処理しない
        return False
    try:
        lang = detect(s)
    except Exception:
        return False
    if lang != 'en':
        return False

    tokens = [t.lower() for t in s.split()]

    # 疑問詞で始まる
    if tokens[0] in WH_WORDS:
        return True

    # wiki / documentary / lyrics / translation などを含む
    if any(t in ENG_HINTS for t in tokens):
        return True

    return False     # ★ “英語だけで 3 語以上” という条件は削除

# --------------------------------------------------------------------
# 5. SBERT + LOF
# --------------------------------------------------------------------
def lof_scores(texts: list[str], n_neighbors: int = 20) -> np.ndarray:
    emb = MODEL.encode(texts, batch_size=64, normalize_embeddings=True,
                       show_progress_bar=False)
    lof = LocalOutlierFactor(n_neighbors=n_neighbors, metric="cosine", novelty=False)
    lof.fit(emb)
    return -lof.negative_outlier_factor_

# --------------------------------------------------------------------
# 6. フラグ付与
# --------------------------------------------------------------------
def add_flags(df: pl.DataFrame, top_percent: float = 5.0) -> pl.DataFrame:
    kws = df["keyword"].to_list()
    scores = lof_scores(kws)
    thr = np.percentile(scores, 100 - top_percent)

    flags = []
    for kw, sc in zip(kws, scores):
        flag = (
            is_garbled(kw) or
            is_part_number(kw) or
            is_irrelevant_english_phrase(kw) or
            sc > thr
        )
        flags.append("除外候補" if flag else "")

    if len(df.columns) >= 3:
        return df.with_columns(pl.Series(name=df.columns[2], values=flags))
    return df.with_columns(pl.Series(name="flag", values=flags))

# --------------------------------------------------------------------
# 7. API
# --------------------------------------------------------------------
def score_sentences(
    sentences: ArrayLike,
    counts: ArrayLike,
    top_percent: float,
) -> ArrayLike:
    df = pl.DataFrame({"keyword": sentences, "count": counts})
    res = add_flags(df, top_percent)

    flags: pl.Series

    if 'flag' in res.columns:
        flags = res['flag']
    else:
        flags = res[res.columns[2]]

    return [1 if flag else 0 for flag in flags]

# --------------------------------------------------------------------
# 8. CLI
# --------------------------------------------------------------------
def main() -> None:
    ap = argparse.ArgumentParser(description="キーワード除外候補検出 (SBERT+LOF v4)")
    ap.add_argument("files", nargs="+")
    ap.add_argument("--head", type=int)
    ap.add_argument("--top-percent", type=float, default=5.0)
    ap.add_argument("--out", type=str)
    args = ap.parse_args()

    df = load_files(args.files, args.head)
    res = add_flags(df, args.top_percent)
    print(res)

    if args.out:
        res.write_csv(args.out)
        print("[INFO] saved:", args.out)

if __name__ == "__main__":
    main()
