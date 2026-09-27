## S

### Sandbox
- **Category:** Agents & tools
- **What it actually means:** An isolated execution environment that restricts an agent's access to files, processes, network destinations, credentials, and host resources.
- **Why it matters:** Generated code and tool calls can be wrong or malicious. Isolation limits their reach and makes disposable verification practical.
- **In practice:** Run tests in an ephemeral container with a read-only base, a scoped writable workspace, no production secrets, and an explicit network allowlist.
- **Common confusion:** A sandbox reduces impact. It does not establish that the code inside is correct or harmless.
- **Learn it:** [Production Agent Runtimes](../phases/14-agent-engineering/29-production-runtimes/)
- **Related terms:** Least Privilege, Approval Gate, Coding Agent, Guardrails

### Saturation
- **Category:** Reliability & operations
- **What it actually means:** The degree to which a constrained resource or service has exhausted its capacity, including queued work that cannot begin promptly.
- **Why it matters:** Utilization alone can appear acceptable while memory, accelerator slots, queue depth, or a downstream quota is already limiting useful throughput.
- **In practice:** Identify each critical resource, measure active and waiting work, relate saturation to tail latency and errors, and alert before the queue enters an unstable growth regime.
- **Common confusion:** Saturation is not one universal percentage. The limiting resource and its queueing behavior depend on the workload and architecture.
- **Related terms:** Observability, Autoscaling, Backpressure, Tail Latency
- **Sources:** [Google SRE: Monitoring Distributed Systems](https://sre.google/sre-book/monitoring-distributed-systems/)

### Scope Contract
- **Category:** AI-native development
- **What it actually means:** A concrete agreement that defines a task's goal, allowed and forbidden surfaces, expected artifacts, verification requirements, and stopping conditions.
- **Why it matters:** It prevents an agent from turning a narrow fix into an unreviewable refactor or from claiming completion without evidence.
- **In practice:** State that only the parser module and its tests may change, public APIs must remain compatible, and the named test suite must pass.
- **Common confusion:** A task description says what you want. A scope contract also defines boundaries and proof.
- **Learn it:** [Scope Contracts](../phases/14-agent-engineering/36-scope-contracts/)
- **Related terms:** Coding Agent, Patch, Verification Gate, Handoff

### Self-Attention
- **Category:** Models & inference
- **What people say:** Tokens deciding which other tokens matter.
- **What it actually means:** Attention in which queries, keys, and values are derived from the same sequence representation. Scaled similarity scores are normalized and used to combine values, subject to causal, padding, local, or other masks.
- **Why it matters:** It builds context-sensitive token representations, but the permitted attention pattern depends on the architecture.
- **Common confusion:** Not every token can always attend to every other token. Causal and sparse models intentionally restrict connections.
- **Learn it:** [Self-Attention from Scratch](../phases/07-transformers-deep-dive/02-self-attention-from-scratch/)
- **Related terms:** Attention, Transformer, Context Window

### Semantic Cache
- **Category:** AI-native development
- **What it actually means:** A cache that reuses a previous result when a new request is judged sufficiently similar under a chosen representation and threshold.
- **Why it matters:** It can reduce latency and cost for repeated intents, but an incorrect match can return stale or user-inappropriate output.
- **In practice:** Cache low-risk FAQ answers by normalized intent, include tenant and policy version in the key, and bypass the cache for personalized or time-sensitive requests.
- **Common confusion:** Semantic similarity does not guarantee that two requests have the same correct answer. A semantic cache reuses a prior result, while prefix caching reuses exact-token KV state and prompt caching follows provider or application eligibility rules.
- **Related terms:** Prompt Cache, Embedding, Cost per Successful Task, Grounding

### Semantic Search
- **Category:** Retrieval & generation
- **What people say:** Search by meaning instead of exact words.
- **What it actually means:** Retrieval that represents a query and candidates in an embedding space and ranks candidates using a vector-similarity function.
- **Why it matters:** It can retrieve paraphrases and conceptually related text, but exact identifiers and rare strings may still need lexical search.
- **Related terms:** Embedding, Hybrid Retrieval, Vector Database, Reranker

### Separation of Duties
- **Category:** Security & governance
- **What it actually means:** Dividing conflicting responsibilities or authority across independent roles so one principal cannot complete a high-risk action without another authorized decision.
- **Why it matters:** A compromised account or mistaken agent should not be able to propose, approve, execute, and conceal the same consequential change.
- **In practice:** Separate artifact creation from release approval, use distinct identities, preserve both decisions in the audit log, and define emergency access with later review.
- **Common confusion:** Separation of duties is about conflicting authority, not simply assigning work to several people or agents that share the same credentials.
- **Related terms:** Approval Gate, Reviewer Agent, Audit Log, Least Privilege
- **Sources:** [NIST SP 800-53 Rev. 5](https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final)

### Service Level Indicator (SLI)
- **Category:** Reliability & operations
- **What it actually means:** A quantitative measure of service behavior at a defined user-relevant boundary, such as successful request ratio or latency below a threshold.
- **Why it matters:** Reliability discussions become actionable only when the observed behavior, eligible events, and measurement point are explicit.
- **In practice:** Define numerator, denominator, exclusions, data source, and aggregation window, then validate that the indicator tracks an outcome users actually experience.
- **Common confusion:** An SLI is the measurement. An SLO is the target applied to that measurement over a defined period.
- **Related terms:** Service Level Objective (SLO), Availability, Tail Latency, Observability
- **Sources:** [Google SRE: Service Level Objectives](https://sre.google/sre-book/service-level-objectives/)

### Service Level Objective (SLO)
- **Category:** Reliability & operations
- **What it actually means:** A target range or threshold for a service-level indicator over a stated population and measurement window.
- **Why it matters:** It translates an expected user outcome into an operating boundary for monitoring, capacity, release risk, and incident decisions.
- **In practice:** Choose an indicator users care about, set the target from product needs rather than current performance, define the window and exclusions, and attach an error-budget policy.
- **Common confusion:** An SLO is an internal reliability objective. A contractual service-level agreement can include remedies and may use different definitions.
- **Learn it:** [Inference Metrics and Goodput](../phases/17-infrastructure-and-production/08-inference-metrics-goodput/)
- **Related terms:** Service Level Indicator (SLI), Error Budget, Availability, Goodput
- **Sources:** [Google SRE: Service Level Objectives](https://sre.google/sre-book/service-level-objectives/)

### SFT (Supervised Fine-Tuning)
- **Category:** Math & training
- **What people say:** Training on example inputs and desired outputs.
- **What it actually means:** Fine-tuning a pretrained model on paired inputs and desired responses so it learns the demonstrated behavior under the training distribution.
- **Common confusion:** SFT can adapt many behaviors beyond chat, and example quality determines what behavior is reinforced.
- **Related terms:** Fine-tuning, DPO (Direct Preference Optimization), RLHF (Reinforcement Learning from Human Feedback)

### Shadow Traffic
- **Category:** Reliability & operations
- **What it actually means:** A copy of live request traffic sent to a candidate system for observation while the candidate response remains outside the primary user response path. Because the copied request still executes, its side effects must be isolated.
- **Why it matters:** It exposes the candidate to real input shapes and load while limiting user impact, which can reveal failures absent from synthetic tests.
- **In practice:** Remove or tokenize sensitive fields, route tools and dependencies to sandboxed or no-op targets, block writes at capability boundaries, preserve request correlation, and prevent shadow load from competing with user traffic.
- **Common confusion:** Keeping a candidate response off the primary path does not make execution side-effect-free. A canary release differs because it serves real users from the candidate for a controlled share of traffic.
- **Learn it:** [Shadow, Canary, and Progressive Delivery](../phases/17-infrastructure-and-production/20-shadow-canary-progressive/)
- **Related terms:** Canary Release, Evaluation (Eval), Trace, Model Serving
- **Sources:** [Istio Traffic Mirroring](https://istio.io/latest/docs/tasks/traffic-management/mirroring/)

### Shared Embedding Space
- **Category:** Multimodal systems
- **What it actually means:** A common vector space in which representations from different modalities can be compared with the same similarity function.
- **Why it matters:** It enables cross-modal retrieval and matching, such as finding images from text, without requiring both items to share a raw representation.
- **In practice:** Train paired and unpaired negatives deliberately, normalize vectors when the objective requires it, evaluate both retrieval directions, and inspect subgroup and language performance.
- **Common confusion:** Sharing a vector dimension does not create a shared semantic space. The training objective and data must establish cross-modal comparability.
- **Learn it:** [CLIP Contrastive Pretraining](../phases/12-multimodal-ai/02-clip-contrastive-pretraining/)
- **Related terms:** Embedding, Cosine Similarity, Modality Alignment, Semantic Search
- **Sources:** [Learning Transferable Visual Models From Natural Language Supervision](https://proceedings.mlr.press/v139/radford21a.html)

### Skill Bundle
- **Category:** Agents & tools
- **What it actually means:** The complete installable skill directory, including `SKILL.md` and every reference, script, asset, fixture, or companion file required by the workflow.
- **Why it matters:** Copying only the entry file can leave valid-looking instructions that point to missing resources or lose the deterministic code the workflow depends on.
- **In practice:** Install the tree as one unit, record hashes and source revision, validate the installed copy, and show collisions before replacing an existing bundle.
- **Common confusion:** `SKILL.md` is the entry point, not necessarily the entire artifact.
- **Learn it:** [Skill Evals, Packaging, and Portability](../phases/13-tools-and-protocols/27-skill-evals-packaging-and-portability/)
- **Related terms:** Agent Skill, Skill Catalog, Reproducible Build, Provenance Attestation
- **Sources:** [Agent Skills specification](https://agentskills.io/specification)

### Skill Catalog
- **Category:** Agents & tools
- **What it actually means:** The compact model-visible inventory of eligible skills, usually containing routing metadata such as name, description, and an internal source identifier rather than every skill body.
- **Why it matters:** A catalog lets an agent discover relevant procedures without loading every installed package into the working context.
- **In practice:** Validate packages first, apply an explicit duplicate-name policy, measure the serialized catalog budget, and retain diagnostics for entries that were shortened, omitted, or shadowed.
- **Common confusion:** A catalog entry means the skill is discoverable. It does not mean the body is active or its tools are authorized.
- **Learn it:** [Skill Discovery and Progressive Disclosure](../phases/13-tools-and-protocols/24-skill-discovery-and-progressive-disclosure/)
- **Related terms:** Skill Discovery, Skill Invocation, Progressive Disclosure, Token Budget
- **Sources:** [Agent Skills specification](https://agentskills.io/specification)

### Skill Discovery
- **Category:** Agents & tools
- **What it actually means:** A runtime pipeline that searches configured roots, identifies candidate skill directories, validates their package contract, attaches scope and provenance, resolves collisions, and publishes eligible catalog entries.
- **Why it matters:** Deterministic discovery makes missing, malformed, shadowed, and unsafe packages diagnosable before model routing begins.
- **In practice:** Declare search scopes and duplicate behavior, decide how symlinks are handled, reject resource escapes, and log why each candidate was accepted or rejected.
- **Common confusion:** Skill discovery is not an unrestricted recursive search for filenames called `SKILL.md`; installation locations and precedence are runtime policy.
- **Learn it:** [Skill Discovery and Progressive Disclosure](../phases/13-tools-and-protocols/24-skill-discovery-and-progressive-disclosure/)
- **Related terms:** Skill Catalog, Skill Bundle, Progressive Disclosure, Trust Boundary
- **Sources:** [Agent Skills client implementation guide](https://agentskills.io/client-implementation/adding-skills-support)

### Skill Invocation
- **Category:** Agents & tools
- **What it actually means:** The runtime-mediated process in which an eligible human, model, application, or other skill selects a skill and causes its instructions to enter the working context.
- **Why it matters:** Explicit user access, implicit model routing, activation, argument binding, tool permission, and execution are separate decisions with different failure modes.
- **In practice:** Define actor policy, evaluate descriptions with positive and near-miss requests, record the selected package identity, and keep host-specific invocation fields in tested adapters.
- **Common confusion:** Invocation activates instructions. It does not automatically execute a command or bypass approval and sandbox policy.
- **Learn it:** [Skill Invocation and Routing](../phases/13-tools-and-protocols/25-skill-invocation-and-routing/)
- **Related terms:** Agent Skill, Skill Catalog, Approval Gate, Sandbox
- **Sources:** [Evaluating Agent Skills](https://agentskills.io/skill-creation/evaluating-skills)

### Softmax
- **Category:** Math & training
- **What people say:** A function that turns logits into normalized positive values.
- **What it actually means:** A function defined by `softmax(x_i) = exp(x_i) / sum(exp(x_j))`, implemented with numerical stabilization. Its outputs are positive and sum to one, so they can parameterize a categorical distribution.
- **Common confusion:** Softmax values are not automatically calibrated probabilities about real-world correctness.
- **Related terms:** Temperature, Cross-Entropy, Attention

### Software Bill of Materials (SBOM)
- **Category:** Security & governance
- **Aliases:** SBOM
- **What it actually means:** A structured inventory of software components and relationships associated with a product or artifact, often including versions, suppliers, licenses, and identifiers.
- **Why it matters:** You need a component inventory to assess affected dependencies, license obligations, and supply-chain exposure when software changes or vulnerabilities emerge.
- **In practice:** Generate the SBOM during the trusted build, bind it to the release artifact, verify it in policy checks, and update it whenever dependencies or packaging change.
- **Common confusion:** An SBOM is an inventory, not proof that components are secure, correctly licensed, or actually present unless generation and provenance are trustworthy.
- **Related terms:** Provenance Attestation, Reproducible Build, Data Provenance, Audit Log
- **Sources:** [SPDX 3.0.1 specification](https://spdx.github.io/spdx-spec/v3.0/)

### Speculative Decoding
- **Category:** Models & inference
- **What it actually means:** An inference method in which a cheaper draft process proposes several tokens and the target model scores those draft positions in parallel. In exact sampling variants, an acceptance and correction rule preserves the target model's output distribution.
- **Why it matters:** It can reduce serial target-model decoding work when drafts are accepted, without requiring a change to the target model's trained weights.
- **In practice:** Measure acceptance rate and end-to-end latency on real prompts, include draft-model overhead, and verify that the implementation preserves the intended decoding distribution.
- **Common confusion:** Speculative decoding is not ordinary model routing or unverified autocomplete. Exact variants preserve the target distribution through acceptance and correction, while approximate variants may trade that guarantee for speed.
- **Related terms:** Autoregressive, KV Cache, Decoding Strategy, Tokens per Second (TPS)
- **Sources:** [Fast Inference from Transformers via Speculative Decoding](https://proceedings.mlr.press/v202/leviathan23a.html)

### Stateless MCP
- **Category:** Agents & tools
- **What it actually means:** The MCP 2026-07-28 request model in which every request carries the protocol version and client capabilities in `params._meta`, while results carry an explicit `resultType`; no protocol state is keyed by an initialization handshake, connection, or `Mcp-Session-Id`.
- **Why it matters:** Any worker can validate and process a request from its contents and authorization context, which avoids hidden connection affinity and makes horizontal routing easier to reason about.
- **In practice:** Implement `server/discover`, rebuild request metadata on every call, validate transport headers against the JSON-RPC body, and pass server-minted application handles as ordinary tool arguments when continuity is required.
- **Common confusion:** Stateless MCP removes protocol sessions, not application state, transport connections, streaming responses, tasks, or explicit handles.
- **Learn it:** [MCP Fundamentals](../phases/13-tools-and-protocols/06-mcp-fundamentals/)
- **Related terms:** MCP (Model Context Protocol), Multi Round-Trip Request (MRTR), Tool Contract, Idempotency
- **Sources:** [MCP 2026-07-28 key changes](https://modelcontextprotocol.io/specification/2026-07-28/changelog); [MCP Streamable HTTP](https://modelcontextprotocol.io/specification/2026-07-28/basic/transports/streamable-http)

### Stochastic Gradient Descent (SGD)
- **Category:** Math & training
- **Aliases:** SGD
- **What it actually means:** An optimizer family that updates parameters from a gradient estimated on a sampled example or minibatch rather than the complete training dataset.
- **Why it matters:** It is the baseline for understanding gradient noise, momentum, batch scaling, and the adaptive optimizers used in modern training.
- **In practice:** Record batch sampling, learning rate, momentum if used, and schedule, then compare validation behavior under equal update or token budgets.
- **Common confusion:** In current practice, SGD usually means minibatch SGD, and its useful learning rate does not follow one universal batch-scaling rule.
- **Related terms:** Gradient Descent, Batch Size, Learning Rate, Optimizer
- **Sources:** [Optimization Methods for Large-Scale Machine Learning](https://arxiv.org/abs/1606.04838); [Accurate, Large Minibatch SGD](https://arxiv.org/abs/1706.02677)

### Stop Sequence
- **Category:** Models & inference
- **What it actually means:** An application-specified token or text pattern that causes generation to stop when the decoding system encounters it.
- **Why it matters:** Stop sequences bound output protocols and multi-part generation without waiting for the model to decide semantically that it is finished.
- **In practice:** Choose unambiguous delimiters, test tokenization and partial streaming matches, and still enforce output length and schema validation.
- **Common confusion:** A stop sequence is a mechanical decoding condition, not proof that the answer is complete or that an agent goal is satisfied.
- **Related terms:** Decoding Strategy, Structured Output, Token, Termination Condition
- **Sources:** [Transformers text-generation documentation](https://huggingface.co/docs/transformers/main/en/main_classes/text_generation)

### Streaming
- **Category:** Models & inference
- **What people say:** Showing output as it is generated.
- **What it actually means:** Delivering incremental response events before the complete result is ready. A stream may contain token text, structured deltas, tool-call arguments, usage metadata, or status events depending on the API.
- **Why it matters:** It improves perceived responsiveness, but it does not reduce the model's actual time to produce a complete answer.
- **Common confusion:** Network transport, event shape, and chunk boundaries are provider-specific and are not guaranteed to align with words or tokens.
- **Learn it:** [Production LLM Application](../phases/11-llm-engineering/13-production-app/)
- **Related terms:** Time to First Token (TTFT), Autoregressive, Observability

### Structured Output
- **Category:** Agents & tools
- **What it actually means:** Model output constrained or validated against a machine-readable schema so application code can consume fields without parsing free-form prose.
- **Why it matters:** It reduces format ambiguity at the model-to-software boundary and enables field-level validation and retries.
- **In practice:** Require an incident triage result with an allowed severity enum, evidence array, and nullable escalation reason, then reject any response that fails the schema.
- **Common confusion:** Schema-valid output can still contain incorrect values. Structure is not factual verification.
- **Learn it:** [Structured Outputs](../phases/11-llm-engineering/03-structured-outputs/)
- **Related terms:** Function Calling, Tool Contract, Verification Gate

### Swarm
- **Category:** Agents & tools
- **What people say:** Many agents collaborating without one fixed controller.
- **What it actually means:** A loosely coordinated multi-agent pattern in which local agent decisions and message exchange produce system-level behavior. The term is used inconsistently, so the actual topology, state ownership, and termination rules must be specified.
- **Common confusion:** Multiple named agents do not guarantee useful specialization or emergent coordination.
- **Related terms:** Agent, Reviewer Agent, Handoff, Agent State

### System Prompt
- **Category:** Prompting & context
- **What people say:** Developer-controlled instructions for a model interaction.
- **What it actually means:** A provider-defined instruction message or configuration supplied by the application to establish behavior and constraints within that provider's instruction hierarchy.
- **Why it matters:** System instructions can guide behavior, but they are not guaranteed to remain secret and should not be treated as a security boundary.
- **Common confusion:** Priority rules, message roles, persistence, and visibility differ across APIs. Check the current provider contract.
- **Learn it:** [Instructions as Executable Constraints](../phases/14-agent-engineering/33-instructions-as-executable-constraints/)
- **Related terms:** Prompt Engineering, Prompt Injection, Context Engineering, Guardrails

## T

### Tail Latency
- **Category:** Reliability & operations
- **What it actually means:** The latency experienced by the slowest portion of requests, commonly summarized with a high percentile under a stated workload and time window.
- **Why it matters:** Averages can look healthy while a meaningful group of users waits much longer because of queueing, contention, retries, or variable request cost.
- **In practice:** Report several percentiles by route and workload, retain timeouts as censored or failed observations according to a documented rule, and trace slow requests across dependencies.
- **Common confusion:** Tail latency is not the single slowest request and has no meaning without the percentile, population, and measurement boundary.
- **Learn it:** [Inference Metrics and Goodput](../phases/17-infrastructure-and-production/08-inference-metrics-goodput/)
- **Related terms:** Time to First Token (TTFT), Time per Output Token (TPOT), Saturation, Goodput
- **Sources:** [The Tail at Scale](https://research.google/pubs/the-tail-at-scale/)

### Temperature
- **Category:** Models & inference
- **What people say:** A creativity setting.
- **What it actually means:** A decoding parameter that rescales logits before a probability distribution is formed. Higher positive values usually flatten the distribution; lower positive values sharpen it.
- **Why it matters:** Temperature changes sampling behavior, not the model's knowledge or factuality.
- **Common confusion:** A zero setting is often implemented as greedy decoding, but exact behavior and determinism depend on the provider, sampler, seed support, and serving system.
- **Related terms:** Softmax, Autoregressive, Token

### Tensor
- **Category:** Data & representations
- **What people say:** A multidimensional array used for numerical computation.
- **What it actually means:** A typed array with a shape, data type, and device placement that frameworks use to represent inputs, parameters, activations, and gradients. Automatic-differentiation metadata is framework- and operation-dependent, not an inherent property of every tensor.
- **Related terms:** Autograd, Parameter, Mixed Precision

### Tensor Parallelism
- **Category:** Infrastructure & serving
- **What it actually means:** Partitioning tensor operations within a model layer across devices, with collective communication combining partial results during the layer computation.
- **Why it matters:** It lets one layer use memory and compute from several devices, but frequent communication can dominate when the interconnect or partition is unsuitable.
- **In practice:** Match partition dimensions to model shapes, benchmark collective traffic, keep ranks on a fast interconnect, and record the sharding layout with checkpoints and serving configuration.
- **Common confusion:** Tensor parallelism splits work inside layers. Pipeline parallelism places different layer groups on different devices.
- **Learn it:** [Scaling and Distributed Training](../phases/10-llms-from-scratch/05-scaling-distributed/)
- **Related terms:** Tensor, Pipeline Parallelism, Expert Parallelism, Parameter
- **Sources:** [Megatron-LM](https://arxiv.org/abs/1909.08053)

### Termination Condition
- **Category:** Agents & tools
- **What it actually means:** An explicit rule that ends or pauses an agent run when it succeeds, fails, exhausts a budget, reaches a safe boundary, or requires escalation.
- **Why it matters:** Without a termination condition, an agent can loop, repeat side effects, waste budget, or claim completion without satisfying the goal.
- **In practice:** Define success evidence, maximum steps and cost, non-retryable errors, and escalation states before starting the loop.
- **Common confusion:** A stop sequence ends text generation; a termination condition decides whether the task or workflow should stop.
- **Related terms:** Agent Harness, Token Budget, Verification Gate, Stop Sequence
- **Sources:** [AutoGen](https://arxiv.org/abs/2308.08155)

### Test Oracle
- **Category:** AI-native development
- **What it actually means:** The mechanism, specification, reference, invariant, or human judgment used to decide whether observed program behavior is correct.
- **Why it matters:** Generating test inputs is not enough; automated verification requires an independent basis for classifying each result.
- **In practice:** Prefer executable invariants, reference implementations, schemas, and deterministic expected outputs, then document where human judgment remains necessary.
- **Common confusion:** The model that wrote the code should not be treated as an independent oracle merely because you ask it whether its own output is correct.
- **Related terms:** Regression Test, Verification Gate, Eval Set, Human-in-the-Loop (HITL)
- **Sources:** [The Oracle Problem in Software Testing](https://www.computer.org/csdl/journal/ts/2015/05/06963470/13rRUx0geBw)

### Threat Model
- **Category:** Security & governance
- **What it actually means:** A documented account of protected assets, trust boundaries, potential adversaries, assumed capabilities, attack paths, impacts, and planned controls.
- **Why it matters:** Security controls cannot be judged without stating what they defend, against whom, and under which assumptions.
- **In practice:** Map data and authority across model, retrieval, tools, users, and external services, then turn credible abuse paths into red-team cases and mitigations.
- **Common confusion:** A threat model prioritizes plausible risks; it is not a checklist that proves the system secure or predicts every future attack.
- **Related terms:** Least Privilege, Prompt Injection, Sandbox, Red Teaming
- **Sources:** [NIST SP 800-154](https://csrc.nist.gov/pubs/sp/800/154/ipd); [NIST Generative AI Profile](https://nvlpubs.nist.gov/nistpubs/ai/nist.ai.600-1.pdf)

### Time per Output Token (TPOT)
- **Category:** Infrastructure & serving
- **What it actually means:** For one request with `N > 1` output tokens, the average post-first-token interval: `(t_N - t_1) / (N - 1)`. System distributions then aggregate those per-request averages.
- **Why it matters:** Users can receive the first token quickly while the rest of the answer streams slowly, so startup latency alone does not describe generation responsiveness.
- **In practice:** Compute TPOT separately for each request, report percentiles across requests by output length and concurrency, and avoid pooling all token intervals or comparing systems with different tokenizers and measurement boundaries.
- **Common confusion:** TPOT is a per-request average. An individual inter-token latency is one gap between consecutive tokens, while time to first token includes the wait before output starts.
- **Learn it:** [Inference Metrics and Goodput](../phases/17-infrastructure-and-production/08-inference-metrics-goodput/)
- **Related terms:** Decode Phase, Time to First Token (TTFT), Streaming, Goodput
- **Sources:** [DistServe](https://arxiv.org/abs/2401.09670)

### Time to First Token (TTFT)
- **Category:** Models & inference
- **Aliases:** TTFT
- **What it actually means:** The elapsed time from submitting a generation request until the client receives the first output token or content event under a defined measurement boundary.
- **Why it matters:** TTFT strongly affects perceived responsiveness and can reveal queueing, prompt processing, cache, or network delays.
- **In practice:** Record client-side TTFT by model, prompt length, region, and cache status, then separate it from total completion time.
- **Common confusion:** TTFT is not tokens per second. One measures startup latency; the other measures generation throughput after output begins.
- **Related terms:** Streaming, Prompt Cache, Observability, Token Budget

### Token
- **Category:** Data & representations
- **What people say:** A word-sized piece of model input or output.
- **What it actually means:** An integer identifier produced by a model-specific tokenizer from text, bytes, images, audio, or another input representation. A token can be a whole word, part of a word, punctuation, whitespace, a byte sequence, or a special control symbol.
- **Common confusion:** Character-to-token ratios vary by language, content, and tokenizer, so count with the target model's tokenizer or provider tools.
- **Learn it:** [Tokenizers](../phases/10-llms-from-scratch/01-tokenizers/)
- **Related terms:** Token Budget, Context Window, Autoregressive

### Token Budget
- **Category:** Prompting & context
- **What it actually means:** An explicit allocation of token capacity across instructions, evidence, history, tool results, reasoning or working space, and output.
- **Why it matters:** Every included token competes for context capacity, latency, and cost. Budgeting forces you to preserve high-value evidence first.
- **In practice:** Reserve output capacity, cap retrieved chunks, summarize old tool results into state, and stop or compact before the model limit is reached.
- **Common confusion:** A token budget is a planning constraint. It is not the same as the model's maximum context window.
- **Learn it:** [Context Engineering](../phases/11-llm-engineering/05-context-engineering/)
- **Related terms:** Context Window, Context Engineering, Progressive Disclosure, Cost per Successful Task

### Tokenization
- **Category:** Data & representations
- **What it actually means:** Converting an input representation into the ordered token identifiers a specific model or tokenizer accepts.
- **Why it matters:** Tokenization determines sequence length, vocabulary boundaries, cost accounting, truncation behavior, and how text or code is represented before embedding.
- **In practice:** Use the exact tokenizer for the target model, version it with artifacts, and test multilingual text, code, whitespace, and special tokens.
- **Common confusion:** Tokenization is not always word splitting, and two models can assign different token counts and IDs to the same input.
- **Related terms:** Token, Vocabulary, Byte Pair Encoding (BPE), Embedding
- **Sources:** [Neural Machine Translation of Rare Words with Subword Units](https://arxiv.org/abs/1508.07909)

### Tokens per Second (TPS)
- **Category:** Infrastructure & serving
- **Aliases:** TPS, output token throughput
- **What it actually means:** A throughput measure reporting how many output tokens a serving system produces per unit time under a stated scope and workload.
- **Why it matters:** It complements startup latency by showing how quickly generation proceeds after output begins and how serving behaves under load.
- **In practice:** State whether TPS is per request or aggregate, exclude or identify prefill, and report batch, concurrency, sequence lengths, hardware, and percentile latency.
- **Common confusion:** TPS is not directly comparable across different tokenizers, workloads, quality settings, or measurement boundaries.
- **Related terms:** Time to First Token (TTFT), Streaming, Prefill, Observability
- **Sources:** [Sarathi-Serve](https://www.usenix.org/system/files/osdi24-agrawal.pdf)

### Tool Contract
- **Category:** Agents & tools
- **What it actually means:** The complete agreement for a tool boundary: purpose, typed inputs, outputs, validation, permissions, side effects, errors, timeouts, idempotency, and evidence returned to the caller.
- **Why it matters:** A schema tells a model what fields exist; a contract tells the system when the tool is safe and how failures must be handled.
- **In practice:** Define a file-write tool with an allowed root, expected base revision, maximum size, dry-run mode, explicit conflict errors, and a returned patch hash.
- **Common confusion:** A JSON Schema is part of a tool contract, not the whole contract.
- **Learn it:** [Tool Use and Function Calling](../phases/14-agent-engineering/06-tool-use-and-function-calling/)
- **Related terms:** Function Calling, Structured Output, Least Privilege, Idempotency

### Top-k Sampling
- **Category:** Models & inference
- **What it actually means:** A decoding method that restricts the next-token distribution to the k highest-scoring candidates, renormalizes their probabilities, and samples from that set.
- **Why it matters:** It removes the long low-probability tail from sampling while keeping a fixed maximum candidate count.
- **In practice:** Evaluate k together with temperature, top-p, and stop settings, and record the complete sampler configuration with generated results.
- **Common confusion:** Top-k uses a fixed candidate count, while top-p uses a probability-mass threshold whose candidate count changes by step.
- **Related terms:** Nucleus Sampling (Top-p), Temperature, Decoding Strategy, Logits
- **Sources:** [The Curious Case of Neural Text Degeneration](https://arxiv.org/abs/1904.09751)

### Trace
- **Category:** AI-native development
- **What it actually means:** A correlated record of one request or task across model calls, retrieval, tools, state transitions, retries, approvals, and evaluations.
- **Why it matters:** It lets you reconstruct where time, cost, and failure entered a multi-step workflow.
- **In practice:** Propagate one trace identifier through the agent harness and attach redacted spans for each model and tool operation.
- **Common confusion:** A trace should record operational evidence, not expose hidden model reasoning, secrets, or unredacted sensitive content.
- **Learn it:** [OpenTelemetry GenAI Conventions](../phases/14-agent-engineering/23-otel-genai-conventions/)
- **Sources:** [OpenTelemetry traces](https://opentelemetry.io/docs/concepts/signals/traces/)
- **Related terms:** Observability, Agent State, Time to First Token (TTFT), Evaluation (Eval)

### Transfer Learning
- **Category:** Math & training
- **What people say:** Reusing a pretrained model for a new task.
- **What it actually means:** Starting from representations or parameters learned on one data distribution or objective and adapting them for another. The transferable components and update strategy depend on architecture and task.
- **Common confusion:** Transfer is not limited to later layers, and successful transfer is not guaranteed when source and target tasks differ sharply.
- **Related terms:** Fine-tuning, Feature, SFT (Supervised Fine-Tuning)

### Transformer
- **Category:** Models & inference
- **What people say:** The architecture behind many modern language models.
- **What it actually means:** A neural-network architecture built from attention, position information, feed-forward sublayers, residual connections, and normalization. Encoder, decoder, and encoder-decoder variants use different masks and information flows.
- **Why it matters:** Training can process many sequence positions in parallel, while autoregressive generation still produces outputs step by step.
- **Common confusion:** Self-attention does not imply unrestricted all-to-all attention in every transformer.
- **Learn it:** [Build a Full Transformer](../phases/07-transformers-deep-dive/05-full-transformer/)
- **Sources:** [Attention Is All You Need](https://arxiv.org/abs/1706.03762)
- **Related terms:** Attention, Self-Attention, Encoder, Decoder

### Trust Boundary
- **Category:** Security & governance
- **What it actually means:** An interface where data, instructions, identity, or authority crosses between components or principals that operate under different trust assumptions.
- **Why it matters:** A boundary crossing is where the system must authenticate actors, validate data, constrain permissions, and decide which claims can influence action.
- **In practice:** Draw boundaries around users, model context, retrieval sources, tools, networks, and data stores, then specify validation and authorization for every crossing.
- **Common confusion:** A network boundary is only one kind of trust boundary. Untrusted document text entering a privileged agent context also crosses one.
- **Learn it:** [Jailbreak Taxonomy](../phases/19-capstone-projects/82-jailbreak-taxonomy/)
- **Related terms:** Threat Model, Least Privilege, Sandbox, Indirect Prompt Injection
- **Sources:** [Microsoft Learn: Trust Boundary, the Trust Zone Change Element](https://learn.microsoft.com/en-us/training/modules/tm-create-a-threat-model-using-foundational-data-flow-diagram-elements/6-trust-boundary-the-trust-zone-change-element); [OWASP Threat Modeling](https://owasp.org/www-community/Threat_Modeling)

## U

### Underfitting
- **Category:** Math & training
- **What people say:** The model cannot fit the training task well enough.
- **What it actually means:** A model or training setup has insufficient effective capacity, optimization, features, or training signal to capture useful patterns in the training data.
- **In practice:** Diagnose data and optimization first, then consider training longer, changing features, reducing excessive regularization, or increasing suitable capacity.
- **Related terms:** Overfitting, Loss Function, Hyperparameter

## V

### VAE (Variational Autoencoder)
- **Category:** Models & inference
- **What people say:** A probabilistic generative autoencoder.
- **What it actually means:** A latent-variable model trained with a reconstruction objective and a regularization term that keeps an approximate posterior close to a chosen prior. The reparameterization estimator allows gradients through stochastic latent sampling.
- **Common confusion:** A VAE does not force every latent distribution to one fixed Gaussian; the exact prior and approximate posterior are modeling choices.
- **Sources:** [Auto-Encoding Variational Bayes](https://arxiv.org/abs/1312.6114)
- **Related terms:** Latent Space, Encoder, Decoder, Diffusion Model

### Vector Database
- **Category:** Retrieval & generation
- **What people say:** A database optimized for vector similarity search.
- **What it actually means:** A storage and indexing system that supports nearest-neighbor queries over vector representations, often with metadata filtering, persistence, and approximate indexes.
- **Common confusion:** A vector database stores and searches vectors. It does not create high-quality embeddings or guarantee relevant retrieval.
- **Related terms:** Embedding, Semantic Search, Hybrid Retrieval

### Verification Gate
- **Category:** Evaluation & safety
- **What it actually means:** A control point that blocks progress until defined evidence satisfies a correctness or quality criterion.
- **Why it matters:** It converts a model's claim of completion into an evidence-backed decision.
- **In practice:** Prevent a coding task from completing until the patch applies, scoped tests pass, forbidden files remain unchanged, and required artifacts exist.
- **Common confusion:** Verification checks whether evidence meets criteria. Approval grants authority to proceed, even when the evidence is already known.
- **Learn it:** [Verification Gates](../phases/14-agent-engineering/38-verification-gates/)
- **Related terms:** Approval Gate, Regression Test, Scope Contract, Structured Output

### Vision-Language Model (VLM)
- **Category:** Multimodal systems
- **What it actually means:** A model that learns relationships between, or jointly processes, visual and language representations for tasks such as retrieval, description, question answering, or grounded generation.
- **Why it matters:** VLM performance depends on the visual encoder, language component, connection mechanism, training data, and resolution policy rather than one generic capability label.
- **In practice:** Evaluate text-only and vision-only controls, vary image resolution and layout, require evidence localization where possible, and report failures by visual skill and language.
- **Common confusion:** Accepting an image does not prove the model uses it correctly, and a VLM is not necessarily able to generate images.
- **Learn it:** [Vision-Language Models](../phases/04-computer-vision/25-vision-language-models/)
- **Related terms:** Multimodal Model, Vision Transformer (ViT), Cross-Attention, Visual Grounding
- **Sources:** [CLIP](https://arxiv.org/abs/2103.00020); [Flamingo](https://arxiv.org/abs/2204.14198)

### Vision Transformer (ViT)
- **Category:** Multimodal systems
- **What it actually means:** A vision architecture that represents an image as a sequence of patch embeddings with position information and processes that sequence with transformer encoder blocks.
- **Why it matters:** It provides a sequence-model interface for visual data, but performance and compute depend on patch size, resolution, pretraining, and inductive biases.
- **In practice:** Keep patching and normalization consistent with training, account for position-embedding behavior at new resolutions, and compare against a suitable visual baseline on the target dataset.
- **Common confusion:** ViT is an architecture family, not every transformer that accepts images, and its patches are not inherently semantic objects.
- **Learn it:** [Vision Transformers](../phases/04-computer-vision/14-vision-transformers/)
- **Related terms:** Transformer, Patch Embedding, Self-Attention, Encoder
- **Sources:** [An Image is Worth 16x16 Words](https://arxiv.org/abs/2010.11929)

### Visual Grounding
- **Category:** Multimodal systems
- **What it actually means:** Connecting a language expression to spatial evidence in an image or video, such as a region, object, mask, or tracked entity.
- **Why it matters:** A fluent visual answer can be unsupported, while grounding makes the claimed referent inspectable and enables region-level evaluation.
- **In practice:** Require a box, mask, or temporal segment with the answer, test ambiguous and absent referents, and score localization separately from language correctness.
- **Common confusion:** Visual grounding identifies where the referenced evidence is. General image captioning can describe a scene without localizing each claim.
- **Learn it:** [Cross-Attention Fusion](../phases/19-capstone-projects/61-cross-attention-fusion/)
- **Related terms:** Grounding, Vision-Language Model (VLM), Attention, Evaluation (Eval)
- **Sources:** [MDETR](https://arxiv.org/abs/2104.12763)

### Vocabulary
- **Category:** Data & representations
- **What it actually means:** The finite mapping between token identifiers and the units a tokenizer can emit, including ordinary, byte-level, and special control tokens.
- **Why it matters:** Vocabulary design affects sequence length, multilingual coverage, code representation, embedding size, and compatibility between tokenizers and model weights.
- **In practice:** Version the vocabulary and special-token assignments with the model, test encode-decode round trips, and never substitute a tokenizer with merely similar token names.
- **Common confusion:** A model vocabulary is not a dictionary of human words; many entries are fragments, bytes, whitespace patterns, or control symbols.
- **Related terms:** Tokenization, Byte Pair Encoding (BPE), Token, Embedding
- **Sources:** [Neural Machine Translation of Rare Words with Subword Units](https://arxiv.org/abs/1508.07909)

## W

### Warmup
- **Category:** Math & training
- **What it actually means:** An initial training phase in which the learning rate rises from a smaller value toward the main schedule's target value.
- **Why it matters:** Early gradients and optimizer statistics can be unstable, especially in large-batch or transformer training, so abrupt full-size updates may damage optimization.
- **In practice:** Define warmup in steps or processed tokens, log the realized curve, and tune it with the batch, optimizer, and total training budget held visible.
- **Common confusion:** Warmup is not required for every model and does not make an otherwise unsuitable learning rate safe.
- **Related terms:** Learning Rate Schedule, Learning Rate, Batch Size, AdamW
- **Sources:** [Accurate, Large Minibatch SGD](https://arxiv.org/abs/1706.02677)

### Weight
- **Category:** Math & training
- **What people say:** A learned number inside a model.
- **What it actually means:** A trainable coefficient in a model transformation. Weights are usually organized into tensors, and optimization adjusts them to reduce the training objective.
- **Common confusion:** Not every parameter is called a weight; biases, embeddings, and normalization scales are parameters too.
- **Related terms:** Parameter, Tensor, Optimizer

### Weight Decay
- **Category:** Math & training
- **What people say:** Regularization that shrinks weights during optimization.
- **What it actually means:** An update rule that reduces selected parameter magnitudes over training, often by multiplying weights by a shrinkage factor separate from the gradient update.
- **Why it matters:** It can improve generalization, but the useful coefficient and excluded parameter groups depend on model, optimizer, schedule, and data.
- **Common confusion:** Decoupled weight decay is equivalent to an L2 loss penalty for some simple optimizers, but not generally for adaptive optimizers such as Adam.
- **Related terms:** AdamW, Overfitting, Optimizer

### Worktree
- **Category:** AI-native development
- **What it actually means:** In Git, a working directory attached to a repository and branch or commit, with shared object storage but its own checked-out files and index.
- **Why it matters:** Separate worktrees let people and agents work concurrently without constantly switching or overwriting one checkout.
- **In practice:** Give each coding agent a named feature branch and exact worktree path, then review and integrate patches through normal Git history.
- **Common confusion:** A worktree isolates checked-out files, not every process, port, cache, database, or secret on the machine.
- **Learn it:** [Workbench for Real Repositories](../phases/14-agent-engineering/41-workbench-for-real-repos/)
- **Sources:** [git-worktree documentation](https://git-scm.com/docs/git-worktree)
- **Related terms:** Coding Agent, Patch, Scope Contract, Handoff

## Z

### Zero-Shot
- **Category:** Prompting & context
- **What people say:** Asking for a task without examples in the current prompt.
- **What it actually means:** Performing a task from instructions or task framing without including task-specific demonstrations in the immediate input.
- **Common confusion:** Zero-shot does not mean the model had no relevant pretraining, instruction tuning, tools, or retrieved context.
- **Related terms:** Few-Shot, Prompt Engineering, Transfer Learning

### Zero Trust
- **Category:** Security & governance
- **What it actually means:** A security model that grants no implicit trust from network location or asset ownership and instead evaluates each access request against identity, device, resource, policy, and current context.
- **Why it matters:** AI tools and agents span local files, cloud services, models, and external content, so a trusted internal network is too broad a basis for authority.
- **In practice:** Authenticate every actor and workload, authorize each resource action, issue short-lived credentials, segment access, and continuously record and reevaluate policy-relevant signals.
- **Common confusion:** Zero trust does not mean trusting nothing or blocking all automation. It means making trust decisions explicit, scoped, and continuously verifiable.
- **Learn it:** [Security, Secrets, and Audit](../phases/17-infrastructure-and-production/25-security-secrets-audit/)
- **Related terms:** Least Privilege, Trust Boundary, Approval Gate, Audit Log
- **Sources:** [NIST SP 800-207](https://csrc.nist.gov/pubs/sp/800/207/final)
