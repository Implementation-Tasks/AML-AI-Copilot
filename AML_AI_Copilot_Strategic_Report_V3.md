# **TECHNICAL ANALYSIS & STARTUP STRATEGY REPORT**

## **Hybrid Quantum-Agentic AML Platform**

**Project:** AML AI Copilot (QCFinOp Team)  
**Context:** SEA Quantathon 2026  
**Role:** Startup Advisor & Technical Focus  
**Analyst:** Crypto AML & False Positive Mitigation

### **Answer 1: Founder-Market Fit / Founder-Problem Fit**

The team's greatest and most core advantage lies in exceptional execution speed (rapid prototyping) along with deep expertise in AI agentic workflows. As AI Solutions Architects and Agentic Developers, the team has the practical capacity to seamlessly bridge the gap between complex theoretical algorithmic models and real-world production environments.  
Thanks to the proficient application of advanced AI coding tools like Cursor, Windsurf, and Claude Code, the project's engineering and software development cycle is accelerated exponentially compared to traditional teams. While other teams struggle with data pipelines, AML AI Copilot can immediately establish a multi-task system to automatically analyze and explain data structures. This directly addresses the biggest "pain point" in the anti-money laundering (AML) industry today: the severe shortage of personnel capable of reading and processing thousands of alert reports daily.  
**Hardware-Agnostic & Multi-Ecosystem Capability:** Beyond software execution, the team possesses a strong "Hardware-Agnostic" mindset. Through the integration of the Quapp.cloud platform, our architecture comes pre-equipped to utilize major quantum SDKs (including Qiskit, AWS Braket, PennyLane, and D-Wave). Furthermore, the team is diversifying its approach by exploring Photonic Quantum Computing. We are prepared to utilize Quandela's Perceval open-source SDK to design and simulate photonic circuits (using single photons as qubits) as a strategic expansion path for deeper crypto network analysis algorithms.

### **Answer 2: Target Compliance & Risk Domain**

The AML AI Copilot project chooses to focus 100% on the Crypto AML & Scam Wallets niche in Southeast Asia (SEA) during the initial phase. This strategic orientation is based on key reasons:

* The Southeast Asian region is currently a global hotspot for cryptocurrency adoption rates, accompanied by an explosion of sophisticated high-tech scam networks.  
* On-chain data of the blockchain possesses absolute transparency, integrity, and irreversibility.  
* The inherent structure of blockchain consists of graph networks (wallets are nodes, transaction flows are edges), completely compatible and an ideal environment for testing network analysis algorithms and quantum optimization.

This approach overcomes the limitations of traditional finance (TradFi) where data is fragmented, siloed, and entangled in strict legal regulations.

### **Answer 3: Feasibility of Obtaining a Letter of Intent (LOI)**

Obtaining a collaboration document or a non-binding Letter of Intent (LOI) is completely feasible and is the core action goal of the team before entering the Finals in Vietnam. The team agrees on the strategy to completely bypass prolonged and ineffective user interviews, moving straight into demonstrating real value through specific growth numbers.  
AML AI Copilot will build a Proof-of-Concept (POC) model running on historical blockchain data to demonstrate the system's effectiveness in reducing false positive rates for partners. The specific goal is to secure a non-binding LOI with a mid-sized Crypto exchange in Southeast Asia or a leading Web3 security firm. The team also aims to leverage Mentor Kai's strong network connections in the industry to get warm introductions directly to Chief Compliance Officers.

### **Answer 4: Data Sources of the System**

The initial foundational data source of the system comes from public ledgers (Public Ledger Data) such as Etherscan API (Ethereum), Binance Smart Chain (BSC) combined with the industry-standard open-source dataset on Kaggle, the Elliptic Data Set (which maps Bitcoin transactions to licit/illicit entities) to train the baseline model.  
To build a comprehensive AI AML model covering both on-chain, off-chain behaviors and legal realities, the data source is expanded in depth according to 3 groups:

* **Expanded On-chain Data & Transaction Graphs:** Using Dune Analytics (writing SQL queries to extract complex behavior patterns from DeFi protocols, Tornado Cash, cross-chain bridges), The Graph (GraphQL APIs querying dApps status via highly standardized graph structures), and Stanford Network Analysis Platform (SNAP) Bitcoin Datasets to analyze entity reputation scores.  
* **Threat Intelligence & Sanction Lists:** Integrating OpenSanctions Database (continuously updated international open data on politically exposed persons PEPs, entities sanctioned by OFAC, EU, UN), OFAC Sanctions List API (official list of sanctioned crypto wallet addresses), and CryptoScamDB (community datasets recording wallets related to phishing, malware, or rug-pull projects on GitHub) to serve as Ground Truth.  
* **Advanced Synthetic Data Generation:** Using the open-source framework IBM AMLSim (Multi-Agent Simulation) to configure common money laundering scenarios (such as structuring, smurfing, layering) to generate millions of real-world-like complex simulated transactions, combined with PaySim and Quantum Circuit Born Machines techniques to simulate transaction distributions for stress-testing.

