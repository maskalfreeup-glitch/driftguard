export interface NetworkConfig {
  id: string
  name: string
  chainId: number
  endpoint: string
  mirrorDisplay: string
  mirrorUrl: string
  badge: string
}

export const NETWORKS: NetworkConfig[] = [
  {
    id: "arb",
    name: "Arbitrum One",
    chainId: 42161,
    endpoint: "https://rpc.driftguard.live/arb",
    mirrorDisplay: "Consensus Fallback Pool (Auto-drained)",
    mirrorUrl: "https://rpc.driftguard.live/arb",
    badge: "Mainnet Core"
  },
  {
    id: "nova",
    name: "Arbitrum Nova",
    chainId: 42170,
    endpoint: "https://rpc.driftguard.live/nova",
    mirrorDisplay: "Consensus Fallback Pool (Auto-drained)",
    mirrorUrl: "https://rpc.driftguard.live/nova",
    badge: "AnyTrust"
  },
  {
    id: "arb-sepolia",
    name: "Arbitrum Sepolia",
    chainId: 421614,
    endpoint: "https://rpc.driftguard.live/arb-sepolia",
    mirrorDisplay: "Consensus Fallback Pool (Auto-drained)",
    mirrorUrl: "https://rpc.driftguard.live/arb-sepolia",
    badge: "Testnet"
  }
]
