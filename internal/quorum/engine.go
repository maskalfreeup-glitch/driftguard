package quorum

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"strconv"
	"strings"
	"sync"
	"time"
)

// DecisionType represents the quorum consensus classification.
type DecisionType string

const (
	// StrongConsensus: All 3 providers agree on hash lineage within lagTolerance.
	DecisionStrongConsensus DecisionType = "DecisionStrongConsensus"
	// MajorityConsensus: 2 providers agree; 1 provider is lagging, timing out, or invalid.
	DecisionMajorityConsensus DecisionType = "DecisionMajorityConsensus"
	// Ambiguous: 2 providers disagree on hash, or 3 report different chains.
	DecisionAmbiguous DecisionType = "DecisionAmbiguous"
	// ForkDivergence: Providers at the same height have conflicting block hashes or parent-hash linkage fails.
	DecisionForkDivergence DecisionType = "DecisionForkDivergence"
	// QuorumUnavailable: Fewer than 2 providers respond.
	DecisionQuorumUnavailable DecisionType = "DecisionQuorumUnavailable"
)

// ProviderSample represents the state collected from an RPC provider at a given instant.
type ProviderSample struct {
	ProviderID  string        `json:"provider_id"`
	ChainID     string        `json:"chain_id"`
	BlockNumber uint64        `json:"block_number"`
	BlockHash   string        `json:"block_hash"`
	ParentHash  string        `json:"parent_hash"`
	Latency     time.Duration `json:"latency_ns"`
	Timestamp   time.Time     `json:"timestamp"`
	Error       error         `json:"error,omitempty"`
}

// QuorumResult represents the evaluated consensus decision.
type QuorumResult struct {
	Decision        DecisionType     `json:"decision"`
	Confidence      float64          `json:"confidence"`
	CanonicalHeight uint64           `json:"canonical_height"`
	CanonicalHash   string           `json:"canonical_hash"`
	CanonicalParent string           `json:"canonical_parent,omitempty"`
	OutlierProvider string           `json:"outlier_provider,omitempty"`
	AgreedProviders []string         `json:"agreed_providers"`
	Samples         []ProviderSample `json:"samples"`
	Details         string           `json:"details,omitempty"`
}

// LineageStatus holds the comparison result between two providers.
type LineageStatus struct {
	Compatible bool
	Divergent  bool
	Reason     string
}

// Collector collects RPC block data from multiple providers.
type Collector struct {
	Endpoints  []string
	HTTPClient *http.Client
	Timeout    time.Duration
}

// NewCollector creates a new RPC collector.
func NewCollector(endpoints []string, timeout time.Duration) *Collector {
	if timeout <= 0 {
		timeout = 2 * time.Second
	}
	return &Collector{
		Endpoints: endpoints,
		HTTPClient: &http.Client{
			Timeout: timeout,
		},
		Timeout: timeout,
	}
}

type jsonRPCRequest struct {
	JSONRPC string        `json:"jsonrpc"`
	Method  string        `json:"method"`
	Params  []interface{} `json:"params"`
	ID      int           `json:"id"`
}

type jsonRPCResponse struct {
	JSONRPC string          `json:"jsonrpc"`
	ID      int             `json:"id"`
	Result  json.RawMessage `json:"result,omitempty"`
	Error   *struct {
		Code    int    `json:"code"`
		Message string `json:"message"`
	} `json:"error,omitempty"`
}

type blockRPCResult struct {
	Number     string `json:"number"`
	Hash       string `json:"hash"`
	ParentHash string `json:"parentHash"`
}

func parseHexUint64(hexStr string) (uint64, error) {
	clean := strings.TrimPrefix(strings.TrimSpace(hexStr), "0x")
	if clean == "" {
		return 0, fmt.Errorf("empty hex string")
	}
	return strconv.ParseUint(clean, 16, 64)
}

func normalizeHash(h string) string {
	clean := strings.ToLower(strings.TrimSpace(h))
	if clean != "" && !strings.HasPrefix(clean, "0x") {
		clean = "0x" + clean
	}
	return clean
}

