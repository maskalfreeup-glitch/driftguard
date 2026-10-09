package controller

import (
	"bufio"
	"fmt"
	"net"
	"strings"
	"sync"
	"time"
)

// HAProxyClient defines the interface for controlling HAProxy via its admin socket.
type HAProxyClient interface {
	DrainServer(backend, server string) error
	ReadyServer(backend, server string) error
	GetServerState(backend, server string) (string, error)
	GetHealthyServerCount(backend string) (int, error)
}

// UnixSocketHAProxy communicates with HAProxy over a UNIX domain socket.
type UnixSocketHAProxy struct {
	SocketPath string
	Timeout    time.Duration
	mu         sync.Mutex
}

// NewUnixSocketHAProxy creates an HAProxy client pointing to a UNIX socket path.
func NewUnixSocketHAProxy(socketPath string, timeout time.Duration) *UnixSocketHAProxy {
	if timeout <= 0 {
		timeout = 2 * time.Second
	}
	return &UnixSocketHAProxy{
		SocketPath: socketPath,
		Timeout:    timeout,
	}
}

func (c *UnixSocketHAProxy) executeCommand(cmd string) (string, error) {
	c.mu.Lock()
	defer c.mu.Unlock()

	conn, err := net.DialTimeout("unix", c.SocketPath, c.Timeout)
	if err != nil {
		return "", fmt.Errorf("dial haproxy unix socket %s: %w", c.SocketPath, err)
	}
	defer conn.Close()

	_ = conn.SetDeadline(time.Now().Add(c.Timeout))

	if !strings.HasSuffix(cmd, "\n") {
		cmd += "\n"
	}

	if _, err := conn.Write([]byte(cmd)); err != nil {
		return "", fmt.Errorf("write command to haproxy socket: %w", err)
	}

	reader := bufio.NewReader(conn)
	var sb strings.Builder
	for {
		line, err := reader.ReadString('\n')
		sb.WriteString(line)
		if err != nil {
			break
		}
	}
	return sb.String(), nil
}

// DrainServer executes: set server <backend>/<srv> state drain
func (c *UnixSocketHAProxy) DrainServer(backend, server string) error {
	cmd := fmt.Sprintf("set server %s/%s state drain", backend, server)
	resp, err := c.executeCommand(cmd)
	if err != nil {
		return err
	}
	if strings.Contains(strings.ToLower(resp), "error") {
		return fmt.Errorf("haproxy drain error: %s", strings.TrimSpace(resp))
	}
	return nil
}

// ReadyServer executes: set server <backend>/<srv> state ready
func (c *UnixSocketHAProxy) ReadyServer(backend, server string) error {
	cmd := fmt.Sprintf("set server %s/%s state ready", backend, server)
	resp, err := c.executeCommand(cmd)
	if err != nil {
		return err
	}
	if strings.Contains(strings.ToLower(resp), "error") {
		return fmt.Errorf("haproxy ready error: %s", strings.TrimSpace(resp))
	}
	return nil
}

// GetServerState returns the current operational state of a server in a backend.
func (c *UnixSocketHAProxy) GetServerState(backend, server string) (string, error) {
	resp, err := c.executeCommand(fmt.Sprintf("show servers state %s", backend))
	if err != nil {
		return "", err
	}

	scanner := bufio.NewScanner(strings.NewReader(resp))
	for scanner.Scan() {
		line := strings.TrimSpace(scanner.Text())
		if strings.HasPrefix(line, "#") || line == "" {
			continue
		}
		fields := strings.Fields(line)
		if len(fields) >= 6 && fields[3] == server {
			// fields[5] is srv_op_state in HAProxy: 0=STOP, 1=START, 2=DRAIN, 3=NO_CHECK
			// Also fields[6] is admin state
			return fields[5], nil
		}
	}
	return "UNKNOWN", nil
}

// GetHealthyServerCount parses HAProxy `show stat` to count healthy, non-drained servers for a backend.
func (c *UnixSocketHAProxy) GetHealthyServerCount(backend string) (int, error) {
	resp, err := c.executeCommand("show stat")
	if err != nil {
		return 0, err
	}

	healthyCount := 0
	scanner := bufio.NewScanner(strings.NewReader(resp))
	for scanner.Scan() {
		line := strings.TrimSpace(scanner.Text())
		if strings.HasPrefix(line, "#") || line == "" {
			continue
		}
		parts := strings.Split(line, ",")
		if len(parts) < 18 {
			continue
		}
		pxname := parts[0]
		svname := parts[1]
		status := parts[17]

		if pxname == backend && svname != "BACKEND" && svname != "FRONTEND" {
			// Status UP or UP 1/2 etc. Not DRAIN, MAINT, or DOWN.
			if strings.HasPrefix(status, "UP") {
				healthyCount++
			}
		}
	}
	return healthyCount, nil
}

// MockHAProxy is an in-memory implementation of HAProxyClient for deterministic testing.
type MockHAProxy struct {
	mu           sync.Mutex
	ServerStates map[string]string // key: "backend/server" -> "DRAIN", "READY", "UP", "DOWN"
	HealthyCount map[string]int    // key: "backend" -> count
	Commands     []string
}

// NewMockHAProxy creates a new MockHAProxy instance.
func NewMockHAProxy() *MockHAProxy {
	return &MockHAProxy{
		ServerStates: make(map[string]string),
		HealthyCount: make(map[string]int),
		Commands:     make([]string, 0),
	}
}

func (m *MockHAProxy) DrainServer(backend, server string) error {
	m.mu.Lock()
	defer m.mu.Unlock()
	key := backend + "/" + server
	m.ServerStates[key] = "DRAIN"
	m.Commands = append(m.Commands, fmt.Sprintf("set server %s state drain", key))
	if m.HealthyCount[backend] > 0 {
		m.HealthyCount[backend]--
	}
	return nil
}

func (m *MockHAProxy) ReadyServer(backend, server string) error {
	m.mu.Lock()
	defer m.mu.Unlock()
	key := backend + "/" + server
	m.ServerStates[key] = "READY"
	m.Commands = append(m.Commands, fmt.Sprintf("set server %s state ready", key))
	m.HealthyCount[backend]++
	return nil
}

func (m *MockHAProxy) GetServerState(backend, server string) (string, error) {
	m.mu.Lock()
	defer m.mu.Unlock()
	key := backend + "/" + server
	if st, ok := m.ServerStates[key]; ok {
		return st, nil
	}
	return "READY", nil
}

func (m *MockHAProxy) GetHealthyServerCount(backend string) (int, error) {
	m.mu.Lock()
	defer m.mu.Unlock()
	if c, ok := m.HealthyCount[backend]; ok {
		return c, nil
	}
	return 2, nil // default 2 healthy servers in pool
}

func (m *MockHAProxy) SetHealthyServerCount(backend string, count int) {
	m.mu.Lock()
	defer m.mu.Unlock()
	m.HealthyCount[backend] = count
}
