# Technical blog content patterns

Use this reference when outlining a substantial theory-first blog or revising a draft whose mathematics and evidence are difficult to follow.

## Contents

1. Reader contract
2. Four-layer explanation
3. Symbol-table pattern
4. Derivation pattern
5. Evidence and applicability
6. Transferability
7. Editorial review

## 1. Reader contract

Open with four answers:

- What problem does the work address?
- What is the output readers can use?
- What evidence supports it?
- What does it not establish?

Use a strong status sentence such as “The estimator is a standard conditional-density method adapted to this domain; the novelty is the application and calibration design.” Avoid novelty by implication.

## 2. Four-layer explanation

Separate these layers whenever they coexist:

1. **Representation:** raw object to learned or engineered features.
2. **Predictive/statistical:** features to a point estimate or conditional distribution.
3. **Semantic:** a numerical variable to human-readable classes or decisions.
4. **Decision:** probabilities plus cost, preference, or expert review to an action.

A system can be validated at one layer and unvalidated at another. High predictive accuracy does not validate semantic labels; stable clusters do not validate a decision policy.

## 3. Symbol-table pattern

Place a glossary before readers have accumulated more than five unfamiliar symbols.

| Symbol | Type / shape / unit | Definition | Layer |
|---|---|---|---|
| \(x\) | scalar, min | model-predicted retention time | predictive input |
| \(y\) | scalar, min | experimental retention time | observed target |
| \(k\) | integer index | local mixture expert | error model |
| \(p(y\mid x)\) | density | calibrated outcome distribution | inference |

Also define a symbol in prose at first appearance. The table supports scanning; it does not excuse unexplained notation in the narrative.

## 4. Derivation pattern

For each mathematical block, use this order:

1. State the modeling assumption.
2. Define observed and latent variables.
3. Write the objective or joint distribution.
4. Show the non-obvious algebraic bridge.
5. Present the final estimator or update.
6. Translate it into one operational sentence.
7. State the failure condition.

For EM, show the complete-data log likelihood, posterior responsibilities, expected objective, constrained weight update, and weighted sufficient statistics. For conditional Gaussians, partition the covariance and derive the conditional mean and Schur-complement variance. For numerical integration, state the change of variables and quadrature nodes/weights.

## 5. Evidence and applicability

### Posterior is not support

A normalized posterior can be near one where every component density is almost zero. Whenever this can happen:

- show marginal density or a support score;
- define the support threshold from training data rather than visual taste;
- fade, mask, or mark unsupported regions;
- include an abstain/unknown recommendation for deployment.

### Components are not mechanisms

Describe a fitted component first as a density region or local expert. A mechanistic interpretation requires independent evidence. Report weight, center, covariance/scale, activation region, local bias/slope, and residual spread when available.

### Evaluation labels

Identify whether the target is an experimental gold label, expert label, pseudo-label, soft cluster membership, or model-generated weak label. Never report agreement with a weak label as proof of real-world decision quality.

## 6. Transferability

Analyze transfer as a composition of mappings. Ask, for every mapping:

- Which variables change with domain or protocol?
- Is absolute scale preserved, only rank preserved, or neither?
- Does local neighborhood structure remain meaningful?
- What small calibration set would identify the new coordinate system?
- Does a more expressive model add information or merely fit the same weak target better?

When invoking manifold learning, optimal transport, flow matching, foundation models, or another abstract framework, connect it to one specific replaceable layer. State its data requirement and the supervision gap it cannot repair.

## 7. Editorial review

Read the article in three passes:

1. **Cold-reader pass:** Can a technical reader explain every symbol and arrow without opening the code?
2. **Adversarial pass:** Where can a mathematically valid number be scientifically meaningless?
3. **Reproduction pass:** Can a maintainer locate the data, command, model, figure, and metric behind each main claim?

Remove sections that merely display sophistication. Keep abstractions only when they change interpretation, transfer strategy, or the next experiment.
