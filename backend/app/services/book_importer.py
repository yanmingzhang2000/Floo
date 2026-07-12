"""
书籍抓取导入服务 —— 从 tingroom 站点批量导入英文经典读物到 learning_contents。

为什么单独放一个 service：
  - 抓取 + 解析 + 落库是一个完整的编排流程，不属于任何 router
  - 分层严格：I/O (fetch) 与纯解析 (parse) 完全解耦，方便测试和替换数据源
  - 未来接入其它站点（gutenberg / 双语站）时只需替换 parse_* 即可

数据源结构（tingroom /jingdian/{id}/）：
  - 目录页 `/jingdian/{book_id}/list.html`：<div class="text"> > <ol> > <li><a href="{cid}.html">Title</a></li>
  - 章节页 `/jingdian/{book_id}/{chapter_id}.html`：
      1. <div class="text" id="tt_text">：正文 <P> 段落，含 <a href="dict.qsbdc.com/word">
         内联链接和 <sup class="circle"><a href="#_w_N">N</a></sup> 上标编号
      2. <div id="wz_jx">：页脚编号词汇表，每个词一个 <div class="zc_boxl">，含
         <span class="danci"><a>word</a></span> 词形 + <td class="zhushi">释义 +
         <div class="liju"><li>例句</li></div>

版权：调用方必须确保只对已购买正版的用户开放（通过 UserBookAccess 白名单）。
"""
from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup, Tag
from sqlalchemy.orm import Session

from app.models import (
    BookChapter,
    BookChapterSegment,
    BookSeries,
    LearningContent,
)

log = logging.getLogger(__name__)

# 单章分段目标词数：语言学习节奏经验值，太长注意力涣散、太短失去上下文
SEGMENT_TARGET_WORDS = 450
SEGMENT_MIN_WORDS = 300  # 段末不足此阈值则合并到上一段，避免出现半句零头
# 抓取节流：连续请求间隔（秒），出于对来源站点的尊重
FETCH_INTERVAL_SEC = 0.5
# 请求 UA 加上项目标识，方便对方站点判断流量来源
USER_AGENT = "FlooEnglishApp/1.0 (educational; contact via app repo)"


@dataclass
class ChapterMeta:
    """目录页解析出的章节元信息。"""
    order_no: int          # 0=Introduction, 1=Chapter 1, ...
    title: str
    source_url: str        # 章节页 URL（绝对路径）


@dataclass
class LexiconItem:
    """页脚编号词汇表单条。"""
    word: str
    meaning: str
    example: str = ""      # 中英对照第一条例句拼成一行


@dataclass
class ParsedChapter:
    """章节页解析产物。"""
    title: str
    body_text: str                          # 纯文本正文（去掉所有 HTML 标签）
    lexicon: list[LexiconItem] = field(default_factory=list)


@dataclass
class BookMeta:
    """书籍元信息 —— 目录页顶部提取。"""
    name: str
    name_cn: Optional[str] = None
    author: Optional[str] = None
    description: Optional[str] = None


# =========================================================================
# I/O 层：只做网络请求，不做任何解析
# =========================================================================

def fetch_html(url: str, timeout: float = 10.0) -> str:
    """抓取指定 URL 的 HTML 文本。

    为什么单独封装：所有网络异常统一在这里处理，上层拿到的要么是 HTML 字符串
    要么直接抛出，语义清晰。tingroom 声明字符集为 utf-8，直接按此解码。
    """
    log.debug("fetch_html 开始 url=%s", url)
    with httpx.Client(
        timeout=timeout,
        headers={"User-Agent": USER_AGENT},
        follow_redirects=True,
    ) as client:
        resp = client.get(url)
        resp.raise_for_status()
        # tingroom Content-Type 头有时缺失 charset，httpx 会 fallback 到 ISO-8859-1
        # 直接强制 utf-8 解码，实测所有页面都是 utf-8
        resp.encoding = "utf-8"
        log.debug("fetch_html 成功 url=%s len=%s", url, len(resp.text))
        return resp.text


