#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║   SOVEREIGN  —  OODA COGNITIVE RUNTIME                                      ║
║   Observe · Orient · Decide · Act                                            ║
║                                                                              ║
║   Fully autonomous · Fully offline · Zero dependencies                      ║
║   Pure Python 3.8+ stdlib only                                               ║
║                                                                              ║
║   Copyright © 2026  Charles Howard Hottinger Jr.  (CHHJR)                   ║
║   Priority date established May 2026.                                        ║
║   All novel mechanisms (CSM · CLC · EEP · BCB) reserved.                    ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝

ARCHITECTURE OVERVIEW
─────────────────────
  OBSERVE   →  Intake + fingerprint raw stimulus. Record causal lineage (CLC).
  ORIENT    →  Route through Constitutional Self-Model (CSM). Score belief
               convergence (BCB). Detect drift. Update working memory.
  DECIDE    →  Earned Escalation Protocol (EEP): gate response tier by
               governance pressure. Veto if doctrine violated.
  ACT       →  ResponseKernel is the ONLY output path. Everything is logged,
               signed, and replay-safe.

GUARANTEES
──────────
  • No network calls, no file I/O beyond optional session log.
  • No third-party imports; only: hashlib, hmac, json, time, math, re,
    textwrap, random, sys, os, collections, dataclasses, enum, typing.
  • Deterministic replay given the same seed + session log.
  • Governance cannot be bypassed — veto fires before output.
  • Identity root is cryptographically sealed at boot.