// FetchSingleProvider queries an RPC provider for ChainID, latest block height, block hash, and parent hash.
func (c *Collector) FetchSingleProvider(ctx context.Context, endpoint string) ProviderSample {
	sample := ProviderSample{
		ProviderID: endpoint,
		Timestamp:  time.Now(),
	}

	start := time.Now()
	chainID, err := c.queryRPCString(ctx, endpoint, "eth_chainId", nil)
	if err != nil {
		sample.Latency = time.Since(start)
		sample.Error = fmt.Errorf("eth_chainId failed: %w", err)
		return sample
	}
	sample.ChainID = chainID

	blockData, err := c.queryRPCBlock(ctx, endpoint, "eth_getBlockByNumber", []interface{}{"latest", false})
	sample.Latency = time.Since(start)
	if err != nil {
		sample.Error = fmt.Errorf("eth_getBlockByNumber failed: %w", err)
		return sample
	}

	blockNum, err := parseHexUint64(blockData.Number)
	if err != nil {
		sample.Error = fmt.Errorf("invalid block number %q: %w", blockData.Number, err)
		return sample
	}

	sample.BlockNumber = blockNum
	sample.BlockHash = normalizeHash(blockData.Hash)
	sample.ParentHash = normalizeHash(blockData.ParentHash)
	return sample
}

func (c *Collector) queryRPCString(ctx context.Context, endpoint, method string, params []interface{}) (string, error) {
	if params == nil {
		params = []interface{}{}
	}
	reqBody, err := json.Marshal(jsonRPCRequest{
		JSONRPC: "2.0",
		Method:  method,
		Params:  params,
		ID:      1,
	})
	if err != nil {
		return "", err
	}

	req, err := http.NewRequestWithContext(ctx, http.MethodPost, endpoint, bytes.NewReader(reqBody))
	if err != nil {
		return "", err
	}
	req.Header.Set("Content-Type", "application/json")

	resp, err := c.HTTPClient.Do(req)
	if err != nil {
		return "", err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		return "", fmt.Errorf("http %d: %s", resp.StatusCode, string(body))
	}

	var rpcResp jsonRPCResponse
	if err := json.NewDecoder(resp.Body).Decode(&rpcResp); err != nil {
		return "", err
	}
	if rpcResp.Error != nil {
		return "", fmt.Errorf("rpc error %d: %s", rpcResp.Error.Code, rpcResp.Error.Message)
	}

	var strRes string
	if err := json.Unmarshal(rpcResp.Result, &strRes); err != nil {
		return "", err
	}
	return strRes, nil
}

func (c *Collector) queryRPCBlock(ctx context.Context, endpoint, method string, params []interface{}) (*blockRPCResult, error) {
	reqBody, err := json.Marshal(jsonRPCRequest{
		JSONRPC: "2.0",
		Method:  method,
		Params:  params,
		ID:      2,
	})
	if err != nil {
		return nil, err
	}

	req, err := http.NewRequestWithContext(ctx, http.MethodPost, endpoint, bytes.NewReader(reqBody))
	if err != nil {
		return nil, err
	}
	req.Header.Set("Content-Type", "application/json")

	resp, err := c.HTTPClient.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("http %d: %s", resp.StatusCode, string(body))
	}

	var rpcResp jsonRPCResponse
	if err := json.NewDecoder(resp.Body).Decode(&rpcResp); err != nil {
		return nil, err
	}
	if rpcResp.Error != nil {
		return nil, fmt.Errorf("rpc error %d: %s", rpcResp.Error.Code, rpcResp.Error.Message)
	}

	var block blockRPCResult
	if err := json.Unmarshal(rpcResp.Result, &block); err != nil {
		return nil, err
	}
	return &block, nil
}

// Collect queries all configured endpoints concurrently.
func (c *Collector) Collect(ctx context.Context) []ProviderSample {
	samples := make([]ProviderSample, len(c.Endpoints))
	var wg sync.WaitGroup
	for i, ep := range c.Endpoints {
		wg.Add(1)
		go func(idx int, endpoint string) {
			defer wg.Done()
			samples[idx] = c.FetchSingleProvider(ctx, endpoint)
		}(i, ep)
	}
	wg.Wait()
	return samples
}

// Engine implements multi-provider quorum consensus and cryptographic lineage verification.
type Engine struct {
	LagTolerance uint64
	Collector    *Collector
}

// NewEngine creates a new quorum Engine.
func NewEngine(lagTolerance uint64, collector *Collector) *Engine {
	if lagTolerance == 0 {
		lagTolerance = 2
	}
	return &Engine{
		LagTolerance: lagTolerance,
		Collector:    collector,
	}
}

