# 토크나이저 처음부터 만들기

> 🇰🇷 이 문서는 한국어 번역본입니다(ELI5 스타일). 원문: [en.md](en.md)

> 레슨 01이 장난감을 주었다면, 이 레슨은 무기를 줍니다.

**유형:** Build
**언어:** Python
**선수 지식:** 페이즈 10, 레슨 01 (토크나이저: BPE, WordPiece, SentencePiece)
**소요 시간:** 약 90분

## 학습 목표

- 유니코드, 공백 정규화, 특수 토큰을 처리하는 프로덕션급 BPE 토크나이저 만들기
- 바이트 수준 폴백을 구현해 이모지, CJK(한중일), 코드를 포함한 어떤 입력도 미지 토큰 없이 인코딩하기
- BPE 병합을 적용하기 전에 단어 경계에서 텍스트를 나누는 사전 토큰화 정규식 패턴 추가하기
- 말뭉치로 커스텀 토크나이저를 학습시키고 다국어 텍스트에서 tiktoken과 압축률을 비교 평가하기

## 문제 상황

레슨 01의 BPE 토크나이저는 영어 텍스트에서는 잘 작동합니다. 이제 일본어를 던져 보세요. 이모지는요? 탭과 공백이 섞인 Python 코드는요?

무너집니다.

BPE가 틀려서가 아닙니다 — 구현이 불완전해서입니다. 프로덕션 토크나이저는 어떤 인코딩의 날것 바이트도 처리하고, 나누기 전에 유니코드를 정규화하고, 절대 병합되지 않는 특수 토큰을 관리하고, 사전 토큰화를 서브워드 분할과 연결하고, 15조 토큰을 처리하는 학습 파이프라인의 병목이 되지 않을 만큼 빠릅니다.

GPT-2의 토크나이저는 50,257개 토큰입니다. Llama 3는 128,256개. GPT-4는 약 100,000개. 장난감 숫자가 아닙니다. 그 어휘 뒤에 있는 병합 테이블은 수백 기가바이트의 텍스트로 학습됐고, 주변 장치들 — 정규화, 사전 토큰화, 특수 토큰 주입, 챗 템플릿 포매팅 — 이야말로 "hello world"를 다루는 토크나이저와 인터넷 전체를 다루는 토크나이저를 가르는 것입니다.

여러분은 그 장치를 만들 것입니다.

## 핵심 개념

### 전체 파이프라인

프로덕션 토크나이저는 알고리즘 하나가 아닙니다. 각기 다른 문제를 푸는 다섯 단계의 파이프라인입니다.

```mermaid
graph LR
    A[날것 텍스트] --> B[정규화]
    B --> C[사전 토큰화]
    C --> D[BPE 병합]
    D --> E[특수 토큰]
    E --> F[토큰 ID]

    style A fill:#1a1a2e,stroke:#e94560,color:#fff
    style B fill:#1a1a2e,stroke:#e94560,color:#fff
    style C fill:#1a1a2e,stroke:#e94560,color:#fff
    style D fill:#1a1a2e,stroke:#e94560,color:#fff
    style E fill:#1a1a2e,stroke:#e94560,color:#fff
    style F fill:#1a1a2e,stroke:#e94560,color:#fff
```

각 단계의 고유한 임무:

| 단계 | 하는 일 | 중요한 이유 |
|-------|-------------|----------------|
| 정규화 | NFKC 유니코드, 소문자화 선택, 악센트 제거 선택 | fi 합자(U+FB01)가 "fi"(두 문자)가 된다. 이게 없으면 같은 단어가 다른 토큰을 받는다. |
| 사전 토큰화 | BPE 전에 텍스트를 조각으로 나눈다 | BPE가 단어 경계를 가로지르며 병합하는 것을 막는다. "the cat"이 절대 토큰 "e c"을 만들면 안 된다. |
| BPE 병합 | 학습된 병합 규칙을 바이트 시퀀스에 적용 | 핵심 압축. 날것 바이트를 서브워드 토큰으로 바꾼다. |
| 특수 토큰 | [BOS], [EOS], [PAD], 챗 템플릿 마커를 주입 | 이 토큰들은 고정 ID를 가진다. 절대 BPE 병합에 참여하지 않는다. 모델이 구조를 위해 필요로 한다. |
| ID 대응 | 토큰 문자열을 정수 ID로 변환 | 모델은 문자열이 아니라 정수를 본다. |

