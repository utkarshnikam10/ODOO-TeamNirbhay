import React, { useState } from 'react';
import { User as UserIcon, Mail, Shield, Clock, Key, LogOut, CheckCircle2 } from 'lucide-react';
import { useInventory } from '../context/InventoryContext';

interface ProfileViewProps {
  onLogoutClick: () => void;
}

export const ProfileView: React.FC<ProfileViewProps> = ({ onLogoutClick }) => {
  const { currentUser, showToast } = useInventory();

  const [name, setName] = useState(currentUser.name);
  const [email, setEmail] = useState(currentUser.email);
  const [role, setRole] = useState(currentUser.role);

  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');

  const handleSaveProfile = (e: React.FormEvent) => {
    e.preventDefault();
    showToast('success', 'Profile Saved', 'User profile information updated successfully.');
  };

  const handleChangePassword = (e: React.FormEvent) => {
    e.preventDefault();
    if (!currentPassword || !newPassword) {
      showToast('error', 'Error', 'Please fill in all password fields.');
      return;
    }
    if (newPassword !== confirmPassword) {
      showToast('error', 'Error', 'New passwords do not match.');
      return;
    }
    showToast('success', 'Password Changed', 'Security password updated successfully.');
    setCurrentPassword('');
    setNewPassword('');
    setConfirmPassword('');
  };

  return (
    <div className="space-y-6 pb-12 font-sans max-w-4xl mx-auto">
      {/* Header */}
      <div className="border-b border-slate-200 pb-4">
        <h1 className="text-xl font-bold tracking-tight text-slate-900">User Profile & Security Settings</h1>
        <p className="text-xs text-slate-500 mt-0.5">Manage operator credentials, access roles, and security authentication</p>
      </div>

      {/* User Info Overview Card */}
      <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-xs flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <div className="h-16 w-16 rounded-full bg-sky-700 text-white flex items-center justify-center font-bold text-xl shadow-md ring-4 ring-sky-100">
            VS
          </div>
          <div>
            <h2 className="text-lg font-bold text-slate-900">{name}</h2>
            <div className="flex flex-wrap items-center gap-3 text-xs text-slate-500 mt-1">
              <span className="flex items-center gap-1">
                <Mail className="h-3.5 w-3.5 text-slate-400" />
                {email}
              </span>
              <span className="flex items-center gap-1 font-semibold text-sky-800 bg-sky-50 px-2 py-0.5 rounded border border-sky-200">
                <Shield className="h-3.5 w-3.5" />
                {role}
              </span>
            </div>
          </div>
        </div>

        <div className="text-right text-xs text-slate-500">
          <div className="flex items-center gap-1 justify-end">
            <Clock className="h-3.5 w-3.5 text-slate-400" />
            Last active session:
          </div>
          <div className="font-mono text-slate-800 font-semibold">{currentUser.lastLogin}</div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Profile Edit Form */}
        <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-xs">
          <h3 className="text-sm font-bold text-slate-900 mb-3 border-b border-slate-100 pb-2">
            Personal Information
          </h3>
          <form onSubmit={handleSaveProfile} className="space-y-4 text-xs">
            <div>
              <label className="block font-medium text-slate-700 mb-1">Full Name</label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full rounded-md border border-slate-300 p-2 text-xs focus:border-sky-500 focus:outline-none"
              />
            </div>

            <div>
              <label className="block font-medium text-slate-700 mb-1">Email Address</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full rounded-md border border-slate-300 p-2 text-xs focus:border-sky-500 focus:outline-none"
              />
            </div>

            <div>
              <label className="block font-medium text-slate-700 mb-1">Assigned Role</label>
              <input
                type="text"
                value={role}
                onChange={(e) => setRole(e.target.value)}
                className="w-full rounded-md border border-slate-300 p-2 text-xs focus:border-sky-500 focus:outline-none bg-slate-50"
              />
            </div>

            <div className="pt-2">
              <button
                type="submit"
                className="px-4 py-2 text-xs font-semibold text-white bg-sky-700 rounded-md hover:bg-sky-800 transition-colors shadow-xs"
              >
                Save Profile Changes
              </button>
            </div>
          </form>
        </div>

        {/* Change Password Form */}
        <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-xs">
          <h3 className="text-sm font-bold text-slate-900 mb-3 border-b border-slate-100 pb-2 flex items-center gap-1.5">
            <Key className="h-4 w-4 text-slate-600" />
            Security & Password
          </h3>
          <form onSubmit={handleChangePassword} className="space-y-4 text-xs">
            <div>
              <label className="block font-medium text-slate-700 mb-1">Current Password</label>
              <input
                type="password"
                placeholder="••••••••••••"
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                className="w-full rounded-md border border-slate-300 p-2 text-xs focus:border-sky-500 focus:outline-none"
              />
            </div>

            <div>
              <label className="block font-medium text-slate-700 mb-1">New Security Password</label>
              <input
                type="password"
                placeholder="New password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                className="w-full rounded-md border border-slate-300 p-2 text-xs focus:border-sky-500 focus:outline-none"
              />
            </div>

            <div>
              <label className="block font-medium text-slate-700 mb-1">Confirm New Password</label>
              <input
                type="password"
                placeholder="Re-enter new password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                className="w-full rounded-md border border-slate-300 p-2 text-xs focus:border-sky-500 focus:outline-none"
              />
            </div>

            <div className="pt-2 flex items-center justify-between">
              <button
                type="submit"
                className="px-4 py-2 text-xs font-semibold text-white bg-slate-800 rounded-md hover:bg-slate-900 transition-colors shadow-xs"
              >
                Update Password
              </button>

              <button
                type="button"
                onClick={onLogoutClick}
                className="inline-flex items-center gap-1 text-xs font-semibold text-rose-700 hover:text-rose-900"
              >
                <LogOut className="h-3.5 w-3.5" />
                Sign Out
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};
