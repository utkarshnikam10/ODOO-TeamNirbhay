import React, { useState, useRef, useEffect } from 'react';
import { KeyRound, CheckCircle2, ArrowRight, ShieldCheck, RefreshCw } from 'lucide-react';
import { Modal } from '../common/Modal';

interface OtpModalProps {
  isOpen: boolean;
  onClose: () => void;
  email: string;
  onSuccess: () => void;
}

export const OtpModal: React.FC<OtpModalProps> = ({ isOpen, onClose, email, onSuccess }) => {
  const [otp, setOtp] = useState<string[]>(['8', '4', '9', '2', '0', '1']);
  const [timer, setTimer] = useState<number>(45);
  const [isVerifying, setIsVerifying] = useState<boolean>(false);
  const [isSuccess, setIsSuccess] = useState<boolean>(false);
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [step, setStep] = useState<'otp' | 'new_password'>('otp');
  const [error, setError] = useState('');

  const inputRefs = useRef<(HTMLInputElement | null)[]>([]);

  useEffect(() => {
    let interval: any = null;
    if (isOpen && timer > 0) {
      interval = setInterval(() => {
        setTimer((prev) => prev - 1);
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [isOpen, timer]);

  const handleChange = (index: number, value: string) => {
    if (!/^\d*$/.test(value)) return;
    const newOtp = [...otp];
    newOtp[index] = value.slice(-1);
    setOtp(newOtp);

    if (value && index < 5) {
      inputRefs.current[index + 1]?.focus();
    }
  };

  const handleKeyDown = (index: number, e: React.KeyboardEvent) => {
    if (e.key === 'Backspace' && !otp[index] && index > 0) {
      inputRefs.current[index - 1]?.focus();
    }
  };

  const handleVerifyOtp = (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    const code = otp.join('');
    if (code.length < 6) {
      setError('Please enter the complete 6-digit verification code.');
      return;
    }

    setIsVerifying(true);
    setTimeout(() => {
      setIsVerifying(false);
      setStep('new_password');
    }, 800);
  };

  const handleResetPassword = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newPassword || newPassword.length < 6) {
      setError('Password must be at least 6 characters long.');
      return;
    }
    if (newPassword !== confirmPassword) {
      setError('Passwords do not match.');
      return;
    }

    setIsSuccess(true);
    setTimeout(() => {
      onSuccess();
      onClose();
    }, 1200);
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="2FA & Password Recovery" maxWidth="md">
      <div className="text-xs text-slate-700">
        {step === 'otp' && (
          <form onSubmit={handleVerifyOtp} className="space-y-4">
            <div className="flex items-center gap-3 p-3 bg-sky-50 border border-sky-200 rounded-md text-sky-900">
              <ShieldCheck className="h-5 w-5 text-sky-600 flex-shrink-0" />
              <div>
                <div className="font-semibold text-sky-950">Verification Code Sent</div>
                <div className="text-[11px] text-sky-800">
                  We have dispatched a 6-digit security OTP code to{' '}
                  <span className="font-mono font-semibold">{email || 'user@stocksense.io'}</span>
                </div>
              </div>
            </div>

            {error && <div className="p-2 text-[11px] text-rose-700 bg-rose-50 border border-rose-200 rounded">{error}</div>}

            <div className="space-y-2 py-2 text-center">
              <label className="block text-xs font-semibold text-slate-800 uppercase tracking-wider">
                Enter 6-Digit Security Code
              </label>
              <div className="flex justify-center gap-2">
                {otp.map((digit, idx) => (
                  <input
                    key={idx}
                    ref={(el) => { inputRefs.current[idx] = el; }}
                    type="text"
                    maxLength={1}
                    value={digit}
                    onChange={(e) => handleChange(idx, e.target.value)}
                    onKeyDown={(e) => handleKeyDown(idx, e)}
                    className="h-11 w-11 text-center font-mono text-lg font-bold text-slate-900 border border-slate-300 rounded-md shadow-2xs focus:border-sky-600 focus:ring-1 focus:ring-sky-600 focus:outline-none"
                  />
                ))}
              </div>
              <p className="text-[10px] text-slate-400">Default demo OTP: 849201</p>
            </div>

            <div className="flex items-center justify-between text-xs text-slate-500 pt-2 border-t border-slate-100">
              <button
                type="button"
                disabled={timer > 0}
                onClick={() => setTimer(45)}
                className="flex items-center gap-1 font-medium text-sky-700 hover:text-sky-900 disabled:text-slate-400 disabled:no-underline"
              >
                <RefreshCw className="h-3 w-3" />
                Resend Code {timer > 0 ? `(${timer}s)` : ''}
              </button>

              <button
                type="submit"
                disabled={isVerifying}
                className="inline-flex items-center gap-1.5 px-4 py-2 text-xs font-semibold text-white bg-sky-700 rounded-md hover:bg-sky-800 transition-colors shadow-xs"
              >
                {isVerifying ? 'Verifying...' : 'Verify OTP'}
                <ArrowRight className="h-3.5 w-3.5" />
              </button>
            </div>
          </form>
        )}

        {step === 'new_password' && !isSuccess && (
          <form onSubmit={handleResetPassword} className="space-y-4">
            <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-md text-emerald-900 text-xs flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4 text-emerald-600 flex-shrink-0" />
              <span>OTP verified successfully. Set your new security password.</span>
            </div>

            {error && <div className="p-2 text-[11px] text-rose-700 bg-rose-50 border border-rose-200 rounded">{error}</div>}

            <div>
              <label className="block font-medium text-slate-700 mb-1">New Password *</label>
              <input
                type="password"
                placeholder="At least 6 characters"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                className="w-full rounded-md border border-slate-300 p-2 text-xs focus:border-sky-500 focus:outline-none"
              />
            </div>

            <div>
              <label className="block font-medium text-slate-700 mb-1">Confirm New Password *</label>
              <input
                type="password"
                placeholder="Re-enter new password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                className="w-full rounded-md border border-slate-300 p-2 text-xs focus:border-sky-500 focus:outline-none"
              />
            </div>

            <div className="flex justify-end gap-3 pt-3 border-t border-slate-200">
              <button
                type="submit"
                className="px-4 py-2 text-xs font-semibold text-white bg-sky-700 rounded-md hover:bg-sky-800 transition-colors shadow-xs"
              >
                Update Password & Login
              </button>
            </div>
          </form>
        )}

        {isSuccess && (
          <div className="p-6 text-center space-y-3">
            <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-emerald-100 text-emerald-600">
              <CheckCircle2 className="h-6 w-6" />
            </div>
            <h3 className="text-sm font-bold text-slate-900">Password Reset Successful!</h3>
            <p className="text-xs text-slate-500">Redirecting to StockSense operational dashboard...</p>
          </div>
        )}
      </div>
    </Modal>
  );
};