### 바이트 수준 BPE

레슨 01의 토크나이저는 UTF-8 바이트 위에서 동작했습니다. 옳은 선택이었죠. 하지만 중요한 것을 하나 건너뛰었습니다: 그 바이트들이 유효한 UTF-8이 아니면 어떻게 될까요?

바이트 수준 BPE는 모든 가능한 바이트 값(0-255)을 유효한 토큰으로 취급해 이 문제를 풉니다. 기본 어휘가 정확히 256개입니다. 어떤 파일이든 — 텍스트, 이진, 손상된 것까지 — 미지 토큰 없이 토큰화할 수 있습니다.

GPT-2는 한 가지 트릭을 얹었습니다: 각 바이트를 출력 가능한 유니코드 문자로 대응시켜 어휘가 사람이 읽을 수 있게 유지한 것입니다. 바이트 0x20(공백)이 그 매핑에서는 문자 "G"가 됩니다. 순전히 보기 좋게 하려는 것일 뿐입니다. 알고리즘은 아무래도 상관없습니다.

진짜 힘은 여기 있습니다: 바이트 수준 BPE는 지구상의 모든 언어를 다룹니다. 중국어 문자는 각각 UTF-8로 3바이트입니다. 일본어는 3~4바이트일 수 있습니다. 아랍어, 데바나가리, 이모지 — 전부 그냥 바이트 시퀀스입니다. BPE 알고리즘은 이 바이트 시퀀스들에서 영어 ASCII 바이트에서와 정확히 같은 방식으로 패턴을 찾습니다.

### 사전 토큰화

BPE가 텍스트를 만지기 전에 조각으로 나눠야 합니다. 병합 알고리즘이 단어 경계를 넘는 토큰을 만드는 것을 막아 줍니다.

GPT-2는 정규식 패턴으로 텍스트를 나눕니다:

```
'(?:[sdmt]|ll|ve|re)| ?\p{L}+| ?\p{N}+| ?[^\s\p{L}\p{N}]+|\s+(?!\S)|\s+
```

이 패턴은 축약형("don't"가 "don" + "'t"로 분리), 앞 공백을 붙일 수 있는 단어, 숫자, 구두점, 공백에서 나눕니다. 앞 공백은 단어에 붙은 채 유지됩니다 — 그래서 "the cat"이 ["the", " ", "cat"]이 아니라 [" the", " cat"]이 됩니다.

Llama는 SentencePiece를 쓰는데, 정규식을 아예 건너뜁니다. 날것 바이트 스트림을 하나의 긴 시퀀스로 취급하고 경계 판단을 BPE 알고리즘에 맡깁니다. 더 단순하지만 BPE에 단어를 넘는 토큰을 만들 자유를 더 많이 줍니다.

이 선택은 중요합니다. GPT-2의 정규식은 토크나이저가 한 단어 끝의 "the"와 다음 단어 시작의 "the"를 병합해야 한다고 학습하는 것을 막습니다. SentencePiece는 이를 허용하는데, 때로 더 효율적인 압축을 내지만 토큰의 해석력은 떨어집니다.

### 특수 토큰

모든 프로덕션 토크나이저는 구조 표시자를 위한 토큰 ID를 예약해 둡니다:

| 토큰 | 용도 | 사용처 |
|-------|---------|---------|
| `[BOS]` / `<s>` | 시퀀스의 시작 | Llama 3, GPT |
| `[EOS]` / `</s>` | 시퀀스의 끝 | 모든 모델 |
| `[PAD]` | 배치 정렬용 패딩 | BERT, T5 |
| `[UNK]` | 미지 토큰 (바이트 수준 BPE는 이것을 제거) | BERT, WordPiece |
| `<\|im_start\|>` | 챗 메시지 경계 시작 | ChatGPT, Qwen |
| `<\|im_end\|>` | 챗 메시지 경계 끝 | ChatGPT, Qwen |
| `<\|user\|>` | 사용자 턴 표시 | Llama 3 |
| `<\|assistant\|>` | 어시스턴트 턴 표시 | Llama 3 |

