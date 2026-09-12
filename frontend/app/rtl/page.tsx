'use client';

import { useState, useEffect } from 'react';
import { 
  Code, 
  FileText, 
  Search, 
  ChevronDown, 
  ChevronRight,
  Copy,
  Check,
  AlertCircle,
  Info,
  Terminal,
  Database,
  Zap,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { rtlApi } from '@/lib/api';
import { api } from '@/lib/api';

const defaultRtl = `module fifo_sync #(
    parameter int DEPTH = 16,
    parameter int DATA_WIDTH = 32
) (
    input  logic                  clk,
    input  logic                  reset,
    input  logic                  wr_en,
    input  logic                  rd_en,
    input  logic [DATA_WIDTH-1:0] din,
    output logic [DATA_WIDTH-1:0] dout,
    output logic                  full,
    output logic                  empty,
    output logic [$clog2(DEPTH):0] count
);

    logic [DATA_WIDTH-1:0] mem [0:DEPTH-1];
    logic [$clog2(DEPTH):0] wr_ptr, rd_ptr;

    always_ff @(posedge clk) begin
        if (reset) begin
            wr_ptr <= 0;
            rd_ptr <= 0;
        end else begin
            if (wr_en && !full) wr_ptr <= wr_ptr + 1;
            if (rd_en && !empty) rd_ptr <= rd_ptr + 1;
        end
    end

    property p_no_write_when_full;
        @(posedge clk) disable iff (reset) full |-> !wr_en;
    endproperty
    a_no_write_when_full: assert property (p_no_write_when_full);

    property p_no_read_when_empty;
        @(posedge clk) disable iff (reset) empty |-> !rd_en;
    endproperty
    a_no_read_when_empty: assert property (p_no_read_when_empty);

endmodule`;

export default function RTLPage() {
  const [rtlContent, setRtlContent] = useState(defaultRtl);
  const [analysis, setAnalysis] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'analysis' | 'source'>('analysis');
  const [filename, setFilename] = useState('fifo.sv');

  const handleAnalyze = async () => {
    setLoading(true);
    try {
      const result = await rtlApi.analyze(rtlContent, filename);
      setAnalysis(result);
      setActiveTab('analysis');
    } catch (error) {
      console.error('Analysis failed:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleLoadExample = async () => {
    try {
      const result = await rtlApi.getFifoExample();
      setRtlContent(result.data.content);
      setFilename('fifo.sv');
    } catch (error) {
      console.error('Failed to load example:', error);
    }
  };

  const renderModuleTree = (modules: any[]) => {
    return modules.map((module, idx) => (
      <div key={idx} className="border border-border rounded-lg overflow-hidden">
        <div className="bg-secondary px-4 py-2 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Code className="w-5 h-5 text-primary" />
            <span className="font-mono font-medium">{module.name}</span>
            <span className="px-2 py-0.5 text-xs bg-primary/20 text-primary rounded">
              {module.module_type}
            </span>
            {module.is_top && (
              <span className="px-2 py-0.5 text-xs bg-green-500/20 text-green-400 rounded">
                TOP
              </span>
            )}
          </div>
          <span className="text-xs text-muted-foreground">
            Lines {module.start_line}-{module.end_line}
          </span>
        </div>
        <div className="p-4 space-y-4">
          {module.parameters.length > 0 && (
            <Section title="Parameters" icon={Database}>
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border">
                    <th className="text-left pb-2">Name</th>
                    <th className="text-left pb-2">Default</th>
                  </tr>
                </thead>
                <tbody>
                  {module.parameters.map((p: any) => (
                    <tr key={p.name} className="border-b border-border/50">
                      <td className="py-2 font-mono">{p.name}</td>
                      <td className="py-2 font-mono text-muted-foreground">{p.default_value}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </Section>
          )}

          {module.ports.length > 0 && (
            <Section title="Ports" icon={Terminal}>
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border">
                    <th className="text-left pb-2">Name</th>
                    <th className="text-left pb-2">Direction</th>
                    <th className="text-left pb-2">Width</th>
                  </tr>
                </thead>
                <tbody>
                  {module.ports.map((p: any) => (
                    <tr key={p.name} className="border-b border-border/50">
                      <td className="py-2 font-mono">{p.name}</td>
                      <td className="py-2">
                        <span className={cn(
                          'px-2 py-0.5 text-xs rounded',
                          p.direction === 'input' && 'bg-blue-500/20 text-blue-400',
                          p.direction === 'output' && 'bg-green-500/20 text-green-400',
                          p.direction === 'inout' && 'bg-yellow-500/20 text-yellow-400'
                        )}>
                          {p.direction}
                        </span>
                      </td>
                      <td className="py-2 font-mono text-muted-foreground">{p.width || '1'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </Section>
          )}

          {module.signals.length > 0 && (
            <Section title="Internal Signals" icon={Database}>
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border">
                    <th className="text-left pb-2">Name</th>
                    <th className="text-left pb-2">Type</th>
                    <th className="text-left pb-2">Width</th>
                  </tr>
                </thead>
                <tbody>
                  {module.signals.slice(0, 20).map((s: any) => (
                    <tr key={s.name} className="border-b border-border/50">
                      <td className="py-2 font-mono">{s.name}</td>
                      <td className="py-2 text-muted-foreground">{s.type}</td>
                      <td className="py-2 font-mono text-muted-foreground">{s.width || '1'}</td>
                    </tr>
                  ))}
                  {module.signals.length > 20 && (
                    <tr>
                      <td colSpan={3} className="py-2 text-center text-muted-foreground">
                        ... and {module.signals.length - 20} more signals
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </Section>
          )}

          {module.fsm_info.length > 0 && (
            <Section title="FSMs" icon={Zap}>
              {module.fsm_info.map((fsm: any, fi: number) => (
                <div key={fi} className="border border-border rounded-lg p-3">
                  <div className="font-medium mb-2">{fsm.name} (state: {fsm.state_variable})</div>
                  <div className="flex flex-wrap gap-1 mb-2">
                    {fsm.states.map((s: string) => (
                      <span key={s} className="px-2 py-0.5 text-xs bg-primary/20 text-primary rounded">
                        {s}
                      </span>
                    ))}
                  </div>
                  {fsm.transitions.length > 0 && (
                    <div className="text-sm text-muted-foreground">
                      Transitions: {fsm.transitions.map((t: any) => `${t.from}→${t.to}`).join(', ')}
                    </div>
                  )}
                </div>
              ))}
            </Section>
          )}

          {module.always_blocks.length > 0 && (
            <Section title="Always Blocks" icon={Info}>
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border">
                    <th className="text-left pb-2">Sensitivity</th>
                    <th className="text-left pb-2">Clock</th>
                    <th className="text-left pb-2">Reset</th>
                  </tr>
                </thead>
                <tbody>
                  {module.always_blocks.map((ab: any, ai: number) => (
                    <tr key={ai} className="border-b border-border/50">
                      <td className="py-2 font-mono text-xs">{ab.sensitivity}</td>
                      <td className="py-2 font-mono text-xs">{ab.clock || '-'}</td>
                      <td className="py-2 font-mono text-xs">
                        {ab.reset ? `${ab.reset} (${ab.reset_type})` : '-'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </Section>
          )}

          {module.assertions.length > 0 && (
            <Section title="Existing Assertions" icon={AlertCircle}>
              {module.assertions.map((a: any, ai: number) => (
                <div key={ai} className="border border-border rounded-lg p-3 font-mono text-xs">
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-medium">{a.name}</span>
                    <span className="px-2 py-0.5 text-xs bg-muted text-muted-foreground rounded">
                      {a.type}
                    </span>
                  </div>
                  <pre className="text-muted-foreground overflow-x-auto">{a.code}</pre>
                </div>
              ))}
            </Section>
          )}
        </div>
      </div>
    ));
  };

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b border-border bg-card/50 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 py-3">
          <div className="flex items-center justify-between">
            <h1 className="text-xl font-bold">RTL Explorer</h1>
            <div className="flex items-center gap-2">
              <button
                onClick={handleLoadExample}
                className="px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors"
              >
                Load FIFO Example
              </button>
              <button
                onClick={handleAnalyze}
                disabled={loading}
                className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50"
              >
                {loading ? 'Analyzing...' : 'Analyze RTL'}
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Editor Panel */}
          <div className="lg:col-span-2">
            <div className="bg-card border border-border rounded-xl overflow-hidden">
              <div className="border-b border-border px-4 py-2 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <FileText className="w-5 h-5" />
                  <input
                    type="text"
                    value={filename}
                    onChange={(e) => setFilename(e.target.value)}
                    className="bg-transparent border-none outline-none font-mono text-sm"
                  />
                </div>
                <div className="flex items-center gap-2">
                  <button className="p-2 hover:bg-secondary rounded-lg transition-colors" title="Copy">
                    <Copy className="w-4 h-4" />
                  </button>
                </div>
              </div>
              <textarea
                value={rtlContent}
                onChange={(e) => setRtlContent(e.target.value)}
                className="w-full h-[600px] p-4 font-mono text-sm resize-none bg-transparent outline-none"
                spellCheck={false}
                placeholder="Paste SystemVerilog/Verilog RTL here..."
              />
            </div>
          </div>

          {/* Analysis Panel */}
          <div className="space-y-4">
            <div className="bg-card border border-border rounded-xl overflow-hidden">
              <div className="border-b border-border px-4 py-2 flex items-center gap-2">
                <Search className="w-5 h-5" />
                <span className="font-medium">Analysis Results</span>
              </div>
              <div className="p-4">
                {analysis ? (
                  <>
                    <div className="grid grid-cols-2 gap-4 mb-4">
                      <StatCard label="Modules" value={analysis.summary?.num_modules || 0} icon={Code} />
                      <StatCard label="Ports" value={analysis.summary?.total_ports || 0} icon={Terminal} />
                      <StatCard label="Signals" value={analysis.summary?.total_internal_signals || 0} icon={Database} />
                      <StatCard label="FSMs" value={analysis.summary?.total_fsm_count || 0} icon={Zap} />
                      <StatCard label="Assertions" value={analysis.summary?.total_assertions || 0} icon={AlertCircle} />
                      <StatCard label="Instances" value={analysis.summary?.total_module_instances || 0} icon={Info} />
                    </div>

                    {analysis.summary?.clock_signals.length > 0 && (
                      <InfoBox title="Clocks" icon={Zap}>
                        {analysis.summary.clock_signals.map((c: string) => (
                          <span key={c} className="px-2 py-0.5 text-xs bg-primary/20 text-primary rounded mr-1">
                            {c}
                          </span>
                        ))}
                      </InfoBox>
                    )}

                    {analysis.summary?.reset_signals.length > 0 && (
                      <InfoBox title="Resets" icon={AlertCircle}>
                        {analysis.summary.reset_signals.map((r: string) => (
                          <span key={r} className="px-2 py-0.5 text-xs bg-yellow-500/20 text-yellow-400 rounded mr-1">
                            {r}
                          </span>
                        ))}
                      </InfoBox>
                    )}

                    {analysis.summary?.protocols_detected.length > 0 && (
                      <InfoBox title="Protocols" icon={Database}>
                        {analysis.summary.protocols_detected.map((p: string) => (
                          <span key={p} className="px-2 py-0.5 text-xs bg-green-500/20 text-green-400 rounded mr-1">
                            {p}
                          </span>
                        ))}
                      </InfoBox>
                    )}
                  </>
                ) : (
                  <div className="text-center py-12 text-muted-foreground">
                    <Code className="w-12 h-12 mx-auto mb-4 opacity-50" />
                    <p>Analyze RTL to see results</p>
                  </div>
                )}
              </div>
            </div>

            {analysis && (
              <div className="bg-card border border-border rounded-xl overflow-hidden">
                <div className="border-b border-border px-4 py-2 flex items-center gap-2">
                  <Code className="w-5 h-5" />
                  <span className="font-medium">Module Details</span>
                </div>
                <div className="p-4 max-h-96 overflow-y-auto">
                  {renderModuleTree(analysis.modules)}
                </div>
              </div>
            )}

            {analysis && analysis.summary?.warnings && analysis.summary.warnings.length > 0 && (
              <div className="bg-card border border-border rounded-xl overflow-hidden">
                <div className="border-b border-border px-4 py-2 flex items-center gap-2">
                  <AlertCircle className="w-5 h-5 text-yellow-500" />
                  <span className="font-medium text-yellow-500">Warnings</span>
                </div>
                <div className="p-4">
                  <ul className="space-y-1">
                    {analysis.summary.warnings.map((w: string, i: number) => (
                      <li key={i} className="text-sm text-yellow-400 flex items-center gap-2">
                        <AlertCircle className="w-4 h-4 flex-shrink-0" />
                        {w}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}

function Section({ title, icon: Icon, children }: { title: string; icon: any; children: React.ReactNode }) {
  return (
    <div>
      <div className="flex items-center gap-2 mb-3">
        <Icon className="w-4 h-4 text-muted-foreground" />
        <span className="font-medium text-sm">{title}</span>
      </div>
      {children}
    </div>
  );
}

function StatCard({ label, value, icon: Icon }: { label: string; value: number; icon: any }) {
  return (
    <div className="bg-secondary/50 rounded-lg p-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Icon className="w-5 h-5 text-primary" />
          <span className="text-sm text-muted-foreground">{label}</span>
        </div>
        <span className="text-2xl font-bold tabular-nums">{value}</span>
      </div>
    </div>
  );
}

function InfoBox({ title, icon: Icon, children }: { title: string; icon: any; children: React.ReactNode }) {
  return (
    <div className="bg-secondary/50 rounded-lg p-3">
      <div className="flex items-center gap-2 mb-2">
        <Icon className="w-4 h-4 text-muted-foreground" />
        <span className="font-medium text-sm">{title}</span>
      </div>
      <div className="flex flex-wrap gap-1">{children}</div>
    </div>
  );
}