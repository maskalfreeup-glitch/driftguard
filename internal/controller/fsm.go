package controller

import (
	"fmt"
	"strings"
	"sync"

	"driftguard/internal/quorum"
)

// NodeState defines the hysteresis state of a monitored node.
type NodeState string

const (
	StateHealthy    NodeState = "HEALTHY"
	StateSuspect    NodeState = "SUSPECT"
	StateDrained    NodeState = "DRAINED"
	StateRecovering NodeState = "RECOVERING"
)

// Telemetry alert types
const (
	AlertMinimumHealthyTriggered = "MINIMUM_HEALTHY_TRIGGERED"
	AlertForkDivergenceDetected  = "FORK_DIVERGENCE_DETECTED"
	AlertNodeLagging             = "NODE_LAGGING"
	AlertNodeDrained             = "NODE_DRAINED"
	AlertNodeRecovered           = "NODE_RECOVERED"
)

// FSMConfig holds tuning parameters for hysteresis and actuation.
type FSMConfig struct {
	BackendName        string `json:"backend_name"`
	ServerName         string `json:"server_name"`
	LagThreshold       uint64 `json:"lag_threshold"`        // default: 4 blocks
	SuspectThresholdK  int    `json:"suspect_threshold_k"`  // default: 3 consecutive suspect ticks
	RecoveryThresholdM int    `json:"recovery_threshold_m"` // default: 5 consecutive synced ticks
}

// DefaultFSMConfig provides default parameters satisfying the Arbitrum Nitro specification.
func DefaultFSMConfig(backend, server string) FSMConfig {
	return FSMConfig{
		BackendName:        backend,
		ServerName:         server,
		LagThreshold:       4,
		SuspectThresholdK:  3,
		RecoveryThresholdM: 5,
	}
}

// TickResult records the state transition and actuation decisions of a single tick.
type TickResult struct {
	PreviousState  NodeState `json:"previous_state"`
	CurrentState   NodeState `json:"current_state"`
	SuspectCount   int       `json:"suspect_count"`
	RecoveryCount  int       `json:"recovery_count"`
	LagBlocks      uint64    `json:"lag_blocks"`
	ForkDivergent  bool      `json:"fork_divergent"`
	DrainAction    bool      `json:"drain_action"`
	ReadyAction    bool      `json:"ready_action"`
	DrainRefused   bool      `json:"drain_refused"`
	AlertEmitted   string    `json:"alert_emitted,omitempty"`
	FrozenFailOpen bool      `json:"frozen_fail_open"`
	Message        string    `json:"message"`
}

// NodeFSM manages the state machine for a single RPC node, separating detection from actuation.
type NodeFSM struct {
	config        FSMConfig
	state         NodeState
	suspectCount  int
	recoveryCount int
	haproxy       HAProxyClient
	alerts        []string
	mu            sync.RWMutex
}

// NewNodeFSM creates a new hysteresis state machine controller.
func NewNodeFSM(cfg FSMConfig, haproxy HAProxyClient) *NodeFSM {
	if cfg.LagThreshold == 0 {
		cfg.LagThreshold = 4
	}
	if cfg.SuspectThresholdK <= 0 {
		cfg.SuspectThresholdK = 3
	}
	if cfg.RecoveryThresholdM <= 0 {
		cfg.RecoveryThresholdM = 5
	}
	return &NodeFSM{
		config:        cfg,
		state:         StateHealthy,
		suspectCount:  0,
		recoveryCount: 0,
		haproxy:       haproxy,
		alerts:        make([]string, 0),
	}
}

// State returns the current FSM state.
func (f *NodeFSM) State() NodeState {
	f.mu.RLock()
	defer f.mu.RUnlock()
	return f.state
}

// Counters returns current suspectCount and recoveryCount.
func (f *NodeFSM) Counters() (int, int) {
	f.mu.RLock()
	defer f.mu.RUnlock()
	return f.suspectCount, f.recoveryCount
}

// Alerts returns recorded telemetry alerts.
func (f *NodeFSM) Alerts() []string {
	f.mu.RLock()
	defer f.mu.RUnlock()
	out := make([]string, len(f.alerts))
	copy(out, f.alerts)
	return out
}