After securing an LOI with a partner, the system will conduct specialized fine-tuning using proprietary flagged-wallet data directly from the partner's own system.

### **Answer 5: Exact Objective Function for Minimizing False Positives**

In the AML compliance field, data is extremely imbalanced (the proportion of dirty transactions is small but causes massive noise). Therefore, AML AI Copilot does not use standard accuracy (Accuracy). The ultimate goal of the system is to Minimize the False Positive Rate (FPR) while maintaining recall (Recall) at an acceptable baseline level. Each false positive represents a wrong account freeze, severely damaging user experience and wasting operational resources on manual checks.  
The specific mathematical model applied is optimizing the weighted F-score (F\_β) with the parameter condition β \< 1 to prioritize precision (Precision) over recall (Recall):

E\_β \= ((1 \+ β^2) \* Precision \* Recall) / ((β^2 \* Precision) \+ Recall)

Where the individual components are defined as:

Precision \= TP / (TP \+ FP)  
Recall \= TP / (TP \+ FN)

Forcing the parameter β below 1 ensures that the system only flags alerts when the probability of that entity being involved in financial crime is extremely high, optimizing investigative resources.

### **Answer 6: Leveraging AI Agent Capabilities**

The team commits to fully and comprehensively exploiting the power of AI Agents at 3 structural levels, fully orchestrated by a robust Quantum-as-a-Service middleware:

* **Core Orchestration Layer (Quapp Platform):** To synchronize our complex AI and quantum elements, we utilize Quapp.cloud as our core "Launchpad for Quantum Builders". Quapp acts as the central middleware managing the project lifecycle, handling asynchronous tasks, and seamlessly connecting the Hybrid Quantum-HPC workflows between our autonomous AI Agents and traditional high-performance computing infrastructure.  
* **Engineering Level:** Utilizing specialized coding agent workflows to automatically generate source code boilerplate for modules using Rust, supporting automated testing and ultra-fast infrastructure deployment, reducing time-to-market.  
* **Product Level:** The product architecture integrates a multi-agent system. When the quantum optimization model detects and flags a suspicious transaction node, the system immediately activates an autonomous AI Agent. This agent automatically traces multi-hop cash flows, gathers open-source threat intelligence (OSINT), cross-references KYC entities, and automatically compiles a detailed, structured, auditable compliance report.  
* **Presentation Level (External-facing):** AI Agents are applied to optimize the R\&D process, standardize fundraising documentation (packaging), and create high-quality solution introductory videos to maximize scoring potential before the judging panel and investors.

### **Answer 7: Pure Quantum ML vs. Quantum-Inspired Optimization**

