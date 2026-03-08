'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { Button } from '@/components/livekit/button';
import { cn } from '@/lib/utils';

const PURPOSES = ['For Fun', 'For Pattreeya', 'For Learning About KasiOss'] as const;

interface GateDialogProps {
  onGranted: (guestName: string) => void;
}

export function GateDialog({ onGranted }: GateDialogProps) {
  const [guestName, setGuestName] = useState('');
  const [purpose, setPurpose] = useState<string>('');
  const [passwd, setPasswd] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError('');

    if (!guestName.trim()) {
      setError('Please tell us your name.');
      return;
    }
    if (guestName.trim().toLowerCase() === 'pat') {
      onGranted(guestName.trim());
      return;
    }
    if (!purpose) {
      setError('Please select a purpose.');
      return;
    }
    if (!passwd.trim()) {
      setError('Please enter the secret.');
      return;
    }

    setLoading(true);
    try {
      const res = await fetch('/api/verify-access', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ purpose, passwd }),
      });
      const data = (await res.json()) as { ok: boolean; message?: string };
      if (data.ok) {
        onGranted(guestName.trim());
      } else {
        setError(data.message ?? 'Access denied.');
      }
    } catch {
      setError('Something went wrong. Please try again.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="bg-background flex min-h-svh items-center justify-center px-4">
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, ease: 'easeOut' }}
        className="bg-card border-border w-full max-w-sm rounded-2xl border p-8 shadow-lg"
      >
        {/* Icon */}
        <div className="mb-6 flex justify-center">
          <svg
            width="48"
            height="48"
            viewBox="0 0 64 64"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
            className="text-foreground"
          >
            <path
              d="M15 24V40C15 40.7957 14.6839 41.5587 14.1213 42.1213C13.5587 42.6839 12.7956 43 12 43C11.2044 43 10.4413 42.6839 9.87868 42.1213C9.31607 41.5587 9 40.7957 9 40V24C9 23.2044 9.31607 22.4413 9.87868 21.8787C10.4413 21.3161 11.2044 21 12 21C12.7956 21 13.5587 21.3161 14.1213 21.8787C14.6839 22.4413 15 23.2044 15 24ZM22 5C21.2044 5 20.4413 5.31607 19.8787 5.87868C19.3161 6.44129 19 7.20435 19 8V56C19 56.7957 19.3161 57.5587 19.8787 58.1213C20.4413 58.6839 21.2044 59 22 59C22.7956 59 23.5587 58.6839 24.1213 58.1213C24.6839 57.5587 25 56.7957 25 56V8C25 7.20435 24.6839 6.44129 24.1213 5.87868C23.5587 5.31607 22.7956 5 22 5ZM32 13C31.2044 13 30.4413 13.3161 29.8787 13.8787C29.3161 14.4413 29 15.2044 29 16V48C29 48.7957 29.3161 49.5587 29.8787 50.1213C30.4413 50.6839 31.2044 51 32 51C32.7956 51 33.5587 50.6839 34.1213 50.1213C34.6839 49.5587 35 48.7957 35 48V16C35 15.2044 34.6839 14.4413 34.1213 13.8787C33.5587 13.3161 32.7956 13 32 13ZM42 21C41.2043 21 40.4413 21.3161 39.8787 21.8787C39.3161 22.4413 39 23.2044 39 24V40C39 40.7957 39.3161 41.5587 39.8787 42.1213C40.4413 42.6839 41.2043 43 42 43C42.7957 43 43.5587 42.6839 44.1213 42.1213C44.6839 41.5587 45 40.7957 45 40V24C45 23.2044 44.6839 22.4413 44.1213 21.8787C43.5587 21.3161 42.7957 21 42 21ZM52 17C51.2043 17 50.4413 17.3161 49.8787 17.8787C49.3161 18.4413 49 19.2044 49 20V44C49 44.7957 49.3161 45.5587 49.8787 46.1213C50.4413 46.6839 51.2043 47 52 47C52.7957 47 53.5587 46.6839 54.1213 46.1213C54.6839 45.5587 55 44.7957 55 44V20C55 19.2044 54.6839 18.4413 54.1213 17.8787C53.5587 17.3161 52.7957 17 52 17Z"
              fill="currentColor"
            />
          </svg>
        </div>

        <h1 className="text-foreground mb-1 text-center font-mono text-lg font-bold tracking-wide uppercase">
          Pattreeya&apos;s Voice Agent
        </h1>
        <p className="text-muted-foreground mb-6 text-center font-mono text-xs">
          Let&apos;s make sure we know each other.
        </p>

        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          {/* Guest name */}
          <div className="flex flex-col gap-1.5">
            <label className="text-foreground font-mono text-xs font-semibold tracking-wider uppercase">
              What should I call you?
            </label>
            <input
              type="text"
              value={guestName}
              onChange={(e) => setGuestName(e.target.value)}
              placeholder="Your name"
              autoComplete="off"
              className={cn(
                'border-input bg-background text-foreground placeholder:text-muted-foreground',
                'rounded-full border px-4 py-2 font-mono text-sm outline-none',
                'focus:ring-ring focus:ring-2 focus:ring-offset-0',
                'transition-colors duration-200'
              )}
            />
          </div>

          {/* Purpose */}
          <div className="flex flex-col gap-1.5">
            <label className="text-foreground font-mono text-xs font-semibold tracking-wider uppercase">
              Why are you here for?
            </label>
            <select
              value={purpose}
              onChange={(e) => setPurpose(e.target.value)}
              className={cn(
                'border-input bg-background text-foreground',
                'rounded-full border px-4 py-2 font-mono text-sm outline-none',
                'focus:ring-ring focus:ring-2 focus:ring-offset-0',
                'transition-colors duration-200 cursor-pointer',
                !purpose && 'text-muted-foreground'
              )}
            >
              <option value="" disabled>
                Select a reason…
              </option>
              {PURPOSES.map((p) => (
                <option key={p} value={p} className="text-foreground">
                  {p}
                </option>
              ))}
            </select>
          </div>

          {/* Password */}
          <div className="flex flex-col gap-1.5">
            <label className="text-foreground font-mono text-xs font-semibold tracking-wider uppercase">
              Give me our secret
            </label>
            <input
              type="password"
              value={passwd}
              onChange={(e) => setPasswd(e.target.value)}
              placeholder="••••••••"
              autoComplete="current-password"
              className={cn(
                'border-input bg-background text-foreground placeholder:text-muted-foreground',
                'rounded-full border px-4 py-2 font-mono text-sm outline-none',
                'focus:ring-ring focus:ring-2 focus:ring-offset-0',
                'transition-colors duration-200'
              )}
            />
          </div>

          {/* Error message */}
          <AnimatePresence mode="wait">
            {error && (
              <motion.p
                key={error}
                initial={{ opacity: 0, y: -4 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.2 }}
                className="text-destructive rounded-lg border border-current/20 bg-current/5 px-3 py-2 text-center font-mono text-xs"
              >
                {error}
              </motion.p>
            )}
          </AnimatePresence>

          <Button
            type="submit"
            variant="primary"
            size="lg"
            disabled={loading}
            className="mt-2 w-full font-mono"
          >
            {loading ? 'Checking…' : 'Enter'}
          </Button>
        </form>
      </motion.div>
    </div>
  );
}