특수 토큰은 절대 BPE로 쪼개지지 않습니다. 병합 알고리즘이 돌기 전에 정확히 일치하는지 확인되고, 고정 ID로 치환되며, 주변 텍스트는 평소처럼 토큰화됩니다.

### 챗 템플릿

대부분의 사람들이 헷갈리고 대부분의 구현이 무너지는 지점입니다.

챗 모델에 메시지를 보내면 API는 메시지 목록을 받습니다:

```
[
  {"role": "system", "content": "You are helpful."},
  {"role": "user", "content": "Hello"},
  {"role": "assistant", "content": "Hi there!"}
]
```

모델은 JSON을 보지 않습니다. 평평한(flat) 토큰 시퀀스를 봅니다. 챗 템플릿이 메시지를 특수 토큰을 사용해 그 평평한 시퀀스로 바꿉니다. 모델마다 방식이 다릅니다:

```
Llama 3:
<|begin_of_text|><|start_header_id|>system<|end_header_id|>

You are helpful.<|eot_id|><|start_header_id|>user<|end_header_id|>

Hello<|eot_id|><|start_header_id|>assistant<|end_header_id|>

Hi there!<|eot_id|>

ChatGPT:
<|im_start|>system
You are helpful.<|im_end|>
<|im_start|>user
Hello<|im_end|>
<|im_start|>assistant
Hi there!<|im_end|>
```

템플릿이 틀리면 모델은 엉터리를 내놓습니다. 모델은 정확히 그 하나의 형식으로 학습됐습니다. 빠진 줄바꿈 하나, 뒤바뀐 토큰 하나, 여분의 공백 하나만으로도 입력이 학습 분포 밖으로 나가 버립니다.

### 속도

Python은 프로덕션 토큰화에는 너무 느립니다.

tiktoken(OpenAI)은 Python 바인딩을 갖춘 Rust로 쓰였습니다. HuggingFace tokenizers도 Rust입니다. SentencePiece는 C++입니다. 이들은 순수 Python 대비 10~100배의 속도를 냅니다.

감을 잡아 보면: Llama 3 사전학습을 위해 15조 토큰을 초당 100만 토큰 속도(빠른 Python)로 토큰화하면 174일이 걸립니다. 초당 1억 토큰(Rust)이면 1.7일입니다.

여러분이 Python으로 만드는 것은 알고리즘을 이해하기 위함입니다. 프로덕션에서는 컴파일된 구현을 쓰고 Python 래퍼만 만지게 됩니다.

```figure
weight-tying
```

## 직접 만들기

### 단계 1: 바이트 수준 인코딩

기초입니다. 임의의 문자열을 바이트 시퀀스로 바꾸고, 표시를 위해 각 바이트를 출력 가능한 문자로 대응시키고, 그 과정을 되돌립니다.

```python
def bytes_to_tokens(text):
    return list(text.encode("utf-8"))

def tokens_to_text(token_bytes):
    return bytes(token_bytes).decode("utf-8", errors="replace")
```

다국어 텍스트로 바이트 수를 확인해 보세요:

```python
texts = [
    ("English", "hello"),
    ("Chinese", "你好"),
    ("Emoji", "🔥"),
    ("Mixed", "hello你好🔥"),
]

for label, text in texts:
    b = bytes_to_tokens(text)
    print(f"{label}: {len(text)} chars -> {len(b)} bytes -> {b}")
```

"hello"는 5바이트입니다. "你好"는 6바이트(문자당 3바이트)입니다. 불 이모지는 4바이트입니다. 바이트 수준 토크나이저는 그것이 어떤 언어든 신경 쓰지 않습니다. 바이트는 바이트일 뿐입니다.

### 단계 2: 정규식 사전 토크나이저

