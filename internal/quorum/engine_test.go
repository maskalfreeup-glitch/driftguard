package quorum

import (
	"errors"
	"testing"
	"time"
)

func TestVerifyPairLineage(t *testing.T) {
	lagTol := uint64(2)

	// Equal height, matching hash
	s1 := ProviderSample{BlockNumber: 100, BlockHash: "0xaaa", ParentHash: "0x999"}
	s2 := ProviderSample{BlockNumber: 100, BlockHash: "0xaaa", ParentHash: "0x999"}
	status := VerifyPairLineage(s1, s2, lagTol)
	if !status.Compatible || status.Divergent {
		t.Fatalf("expected compatible and not divergent, got: %+v", status)
	}

	// Equal height, conflicting hash -> Fork Divergence
	s3 := ProviderSample{BlockNumber: 100, BlockHash: "0xbbb", ParentHash: "0x999"}
	status = VerifyPairLineage(s1, s3, lagTol)
	if status.Compatible || !status.Divergent {
		t.Fatalf("expected fork divergence for same height different hash, got: %+v", status)
	}

	// Delta=1, parent hash matches lower block hash
	sLow := ProviderSample{BlockNumber: 100, BlockHash: "0xparent", ParentHash: "0xgrandparent"}
	sHigh := ProviderSample{BlockNumber: 101, BlockHash: "0xchild", ParentHash: "0xparent"}
	status = VerifyPairLineage(sLow, sHigh, lagTol)
	if !status.Compatible || status.Divergent {
		t.Fatalf("expected compatible for valid delta=1 parent linkage, got: %+v", status)
	}

	// Delta=1, parent hash does NOT match lower block hash -> Fork Divergence
	sHighBadParent := ProviderSample{BlockNumber: 101, BlockHash: "0xchild", ParentHash: "0xwrongparent"}
	status = VerifyPairLineage(sLow, sHighBadParent, lagTol)
	if status.Compatible || !status.Divergent {
		t.Fatalf("expected fork divergence for bad delta=1 parent linkage, got: %+v", status)
	}

	// Delta=2, within lag tolerance (2 <= 2)
	sHighDelta2 := ProviderSample{BlockNumber: 102, BlockHash: "0xdelta2", ParentHash: "0xdelta1"}
	status = VerifyPairLineage(sLow, sHighDelta2, lagTol)
	if !status.Compatible || status.Divergent {
		t.Fatalf("expected compatible for delta 2 within tolerance 2, got: %+v", status)
	}

	// Delta=3, exceeds lag tolerance (3 > 2)
	sHighDelta3 := ProviderSample{BlockNumber: 103, BlockHash: "0xdelta3", ParentHash: "0xdelta2"}
	status = VerifyPairLineage(sLow, sHighDelta3, lagTol)
	if status.Compatible || status.Divergent {
		t.Fatalf("expected incompatible (lag) but not divergent, got: %+v", status)
	}
}

func TestStrongConsensus(t *testing.T) {
	engine := NewEngine(2, nil)

	samples := []ProviderSample{
		{ProviderID: "p1", BlockNumber: 1000, BlockHash: "0xhash1000", ParentHash: "0xhash999"},
		{ProviderID: "p2", BlockNumber: 1000, BlockHash: "0xhash1000", ParentHash: "0xhash999"},
		{ProviderID: "p3", BlockNumber: 1000, BlockHash: "0xhash1000", ParentHash: "0xhash999"},
	}

	result := engine.Evaluate(samples)
	if result.Decision != DecisionStrongConsensus {
		t.Fatalf("expected DecisionStrongConsensus, got %s", result.Decision)
	}
	if result.Confidence != 1.0 {
		t.Fatalf("expected confidence 1.0, got %f", result.Confidence)
	}
	if result.CanonicalHeight != 1000 {
		t.Fatalf("expected canonical height 1000, got %d", result.CanonicalHeight)
	}
	if result.CanonicalHash != "0xhash1000" {
		t.Fatalf("expected canonical hash 0xhash1000, got %s", result.CanonicalHash)
	}
	if len(result.AgreedProviders) != 3 {
		t.Fatalf("expected 3 agreed providers, got %d", len(result.AgreedProviders))
	}
}

func TestStrongConsensusDelta1(t *testing.T) {
	engine := NewEngine(2, nil)

	samples := []ProviderSample{
		{ProviderID: "p1", BlockNumber: 100, BlockHash: "0xhash100", ParentHash: "0xhash99"},
		{ProviderID: "p2", BlockNumber: 101, BlockHash: "0xhash101", ParentHash: "0xhash100"},
		{ProviderID: "p3", BlockNumber: 101, BlockHash: "0xhash101", ParentHash: "0xhash100"},
	}

	result := engine.Evaluate(samples)
	if result.Decision != DecisionStrongConsensus {
		t.Fatalf("expected DecisionStrongConsensus, got %s", result.Decision)
	}
	if result.Confidence != 1.0 {
		t.Fatalf("expected confidence 1.0, got %f", result.Confidence)
	}
	if result.CanonicalHeight != 101 {
		t.Fatalf("expected canonical height 101, got %d", result.CanonicalHeight)
	}
}