# =========================================================================
# 解析层：纯函数，输入 HTML 字符串，输出结构化数据
# =========================================================================

def parse_book_meta(toc_html: str) -> BookMeta:
    """从目录页顶部解析书名、作者、简介。

    Why：BookSeries 需要一个能展示给用户的中英文名+简介，从目录页 <h1> 和
    <div id="infoShort"> 抽取。tingroom 的书名格式通常是 "英文名+中文名" 混在一起，
    比如 "Rich Dad Poor Dad穷爸爸富爸爸"，这里粗略拆分即可。
    """
    soup = BeautifulSoup(toc_html, "lxml")

    # 书名：优先取 <h1> 里的 <a>；退化到 <title>
    raw_name = ""
    h1_link = soup.select_one("#focus_book_info h1 a")
    if h1_link:
        raw_name = h1_link.get_text(strip=True)
        log.debug("parse_book_meta h1 命中 raw_name=%s", raw_name)
    else:
        title_tag = soup.title
        if title_tag:
            raw_name = title_tag.get_text(strip=True).split("_")[0]
            log.debug("parse_book_meta 退化到 title raw_name=%s", raw_name)

    # 拆分中英文名：找到第一个中文字符的位置，前面是英文，后面是中文
    name_en, name_cn = _split_bilingual_title(raw_name)
    log.debug("parse_book_meta 拆分 en=%s cn=%s", name_en, name_cn)

    # 作者：<span> 里带链接的 <a>
    author = None
    author_tag = soup.select_one("#focus_book_info span a[href*='/writer/']")
    if author_tag:
        author = author_tag.get_text(strip=True)

    # 简介：优先取展开后的 infoLong，退化到 infoShort
    description = None
    long_desc = soup.select_one("#infoLong")
    short_desc = soup.select_one("#infoShort")
    if long_desc and long_desc.get_text(strip=True):
        description = long_desc.get_text(" ", strip=True)
    elif short_desc:
        description = short_desc.get_text(" ", strip=True)

    return BookMeta(
        name=name_en or raw_name or "Unknown Book",
        name_cn=name_cn,
        author=author,
        description=description,
    )


def _split_bilingual_title(raw: str) -> tuple[str, Optional[str]]:
    """把 "Rich Dad Poor Dad穷爸爸富爸爸" 拆成 ("Rich Dad Poor Dad", "穷爸爸富爸爸")。

    规则：从右向左扫描，找到第一个非中文字符的位置作为切点。
    """
    if not raw:
        return "", None
    # 中文字符范围（含常用符号）
    cn_pattern = re.compile(r"[\u4e00-\u9fff]")
    match = cn_pattern.search(raw)
    if not match:
        # 全英文
        return raw.strip(), None
    idx = match.start()
    en_part = raw[:idx].strip()
    cn_part = raw[idx:].strip()
    return en_part, cn_part or None


def parse_toc(toc_html: str, base_url: str) -> list[ChapterMeta]:
    """从目录页 HTML 抽取所有章节链接。

    tingroom 的目录页有两种：主页 `/jingdian/{id}/` 只列前 10 章，
    完整目录在 `/jingdian/{id}/list.html`。调用方应传 list.html 进来以拿到全量。
    """
    soup = BeautifulSoup(toc_html, "lxml")
    # list.html 的 <ol> 在 #tt_text 下；主页在 #book_detail 下
    ol = soup.select_one("#tt_text ol") or soup.select_one("#book_detail ol")
    if not ol:
        log.debug("parse_toc 未找到 <ol> 目录节点 base_url=%s", base_url)
        return []

    chapters: list[ChapterMeta] = []
    for order_no, li in enumerate(ol.find_all("li")):
        a = li.find("a")
        if not a or not a.get("href"):
            # 目录里可能有占位 "......"，跳过
            log.debug("parse_toc 跳过无链接 li idx=%s text=%s", order_no, li.get_text(strip=True))
            continue
        href = str(a["href"])
        title_attr = a.get("title")
        title = str(title_attr) if title_attr else a.get_text(strip=True)
        source_url = urljoin(base_url, href)
        chapters.append(ChapterMeta(
            order_no=len(chapters),  # 按有效条目重新编号
            title=title,
            source_url=source_url,
        ))
        log.debug("parse_toc 命中 order_no=%s title=%s url=%s", len(chapters) - 1, title, source_url)

    log.debug("parse_toc 共提取 %s 章", len(chapters))
    return chapters