GPT-2 정규식 패턴으로 텍스트를 조각으로 나눕니다. 각 조각은 BPE가 독립적으로 토큰화합니다.

```python
import re

try:
    import regex
    GPT2_PATTERN = regex.compile(
        r"""'(?:[sdmt]|ll|ve|re)| ?\p{L}+| ?\p{N}+| ?[^\s\p{L}\p{N}]+|\s+(?!\S)|\s+"""
    )
except ImportError:
    GPT2_PATTERN = re.compile(
        r"""'(?:[sdmt]|ll|ve|re)| ?[a-zA-Z]+| ?[0-9]+| ?[^\s\w]+|\s+(?!\S)|\s+"""
    )

def pre_tokenize(text):
    return [match.group() for match in GPT2_PATTERN.finditer(text)]
```

`regex` 모듈은 유니코드 속성 이스케이프(문자는 `\p{L}`, 숫자는 `\p{N}`)를 지원합니다. 표준 라이브러리의 `re` 모듈은 지원하지 않으므로 ASCII 문자 클래스로 폴백합니다. 프로덕션 다국어 토크나이저라면 `regex`를 설치하세요.

시험해 보세요:

```python
print(pre_tokenize("Hello, world! Don't stop."))
# [' Hello', ',', ' world', '!', " Don", "'t", ' stop', '.']
```

앞 공백은 단어에 붙어 있습니다. 축약형은 어포스트로피에서 갈라집니다. 구두점은 자기만의 조각이 됩니다. BPE는 이 경계들을 가로지르며 토큰을 병합할 일이 없습니다.

### 단계 3: 바이트 시퀀스에 대한 BPE

레슨 01의 핵심 알고리즘인데, 이제 사전 토큰화된 조각 위에서 독립적으로 동작합니다.

```python
from collections import Counter

def get_byte_pairs(chunks):
    pairs = Counter()
    for chunk in chunks:
        byte_seq = list(chunk.encode("utf-8"))
        for i in range(len(byte_seq) - 1):
            pairs[(byte_seq[i], byte_seq[i + 1])] += 1
    return pairs

def apply_merge(byte_seq, pair, new_id):
    merged = []
    i = 0
    while i < len(byte_seq):
        if i < len(byte_seq) - 1 and byte_seq[i] == pair[0] and byte_seq[i + 1] == pair[1]:
            merged.append(new_id)
            i += 2
        else:
            merged.append(byte_seq[i])
            i += 1
    return merged
```

### 단계 4: 특수 토큰 처리

특수 토큰은 정확한 일치와 고정 ID가 필요합니다. BPE를 완전히 우회합니다.

```python
class SpecialTokenHandler:
    def __init__(self):
        self.special_tokens = {}
        self.pattern = None

    def add_token(self, token_str, token_id):
        self.special_tokens[token_str] = token_id
        escaped = [re.escape(t) for t in sorted(self.special_tokens.keys(), key=len, reverse=True)]
        self.pattern = re.compile("|".join(escaped))

    def split_with_specials(self, text):
        if not self.pattern:
            return [(text, False)]
        parts = []
        last_end = 0
        for match in self.pattern.finditer(text):
            if match.start() > last_end:
                parts.append((text[last_end:match.start()], False))
            parts.append((match.group(), True))
            last_end = match.end()
        if last_end < len(text):
            parts.append((text[last_end:], False))
        return parts
```

### 단계 5: 전체 토크나이저 클래스

모든 것을 사슬처럼 엮습니다: 정규화, 특수 토큰 분리, 사전 토큰화, BPE 병합, ID 대응.

