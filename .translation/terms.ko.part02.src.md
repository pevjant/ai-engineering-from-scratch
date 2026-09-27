## G

### GAN (Generative Adversarial Network)
- **Category:** Models & inference
- **What people say:** Two neural networks competing during training.
- **What it actually means:** A generator network tries to create realistic data while a discriminator network tries to tell real from fake. They train together: the generator gets better at fooling the discriminator, and the discriminator gets better at detecting fakes.
- **Related terms:** Loss Function, Latent Space, Diffusion Model

### Goodput
- **Category:** Infrastructure & serving
- **What it actually means:** The rate of completed requests that satisfy defined service constraints, such as both time-to-first-token and per-token latency objectives, under a stated workload.
- **Why it matters:** Raw throughput can rise while users experience more slow requests. Goodput counts only work that meets the service contract.
- **In practice:** Declare the request distribution and latency thresholds, count only compliant completions, report percentiles beside the aggregate rate, and avoid comparing systems under different objectives.
- **Common confusion:** Goodput is not all completed throughput and is not a universal property of a model. It depends on workload and success thresholds.
- **Learn it:** [Inference Metrics and Goodput](../phases/17-infrastructure-and-production/08-inference-metrics-goodput/)
- **Related terms:** Service Level Objective (SLO), Time to First Token (TTFT), Time per Output Token (TPOT), Cost per Successful Task
- **Sources:** [DistServe](https://arxiv.org/abs/2401.09670)

### GPT
- **Category:** Models & inference
- **What people say:** A generic name for any chatbot.
- **What it actually means:** Generative Pre-trained Transformer, a family label for generative transformer models pretrained on sequence-prediction objectives and adapted for downstream use. Product names and model architectures should not be treated as interchangeable.
- **Why it's called that:** Generative describes output production, pre-trained describes the initial broad training stage, and transformer identifies the architecture family.
- **Related terms:** Transformer, Autoregressive, LLM (Large Language Model)

### Graceful Degradation
- **Category:** Reliability & operations
- **What it actually means:** Preserving a bounded core service when capacity or dependencies are impaired by reducing optional quality, features, freshness, or workload instead of failing every request.
- **Why it matters:** AI systems often depend on several slow or fallible components, so an explicit reduced mode can protect essential user outcomes during partial failure.
- **In practice:** Predefine which capabilities may be disabled, keep the reduced mode visible to operators, protect safety checks, test the fallback under dependency failure, and restore full service deliberately. Tell users when correctness, safety, freshness, or a promised contract materially changes.
- **Common confusion:** Graceful degradation is not silently returning a worse answer as if nothing happened. Operators always need visibility; users need disclosure when the reduced mode materially changes the result or service contract.
- **Learn it:** [Production LLM Application](../phases/11-llm-engineering/13-production-app/)
- **Related terms:** Circuit Breaker, Load Shedding, Model Router, Availability
- **Sources:** [Google SRE: Addressing Cascading Failures](https://sre.google/sre-book/addressing-cascading-failures/)

### Gradient
- **Category:** Math & training
- **What people say:** The slope of the loss.
- **What it actually means:** A vector of partial derivatives pointing in the direction of steepest increase. In ML, you go opposite to the gradient (gradient descent) to minimize the loss.
- **Common confusion:** Optimizers can transform, average, clip, or adapt gradients instead of taking a plain negative-gradient step.
- **Related terms:** Backpropagation, Gradient Descent, Optimizer

### Gradient Accumulation
- **Category:** Math & training
- **What it actually means:** Summing or averaging gradients from several microbatches before performing one optimizer update.
- **Why it matters:** It lets you approximate a larger effective batch when one device cannot hold all examples and activations at once.
- **In practice:** Scale the loss consistently, call the optimizer only after the chosen number of microbatches, and measure whether normalization or distributed synchronization changes behavior.
- **Common confusion:** Gradient accumulation reduces per-step activation memory, but it does not reproduce every property of processing the full batch simultaneously.
- **Related terms:** Batch Size, Mixed Precision, Optimizer, Backpropagation
- **Sources:** [PyTorch AMP examples: Gradient accumulation](https://docs.pytorch.org/docs/stable/notes/amp_examples.html#gradient-accumulation)

### Gradient Clipping
- **Category:** Math & training
- **What it actually means:** Limiting gradient values or their combined norm before an optimizer update when they exceed a chosen threshold.
- **Why it matters:** It can prevent an unusually large gradient from destabilizing a training step and producing non-finite values.
- **In practice:** Log unclipped norms, clip after unscaling mixed-precision gradients, and investigate repeated clipping instead of treating it as a substitute for diagnosing instability.
- **Common confusion:** Clipping controls update magnitude; it does not repair invalid data, a broken loss, or a consistently unsuitable learning rate.
- **Related terms:** Gradient, NaN (Not a Number), Mixed Precision, Learning Rate
- **Sources:** [On the difficulty of training recurrent neural networks](https://arxiv.org/abs/1211.5063)

### Gradient Descent
- **Category:** Math & training
- **What people say:** Walking downhill on the loss surface.
- **What it actually means:** A family of optimization updates that move parameters using the negative gradient of an objective, usually estimated from batches rather than the entire dataset.
- **Related terms:** Gradient, Learning Rate, Optimizer

### Grounding
- **Category:** Retrieval & generation
- **What it actually means:** Connecting a generated answer or action to evidence, state, or observations that the system can identify and check.
- **Why it matters:** Grounding gives the system a basis beyond unconstrained generation and makes unsupported claims easier to detect.
- **In practice:** Retrieve a policy section, require the answer to cite it, and reject claims that the cited passage does not support.
- **Common confusion:** Adding documents to a prompt creates an opportunity for grounding. It does not guarantee the model will use them correctly.
- **Learn it:** [Retrieval-Augmented Generation](../phases/11-llm-engineering/06-rag/)
- **Related terms:** RAG (Retrieval-Augmented Generation), Hallucination, Verification Gate, Reranker

### Guardrails
- **Category:** Evaluation & safety
- **What people say:** Safety filters around a model.
- **What it actually means:** System controls that constrain inputs, tool use, outputs, permissions, and escalation. They can include schemas, policy checks, classifiers, allowlists, sandboxing, approvals, and post-action verification.
- **Why it matters:** No single filter covers all failure modes, so controls should be layered according to risk.
- **Common confusion:** Guardrails reduce risk; they do not prove that an AI system is safe.
- **Learn it:** [Guardrails](../phases/11-llm-engineering/12-guardrails/)
- **Related terms:** Least Privilege, Approval Gate, Sandbox, Evaluation (Eval)

## H

### Hallucination
- **Category:** Evaluation & safety
- **What people say:** The model is lying.
- **What it actually means:** Generated content that is false, unsupported by the available evidence, or inconsistent with the task's source of truth. It can arise even when the output is fluent and the model is not attempting to deceive.
- **Why it matters:** You usually cannot inspect whether a statement existed in training data, so production checks should focus on support, correctness, and traceability.
- **In practice:** Require cited evidence for factual answers and evaluate whether each citation actually supports the associated claim.
- **Common confusion:** A hallucination is an output-quality failure, not a diagnosis of model intent.
- **Related terms:** Grounding, RAG (Retrieval-Augmented Generation), Verification Gate

### Handoff
- **Category:** AI-native development
- **What it actually means:** A structured transfer of a task between people or agents that preserves the objective, current state, evidence, decisions, constraints, and remaining work.
- **Why it matters:** A good handoff prevents the next worker from reconstructing the entire task from a long transcript or repeating completed actions.
- **In practice:** Pass the accepted plan, changed files, test commands and results, unresolved risks, and exact next action in a compact task packet.
- **Common confusion:** A summary says what happened. A handoff also says what state is authoritative and what should happen next.
- **Learn it:** [Multi-Session Handoff](../phases/14-agent-engineering/40-multi-session-handoff/)
- **Related terms:** Agent State, Checkpoint, Scope Contract, Progressive Disclosure

### HNSW
- **Category:** Retrieval & generation
- **Aliases:** Hierarchical Navigable Small World
- **What it actually means:** An approximate-nearest-neighbor index that organizes vectors in layered proximity graphs and searches from coarse upper layers toward detailed lower layers.
- **Why it matters:** It is a common way to make high-recall vector search practical at scales where exhaustive comparison is too slow.
- **In practice:** Tune construction and query parameters against latency, memory, and Recall@K targets, then rebuild the index when embedding versions change.
- **Common confusion:** HNSW is an index algorithm, not a similarity metric, embedding model, or complete vector database.
- **Related terms:** Approximate Nearest Neighbor (ANN), Vector Database, Embedding, Recall@K
- **Sources:** [Efficient and Robust Approximate Nearest Neighbor Search Using HNSW](https://dl.acm.org/doi/10.1109/TPAMI.2018.2889473)

### Human-in-the-Loop (HITL)
- **Category:** Agents & tools
- **Aliases:** Human oversight, human review
- **What it actually means:** A workflow design in which a person supplies judgment, correction, approval, or escalation at defined points in an AI-driven process.
- **Why it matters:** Human involvement is most useful at high-impact, ambiguous, or irreversible boundaries, not as an undefined fallback after every step.
- **In practice:** Let the agent classify routine requests automatically, but route uncertain or high-value cases to a reviewer with the evidence and proposed action.
- **Common confusion:** HITL does not automatically make a system safe. Reviewers need time, context, authority, and a clear decision standard.
- **Related terms:** Approval Gate, Verification Gate, Agent, Guardrails

### Hybrid Retrieval
- **Category:** Retrieval & generation
- **What it actually means:** Retrieval that combines signals from different methods, commonly lexical matching and dense-vector similarity, before merging or reranking results.
- **Why it matters:** Exact identifiers, rare terms, and semantic paraphrases behave differently, so one retrieval signal can miss useful evidence.
- **In practice:** Retrieve candidates with both BM25-style keyword search and embeddings, merge their ranks, then rerank the combined set for the user query.
- **Common confusion:** Hybrid retrieval combines candidate signals. A reranker applies a second relevance model to candidates already retrieved.
- **Learn it:** [Advanced RAG](../phases/11-llm-engineering/07-advanced-rag/)
- **Related terms:** Semantic Search, Reranker, RAG (Retrieval-Augmented Generation), Embedding

### Hyperparameter
- **Category:** Math & training
- **What people say:** A setting you tune.
- **What it actually means:** A configuration choice that shapes model structure, optimization, data processing, or inference rather than being learned as an ordinary model parameter. Examples include learning rate, batch size, layer count, and decoding settings.
- **Common confusion:** Some hyperparameters are selected before training, while others can be changed during a schedule or at inference time.
- **Related terms:** Parameter, Learning Rate, Batch Size, Temperature

## I

### Idempotency
- **Category:** AI-native development
- **What it actually means:** The property that repeating the same operation with the same identity does not create additional side effects beyond the first successful application.
- **Why it matters:** Retries are normal in distributed agent systems. Without idempotency, one uncertain response can duplicate payments, comments, deployments, or records.
- **In practice:** Attach an idempotency key to a tool request and persist the completed result so a retry returns that result instead of executing the write again.
- **Common confusion:** Idempotency does not mean every response is byte-for-byte identical. It means the intended state change is not duplicated.
- **Sources:** [HTTP Semantics: idempotent methods](https://www.rfc-editor.org/rfc/rfc9110.html#name-idempotent-methods)
- **Related terms:** Retry with Backoff, Durable Execution, Checkpoint

### Image Token
- **Category:** Multimodal systems
- **What it actually means:** A model-specific visual unit represented as a vector or discrete code, commonly derived from an image patch, region, or learned visual-codebook entry.
- **Why it matters:** Turning visual input into a sequence lets transformer-style components process images together with text or other tokenized modalities.
- **In practice:** Document whether tokens are continuous patches or discrete codes, preserve spatial position, test resolution and aspect-ratio changes, and count visual tokens in the model's input budget.
- **Common confusion:** An image token is not necessarily one pixel, one object, or one fixed physical area. Its scope follows the visual encoder or tokenizer.
- **Learn it:** [Vision-Language Models](../phases/04-computer-vision/25-vision-language-models/)
- **Related terms:** Patch Embedding, Token, VAE (Variational Autoencoder), Vision Transformer (ViT)
- **Sources:** [Vision Transformer](https://arxiv.org/abs/2010.11929); [VQ-VAE](https://arxiv.org/abs/1711.00937)

### In-Context Learning
- **Category:** Prompting & context
- **What it actually means:** A model adapting its behavior from instructions, examples, or patterns supplied in the current input without an ordinary parameter update.
- **Why it matters:** It explains how one pretrained model can perform a new task from context while keeping its weights unchanged.
- **In practice:** Place representative demonstrations before the target input, test order and formatting variants, and keep evaluation examples separate from the demonstrations.
- **Common confusion:** In-context learning is temporary conditioning, not fine-tuning, durable memory, or proof that the model inferred the intended rule.
- **Related terms:** Few-Shot, Zero-Shot, Context Window, Prompt Engineering
- **Sources:** [Language Models are Few-Shot Learners](https://arxiv.org/abs/2005.14165)

### Incident Response
- **Category:** Reliability & operations
- **What it actually means:** The coordinated process for detecting, analyzing, containing, recovering from, communicating, and learning from an event that threatens service, data, safety, or security.
- **Why it matters:** During an incident, clear roles and evidence matter more than improvised heroics, especially when model behavior and distributed dependencies obscure the failing boundary.
- **In practice:** Define severity and command roles, preserve traces and audit records, stop harmful actions, communicate impact, verify recovery, and track corrective work to completion.
- **Common confusion:** Incident response manages the event and its consequences. Root-cause analysis and long-term prevention continue after immediate service is restored.
- **Learn it:** [SRE for AI](../phases/17-infrastructure-and-production/23-sre-for-ai/)
- **Related terms:** Observability, Audit Log, Postmortem, Availability
- **Sources:** [Google SRE: Managing Incidents](https://sre.google/sre-book/managing-incidents/); [NIST SP 800-61 Rev. 3](https://csrc.nist.gov/pubs/sp/800/61/r3/final)

### Indirect Prompt Injection
- **Category:** Security & governance
- **What it actually means:** A prompt-injection attack delivered through content the system retrieves or observes, such as a webpage, document, email, image text, or tool result, rather than directly through the user's instruction.
- **Why it matters:** An agent can encounter attacker-controlled instructions while performing an authorized task and mistake that content for authority-bearing guidance.
- **In practice:** Label external content as untrusted data, separate it from instructions, minimize tool permissions, require approval for consequential actions, and include malicious retrieved content in regression tests.
- **Common confusion:** Indirect describes the delivery path, not a weaker attack. A hidden instruction in retrieved content can be as consequential as a direct user prompt.
- **Learn it:** [Indirect Prompt Injection](../phases/18-ethics-safety-alignment/15-indirect-prompt-injection/)
- **Related terms:** Prompt Injection, Instruction Hierarchy, Trust Boundary, Data Exfiltration
- **Sources:** [Compromising Real-World LLM-Integrated Applications with Indirect Prompt Injection](https://arxiv.org/abs/2302.12173)

### Inductive Bias
- **Category:** Models & inference
- **What people say:** Assumptions built into a learning system.
- **What it actually means:** Structural or statistical assumptions that favor some functions or representations over others. Convolution favors locality and shared filters; causal masking favors prediction from preceding positions.
- **Common confusion:** Transformers still have inductive biases through tokenization, position handling, masking, architecture, data, and objective.
- **Related terms:** CNN (Convolutional Neural Network), Transformer, Feature

### Inference
- **Category:** Models & inference
- **What people say:** Running a trained model.
- **What it actually means:** Executing a trained model to produce predictions, scores, embeddings, or generated tokens without performing an ordinary training update to its parameters.
- **Common confusion:** An application can update caches, conversation state, or external memory during inference even though model weights stay unchanged.
- **Related terms:** Autoregressive, Streaming, KV Cache

### Instruction Following
- **Category:** Prompting & context
- **What it actually means:** A model capability to map natural-language directions and supplied context to behavior that satisfies the stated task and constraints.
- **Why it matters:** Language generation can be fluent without obeying the user's requested operation, format, boundaries, or priorities.
- **In practice:** Evaluate instruction adherence separately from answer quality using conflicting constraints, format requirements, irrelevant context, and refusal cases.
- **Common confusion:** Instruction following is not factual correctness, alignment, or obedience to every string that looks like an instruction.
- **Related terms:** SFT (Supervised Fine-Tuning), Prompt Engineering, Instruction Hierarchy, Alignment
- **Sources:** [Finetuned Language Models Are Zero-Shot Learners](https://arxiv.org/abs/2109.01652)

### Instruction Hierarchy
- **Category:** Prompting & context
- **What it actually means:** A rule set for resolving conflicts among instructions from sources with different authority, such as application policy, users, and untrusted retrieved content.
- **Why it matters:** Agent systems mix trusted goals with external text, so the model and harness need a defined response when lower-authority content conflicts with higher-authority constraints.
- **In practice:** Label untrusted tool output as data, preserve higher-priority constraints outside that content, and test direct and indirect conflict cases.
- **Common confusion:** An instruction hierarchy can improve behavior but is not a security boundary; least privilege and approval controls still limit consequences.
- **Related terms:** System Prompt, Prompt Injection, Least Privilege, Tool Contract
- **Sources:** [The Instruction Hierarchy](https://arxiv.org/abs/2404.13208)

### Inter-Token Latency (ITL)
- **Category:** Infrastructure & serving
- **What it actually means:** The elapsed time between two consecutive output-token arrival events for one request, calculated as `t_i - t_(i-1)` for an output token after the first.
- **Why it matters:** Individual gaps expose decode stalls and streaming jitter that a per-request average can hide, especially under batching, preemption, or mixed workloads.
- **In practice:** Record each post-first-token interval with its request and token position, then report distributions by workload, output length, and concurrency without pooling away request boundaries.
- **Common confusion:** ITL is one interval between consecutive tokens. Time per output token is a per-request average across those intervals, while time to first token covers the wait before streaming begins.
- **Learn it:** [Inference Metrics and Goodput](../phases/17-infrastructure-and-production/08-inference-metrics-goodput/)
- **Related terms:** Time per Output Token (TPOT), Time to First Token (TTFT), Decode Phase, Tail Latency
- **Sources:** [DistServe](https://arxiv.org/abs/2401.09670)

## J

### Jailbreak
- **Category:** Security & governance
- **What it actually means:** An adversarial input or interaction strategy intended to make a model produce behavior that its training or application controls are designed to prevent.
- **Why it matters:** Successful jailbreaks expose gaps between stated policy and actual behavior, and they can become more consequential when the model controls tools or protected data.
- **In practice:** Derive test families from prohibited behaviors, vary format and interaction length, measure both refusal and harmful completion, and convert confirmed failures into versioned adversarial evals.
- **Common confusion:** A jailbreak targets model or system behavioral restrictions. Prompt injection redirects instruction following, often toward an attacker's goal; one interaction can involve both.
- **Learn it:** [Jailbreak Taxonomy](../phases/19-capstone-projects/82-jailbreak-taxonomy/)
- **Related terms:** Prompt Injection, Red Teaming, Guardrails, Eval Set
- **Sources:** [Universal and Transferable Adversarial Attacks on Aligned Language Models](https://arxiv.org/abs/2307.15043)

### JAX
- **Category:** Math & training
- **What people say:** A NumPy-like system for accelerated machine learning.
- **What it actually means:** A Python library for transforming numerical functions with automatic differentiation, compilation, vectorization, and parallel execution across accelerators. Its transformations work best with explicit state and functional-style code.
- **Common confusion:** JAX does not prohibit all stateful programming, but hidden mutation inside transformed functions can produce incorrect or unsupported behavior.
- **Learn it:** [Introduction to JAX](../phases/03-deep-learning-core/12-intro-to-jax/)
- **Sources:** [JAX documentation](https://docs.jax.dev/en/latest/)
- **Related terms:** Autograd, Tensor, CUDA

## K

### Knowledge Distillation
- **Category:** Math & training
- **What it actually means:** Training a student model to reproduce selected behavior or output distributions from a more capable teacher, often alongside ordinary target labels.
- **Why it matters:** It can transfer useful behavior into a smaller or cheaper model when serving the teacher directly is impractical.
- **In practice:** Define teacher outputs, temperature, student loss, and a held-out eval set, then compare the student with both the teacher and a label-only baseline.
- **Common confusion:** Distillation transfers behavior on the training distribution; it does not copy every capability, fact, or safety property of the teacher.
- **Related terms:** Fine-tuning, Loss Function, Logits, Quantization
- **Sources:** [Distilling the Knowledge in a Neural Network](https://arxiv.org/abs/1503.02531)

### KV Cache
- **Category:** Models & inference
- **What people say:** A cache that makes token generation faster.
- **What it actually means:** Stored key and value tensors from earlier positions in autoregressive generation. Reusing them avoids recomputing attention projections for the unchanged prefix at every decoding step.
- **Why it matters:** It reduces repeated computation but consumes memory that grows with sequence length, layers, batch, and model configuration.
- **Common confusion:** A KV cache is runtime attention state for a sequence. Prefix caching reuses eligible KV state across requests, while prompt caching is a broader provider or application reuse contract.
- **Learn it:** [KV Cache and Flash Attention](../phases/07-transformers-deep-dive/12-kv-cache-flash-attention/)
- **Related terms:** Attention, Autoregressive, Prefix Caching, Prompt Cache

## L

### Late Fusion
- **Category:** Multimodal systems
- **What it actually means:** Processing modalities through separate encoders or predictors and combining their high-level representations, scores, or decisions near the task output.
- **Why it matters:** Separate branches can use modality-specific architectures and tolerate missing inputs, though they may miss fine-grained interactions available to earlier fusion.
- **In practice:** Calibrate each branch, define how missing modalities affect the merge, compare score-level and feature-level combinations, and evaluate each branch alone as an ablation.
- **Common confusion:** Late fusion describes the position of combination. It does not mean simple averaging or guarantee that the modalities contribute equally.
- **Learn it:** [Cross-Attention Fusion](../phases/19-capstone-projects/61-cross-attention-fusion/)
- **Related terms:** Early Fusion, Multimodal Fusion, Modality, Evaluation (Eval)
- **Sources:** [Multimodal Deep Learning](https://ai.stanford.edu/~ang/papers/icml11-MultimodalDeepLearning.pdf); [Multimodal Machine Learning: A Survey and Taxonomy](https://arxiv.org/abs/1705.09406)

### Latent Space
- **Category:** Data & representations
- **What people say:** A model's hidden representation space.
- **What it actually means:** A learned representation space whose coordinates encode factors useful to a model. It may be lower-dimensional than the input, but compression is not required for every latent representation.
- **Common confusion:** Nearby points are only meaningfully similar according to what the model and training objective learned.
- **Related terms:** Embedding, VAE (Variational Autoencoder), Feature

### Learning Rate
- **Category:** Math & training
- **What people say:** How large each optimization step is.
- **What it actually means:** A scale factor used by an optimizer to control parameter-update magnitude. Values that are too large can destabilize training; values that are too small can make useful progress impractically slow.
- **Common confusion:** The effective update also depends on the optimizer, schedule, gradient scale, batch, and parameter history.
- **Related terms:** Optimizer, Gradient Descent, Batch Size

### Learning Rate Schedule
- **Category:** Math & training
- **What it actually means:** A policy that changes the optimizer's learning rate as training progresses according to steps, epochs, metrics, or a predefined curve.
- **Why it matters:** Different training stages can benefit from different update scales, so one constant rate may be unstable early or wasteful late.
- **In practice:** Version the schedule with the optimizer configuration, log the actual rate at every step, and compare schedules under the same token or update budget.
- **Common confusion:** A scheduler controls the learning rate over time; it does not decide when an optimizer step occurs or guarantee convergence.
- **Related terms:** Learning Rate, Warmup, Optimizer, Epoch
- **Sources:** [SGDR](https://arxiv.org/abs/1608.03983); [Attention Is All You Need](https://arxiv.org/abs/1706.03762)

### Least Privilege
- **Category:** Evaluation & safety
- **What it actually means:** Giving a model, agent, tool, or user only the permissions required for the current task, for only as long as those permissions are needed.
- **Why it matters:** Models can make mistakes or follow malicious instructions. Narrow permissions reduce the damage any one failure can cause.
- **In practice:** Give a documentation agent read access to source files and write access to one branch, but no production credentials or merge permission.
- **Common confusion:** Authentication proves identity. Least privilege limits what that identity can do.
- **Related terms:** Sandbox, Approval Gate, Prompt Injection, Tool Contract

### LLM (Large Language Model)
- **Category:** Models & inference
- **What people say:** The brain of an AI application.
- **What it actually means:** A language model with enough capacity and broad training to perform many language tasks through prompting or adaptation. Most current LLMs use transformer architectures and sequence-prediction objectives, but size thresholds, data sources, and training recipes vary.
- **Common confusion:** An LLM is a model component. Tools, retrieval, state, policies, and product logic live in the surrounding system.
- **Related terms:** Transformer, Autoregressive, Agent Harness

### LLM-as-a-Judge
- **Category:** Evaluation & safety
- **What it actually means:** Using a language model to score, compare, classify, or critique another system's output against a rubric.
- **Why it matters:** It can scale evaluation of qualities that are difficult to express as exact-match tests, such as clarity or instruction adherence.
- **In practice:** Give a separate evaluator model the task, candidate answer, reference evidence, and a structured rubric, then calibrate its scores against human-reviewed examples.
- **Common confusion:** A judge model is not ground truth. It can be biased by order, verbosity, style, prompt wording, or shared model failures.
- **Learn it:** [Eval-Driven Agent Development](../phases/14-agent-engineering/30-eval-driven-agent-development/)
- **Related terms:** Evaluation (Eval), Eval Set, Verification Gate, Precision & Recall

### Load Shedding
- **Category:** Reliability & operations
- **What it actually means:** Deliberately rejecting, dropping, or cancelling selected work at one or more overload boundaries when demand exceeds the capacity available to produce useful results.
- **Why it matters:** Continuing to accept every request during overload can increase queueing until nearly all requests miss their deadlines and recovery becomes harder.
- **In practice:** Shed at the earliest informed boundary, preserve high-priority and already-admitted work when possible, identify the overloaded scope, and mark a response retryable only when the condition is transient and the request remains within its retry budget.
- **Common confusion:** Load shedding is not confined to work that has already been accepted. Admission control is specifically the pre-acceptance gate, while rate limiting can enforce a usage policy even when capacity remains.
- **Related terms:** Admission Control, Backpressure, Rate Limit, Graceful Degradation
- **Sources:** [Google SRE: Handling Overload](https://sre.google/sre-book/handling-overload/)

### Logits
- **Category:** Models & inference
- **What it actually means:** The model's unnormalized numeric scores for candidate outcomes before a normalization function or decoding rule converts them into selections.
- **Why it matters:** Temperature, softmax, top-k, and top-p operate on or derive from logits, so logits connect model computation to generated tokens.
- **In practice:** Inspect logits or log probabilities when the API exposes them, apply masks before sampling, and avoid interpreting raw magnitude as calibrated confidence.
- **Common confusion:** Logits are not probabilities and are not comparable across unrelated positions, models, or tasks without a defined transformation.
- **Related terms:** Softmax, Temperature, Token, Cross-Entropy
- **Sources:** [Attention Is All You Need](https://arxiv.org/abs/1706.03762)

### LoRA (Low-Rank Adaptation)
- **Category:** Math & training
- **What people say:** Parameter-efficient fine-tuning.
- **What it actually means:** A method that keeps base weights frozen and learns low-rank update matrices for selected layers. It reduces the number of trainable parameters and can lower training memory relative to full-parameter fine-tuning.
- **Common confusion:** Actual memory and speed savings depend on rank, target modules, optimizer state, activation memory, quantization, and implementation.
- **Learn it:** [Fine-Tuning and LoRA](../phases/11-llm-engineering/08-fine-tuning-lora/)
- **Sources:** [LoRA paper](https://arxiv.org/abs/2106.09685)
- **Related terms:** Fine-tuning, QLoRA, Parameter

### Loss Function
- **Category:** Math & training
- **What people say:** A number that measures training error.
- **What it actually means:** An objective that maps predictions and targets, sometimes with regularization terms, to a value optimization tries to reduce. The loss determines which errors training directly rewards or penalizes.
- **Common confusion:** A low training loss does not guarantee useful, safe, or generalizable behavior on production tasks.
- **Related terms:** Cross-Entropy, Gradient, Evaluation (Eval)

### Lost in the Middle
- **Category:** Prompting & context
- **What it actually means:** A long-context failure pattern in which model performance changes with evidence position and can degrade when relevant information sits between the beginning and end.
- **Why it matters:** Fitting evidence inside the context window does not guarantee that the model will use every position with equal reliability.
- **In practice:** Test several evidence positions, reduce distractors, place decision-critical constraints where they remain salient, and verify answers against the source.
- **Common confusion:** It is an observed behavior pattern, not a fixed law that affects every model, task, or position identically.
- **Related terms:** Context Window, Context Engineering, Eval Set, Grounding
- **Sources:** [Lost in the Middle](https://aclanthology.org/2024.tacl-1.9/)

