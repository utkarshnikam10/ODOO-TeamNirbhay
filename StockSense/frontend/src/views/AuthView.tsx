import React, { useState } from 'react';
import { Boxes, ArrowRight, ShieldCheck, Lock, Mail, User, Building } from 'lucide-react';
import { OtpModal } from '../components/auth/OtpModal';

interface AuthViewProps {
  onLoginSuccess: () => void;
}

export const AuthView: React.FC<AuthViewProps> = ({ onLoginSuccess }) => {
  const [mode, setMode] = useState<'login' | 'signup' | 'forgot'>('login');
  const [email, setEmail] = useState('vikram.singh@stocksense.io');
  const [password, setPassword] = useState('••••••••••••');
  const [name, setName] = useState('Vikramjit Singh');
  const [company, setCompany] = useState('Vardhman Industrial Group');
  const [isOtpOpen, setIsOtpOpen] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (mode === 'login') {
      if (!email || !password) {
        setError('Please enter valid email and password credentials.');
        return;
      }
      onLoginSuccess();
    } else if (mode === 'signup') {
      if (!name || !email || !password) {
        setError('Please complete all required fields.');
        return;
      }
      onLoginSuccess();
    } else if (mode === 'forgot') {
      if (!email) {
        setError('Please enter your account email address.');
        return;
      }
      setIsOtpOpen(true);
    }
  };

  return (
    <div className="min-h-screen bg-slate-900 flex flex-col justify-center py-12 sm:px-6 lg:px-8 font-sans selection:bg-sky-500 selection:text-white">
      {/* Brand Header */}
      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center space-y-3">
        <div className="inline-flex h-12 w-12 items-center justify-center rounded-xl bg-sky-600 text-white shadow-lg ring-4 ring-sky-500/20">
          <Boxes className="h-7 w-7" />
        </div>
        <h2 className="text-2xl font-bold tracking-tight text-white">StockSense</h2>
        <p className="text-xs text-slate-400">Enterprise Inventory & Warehouse Control Platform</p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-8 px-4 shadow-2xl rounded-xl sm:px-10 border border-slate-200">
          {/* Mode Switcher Tabs */}
          <div className="flex border-b border-slate-200 mb-6 text-xs font-semibold">
            <button
              onClick={() => {
                setMode('login');
                setError('');
              }}
              className={`flex-1 pb-3 text-center transition-colors border-b-2 ${
                mode === 'login' ? 'border-sky-600 text-sky-700 font-bold' : 'border-transparent text-slate-500 hover:text-slate-800'
              }`}
            >
              Sign In
            </button>
            <button
              onClick={() => {
                setMode('signup');
                setError('');
              }}
              className={`flex-1 pb-3 text-center transition-colors border-b-2 ${
                mode === 'signup' ? 'border-sky-600 text-sky-700 font-bold' : 'border-transparent text-slate-500 hover:text-slate-800'
              }`}
            >
              Create Account
            </button>
            <button
              onClick={() => {
                setMode('forgot');
                setError('');
              }}
              className={`flex-1 pb-3 text-center transition-colors border-b-2 ${
                mode === 'forgot' ? 'border-sky-600 text-sky-700 font-bold' : 'border-transparent text-slate-500 hover:text-slate-800'
              }`}
            >
              Reset Key
            </button>
          </div>

          {error && (
            <div className="mb-4 p-3 rounded-md bg-rose-50 border border-rose-200 text-rose-800 text-xs font-medium">
              {error}
            </div>
          )}

          <form className="space-y-4 text-xs" onSubmit={handleSubmit}>
            {mode === 'signup' && (
              <>
                <div>
                  <label className="block font-medium text-slate-700 mb-1">Full Name *</label>
                  <div className="relative">
                    <User className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
                    <input
                      type="text"
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                      className="w-full rounded-md border border-slate-300 py-2 pl-9 pr-3 text-xs focus:border-sky-500 focus:outline-none"
                      placeholder="Vikramjit Singh"
                    />
                  </div>
                </div>

                <div>
                  <label className="block font-medium text-slate-700 mb-1">Company / Organization *</label>
                  <div className="relative">
                    <Building className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
                    <input
                      type="text"
                      value={company}
                      onChange={(e) => setCompany(e.target.value)}
                      className="w-full rounded-md border border-slate-300 py-2 pl-9 pr-3 text-xs focus:border-sky-500 focus:outline-none"
                      placeholder="Vardhman Industrial Group"
                    />
                  </div>
                </div>
              </>
            )}

            <div>
              <label className="block font-medium text-slate-700 mb-1">Work Email Address *</label>
              <div className="relative">
                <Mail className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full rounded-md border border-slate-300 py-2 pl-9 pr-3 text-xs focus:border-sky-500 focus:outline-none"
                  placeholder="name@company.com"
                />
              </div>
            </div>

            {mode !== 'forgot' && (
              <div>
                <div className="flex items-center justify-between mb-1">
                  <label className="block font-medium text-slate-700">Security Password *</label>
                  {mode === 'login' && (
                    <button
                      type="button"
                      onClick={() => setMode('forgot')}
                      className="text-[11px] text-sky-700 hover:text-sky-900 font-medium"
                    >
                      Forgot password?
                    </button>
                  )}
                </div>
                <div className="relative">
                  <Lock className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
                  <input
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full rounded-md border border-slate-300 py-2 pl-9 pr-3 text-xs focus:border-sky-500 focus:outline-none"
                    placeholder="••••••••••••"
                  />
                </div>
              </div>
            )}

            <div>
              <button
                type="submit"
                className="w-full flex justify-center items-center gap-2 py-2.5 px-4 border border-transparent rounded-md shadow-sm text-xs font-semibold text-white bg-sky-700 hover:bg-sky-800 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-sky-500 transition-colors"
              >
                {mode === 'login' ? 'Access Inventory Console' : mode === 'signup' ? 'Create Enterprise Account' : 'Request OTP Reset'}
                <ArrowRight className="h-4 w-4" />
              </button>
            </div>
          </form>

          {/* Quick Demo Pre-fill helper */}
          <div className="mt-6 pt-4 border-t border-slate-100 text-center">
            <button
              onClick={() => onLoginSuccess()}
              className="inline-flex items-center gap-1.5 text-xs text-slate-500 hover:text-sky-700 font-medium"
            >
              <ShieldCheck className="h-3.5 w-3.5 text-emerald-600" />
              Quick Hackathon Demo Instant Access →
            </button>
          </div>
        </div>
      </div>

      <OtpModal
        isOpen={isOtpOpen}
        onClose={() => setIsOtpOpen(false)}
        email={email}
        onSuccess={() => {
          setIsOtpOpen(false);
          onLoginSuccess();
        }}
      />
    </div>
  );
};