// VerifyPairLineage verifies cryptographic lineage between two provider samples.
// Rules:
// 1. Equal height: BlockHash must be identical. If different -> Fork Divergence.
// 2. Delta is 1 block: block(h).ParentHash == block(h-1).BlockHash. If not -> Fork Divergence.
// 3. Delta <= lagTolerance: within tolerance. If delta > lagTolerance: out of tolerance.
func VerifyPairLineage(a, b ProviderSample, lagTolerance uint64) LineageStatus {
	if a.Error != nil || b.Error != nil {
		return LineageStatus{Compatible: false, Divergent: false, Reason: "provider error"}
	}

	hA := a.BlockNumber
	hB := b.BlockNumber

	hashA := normalizeHash(a.BlockHash)
	hashB := normalizeHash(b.BlockHash)

	parentA := normalizeHash(a.ParentHash)
	parentB := normalizeHash(b.ParentHash)

	// Equal height verification
	if hA == hB {
		if hashA == hashB {
			return LineageStatus{Compatible: true, Divergent: false, Reason: "equal height hashes match"}
		}
		return LineageStatus{
			Compatible: false,
			Divergent:  true,
			Reason:     fmt.Sprintf("fork divergence at height %d: %s != %s", hA, hashA, hashB),
		}
	}

	// Order by height so higher is high, lower is low
	high, low := a, b
	highHash, lowHash := hashA, hashB
	highParent := parentA
	if hB > hA {
		high, low = b, a
		highHash, lowHash = hashB, hashA
		highParent = parentB
	}
	_ = highHash

	delta := high.BlockNumber - low.BlockNumber

	// Delta == 1 verification: block(h).ParentHash == block(h-1).BlockHash
	if delta == 1 {
		if highParent == lowHash {
			return LineageStatus{Compatible: true, Divergent: false, Reason: "delta=1 parent hash matches lower block hash"}
		}
		return LineageStatus{
			Compatible: false,
			Divergent:  true,
			Reason:     fmt.Sprintf("fork divergence across delta=1: block(%d).ParentHash(%s) != block(%d).BlockHash(%s)", high.BlockNumber, highParent, low.BlockNumber, lowHash),
		}
	}

	// Delta within lag tolerance
	if delta <= lagTolerance {
		return LineageStatus{Compatible: true, Divergent: false, Reason: fmt.Sprintf("delta %d within tolerance %d", delta, lagTolerance)}
	}

	return LineageStatus{
		Compatible: false,
		Divergent:  false,
		Reason:     fmt.Sprintf("delta %d exceeds lag tolerance %d", delta, lagTolerance),
	}
}

