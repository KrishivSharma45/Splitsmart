import { useState } from "react";
import toast from "react-hot-toast";
import * as authApi from "../api/auth";
import { extractErrorMessage } from "../api/client";
import { Card } from "../components/ui/Card";
import { useAuth } from "../context/AuthContext";

export function Settings() {
  const { user, setUser, logout } = useAuth();
  const [fullName, setFullName] = useState(user?.full_name ?? "");
  const [savingProfile, setSavingProfile] = useState(false);

  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [savingPassword, setSavingPassword] = useState(false);

  async function handleProfileSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSavingProfile(true);
    try {
      const updated = await authApi.updateMe(fullName);
      setUser(updated);
      toast.success("Profile updated");
    } catch (err) {
      toast.error(extractErrorMessage(err));
    } finally {
      setSavingProfile(false);
    }
  }

  async function handlePasswordSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSavingPassword(true);
    try {
      await authApi.changePassword(currentPassword, newPassword);
      toast.success("Password changed. Please log in again.");
      setCurrentPassword("");
      setNewPassword("");
      await logout();
      window.location.href = "/login";
    } catch (err) {
      toast.error(extractErrorMessage(err));
    } finally {
      setSavingPassword(false);
    }
  }

  return (
    <div className="mx-auto max-w-2xl">
      <h1 className="font-serif text-3xl text-ink">Settings</h1>
      <p className="mt-1 text-sm text-ink-faint">Manage your profile and account security.</p>

      <Card className="mt-6">
        <h2 className="font-serif text-lg text-ink">Profile</h2>
        <form onSubmit={handleProfileSubmit} className="mt-4 space-y-4">
          <div>
            <label className="label">Full name</label>
            <input className="input" value={fullName} onChange={(e) => setFullName(e.target.value)} />
          </div>
          <div>
            <label className="label">Email</label>
            <input className="input opacity-60" value={user?.email ?? ""} disabled />
            <p className="mt-1 text-xs text-ink-faint">Email cannot be changed.</p>
          </div>
          <button type="submit" disabled={savingProfile} className="btn-primary">
            {savingProfile ? "Saving…" : "Save profile"}
          </button>
        </form>
      </Card>

      <Card className="mt-6">
        <h2 className="font-serif text-lg text-ink">Change password</h2>
        <form onSubmit={handlePasswordSubmit} className="mt-4 space-y-4">
          <div>
            <label className="label">Current password</label>
            <input
              type="password"
              required
              className="input"
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
            />
          </div>
          <div>
            <label className="label">New password</label>
            <input
              type="password"
              required
              className="input"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
            />
            <p className="mt-1 text-xs text-ink-faint">
              At least 8 characters, with an uppercase letter, lowercase letter, and a digit.
            </p>
          </div>
          <button type="submit" disabled={savingPassword} className="btn-primary">
            {savingPassword ? "Changing…" : "Change password"}
          </button>
        </form>
      </Card>

      <Card className="mt-6 border-line">
        <h2 className="font-serif text-lg text-ink">Account</h2>
        <p className="mt-2 text-sm text-ink-faint">
          Member since {user ? new Date(user.created_at).toLocaleDateString() : "—"}.
        </p>
      </Card>
    </div>
  );
}
