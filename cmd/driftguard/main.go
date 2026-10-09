package main

import (
	"context"
	"encoding/json"
	"log"
	"net/http"
	"os"
	"os/signal"
	"strconv"
	"strings"
	"sync"
	"syscall"
	"time"

	"driftguard/internal/controller"
	"driftguard/internal/quorum"
)

type DaemonState struct {
	mu           sync.RWMutex
	StartTime    time.Time               `json:"start_time"`
	State        controller.NodeState    `json:"state"`
	SuspectCount int                     `json:"suspect_count"`
	RecoverCount int                     `json:"recover_count"`
	LatestQuorum quorum.QuorumResult     `json:"latest_quorum"`
	LocalSample  quorum.ProviderSample   `json:"local_sample"`
	LatestTick   controller.TickResult   `json:"latest_tick"`
	Alerts       []string                `json:"alerts"`
	TickCount    uint64                  `json:"tick_count"`
}

func getEnv(key, defaultVal string) string {
	if v := os.Getenv(key); v != "" {
		return v
	}
	return defaultVal
}

func getEnvInt(key string, defaultVal int) int {
	if v := os.Getenv(key); v != "" {
		if n, err := strconv.Atoi(v); err == nil {
			return n
		}
	}
	return defaultVal
}

func getEnvUint64(key string, defaultVal uint64) uint64 {
	if v := os.Getenv(key); v != "" {
		if n, err := strconv.ParseUint(v, 10, 64); err == nil {
			return n
		}
	}
	return defaultVal
}

