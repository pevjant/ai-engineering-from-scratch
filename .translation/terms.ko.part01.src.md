## A

### Activation Checkpointing
- **Category:** Math & training
- **What it actually means:** A training-memory technique that saves only selected forward-pass activations and recomputes the omitted ones during backpropagation.
- **Why it matters:** It lets you train larger models or sequences within a fixed memory budget by trading additional computation for lower activation storage.
- **In practice:** Checkpoint the memory-heavy transformer blocks, measure the extra step time, and keep recovery checkpoints separate from activation-recomputation settings.
- **Common confusion:** Activation checkpointing is not a durable training checkpoint. It helps one forward and backward pass fit in memory but cannot resume a crashed run.
- **Related terms:** Autograd, Backpropagation, Checkpoint, Mixed Precision
- **Sources:** [Training Deep Nets with Sublinear Memory Cost](https://arxiv.org/abs/1604.06174)

### Activation Function
- **Category:** Math & training
- **What people say:** The nonlinear operation between layers.
- **What it actually means:** A function applied after a linear or affine layer that introduces nonlinearity. Without it, composing layers with weights and biases collapses to one affine transformation. ReLU, GELU, and SiLU are common choices. The choice directly affects whether gradients flow during training.
- **Learn it:** [Activation Functions](../phases/03-deep-learning-core/04-activation-functions/)
- **Related terms:** ReLU, Gradient, Backpropagation

### Adam (Optimizer)
- **Category:** Math & training
- **What people say:** The optimizer you use without thinking about it.
- **What it actually means:** Adaptive Moment Estimation. It combines an exponential average of gradients with an exponential average of squared gradients, applies bias correction, and adapts the update scale per parameter. It is a useful baseline, but it still needs a suitable learning rate and schedule.
- **Common confusion:** Adam is a strong baseline, not a universal best optimizer.
- **Sources:** [Adam paper](https://arxiv.org/abs/1412.6980)
- **Related terms:** AdamW, Optimizer, Learning Rate

### AdamW
- **Category:** Math & training
- **What people say:** Adam with weight decay fixed.
- **What it actually means:** An Adam variant that decouples weight decay from the gradient-based parameter update. That makes the shrinkage behavior easier to reason about than adding an L2 penalty inside Adam's adaptively scaled gradient.
- **Common confusion:** Decoupled weight decay does not make AdamW universally optimal. Model, data, and training scale still determine the best optimizer and schedule.
- **Sources:** [Decoupled Weight Decay Regularization](https://arxiv.org/abs/1711.05101)
- **Related terms:** Adam (Optimizer), Weight Decay, Optimizer

### Admission Control
- **Category:** Reliability & operations
- **What it actually means:** A pre-acceptance gate that decides whether a request may enter a bounded queue or service under the system's current capacity, priority, and policy.
- **Why it matters:** Rejecting excess work at a controlled boundary protects admitted requests from queue growth, timeout cascades, and resource exhaustion.
- **In practice:** Estimate the request's cost, check tenant and system capacity, reserve the required budget atomically, and identify the overloaded scope when rejecting. Give retry guidance only when the condition is transient and the caller's retry budget permits another attempt.
- **Common confusion:** Admission control acts before acceptance. Load shedding can reject or remove work at ingress, in queues, at dependencies, or at other overload boundaries.
- **Related terms:** Load Shedding, Backpressure, Rate Limit, Saturation
- **Sources:** [Google SRE: Handling Overload](https://sre.google/sre-book/handling-overload/)

### Agent
- **Category:** Agents & tools
- **What people say:** An autonomous model that thinks and acts alone.
- **What it actually means:** A software system that lets a model select actions toward a goal, observe tool or environment results, and continue under an orchestration policy. An agent may use a loop, a state machine, a workflow engine, or human approvals. The model is one component, not the entire system.
- **Why it matters:** Reliability comes from the harness, tool contracts, state, permissions, and verification around the model.
- **In practice:** A coding agent reads repository context, proposes a patch, runs tests in a sandbox, and stops for approval before deployment.
- **Common confusion:** Autonomy is a degree of delegated authority, not a required property of every agent.
- **Learn it:** [The Agent Loop](../phases/14-agent-engineering/01-the-agent-loop/)
- **Related terms:** Agent Harness, Agent State, Tool Contract, Human-in-the-Loop (HITL)

### Agent Harness
- **Category:** Agents & tools
- **What it actually means:** The runtime around a model that assembles context, exposes tools, manages state, enforces limits, records traces, and decides when the agent should continue, retry, ask, or stop.
- **Why it matters:** Two systems using the same model can perform very differently because their harnesses provide different context, tools, feedback, and safety boundaries.
- **In practice:** Your harness can limit an agent to five tool calls, persist a checkpoint after each accepted patch, and require a passing test command before completion.
- **Common confusion:** A harness is broader than a prompt template and narrower than the complete product.
- **Learn it:** [Minimal Agent Workbench](../phases/14-agent-engineering/32-minimal-agent-workbench/)
- **Related terms:** Agent, Tool Contract, Agent State, Verification Gate, Sandbox

### Agent Memory
- **Category:** Agents & tools
- **What it actually means:** Information stored outside the model and selected for use in later agent steps, such as prior decisions, user preferences, task episodes, or verified facts.
- **Why it matters:** It gives an agent continuity beyond one context window without forcing every past event into every prompt.
- **In practice:** Store a compact task outcome with provenance, retrieve it only when relevant, and let the user inspect or correct durable personal information.
- **Common confusion:** Agent memory is not the same as agent state. State tracks the current run; memory preserves selected information for possible future runs.
- **Related terms:** Agent State, Context Engineering, Checkpoint, Semantic Cache
- **Sources:** [Generative Agents](https://arxiv.org/abs/2304.03442)

### Agent State
- **Category:** Agents & tools
- **What it actually means:** The explicit data an agent carries across steps, such as the current objective, completed actions, tool results, open questions, budgets, approvals, and artifact references.
- **Why it matters:** Explicit state makes long tasks resumable, inspectable, and less dependent on the model reconstructing progress from a transcript.
- **In practice:** Store the selected issue, changed files, latest test result, and remaining checks in a typed object that is updated after each action.
- **Common confusion:** State is not the same as conversation history. A transcript is evidence; state is the compact operational record used to decide what happens next.
- **Learn it:** [Repository Memory and State](../phases/14-agent-engineering/34-repo-memory-and-state/)
- **Related terms:** Checkpoint, Durable Execution, Context Engineering, Handoff

### Agent Skill
- **Category:** Agents & tools
- **What it actually means:** A discoverable directory of procedural instructions whose entry point is `SKILL.md`, with optional references, scripts, and assets that a compatible runtime can load in stages.
- **Why it matters:** It packages reusable task knowledge separately from one conversation while keeping deeper context and deterministic helpers available on demand.
- **In practice:** Publish a compact name and routing description, load the workflow only after activation, and read branch-specific references when the task reaches them.
- **Common confusion:** Activating a skill supplies context. It does not expose a tool, grant permission, create a sandbox, or prove that the resulting work is correct.
- **Learn it:** [Agent Skills: Portable Contract and Runtime Boundary](../phases/13-tools-and-protocols/22-skills-and-agent-sdks/)
- **Related terms:** Skill Bundle, Skill Catalog, Skill Invocation, Progressive Disclosure, MCP (Model Context Protocol)
- **Sources:** [Agent Skills specification](https://agentskills.io/specification)

### AI Risk Assessment
- **Category:** Security & governance
- **What it actually means:** A documented analysis of how an AI system can affect people, organizations, and environments, including context, hazards, likelihood, impact, controls, residual risk, and monitoring responsibilities.
- **Why it matters:** Model capability alone does not determine risk. Deployment context, affected groups, human authority, data, and system integrations change both the harms and the controls required.
- **In practice:** Define the intended use and affected parties, identify credible failure and misuse scenarios, assign owners to controls, record residual risk, and set review triggers for material changes.
- **Common confusion:** A risk assessment supports a decision under stated assumptions. It is not a one-time safety certificate or proof that every hazard has been found.
- **Related terms:** Threat Model, Guardrails, Human-in-the-Loop (HITL), Data Classification
- **Sources:** [NIST AI Risk Management Framework](https://www.nist.gov/itl/ai-risk-management-framework)

### Alignment
- **Category:** Evaluation & safety
- **What people say:** Making AI safe.
- **What it actually means:** The effort to make a model or AI system behave in ways that match intended goals, constraints, and human preferences across both expected and adversarial situations.
- **Why it matters:** A system can optimize the stated metric while violating the user's real intent, so alignment requires evaluation, oversight, and system controls as well as model training.
- **Related terms:** Guardrails, Evaluation (Eval), Human-in-the-Loop (HITL)

### Approval Gate
- **Category:** Agents & tools
- **What it actually means:** A control point that blocks a consequential action until an authorized person or policy grants permission.
- **Why it matters:** It limits the blast radius of uncertain model decisions while preserving automation for reversible work.
- **In practice:** Let an agent draft a database migration and run it against a disposable database, but require an owner to approve any production execution.
- **Common confusion:** An approval gate asks whether an action is authorized. A verification gate asks whether evidence shows the action is correct.
- **Learn it:** [Verification Gates](../phases/14-agent-engineering/38-verification-gates/)
- **Related terms:** Human-in-the-Loop (HITL), Verification Gate, Least Privilege

### Approximate Nearest Neighbor (ANN)
- **Category:** Retrieval & generation
- **What it actually means:** A search method that returns vectors likely to be among the nearest to a query without exhaustively comparing the query with every stored vector.
- **Why it matters:** Approximation makes large vector indexes practical, but it introduces a measurable tradeoff between search speed, memory, and retrieval recall.
- **In practice:** Tune index and search parameters against a held-out query set, then report latency together with Recall@K instead of assuming every true neighbor is found.
- **Common confusion:** ANN describes a search objective and tradeoff, while HNSW is one particular index algorithm that can implement it.
- **Related terms:** Vector Database, HNSW, Cosine Similarity, Recall@K
- **Sources:** [Efficient and Robust Approximate Nearest Neighbor Search Using HNSW](https://dl.acm.org/doi/10.1109/TPAMI.2018.2889473)

### Attention
- **Category:** Models & inference
- **What people say:** How a model focuses on important tokens.
- **What it actually means:** A mechanism that forms contextual representations by comparing query vectors with key vectors, normalizing the resulting scores, and using them to combine value vectors. Masks, position rules, or sparse patterns can restrict which positions participate.
- **Why it matters:** Attention lets a model route information between sequence positions, but it does not by itself explain or prove what the model understood.
- **Common confusion:** Attention weights are computation coefficients, not a faithful explanation of model reasoning.
- **Learn it:** [Self-Attention from Scratch](../phases/07-transformers-deep-dive/02-self-attention-from-scratch/)
- **Sources:** [Attention Is All You Need](https://arxiv.org/abs/1706.03762)
- **Related terms:** Self-Attention, Transformer, KV Cache

### Audio Token
- **Category:** Multimodal systems
- **What it actually means:** A discrete identifier produced by an audio codec or tokenizer for a short segment or feature of an audio signal, sometimes across several codebooks.
- **Why it matters:** Discrete audio representations let sequence models process, predict, store, or generate sound using token-oriented architectures.
- **In practice:** Version the codec with the model, preserve sample-rate and codebook metadata, measure reconstruction quality, and distinguish semantic audio tokens from waveform-compression tokens.
- **Common confusion:** An audio token is not a fixed duration, phoneme, or word. Its meaning and time span depend on the tokenizer and codebook design.
- **Learn it:** [Neural Audio Codecs](../phases/06-speech-and-audio/13-neural-audio-codecs/)
- **Related terms:** Token, Embedding, Automatic Speech Recognition (ASR), Multimodal Model
- **Sources:** [SoundStream](https://arxiv.org/abs/2107.03312)

### Audit Log
- **Category:** Security & governance
- **What it actually means:** A durable, access-controlled record of security- or accountability-relevant events, including who or what acted, what changed, when it happened, and the resulting status.
- **Why it matters:** Consequential agent actions need evidence that supports investigation, policy review, and responsibility beyond performance debugging.
- **In practice:** Record tool authorization, approval decisions, external writes, policy versions, and artifact identifiers while redacting secrets and restricting log access.
- **Common confusion:** A trace helps diagnose one execution path. An audit log preserves events required for accountability across executions and over time.
- **Related terms:** Trace, Observability, Approval Gate, Provenance Attestation
- **Sources:** [NIST SP 800-92](https://csrc.nist.gov/pubs/sp/800/92/final)

### Autograd
- **Category:** Math & training
- **What people say:** Automatic gradients.
- **What it actually means:** A system that records or transforms tensor operations so it can compute derivatives, usually with reverse-mode automatic differentiation. You write the forward computation and the framework derives the gradients needed for backpropagation.
- **Learn it:** [Chain Rule and Automatic Differentiation](../phases/01-math-foundations/05-chain-rule-and-autodiff/)
- **Related terms:** Backpropagation, Gradient, Tensor

### Automatic Speech Recognition (ASR)
- **Category:** Multimodal systems
- **What it actually means:** The task and system pipeline that maps a speech signal to a transcription, often with optional token or segment timing and confidence information.
- **Why it matters:** Speech interfaces depend on more than language modeling. Acoustic variation, segmentation, decoding, vocabulary, and domain conditions all affect the final transcript.
- **In practice:** Evaluate word or character errors by language, speaker, noise, and domain, retain timestamps when downstream grounding needs them, and test the exact audio preprocessing used in production.
- **Common confusion:** ASR transcribes what was said. Determining who spoke requires diarization or speaker recognition, while translation and intent understanding are separate tasks.
- **Learn it:** [Speech Recognition and ASR](../phases/06-speech-and-audio/04-speech-recognition-asr/)
- **Related terms:** Audio Token, Encoder, Tokenization, Multimodal Model
- **Sources:** [Connectionist Temporal Classification](https://www.cs.toronto.edu/~graves/icml_2006.pdf)

### Autoregressive
- **Category:** Models & inference
- **What people say:** The model generates one word at a time.
- **What it actually means:** A factorization in which each output token is predicted from the tokens that precede it. During generation, the selected token is appended to the sequence and becomes part of the next prediction's context.
- **Common confusion:** The unit is a token, not necessarily a word, and generation can use decoding methods other than always selecting the highest-probability token.
- **Related terms:** Token, Temperature, KV Cache

### Autoscaling
- **Category:** Infrastructure & serving
- **What it actually means:** A control loop that changes the number or capacity of serving workers from observed demand, resource use, or application metrics within configured bounds.
- **Why it matters:** AI workloads can change faster than manual provisioning, but scaling decisions must account for model-load time, accelerator availability, queueing, and request cost.
- **In practice:** Scale from a demand signal tied to useful work, set minimum warm capacity, bound scale-down churn, and verify that new replicas pass readiness checks before receiving traffic.
- **Common confusion:** Autoscaling adds or removes capacity. It does not make an overloaded dependency faster or guarantee that enough hardware can be acquired in time.
- **Learn it:** [GPU Autoscaling on Kubernetes](../phases/17-infrastructure-and-production/03-gpu-autoscaling-kubernetes/)
- **Related terms:** Model Serving, Saturation, Readiness Probe, Backpressure
- **Sources:** [Kubernetes Horizontal Pod Autoscaling](https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/)

### Availability
- **Category:** Reliability & operations
- **What it actually means:** The proportion of eligible service interactions or time windows in which users can obtain the defined acceptable service under a stated measurement boundary.
- **Why it matters:** A service can be running while users still cannot complete useful requests, so availability must be tied to user-visible success rather than process uptime alone.
- **In practice:** Define eligible events and acceptable outcomes, exclude only documented cases, calculate the indicator over a fixed window, and investigate both total failures and prolonged partial degradation.
- **Common confusion:** Availability is one reliability outcome. It does not describe latency, correctness, safety, or the experience of every user segment.
- **Related terms:** Service Level Indicator (SLI), Service Level Objective (SLO), Error Budget, Incident Response
- **Sources:** [Google SRE: Service Level Objectives](https://sre.google/sre-book/service-level-objectives/)

## B

### Backpressure
- **Category:** AI-native development
- **What it actually means:** A flow-control mechanism that slows or rejects upstream work when a downstream component cannot process it safely at the current rate.
- **Why it matters:** Without backpressure, queued agent runs, tool calls, or streamed events can exhaust memory, exceed rate limits, and amplify retries.
- **In practice:** When the evaluator queue reaches its limit, pause new agent jobs or return a retryable response instead of accepting unbounded work.
- **Common confusion:** Backpressure protects capacity before failure. A circuit breaker stops calls after failures show a dependency is unhealthy.
- **Related terms:** Rate Limit, Retry with Backoff, Circuit Breaker

### Backpropagation
- **Category:** Math & training
- **What people say:** How neural networks learn.
- **What it actually means:** An efficient application of the chain rule that propagates derivatives from a scalar loss backward through a computation graph. It computes gradients; an optimizer uses those gradients to update parameters.
- **Common confusion:** Backpropagation calculates gradients. It does not choose the update rule or learning rate.
- **Why it's called that:** Derivative information moves backward from the loss toward earlier operations.
- **Learn it:** [Backpropagation from Scratch](../phases/03-deep-learning-core/03-backpropagation/)
- **Related terms:** Autograd, Gradient, Optimizer

### Batch Size
- **Category:** Math & training
- **What people say:** How many examples are processed at once.
- **What it actually means:** The number of examples whose losses contribute to one gradient estimate before an optimizer update. Larger batches can improve hardware utilization and reduce gradient noise, but they require more memory and may need different learning-rate or scheduling choices.
- **Common confusion:** There is no universal batch-size range or rule that says every batch increase should produce the same learning-rate increase.
- **Related terms:** Learning Rate, Gradient, Optimizer

### Benchmark Contamination
- **Category:** Evaluation & safety
- **What it actually means:** Overlap or information leakage between evaluation examples and data used to pretrain, tune, prompt, select, or otherwise improve the evaluated system.
- **Why it matters:** Contamination can make a benchmark score reflect prior exposure rather than the ability to generalize to unseen tasks.
- **In practice:** Track dataset provenance, search training sources for exact and near duplicates, hold back private test cases, and refresh public evals with newly authored examples.
- **Common confusion:** Contamination is broader than exact copying. Paraphrases, answer keys, benchmark metadata, and repeated prompt tuning can also leak evaluation information.
- **Related terms:** Data Leakage, Data Deduplication, Eval Set, Exact Match (EM)
- **Sources:** [Investigating Data Contamination in Modern Benchmarks for Large Language Models](https://arxiv.org/abs/2311.09783)

### BM25
- **Category:** Retrieval & generation
- **What it actually means:** A lexical ranking function that scores a document from query-term matches while accounting for term rarity, repeated occurrences, and document length.
- **Why it matters:** It is a strong exact-term retrieval baseline and complements dense retrieval for identifiers, rare words, and domain-specific phrases.
- **In practice:** Retrieve candidates with BM25 and dense search, combine their ranks, then evaluate the merged results before adding a more expensive reranker.
- **Common confusion:** BM25 does not understand semantic similarity directly, and its score has no universal meaning across different queries or index configurations.
- **Related terms:** Hybrid Retrieval, Dense Retrieval, Reranker, RAG (Retrieval-Augmented Generation)
- **Sources:** [The Probabilistic Relevance Framework: BM25 and Beyond](https://doi.org/10.1561/1500000019)

### Byte Pair Encoding (BPE)
- **Category:** Data & representations
- **What it actually means:** A subword-tokenization method that repeatedly merges frequent adjacent units to construct a fixed vocabulary from training text.
- **Why it matters:** It balances vocabulary size with the ability to represent rare or unseen words as smaller units.
- **In practice:** Train the tokenizer only on approved corpus splits, version its merge rules with the model, and inspect how it segments code, multilingual text, and whitespace.
- **Common confusion:** BPE is one tokenizer family, not a universal description of how every model creates tokens.
- **Related terms:** Tokenization, Vocabulary, Token, Embedding
- **Sources:** [Neural Machine Translation of Rare Words with Subword Units](https://arxiv.org/abs/1508.07909)

## C

### Calibration
- **Category:** Evaluation & safety
- **What it actually means:** The agreement between a system's stated confidence and the observed frequency with which predictions at that confidence are correct.
- **Why it matters:** A system can be accurate on average yet dangerously overconfident on the cases where people rely on its score.
- **In practice:** Bucket predictions by confidence, compare confidence with empirical accuracy, and recalibrate or abstain when the gap is unacceptable.
- **Common confusion:** Calibration measures confidence reliability, not overall accuracy, factuality, or reasoning quality.
- **Related terms:** Softmax, Evaluation (Eval), Precision & Recall, Logits
- **Sources:** [On Calibration of Modern Neural Networks](https://proceedings.mlr.press/v70/guo17a.html)

### Canary Release
- **Category:** Reliability & operations
- **What it actually means:** A deployment strategy that exposes a new version to a limited slice of traffic or infrastructure before expanding the rollout.
- **Why it matters:** It limits the impact of defects and gives you production evidence before the new model, prompt, agent, or service reaches everyone.
- **In practice:** Route a small eligible cohort to the release, compare quality and operational metrics with the control, and stop or roll back on predefined failures.
- **Common confusion:** A canary release limits exposure; it does not replace pre-deployment tests, approval, or rollback preparation.
- **Related terms:** Evaluation (Eval), Observability, Rollback, Verification Gate
- **Sources:** [Kubernetes Deployments: Canary Deployment](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/#canary-deployment)

### Chain of Thought (CoT)
- **Category:** Prompting & context
- **What people say:** Asking the model to show every step of its thinking.
- **What it actually means:** Intermediate reasoning used to decompose a task before producing an answer. A prompt can request a visible rationale, while some systems use internal reasoning that is not returned to the user.
- **Why it matters:** Decomposition can help on multi-step tasks, but a fluent rationale is not proof that the answer is correct or that the text faithfully represents the model's internal computation.
- **In practice:** Ask for a concise plan, independently check the result, and request verifiable calculations or citations instead of relying on a long reasoning transcript.
- **Common confusion:** Chain of thought is not a substitute for tools, tests, or external verification.
- **Learn it:** [Few-Shot and Chain of Thought](../phases/11-llm-engineering/02-few-shot-cot/)
- **Related terms:** Prompt Engineering, Verification Gate, Evaluation (Eval)

### Checkpoint
- **Category:** Agents & tools
- **What it actually means:** A durable snapshot used to resume from a known boundary. In a workflow, it stores operational state and artifact references. In model training, it can store parameters, optimizer state, scheduler state, and the training position.
- **Why it matters:** Long-running workflows and training runs can recover from interruption without replaying completed work or losing expensive progress.
- **In practice:** Save an agent's accepted patch and test evidence after a verified step, or save a training run's weights, optimizer state, random state, and data position before shutdown.
- **Common confusion:** A workflow checkpoint and a model-training checkpoint serve the same recovery goal but preserve different state. Neither is merely a transcript or a weights file with no resume metadata.
- **Learn it:** [Checkpoint Save and Resume](../phases/19-capstone-projects/47-checkpoint-save-resume/); [Repository Memory and State](../phases/14-agent-engineering/34-repo-memory-and-state/)
- **Related terms:** Agent State, Durable Execution, Parameter, Optimizer

### Chunked Prefill
- **Category:** Infrastructure & serving
- **What it actually means:** A serving technique that divides a long prompt's prefill work into smaller schedulable pieces so prompt processing can interleave with decode work from other requests.
- **Why it matters:** One long prompt can otherwise occupy the accelerator and delay active generations, producing poor tail latency even when total throughput looks healthy.
- **In practice:** Choose a chunk policy from measured workloads, account for scheduling overhead, and compare prefill completion, decode latency, and goodput under mixed prompt lengths.
- **Common confusion:** Chunked prefill changes how prompt computation is scheduled. It does not split the user's context into independent semantic chunks or change the model's context window.
- **Learn it:** [vLLM Serving Internals](../phases/17-infrastructure-and-production/04-vllm-serving-internals/)
- **Related terms:** Prefill, Decode Phase, Dynamic Batching, Tail Latency
- **Sources:** [Sarathi-Serve](https://arxiv.org/abs/2403.02310)

### Chunking
- **Category:** Retrieval & generation
- **What people say:** Splitting documents into pieces.
- **What it actually means:** Dividing source material into retrievable units before indexing. Chunk boundaries, overlap, metadata, and document structure determine whether retrieval returns enough context without flooding the prompt.
- **Why it matters:** The right chunking strategy depends on document shape, query type, embedding model, and evaluation results. There is no universal token size or overlap percentage.
- **In practice:** Keep headings and code blocks intact, attach source metadata, then measure retrieval quality on real questions before tuning size.
- **Related terms:** RAG (Retrieval-Augmented Generation), Reranker, Grounding

### Circuit Breaker
- **Category:** AI-native development
- **What it actually means:** A reliability control that temporarily stops calls to a dependency after failures cross a threshold, then probes whether the dependency has recovered.
- **Why it matters:** It prevents repeated model or tool failures from consuming latency, budget, and capacity across the rest of the system.
- **In practice:** Open the breaker after repeated provider timeouts, fail over or return a controlled response, then allow a limited health probe after a cooldown.
- **Common confusion:** A circuit breaker reacts to dependency health. A rate limit controls allowed request volume.
- **Related terms:** Retry with Backoff, Rate Limit, Model Router, Backpressure

### CNN (Convolutional Neural Network)
- **Category:** Models & inference
- **What people say:** A neural network for images.
- **What it actually means:** A neural network that uses convolution operations (sliding filters over the input) to detect local patterns. Stacking convolutions detects increasingly complex features: edges, textures, objects.
- **Common confusion:** Convolutions also work on audio, time series, and other grid-like data.
- **Related terms:** Feature, Inductive Bias, Activation Function

### Coding Agent
- **Category:** AI-native development
- **What it actually means:** An agent specialized for software work that can inspect a repository, edit files, run development tools, and use their outputs to advance a scoped engineering task.
- **Why it matters:** Its value depends on repository context, tool permissions, review boundaries, and verification, not only code generation quality.
- **In practice:** Give the agent an issue, a scope contract, repository instructions, and a test command; review the resulting patch and evidence before accepting it.
- **Common confusion:** A coding assistant that only suggests text is not necessarily an agent. The agent acts through tools and observes results.
- **Learn it:** [Skill Discovery and Progressive Disclosure](../phases/13-tools-and-protocols/24-skill-discovery-and-progressive-disclosure/)
- **Related terms:** Agent Harness, Repository Map, Patch, Scope Contract, Reviewer Agent

### Compensating Action
- **Category:** Agents & tools
- **What it actually means:** A deliberate operation that semantically counteracts a completed side effect when the original operation cannot be rolled back atomically.
- **Why it matters:** Multi-step agent workflows cross databases and external services where a later failure cannot undo earlier writes through one transaction.
- **In practice:** If a booking workflow charges a card but the reservation fails, issue a tracked refund and preserve both events rather than deleting history.
- **Common confusion:** Compensation is a new business action, not time travel. It can fail and therefore needs idempotency, monitoring, and escalation.
- **Related terms:** Durable Execution, Idempotency, Checkpoint, Approval Gate
- **Sources:** [Sagas](https://dl.acm.org/doi/10.1145/38713.38742)

### Content Provenance
- **Category:** Security & governance
- **What it actually means:** Verifiable information about the origin and editing history of a piece of media or other digital content, including the actors, tools, transformations, and assertions attached to it.
- **Why it matters:** Generative systems make origin claims difficult to infer from appearance alone, so consumers and platforms need inspectable evidence about how content was produced.
- **In practice:** Bind provenance assertions to the content, sign them with controlled identities, preserve transformation history, and show clearly when evidence is missing or cannot be verified.
- **Common confusion:** Provenance can establish who asserted a history and whether the record was altered. It does not prove that the depicted event is true or that the content is harmless.
- **Learn it:** [Watermarking, SynthID, Stable Signature, and C2PA](../phases/18-ethics-safety-alignment/23-watermarking-synthid-stable-signature-c2pa/)
- **Related terms:** Data Provenance, Provenance Attestation, Audit Log, Grounding
- **Sources:** [C2PA Technical Specification](https://c2pa.org/specifications/specifications/2.2/specs/C2PA_Specification.html)

### Context Compression
- **Category:** Prompting & context
- **What it actually means:** Reducing the token footprint of source material while attempting to preserve the information required for a later model decision.
- **Why it matters:** Compression can make long tasks fit within budget, but every omitted detail creates a risk that the model loses evidence, constraints, or unresolved state.
- **In practice:** Preserve authoritative facts and identifiers verbatim, summarize redundant history, attach source pointers, and test the compressed context on representative tasks.
- **Common confusion:** Compression is lossy unless it retains the full original. A shorter summary is not automatically an equivalent context.
- **Related terms:** Token Budget, Context Engineering, Progressive Disclosure, Handoff
- **Sources:** [LLMLingua](https://arxiv.org/abs/2310.05736)

### Context Engineering
- **Category:** Prompting & context
- **What it actually means:** Designing the full information environment supplied to a model at each step, including instructions, selected files, retrieved evidence, tool results, examples, state, and output constraints.
- **Why it matters:** Model performance often fails because relevant evidence is missing, stale, badly ordered, or overwhelmed by noise.
- **In practice:** Build a compact task packet with the goal, repository rules, relevant interfaces, recent tool output, and unresolved decisions, then update it as state changes.
- **Common confusion:** Prompt engineering focuses on instruction wording. Context engineering also decides what evidence and state enter the model's working context.
- **Learn it:** [Context Engineering](../phases/11-llm-engineering/05-context-engineering/)
- **Related terms:** Context Window, Progressive Disclosure, Agent State, Repository Map

### Context Window
- **Category:** Prompting & context
- **What people say:** How much the model remembers.
- **What it actually means:** The maximum token capacity available to one model inference under a specific model and API contract. The capacity may include system instructions, messages, retrieved content, tool exchanges, and generated output, with provider-specific accounting and output limits.
- **Why it matters:** Conversation history is only available when the application sends or reconstructs it. A large window does not guarantee that every included detail will be used reliably.
- **Common confusion:** Context is temporary input to an inference. Durable memory is stored outside the model and selected back into later context.
- **Learn it:** [Context Engineering](../phases/11-llm-engineering/05-context-engineering/)
- **Related terms:** Token Budget, Context Engineering, Prompt Cache, Agent State

### Continuous Batching
- **Category:** Infrastructure & serving
- **What it actually means:** A serving scheduler that adds and removes generation requests at iteration boundaries instead of waiting for every request in a fixed batch to finish.
- **Why it matters:** Autoregressive requests produce different output lengths, so continuous batching can keep accelerators utilized without forcing short requests to wait for the longest one.
- **In practice:** Admit new requests when capacity becomes available, track per-request latency, and apply backpressure when the live batch or KV-cache budget is full.
- **Common confusion:** Continuous batching is an inference scheduling policy, not gradient accumulation or a training batch-size technique.
- **Related terms:** Dynamic Batching, Decode Phase, Backpressure, Rate Limit
- **Sources:** [Orca](https://www.usenix.org/conference/osdi22/presentation/yu)

### Contrastive Learning
- **Category:** Math & training
- **What people say:** Learning by comparison.
- **What it actually means:** Training by pulling similar pairs closer and pushing dissimilar pairs apart in embedding space. CLIP uses this: matching image-text pairs vs non-matching ones.
- **Related terms:** Embedding, Cosine Similarity, Loss Function

### Cosine Similarity
- **Category:** Data & representations
- **What people say:** How similar two vectors are.
- **What it actually means:** The normalized dot product of two vectors. It compares their direction rather than their magnitude and ranges from -1 to 1 for real-valued vectors.
- **Common confusion:** High cosine similarity only has meaning relative to the embedding model and the data distribution. It does not prove factual or semantic equivalence.
- **Related terms:** Embedding, Semantic Search, Reranker

### Cost per Successful Task
- **Category:** AI-native development
- **What it actually means:** Total system cost divided by the number of tasks that satisfy a defined success criterion, including retries, failed runs, tool use, and evaluation overhead.
- **Why it matters:** A cheap model call can produce an expensive workflow if it fails often or requires repeated human correction.
- **In practice:** Measure provider charges and infrastructure cost across 100 repository tasks, then divide by the number whose patches pass tests and review.
- **Common confusion:** Cost per token measures usage. Cost per successful task measures useful outcomes.
- **Related terms:** Evaluation (Eval), Retry with Backoff, Model Router, Verification Gate

### Cross-Attention
- **Category:** Multimodal systems
- **What it actually means:** Attention in which the query representation comes from one sequence or representation while keys and values come from another.
- **Why it matters:** It gives one stream a learnable way to retrieve information from another, such as language tokens attending to visual features.
- **In practice:** State which stream supplies queries, keys, and values, apply masks for missing or invalid positions, and inspect whether the model still performs when one modality is ablated.
- **Common confusion:** Cross-attention is not intrinsically multimodal. It can connect two text sequences or other representations; self-attention instead derives queries, keys, and values from the same sequence representation.
- **Related terms:** Attention, Self-Attention, Vision-Language Model (VLM), Multimodal Fusion
- **Sources:** [Attention Is All You Need](https://arxiv.org/abs/1706.03762)

### Cross-Entropy
- **Category:** Math & training
- **What people say:** The classification loss.
- **What it actually means:** A loss based on the negative log probability assigned to the target outcome. In next-token training, it penalizes the model when it assigns low probability to the observed next token.
- **Common confusion:** Perplexity is the exponentiated average cross-entropy only when the averaging and logarithm base are defined consistently.
- **Related terms:** Loss Function, Softmax, Perplexity

### CUDA
- **Category:** Models & inference
- **What people say:** GPU programming.
- **What it actually means:** NVIDIA's platform and programming model for general-purpose computation on compatible GPUs. Deep-learning frameworks use CUDA libraries and kernels to execute many tensor operations in parallel.
- **Common confusion:** GPU acceleration is not synonymous with CUDA; other hardware and software stacks exist.
- **Related terms:** Tensor, Mixed Precision, JAX

## D

### Data Augmentation
- **Category:** Math & training
- **What people say:** Making more training data.
- **What it actually means:** Creating modified examples, such as transformed images, perturbed audio, or paraphrased text, to increase training diversity without collecting entirely new source data. It can reduce overfitting when the transformation preserves the task signal.
- **Common confusion:** An augmentation must preserve the target label or behavior you want the model to learn.
- **Related terms:** Overfitting, Epoch, Eval Set

### Data Classification
- **Category:** Security & governance
- **What it actually means:** Assigning data to documented sensitivity or impact classes so handling, access, retention, sharing, and incident rules follow the consequences of disclosure or loss.
- **Why it matters:** An AI pipeline cannot apply proportionate controls if source documents, prompts, traces, and generated artifacts are treated as equally sensitive.
- **In practice:** Classify data at ingestion, carry the label through derived artifacts, restrict tools and destinations by class, and define how labels change after transformation or aggregation.
- **Common confusion:** Data classification describes protection requirements. It is not the same as a machine-learning classification task or a claim that the data is accurate.
- **Related terms:** Data Minimization, Trust Boundary, Least Privilege, Audit Log
- **Sources:** [NIST SP 1800-39 Initial Public Draft: Data Classification Practices](https://www.nccoe.nist.gov/sites/default/files/2026-02/nist-sp-1800-39-ipd.pdf); [NIST FIPS 199: Federal Information and Information System Categorization](https://csrc.nist.gov/pubs/fips/199/final)

### Data Deduplication
- **Category:** Data & representations
- **What it actually means:** Detecting and removing exact and near-duplicate examples within or across datasets.
- **Why it matters:** Repetition can distort the training distribution, increase memorization, leak test material, and make evaluation appear stronger than it is.
- **In practice:** Normalize content, use exact hashes and similarity methods, review borderline clusters, and record which version and rule removed each example.
- **Common confusion:** Deduplication is not ordinary data cleaning. Two distinct records can legitimately share text, and two paraphrases can still carry the same leaked information.
- **Related terms:** Data Provenance, Benchmark Contamination, Dataset Split, Overfitting
- **Sources:** [Deduplicating Training Data Makes Language Models Better](https://arxiv.org/abs/2107.06499)

### Data Exfiltration
- **Category:** Security & governance
- **What it actually means:** Unauthorized transfer of protected data from a system or trust zone to a person, tool, service, or storage location that is not permitted to receive it.
- **Why it matters:** An agent can expose secrets through generated text, tool arguments, URLs, logs, or side effects even when the original data store remains intact.
- **In practice:** Minimize readable data, allowlist destinations, inspect outbound tool calls, redact sensitive fields, and alert on unusual transfers across trust boundaries.
- **Common confusion:** Exfiltration is about unauthorized movement or disclosure. Ordinary retrieval of data by an authorized component is not exfiltration, although later use can become one.
- **Learn it:** [EchoLeak and CVEs for AI](../phases/18-ethics-safety-alignment/25-echoleak-cves-for-ai/)
- **Related terms:** Trust Boundary, Least Privilege, Indirect Prompt Injection, Audit Log
- **Sources:** [NIST SP 800-53 Rev. 5: AC-4 Information Flow Enforcement](https://csrc.nist.gov/files/pubs/sp/800/53/r5/upd1/final/docs/sp800-53r5-controls.xlsx)

### Data Leakage
- **Category:** Data & representations
- **What it actually means:** Unintended use of information during training or feature construction that would not be available at the real prediction point or belongs to a held-out evaluation boundary.
- **Why it matters:** Leakage produces optimistic metrics that collapse when the system encounters genuinely unseen inputs.
- **In practice:** Split data before fitting preprocessors, keep future information out of historical features, and isolate test labels and benchmark answers from prompts and tuning loops.
- **Common confusion:** Leakage is not limited to duplicate rows. Global normalization statistics, timestamps, target-derived features, and repeated test-driven prompt edits can all leak information.
- **Related terms:** Dataset Split, Benchmark Contamination, Eval Set, Data Provenance
- **Sources:** [scikit-learn: Data leakage](https://scikit-learn.org/stable/common_pitfalls.html#data-leakage)

### Data Lineage
- **Category:** Security & governance
- **What it actually means:** A record of how a data artifact was derived across sources, transformations, joins, filters, versions, and downstream uses.
- **Why it matters:** When a source is corrected, revoked, or found unsafe, lineage identifies which datasets, embeddings, evaluations, and model artifacts may be affected.
- **In practice:** Give inputs and outputs stable identifiers, record each transformation and version, preserve parent-child relationships, and test whether an affected source can be traced to every derivative.
- **Common confusion:** Data provenance explains origin and custody broadly. Lineage emphasizes the transformation path and dependencies between data artifacts.
- **Related terms:** Data Provenance, Datasheet for Datasets, Audit Log, Content Provenance
- **Sources:** [W3C PROV-O](https://www.w3.org/TR/prov-o/)

### Data Minimization
- **Category:** Security & governance
- **What it actually means:** For personal data, limiting what is collected, processed, exposed, and retained to what is necessary for a specified purpose. Teams can apply the same discipline to sensitive non-personal data as an engineering control.
- **Why it matters:** Every unnecessary field placed in a prompt, trace, cache, or tool call increases privacy exposure and the possible impact of misuse or compromise.
- **In practice:** Define the required fields before collection, redact or aggregate at the earliest boundary, set retention limits, and verify that optional context improves a measured task outcome before keeping it.
- **Common confusion:** Minimization does not mean keeping no data. It means being able to justify each data element, use, recipient, and retention period against the stated purpose.
- **Related terms:** Purpose Limitation, Data Classification, Least Privilege, Context Engineering
- **Sources:** [General Data Protection Regulation, Article 5(1)(c)](https://eur-lex.europa.eu/eli/reg/2016/679/oj)

### Data Provenance
- **Category:** Data & representations
- **What it actually means:** Traceable information about where data originated, who or what transformed it, which versions were used, and how derived artifacts relate to their sources.
- **Why it matters:** You need provenance to reproduce results, honor usage constraints, investigate contamination, and remove affected data when a source changes.
- **In practice:** Assign immutable dataset versions, record transformation jobs and source identifiers, and carry lineage metadata into embeddings, eval cases, and model artifacts.
- **Common confusion:** A source URL is only one piece of provenance; it does not describe collection time, licensing, filtering, transformation, or downstream use.
- **Related terms:** Dataset Split, Data Deduplication, Provenance Attestation, Grounding
- **Sources:** [W3C PROV Overview](https://www.w3.org/TR/prov-overview/)

### Dataset Split
- **Category:** Data & representations
- **What it actually means:** A documented partition of examples into separate subsets for fitting, development decisions, and final evaluation.
- **Why it matters:** Separation prevents the evidence used to choose a system from also serving as independent proof that the chosen system generalizes.
- **In practice:** Split by the real deployment unit, such as user, repository, organization, or time, rather than randomly dividing correlated rows.
- **Common confusion:** A random split is not automatically independent. Near duplicates, future observations, or records from the same entity can cross the boundary.
- **Related terms:** Eval Set, Overfitting, Data Leakage, Distribution Shift
- **Sources:** [Datasheets for Datasets](https://cacm.acm.org/research/datasheets-for-datasets/)

### Datasheet for Datasets
- **Category:** Security & governance
- **What it actually means:** Structured documentation of a dataset's motivation, composition, collection process, preprocessing, uses, distribution, maintenance, and known limitations.
- **Why it matters:** A dataset is not safe or suitable merely because it is available. Downstream builders need evidence about how it was created and where its assumptions break.
- **In practice:** Publish the datasheet with a versioned dataset, identify who can answer questions, record excluded populations and transformations, and update the document when the dataset changes.
- **Common confusion:** A datasheet documents evidence and intended use. It is not a license, quality guarantee, or substitute for deployment-specific evaluation.
- **Learn it:** [Model, System, and Dataset Cards](../phases/18-ethics-safety-alignment/26-model-system-dataset-cards/)
- **Related terms:** Data Lineage, Data Provenance, Model Card, Dataset Split
- **Sources:** [Datasheets for Datasets](https://arxiv.org/abs/1803.09010)

### Deadline Propagation
- **Category:** Reliability & operations
- **What it actually means:** Passing the remaining end-to-end time budget to downstream calls so each dependency knows how long the original request can still usefully wait.
- **Why it matters:** Independent timeouts can exceed the user's deadline and leave abandoned work consuming capacity after the result is no longer useful.
- **In practice:** Set one request deadline at ingress, subtract elapsed time for each downstream call, cancel expired work, and record which boundary exhausted the budget.
- **Common confusion:** A deadline is an absolute or remaining completion boundary. A retry delay controls when another attempt begins and must fit inside that same budget.
- **Related terms:** Retry with Backoff, Retry Budget, Tail Latency, Service Level Objective (SLO)
- **Sources:** [gRPC Deadlines](https://grpc.io/docs/guides/deadlines/)

### Decode Phase
- **Category:** Infrastructure & serving
- **What it actually means:** The iterative stage of autoregressive inference that generates new tokens one step at a time after the input prefix has been processed.
- **Why it matters:** Decode work has different compute, memory, and scheduling behavior from prefill, so one aggregate latency number can hide the actual serving bottleneck.
- **In practice:** Measure inter-token latency and output throughput separately, account for KV-cache occupancy, and test mixed workloads where active decodes share capacity with new prefills.
- **Common confusion:** Decode phase is not the decoder component of an encoder-decoder model. It names the runtime generation stage.
- **Learn it:** [Disaggregated Prefill and Decode](../phases/17-infrastructure-and-production/17-disaggregated-prefill-decode/)
- **Related terms:** Prefill, Autoregressive, KV Cache, Time per Output Token (TPOT)
- **Sources:** [DistServe](https://arxiv.org/abs/2401.09670)

### Decoder
- **Category:** Models & inference
- **What people say:** The output side of a model.
- **What it actually means:** A component that maps a representation into an output. In an encoder-decoder transformer, the decoder uses masked self-attention and cross-attention to generate outputs. Decoder-only language models instead generate from a single causal stack.
- **Related terms:** Encoder, Transformer, Autoregressive

### Decoding Strategy
- **Category:** Models & inference
- **What it actually means:** The algorithm that converts a model's sequence of next-token scores into selected tokens and a completed output.
- **Why it matters:** Greedy selection, sampling, truncation, and search can produce different quality, diversity, latency, and repeatability from the same logits.
- **In practice:** Define the task's decoding settings, stop rules, and seed behavior in the eval configuration so results can be compared fairly.
- **Common confusion:** Decoding changes how outputs are selected; it does not change the model's trained parameters or add knowledge.
- **Related terms:** Autoregressive, Temperature, Top-k Sampling, Nucleus Sampling (Top-p)
- **Sources:** [The Curious Case of Neural Text Degeneration](https://arxiv.org/abs/1904.09751)

### Defense in Depth
- **Category:** Security & governance
- **What it actually means:** Using independent preventive, detective, and corrective controls at several system boundaries so one failed control does not determine the outcome.
- **Why it matters:** AI systems combine probabilistic models, untrusted content, tools, and external services, making any single filter or prompt an inadequate security boundary.
- **In practice:** Pair instruction controls with narrow permissions, sandboxing, schema validation, approval for consequential actions, monitoring, and a tested recovery path.
- **Common confusion:** More controls are not automatically better. Layers should address distinct failure modes and remain testable rather than repeat the same assumption.
- **Related terms:** Guardrails, Sandbox, Least Privilege, Trust Boundary
- **Sources:** [NIST Glossary: Defense in Depth](https://csrc.nist.gov/glossary/term/defense_in_depth)

### Delegation
- **Category:** Agents & tools
- **What it actually means:** Assigning a bounded subtask to another person or agent together with the needed context, authority, output contract, and return conditions.
- **Why it matters:** Explicit delegation enables specialization and parallel work without losing ownership, scope, or the ability to integrate results.
- **In practice:** Give a reviewer agent the exact files, rubric, evidence, and deadline, then require it to return findings rather than silently modifying the primary artifact.
- **Common confusion:** Sending a vague message to another agent is not reliable delegation. The receiver needs a scope contract and a defined handoff back.
- **Related terms:** Scope Contract, Handoff, Reviewer Agent, Orchestration
- **Sources:** [Building Effective Agents](https://www.anthropic.com/research/building-effective-agents)

### Dense Retrieval
- **Category:** Retrieval & generation
- **What it actually means:** First-stage retrieval that embeds queries and candidates into vector representations and ranks candidates by a similarity function.
- **Why it matters:** It can retrieve paraphrases and semantic matches that share few exact words, complementing lexical methods such as BM25.
- **In practice:** Train or select an embedding model for the domain, index candidate vectors, and evaluate retrieval recall before connecting the results to generation.
- **Common confusion:** Dense retrieval is not a reranker. It searches the collection, while a reranker rescores a smaller candidate set.
- **Related terms:** Embedding, Semantic Search, BM25, Hybrid Retrieval
- **Sources:** [Dense Passage Retrieval](https://aclanthology.org/2020.emnlp-main.550/)

### Diffusion Model
- **Category:** Models & inference
- **What people say:** A model that generates images from noise.
- **What it actually means:** A generative model trained around a progressive noising process and a learned reverse process. Sampling usually begins from noise and applies repeated denoising steps, sometimes in a learned latent space.
- **Common confusion:** Diffusion is a general generative framework, not an image-only technique.
- **Related terms:** Latent Space, VAE (Variational Autoencoder), Inference

### Disaggregated Serving
- **Category:** Infrastructure & serving
- **What it actually means:** A serving architecture that runs prefill and decode work in separately provisioned worker pools and transfers the required attention state between them.
- **Why it matters:** Prefill and decode stress hardware differently, so independent pools can be sized and scheduled for their own bottlenecks instead of competing in one queue.
- **In practice:** Measure state-transfer cost, route requests through compatible model versions, scale each pool from its own demand signal, and test failure recovery between phases.
- **Common confusion:** Disaggregation separates runtime stages. It does not split one model into tensor or pipeline-parallel shards within a stage.
- **Learn it:** [Disaggregated Prefill and Decode](../phases/17-infrastructure-and-production/17-disaggregated-prefill-decode/)
- **Related terms:** Prefill, Decode Phase, Model Serving, Goodput
- **Sources:** [DistServe](https://arxiv.org/abs/2401.09670)

### Distribution Shift
- **Category:** Evaluation & safety
- **What it actually means:** A difference between the data distribution used to build or evaluate a system and the distribution it encounters after deployment.
- **Why it matters:** A model can pass held-out tests yet fail when users, tasks, language, tools, or operating conditions change.
- **In practice:** Define expected deployment slices, monitor performance and input characteristics by slice, and add new failures to a versioned eval set.
- **Common confusion:** Distribution shift is not always model drift. The model may be unchanged while its environment or user population changes.
- **Related terms:** Dataset Split, Eval Set, Overfitting, Model Card
- **Sources:** [WILDS](https://proceedings.mlr.press/v139/koh21a.html)

### DPO (Direct Preference Optimization)
- **Category:** Math & training
- **What people say:** Preference training without a separate reward-model stage.
- **What it actually means:** A preference-optimization objective that trains a policy directly from preferred and rejected response pairs relative to a reference policy. It avoids running an explicit reward model and reinforcement-learning loop during this stage.
- **Common confusion:** DPO still depends on the quality and coverage of preference data and does not eliminate evaluation or alignment risk.
- **Learn it:** [Direct Preference Optimization](../phases/10-llms-from-scratch/08-dpo/)
- **Sources:** [Direct Preference Optimization paper](https://arxiv.org/abs/2305.18290)
- **Related terms:** RLHF (Reinforcement Learning from Human Feedback), SFT (Supervised Fine-Tuning), Alignment

### Dropout
- **Category:** Math & training
- **What people say:** Randomly turning off activations.
- **What it actually means:** During training, randomly setting a fraction of activations to zero encourages the network not to rely on one activation path. It is normally disabled for standard inference, although Monte Carlo dropout deliberately keeps it active to estimate uncertainty.
- **Related terms:** Overfitting, Weight Decay, Activation Function

### Durable Execution
- **Category:** Agents & tools
- **What it actually means:** Running a workflow so its state and completed steps survive process crashes, restarts, or long waits without redoing confirmed side effects.
- **Why it matters:** Agent tasks often span model calls, tools, approvals, and external systems. A transient process should not be the only record of progress.
- **In practice:** Persist each workflow transition, use idempotency keys for external writes, and resume from the latest checkpoint after a worker restarts.
- **Common confusion:** Durable execution does not make every operation safe automatically. Side effects still need idempotency and compensation rules.
- **Related terms:** Checkpoint, Agent State, Idempotency, Approval Gate

### Dynamic Batching
- **Category:** Infrastructure & serving
- **What it actually means:** A runtime policy that forms inference batches from queued requests according to compatible shapes, maximum size, priority, and allowed queue delay.
- **Why it matters:** Grouping requests can improve hardware utilization, but waiting for a batch can make latency worse when traffic is sparse or requests differ sharply.
- **In practice:** Set queue-delay and batch limits from measured latency objectives, separate incompatible request shapes, and compare throughput with tail latency at realistic arrival rates.
- **Common confusion:** Dynamic batching assembles batches from queued work. Continuous batching changes membership while autoregressive generation is already running.
- **Learn it:** [vLLM Serving Internals](../phases/17-infrastructure-and-production/04-vllm-serving-internals/)
- **Related terms:** Admission Control, Continuous Batching, Saturation, Tail Latency
- **Sources:** [NVIDIA Triton: Models and Schedulers](https://docs.nvidia.com/deeplearning/triton-inference-server/user-guide/docs/user_guide/model_configuration.html#scheduling-and-batching)

## E

### Early Fusion
- **Category:** Multimodal systems
- **What it actually means:** Combining raw or low-level representations from several modalities before most task-specific modeling occurs.
- **Why it matters:** Early interaction can expose fine-grained cross-modal relationships, but it also requires compatible representations and careful handling of alignment and missing inputs.
- **In practice:** Convert each modality into a declared token or feature representation, preserve source and position markers, fuse them before the shared backbone, and compare against single-modality and late-fusion baselines.
- **Common confusion:** Early fusion describes where streams are combined in the architecture. It does not guarantee that the model learns useful alignment between them.
- **Learn it:** [Chameleon Early-Fusion Tokens](../phases/12-multimodal-ai/11-chameleon-early-fusion-tokens/)
- **Related terms:** Late Fusion, Multimodal Fusion, Modality Alignment, Token
- **Sources:** [Chameleon: Mixed-Modal Early-Fusion Foundation Models](https://arxiv.org/abs/2405.09818); [Multimodal Machine Learning: A Survey and Taxonomy](https://arxiv.org/abs/1705.09406)

### Eigenvalue
- **Category:** Math & training
- **What people say:** A matrix property used in PCA.
- **What it actually means:** A scalar that describes how a linear transformation scales a corresponding nonzero eigenvector without changing its direction. In covariance-matrix PCA, larger eigenvalues correspond to directions with more variance.
- **Related terms:** Tensor, Feature, Latent Space

### Embedding
- **Category:** Data & representations
- **What people say:** A vector that represents meaning.
- **What it actually means:** A learned mapping from discrete items (words, images, users) to dense vectors in continuous space, where similar items end up close together
- **Common confusion:** Similarity depends on the model, training objective, and metric. Distance in one embedding space does not carry over to another.
- **Why it's called that:** The items are placed, or embedded, in a geometric representation space.
- **Learn it:** [Embeddings](../phases/11-llm-engineering/04-embeddings/)
- **Related terms:** Cosine Similarity, Semantic Search, Vector Database

### Encoder
- **Category:** Models & inference
- **What people say:** The input side of a model.
- **What it actually means:** A component that transforms input into a representation. A transformer encoder commonly uses non-causal self-attention, subject to any masks, so each position can incorporate context from across the input.
- **Common confusion:** Encoder-only models can produce outputs through task heads even though they are not typically used for autoregressive text generation.
- **Related terms:** Decoder, Transformer, Embedding

### Epoch
- **Category:** Math & training
- **What people say:** One pass through the training data.
- **What it actually means:** One traversal of the defined training dataset. In distributed or sampled training, the exact implementation of an epoch depends on the data loader and sampling policy.
- **Common confusion:** More epochs do not guarantee better generalization; evaluate on held-out data.
- **Related terms:** Batch Size, Overfitting, Eval Set

### Error Budget
- **Category:** Reliability & operations
- **What it actually means:** The amount of unsuccessful service allowed by a service-level objective over its measurement window before the objective is exhausted.
- **Why it matters:** It gives reliability and product work a shared decision boundary: teams can spend remaining budget on change while slowing risk when user-visible failure consumes it.
- **In practice:** Derive the budget from the SLO, track burn by cause and user segment, define release actions before exhaustion, and avoid resetting the accounting after an incident.
- **Common confusion:** An error budget is not a quota for causing incidents. It is an operating policy derived from a user-facing reliability target.
- **Related terms:** Service Level Objective (SLO), Service Level Indicator (SLI), Availability, Incident Response
- **Sources:** [Google SRE Workbook: Error Budget Policy](https://sre.google/workbook/error-budget-policy/)

### Eval Set
- **Category:** Evaluation & safety
- **Aliases:** Evaluation set
- **What it actually means:** A versioned collection of inputs, expected properties, scoring rules, and metadata used to measure an AI system against a defined capability or risk.
- **Why it matters:** A repeatable set turns vague quality claims into comparable evidence and catches regressions after prompts, models, tools, or retrieval change.
- **In practice:** Keep representative support questions, adversarial instructions, expected citations, and failure labels in a reviewed dataset that is separate from development examples.
- **Common confusion:** A development eval guides iteration, a final held-out test estimates performance after choices are fixed, and a standardized benchmark supports comparison under a shared protocol. Repeated tuning against any held-out set leaks test information and inflates results.
- **Learn it:** [Eval-Driven Agent Development](../phases/14-agent-engineering/30-eval-driven-agent-development/)
- **Related terms:** Evaluation (Eval), Regression Test, LLM-as-a-Judge, Verification Gate

### Evaluation (Eval)
- **Category:** Evaluation & safety
- **Aliases:** Eval
- **What it actually means:** A defined process for measuring model or system behavior on representative tasks using explicit success criteria, data, scorers, and review procedures.
- **Why it matters:** You cannot improve reliability if success is only a subjective impression from a few demos.
- **In practice:** Run the same customer-support scenarios before and after changing retrieval, score correctness and citation support, and inspect failures by category.
- **Common confusion:** A benchmark score is one evaluation result, not a complete account of production quality.
- **Learn it:** [LLM Evaluation](../phases/11-llm-engineering/10-evaluation/)
- **Related terms:** Eval Set, LLM-as-a-Judge, Cost per Successful Task, Regression Test

### Exact Match (EM)
- **Category:** Evaluation & safety
- **What it actually means:** A metric that counts an output as correct only when its normalized representation exactly equals an accepted reference answer.
- **Why it matters:** It is deterministic and easy to audit for tasks with one canonical answer, but it exposes no partial credit.
- **In practice:** Define normalization and all accepted references before evaluation, then pair exact match with task-specific checks when several outputs can be valid.
- **Common confusion:** A low exact-match score can reflect harmless formatting differences, while a matching string can still be unsupported or unsafe in context.
- **Related terms:** ROUGE, Eval Set, Structured Output, Pass@k
- **Sources:** [SQuAD](https://aclanthology.org/D16-1264/)

### Expert Parallelism
- **Category:** Infrastructure & serving
- **What it actually means:** Distributing mixture-of-experts subnetworks across devices and routing each token's activations to the devices that host its selected experts.
- **Why it matters:** Sparse experts increase model capacity without executing every expert for every token, but routing introduces communication, load-balance, and placement constraints.
- **In practice:** Measure token distribution by expert, provision communication bandwidth, cap or route overflow deliberately, and test quality when traffic produces uneven expert demand.
- **Common confusion:** Expert parallelism partitions experts selected by a router. Tensor parallelism partitions the tensor operations inside layers.
- **Learn it:** [Mixture of Experts](../phases/07-transformers-deep-dive/11-mixture-of-experts/)
- **Related terms:** MoE (Mixture of Experts), Tensor Parallelism, Pipeline Parallelism, Model Serving
- **Sources:** [GShard](https://arxiv.org/abs/2006.16668)

## F

### Feature
- **Category:** Data & representations
- **What people say:** A column in a dataset.
- **What it actually means:** An individual measurable property of the data. In classical ML, you engineer features by hand. In deep learning, the network learns features automatically from raw data.
- **Common confusion:** A stored column can contain several useful features, and a learned representation can contain features with no simple human label.
- **Related terms:** Embedding, Latent Space, Inductive Bias

### Few-Shot
- **Category:** Prompting & context
- **What people say:** Give the model a few examples in the prompt.
- **What it actually means:** In-context learning that includes a small set of demonstrations before the target input so the model can infer the desired task, format, or decision boundary.
- **Why it matters:** Example quality and coverage matter more than a universal example count. Poor or contradictory demonstrations can reduce reliability.
- **Related terms:** Zero-Shot, In-Context Learning, Prompt Engineering, Context Window

### Fine-tuning
- **Category:** Math & training
- **What people say:** Training a model on your data.
- **What it actually means:** Continuing training from pretrained parameters on a narrower dataset or objective. Depending on the method, you may update all parameters, selected parameters, or added adapter parameters.
- **Why it matters:** Fine-tuning can adapt behavior, style, format, or task performance, but it is not a dependable replacement for retrieval when facts must stay current or traceable.
- **Common confusion:** Fine-tuning can influence encoded knowledge, but it does not simply append records to a searchable database inside the model.
- **Learn it:** [Fine-Tuning and LoRA](../phases/11-llm-engineering/08-fine-tuning-lora/)
- **Related terms:** SFT (Supervised Fine-Tuning), LoRA (Low-Rank Adaptation), QLoRA, RAG (Retrieval-Augmented Generation)

### Flaky Test
- **Category:** AI-native development
- **What it actually means:** A test that can pass and fail across equivalent runs without a relevant change to the code or intended test environment.
- **Why it matters:** Flakiness weakens verification gates and can train people or agents to ignore real failures or retry until they obtain a false pass.
- **In practice:** Preserve the failing seed and environment, quarantine only with an owner and deadline, then fix uncontrolled time, concurrency, network, order, or shared-state dependencies.
- **Common confusion:** A test that consistently exposes an intermittent product bug is valuable evidence, not necessarily a flaky test.
- **Related terms:** Regression Test, Test Oracle, Retry with Backoff, Verification Gate
- **Sources:** [De-Flake Your Tests](https://conferences.computer.org/icsme/pdfs/ICSME2020-1oOutvkGTwF4GyVvNtr3Mm/561900a736/561900a736.pdf)

### FlashAttention
- **Category:** Infrastructure & serving
- **What it actually means:** An exact attention algorithm that tiles the computation to reduce transfers between accelerator memory levels while avoiding materialization of the full attention matrix in high-bandwidth memory.
- **Why it matters:** Attention can be limited by memory movement rather than arithmetic, especially for long sequences, so an IO-aware kernel can improve usable speed and memory efficiency.
- **In practice:** Use a kernel supported by the model's shapes, masks, dtype, and hardware, verify numerical tolerance, and benchmark end-to-end latency rather than quoting a paper result as a fixed multiplier.
- **Common confusion:** FlashAttention changes how attention is computed, not the mathematical attention result it targets. It is separate from KV caching and quantization.
- **Learn it:** [KV Cache and Flash Attention](../phases/07-transformers-deep-dive/12-kv-cache-flash-attention/)
- **Related terms:** Attention, Self-Attention, KV Cache, Mixed Precision
- **Sources:** [FlashAttention](https://arxiv.org/abs/2205.14135)

### Function Calling
- **Category:** Agents & tools
- **What people say:** A model using tools.
- **What it actually means:** A provider or application interface through which a model emits a structured request naming a tool and its arguments. Application code validates the request, performs the operation, and can return the result for another model step.
- **Common confusion:** The model requests a function call; your trusted code decides whether and how to execute it. Function calling alone is not a complete agent.
- **Learn it:** [Function Calling](../phases/11-llm-engineering/09-function-calling/)
- **Related terms:** Structured Output, Tool Contract, Agent, MCP (Model Context Protocol)