func TestMajorityConsensusWithLaggingOutlier(t *testing.T) {
	engine := NewEngine(2, nil)

	// p1 and p2 agree at 1000. p3 is lagging at 990 (10 blocks behind)
	samples := []ProviderSample{
		{ProviderID: "p1", BlockNumber: 1000, BlockHash: "0xhash1000", ParentHash: "0xhash999"},
		{ProviderID: "p2", BlockNumber: 1000, BlockHash: "0xhash1000", ParentHash: "0xhash999"},
		{ProviderID: "p3", BlockNumber: 990, BlockHash: "0xhash990", ParentHash: "0xhash989"},
	}

	result := engine.Evaluate(samples)
	if result.Decision != DecisionMajorityConsensus {
		t.Fatalf("expected DecisionMajorityConsensus, got %s", result.Decision)
	}
	if result.Confidence < 0.6 {
		t.Fatalf("expected majority confidence >= 0.6, got %f", result.Confidence)
	}
	if result.CanonicalHeight != 1000 {
		t.Fatalf("expected canonical height 1000, got %d", result.CanonicalHeight)
	}
	if result.OutlierProvider != "p3" {
		t.Fatalf("expected outlier p3, got %s", result.OutlierProvider)
	}
	if len(result.AgreedProviders) != 2 {
		t.Fatalf("expected 2 agreed providers, got %d", len(result.AgreedProviders))
	}
}

func TestMajorityConsensusWithTimeoutOutlier(t *testing.T) {
	engine := NewEngine(2, nil)

	// p3 has error / timeout
	samples := []ProviderSample{
		{ProviderID: "p1", BlockNumber: 1000, BlockHash: "0xhash1000", ParentHash: "0xhash999"},
		{ProviderID: "p2", BlockNumber: 1000, BlockHash: "0xhash1000", ParentHash: "0xhash999"},
		{ProviderID: "p3", Error: errors.New("connection timeout"), Latency: 2 * time.Second},
	}

	result := engine.Evaluate(samples)
	if result.Decision != DecisionMajorityConsensus {
		t.Fatalf("expected DecisionMajorityConsensus, got %s", result.Decision)
	}
	if result.Confidence < 0.6 {
		t.Fatalf("expected confidence >= 0.6, got %f", result.Confidence)
	}
	if result.CanonicalHeight != 1000 {
		t.Fatalf("expected canonical height 1000, got %d", result.CanonicalHeight)
	}
	if result.OutlierProvider != "p3" {
		t.Fatalf("expected outlier p3, got %s", result.OutlierProvider)
	}
}

func TestMajorityConsensusWithDivergentOutlier(t *testing.T) {
	engine := NewEngine(2, nil)

	// p1 and p2 agree at 1000. p3 is on a divergent fork at 1000 with a different hash
	samples := []ProviderSample{
		{ProviderID: "p1", BlockNumber: 1000, BlockHash: "0xcanonical", ParentHash: "0xparent"},
		{ProviderID: "p2", BlockNumber: 1000, BlockHash: "0xcanonical", ParentHash: "0xparent"},
		{ProviderID: "p3", BlockNumber: 1000, BlockHash: "0xdivergent", ParentHash: "0xotherparent"},
	}

	result := engine.Evaluate(samples)
	if result.Decision != DecisionMajorityConsensus {
		t.Fatalf("expected DecisionMajorityConsensus, got %s", result.Decision)
	}
	if result.OutlierProvider != "p3" {
		t.Fatalf("expected outlier p3, got %s", result.OutlierProvider)
	}
	if result.CanonicalHash != "0xcanonical" {
		t.Fatalf("expected canonical hash 0xcanonical, got %s", result.CanonicalHash)
	}
}

func TestAmbiguousForkDivergence(t *testing.T) {
	engine := NewEngine(2, nil)

	// 3 providers all report different hashes at same height
	samples := []ProviderSample{
		{ProviderID: "p1", BlockNumber: 1000, BlockHash: "0xhashA", ParentHash: "0xparent"},
		{ProviderID: "p2", BlockNumber: 1000, BlockHash: "0xhashB", ParentHash: "0xparent"},
		{ProviderID: "p3", BlockNumber: 1000, BlockHash: "0xhashC", ParentHash: "0xparent"},
	}

	result := engine.Evaluate(samples)
	if result.Decision != DecisionForkDivergence && result.Decision != DecisionAmbiguous {
		t.Fatalf("expected DecisionForkDivergence or DecisionAmbiguous, got %s", result.Decision)
	}
	if result.Confidence != 0.0 {
		t.Fatalf("fail-open core principle: expected confidence 0.0, got %f", result.Confidence)
	}
}

func TestAmbiguousTwoRespondingDisagreed(t *testing.T) {
	engine := NewEngine(2, nil)

	// 2 providers respond with different hashes at same height, 1 timed out
	samples := []ProviderSample{
		{ProviderID: "p1", BlockNumber: 1000, BlockHash: "0xhashA", ParentHash: "0xparent"},
		{ProviderID: "p2", BlockNumber: 1000, BlockHash: "0xhashB", ParentHash: "0xparent"},
		{ProviderID: "p3", Error: errors.New("timeout")},
	}

	result := engine.Evaluate(samples)
	if result.Decision != DecisionForkDivergence && result.Decision != DecisionAmbiguous {
		t.Fatalf("expected fork divergence or ambiguous, got %s", result.Decision)
	}
	if result.Confidence != 0.0 {
		t.Fatalf("expected confidence 0.0, got %f", result.Confidence)
	}
}

func TestQuorumUnavailable(t *testing.T) {
	engine := NewEngine(2, nil)

	// 2 providers timed out, only 1 responds
	samples := []ProviderSample{
		{ProviderID: "p1", BlockNumber: 1000, BlockHash: "0xhash1000", ParentHash: "0xparent"},
		{ProviderID: "p2", Error: errors.New("timeout")},
		{ProviderID: "p3", Error: errors.New("timeout")},
	}

	result := engine.Evaluate(samples)
	if result.Decision != DecisionQuorumUnavailable {
		t.Fatalf("expected DecisionQuorumUnavailable, got %s", result.Decision)
	}
	if result.Confidence != 0.0 {
		t.Fatalf("fail-open core principle: expected confidence 0.0, got %f", result.Confidence)
	}
}