AML AI Copilot chooses the direction of Quantum-inspired optimization combined with solving QUBO (Quadratic Unconstrained Binary Optimization) problems using Tensor Networks, instead of using Pure Quantum ML.  
The core technical reason is that current real-world quantum computers (the NISQ generation \- Noisy Intermediate-Scale Quantum) still face massive hardware limitations due to the lack of fault-tolerant hardware and insufficient stable qubits to process massive blockchain transaction graphs in real time. Mapping the combinatorial optimization problem to QUBO and running quantum-inspired algorithms on classical High-Performance Computing (HPC) infrastructure solves the customer's real-world problem immediately (reducing 90% of false positives).  
**Real-world Simulation & Scaling Pathway:** However, our architecture is entirely "Quantum-Ready" and goes beyond mere theoretical design. Leveraging deep technical insights from the Qudora Training Session, the team is actively adapting the system for Trapped-Ion architectures. We utilize the Qamelion Emulator (Qudora's hardware simulator) to test run combinatorial algorithms like QAOA and QUBO on simulated transaction data.  
Looking toward the future shift to Quantum Processing Units (QPUs), we identify Qudora's NFQC® (Near-Field Quantum Control) technology as a critical advantage. By utilizing microwave magnetic fields integrated directly on-chip rather than bulky optical lasers, this approach perfectly aligns with our system's need for scalable, high-volume processing of blockchain graph networks when real quantum hardware reaches its tipping point.

### **Answer 8: Baseline Models for Benchmarking**

To prove the superior advantage of the quantum-inspired optimization architecture, AML AI Copilot designs a benchmark process directly against the strongest industry standard models on two data structures:

* **For Graph Data:** Benchmarking against standard Graph Neural Networks (GNNs), specifically GraphSAGE and GAT (Graph Attention Network) currently deployed by entities like Chainalysis and Elliptic.  
* **For Tabular Data:** Benchmarking against ensemble tree models including XGBoost and Random Forest.

### **Answer 9: Research Paper Publication Plan**

Yes. The team has a clear plan to publish a detailed arXiv preprint deeply analyzing the Hybrid Quantum-Agentic Architecture in detecting on-chain entities immediately after completing the technical benchmark numbers. The combination of quantum-inspired graph processing and the use of LLM Agents for model explanation (Explainable AI \- XAI) is an extremely new academic direction, creating a strong technical credibility and competitive edge for both the Quantathon panel and technical deep tech venture capital investors.

### **Answer 10: 2x2 Competitive Landscape Matrix**

As requested, the competitive landscape is presented below in an expanded tabular form, highlighting the structural positioning across computing paradigms and operational workflows:

| Compute / Processing Paradigm | Manual Investigation (Slow / Manual Process) | Autonomous Agentic Reporting (Fast / Autonomous Workflow)   |
| :---- | :---- | :---- |
| **Quantum-Ready / Quantum-Inspired** Multidimensional network processing without QPU constraints | **QUADRANT 3: EXPLORATORY** High-level algorithmic thinking capable of assessing complex multi-hop graphs, but bottlenecked by sequential manual verification workflows, relying heavily on slow human analysis. | **QUADRANT 4: SMART PIONEER** Multidimensional network optimization combined with automated reasoning. Self-executing data triage operating at real-time speeds to uncover deeply hidden patterns. **AML AI COPILOT (LEADER)** |
| **Traditional AI/ML** Linear, tabular, and traditional rule-based mechanisms | **QUADRANT 1: LEGACY PROCESSING** Sequential rule-based processing where human analysts must directly intervene at every single validation step. False positive rates typically exceed 90%. | **QUADRANT 2: LINEAR AUTOMATION** Execution of automated linear scripts for rapid rote tasks, but severely lacks contextual reasoning capabilities or a holistic graphwide-understanding of anomalies. |

### **Answer 11: 30-Second Elevator Pitch**

"AML AI Copilot is a specialized anti-money laundering platform neutralizing crypto laundering and scam networks in Southeast Asia. We solve the 90% false positive problem of current systems by combining quantum-inspired optimization to process millions of on-chain data points that traditional models miss. Beyond just flagging data, our autonomous AI agents instantly investigate anomalies and auto-generate compliance reports, saving exchanges millions in regulatory fines and operational overhead. Instead of selling software the old way, we directly monetize through an independent Bounty Hunting model on illicit funds. We are faster, smarter, and quantum-ready\!"

### **Answer 12: Target Market Sequencing: TradFi vs. Crypto**

AML AI Copilot chooses the strategic starting point of Crypto AML. The crypto transaction market in Southeast Asia is currently a global hotspot for dirty money flows and scam losses. More importantly from a technical standpoint, blockchain data is entirely transparent, freely accessible, and its natural graph structure is perfectly compatible with quantum network optimization algorithms. This allows the team to rapidly build, test, and optimize models, avoiding the immediate hurdle of facing "frozen" (siloed), closed data and extremely complex privacy regulations of traditional finance (TradFi) banks.

### **Answer 13: Business Model Evolution: Bounty Hunting vs. SaaS**

AML AI Copilot does not follow a traditional B2B enterprise SaaS model from the start because the sales cycle is very long and it is difficult to prove capability without an established brand. Instead, the project deploys a highly pragmatic Go-To-Market strategy using the Bounty Hunting model (Independent Bounty Hunting).  
The system will initially operate similarly to an internal security/quant fund. The team uses its own quantum-inspired and AI Agent technology infrastructure to actively scan, detect, and trace large-scale hacks and scam wallets on the public blockchain ledger. Then, AML AI Copilot coordinates with exchanges to provide evidence to freeze assets and receives a percentage of recovered fees (via Arkham Intel Exchange or direct Bug/ Protocol Bounties from projects). Proving the capability to generate profits with real money will be an ironclad proof and the strongest leverage helping the company transition to selling a subscription SaaS model to large financial institutions later.

### **Answer 14: Specific Support from Mentor Kai**

The AML AI Copilot team positions specific support from Mentor Kai \- who operates a specialized quant fund at two major strategic turning points:

1. **Warm Intros & LOI:** Leveraging Kai's deep network in the global crypto ecosystem, the team hopes he can directly connect them to Chief Compliance Officers and Risk Management departments at major crypto exchanges in SEA or leading Web3 Security firms to present the technical solution and secure a non-binding Letter of Intent (LOI).  
2. **Benchmark Design:** The team highly values Kai's direct guidance in structuring the problem and designing the quantum-inspired benchmark metrics. The orientation of a quantum finance expert will ensure the output numbers meet rigorous standards, possessing absolute persuasiveness before tech investors, academic peers, and enterprise risk management teams.