def parse_chapter(chapter_html: str) -> ParsedChapter:
    """从章节页 HTML 抽取标题、正文、页脚词汇。

    正文与词汇混在同一个 <div class="text" id="tt_text"> 里，
    但词汇部分被 <div id="wz_jx"> 包起来。所以先从 tt_text 里剔除 wz_jx，
    剩下的就是纯正文。
    """
    soup = BeautifulSoup(chapter_html, "lxml")

    # 章节标题：<div class="title"><span>...</span></div>（页面上有多个 .title，用 showmain 内的）
    title = "Untitled"
    title_span = soup.select_one("#showmain .title span")
    if title_span:
        title = title_span.get_text(strip=True)
        log.debug("parse_chapter 标题=%s", title)

    tt_text = soup.select_one("#tt_text")
    if not tt_text:
        log.debug("parse_chapter 未找到 #tt_text 节点")
        return ParsedChapter(title=title, body_text="")

    # 抽取词汇表（在移除之前）
    wz_jx = tt_text.select_one("#wz_jx")
    lexicon = _parse_lexicon(wz_jx) if wz_jx else []
    log.debug("parse_chapter 词汇 count=%s", len(lexicon))

    # 从正文树里剔除词汇区、广告 div、图片装饰，其余转成纯文本
    body_text = _extract_body_text(tt_text)
    log.debug("parse_chapter 正文长度=%s 字符", len(body_text))

    return ParsedChapter(title=title, body_text=body_text, lexicon=lexicon)


def _extract_body_text(tt_text: Tag) -> str:
    """从 #tt_text 节点里提取纯正文，去掉词汇表、广告脚本、图片。

    为什么复制节点：BeautifulSoup 的 .decompose() 会修改原树，
    如果后续还要复用同一个 soup，会踩坑。这里 copy 后 decompose 安全。
    """
    from copy import copy
    # BeautifulSoup 不支持深拷贝 Tag，退化到重新 parse
    node = BeautifulSoup(str(tt_text), "lxml")

    # 剔除词汇区
    wz = node.select_one("#wz_jx")
    if wz:
        wz.decompose()

    # 剔除脚注上标编号（<sup class="circle"><a>N</a></sup>）
    for sup in node.select("sup.circle"):
        sup.decompose()

    # 剔除页内广告脚本区
    for script in node.find_all("script"):
        script.decompose()
    for ad in node.select("[id^='play_ggr']"):
        ad.decompose()

    # 剔除装饰图片（书末的 4.jpg 等）
    for img in node.find_all("img"):
        img.decompose()

    # 用 <P> 分段，段与段之间用换行分隔
    paragraphs: list[str] = []
    for p in node.find_all(["p", "P"]):
        # get_text 会保留 <BR> 之间的分隔，用 separator 参数确保 BR 变空格
        text = p.get_text(separator=" ", strip=True)
        if text:
            paragraphs.append(text)

    body = "\n\n".join(paragraphs)
    # 清理常见 HTML 实体残留和多余空白
    body = re.sub(r"[ \t]+", " ", body)
    body = re.sub(r"\n{3,}", "\n\n", body)
    return body.strip()


