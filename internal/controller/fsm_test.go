package controller

import (
	"testing"

	"driftguard/internal/quorum"
)

func validQuorum(height uint64, hash, parent string) quorum.QuorumResult {
	return quorum.QuorumResult{
		Decision:        quorum.DecisionStrongConsensus,
		Confidence:      1.0,
		CanonicalHeight: height,
		CanonicalHash:   hash,
		CanonicalParent: parent,
	}
}

func TestFSM_HealthyToSuspectToDrained(t *testing.T) {
	mockHP := NewMockHAProxy()
	cfg := DefaultFSMConfig("be_nitro", "local")
	fsm := NewNodeFSM(cfg, mockHP)

	// Step 0: Initially Healthy & Synced
	q := validQuorum(100, "0x100", "0x99")
	local := quorum.ProviderSample{BlockNumber: 100, BlockHash: "0x100", ParentHash: "0x99"}
	res := fsm.ProcessTick(q, local)
	if res.CurrentState != StateHealthy || res.DrainAction {
		t.Fatalf("expected HEALTHY with no drain, got %s", res.CurrentState)
	}

	// Step 1: Tick 1 of lag (lag = 4 blocks: canonical=104, local=100)
	q = validQuorum(104, "0x104", "0x103")
	res = fsm.ProcessTick(q, local)
	if res.CurrentState != StateSuspect {
		t.Fatalf("expected SUSPECT on tick 1 of lag >= 4, got %s", res.CurrentState)
	}
	if res.SuspectCount != 1 {
		t.Fatalf("expected suspectCount 1, got %d", res.SuspectCount)
	}
	if res.DrainAction {
		t.Fatalf("unexpected drain on tick 1")
	}

	// Step 2: Tick 2 of lag
	q = validQuorum(105, "0x105", "0x104")
	res = fsm.ProcessTick(q, local)
	if res.CurrentState != StateSuspect {
		t.Fatalf("expected SUSPECT on tick 2, got %s", res.CurrentState)
	}
	if res.SuspectCount != 2 {
		t.Fatalf("expected suspectCount 2, got %d", res.SuspectCount)
	}
	if res.DrainAction {
		t.Fatalf("unexpected drain on tick 2")
	}

	// Step 3: Tick 3 of lag (K=3) -> must transition to DRAINED and actuate HAProxy drain
	q = validQuorum(106, "0x106", "0x105")
	res = fsm.ProcessTick(q, local)
	if res.CurrentState != StateDrained {
		t.Fatalf("expected DRAINED on tick 3 (K=3), got %s", res.CurrentState)
	}
	if !res.DrainAction {
		t.Fatalf("expected DrainAction to be true on tick 3")
	}
	st, _ := mockHP.GetServerState("be_nitro", "local")
	if st != "DRAIN" {
		t.Fatalf("expected HAProxy server state DRAIN, got %s", st)
	}
}

func TestFSM_TransientLagRecoversBeforeK(t *testing.T) {
	mockHP := NewMockHAProxy()
	cfg := DefaultFSMConfig("be_nitro", "local")
	fsm := NewNodeFSM(cfg, mockHP)

	// Tick 1: lag >= 4 -> SUSPECT
	q := validQuorum(104, "0x104", "0x103")
	local := quorum.ProviderSample{BlockNumber: 100, BlockHash: "0x100"}
	res := fsm.ProcessTick(q, local)
	if res.CurrentState != StateSuspect {
		t.Fatalf("expected SUSPECT, got %s", res.CurrentState)
	}

	// Tick 2: node catches up to 104 -> reverts to HEALTHY without draining!
	local = quorum.ProviderSample{BlockNumber: 104, BlockHash: "0x104"}
	res = fsm.ProcessTick(q, local)
	if res.CurrentState != StateHealthy {
		t.Fatalf("expected revert to HEALTHY, got %s", res.CurrentState)
	}
	if res.SuspectCount != 0 {
		t.Fatalf("expected suspectCount reset to 0, got %d", res.SuspectCount)
	}
	if res.DrainAction {
		t.Fatalf("unexpected drain on recovered node")
	}
}