```python
import unicodedata

class ProductionTokenizer:
    def __init__(self):
        self.merges = {}
        self.vocab = {i: bytes([i]) for i in range(256)}
        self.special_handler = SpecialTokenHandler()
        self.next_id = 256

    def normalize(self, text):
        return unicodedata.normalize("NFKC", text)

    def train(self, text, num_merges):
        text = self.normalize(text)
        chunks = pre_tokenize(text)
        chunk_bytes = [list(chunk.encode("utf-8")) for chunk in chunks]

        for i in range(num_merges):
            pairs = Counter()
            for seq in chunk_bytes:
                for j in range(len(seq) - 1):
                    pairs[(seq[j], seq[j + 1])] += 1
            if not pairs:
                break
            best = max(pairs, key=pairs.get)
            new_id = self.next_id
            self.next_id += 1
            self.merges[best] = new_id
            self.vocab[new_id] = self.vocab[best[0]] + self.vocab[best[1]]
            chunk_bytes = [apply_merge(seq, best, new_id) for seq in chunk_bytes]

    def add_special_token(self, token_str):
        token_id = self.next_id
        self.next_id += 1
        self.special_handler.add_token(token_str, token_id)
        self.vocab[token_id] = token_str.encode("utf-8")
        return token_id

    def encode(self, text):
        text = self.normalize(text)
        parts = self.special_handler.split_with_specials(text)
        all_ids = []
        for part_text, is_special in parts:
            if is_special:
                all_ids.append(self.special_handler.special_tokens[part_text])
            else:
                for chunk in pre_tokenize(part_text):
                    byte_seq = list(chunk.encode("utf-8"))
                    for pair, new_id in self.merges.items():
                        byte_seq = apply_merge(byte_seq, pair, new_id)
                    all_ids.extend(byte_seq)
        return all_ids

    def decode(self, ids):
        byte_parts = []
        for token_id in ids:
            if token_id in self.vocab:
                byte_parts.append(self.vocab[token_id])
        return b"".join(byte_parts).decode("utf-8", errors="replace")

    def vocab_size(self):
        return len(self.vocab)
```

### 단계 6: 다국어 테스트

진짜 시험입니다. 영어, 중국어, 이모지, 코드를 던져 보세요.

```python
corpus = (
    "The quick brown fox jumps over the lazy dog. "
    "The quick brown fox runs through the forest. "
    "Machine learning models process natural language. "
    "Deep learning transforms how we build software. "
    "def train(model, data): return model.fit(data) "
    "def predict(model, x): return model(x) "
)

tok = ProductionTokenizer()
tok.train(corpus, num_merges=50)

bos = tok.add_special_token("<|begin|>")
eos = tok.add_special_token("<|end|>")

test_texts = [
    "The quick brown fox.",
    "你好世界",
    "Hello 🌍 World",
    "def foo(x): return x + 1",
    f"<|begin|>Hello<|end|>",
]

for text in test_texts:
    ids = tok.encode(text)
    decoded = tok.decode(ids)
    print(f"Input:   {text}")
    print(f"Tokens:  {len(ids)} ids")
    print(f"Decoded: {decoded}")
    print()
```

중국어 문자는 각각 3바이트를 만들고, 이모지는 4바이트를 만듭니다. 이 중 하나도 토크나이저를 죽이지 못합니다. 미지 토큰도 하나도 나오지 않습니다. 이것이 바이트 수준 BPE의 힘입니다.

## 실전에서 활용하기

### 진짜 토크나이저 비교

Llama 3, GPT-4, Mistral의 실제 토크나이저를 불러 옵니다. 각각이 같은 다국어 문단을 어떻게 다루는지 보세요.

```python
import tiktoken

gpt4_enc = tiktoken.get_encoding("cl100k_base")

test_paragraph = "Machine learning is powerful. 机器学习很强大。 L'apprentissage automatique est puissant. 🤖💪"

tokens = gpt4_enc.encode(test_paragraph)
pieces = [gpt4_enc.decode([t]) for t in tokens]
print(f"GPT-4 ({len(tokens)} tokens): {pieces}")
```

```python
from transformers import AutoTokenizer

llama_tok = AutoTokenizer.from_pretrained("meta-llama/Meta-Llama-3-8B")
mistral_tok = AutoTokenizer.from_pretrained("mistralai/Mistral-7B-v0.1")

for name, tok in [("Llama 3", llama_tok), ("Mistral", mistral_tok)]:
    tokens = tok.encode(test_paragraph)
    pieces = tok.convert_ids_to_tokens(tokens)
    print(f"{name} ({len(tokens)} tokens): {pieces[:20]}...")
```

