# OCR 提取国标文本：问题与解决方案

本文记录把「全国茶叶标准化技术委员会」的国标 PDF 提取成可检索知识文本的完整踩坑过程。
核心链路：**下载 PDF → 渲染成图片 → RapidOCR 识别 → 清洗 → 切块 → 入库**。

> 目标读者：想要贡献茶叶知识、或复现国标导入流程的开发者。

---

## 一、整体流程

```bash
# 1. 批量处理（下载 → 转图 → OCR → 输出 markdown）
.venv\Scripts\python scripts/batch_process.py

# 2. 用 DeepSeek 从 OCR 文本提取结构化信息
.venv\Scripts\python scripts/extract_enrich.py --all

# 3. 重建向量库
.venv\Scripts\python scripts/build_index.py
```

涉及的关键脚本：

| 脚本 | 作用 |
|------|------|
| `pdf_to_images.py` | PDF 每页渲染成 PNG（pymupdf） |
| `ocr_pdfs.py` | 图片逐页 OCR，输出 markdown |
| `chunking.py` | 加载 + 清洗 + 按章节切块 |
| `build_index.py` | 向量化并写入 Chroma |

---

## 二、遇到的问题与解决方案

### 问题 1：国标 PDF 文字层是 CID 乱码，无法直接提取文本

**现象**：用 `pypdf` 提取，得到 `/G21/G22/G23` 这种字形编号；用 `pymupdf` 提取，得到乱码标点和无关字符。

**原因**：国标 PDF 并非扫描件（有文字层），但字体用了**自定义 CID 编码**，普通 PDF 文本提取器无法映射成可读汉字。

**解决**：放弃「直接提取文本」这条路，改用 **OCR**——用 `pymupdf` 把每页渲染成高清 PNG（dpi=300），再用 OCR 引擎识别图片。

```python
import pymupdf
doc = pymupdf.open(pdf)
for i in range(len(doc)):
    pix = doc[i].get_pixmap(dpi=300)
    pix.save(f"page_{i+1:03d}.png")
```

---

### 问题 2：PaddleOCR / PP-StructureV3 装不上

**现象**：`pip install paddlepaddle` 报 `No matching distribution found`。

**原因**：PP-StructureV3（版面分析表格识别）依赖 `paddlepaddle`，而 paddlepaddle 最高只支持 **Python 3.12**，当前环境是 Python 3.14。

**解决**：改用 **`rapidocr-onnxruntime`**——它基于 `onnxruntime`（本项目已装、兼容 3.14），对中文标准文本识别质量足够好。

```bash
pip install rapidocr-onnxruntime
```

> 教训：选 OCR 引擎前先确认它依赖的深度学习框架是否支持你的 Python 版本。

---

### 问题 3：Windows 终端 GBK 编码，print 中文/emoji 报错

**现象**：`print("📄")` 报 `UnicodeEncodeError: 'gbk' codec can't encode character`。

**原因**：Windows 终端默认 GBK 编码，Python stdout 输出 emoji 或某些中文会失败。

**解决**：在 `config.py` 顶部强制 stdout/stderr 用 UTF-8：

```python
import sys
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")
```

---

### 问题 4：封面、前言页产生大量噪声

**现象**：封面和前言页有「红茶」「国家标准」等通用词，在每个标准里重复出现，向量相似度虚高，把真正有答案的正文块挤出检索 top-k。

**原因**：国标结构固定——第 1 页封面、第 2 页前言，第 3 页才是正文（「1 范围」）。

**解决**：OCR 阶段**跳过前 2 页**，从第 3 页正文开始识别：

```python
SKIP_PAGES = 2  # 国标：第1页封面、第2页前言
pages = pages[SKIP_PAGES:]
```

这个改动比「正则清洗封面内容」可靠得多——封面和前言直接不进 OCR，噪声从源头消除。

---

### 问题 5：表格被 OCR 拆成碎片，抢占检索排序