func TestFSM_RecoveryHysteresisM5(t *testing.T) {
	mockHP := NewMockHAProxy()
	cfg := DefaultFSMConfig("be_nitro", "local")
	fsm := NewNodeFSM(cfg, mockHP)

	// Drive into DRAINED
	localLagging := quorum.ProviderSample{BlockNumber: 100, BlockHash: "0x100"}
	for i := 1; i <= 3; i++ {
		q := validQuorum(uint64(104+i), "0xcanon", "0xparent")
		fsm.ProcessTick(q, localLagging)
	}
	if fsm.State() != StateDrained {
		t.Fatalf("expected DRAINED state, got %s", fsm.State())
	}

	// Now node catches up.
	// Tick 1: transitions to RECOVERING (count=1)
	q := validQuorum(110, "0x110", "0x109")
	localSynced := quorum.ProviderSample{BlockNumber: 110, BlockHash: "0x110"}
	res := fsm.ProcessTick(q, localSynced)
	if res.CurrentState != StateRecovering || res.RecoveryCount != 1 {
		t.Fatalf("expected RECOVERING with count 1, got %s (%d)", res.CurrentState, res.RecoveryCount)
	}
	if res.ReadyAction {
		t.Fatalf("unexpected ready action on tick 1 of recovery")
	}

	// Ticks 2, 3, 4 of recovery: should stay RECOVERING
	for expectedCount := 2; expectedCount <= 4; expectedCount++ {
		h := uint64(110 + expectedCount)
		q = validQuorum(h, "0xhash", "0xprev")
		localSynced = quorum.ProviderSample{BlockNumber: h, BlockHash: "0xhash"}
		res = fsm.ProcessTick(q, localSynced)
		if res.CurrentState != StateRecovering || res.RecoveryCount != expectedCount {
			t.Fatalf("expected RECOVERING with count %d, got %s (%d)", expectedCount, res.CurrentState, res.RecoveryCount)
		}
		if res.ReadyAction {
			t.Fatalf("unexpected ready action before M=5")
		}
	}

	// Tick 5 of recovery (M=5): must transition to HEALTHY and issue ready command!
	q = validQuorum(115, "0x115", "0x114")
	localSynced = quorum.ProviderSample{BlockNumber: 115, BlockHash: "0x115"}
	res = fsm.ProcessTick(q, localSynced)
	if res.CurrentState != StateHealthy {
		t.Fatalf("expected HEALTHY after 5 recovery ticks, got %s", res.CurrentState)
	}
	if !res.ReadyAction {
		t.Fatalf("expected ReadyAction to be true on M=5")
	}
	st, _ := mockHP.GetServerState("be_nitro", "local")
	if st != "READY" {
		t.Fatalf("expected HAProxy server state READY, got %s", st)
	}
}

func TestFSM_RecoveryAbortedIfNodeLagsAgain(t *testing.T) {
	mockHP := NewMockHAProxy()
	cfg := DefaultFSMConfig("be_nitro", "local")
	fsm := NewNodeFSM(cfg, mockHP)

	// Drive to DRAINED
	for i := 1; i <= 3; i++ {
		q := validQuorum(uint64(104+i), "0xcanon", "0xparent")
		fsm.ProcessTick(q, quorum.ProviderSample{BlockNumber: 100, BlockHash: "0x100"})
	}

	// 2 synced ticks -> RECOVERING (count=2)
	q := validQuorum(110, "0x110", "0x109")
	fsm.ProcessTick(q, quorum.ProviderSample{BlockNumber: 110, BlockHash: "0x110"})
	fsm.ProcessTick(q, quorum.ProviderSample{BlockNumber: 110, BlockHash: "0x110"})
	if fsm.State() != StateRecovering {
		t.Fatalf("expected RECOVERING, got %s", fsm.State())
	}

	// Node lags again: should drop back to DRAINED and reset recovery count to 0
	q = validQuorum(120, "0x120", "0x119")
	res := fsm.ProcessTick(q, quorum.ProviderSample{BlockNumber: 110, BlockHash: "0x110"})
	if res.CurrentState != StateDrained {
		t.Fatalf("expected fallback to DRAINED, got %s", res.CurrentState)
	}
	if res.RecoveryCount != 0 {
		t.Fatalf("expected recovery count reset to 0, got %d", res.RecoveryCount)
	}
}

