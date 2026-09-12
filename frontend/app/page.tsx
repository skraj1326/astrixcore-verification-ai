'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { 
  LayoutDashboard, 
  Code, 
  FileText, 
  ShieldCheck, 
  PlayCircle, 
  BarChart, 
  AlertTriangle,
  GitBranch,
  Search,
  Settings,
  Zap,
  ChevronRight,
  ExternalLink,
  Database,
  TestTube,
  Bug,
  Layers,
  RefreshCw,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { api } from '@/lib/api';

const navigation = [
  { name: 'Dashboard', href: '/', icon: LayoutDashboard, description: 'Project overview & quick actions' },
  { name: 'RTL Explorer', href: '/rtl', icon: Code, description: 'Parse, analyze & explore RTL designs' },
  { name: 'Verification Plan', href: '/plan', icon: FileText, description: 'Auto-generated verification plans' },
  { name: 'Assertions', href: '/assertions', icon: ShieldCheck, description: 'SVA generation & management' },
  { name: 'Tests', href: '/tests', icon: TestTube, description: 'Directed, random & UVM tests' },
  { name: 'Simulation', href: '/simulation', icon: PlayCircle, description: 'Run & manage simulations' },
  { name: 'Coverage', href: '/coverage', icon: BarChart, description: 'Coverage analysis & gap detection' },
  { name: 'Failures', href: '/failures', icon: AlertTriangle, description: 'Failure analysis & debug' },
  { name: 'Regression', href: '/regression', icon: RefreshCw, description: 'Regression runs & tracking' },
  { name: 'Traceability', href: '/traceability', icon: GitBranch, description: 'Requirement traceability matrix' },
  { name: 'Settings', href: '/settings', icon: Settings, description: 'Configuration & preferences' },
];

const features = [
  {
    title: 'RTL Intelligence',
    description: 'Parse SystemVerilog/Verilog. Extract modules, ports, signals, clocks, resets, FSMs, FIFOs, protocols. Build a Design Knowledge Graph.',
    icon: Code,
    color: 'bg-blue-600/20 text-blue-400',
  },
  {
    title: 'Verification Planner',
    description: 'Auto-generate verification plans with traceable items. Every item linked to RTL behavior or specification. RTL-derived, Spec-derived, AI-inferred.',
    icon: FileText,
    color: 'bg-purple-600/20 text-purple-400',
  },
  {
    title: 'SVA Generator',
    description: 'Generate SystemVerilog Assertions with evidence, confidence levels, and false-positive warnings. Reset, handshake, FSM, FIFO, counter assertions.',
    icon: ShieldCheck,
    color: 'bg-green-600/20 text-green-400',
  },
  {
    title: 'Test Generator',
    description: 'Generate directed, constrained-random, and UVM tests with stated verification objectives. Coverage-targeted test generation.',
    icon: TestTube,
    color: 'bg-orange-600/20 text-orange-400',
  },
  {
    title: 'Coverage Intelligence',
    description: 'Analyze coverage reports, identify gaps, classify reachability (reachable_untested, potentially_unreachable, unreachable), generate targeted tests.',
    icon: BarChart,
    color: 'bg-red-600/20 text-red-400',
  },
  {
    title: 'Closed-Loop AI',
    description: 'AI-driven loop: coverage gaps → targeted tests → simulate → measure → repeat until closure. Mock provider for offline, OpenAI-compatible for cloud.',
    icon: Zap,
    color: 'bg-cyan-600/20 text-cyan-400',
  },
];

const pipelineSteps = [
  'RTL Upload',
  'Parse & Analyze',
  'Knowledge Graph',
  'Verify Plan',
  'Generate SVA',
  'Generate Tests',
  'Simulate',
  'Coverage Analysis',
  'Gap Detection',
  'Targeted Tests',
  'Re-simulate',
  'Closure',
];