def _parse_lexicon(wz_jx: Tag) -> list[LexiconItem]:
    """解析 #wz_jx 里的编号词汇列表。

    每个词一个 <div class="zc_boxl">，里面：
      - <span class="danci"><a>word</a></span>：词形（可能是短语或屈折变形）
      - <td class="zhushi">释义</td>：词性 + 中文释义
      - <div class="liju"><ul><li>中英例句</li></ul></div>：例句
    """
    items: list[LexiconItem] = []
    for box in wz_jx.select(".zc_boxl"):
        word_tag = box.select_one(".danci a") or box.select_one(".danci")
        meaning_tag = box.select_one(".zhushi")
        example_tag = box.select_one(".liju li")

        if not word_tag or not meaning_tag:
            log.debug("_parse_lexicon 跳过不完整条目")
            continue

        word = word_tag.get_text(strip=True)
        meaning = meaning_tag.get_text(strip=True)
        example = example_tag.get_text(" ", strip=True) if example_tag else ""
        items.append(LexiconItem(word=word, meaning=meaning, example=example))

    return items


# =========================================================================
# 分段层：把长文本切成 400-500 词的学习段
# =========================================================================

def split_into_segments(text: str, target_words: int = SEGMENT_TARGET_WORDS) -> list[str]:
    """把整章正文按目标词数切成若干段，尽量在段落 / 句子边界切。

    切分策略：
      1. 先按空行拆成 paragraph 列表
      2. 累计 paragraph 直到词数超过 target_words，则收尾
      3. 若单个 paragraph 超过 1.5 * target_words，则内部按句号切
      4. 最后一段词数不足 SEGMENT_MIN_WORDS 时合并到上一段，避免"零头"
    """
    if not text.strip():
        log.debug("split_into_segments 空文本，返回空")
        return []

    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    segments: list[list[str]] = [[]]
    current_words = 0

    for para in paragraphs:
        para_words = _count_words(para)

        if para_words > target_words * 1.5:
            # 段太长，内部按句号切
            log.debug("split_into_segments 拆超长段 words=%s", para_words)
            for chunk in _split_long_paragraph(para, target_words):
                chunk_words = _count_words(chunk)
                if _should_start_new_segment(current_words, chunk_words, target_words) and segments[-1]:
                    segments.append([])
                    current_words = 0
                segments[-1].append(chunk)
                current_words += chunk_words
            continue

        # 判断是否开新段：既要看能不能装下，也要防止当前段太瘦弱就切
        if _should_start_new_segment(current_words, para_words, target_words) and segments[-1]:
            log.debug("split_into_segments 换段 current=%s add=%s", current_words, para_words)
            segments.append([])
            current_words = 0
        segments[-1].append(para)
        current_words += para_words

    # 尾段合并：如果最后一段不足门槛，并回上一段
    if len(segments) >= 2 and _count_words("\n\n".join(segments[-1])) < SEGMENT_MIN_WORDS:
        log.debug("split_into_segments 尾段过短，合并到上一段")
        tail = segments.pop()
        segments[-1].extend(tail)

    result = ["\n\n".join(seg) for seg in segments if seg]
    log.debug("split_into_segments 完成 段数=%s", len(result))
    return result


def _should_start_new_segment(current_words: int, add_words: int, target: int) -> bool:
    """判断是否应该开新段。

    Why 不只是 current + add > target：
      - 如果 current 只有零头（比如 4 词的标题行），强行切会造成小垃圾段
      - 如果 current 已经接近 target 一半以上，即使加进去会超但也在可接受范围
    规则：
      - 当前段不足最低门槛 SEGMENT_MIN_WORDS，一律不切
      - 否则用 target 判断
    """
    if current_words < SEGMENT_MIN_WORDS:
        return False
    return current_words + add_words > target


def _count_words(text: str) -> int:
    """简单按空格切词。对英文足够精确，不用 NLTK 减少依赖。"""
    return len(text.split())


def _split_long_paragraph(para: str, target_words: int) -> list[str]:
    """把超长段落按句号切成 ~target_words 的小块。"""
    sentences = re.split(r"(?<=[.!?])\s+", para)
    chunks: list[list[str]] = [[]]
    current = 0
    for sent in sentences:
        w = _count_words(sent)
        if current + w > target_words and chunks[-1]:
            chunks.append([])
            current = 0
        chunks[-1].append(sent)
        current += w
    return [" ".join(c) for c in chunks if c]


# =========================================================================
# 编排层：串起 fetch → parse → 落库
# =========================================================================