같은 텍스트인데 토큰 수가 다르게 나옵니다. 128K 어휘의 Llama 3는 흔한 패턴을 더 공격적으로 병합합니다. 100K의 GPT-4는 그 중간입니다. 32K의 Mistral은 토큰을 더 많이 만들지만 임베딩 층은 더 작습니다.

트레이드오프는 언제나 같습니다: 어휘가 크면 시퀀스는 짧아지지만 파라미터는 많아집니다.

## 출시하기

이 레슨은 프로덕션 토크나이저를 구축하고 디버깅하기 위한 프롬프트를 산출합니다. `outputs/prompt-tokenizer-builder.md`를 보세요.

## 연습 문제

1. **쉬움:** 임의의 토큰 ID의 날것 바이트를 보여 주는 `get_token_bytes(id)` 메서드를 추가하세요. 가장 자주 병합된 토큰들이 실제로 무엇인지 들여다보는 데 써 보세요.
2. **보통:** 공백과 숫자에서 나누되 앞 공백은 유지하는 Llama 스타일 사전 토크나이저를 구현하세요. 같은 말뭉치에서 그 어휘를 GPT-2 정규식 방식과 비교하세요.
3. **어려움:** `{"role": ..., "content": ...}` 메시지 목록을 받아 Llama 3 챗 형식에 맞는 올바른 토큰 시퀀스를 만드는 챗 템플릿 메서드를 추가하세요. HuggingFace 구현과 비교해 테스트하세요.

## 핵심 용어

| 용어 | 사람들이 말하는 것 | 실제 의미 |
|------|----------------|----------------------|
| 바이트 수준 BPE | "바이트 위에서 도는 토크나이저" | 기본 어휘가 256개 바이트 값인 BPE — 어떤 입력도 미지 토큰 없이 처리 |
| 사전 토큰화 | "BPE 전에 나누기" | BPE가 단어 경계를 넘어 병합하는 것을 막는 정규식 또는 규칙 기반 분할 |
| NFKC 정규화 | "유니코드 청소" | 정규 분해 후 호환성 조합 — fi 합자는 "fi"가 되고, 전각 "A"는 "A"가 된다 |
| 챗 템플릿 | "메시지가 토큰이 되는 방식" | role/content 메시지 목록을 평평한 토큰 시퀀스로 바꾸는 정확한 형식 — 모델별로 다르며 학습 형식과 일치해야 한다 |
| 특수 토큰 | "제어 토큰" | BPE를 우회하는 예약된 토큰 ID — [BOS], [EOS], [PAD], 챗 마커 — 병합 전에 정확히 일치 검사 |
| 다산성(Fertility) | "단어당 토큰 수" | 출력 토큰 수와 입력 단어 수의 비율 — GPT-4의 영어는 1.3, 한국어는 2~3, 높을수록 컨텍스트 낭비 |
| tiktoken | "OpenAI 토크나이저" | Python 바인딩을 갖춘 Rust BPE 구현 — 순수 Python보다 10~100배 빠름 |
| 병합 테이블 | "그 어휘" | 학습 중 배운 바이트 쌍 병합의 순서 목록 — 이것이 곧 토크나이저가 학습한 지식이다 |

## 더 읽을거리

- [OpenAI tiktoken source](https://github.com/openai/tiktoken) -- GPT-3.5/4가 쓰는 Rust BPE 구현
- [HuggingFace tokenizers](https://github.com/huggingface/tokenizers) -- BPE, WordPiece, Unigram을 지원하는 Rust 토크나이저 라이브러리
- [Llama 3 paper (Meta, 2024)](https://arxiv.org/abs/2407.21783) -- 128K 어휘와 토크나이저 학습에 대한 세부 사항
- [SentencePiece (Kudo & Richardson, 2018)](https://arxiv.org/abs/1808.06226) -- 언어 중립 토큰화
- [GPT-2 tokenizer source](https://github.com/openai/gpt-2/blob/master/src/encoder.py) -- 원조 바이트-유니코드 매핑