func TestFSM_ImmediateDrainOnForkDivergence(t *testing.T) {
	mockHP := NewMockHAProxy()
	cfg := DefaultFSMConfig("be_nitro", "local")
	fsm := NewNodeFSM(cfg, mockHP)

	// Local node is at height 1000, but block hash diverges from canonical quorum hash!
	q := validQuorum(1000, "0xcanonical_hash", "0xparent")
	localDivergent := quorum.ProviderSample{BlockNumber: 1000, BlockHash: "0xdivergent_hash", ParentHash: "0xparent"}

	res := fsm.ProcessTick(q, localDivergent)
	if !res.ForkDivergent {
		t.Fatalf("expected fork divergence detected")
	}
	// Immediate transition to DRAINED on tick 1!
	if res.CurrentState != StateDrained {
		t.Fatalf("expected immediate transition to DRAINED on fork divergence, got %s", res.CurrentState)
	}
	if !res.DrainAction {
		t.Fatalf("expected immediate DrainAction on fork divergence")
	}
	st, _ := mockHP.GetServerState("be_nitro", "local")
	if st != "DRAIN" {
		t.Fatalf("expected server state DRAIN, got %s", st)
	}
}

func TestFSM_MinimumHealthyGuardrail(t *testing.T) {
	mockHP := NewMockHAProxy()
	// Set healthy count to 1: draining local would leave 0 healthy backends!
	mockHP.SetHealthyServerCount("be_nitro", 1)

	cfg := DefaultFSMConfig("be_nitro", "local")
	fsm := NewNodeFSM(cfg, mockHP)

	// Drive with 3 lag ticks
	var res TickResult
	for i := 1; i <= 3; i++ {
		q := validQuorum(uint64(104+i), "0xcanon", "0xparent")
		res = fsm.ProcessTick(q, quorum.ProviderSample{BlockNumber: 100, BlockHash: "0x100"})
	}

	// On 3rd tick, drain MUST BE REFUSED by Minimum-Healthy Guardrail
	if !res.DrainRefused {
		t.Fatalf("expected DrainRefused to be true when healthyCount <= 1")
	}
	if res.DrainAction {
		t.Fatalf("drain action must NOT be executed when guardrail triggered")
	}
	if res.AlertEmitted != AlertMinimumHealthyTriggered {
		t.Fatalf("expected alert MINIMUM_HEALTHY_TRIGGERED, got %s", res.AlertEmitted)
	}

	// Traffic routing preserved on existing backend (not DRAIN in HAProxy)
	st, _ := mockHP.GetServerState("be_nitro", "local")
	if st == "DRAIN" {
		t.Fatalf("traffic routing was violated: server was drained despite guardrail")
	}
}

func TestFSM_FailOpenRoutingFreeze(t *testing.T) {
	mockHP := NewMockHAProxy()
	cfg := DefaultFSMConfig("be_nitro", "local")
	fsm := NewNodeFSM(cfg, mockHP)

	// Quorum is ambiguous with 0 confidence
	ambiguousQuorum := quorum.QuorumResult{
		Decision:   quorum.DecisionAmbiguous,
		Confidence: 0.0,
		Details:    "split vote",
	}

	local := quorum.ProviderSample{BlockNumber: 10, BlockHash: "0xold"}
	res := fsm.ProcessTick(ambiguousQuorum, local)

	if !res.FrozenFailOpen {
		t.Fatalf("expected FrozenFailOpen to be true")
	}
	if res.CurrentState != StateHealthy {
		t.Fatalf("state must remain unchanged on fail-open freeze, got %s", res.CurrentState)
	}
	if res.DrainAction {
		t.Fatalf("unexpected drain on frozen fail open")
	}
}

func TestFSM_OutlierReferenceDoesNotDrainLocal(t *testing.T) {
	mockHP := NewMockHAProxy()
	cfg := DefaultFSMConfig("be_nitro", "local")
	fsm := NewNodeFSM(cfg, mockHP)

	// Majority consensus where outlier provider is lagging, but canonical tip is 1000
	quorumWithOutlier := quorum.QuorumResult{
		Decision:        quorum.DecisionMajorityConsensus,
		Confidence:      2.0 / 3.0,
		CanonicalHeight: 1000,
		CanonicalHash:   "0xcanon1000",
		OutlierProvider: "ref-rpc-c",
	}

	// Local node is synced with canonical tip (1000)
	local := quorum.ProviderSample{BlockNumber: 1000, BlockHash: "0xcanon1000"}

	// Tick multiple times: local node must remain HEALTHY
	for i := 0; i < 5; i++ {
		res := fsm.ProcessTick(quorumWithOutlier, local)
		if res.CurrentState != StateHealthy {
			t.Fatalf("local healthy node was incorrectly drained due to outlier reference: state=%s", res.CurrentState)
		}
		if res.DrainAction {
			t.Fatalf("unexpected drain action on local healthy node")
		}
	}
}