@dataclass
class ImportSummary:
    """一次 import 的执行结果，供 admin 接口返回。"""
    series_id: int
    series_name: str
    total_chapters: int
    imported_chapters: int
    skipped_chapters: int          # 已存在跳过的
    failed_chapters: list[str]     # 失败的章节 URL + 原因
    total_segments: int


def import_book(db: Session, source_url: str, granted_by: str = "admin") -> ImportSummary:
    """从目录页 URL 开始，完整抓取并落库一本书。

    幂等策略：
      - BookSeries.source_url 已存在则复用；不重复插入
      - BookChapter(series_id, order_no) 已存在则跳过该章
    失败降级：单章解析失败不阻塞其余章节，记录到 failed_chapters 返回。

    Why 事务粒度：每章单独 commit，避免最后一章失败导致前面白抓。
    """
    log.debug("import_book 开始 source_url=%s", source_url)

    # 1. 目录页：解析书籍元信息 + 章节列表
    #    - 索引页 /jingdian/{id}/ 有作者/简介但只列前 10 章
    #    - list.html 有全量章节但没有作者
    #    所以两页都抓：索引页取元信息，list.html 取章节
    index_url = source_url if not source_url.endswith("/list.html") else source_url.rsplit("/", 1)[0] + "/"
    toc_url = _join_list_url(index_url) if not source_url.endswith("/list.html") else source_url

    index_html = fetch_html(index_url)
    book_meta = parse_book_meta(index_html)

    toc_html = fetch_html(toc_url) if toc_url != index_url else index_html
    chapters_meta = parse_toc(toc_html, base_url=toc_url)

    if not chapters_meta:
        log.debug("import_book 目录空，抛错")
        raise ValueError(f"目录页无章节：{toc_url}")

    # 2. BookSeries：查/建
    series = db.query(BookSeries).filter(BookSeries.source_url == source_url).first()
    if series:
        log.debug("import_book series 已存在 id=%s，复用", series.series_id)
    else:
        series = BookSeries(
            name=book_meta.name,
            name_cn=book_meta.name_cn,
            author=book_meta.author,
            source_site="tingroom",
            source_url=source_url,
            description=book_meta.description,
            total_chapters=len(chapters_meta),
        )
        db.add(series)
        db.commit()
        db.refresh(series)
        log.debug("import_book 新建 series id=%s name=%s", series.series_id, series.name)

    # 3. 逐章处理
    imported = 0
    skipped = 0
    failed: list[str] = []
    total_segments = 0

    for meta in chapters_meta:
        try:
            outcome = _import_one_chapter(db, series, meta)
        except Exception as e:
            # 单章失败不阻塞：记下来继续下一章
            log.warning("import_book 单章失败 url=%s err=%s", meta.source_url, e)
            failed.append(f"{meta.source_url} :: {type(e).__name__}: {e}")
            continue

        if isinstance(outcome, str) and outcome == "skipped":
            log.debug("import_book 章节已存在跳过 order_no=%s", meta.order_no)
            skipped += 1
        elif isinstance(outcome, int):
            imported += 1
            total_segments += outcome

    # 更新 series 总章节数（可能之前 total_chapters 是 0）
    new_total = db.query(BookChapter).filter(BookChapter.series_id == series.series_id).count()
    series.total_chapters = new_total  # type: ignore[assignment]
    db.commit()

    log.debug(
        "import_book 完成 series_id=%s imported=%s skipped=%s failed=%s",
        series.series_id, imported, skipped, len(failed),
    )
    return ImportSummary(
        series_id=series.series_id,  # type: ignore[arg-type]
        series_name=series.name,  # type: ignore[arg-type]
        total_chapters=len(chapters_meta),
        imported_chapters=imported,
        skipped_chapters=skipped,
        failed_chapters=failed,
        total_segments=total_segments,
    )


def _join_list_url(source_url: str) -> str:
    """把 /jingdian/{id}/ 补成 /jingdian/{id}/list.html。"""
    if source_url.endswith("/"):
        return source_url + "list.html"
    return source_url + "/list.html"


