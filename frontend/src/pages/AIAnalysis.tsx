import { BrainCircuit } from 'lucide-react';
import { api } from '../lib/api';
import { usePoll } from '../hooks/usePoll';
import { GlassCard } from '../components/GlassCard';
import { subsystemLabel, formatTime } from '../lib/format';

export default function AIAnalysisPage() {
  const { data: insights } = usePoll(() => api.aiInsights(), { intervalMs: 3000 });

  return (
    <div className="space-y-5 animate-fade-up">
      <div>
        <h1 className="text-xl font-bold mb-1">AI Mission Analysis</h1>
        <p className="text-sm text-[var(--color-text-dim)]">
          Explainable, rule-based analysis generated from live detection, risk, and prediction state
          &mdash; not a black-box model. Each insight cites the evidence behind it.
        </p>
      </div>

      <div className="space-y-4">
        {(insights ?? []).map((insight) => (
          <GlassCard key={insight.id} className="relative overflow-hidden">
            <div
              className="absolute top-0 left-0 w-1 h-full"
              style={{ background: 'linear-gradient(180deg, #6C63FF, #00D9FF)' }}
            />
            <div className="pl-3">
              <div className="flex items-start justify-between mb-3 gap-4">
                <div className="flex items-center gap-2">
                  <BrainCircuit size={17} className="text-[var(--color-ai-purple)] shrink-0" />
                  <h2 className="text-base font-semibold">{insight.title}</h2>
                </div>
                <div className="text-right shrink-0">
                  <p className="text-[10px] text-[var(--color-text-faint)] uppercase">Confidence</p>
                  <p className="mono font-bold text-[var(--color-ai-purple)]">{Math.round(insight.confidence * 100)}%</p>
                </div>
              </div>

              {insight.related_subsystems.length > 0 && (
                <div className="flex flex-wrap gap-1.5 mb-3">
                  {insight.related_subsystems.map((s) => (
                    <span key={s} className="text-[10px] mono px-2 py-0.5 rounded-full bg-white/[0.05] text-[var(--color-text-dim)] border border-white/10">
                      {subsystemLabel(s)}
                    </span>
                  ))}
                </div>
              )}

              <div className="mb-4">
                <p className="text-[11px] text-[var(--color-text-faint)] uppercase mb-1.5">Analysis</p>
                <p className="text-sm leading-relaxed text-[var(--color-text-primary)]">{insight.analysis}</p>
              </div>

              <div>
                <p className="text-[11px] text-[var(--color-text-faint)] uppercase mb-1.5">Recommended Action</p>
                <p className="text-sm leading-relaxed p-3 rounded-lg bg-[var(--color-space-cyan)]/10 border border-[var(--color-space-cyan)]/25">
                  {insight.recommended_action}
                </p>
              </div>

              <p className="text-[10px] text-[var(--color-text-faint)] mono mt-3">{formatTime(insight.timestamp)}</p>
            </div>
          </GlassCard>
        ))}

        {(insights ?? []).length === 0 && (
          <GlassCard>
            <p className="text-sm text-[var(--color-text-faint)] text-center py-8">
              Awaiting telemetry to analyze. Start the simulation to generate live insights.
            </p>
          </GlassCard>
        )}
      </div>
    </div>
  );
}