func main() {
	log.Println("[DriftGuard] Initializing Consensus Sentinel & Hysteresis Controller...")

	refEndpointsStr := getEnv("REF_RPC_ENDPOINTS", "http://ref-rpc-a:8545,http://ref-rpc-b:8545,http://ref-rpc-c:8545")
	localEndpoint := getEnv("LOCAL_NODE_ENDPOINT", "http://local-nitro-node:8545")
	haproxySocket := getEnv("HAPROXY_SOCKET_PATH", "/var/run/haproxy/admin.sock")
	haproxyBackend := getEnv("HAPROXY_BACKEND", "be_nitro")
	haproxyServer := getEnv("HAPROXY_SERVER", "local")

	tickIntervalMs := getEnvInt("TICK_INTERVAL_MS", 50)
	lagTolerance := getEnvUint64("LAG_TOLERANCE", 2)
	lagThreshold := getEnvUint64("LAG_THRESHOLD", 4)
	suspectK := getEnvInt("SUSPECT_K", 3)
	recoveryM := getEnvInt("RECOVERY_M", 5)
	telemetryPort := getEnv("PORT", "8000")

	refEndpoints := strings.Split(refEndpointsStr, ",")
	for i := range refEndpoints {
		refEndpoints[i] = strings.TrimSpace(refEndpoints[i])
	}

	log.Printf("[DriftGuard] Configuration: RefProviders=%v, LocalNode=%s, HAProxySocket=%s, Backend=%s/%s, TickInterval=%dms",
		refEndpoints, localEndpoint, haproxySocket, haproxyBackend, haproxyServer, tickIntervalMs)

	// Create RPC collector and Quorum Engine
	collector := quorum.NewCollector(refEndpoints, time.Duration(tickIntervalMs*2)*time.Millisecond)
	localCollector := quorum.NewCollector([]string{localEndpoint}, time.Duration(tickIntervalMs*2)*time.Millisecond)
	engine := quorum.NewEngine(lagTolerance, collector)

	// Create HAProxy client & FSM
	hpClient := controller.NewUnixSocketHAProxy(haproxySocket, 1*time.Second)
	fsmCfg := controller.FSMConfig{
		BackendName:        haproxyBackend,
		ServerName:         haproxyServer,
		LagThreshold:       lagThreshold,
		SuspectThresholdK:  suspectK,
		RecoveryThresholdM: recoveryM,
	}
	fsm := controller.NewNodeFSM(fsmCfg, hpClient)

	daemonState := &DaemonState{
		StartTime: time.Now(),
		State:     controller.StateHealthy,
		Alerts:    make([]string, 0),
	}

	// HTTP Telemetry Server
	mux := http.NewServeMux()
	mux.HandleFunc("/healthz", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusOK)
		_ = json.NewEncoder(w).Encode(map[string]interface{}{
			"status": "healthy",
			"state":  fsm.State(),
		})
	})

	mux.HandleFunc("/status", func(w http.ResponseWriter, r *http.Request) {
		daemonState.mu.RLock()
		defer daemonState.mu.RUnlock()
		w.Header().Set("Content-Type", "application/json")
		_ = json.NewEncoder(w).Encode(daemonState)
	})

	httpServer := &http.Server{
		Addr:    ":" + telemetryPort,
		Handler: mux,
	}

	go func() {
		log.Printf("[DriftGuard] Starting HTTP telemetry server on :%s", telemetryPort)
		if err := httpServer.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Printf("[DriftGuard] HTTP server error: %v", err)
		}
	}()

	// Background ticker loop
	ticker := time.NewTicker(time.Duration(tickIntervalMs) * time.Millisecond)
	ctx, cancel := context.WithCancel(context.Background())

	sigCh := make(chan os.Signal, 1)
	signal.Notify(sigCh, syscall.SIGINT, syscall.SIGTERM)

	go func() {
		<-sigCh
		log.Println("[DriftGuard] Termination signal received, stopping...")
		ticker.Stop()
		cancel()
		shutdownCtx, sCancel := context.WithTimeout(context.Background(), 2*time.Second)
		defer sCancel()
		_ = httpServer.Shutdown(shutdownCtx)
	}()

	for {
		select {
		case <-ctx.Done():
			log.Println("[DriftGuard] Shutdown complete.")
			return
		case <-ticker.C:
			// 1. Concurrently collect from 3 reference providers and local node
			var wg sync.WaitGroup
			var refSamples []quorum.ProviderSample
			var localSample quorum.ProviderSample

			wg.Add(2)
			go func() {
				defer wg.Done()
				refSamples = collector.Collect(ctx)
			}()
			go func() {
				defer wg.Done()
				localSample = localCollector.FetchSingleProvider(ctx, localEndpoint)
			}()
			wg.Wait()

			// 2. Evaluate Quorum Consensus
			qResult := engine.Evaluate(refSamples)

			// 3. Process Hysteresis State Machine
			tickRes := fsm.ProcessTick(qResult, localSample)

			// 4. Update daemon state for telemetry
			daemonState.mu.Lock()
			daemonState.State = fsm.State()
			daemonState.SuspectCount, daemonState.RecoverCount = fsm.Counters()
			daemonState.LatestQuorum = qResult
			daemonState.LocalSample = localSample
			daemonState.LatestTick = tickRes
			daemonState.Alerts = fsm.Alerts()
			daemonState.TickCount++
			daemonState.mu.Unlock()

			// 5. Log state transitions or alerts
			if tickRes.PreviousState != tickRes.CurrentState {
				log.Printf("[DriftGuard] STATE TRANSITION: %s -> %s (msg: %s)",
					tickRes.PreviousState, tickRes.CurrentState, tickRes.Message)
			}
			if tickRes.DrainAction {
				log.Printf("[DriftGuard] [ACTUATION] Drained server %s/%s via HAProxy socket! Reason: %s",
					haproxyBackend, haproxyServer, tickRes.Message)
			}
			if tickRes.ReadyAction {
				log.Printf("[DriftGuard] [ACTUATION] Readied server %s/%s via HAProxy socket! Reason: %s",
					haproxyBackend, haproxyServer, tickRes.Message)
			}
			if tickRes.DrainRefused {
				log.Printf("[DriftGuard] [GUARDRAIL] MINIMUM_HEALTHY_TRIGGERED! Preserving routing on %s/%s",
					haproxyBackend, haproxyServer)
			}
		}
	}
}