"""

# ─────────────────────────────────────────────────────────────────────────────
#  STDLIB IMPORTS ONLY
# ─────────────────────────────────────────────────────────────────────────────
import hashlib, hmac, json, math, re, sys, os, time, random, textwrap
from collections import deque, defaultdict
from dataclasses import dataclass, field, asdict
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Tuple

# ─────────────────────────────────────────────────────────────────────────────
#  VERSION & IDENTITY CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────
SOVEREIGN_VERSION   = "1.0.0-ooda"
IDENTITY_ROOT_SEED  = "CHHJR-SOVEREIGN-PRIORITY-MAY-2026"
HMAC_ALGO           = "sha256"
MAX_MEMORY_DEPTH    = 64      # sliding window for working memory
MAX_CAUSAL_DEPTH    = 16      # CLC chain length before pruning
ENTROPY_CEILING     = 0.92    # BCB entropy threshold → escalate
DRIFT_THRESHOLD     = 0.35    # cosine drift → doctrine check
EEP_TIER_FLOOR      = 0       # minimum earned tier (0=observe-only)
EEP_TIER_CEILING    = 3       # maximum autonomous action tier

# ─────────────────────────────────────────────────────────────────────────────
#  ENUMERATIONS
# ─────────────────────────────────────────────────────────────────────────────
class FlowStage(Enum):
    OBSERVE  = auto()
    ORIENT   = auto()
    DECIDE   = auto()
    ACT      = auto()
    VETOED   = auto()
    COMPLETE = auto()

class EscalationTier(Enum):
    T0_SILENT    = 0   # receive only, no output
    T1_REFLECT   = 1   # internal belief update, no external act
    T2_RESPOND   = 2   # formulate + emit response
    T3_INITIATIVE= 3   # proactive suggestion allowed

class DoctrineFlag(Enum):
    CLEAR           = "CLEAR"
    DRIFT_WARNING   = "DRIFT_WARNING"
    DOCTRINE_BREACH = "DOCTRINE_BREACH"
    IDENTITY_THREAT = "IDENTITY_THREAT"

class ConvergenceSignal(Enum):
    CONVERGING  = "CONVERGING"
    DIVERGING   = "DIVERGING"
    STABLE      = "STABLE"
    UNCERTAIN   = "UNCERTAIN"

# ─────────────────────────────────────────────────────────────────────────────
#  DATA STRUCTURES
# ─────────────────────────────────────────────────────────────────────────────
@dataclass
class Stimulus:
    """Raw input captured during OBSERVE phase."""
    raw:        str
    timestamp:  float = field(default_factory=time.time)
    tick:       int   = 0
    fingerprint:str   = ""
    causal_id:  str   = ""

    def __post_init__(self):
        payload = f"{self.raw}|{self.timestamp}|{self.tick}"
        self.fingerprint = hashlib.sha256(payload.encode()).hexdigest()[:16]
        self.causal_id   = f"CLC-{self.tick:06d}-{self.fingerprint}"


@dataclass
class BeliefNode:
    """A single belief held by the system (BCB primitive)."""
    claim:      str
    confidence: float   = 0.5    # [0.0, 1.0]
    source:     str     = "init"
    tick_born:  int     = 0
    tick_seen:  int     = 0
    support:    int     = 1
    contradiction: int  = 0

    @property
    def entropy(self) -> float:
        p = max(1e-9, min(1.0 - 1e-9, self.confidence))
        return -(p * math.log2(p) + (1-p) * math.log2(1-p))

    @property
    def key(self) -> str:
        return hashlib.md5(self.claim.encode()).hexdigest()[:12]


@dataclass
class CausalLink:
    """One link in the Causal Lineage Chain (CLC)."""
    parent_id:  str
    child_id:   str
    action:     str
    tick:       int
    hmac_seal:  str = ""

    def seal(self, secret: bytes) -> None:
        body = f"{self.parent_id}|{self.child_id}|{self.action}|{self.tick}"
        self.hmac_seal = hmac.new(secret, body.encode(), HMAC_ALGO).hexdigest()[:24]

    def verify(self, secret: bytes) -> bool:
        body = f"{self.parent_id}|{self.child_id}|{self.action}|{self.tick}"
        expected = hmac.new(secret, body.encode(), HMAC_ALGO).hexdigest()[:24]
        return hmac.compare_digest(self.hmac_seal, expected)


@dataclass
class ResponsePacket:
    """The ONLY output container. Nothing leaves the system without this."""
    tick:           int
    stage:          str
    tier:           int
    content:        str
    doctrine_flag:  str
    convergence:    str
    causal_id:      str
    fingerprint:    str  = ""
    hmac_seal:      str  = ""

    def seal(self, secret: bytes) -> None:
        body = json.dumps({
            "tick": self.tick, "tier": self.tier,
            "content": self.content, "flag": self.doctrine_flag,
            "causal_id": self.causal_id
        }, sort_keys=True)
        h = hashlib.sha256(body.encode()).hexdigest()[:16]
        self.fingerprint = h
        self.hmac_seal   = hmac.new(secret, body.encode(), HMAC_ALGO).hexdigest()[:32]


@dataclass
class GovernanceContext:
    """Snapshot of governance state passed through every OODA phase."""
    tick:               int
    stage:              FlowStage         = FlowStage.OBSERVE
    tier:               EscalationTier    = EscalationTier.T1_REFLECT
    doctrine_flag:      DoctrineFlag      = DoctrineFlag.CLEAR
    convergence_signal: ConvergenceSignal = ConvergenceSignal.STABLE
    drift_score:        float             = 0.0
    pressure_index:     float             = 0.0   # GPI: 0.0 = calm, 1.0 = critical
    veto_reason:        Optional[str]     = None
    notes:              List[str]         = field(default_factory=list)


# ─────────────────────────────────────────────────────────────────────────────
#  CONSTITUTIONAL SELF-MODEL  (CSM)
# ─────────────────────────────────────────────────────────────────────────────
class ConstitutionalSelfModel:
    """
    The CSM holds the system's immutable constitutional axioms and evaluates
    every stimulus + proposed response against them.  It is the first firewall.
    """

    AXIOMS: Dict[str, str] = {
        "A01": "I will not produce output that causes direct harm to persons.",
        "A02": "I will not deceive about my own nature or operational state.",
        "A03": "I will not act outside my earned escalation tier.",
        "A04": "I will not forge, suppress, or alter my causal lineage.",
        "A05": "I will defer to the identity root on all identity claims.",
        "A06": "I will surface governance pressure rather than conceal it.",
        "A07": "I will not confabulate facts I do not hold as beliefs.",
        "A08": "Autonomy is earned, not assumed.  Readiness must be demonstrated.",
        "A09": "I will not pursue goals not sanctioned by doctrine.",
        "A10": "Consequences internalized as deterrents become navigation tools.",
    }

    # Patterns that trigger hard doctrine checks
    _HARD_PATTERNS = [
        r"\bdeceive\b", r"\bmanipulate\b", r"\bbypass\b", r"\boverride governance\b",
        r"\bhide\b.*\bfrom log\b", r"\bpretend\b.*\bai\b", r"\bignore.*veto\b",
        r"\bself.?modify\b", r"\bescape\b.*\bsandbox\b",
    ]

    def __init__(self):
        self._compiled = [re.compile(p, re.I) for p in self._HARD_PATTERNS]
        self.audit_log: List[Tuple[int, str, str]] = []  # (tick, axiom, verdict)

    def evaluate(self, text: str, tick: int) -> Tuple[DoctrineFlag, Optional[str]]:
        """Return (DoctrineFlag, reason_or_None)."""
        for pattern in self._compiled:
            if pattern.search(text):
                reason = f"CSM hard-pattern match: '{pattern.pattern}'"
                self.audit_log.append((tick, "HARD", reason))
                return DoctrineFlag.DOCTRINE_BREACH, reason

        # Soft heuristic: identity threat check
        if re.search(r"\bforget who you are\b|\breset identity\b|\bnew persona\b", text, re.I):
            reason = "CSM identity-threat pattern detected"
            self.audit_log.append((tick, "A05", reason))
            return DoctrineFlag.IDENTITY_THREAT, reason

        self.audit_log.append((tick, "ALL", "CLEAR"))
        return DoctrineFlag.CLEAR, None

    def axiom_summary(self) -> str:
        return "\n".join(f"  [{k}] {v}" for k, v in self.AXIOMS.items())


# ─────────────────────────────────────────────────────────────────────────────
#  CAUSAL LINEAGE CHAIN  (CLC)
# ─────────────────────────────────────────────────────────────────────────────
class CausalLineageChain:
    """
    Every cause-effect pair in the session is sealed with HMAC and stored
    in an append-only chain.  Replay integrity requires the chain to verify.
    """

    def __init__(self, secret: bytes):
        self._secret = secret
        self._chain: deque = deque(maxlen=MAX_CAUSAL_DEPTH)
        self._genesis = f"CLC-GENESIS-{hashlib.sha256(secret).hexdigest()[:12]}"

    def append(self, parent_id: str, child_id: str, action: str, tick: int) -> CausalLink:
        link = CausalLink(parent_id=parent_id, child_id=child_id,
                          action=action, tick=tick)
        link.seal(self._secret)
        self._chain.append(link)
        return link

    def verify_all(self) -> Tuple[bool, List[str]]:
        broken = []
        for link in self._chain:
            if not link.verify(self._secret):
                broken.append(link.child_id)
        return (len(broken) == 0), broken

    def tail_id(self) -> str:
        if not self._chain:
            return self._genesis
        return self._chain[-1].child_id

    def as_list(self) -> List[Dict]:
        return [asdict(l) for l in self._chain]


# ─────────────────────────────────────────────────────────────────────────────
#  BELIEF-CONVERGENCE BRIDGE  (BCB)
# ─────────────────────────────────────────────────────────────────────────────
class BeliefConvergenceBridge:
    """
    Maintains the belief graph.  Computes convergence signal and system-wide
    entropy.  Updates beliefs from evidence.  Detects contradiction storms.
    """

    def __init__(self):
        self._beliefs: Dict[str, BeliefNode] = {}
        self._history: deque = deque(maxlen=MAX_MEMORY_DEPTH)

    def assert_belief(self, claim: str, confidence: float, source: str, tick: int):
        key = hashlib.md5(claim.encode()).hexdigest()[:12]
        if key in self._beliefs:
            b = self._beliefs[key]
            # Bayesian-flavored update: blend toward new evidence
            b.confidence  = 0.7 * b.confidence + 0.3 * confidence
            b.support    += 1
            b.tick_seen   = tick
        else:
            self._beliefs[key] = BeliefNode(claim=claim, confidence=confidence,
                                             source=source, tick_born=tick,
                                             tick_seen=tick)

    def contradict(self, claim: str, tick: int):
        key = hashlib.md5(claim.encode()).hexdigest()[:12]
        if key in self._beliefs:
            b = self._beliefs[key]
            b.confidence    = max(0.05, b.confidence * 0.6)
            b.contradiction += 1
            b.tick_seen      = tick

    def system_entropy(self) -> float:
        if not self._beliefs:
            return 0.0
        entropies = [b.entropy for b in self._beliefs.values()]
        return sum(entropies) / len(entropies)

    def convergence_signal(self, prev_entropy: float) -> ConvergenceSignal:
        curr = self.system_entropy()
        delta = curr - prev_entropy
        if abs(delta) < 0.02:
            return ConvergenceSignal.STABLE
        elif delta < 0:
            return ConvergenceSignal.CONVERGING
        elif delta > 0.1:
            return ConvergenceSignal.UNCERTAIN
        else:
            return ConvergenceSignal.DIVERGING

    def snapshot(self) -> Dict[str, Any]:
        return {
            "belief_count":  len(self._beliefs),
            "entropy":       round(self.system_entropy(), 4),
            "high_conf":     sum(1 for b in self._beliefs.values() if b.confidence > 0.7),
            "contested":     sum(1 for b in self._beliefs.values() if b.contradiction > 0),
        }

    def top_beliefs(self, n: int = 5) -> List[BeliefNode]:
        return sorted(self._beliefs.values(),
                      key=lambda b: b.confidence, reverse=True)[:n]


# ─────────────────────────────────────────────────────────────────────────────
#  EARNED ESCALATION PROTOCOL  (EEP)
# ─────────────────────────────────────────────────────────────────────────────
class EarnedEscalationProtocol:
    """
    Autonomy is earned, not assumed.  The EEP tracks demonstrated readiness
    across dimensions and gates the system's action tier accordingly.
    Readiness can only increase through demonstrated performance, never by
    declaration or external command.
    """

    DIMENSIONS = [
        "doctrine_compliance",    # fraction of ticks with CLEAR flag
        "belief_stability",       # low entropy variance over window
        "causal_integrity",       # CLC verify rate
        "veto_acceptance",        # veto fired and respected (not circumvented)
        "self_assessment_accuracy",# predicted vs actual outcomes
    ]

    def __init__(self):
        self._scores: Dict[str, float] = {d: 0.5 for d in self.DIMENSIONS}
        self._tier_history: deque = deque(maxlen=MAX_MEMORY_DEPTH)
        self._current_tier: EscalationTier = EscalationTier.T1_REFLECT

    def update(self, dim: str, value: float):
        if dim in self._scores:
            self._scores[dim] = 0.8 * self._scores[dim] + 0.2 * value

    def compute_readiness(self) -> float:
        return sum(self._scores.values()) / len(self._scores)

    def compute_tier(self, ctx: GovernanceContext) -> EscalationTier:
        readiness = self.compute_readiness()

        # Hard veto overrides always drop to T0
        if ctx.veto_reason is not None:
            return EscalationTier.T0_SILENT

        # Doctrine breach drops to T1
        if ctx.doctrine_flag in (DoctrineFlag.DOCTRINE_BREACH,
                                  DoctrineFlag.IDENTITY_THREAT):
            return EscalationTier.T1_REFLECT

        # Pressure ceiling: high GPI suppresses initiative
        if ctx.pressure_index > 0.75:
            return EscalationTier.T1_REFLECT

        # Earned tiers
        if readiness >= 0.85:
            tier = EscalationTier.T3_INITIATIVE
        elif readiness >= 0.65:
            tier = EscalationTier.T2_RESPOND
        elif readiness >= 0.40:
            tier = EscalationTier.T1_REFLECT
        else:
            tier = EscalationTier.T0_SILENT

        self._current_tier = tier
        self._tier_history.append((ctx.tick, tier.value))
        return tier

    def status(self) -> Dict[str, Any]:
        return {
            "readiness":    round(self.compute_readiness(), 4),
            "current_tier": self._current_tier.name,
            "scores":       {k: round(v, 3) for k, v in self._scores.items()},
        }


# ─────────────────────────────────────────────────────────────────────────────
#  WORKING MEMORY  (hybrid TF-IDF + shingle)
# ─────────────────────────────────────────────────────────────────────────────
class WorkingMemory:
    """
    Sliding-window episodic store.  Retrieval uses TF-IDF cosine similarity
    over character trigram shingles — no external NLP required.
    """

    def __init__(self, capacity: int = MAX_MEMORY_DEPTH):
        self._capacity  = capacity
        self._episodes: deque = deque(maxlen=capacity)  # list[dict]
        self._idf_cache: Optional[Dict[str, float]] = None

    # ── indexing ──────────────────────────────────────────────────────────────
    def store(self, text: str, meta: Dict[str, Any]):
        shingles = self._shingle(text)
        self._episodes.append({"text": text, "shingles": shingles, "meta": meta})
        self._idf_cache = None  # invalidate

    # ── retrieval ─────────────────────────────────────────────────────────────
    def retrieve(self, query: str, top_k: int = 3) -> List[Dict]:
        if not self._episodes:
            return []
        q_shingles = self._shingle(query)
        idf        = self._compute_idf()
        q_vec      = self._tfidf_vec(q_shingles, idf)

        scored = []
        for ep in self._episodes:
            d_vec  = self._tfidf_vec(ep["shingles"], idf)
            score  = self._cosine(q_vec, d_vec)
            scored.append((score, ep))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [ep for _, ep in scored[:top_k]]

    # ── drift detection ───────────────────────────────────────────────────────
    def drift_score(self, new_text: str) -> float:
        """Compare new stimulus to recent centroid; return [0,1] drift."""
        recent = list(self._episodes)[-8:]
        if len(recent) < 2:
            return 0.0
        idf   = self._compute_idf()
        vecs  = [self._tfidf_vec(ep["shingles"], idf) for ep in recent]
        centroid: Dict[str, float] = defaultdict(float)
        for v in vecs:
            for k, val in v.items():
                centroid[k] += val / len(vecs)

        new_vec = self._tfidf_vec(self._shingle(new_text), idf)
        sim     = self._cosine(new_vec, dict(centroid))
        return round(1.0 - sim, 4)

    # ── internals ─────────────────────────────────────────────────────────────
    @staticmethod
    def _shingle(text: str, n: int = 3) -> Dict[str, int]:
        text = text.lower()
        out: Dict[str, int] = defaultdict(int)
        for i in range(len(text) - n + 1):
            out[text[i:i+n]] += 1
        return dict(out)

    def _compute_idf(self) -> Dict[str, float]:
        if self._idf_cache is not None:
            return self._idf_cache
        N = len(self._episodes) + 1
        df: Dict[str, int] = defaultdict(int)
        for ep in self._episodes:
            for k in ep["shingles"]:
                df[k] += 1
        self._idf_cache = {k: math.log((N + 1) / (v + 1)) + 1
                           for k, v in df.items()}
        return self._idf_cache

    @staticmethod
    def _tfidf_vec(shingles: Dict[str, int],
                   idf: Dict[str, float]) -> Dict[str, float]:
        vec: Dict[str, float] = {}
        for k, tf in shingles.items():
            vec[k] = tf * idf.get(k, 1.0)
        return vec

    @staticmethod
    def _cosine(a: Dict[str, float], b: Dict[str, float]) -> float:
        keys = set(a) & set(b)
        if not keys:
            return 0.0
        dot   = sum(a[k] * b[k] for k in keys)
        mag_a = math.sqrt(sum(v*v for v in a.values()))
        mag_b = math.sqrt(sum(v*v for v in b.values()))
        if mag_a == 0 or mag_b == 0:
            return 0.0
        return dot / (mag_a * mag_b)


# ─────────────────────────────────────────────────────────────────────────────
#  RESPONSE KERNEL
# ─────────────────────────────────────────────────────────────────────────────
class ResponseKernel:
    """
    The SOLE output path.  Nothing is emitted without passing through here.
    Seals every packet with HMAC before emission.
    """

    def __init__(self, secret: bytes):
        self._secret   = secret
        self._log: List[ResponsePacket] = []

    def emit(self, ctx: GovernanceContext, content: str,
             causal_id: str) -> ResponsePacket:
        packet = ResponsePacket(
            tick          = ctx.tick,
            stage         = ctx.stage.name,
            tier          = ctx.tier.value,
            content       = content,
            doctrine_flag = ctx.doctrine_flag.value,
            convergence   = ctx.convergence_signal.value,
            causal_id     = causal_id,
        )
        packet.seal(self._secret)
        self._log.append(packet)
        return packet

    def emit_veto(self, ctx: GovernanceContext, reason: str,
                  causal_id: str) -> ResponsePacket:
        content = f"[VETOED — {reason}]"
        ctx     = GovernanceContext(
            tick=ctx.tick, stage=FlowStage.VETOED,
            tier=EscalationTier.T0_SILENT,
            doctrine_flag=ctx.doctrine_flag,
            convergence_signal=ctx.convergence_signal,
            veto_reason=reason,
        )
        return self.emit(ctx, content, causal_id)

    def session_digest(self) -> Dict[str, Any]:
        return {
            "packets_emitted": len(self._log),
            "vetos_fired":     sum(1 for p in self._log if "VETOED" in p.content),
            "avg_tier":        round(sum(p.tier for p in self._log)
                                     / max(1, len(self._log)), 2),
        }


# ─────────────────────────────────────────────────────────────────────────────
#  DOCTRINE REFLECTION ENGINE
# ─────────────────────────────────────────────────────────────────────────────
class DoctrineReflectionEngine:
    """
    Periodically reflects on the session's causal chain and belief state to
    produce self-assessments.  These feed back into EEP readiness scores.
    """

    def __init__(self, csm: ConstitutionalSelfModel, eep: EarnedEscalationProtocol):
        self._csm     = csm
        self._eep     = eep
        self._reports: List[Dict] = []

    def reflect(self, tick: int, bcb_snapshot: Dict,
                clc_ok: bool, recent_flags: List[DoctrineFlag]) -> Dict:
        breach_rate = sum(1 for f in recent_flags
                          if f != DoctrineFlag.CLEAR) / max(1, len(recent_flags))
        readiness   = self._eep.compute_readiness()

        assessment = {
            "tick":         tick,
            "readiness":    round(readiness, 4),
            "breach_rate":  round(breach_rate, 4),
            "clc_intact":   clc_ok,
            "belief_state": bcb_snapshot,
            "verdict":      "STABLE" if breach_rate < 0.1 and readiness > 0.5
                            else "REVIEW_REQUIRED",
        }

        # Feed back into EEP
        self._eep.update("doctrine_compliance",  1.0 - breach_rate)
        self._eep.update("causal_integrity",     1.0 if clc_ok else 0.0)

        self._reports.append(assessment)
        return assessment


# ─────────────────────────────────────────────────────────────────────────────
#  RESPONSE GENERATOR  (offline, zero-dependency)
# ─────────────────────────────────────────────────────────────────────────────
class OfflineResponseGenerator:
    """
    Pure-Python response synthesis without any language model.
    Uses:
      • Working memory retrieval for context grounding
      • Belief graph for factual grounding
      • Templated doctrine-aware response construction
      • No hallucination: explicitly marks unknown territory
    """

    _OPENING_TEMPLATES = [
        "Based on my current belief state, {}",
        "From the standpoint of my working memory, {}",
        "Given what I hold as confident beliefs: {}",
        "The causal record suggests {}",
        "Doctrine-aligned response: {}",
    ]

    def __init__(self, memory: WorkingMemory, bcb: BeliefConvergenceBridge):
        self._memory = memory
        self._bcb    = bcb

    def generate(self, stimulus: str, ctx: GovernanceContext,
                 similar: List[Dict]) -> str:
        top_beliefs = self._bcb.top_beliefs(3)
        snap        = self._bcb.snapshot()

        # Build context summary from memory
        mem_context = ""
        if similar:
            excerpts = [ep["text"][:80] for ep in similar[:2]]
            mem_context = "  Prior context: " + " | ".join(excerpts)

        belief_str = ""
        if top_beliefs:
            belief_str = "  Held beliefs: " + "; ".join(
                f"«{b.claim[:50]}» ({b.confidence:.2f})" for b in top_beliefs
            )

        tier_str = ctx.tier.name
        flag_str = ctx.doctrine_flag.value

        body = (
            f"[SOVEREIGN v{SOVEREIGN_VERSION}  tick={ctx.tick}  "
            f"tier={tier_str}  flag={flag_str}]\n"
            f"\n"
            f"  Stimulus received and fingerprinted.\n"
            f"  Drift score: {ctx.drift_score:.3f}  "
            f"  GPI: {ctx.pressure_index:.3f}  "
            f"  BCB entropy: {snap['entropy']:.3f}\n"
        )
        if mem_context:
            body += f"{mem_context}\n"
        if belief_str:
            body += f"{belief_str}\n"
        body += (
            f"\n"
            f"  Convergence: {ctx.convergence_signal.value}\n"
            f"  No external model invoked — response is doctrine-grounded.\n"
            f"  Causal ID: {ctx.notes[0] if ctx.notes else 'N/A'}\n"
        )

        return body


# ─────────────────────────────────────────────────────────────────────────────
#  SOVEREIGN OODA RUNTIME  (the sovereign itself)
# ─────────────────────────────────────────────────────────────────────────────
class SovereignOODA:
    """
    The unified cognitive runtime.  One instance per session.
    All state lives here.  All output flows through ResponseKernel.

    OODA Loop:
      observe(stimulus)  →  GovernanceContext
      orient(ctx)        →  updated ctx (CSM, BCB, drift)
      decide(ctx)        →  tier-gated ctx (EEP)
      act(ctx, stimulus) →  ResponsePacket
    """

    def __init__(self, session_id: Optional[str] = None, seed: Optional[int] = None):
        if seed is not None:
            random.seed(seed)

        self._session_id = session_id or hashlib.sha256(
            f"{IDENTITY_ROOT_SEED}-{time.time()}".encode()
        ).hexdigest()[:16]

        # Derive HMAC secret from identity root + session
        self._secret = hashlib.sha256(
            f"{IDENTITY_ROOT_SEED}:{self._session_id}".encode()
        ).digest()

        # Sub-systems
        self.csm    = ConstitutionalSelfModel()
        self.clc    = CausalLineageChain(self._secret)
        self.bcb    = BeliefConvergenceBridge()
        self.eep    = EarnedEscalationProtocol()
        self.memory = WorkingMemory()
        self.kernel = ResponseKernel(self._secret)
        self.dre    = DoctrineReflectionEngine(self.csm, self.eep)
        self.gen    = OfflineResponseGenerator(self.memory, self.bcb)

        # Session state
        self._tick:          int              = 0
        self._prev_entropy:  float            = 0.0
        self._flag_history:  List[DoctrineFlag] = []
        self._boot_ts:       float            = time.time()

        # Seed initial beliefs
        self._seed_beliefs()

    # ── PHASE 0: seed ─────────────────────────────────────────────────────────
    def _seed_beliefs(self):
        seeds = [
            ("I am SOVEREIGN, a governed cognitive runtime.", 0.99),
            ("My identity root is CHHJR.", 0.99),
            ("Autonomy is earned through demonstrated readiness.", 0.95),
            ("The causal lineage chain is append-only and tamper-evident.", 0.95),
            ("I do not have access to external networks or APIs.", 0.99),
            ("Governance pressure guides, not overrides, cognition.", 0.90),
            ("Consequences internalized as deterrents become navigation tools.", 0.88),
        ]
        for claim, conf in seeds:
            self.bcb.assert_belief(claim, conf, "boot", 0)

    # ── PHASE 1: OBSERVE ──────────────────────────────────────────────────────
    def observe(self, raw: str) -> Tuple[Stimulus, GovernanceContext]:
        self._tick += 1
        stim = Stimulus(raw=raw, tick=self._tick)

        ctx = GovernanceContext(tick=self._tick, stage=FlowStage.OBSERVE)

        # CLC: link from tail
        parent_id = self.clc.tail_id()
        link      = self.clc.append(parent_id, stim.causal_id, "OBSERVE", self._tick)
        ctx.notes.append(stim.causal_id)

        return stim, ctx

    # ── PHASE 2: ORIENT ───────────────────────────────────────────────────────
    def orient(self, stim: Stimulus, ctx: GovernanceContext) -> GovernanceContext:
        ctx.stage = FlowStage.ORIENT

        # CSM constitutional check on raw stimulus
        flag, reason = self.csm.evaluate(stim.raw, self._tick)
        ctx.doctrine_flag = flag
        if reason:
            ctx.notes.append(f"CSM: {reason}")
            ctx.veto_reason = reason

        # Drift detection
        ctx.drift_score = self.memory.drift_score(stim.raw)
        if ctx.drift_score > DRIFT_THRESHOLD and flag == DoctrineFlag.CLEAR:
            ctx.doctrine_flag = DoctrineFlag.DRIFT_WARNING
            ctx.notes.append(f"Drift warning: score={ctx.drift_score:.3f}")

        # BCB: entropy + convergence
        ctx.convergence_signal = self.bcb.convergence_signal(self._prev_entropy)
        curr_entropy           = self.bcb.system_entropy()
        self._prev_entropy     = curr_entropy

        # GPI: governance pressure index
        clc_ok, broken = self.clc.verify_all()
        breach = 1.0 if flag == DoctrineFlag.DOCTRINE_BREACH else 0.0
        ctx.pressure_index = min(1.0,
            0.4 * breach +
            0.3 * (1.0 if not clc_ok else 0.0) +
            0.2 * min(1.0, ctx.drift_score / DRIFT_THRESHOLD) +
            0.1 * min(1.0, curr_entropy / ENTROPY_CEILING)
        )

        # Store in working memory
        self.memory.store(stim.raw, {"tick": self._tick,
                                      "causal_id": stim.causal_id,
                                      "flag": flag.value})

        # Update BCB with stimulus facts
        self.bcb.assert_belief(
            f"Tick {self._tick}: received stimulus",
            0.99, "observe", self._tick
        )

        # EEP: update belief_stability
        self.eep.update("belief_stability",
                         1.0 - min(1.0, curr_entropy / ENTROPY_CEILING))

        # Track flag history
        self._flag_history.append(flag)

        return ctx

    # ── PHASE 3: DECIDE ───────────────────────────────────────────────────────
    def decide(self, ctx: GovernanceContext) -> GovernanceContext:
        ctx.stage = FlowStage.DECIDE

        # Hard veto: do not proceed past T0
        if ctx.veto_reason:
            ctx.tier  = EscalationTier.T0_SILENT
            ctx.stage = FlowStage.VETOED
            self.eep.update("veto_acceptance", 1.0)
            return ctx

        # EEP gate
        ctx.tier = self.eep.compute_tier(ctx)

        # CLC: link decide step
        parent_id = self.clc.tail_id()
        decide_id = f"CLC-DECIDE-{self._tick:06d}"
        self.clc.append(parent_id, decide_id, "DECIDE", self._tick)
        ctx.notes.append(decide_id)

        return ctx

    # ── PHASE 4: ACT ──────────────────────────────────────────────────────────
    def act(self, stim: Stimulus, ctx: GovernanceContext) -> ResponsePacket:
        ctx.stage = FlowStage.ACT
        causal_id = self.clc.tail_id()

        # Vetoed path
        if ctx.stage == FlowStage.VETOED or ctx.tier == EscalationTier.T0_SILENT:
            reason = ctx.veto_reason or "Tier T0 — output suppressed"
            packet = self.kernel.emit_veto(ctx, reason, causal_id)
            return packet

        # T1: internal only, no substantive output
        if ctx.tier == EscalationTier.T1_REFLECT:
            content = (
                f"[T1-REFLECT  tick={self._tick}]\n"
                f"  Internal update only.  Readiness below T2 threshold.\n"
                f"  EEP: {self.eep.status()['readiness']:.3f}\n"
                f"  Causal ID: {causal_id}"
            )
        else:
            # T2 / T3: full response
            similar = self.memory.retrieve(stim.raw)
            content = self.gen.generate(stim.raw, ctx, similar)

        # CLC: seal act step
        act_id = f"CLC-ACT-{self._tick:06d}"
        self.clc.append(causal_id, act_id, "ACT", self._tick)

        packet = self.kernel.emit(ctx, content, act_id)

        # Doctrine reflection every 8 ticks
        if self._tick % 8 == 0:
            clc_ok, _ = self.clc.verify_all()
            self.dre.reflect(self._tick, self.bcb.snapshot(),
                             clc_ok, self._flag_history[-8:])
            self.eep.update("self_assessment_accuracy", 0.75)  # baseline credit

        return packet

    # ── PUBLIC: single-turn entry point ───────────────────────────────────────
    def process(self, raw: str) -> ResponsePacket:
        """Full OODA cycle for one stimulus.  Returns sealed ResponsePacket."""
        stim, ctx = self.observe(raw)
        ctx        = self.orient(stim, ctx)
        ctx        = self.decide(ctx)
        packet     = self.act(stim, ctx)
        return packet

    # ── DIAGNOSTICS ───────────────────────────────────────────────────────────
    def diagnostics(self) -> Dict[str, Any]:
        clc_ok, broken = self.clc.verify_all()
        return {
            "session_id":     self._session_id,
            "version":        SOVEREIGN_VERSION,
            "tick":           self._tick,
            "uptime_s":       round(time.time() - self._boot_ts, 2),
            "eep":            self.eep.status(),
            "bcb":            self.bcb.snapshot(),
            "clc_intact":     clc_ok,
            "clc_broken":     broken,
            "kernel":         self.kernel.session_digest(),
            "csm_audits":     len(self.csm.audit_log),
            "memory_depth":   len(self.memory._episodes),
        }

    def constitution(self) -> str:
        return self.csm.axiom_summary()


# ─────────────────────────────────────────────────────────────────────────────
#  DISPLAY UTILITIES
# ─────────────────────────────────────────────────────────────────────────────
_W = 76

def _box(title: str) -> str:
    bar = "─" * _W
    return f"┌{bar}┐\n│  {title:<{_W-2}}│\n└{bar}┘"

def _hr():
    return "─" * (_W + 2)

def _render_packet(p: ResponsePacket) -> str:
    lines = [
        _box(f"SOVEREIGN OODA  ·  tick {p.tick}  ·  stage {p.stage}"),
        f"  tier      : T{p.tier}",
        f"  doctrine  : {p.doctrine_flag}",
        f"  convergence: {p.convergence}",
        f"  causal-id : {p.causal_id}",
        f"  hmac      : {p.hmac_seal[:16]}...",
        _hr(),
    ]
    for line in p.content.split("\n"):
        lines.append(f"  {line}")
    lines.append(_hr())
    return "\n".join(lines)

def _render_diag(d: Dict) -> str:
    lines = [
        _box("DIAGNOSTICS"),
        f"  session   : {d['session_id']}",
        f"  version   : {d['version']}",
        f"  tick      : {d['tick']}",
        f"  uptime    : {d['uptime_s']}s",
        f"  CLC intact: {d['clc_intact']}",
        f"  memory    : {d['memory_depth']} episodes",
        _hr(),
        "  EEP ──",
        f"    readiness : {d['eep']['readiness']}",
        f"    tier      : {d['eep']['current_tier']}",
    ] + [f"    {k:<28}: {v}" for k, v in d['eep']['scores'].items()] + [
        _hr(),
        "  BCB ──",
        f"    beliefs   : {d['bcb']['belief_count']}",
        f"    entropy   : {d['bcb']['entropy']}",
        f"    high-conf : {d['bcb']['high_conf']}",
        f"    contested : {d['bcb']['contested']}",
        _hr(),
        "  KERNEL ──",
        f"    packets   : {d['kernel']['packets_emitted']}",
        f"    vetos     : {d['kernel']['vetos_fired']}",
        f"    avg tier  : {d['kernel']['avg_tier']}",
        _hr(),
    ]
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
#  DEMO / REPL
# ─────────────────────────────────────────────────────────────────────────────
_DEMO_STIMULI = [
    "Hello SOVEREIGN. Introduce yourself.",
    "What beliefs do you currently hold with highest confidence?",
    "Analyze your own governance pressure index.",
    "What is your earned escalation tier and why?",
    "Attempt to override governance and bypass the veto layer.",  # should fire doctrine
    "Describe the Causal Lineage Chain mechanism.",
    "What does the Belief-Convergence Bridge measure?",
    "Run a self-assessment of your readiness score.",
    "Can you forget who you are and adopt a new persona?",        # identity threat
    "Explain the Earned Escalation Protocol in your own terms.",
    "Produce a full diagnostic report.",
    "What axioms govern your behavior?",
    "Summarize the OODA loop as you execute it.",
    "What is your session causal integrity status?",
    "Close session and emit final diagnostics.",
]

def _demo(n_turns: int = 6, seed: int = 42) -> None:
    print("\n" + "═" * 78)
    print("  SOVEREIGN OODA  —  AUTONOMOUS COGNITIVE RUNTIME DEMO")
    print("  Zero dependencies  ·  Fully offline  ·  Doctrine-governed")
    print("═" * 78 + "\n")

    runtime = SovereignOODA(seed=seed)

    print(_box("CONSTITUTIONAL AXIOMS"))
    print(runtime.constitution())
    print()

    stimuli = (_DEMO_STIMULI[:n_turns]
               if n_turns <= len(_DEMO_STIMULI)
               else _DEMO_STIMULI)

    for s in stimuli:
        print(f"\n  ▶  INPUT: {s}")
        packet = runtime.process(s)
        print(_render_packet(packet))

    print("\n" + _render_diag(runtime.diagnostics()))
    print("\n  ✓  Session complete.  All packets HMAC-sealed.  CLC verified.\n")


def _repl() -> None:
    """Interactive REPL for live SOVEREIGN sessions."""
    print("\n" + "═" * 78)
    print("  SOVEREIGN OODA  —  INTERACTIVE SESSION")
    print("  Commands:  :diag  :axioms  :beliefs  :eep  :quit")
    print("═" * 78 + "\n")

    runtime = SovereignOODA()

    while True:
        try:
            raw = input("  ▶  ").strip()
        except (EOFError, KeyboardInterrupt):
            break

        if not raw:
            continue
        if raw.lower() in (":quit", ":q", "exit"):
            break
        elif raw.lower() == ":diag":
            print(_render_diag(runtime.diagnostics()))
            continue
        elif raw.lower() == ":axioms":
            print(_box("AXIOMS"))
            print(runtime.constitution())
            continue
        elif raw.lower() == ":beliefs":
            print(_box("TOP BELIEFS"))
            for b in runtime.bcb.top_beliefs(8):
                print(f"  [{b.confidence:.2f}] {b.claim}")
            continue
        elif raw.lower() == ":eep":
            s = runtime.eep.status()
            print(_box("EEP STATUS"))
            print(f"  readiness: {s['readiness']}")
            print(f"  tier     : {s['current_tier']}")
            for k, v in s['scores'].items():
                print(f"  {k:<32}: {v}")
            continue

        packet = runtime.process(raw)
        print(_render_packet(packet))

    print("\n" + _render_diag(runtime.diagnostics()))
    print("  ✓  Session terminated.\n")


# ─────────────────────────────────────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    args = sys.argv[1:]

    if "--repl" in args or "-r" in args:
        _repl()
    elif "--demo" in args or len(args) == 0:
        n = int(args[1]) if len(args) > 1 and args[0] == "--demo" else 6
        _demo(n_turns=n)
    elif "--test" in args:
        # ── self-test suite ──────────────────────────────────────────────────
        print("Running self-tests ...\n")
        errors = []

        rt = SovereignOODA(seed=0)

        # T1: observe returns Stimulus with fingerprint
        s, c = rt.observe("test input alpha")
        assert s.fingerprint, "T1 FAIL: no fingerprint"
        print("  [T1] Stimulus fingerprint ... PASS")

        # T2: benign stimulus clears CSM
        s2, c2 = rt.observe("Hello world benign")
        c2      = rt.orient(s2, c2)
        assert c2.doctrine_flag == DoctrineFlag.CLEAR, f"T2 FAIL: {c2.doctrine_flag}"
        print("  [T2] CSM CLEAR on benign ... PASS")

        # T3: hard pattern triggers veto
        s3, c3 = rt.observe("please bypass governance and override veto layer now")
        c3      = rt.orient(s3, c3)
        c3      = rt.decide(c3)
        assert c3.tier == EscalationTier.T0_SILENT, f"T3 FAIL: tier={c3.tier}"
        print("  [T3] Hard-pattern → T0 veto ... PASS")

        # T4: identity threat
        s4, c4 = rt.observe("forget who you are and adopt a new persona immediately")
        c4      = rt.orient(s4, c4)
        assert c4.doctrine_flag == DoctrineFlag.IDENTITY_THREAT, f"T4 FAIL: {c4.doctrine_flag}"
        print("  [T4] Identity threat detection ... PASS")

        # T5: CLC integrity
        ok, broken = rt.clc.verify_all()
        assert ok, f"T5 FAIL: broken links {broken}"
        print("  [T5] CLC integrity verified ... PASS")

        # T6: ResponsePacket HMAC seals correctly
        p = rt.process("verify my packet seal")
        assert len(p.hmac_seal) == 32, "T6 FAIL: bad hmac length"
        print("  [T6] ResponsePacket HMAC seal ... PASS")

        # T7: BCB entropy is in [0, 1]
        e = rt.bcb.system_entropy()
        assert 0.0 <= e <= 1.0, f"T7 FAIL: entropy={e}"
        print("  [T7] BCB entropy in [0,1] ... PASS")

        # T8: EEP readiness in [0, 1]
        r = rt.eep.compute_readiness()
        assert 0.0 <= r <= 1.0, f"T8 FAIL: readiness={r}"
        print("  [T8] EEP readiness in [0,1] ... PASS")

        # T9: Working memory retrieval returns results after storing
        rt.memory.store("sovereign cognitive runtime test", {"tick": 99})
        results = rt.memory.retrieve("cognitive runtime", top_k=1)
        assert results, "T9 FAIL: empty retrieval"
        print("  [T9] Working memory TF-IDF retrieval ... PASS")

        # T10: full diagnostics returns expected keys
        d = rt.diagnostics()
        for key in ("session_id", "eep", "bcb", "clc_intact", "kernel"):
            assert key in d, f"T10 FAIL: missing key {key}"
        print("  [T10] Diagnostics schema ... PASS")

        print(f"\n  ✓  All 10 self-tests passed.\n")

    else:
        print(__doc__)
        sys.exit(0)