**现象**：感官品质表、理化指标表被 OCR 拆成几十个短单元格（「松烟香」「醇厚」等词散落），这些碎片含关键词、数量多，抢占检索排序。

**原因**：固定字数切块会把表格拆碎。

**解决**：**按章节号切块**（国标是条款式结构），表格跟随它所属的章节整体保留，不再被二次切碎：

```python
_CHAPTER_RE = re.compile(r"^(\d+(?:\.\d+)*)\s*[一-鿿]")  # 匹配 1 / 1.1 / 3.1 / 4.2.1 等
```

---

### 问题 6：「规范性引用文件」整章无价值

**现象**：每个标准都有一段「2 规范性引用文件」，列出大段 GB 编号（GB/T 191、GB 2762…），对问答零价值。

**解决**：清洗阶段识别到该标题，直到下一个正文章节（3 产品 / 4 要求…）之前的内容全部丢弃：

```python
if re.match(r"^2?\s*规范性引用文件", s):
    in_ref_section = True
    continue
```

---

### 问题 7：向量检索对专有名词（茶名）命中率低

**现象**：搜「铁观音」，排前面的反而是「工夫红茶」「小种红茶」文档；正确的铁观音文档排到第 13 位。

**原因**：`bge-m3` 向量模型对**短查询专有名词**的精确匹配能力弱，倾向于匹配更宽泛的语义（「铁观音」和「红茶」在向量空间里反而更近）。

**解决**：实现**混合检索**——向量检索 + 关键词检索（用茶名词典做子串匹配），关键词命中的排最前：

```python
# 关键词路：全库扫描含茶名的 chunk，按命中次数排序
# 向量路：语义相似度 top-N，覆盖同义/宽泛问题
# 两路合并去重，关键词命中在前
```

> 这是 RAG 效果从「不可用」到「大部分准确」的关键一步。

---

### 问题 8：文件名含 `/` 导致下载路径断裂

**现象**：批量下载时，标准号「GB/T 14456.2」里的 `/` 被 Windows 当成路径分隔符，生成 `GB\T14456...` 子目录，下载失败。

**解决**：生成安全文件名时清理非法字符：

```python
no = std_no_of(title).replace("/", "").replace(" ", "")
```

---

### 问题 9：全角连字符「－」导致标准号正则匹配失败

**现象**：「肉桂」标准的标准号提取为空，因为原标题里是 `GB/T 30357.5－2015`（全角 `－`，U+FF0D），普通 `-\d{4}` 正则匹配不到。

**解决**：正则同时兼容三种连字符：

```python
re.search(r"GB\s*/?\s*T?\s*\d+(?:\.\d+)?\s*[-－—]\s*\d{4}", title)
```

---

### 问题 10：单个标准「图片过大」OCR 失败

**现象**：信阳毛尖茶（GB/T 22737-2008）报 `Overly large image`，OCR 失败。

**原因**：某页渲染后图片尺寸超出 OCR 引擎限制。

**解决**：暂未处理（遗留项）。方案是对超限页单独降低 DPI 或分块识别。

---

## 三、经验总结

1. **先确认 PDF 是「文字版」还是「扫描版」**——文字版也可能因 CID 编码而不可提取，别急着相信提取结果。
2. **国标结构固定，利用结构规律**——跳过封面/前言、过滤引用文件清单、按章节切块，都是利用国标「条款式」结构的确定性，比通用清洗可靠得多。
3. **OCR 引擎选型先看 Python 版本兼容性**——深度学习框架（paddlepaddle）对最新 Python 的适配往往滞后。
4. **专有名词检索要上混合检索**——纯向量检索对「铁观音」这种专有名词天然吃亏，关键词路是必要的补充。
5. **宁缺毋滥**——国标里「茶多酚」「咖啡碱」大多是限量指标（≤多少），不是含量数值，提取时不要硬凑，没有明确数值的成分宁可留空。