func normalizeHash(h string) string {
	clean := strings.ToLower(strings.TrimSpace(h))
	if clean != "" && !strings.HasPrefix(clean, "0x") {
		clean = "0x" + clean
	}
	return clean
}

// canDrain checks the Minimum-Healthy Guardrail:
// If draining would leave zero healthy backends remaining, return false.
func (f *NodeFSM) canDrain() (bool, error) {
	if f.haproxy == nil {
		return true, nil
	}
	count, err := f.haproxy.GetHealthyServerCount(f.config.BackendName)
	if err != nil {
		return false, fmt.Errorf("query healthy server count: %w", err)
	}
	// If count <= 1, draining this server leaves 0 healthy backends remaining!
	if count <= 1 {
		return false, nil
	}
	return true, nil
}

// ProcessTick processes a single evaluation tick given the latest quorum decision and local node sample.
func (f *NodeFSM) ProcessTick(q quorum.QuorumResult, local quorum.ProviderSample) TickResult {
	f.mu.Lock()
	defer f.mu.Unlock()

	res := TickResult{
		PreviousState: f.state,
		CurrentState:  f.state,
		SuspectCount:  f.suspectCount,
		RecoveryCount: f.recoveryCount,
	}

	// 1. Core Principle (Fail Open):
	// If quorum is ambiguous or unavailable, confidence is 0.0,
	// and the engine must freeze routing state rather than initiating drains.
	if q.Confidence <= 0.0 ||
		q.Decision == quorum.DecisionAmbiguous ||
		q.Decision == quorum.DecisionQuorumUnavailable {
		res.FrozenFailOpen = true
		res.Message = "routing state frozen: quorum ambiguous or unavailable (fail open)"
		return res
	}

	// 2. Cryptographic Lineage & Fork Divergence Detection on Local Node
	forkDivergent := false
	localHash := normalizeHash(local.BlockHash)
	canonHash := normalizeHash(q.CanonicalHash)
	canonParent := normalizeHash(q.CanonicalParent)
	localParent := normalizeHash(local.ParentHash)

	if local.Error == nil && localHash != "" && canonHash != "" {
		// Rule A: Equal height divergence
		if local.BlockNumber == q.CanonicalHeight {
			if localHash != canonHash {
				forkDivergent = true
			}
		} else if local.BlockNumber+1 == q.CanonicalHeight && canonParent != "" {
			// Rule B: Local is 1 block behind canonical tip.
			// Canonical parent must match local tip hash.
			if canonParent != localHash {
				forkDivergent = true
			}
		} else if local.BlockNumber == q.CanonicalHeight+1 && localParent != "" {
			// Rule C: Local is 1 block ahead of canonical tip.
			// Local parent must match canonical tip hash.
			if localParent != canonHash {
				forkDivergent = true
			}
		}
	}
	res.ForkDivergent = forkDivergent

	// 3. Lag Calculation
	var lagBlocks uint64
	if q.CanonicalHeight > local.BlockNumber {
		lagBlocks = q.CanonicalHeight - local.BlockNumber
	}
	res.LagBlocks = lagBlocks

	isLagging := (local.Error != nil) || (lagBlocks >= f.config.LagThreshold)

	// Helper to perform drain with Minimum-Healthy Guardrail check
	executeDrain := func(reason string) bool {
		canDrain, err := f.canDrain()
		if err != nil || !canDrain {
			// Minimum-Healthy Guardrail Triggered!
			res.DrainRefused = true
			res.AlertEmitted = AlertMinimumHealthyTriggered
			f.alerts = append(f.alerts, AlertMinimumHealthyTriggered)
			res.Message = fmt.Sprintf("drain refused by minimum-healthy guardrail: preserving traffic (%s)", reason)
			return false
		}

		// Actuate drain in HAProxy
		if f.haproxy != nil {
			_ = f.haproxy.DrainServer(f.config.BackendName, f.config.ServerName)
		}
		res.DrainAction = true
		res.AlertEmitted = AlertNodeDrained
		f.alerts = append(f.alerts, AlertNodeDrained)
		res.Message = fmt.Sprintf("node drained: %s", reason)
		return true
	}

	// 4. Hysteresis State Machine Transitions
	switch f.state {
	case StateHealthy:
		if forkDivergent {
			// Immediate transition to DRAINED on parent-hash fork divergence
			f.alerts = append(f.alerts, AlertForkDivergenceDetected)
			if executeDrain("immediate parent-hash fork divergence") {
				f.state = StateDrained
				f.suspectCount = 0
				f.recoveryCount = 0
			}
		} else if isLagging {
			// Mark SUSPECT on first tick it lags beyond threshold (>= 4 blocks)
			f.state = StateSuspect
			f.suspectCount = 1
			f.recoveryCount = 0
			res.AlertEmitted = AlertNodeLagging
			f.alerts = append(f.alerts, AlertNodeLagging)
			res.Message = fmt.Sprintf("node marked suspect on tick 1 (lag: %d blocks)", lagBlocks)
		} else {
			// Healthy and synced
			f.suspectCount = 0
			f.recoveryCount = 0
			res.Message = "node healthy and synced"
		}

	case StateSuspect:
		if forkDivergent {
			// Immediate transition on fork divergence
			f.alerts = append(f.alerts, AlertForkDivergenceDetected)
			if executeDrain("immediate parent-hash fork divergence while suspect") {
				f.state = StateDrained
				f.suspectCount = 0
				f.recoveryCount = 0
			}
		} else if isLagging {
			f.suspectCount++
			if f.suspectCount >= f.config.SuspectThresholdK {
				// K=3 consecutive suspect ticks reached -> transition to DRAINED
				if executeDrain(fmt.Sprintf("%d consecutive suspect ticks (lag: %d)", f.suspectCount, lagBlocks)) {
					f.state = StateDrained
					f.recoveryCount = 0
				}
			} else {
				res.Message = fmt.Sprintf("node suspect for %d/%d ticks (lag: %d)", f.suspectCount, f.config.SuspectThresholdK, lagBlocks)
			}
		} else {
			// Synced before reaching K=3! Revert to HEALTHY
			f.state = StateHealthy
			f.suspectCount = 0
			f.recoveryCount = 0
			res.Message = "node recovered to healthy prior to drain threshold"
		}

	case StateDrained:
		if !isLagging && !forkDivergent {
			// First synced tick while DRAINED -> transition to RECOVERING
			f.state = StateRecovering
			f.recoveryCount = 1
			f.suspectCount = 0
			res.Message = fmt.Sprintf("node began recovery (1/%d synced ticks)", f.config.RecoveryThresholdM)
		} else {
			// Still lagging or divergent
			f.recoveryCount = 0
			res.Message = "node remains drained"
		}

	case StateRecovering:
		if isLagging || forkDivergent {
			// Fallen back to lag or divergence while recovering -> revert to DRAINED
			f.state = StateDrained
			f.recoveryCount = 0
			res.Message = "recovery aborted: node lagged or diverged during recovery"
		} else {
			f.recoveryCount++
			if f.recoveryCount >= f.config.RecoveryThresholdM {
				// M=5 consecutive synced ticks reached -> transition to HEALTHY & issue ready
				f.state = StateHealthy
				if f.haproxy != nil {
					_ = f.haproxy.ReadyServer(f.config.BackendName, f.config.ServerName)
				}
				res.ReadyAction = true
				res.AlertEmitted = AlertNodeRecovered
				f.alerts = append(f.alerts, AlertNodeRecovered)
				f.recoveryCount = 0
				f.suspectCount = 0
				res.Message = fmt.Sprintf("node recovered to healthy after %d consecutive synced ticks", f.config.RecoveryThresholdM)
			} else {
				res.Message = fmt.Sprintf("node recovering (%d/%d synced ticks)", f.recoveryCount, f.config.RecoveryThresholdM)
			}
		}
	}

	res.CurrentState = f.state
	res.SuspectCount = f.suspectCount
	res.RecoveryCount = f.recoveryCount
	return res
}
