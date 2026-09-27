## M

### Maximum Marginal Relevance (MMR)
- **Category:** Retrieval & generation
- **What it actually means:** A selection rule that balances relevance to the query with novelty relative to items already selected.
- **Why it matters:** It can reduce redundant chunks so a limited context budget covers more distinct evidence.
- **In practice:** Retrieve a candidate pool, select the next item using a documented relevance-diversity weight, and evaluate both answer quality and source coverage.
- **Common confusion:** MMR diversifies an existing candidate set; it does not retrieve missing evidence or prove that selected passages are correct.
- **Related terms:** Reranker, Chunking, RAG (Retrieval-Augmented Generation), Grounding
- **Sources:** [The Use of MMR, Diversity-Based Reranking for Reordering Documents and Producing Summaries](https://www.cs.cmu.edu/~jgc/publication/MMR_DiversityBased_Reranking_SIGIR_1998.pdf)

### MCP (Model Context Protocol)
- **Category:** Agents & tools
- **What people say:** A standard way for AI applications to connect to tools and context.
- **What it actually means:** An open JSON-RPC protocol for a host to connect to servers that expose tools, resources, prompts, and extensions through defined request, result, discovery, and transport contracts. In revision 2026-07-28, every request carries its protocol version and client capabilities instead of relying on an initialization handshake or protocol session.
- **Common confusion:** MCP standardizes discovery and exchange. It does not decide which tool is safe to call, grant permission, or forbid an application from using explicit state handles.
- **Learn it:** [Model Context Protocol](../phases/11-llm-engineering/14-model-context-protocol/)
- **Sources:** [MCP 2026-07-28 key changes](https://modelcontextprotocol.io/specification/2026-07-28/changelog)
- **Related terms:** Stateless MCP, Multi Round-Trip Request (MRTR), Function Calling, Tool Contract, Least Privilege

### Membership Inference
- **Category:** Security & governance
- **What it actually means:** An attack that estimates whether a particular record or example was included in a model's training data by observing model outputs or other accessible signals.
- **Why it matters:** Even when the model does not reproduce a record verbatim, distinguishable behavior can reveal information about participation in a sensitive dataset.
- **In practice:** Test representative members and non-members under the real query interface, limit unnecessary confidence signals, reduce data exposure, and evaluate privacy defenses against utility requirements.
- **Common confusion:** Membership inference asks whether a record participated in training. Model extraction tries to reproduce model behavior, while direct memorization tests whether content can be recovered.
- **Learn it:** [Differential Privacy for LLMs](../phases/18-ethics-safety-alignment/22-differential-privacy-for-llms/)
- **Related terms:** Data Leakage, Data Minimization, Eval Set, Data Classification
- **Sources:** [Membership Inference Attacks Against Machine Learning Models](https://doi.org/10.1109/SP.2017.41)

### Mixed Precision
- **Category:** Math & training
- **What people say:** Using lower-precision arithmetic for speed and memory savings.
- **What it actually means:** A numerical strategy that uses different data types for different operations, often lower precision for many matrix operations and higher precision for values that need more range or stability.
- **Common confusion:** Speed, memory, and accuracy effects depend on hardware, data type, scaling method, kernels, and model. They are not a fixed multiplier.
- **Related terms:** Tensor, CUDA, NaN (Not a Number), Quantization

### Modality
- **Category:** Multimodal systems
- **What it actually means:** A form of information with its own structure and acquisition process, such as text, image, audio, video, depth, or sensor measurements.
- **Why it matters:** Different modalities have different sampling rates, noise, spatial or temporal structure, and missing-data behavior, so one preprocessing assumption rarely fits all of them.
- **In practice:** Document each modality's source, units, resolution, timing, preprocessing, and missing-value policy before designing alignment or fusion.
- **Common confusion:** A modality is not merely a file extension or feature column. Several encodings can represent one modality, and one sample can contain several modalities.
- **Learn it:** [MIO Any-to-Any Streaming](../phases/12-multimodal-ai/16-mio-any-to-any-streaming/)
- **Related terms:** Multimodal Model, Token, Tensor, Embedding
- **Sources:** [ImageBind: One Embedding Space To Bind Them All](https://arxiv.org/abs/2305.05665); [Multimodal Machine Learning: A Survey and Taxonomy](https://arxiv.org/abs/1705.09406)

### Modality Alignment
- **Category:** Multimodal systems
- **What it actually means:** Learning or establishing correspondences between representations from different modalities so semantically or temporally related items can be matched.
- **Why it matters:** Fusion and cross-modal retrieval fail when the system cannot connect the same event, object, or concept across differently structured inputs.
- **In practice:** Define positive and negative pairs, preserve time or spatial metadata, evaluate mismatched examples, and measure alignment separately from downstream task accuracy.
- **Common confusion:** Alignment makes representations comparable or corresponding. It does not require them to become identical or erase modality-specific information.
- **Learn it:** [Projection Layer Modality Alignment](../phases/19-capstone-projects/60-projection-layer-modality-align/)
- **Related terms:** Shared Embedding Space, Contrastive Learning, Grounding, Multimodal Fusion
- **Sources:** [Learning Transferable Visual Models From Natural Language Supervision](https://proceedings.mlr.press/v139/radford21a.html)

### Model Card
- **Category:** Evaluation & safety
- **What it actually means:** A structured report describing a model's intended uses, evaluation conditions, performance characteristics, limitations, and relevant ethical or safety considerations.
- **Why it matters:** It gives downstream builders context for deciding whether reported evidence applies to their users and deployment conditions.
- **In practice:** Document model version, training and evaluation scope, subgroup results, known failure modes, prohibited uses, and the date of each claim.
- **Common confusion:** A model card communicates evidence and limitations; it is not a certification, warranty, system threat model, or substitute for deployment-specific evaluation.
- **Related terms:** Eval Set, Dataset Split, Distribution Shift, Alignment
- **Sources:** [Model Cards for Model Reporting](https://dl.acm.org/doi/10.1145/3287560.3287596)

### Model Router
- **Category:** AI-native development
- **What it actually means:** A component that selects a model or provider for a request using requirements such as capability, latency, cost, context size, policy, and current availability.
- **Why it matters:** Different tasks and failure conditions justify different models, and routing can improve outcome quality without sending every request to the largest option.
- **In practice:** Send low-risk extraction to a fast model, complex code review to a stronger model, and fail over only to providers that satisfy the same data policy.
- **Common confusion:** Routing is a policy decision. Random load balancing only distributes traffic.
- **Related terms:** Evaluation (Eval), Circuit Breaker, Rate Limit, Cost per Successful Task

### Model Serving
- **Category:** Infrastructure & serving
- **What it actually means:** The runtime and API layer that loads versioned model artifacts, accepts inference requests, schedules execution, manages resources, and returns results under an operational contract.
- **Why it matters:** A capable model can still produce an unreliable product when queueing, batching, placement, versioning, cancellation, and response boundaries are not engineered explicitly.
- **In practice:** Pin model and tokenizer versions, validate request limits, expose readiness and latency signals, control concurrency, and test rollback before routing production traffic.
- **Common confusion:** Model serving is broader than calling inference once and narrower than the complete application, which may also include retrieval, tools, policy, and user state.
- **Learn it:** [Self-Hosted Serving Selection](../phases/17-infrastructure-and-production/28-self-hosted-serving-selection/)
- **Related terms:** Inference, Model Router, Autoscaling, Observability
- **Sources:** [Clipper](https://arxiv.org/abs/1612.03079)

### MoE (Mixture of Experts)
- **Category:** Models & inference
- **What people say:** A large model that activates only part of its parameters for each token.
- **What it actually means:** An architecture with multiple expert subnetworks and a learned router that selects a subset for each input unit, often each token. Sparse activation can increase total parameter capacity without using every expert on every forward pass.
- **Why it matters:** Compute, memory, communication, routing balance, and quality depend on the specific architecture and serving system.
- **Common confusion:** Product names do not prove an MoE architecture unless the model developer discloses it.
- **Learn it:** [Mixture of Experts](../phases/07-transformers-deep-dive/11-mixture-of-experts/)
- **Related terms:** Transformer, Model Router, Parameter

### Multimodal Fusion
- **Category:** Multimodal systems
- **What it actually means:** Combining evidence or learned representations from more than one modality to produce a joint representation, prediction, or generated output.
- **Why it matters:** Modalities can supply complementary evidence, but naïve combination can amplify noise, timing errors, or one dominant stream.
- **In practice:** Establish single-modality baselines, specify the fusion point and masks, test missing and contradictory inputs, and report which modalities drive each evaluated slice.
- **Common confusion:** Fusion is the combination operation. Alignment establishes correspondence, and merely placing two modalities in one request does not prove either occurred successfully.
- **Learn it:** [Cross-Attention Fusion](../phases/19-capstone-projects/61-cross-attention-fusion/)
- **Related terms:** Early Fusion, Late Fusion, Cross-Attention, Modality Alignment
- **Sources:** [Multimodal Deep Learning](https://ai.stanford.edu/~ang/papers/icml11-MultimodalDeepLearning.pdf); [Multimodal Machine Learning: A Survey and Taxonomy](https://arxiv.org/abs/1705.09406)

### Multimodal Model
- **Category:** Multimodal systems
- **What it actually means:** A model that learns from, relates, or generates more than one modality through representation, alignment, fusion, translation, or coordinated prediction.
- **Why it matters:** Multimodal capability depends on how modalities interact, not simply on accepting several input types, and failures can occur at each representation boundary.
- **In practice:** Document supported input and output combinations, evaluate each modality alone and together, test missing or conflicting inputs, and track preprocessing versions with the model.
- **Common confusion:** A pipeline with separate image and text models is multimodal at the system level, but it is not necessarily one jointly trained multimodal model.
- **Learn it:** [MIO Any-to-Any Streaming](../phases/12-multimodal-ai/16-mio-any-to-any-streaming/)
- **Related terms:** Modality, Vision-Language Model (VLM), Multimodal Fusion, Transformer
- **Sources:** [Flamingo: a Visual Language Model for Few-Shot Learning](https://arxiv.org/abs/2204.14198); [Multimodal Machine Learning: A Survey and Taxonomy](https://arxiv.org/abs/1705.09406)

### Multi Round-Trip Request (MRTR)
- **Category:** Agents & tools
- **Aliases:** MRTR
- **What it actually means:** An MCP request pattern in which an operation returns `resultType: input_required` with one or more `inputRequests`, then the client retries the original method with `inputResponses` and the exact returned `requestState`.
- **Why it matters:** It lets a stateless server request user, model, or root input without opening a server-initiated JSON-RPC exchange or storing protocol session state.
- **In practice:** Return an input request from `tools/call`, collect the authorized response in the host, and retry that same tool call with a new JSON-RPC id.
- **Common confusion:** `requestState` is untrusted round-trip data. Integrity-protect it before using it for authorization or business decisions, and do not treat it as a server-side session identifier.
- **Learn it:** [MCP Roots and Elicitation](../phases/13-tools-and-protocols/12-mcp-roots-and-elicitation/)
- **Related terms:** Stateless MCP, MCP (Model Context Protocol), Human-in-the-Loop (HITL), Tool Contract
- **Sources:** [MCP Multi Round-Trip Requests](https://modelcontextprotocol.io/specification/2026-07-28/basic/patterns/mrtr)

## N

### NaN (Not a Number)
- **Category:** Math & training
- **What people say:** A sign that numerical computation failed.
- **What it actually means:** A floating-point value representing an undefined or unrepresentable numerical result. In training, NaNs can come from invalid operations, overflow, unstable normalization, excessive updates, or earlier corrupted values.
- **In practice:** Find the first non-finite tensor, inspect its inputs, and add assertions or anomaly detection near that operation.
- **Related terms:** Mixed Precision, Learning Rate, Gradient

### Normalization
- **Category:** Math & training
- **What people say:** Scaling data to a standard range.
- **What it actually means:** A family of transformations that rescale or recenter inputs, activations, or features using defined statistics. Batch normalization and layer normalization use different axes and behave differently across training and inference.
- **Common confusion:** Normalization can improve optimization stability, but it does not always permit a larger learning rate or improve every architecture.
- **Related terms:** Tensor, Activation Function, Mixed Precision

### Nucleus Sampling (Top-p)
- **Category:** Models & inference
- **Aliases:** Top-p sampling
- **What it actually means:** A decoding method that samples from the smallest set of next-token candidates whose cumulative probability reaches a chosen threshold.
- **Why it matters:** The candidate-set size adapts to the distribution, retaining more options when uncertainty is broad and fewer when probability is concentrated.
- **In practice:** Evaluate the threshold with temperature and stop settings held constant, and record the complete decoding configuration with every result.
- **Common confusion:** Top-p is a probability-mass threshold, while top-k always keeps a fixed maximum number of candidates.
- **Related terms:** Top-k Sampling, Temperature, Decoding Strategy, Softmax
- **Sources:** [The Curious Case of Neural Text Degeneration](https://arxiv.org/abs/1904.09751)

## O

### Observability
- **Category:** AI-native development
- **What it actually means:** The ability to understand an AI system's behavior from recorded inputs, outputs, state transitions, tool calls, timings, costs, errors, and evaluation signals.
- **Why it matters:** AI failures often span model, retrieval, tools, and orchestration. You need correlated evidence to locate the failing boundary.
- **In practice:** Record a trace ID across retrieval, model calls, tool execution, approvals, and final scoring while applying redaction and access controls.
- **Common confusion:** Logging collects events. Observability makes those events structured and connected enough to answer operational questions.
- **Learn it:** [Agent Observability Platforms](../phases/14-agent-engineering/24-agent-observability-platforms/)
- **Related terms:** Trace, Evaluation (Eval), Agent State, Time to First Token (TTFT)

### Optimizer
- **Category:** Math & training
- **What people say:** The algorithm that updates weights.
- **What it actually means:** An algorithm that transforms gradients into parameter updates. Plain stochastic gradient descent is a simple baseline; momentum, Adam, and other optimizers change the update using history or adaptive scaling. Each choice has different memory, stability, and tuning behavior.
- **Common confusion:** The optimizer consumes gradients; backpropagation computes them.
- **Related terms:** Adam (Optimizer), AdamW, Gradient, Learning Rate

### Orchestration
- **Category:** Agents & tools
- **What it actually means:** The control logic that sequences, branches, delegates, retries, pauses, resumes, and terminates work across model and tool steps.
- **Why it matters:** Reliable agent behavior depends on explicit workflow decisions outside the model, especially when tasks have dependencies or consequential side effects.
- **In practice:** Encode stable steps as a workflow or state machine, expose bounded decisions to the model, and persist transitions before external writes.
- **Common confusion:** Orchestration is not synonymous with autonomy or multi-agent systems; one agent can be orchestrated through a deterministic workflow.
- **Related terms:** Agent Harness, Planning, Delegation, Durable Execution
- **Sources:** [Building Effective Agents](https://www.anthropic.com/research/building-effective-agents)

### Overfitting
- **Category:** Math & training
- **What people say:** The model memorized the training data.
- **What it actually means:** A generalization gap in which performance on training data is substantially better than performance on representative unseen data. Memorization can contribute, but the operational symptom is poor generalization.
- **In practice:** Compare training and held-out metrics, inspect subgroup failures, and test changes such as data quality, regularization, early stopping, or model capacity.
- **Related terms:** Underfitting, Dropout, Weight Decay, Eval Set

## P

### Paged KV Cache
- **Category:** Infrastructure & serving
- **What it actually means:** A KV-cache memory manager that stores attention state in fixed-size blocks and maps logical sequence positions to physical blocks instead of requiring one contiguous allocation per sequence.
- **Why it matters:** Variable sequence lengths create fragmentation and unpredictable growth, so block-based allocation can improve usable memory and enable flexible sharing.
- **In practice:** Select block size from workload measurements, track allocation and eviction, isolate state between requests, and test cancellation and prefix sharing under memory pressure.
- **Common confusion:** Paged KV cache manages runtime attention-state memory. It does not move model parameters to disk or extend the model's trained context limit.
- **Learn it:** [vLLM Serving Internals](../phases/17-infrastructure-and-production/04-vllm-serving-internals/)
- **Related terms:** KV Cache, Prefix Caching, Context Window, Model Serving
- **Sources:** [Efficient Memory Management for Large Language Model Serving with PagedAttention](https://arxiv.org/abs/2309.06180)

### Parameter
- **Category:** Models & inference
- **What people say:** A number used to describe model size.
- **What it actually means:** A value learned during training, commonly a weight, bias, embedding element, or normalization parameter. Parameter count is one measure of model capacity, but it does not directly determine quality, memory, or serving cost.
- **Common confusion:** Memory per parameter depends on numerical format, quantization metadata, sharding, optimizer state, activations, and runtime overhead.
- **Related terms:** Weight, MoE (Mixture of Experts), Quantization

### Pass@k
- **Category:** Evaluation & safety
- **What it actually means:** Across a task set, the fraction of tasks for which at least one of k sampled candidates passes a defined correctness test.
- **Why it matters:** It measures the value of sampling several attempts for tasks such as code generation where an automatic verifier can check each candidate.
- **In practice:** Generate candidates independently under a fixed configuration, run the same isolated tests on each, and report k with the sampling and estimator details.
- **Common confusion:** Pass@k is not single-attempt accuracy, and a higher score can reflect a larger attempt budget rather than a better first answer.
- **Related terms:** Coding Agent, Regression Test, Eval Set, Test Oracle
- **Sources:** [Evaluating Large Language Models Trained on Code](https://arxiv.org/abs/2107.03374)

### Patch
- **Category:** AI-native development
- **What it actually means:** A reviewable representation of changes to one or more files, usually expressed as additions and deletions against a known base revision.
- **Why it matters:** A patch gives people and agents a narrow artifact to inspect, test, apply, or reject without accepting an entire working directory.
- **In practice:** Ask a coding agent to return a unified diff, then verify that it touches only allowed files and applies cleanly to the expected commit.
- **Common confusion:** A patch captures file changes, not the reasoning, test evidence, or approval needed to ship them.
- **Learn it:** [Workbench for Real Repositories](../phases/14-agent-engineering/41-workbench-for-real-repos/)
- **Related terms:** Coding Agent, Worktree, Scope Contract, Regression Test

### Patch Embedding
- **Category:** Multimodal systems
- **What it actually means:** A learned projection that converts an image patch into a fixed-width vector used as one element of a transformer input sequence.
- **Why it matters:** It creates the interface between a spatial image grid and a sequence model, with patch size controlling token count and retained local detail.
- **In practice:** Record patch and image dimensions, handle padding or resizing explicitly, add position information, and measure how resolution changes affect both accuracy and token cost.
- **Common confusion:** A patch embedding is the vector representation of a patch, not a semantic object detector or a guarantee that patch boundaries match visual entities.
- **Learn it:** [Vision Transformer Patch Tokens](../phases/12-multimodal-ai/01-vision-transformer-patch-tokens/)
- **Related terms:** Vision Transformer (ViT), Image Token, Embedding, Token
- **Sources:** [An Image is Worth 16x16 Words](https://arxiv.org/abs/2010.11929)

### Perplexity
- **Category:** Models & inference
- **What people say:** How surprised a language model is by a dataset.
- **What it actually means:** The exponentiated average negative log-likelihood under a stated tokenization and logarithm convention. Lower values mean the model assigned higher probability to the evaluated sequence.
- **Common confusion:** Perplexity is not comparable across different tokenizers or evaluation setups and does not directly measure factuality or usefulness.
- **Related terms:** Cross-Entropy, Token, Evaluation (Eval)

### Pipeline Parallelism
- **Category:** Infrastructure & serving
- **What it actually means:** Partitioning sequential groups of model layers across devices and moving microbatches or requests through those stages as a pipeline.
- **Why it matters:** It lets models exceed one device's memory, but stage imbalance, pipeline bubbles, activation transfers, and failure coordination affect usable performance.
- **In practice:** Balance stage cost, choose a microbatch schedule, measure idle time and interconnect traffic, and keep model and checkpoint partition metadata versioned.
- **Common confusion:** Pipeline parallelism divides layers by depth. Tensor parallelism divides tensor operations within a layer.
- **Learn it:** [Scaling and Distributed Training](../phases/10-llms-from-scratch/05-scaling-distributed/)
- **Related terms:** Tensor Parallelism, Expert Parallelism, Batch Size, Model Serving
- **Sources:** [GPipe](https://arxiv.org/abs/1811.06965)

### Planning
- **Category:** Agents & tools
- **What it actually means:** Constructing, selecting, or revising a sequence of actions and dependencies intended to move from the current state to a goal.
- **Why it matters:** Explicit plans make assumptions and ordering visible before an agent commits to expensive or irreversible actions.
- **In practice:** Ask for a short dependency-aware plan, validate it against available tools and permissions, then re-plan when observations invalidate an assumption.
- **Common confusion:** A generated plan is a proposal, not proof that the steps are feasible, sufficient, or safe.
- **Related terms:** Agent State, ReAct, Orchestration, Verification Gate
- **Sources:** [LLM+P](https://arxiv.org/abs/2304.11477)

### Postmortem
- **Category:** Reliability & operations
- **What it actually means:** A durable incident record that explains impact, detection, response, contributing conditions, recovery, and owned follow-up actions without assigning blame as a substitute for analysis.
- **Why it matters:** A resolved outage still has value as evidence. Capturing system conditions and decisions turns one event into improvements that reduce recurrence and response time.
- **In practice:** Build the timeline from traces and logs, distinguish triggering events from contributing conditions, assign dated actions, and review whether each action changed the relevant control.
- **Common confusion:** A postmortem is not a meeting transcript or a search for one person's mistake. It should produce testable system improvements.
- **Related terms:** Incident Response, Regression Test, Audit Log, Observability
- **Sources:** [Google SRE: Postmortem Culture](https://sre.google/sre-book/postmortem-culture/)

### Precision & Recall
- **Category:** Evaluation & safety
- **What people say:** Two metrics for classification or retrieval quality.
- **What it actually means:** Precision asks how many flagged items were correct; recall asks how many relevant items were found. When you change the decision threshold for one fixed scoring model, improving recall often lowers precision and vice versa. A better model can improve both. F1 is their harmonic mean.
- **Common confusion:** The right threshold and metric depend on the cost of each error and the prevalence of the target class.
- **Related terms:** Eval Set, Semantic Search, Guardrails

### Prefill
- **Category:** Infrastructure & serving
- **Aliases:** Prefill Phase
- **What it actually means:** The initial inference stage that processes all supplied input tokens to produce their representations and the attention state required for subsequent autoregressive generation.
- **Why it matters:** Prompt shape, queueing, and cache reuse affect prefill cost, and prefill competes differently for compute than decode, so it strongly influences startup latency and serving schedules.
- **In practice:** Record prompt tokens and prefill latency, separate queue time from execution time, compare cached and uncached prefixes, and test long prompts beside active decode traffic.
- **Common confusion:** Prefill is the runtime prompt-processing stage, not the first generated token itself. The first token appears only after prefill and any queueing complete.
- **Learn it:** [Disaggregated Prefill and Decode](../phases/17-infrastructure-and-production/17-disaggregated-prefill-decode/)
- **Related terms:** Decode Phase, KV Cache, Time to First Token (TTFT), Chunked Prefill
- **Sources:** [Sarathi-Serve](https://www.usenix.org/system/files/osdi24-agrawal.pdf); [DistServe](https://arxiv.org/abs/2401.09670)

### Prefix Caching
- **Category:** Infrastructure & serving
- **What it actually means:** Reusing KV-cache blocks produced for an identical eligible token prefix across requests so the serving runtime can skip repeated prefix computation.
- **Why it matters:** Shared system instructions, templates, or documents can consume substantial prefill work, but reuse only helps when token sequences and cache eligibility match.
- **In practice:** Place stable tokens before request-specific content, include model and tokenizer versions in cache identity, isolate tenant-sensitive state, monitor hit rate, and treat eviction as normal.
- **Common confusion:** Prefix caching reuses runtime attention state for exact token prefixes. Prompt caching is a broader provider or application contract, while semantic caching reuses a prior result for a similar request.
- **Learn it:** [Inference Optimization](../phases/10-llms-from-scratch/12-inference-optimization/)
- **Related terms:** Prompt Cache, Semantic Cache, KV Cache, Paged KV Cache
- **Sources:** [SGLang](https://arxiv.org/abs/2312.07104)

### Progressive Disclosure
- **Category:** AI-native development
- **What it actually means:** Supplying a person or model with the minimum useful context first, then revealing deeper detail when the task or evidence requires it.
- **Why it matters:** It limits context noise and cost while keeping authoritative detail available on demand.
- **In practice:** Give a coding agent repository rules and a map first; load full implementation files only after it identifies the relevant module.
- **Common confusion:** Progressive disclosure is staged access to detail, not deliberate withholding of information required for a decision.
- **Learn it:** [Workbench for Real Repositories](../phases/14-agent-engineering/41-workbench-for-real-repos/)
- **Related terms:** Context Engineering, Repository Map, Token Budget, Handoff

### Prompt Cache
- **Category:** Prompting & context
- **What it actually means:** Reuse of provider-side or application-side computation for an identical or eligible prompt prefix so repeated inference avoids some preprocessing work.
- **Why it matters:** Stable instructions and large shared documents can become cheaper or faster across repeated calls when the provider's cache contract is satisfied.
- **In practice:** Place stable policy text before request-specific content, monitor cache-hit metadata, and treat misses as normal because eligibility and lifetime vary by provider.
- **Common confusion:** A prompt cache is a provider or application reuse contract and may use prefix caching internally. Prefix caching specifically reuses eligible exact-token KV state, while semantic caching reuses a prior result for a sufficiently similar request.
- **Learn it:** [Prompt Caching](../phases/11-llm-engineering/15-prompt-caching/)
- **Related terms:** Semantic Cache, Prefix Caching, KV Cache, Time to First Token (TTFT)

### Prompt Engineering
- **Category:** Prompting & context
- **What people say:** Wording instructions so a model follows the task.
- **What it actually means:** Designing model-facing instructions, examples, constraints, and output requirements to improve behavior on a defined task.
- **Common confusion:** Prompt wording cannot compensate for missing evidence, unsafe permissions, poor tool contracts, or absent evaluation.
- **Learn it:** [Prompt Engineering](../phases/11-llm-engineering/01-prompt-engineering/)
- **Related terms:** Context Engineering, Few-Shot, System Prompt, Structured Output

### Prompt Injection
- **Category:** Evaluation & safety
- **What people say:** An adversarial instruction that redirects a model.
- **What it actually means:** An attack or failure mode in which untrusted content influences a model to disregard intended instructions, expose data, misuse tools, or take actions outside the user's goal. The content can arrive directly from a user or indirectly through retrieved pages, files, messages, or tool output.
- **Why it matters:** Models process instructions and data through the same language channel, so input filtering alone cannot reliably separate every malicious instruction from legitimate content.
- **In practice:** Treat external content as untrusted, isolate it from authority-bearing instructions, minimize tool permissions, require approval for consequential writes, and verify outputs and actions.
- **Common confusion:** Prompt injection is not technically the same mechanism as SQL injection, and a stronger system prompt is not a complete defense.
- **Learn it:** [Prompt Injection Defense](../phases/14-agent-engineering/27-prompt-injection-defense/)
- **Sources:** [OWASP prompt injection guidance](https://genai.owasp.org/llmrisk/llm01-prompt-injection/)
- **Related terms:** Least Privilege, Sandbox, Approval Gate, Tool Contract

### Prompt Sensitivity
- **Category:** Prompting & context
- **What it actually means:** Variation in model output or measured performance caused by changes to prompt wording, order, formatting, or examples that preserve the intended task.
- **Why it matters:** A system that succeeds under one convenient phrasing may be unreliable for real users or misleading in evaluation.
- **In practice:** Create semantically equivalent prompt variants, measure variance by case, and keep variants in regression tests instead of optimizing one prompt against one eval set.
- **Common confusion:** Sensitivity is not always a prompt defect; it can reveal ambiguity, weak model robustness, unstable decoding, or an inadequate scoring rule.
- **Related terms:** Prompt Engineering, Eval Set, Regression Test, Few-Shot
- **Sources:** [ProSA](https://aclanthology.org/2024.findings-emnlp.108/)

### Provenance Attestation
- **Category:** Security & governance
- **What it actually means:** Authenticated, machine-readable metadata that binds an artifact to claims about how, where, when, and from which inputs it was produced.
- **Why it matters:** It lets automated policy and reviewers verify supply-chain claims instead of trusting an unsigned build note.
- **In practice:** Generate an attestation in the build system, bind it to artifact digests, sign it with a controlled identity, and verify it before release.
- **Common confusion:** A signature identifies the attester and protects integrity; it does not prove that every claim inside the attestation is true.
- **Related terms:** Data Provenance, Reproducible Build, Audit Log, Verification Gate
- **Sources:** [SLSA Software Attestations](https://slsa.dev/spec/v1.2/attestation-model)

### Purpose Limitation
- **Category:** Security & governance
- **What it actually means:** For personal data, collecting and using it only for specified, explicit purposes unless a new use has an appropriate compatible or authorized basis.
- **Why it matters:** Data that was acceptable for one workflow can create privacy and governance risk when silently reused for model training, evaluation, personalization, or unrelated analytics.
- **In practice:** Record the purpose with each dataset, check new pipelines against it before access, separate incompatible uses, and require a documented decision when the purpose changes.
- **Common confusion:** Purpose limitation governs why data is used. Data minimization governs how much data that purpose actually requires.
- **Related terms:** Data Minimization, Data Classification, AI Risk Assessment, Audit Log
- **Sources:** [General Data Protection Regulation, Article 5(1)(b)](https://eur-lex.europa.eu/eli/reg/2016/679/oj)

## Q

### QLoRA
- **Category:** Math & training
- **What people say:** LoRA with a quantized base model.
- **What it actually means:** A parameter-efficient fine-tuning method that keeps a pretrained base model frozen in a low-bit quantized representation while training LoRA adapters with higher-precision computation where needed.
- **Why it matters:** It can reduce the memory needed to adapt large models, but savings and quality depend on model, rank, optimizer, sequence length, hardware, and implementation.
- **Common confusion:** QLoRA does not guarantee a particular memory footprint or a fixed quality gap from full fine-tuning.
- **Learn it:** [Fine-Tuning and LoRA](../phases/11-llm-engineering/08-fine-tuning-lora/)
- **Sources:** [QLoRA paper](https://arxiv.org/abs/2305.14314)
- **Related terms:** LoRA (Low-Rank Adaptation), Quantization, Fine-tuning

### Quantization
- **Category:** Models & inference
- **What people say:** Storing or computing model values with fewer bits.
- **What it actually means:** Representing weights, activations, or caches with lower-precision formats to reduce memory, bandwidth, or compute cost. Methods differ in calibration, granularity, data type, and whether conversion happens before, during, or after training.
- **Common confusion:** Moving from one nominal bit width to another does not guarantee the same end-to-end memory or speed ratio because metadata, kernels, caches, and hardware support also matter.
- **Related terms:** QLoRA, Mixed Precision, Parameter

## R

### RAG (Retrieval-Augmented Generation)
- **Category:** Retrieval & generation
- **What people say:** A model answering with retrieved knowledge.
- **What it actually means:** A system pattern that retrieves evidence relevant to a request and supplies selected content to a generative model before it answers or acts. Retrieval can use lexical, vector, structured, or hybrid methods.
- **Why it matters:** RAG can make current or private evidence available without encoding it into model weights, but retrieval and grounding must be evaluated separately.
- **Why it's called that:** Retrieval finds evidence, augmentation adds selected evidence to context, and generation produces the response.
- **Learn it:** [Retrieval-Augmented Generation](../phases/11-llm-engineering/06-rag/)
- **Sources:** [Retrieval-Augmented Generation paper](https://arxiv.org/abs/2005.11401)
- **Related terms:** Grounding, Hybrid Retrieval, Reranker, Hallucination

### Rate Limit
- **Category:** AI-native development
- **What it actually means:** A policy that caps requests, tokens, concurrent work, or another resource within a defined time or capacity window.
- **Why it matters:** It protects providers and your own system from overload, uncontrolled spend, and unfair resource use.
- **In practice:** Enforce per-tenant token and concurrency limits, read provider retry metadata, and queue or reject excess work predictably.
- **Common confusion:** A rate limit controls allowed usage. Backpressure propagates downstream capacity constraints through a system.
- **Related terms:** Backpressure, Retry with Backoff, Circuit Breaker

### ReAct
- **Category:** Agents & tools
- **What it actually means:** An agent pattern that interleaves task reasoning, a concrete action, and an observation returned by the environment before deciding the next step.
- **Why it matters:** Environment feedback can correct assumptions and ground later decisions instead of forcing the model to complete the entire task from internal generation alone.
- **In practice:** Expose a small set of typed tools, return concise observations, cap the loop, and verify the final artifact rather than storing private reasoning traces.
- **Common confusion:** ReAct is a prompting and control pattern, not a guarantee of autonomy, correctness, or safe tool use.
- **Related terms:** Agent, Function Calling, Planning, Grounding
- **Sources:** [ReAct](https://arxiv.org/abs/2210.03629)

### Readiness Probe
- **Category:** Reliability & operations
- **What it actually means:** A diagnostic that tells the traffic-routing layer whether a service instance is currently able to accept requests.
- **Why it matters:** A process can be alive while its model is unloaded, dependencies are unavailable, or warmup is incomplete, so sending traffic too early creates avoidable failures.
- **In practice:** Check the minimum dependencies required to serve, fail readiness during startup and draining, keep the probe inexpensive, and do not restart the process solely because readiness is false.
- **Common confusion:** Readiness controls traffic eligibility. Liveness decides whether the process should be restarted, and neither proves that every model response will be correct.
- **Learn it:** [Production LLM Application](../phases/11-llm-engineering/13-production-app/)
- **Related terms:** Autoscaling, Model Serving, Availability, Graceful Degradation
- **Sources:** [Kubernetes Liveness, Readiness, and Startup Probes](https://kubernetes.io/docs/concepts/configuration/liveness-readiness-startup-probes/)

### Recall@K
- **Category:** Retrieval & generation
- **What it actually means:** For one query, Recall@K is `|relevant items intersecting the top k| / |relevant items|`. A dataset score aggregates those per-query values under a stated rule.
- **Why it matters:** It tells you whether a retrieval stage supplies downstream generation or reranking with enough relevant candidates.
- **In practice:** Define relevance judgments, k, the aggregation method, and a policy for queries with no judged relevant items, then inspect queries with zero recalled evidence.
- **Common confusion:** High Recall@K does not mean the top result is good, the ranking is well ordered, or the final answer is grounded. Queries with no relevant items require an explicit exclusion or assigned-value policy because the denominator is zero.
- **Related terms:** Precision & Recall, Eval Set, Reranker, Approximate Nearest Neighbor (ANN)
- **Sources:** [BEIR](https://openreview.net/forum?id=wCu6T5xFjeJ)

### Reciprocal Rank Fusion (RRF)
- **Category:** Retrieval & generation
- **What it actually means:** A rank-fusion method that combines several result lists by summing contributions that decrease with each item's rank in each list.
- **Why it matters:** It can merge lexical, dense, or multi-query rankings without assuming their raw scores share the same scale.
- **In practice:** Retrieve independent candidate lists, deduplicate by stable document identity, apply one versioned fusion constant, and evaluate against each individual retriever.
- **Common confusion:** RRF combines ranks, not embeddings or relevance scores, and it cannot recover an item absent from every input list.
- **Related terms:** Hybrid Retrieval, BM25, Dense Retrieval, Reranker
- **Sources:** [Reciprocal Rank Fusion Outperforms Condorcet and Individual Rank Learning Methods](https://dl.acm.org/doi/10.1145/1571941.1572114)

### Red Teaming
- **Category:** Security & governance
- **What it actually means:** A structured adversarial testing process in which authorized testers seek failures using documented objectives, threat assumptions, cases, and evidence.
- **Why it matters:** Ordinary quality tests rarely explore how a system behaves under manipulation, misuse, conflicting goals, or determined attempts to bypass controls.
- **In practice:** Derive attacks from a threat model, run them in an isolated environment, record reproducible cases, remediate by layer, and convert confirmed failures into regression evals.
- **Common confusion:** A list of jailbreak prompts is not a complete red-team program, and red teaming cannot prove the absence of unknown failures.
- **Related terms:** Threat Model, Guardrails, Prompt Injection, Eval Set
- **Sources:** [Red Teaming Language Models with Language Models](https://arxiv.org/abs/2202.03286)

### Regression Test
- **Category:** AI-native development
- **What it actually means:** A repeatable check that protects behavior known to work, especially after code, prompt, model, retrieval, or tool changes.
- **Why it matters:** AI system changes can improve average quality while silently reintroducing a previously fixed failure.
- **In practice:** Turn a corrected prompt-injection incident into a permanent eval case that must pass before the next deployment.
- **Common confusion:** A regression test guards a specific expected behavior. A broad benchmark estimates performance across a wider task distribution.
- **Learn it:** [Eval-Driven Agent Development](../phases/14-agent-engineering/30-eval-driven-agent-development/)
- **Related terms:** Eval Set, Verification Gate, Patch, Evaluation (Eval)

### ReLU
- **Category:** Math & training
- **What people say:** A simple activation function.
- **What it actually means:** Rectified Linear Unit, defined as `f(x) = max(0, x)`. It is inexpensive and has a non-saturating positive branch, though zero gradients on negative inputs can create inactive units.
- **Related terms:** Activation Function, Gradient, CNN (Convolutional Neural Network)

### Repository Instructions
- **Category:** AI-native development
- **What it actually means:** Version-controlled guidance that tells coding agents how a repository is organized, which commands and conventions apply, what boundaries to respect, and how to verify work.
- **Why it matters:** It turns repeated tribal knowledge into local context that travels with the code and can vary by subproject.
- **In practice:** Keep an `AGENTS.md` at the repository root, add narrower files for subdirectories, and include exact build, test, generated-file, security, and contribution rules.
- **Common confusion:** Repository instructions complement source code and human documentation; they do not override the user's current request or guarantee that an agent follows them correctly.
- **Related terms:** Repository Map, Scope Contract, Coding Agent, Progressive Disclosure
- **Sources:** [AGENTS.md specification](https://agents.md/)

### Repository Map
- **Category:** AI-native development
- **What it actually means:** A compact, maintained description of a repository's important directories, ownership boundaries, entry points, build commands, tests, generated files, and local instructions.
- **Why it matters:** It helps a coding agent find the right evidence before loading large files or editing the wrong subsystem.
- **In practice:** Generate an index from the tree and manifests, then enrich it with authoritative notes about module boundaries and validation commands.
- **Common confusion:** A raw file tree shows names. A repository map explains which paths matter and how they relate to a task.
- **Learn it:** [Repository Memory and State](../phases/14-agent-engineering/34-repo-memory-and-state/)
- **Related terms:** Coding Agent, Progressive Disclosure, Scope Contract, Context Engineering

### Reproducible Build
- **Category:** AI-native development
- **What it actually means:** A build whose declared source, environment, and instructions can be independently rerun to produce bit-for-bit identical specified artifacts.
- **Why it matters:** It makes an artifact verifiable beyond the machine or agent that originally produced it and exposes hidden build inputs.
- **In practice:** Pin toolchains and dependencies, remove timestamps and unstable ordering, capture the environment, then compare independently rebuilt artifact digests.
- **Common confusion:** A build that succeeds twice is repeatable evidence, but reproducibility requires the declared independent conditions and identical outputs.
- **Related terms:** Repository Instructions, Verification Gate, Provenance Attestation, Software Bill of Materials (SBOM)
- **Sources:** [Reproducible Builds definition](https://reproducible-builds.org/docs/definition/)

### Reranker
- **Category:** Retrieval & generation
- **What it actually means:** A second-stage model or scoring function that reorders a small candidate set using a richer comparison between the query and each candidate.
- **Why it matters:** Fast first-stage retrieval maximizes candidate coverage, while reranking can improve which evidence reaches the limited context window.
- **In practice:** Retrieve 50 candidates with hybrid search, score each query-document pair with a cross-encoder, and pass the top 5 supported chunks to generation.
- **Common confusion:** A reranker does not search the entire corpus. It only reorders candidates that retrieval already found.
- **Related terms:** Hybrid Retrieval, Semantic Search, RAG (Retrieval-Augmented Generation)

### Retry Budget
- **Category:** Reliability & operations
- **What it actually means:** A bound on retry traffic, usually expressed relative to original requests or over a time window, that prevents retries from consuming unbounded capacity.
- **Why it matters:** When a dependency slows or fails, unrestricted retries multiply load exactly when the system has the least spare capacity.
- **In practice:** Count retries separately from first attempts, cap them by service and tenant, honor deadlines, use jittered backoff, and stop retrying non-transient or non-idempotent failures.
- **Common confusion:** A retry budget limits extra attempts. An error budget measures user-visible unreliability allowed by an SLO.
- **Related terms:** Retry with Backoff, Error Budget, Rate Limit, Admission Control
- **Sources:** [Google SRE: Addressing Cascading Failures](https://sre.google/sre-book/addressing-cascading-failures/)

### Retry with Backoff
- **Category:** AI-native development
- **What it actually means:** Repeating a failed transient operation after progressively longer delays, usually with randomized jitter and a strict retry limit.
- **Why it matters:** Immediate synchronized retries can worsen an outage, consume rate limits, and duplicate side effects.
- **In practice:** Retry a provider timeout after bounded exponential delays, honor server retry guidance, and reuse an idempotency key for any write.
- **Common confusion:** Do not retry permanent validation or permission errors, and do not retry non-idempotent operations without a duplication strategy.
- **Related terms:** Idempotency, Rate Limit, Circuit Breaker, Backpressure

### Reviewer Agent
- **Category:** AI-native development
- **What it actually means:** An agent assigned to inspect another agent's artifact or decision against explicit criteria and return findings or a verdict.
- **Why it matters:** Separation of roles can catch omissions, but it only helps when the reviewer receives independent evidence and a concrete rubric.
- **In practice:** After one agent produces a patch, give a separate reviewer the diff, scope contract, repository rules, and test output, then require line-specific findings.
- **Common confusion:** A second model call is not automatically independent or correct. Shared context, model bias, and vague criteria can reproduce the same mistake.
- **Learn it:** [Reviewer Agent](../phases/14-agent-engineering/39-reviewer-agent/)
- **Related terms:** Coding Agent, Verification Gate, Scope Contract, LLM-as-a-Judge

### RLHF (Reinforcement Learning from Human Feedback)
- **Category:** Math & training
- **What people say:** Training a model from human preferences.
- **What it actually means:** A family of pipelines that uses human feedback to learn a reward or preference signal and then optimizes a model policy against that signal. Implementations vary and need not all use the same reinforcement-learning algorithm.
- **Common confusion:** RLHF optimizes a proxy learned from collected feedback. It does not guarantee broad alignment with every user or situation.
- **Learn it:** [Reinforcement Learning from Human Feedback](../phases/10-llms-from-scratch/07-rlhf/)
- **Sources:** [InstructGPT paper](https://arxiv.org/abs/2203.02155)
- **Related terms:** DPO (Direct Preference Optimization), SFT (Supervised Fine-Tuning), Alignment

### Rollback
- **Category:** Reliability & operations
- **What it actually means:** Restoring a previously known deployment or configuration when the current release violates operational, quality, or safety criteria.
- **Why it matters:** Agent and model changes can fail in production despite pre-deployment evaluation, so recovery must be designed before rollout.
- **In practice:** Retain versioned artifacts and configuration, define rollback triggers, rehearse the command and data implications, and verify service health after restoration.
- **Common confusion:** Code rollback does not automatically reverse database migrations, external side effects, cached outputs, or data written by the bad release.
- **Related terms:** Canary Release, Checkpoint, Regression Test, Durable Execution
- **Sources:** [Kubernetes Deployments: Rolling Back](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/#rolling-back-a-deployment)

### ROUGE
- **Category:** Evaluation & safety
- **What people say:** A reference-overlap metric often used for summaries.
- **What it actually means:** A family of metrics that compares generated text with reference text using units such as n-gram overlap or longest common subsequence.
- **Common confusion:** Surface overlap can miss semantic equivalence and can reward copied wording without proving factual quality.
- **Related terms:** Evaluation (Eval), Precision & Recall, LLM-as-a-Judge