def _import_one_chapter(db: Session, series: BookSeries, meta: ChapterMeta) -> int | str:
    """处理单章：抓取 → 解析 → 落库整章内容 → 分段落库。

    返回值：
      - "skipped"：该章已存在，未做任何变更
      - int：新导入并成功切分的段落数
    """
    # 幂等：同一章 (series_id, order_no) 已存在则跳过
    existing = (
        db.query(BookChapter)
        .filter(BookChapter.series_id == series.series_id, BookChapter.order_no == meta.order_no)
        .first()
    )
    if existing:
        return "skipped"

    # 节流
    import time
    time.sleep(FETCH_INTERVAL_SEC)

    html = fetch_html(meta.source_url)
    parsed = parse_chapter(html)
    if not parsed.body_text:
        # 空章节没意义，抛错让上层记 failed
        raise ValueError("正文为空")

    # 词汇转为 learning_contents.key_words 期望的 shape：
    # [{"word": str, "phonetic": str, "meaning": str, "is_phrase": bool}]
    key_words_payload = [
        {
            "word": item.word,
            "phonetic": "",  # tingroom 不提供音标，前端点词查有道时按需补
            "meaning": item.meaning,
            "example": item.example,
            "is_phrase": " " in item.word,
        }
        for item in parsed.lexicon
    ]

    # 1. 整章 learning_content
    whole_content = LearningContent(
        creator_type=0,
        user_id=None,
        difficulty_level="hard",         # 原著文本统一标记 hard
        theme_type="book_richdad",       # 用 theme 做书目分类
        title=f"{series.name} - {parsed.title}",
        content_text=parsed.body_text,
        translation=None,                # tingroom 目录页有段落级双语，但章节页无；MVP 先不塞
        key_words=json.dumps(key_words_payload, ensure_ascii=False),
        content_type="article",
    )
    db.add(whole_content)
    db.flush()
    log.debug("_import_one_chapter 整章 content_id=%s", whole_content.content_id)

    # 2. BookChapter
    chapter = BookChapter(
        series_id=series.series_id,
        order_no=meta.order_no,
        title=parsed.title,
        source_url=meta.source_url,
        content_id=whole_content.content_id,
        word_count=_count_words(parsed.body_text),
    )
    db.add(chapter)
    db.flush()
    log.debug("_import_one_chapter chapter_id=%s order_no=%s", chapter.chapter_id, meta.order_no)

    # 3. 分段 learning_contents + BookChapterSegment
    segments = split_into_segments(parsed.body_text)
    for seg_no, seg_text in enumerate(segments):
        # 分段词汇：只保留在该段落中出现的词，避免整章词汇塞给每一段导致噪音
        seg_lexicon = _filter_lexicon_for_segment(key_words_payload, seg_text)
        seg_content = LearningContent(
            creator_type=0,
            user_id=None,
            difficulty_level="hard",
            theme_type="book_richdad",
            title=f"{series.name} - {parsed.title} - 段 {seg_no + 1}",
            content_text=seg_text,
            translation=None,
            key_words=json.dumps(seg_lexicon, ensure_ascii=False),
            content_type="article",
        )
        db.add(seg_content)
        db.flush()

        seg_row = BookChapterSegment(
            chapter_id=chapter.chapter_id,
            order_no=seg_no,
            content_id=seg_content.content_id,
            word_count=_count_words(seg_text),
        )
        db.add(seg_row)

    db.commit()
    log.debug("_import_one_chapter 章节落库完成 order_no=%s segments=%s", meta.order_no, len(segments))
    return len(segments)


def _filter_lexicon_for_segment(all_words: list[dict], seg_text: str) -> list[dict]:
    """从整章词汇里筛出该段真正包含的词。

    Why：整章有 30-50 个编号词汇，如果每段都塞全部会污染学习焦点。
    简单大小写不敏感的子串匹配足够，因为词汇本身就是原文里的词形。
    """
    lower = seg_text.lower()
    kept = [w for w in all_words if w["word"].lower() in lower]
    return kept