// Evaluate analyzes samples collected from N independent providers (nominally N=3)
// and returns the consensus decision according to the 2/3 consensus rules.
func (e *Engine) Evaluate(samples []ProviderSample) QuorumResult {
	result := QuorumResult{
		Samples: samples,
	}

	// Separate valid responsive samples from errors
	var valid []ProviderSample
	var errored []ProviderSample
	for _, s := range samples {
		if s.Error == nil && s.BlockHash != "" {
			valid = append(valid, s)
		} else {
			errored = append(errored, s)
		}
	}

	// Rule 4: Quorum Unavailable: Fewer than 2 providers respond -> Confidence 0.0
	if len(valid) < 2 {
		result.Decision = DecisionQuorumUnavailable
		result.Confidence = 0.0
		result.Details = fmt.Sprintf("insufficient responsive providers: %d valid out of %d total", len(valid), len(samples))
		return result
	}

	// Handle len(valid) == 2 (1 provider timed out / errored or only 2 configured)
	if len(valid) == 2 {
		p0, p1 := valid[0], valid[1]
		status := VerifyPairLineage(p0, p1, e.LagTolerance)

		if status.Divergent {
			result.Decision = DecisionForkDivergence
			result.Confidence = 0.0
			result.Details = status.Reason
			return result
		}

		if !status.Compatible {
			// Lag delta exceeded tolerance between the only 2 responding providers
			result.Decision = DecisionAmbiguous
			result.Confidence = 0.0
			result.Details = status.Reason
			return result
		}

		// The 2 responsive providers agree!
		var outlierID string
		if len(errored) > 0 {
			outlierID = errored[0].ProviderID
		}
		canonical := p0
		if p1.BlockNumber > p0.BlockNumber {
			canonical = p1
		}

		result.Decision = DecisionMajorityConsensus
		result.Confidence = 2.0 / 3.0
		result.CanonicalHeight = canonical.BlockNumber
		result.CanonicalHash = normalizeHash(canonical.BlockHash)
		result.CanonicalParent = normalizeHash(canonical.ParentHash)
		result.OutlierProvider = outlierID
		result.AgreedProviders = []string{p0.ProviderID, p1.ProviderID}
		result.Details = fmt.Sprintf("2/3 majority consensus reached (outlier: %s)", outlierID)
		return result
	}

	// len(valid) >= 3 (standard N=3 providers all responsive)
	p0, p1, p2 := valid[0], valid[1], valid[2]
	s01 := VerifyPairLineage(p0, p1, e.LagTolerance)
	s12 := VerifyPairLineage(p1, p2, e.LagTolerance)
	s02 := VerifyPairLineage(p0, p2, e.LagTolerance)

	// Check if all 3 form Strong Consensus
	minHeight := min(p0.BlockNumber, min(p1.BlockNumber, p2.BlockNumber))
	maxHeight := max(p0.BlockNumber, max(p1.BlockNumber, p2.BlockNumber))
	spanWithinTol := (maxHeight - minHeight) <= e.LagTolerance

	allCompatible := s01.Compatible && s12.Compatible && s02.Compatible && spanWithinTol
	anyDivergent := s01.Divergent || s12.Divergent || s02.Divergent

	if allCompatible && !anyDivergent {
		// Strong Consensus: All 3 providers agree on hash lineage within lagTolerance
		canonical := p0
		if p1.BlockNumber > canonical.BlockNumber {
			canonical = p1
		}
		if p2.BlockNumber > canonical.BlockNumber {
			canonical = p2
		}

		result.Decision = DecisionStrongConsensus
		result.Confidence = 1.0
		result.CanonicalHeight = canonical.BlockNumber
		result.CanonicalHash = normalizeHash(canonical.BlockHash)
		result.CanonicalParent = normalizeHash(canonical.ParentHash)
		result.AgreedProviders = []string{p0.ProviderID, p1.ProviderID, p2.ProviderID}
		result.Details = fmt.Sprintf("strong 3/3 consensus at height %d (hash %s)", canonical.BlockNumber, canonical.BlockHash)
		return result
	}

	// Check for 2/3 Majority Consensus where 2 agree and 1 is an outlier
	// Pair (0, 1) agrees, 2 is outlier
	if s01.Compatible && !s01.Divergent {
		canonical := p0
		if p1.BlockNumber > canonical.BlockNumber {
			canonical = p1
		}
		result.Decision = DecisionMajorityConsensus
		result.Confidence = 2.0 / 3.0
		result.CanonicalHeight = canonical.BlockNumber
		result.CanonicalHash = normalizeHash(canonical.BlockHash)
		result.CanonicalParent = normalizeHash(canonical.ParentHash)
		result.OutlierProvider = p2.ProviderID
		result.AgreedProviders = []string{p0.ProviderID, p1.ProviderID}
		result.Details = fmt.Sprintf("2/3 majority consensus between %s and %s (outlier: %s)", p0.ProviderID, p1.ProviderID, p2.ProviderID)
		return result
	}

	// Pair (1, 2) agrees, 0 is outlier
	if s12.Compatible && !s12.Divergent {
		canonical := p1
		if p2.BlockNumber > canonical.BlockNumber {
			canonical = p2
		}
		result.Decision = DecisionMajorityConsensus
		result.Confidence = 2.0 / 3.0
		result.CanonicalHeight = canonical.BlockNumber
		result.CanonicalHash = normalizeHash(canonical.BlockHash)
		result.CanonicalParent = normalizeHash(canonical.ParentHash)
		result.OutlierProvider = p0.ProviderID
		result.AgreedProviders = []string{p1.ProviderID, p2.ProviderID}
		result.Details = fmt.Sprintf("2/3 majority consensus between %s and %s (outlier: %s)", p1.ProviderID, p2.ProviderID, p0.ProviderID)
		return result
	}

	// Pair (0, 2) agrees, 1 is outlier
	if s02.Compatible && !s02.Divergent {
		canonical := p0
		if p2.BlockNumber > canonical.BlockNumber {
			canonical = p2
		}
		result.Decision = DecisionMajorityConsensus
		result.Confidence = 2.0 / 3.0
		result.CanonicalHeight = canonical.BlockNumber
		result.CanonicalHash = normalizeHash(canonical.BlockHash)
		result.CanonicalParent = normalizeHash(canonical.ParentHash)
		result.OutlierProvider = p1.ProviderID
		result.AgreedProviders = []string{p0.ProviderID, p2.ProviderID}
		result.Details = fmt.Sprintf("2/3 majority consensus between %s and %s (outlier: %s)", p0.ProviderID, p2.ProviderID, p1.ProviderID)
		return result
	}

	// Ambiguous / Divergent: 2 providers disagree on hash, or 3 report different chains.
	// Fail open: confidence is 0.0
	if anyDivergent {
		result.Decision = DecisionForkDivergence
	} else {
		result.Decision = DecisionAmbiguous
	}
	result.Confidence = 0.0
	result.Details = fmt.Sprintf("no majority consensus among providers (s01=%v, s12=%v, s02=%v)", s01.Reason, s12.Reason, s02.Reason)
	return result
}