export default function Dashboard() {
  const router = useRouter();
  const [projects, setProjects] = useState<any[]>([]);
  const [stats, setStats] = useState({
    totalProjects: 0,
    rtlFiles: 0,
    assertions: 0,
    tests: 0,
    simulations: 0,
    coverage: 0,
    gaps: 0,
    recentRuns: 0,
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [projectsRes, statsRes] = await Promise.all([
        api.get('/projects/'),
        api.get('/projects/stats'),
      ]);
      setProjects(projectsRes.data || []);
      setStats(statsRes.data || stats);
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAnalyzeFifo = async () => {
    try {
      // Get FIFO example
      const fifoRes = await api.get('/rtl/examples/fifo');
      const rtlContent = fifoRes.data.content;

      // Create project
      const projectRes = await api.post('/projects/', {
        name: 'FIFO Demo',
        description: 'Auto-generated FIFO verification demo',
      });
      const projectId = projectRes.data.id;

      // Upload RTL
      await api.post(`/${projectId}/rtl`, {
        content: rtlContent,
        filename: 'fifo.sv',
      });

      // Run full flow
      await api.post('/verification/full-flow', {
        rtl_content: rtlContent,
        specification: 'Parameterized synchronous FIFO with full/empty flags, occupancy counter, and built-in assertions.',
      });

      router.push(`/projects/${projectId}`);
    } catch (error) {
      console.error('Failed to analyze FIFO:', error);
    }
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Top Status Bar */}
      <header className="border-b border-border bg-card/50 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 py-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center">
                  <Zap className="w-5 h-5 text-primary-foreground" />
                </div>
                <span className="text-xl font-bold text-foreground">ASTRIXCORE</span>
                <span className="text-sm text-muted-foreground">Verification AI v0.1</span>
              </div>
            </div>
            <div className="flex items-center gap-4">
              <div className="hidden md:flex items-center gap-2 px-3 py-1.5 rounded-lg bg-secondary text-xs font-medium">
                <span className="w-2 h-2 rounded-full bg-green-500" />
                <span>Backend Connected</span>
              </div>
              <Link href="/settings" className="p-2 hover:bg-secondary rounded-lg transition-colors">
                <Settings className="w-5 h-5" />
              </Link>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-8">
        {/* Sidebar + Content */}
        <div className="flex gap-6">
          {/* Sidebar */}
          <aside className="w-64 flex-shrink-0 hidden lg:block">
            <nav className="space-y-1">
              {navigation.map((item) => (
                <Link
                  key={item.name}
                  href={item.href}
                  className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-muted-foreground hover:bg-secondary hover:text-foreground transition-colors group"
                >
                  <item.icon className="w-5 h-5" />
                  <span>{item.name}</span>
                </Link>
              ))}
            </nav>
          </aside>

          {/* Main Content */}
          <div className="flex-1 min-w-0">
            {/* Hero & Quick Actions */}
            <div className="mb-8">
              <div className="flex items-start justify-between gap-4 mb-6">
                <div>
                  <h1 className="text-3xl font-bold tracking-tight">
                    <span className="text-primary">ASTRIXCORE</span> Verification AI
                  </h1>
                  <p className="text-lg text-muted-foreground mt-1">
                    AI-assisted verification from RTL to coverage closure.
                  </p>
                  <p className="text-sm text-muted-foreground/70 mt-1">
                    Not a chatbot. An engineering tool that integrates with real verification workflows.
                  </p>
                </div>
                <button
                  onClick={handleAnalyzeFifo}
                  className="flex items-center gap-2 px-6 py-3 bg-primary text-primary-foreground rounded-lg font-medium hover:bg-primary/90 transition-colors whitespace-nowrap"
                >
                  <PlayCircle className="w-5 h-5" />
                  Analyze FIFO Demo
                </button>
              </div>

              {/* Feature Cards */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
                {features.map((feature, i) => (
                  <div
                    key={feature.title}
                    className={`p-5 rounded-xl border border-border ${feature.color} hover:border-primary/50 transition-colors`}
                  >
                    <div className={`p-2 rounded-lg ${feature.color} w-fit mb-3`}>
                      <feature.icon className="w-6 h-6" />
                    </div>
                    <h3 className="font-semibold text-lg mb-2">{feature.title}</h3>
                    <p className="text-sm text-muted-foreground">{feature.description}</p>
                  </div>
                ))}
              </div>
            </div>

            {/* Pipeline Overview */}
            <div className="bg-card border border-border rounded-xl p-6 mb-8">
              <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <Layers className="w-5 h-5 text-primary" />
                Verification Pipeline
              </h2>
              <div className="overflow-x-auto pb-4">
                <div className="flex items-center gap-2 min-w-max">
                  {pipelineSteps.map((step, i) => (
                    <div key={step} className="flex-shrink-0 flex flex-col items-center">
                      <div className="w-24 p-3 bg-secondary rounded-lg text-center">
                        <div className="text-primary font-mono text-xs mb-1">{String(i + 1).padStart(2, '0')}</div>
                        <div className="text-xs text-muted-foreground whitespace-nowrap">{step}</div>
                      </div>
                      {i < pipelineSteps.length - 1 && (
                        <ChevronRight className="text-muted-foreground mx-1" />
                      )}
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Project Stats */}
            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-8 gap-4 mb-8">
              {[
                { label: 'Projects', value: stats.totalProjects, icon: Database, color: 'text-blue-400' },
                { label: 'RTL Files', value: stats.rtlFiles, icon: Code, color: 'text-purple-400' },
                { label: 'Assertions', value: stats.assertions, icon: ShieldCheck, color: 'text-green-400' },
                { label: 'Tests', value: stats.tests, icon: TestTube, color: 'text-orange-400' },
                { label: 'Simulations', value: stats.simulations, icon: PlayCircle, color: 'text-cyan-400' },
                { label: 'Coverage', value: `${stats.coverage}%`, icon: BarChart, color: 'text-red-400' },
                { label: 'Gaps', value: stats.gaps, icon: AlertTriangle, color: 'text-yellow-400' },
                { label: 'Recent Runs', value: stats.recentRuns, icon: RefreshCw, color: 'text-pink-400' },
              ].map((stat, i) => (
                <div key={i} className="bg-card border border-border rounded-xl p-5">
                  <div className="flex items-center justify-between mb-2">
                    <stat.icon className={`w-5 h-5 ${stat.color}`} />
                    <span className="text-2xl font-bold tabular-nums">{stat.value}</span>
                  </div>
                  <p className="text-xs text-muted-foreground">{stat.label}</p>
                </div>
              ))}
            </div>

            {/* Recent Projects */}
            <div className="bg-card border border-border rounded-xl">
              <div className="p-5 border-b border-border flex items-center justify-between">
                <h2 className="font-semibold">Recent Projects</h2>
                <Link href="/projects" className="text-sm text-primary hover:underline">View all</Link>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-border">
                      <th className="px-5 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">Project</th>
                      <th className="px-5 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">RTL Files</th>
                      <th className="px-5 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">Assertions</th>
                      <th className="px-5 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">Tests</th>
                      <th className="px-5 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">Simulations</th>
                      <th className="px-5 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">Coverage</th>
                      <th className="px-5 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">Status</th>
                      <th className="px-5 py-3 text-right text-xs font-medium text-muted-foreground uppercase tracking-wider">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border">
                    {loading ? (
                      <tr>
                        <td colSpan={8} className="px-5 py-10 text-center text-muted-foreground">
                          Loading...
                        </td>
                      </tr>
                    ) : projects.length === 0 ? (
                      <tr>
                        <td colSpan={8} className="px-5 py-10 text-center text-muted-foreground">
                          No projects yet. Click "Analyze FIFO Demo" to get started.
                        </td>
                      </tr>
                    ) : (
                      projects.slice(0, 5).map((project) => (
                        <tr key={project.id} className="hover:bg-secondary/50">
                          <td className="px-5 py-4">
                            <div className="font-medium">{project.name}</div>
                            <div className="text-xs text-muted-foreground">{project.description}</div>
                          </td>
                          <td className="px-5 py-4 text-sm">-</td>
                          <td className="px-5 py-4 text-sm">-</td>
                          <td className="px-5 py-4 text-sm">-</td>
                          <td className="px-5 py-4 text-sm">-</td>
                          <td className="px-5 py-4 text-sm">-</td>
                          <td className="px-5 py-4">
                            <span className="px-2 py-0.5 rounded-full text-xs bg-green-500/20 text-green-400">
                              {project.status}
                            </span>
                          </td>
                          <td className="px-5 py-4 text-right">
                            <Link 
                              href={`/projects/${project.id}`}
                              className="text-sm text-primary hover:underline"
                            >
                              Open
                            </Link>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}